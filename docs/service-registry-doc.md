# service-registry

**Alias:** Service Registry / Discovery Service

## Purpose
Provides a centralized registry for service discovery, allowing trading platform services to find each other's endpoints. Uses mTLS-secured MongoDB for storage and enforces client certificate CN allowlist for access control.

## Architecture

```
Service Instance Startup
    ↓
┌──────────────────────────────────┐
│  Register Service                │
│  - POST /register with endpoint  │
│  - Include service name, host    │
│  - Health check interval         │
└──────────┬───────────────────────┘
           ↓
┌──────────────────────────────────┐
│  Store in MongoDB                │
│  - services collection           │
│  - TTL index (30 min heartbeat)  │
│  - Metadata: version, tags       │
└──────────┬───────────────────────┘
           ↓
(Service running: heartbeat every 5 min)
           ↓
┌──────────────────────────────────┐
│  Service Lookup Request          │
│  (from order-validate, etc.)     │
│  - GET /lookup/order-entry       │
│  - Include mTLS cert CN          │
└──────────┬───────────────────────┘
           ↓
┌──────────────────────────────────┐
│  Verify mTLS CN Allowlist        │
│  - Check if caller is authorized│
│  - Prevent rogue services        │
└──────────┬───────────────────────┘
           ↓
┌──────────────────────────────────┐
│  Query MongoDB for Service       │
│  - Lookup by service name        │
│  - Return healthy instances      │
│  - Load balance (round-robin)    │
└──────────┬───────────────────────┘
           ↓
┌──────────────────────────────────┐
│  Return Endpoints                │
│  - host:port                     │
│  - Metadata (version, tags)      │
│  - Cache for 5 minutes           │
└──────────────────────────────────┘
```

## Dependencies

### MongoDB
- **Purpose:** Persistent registry storage
- **Collections:**
  - `services` — Registered services (name, endpoint, health, tags)
  - `service_metadata` — Service versions, capabilities
  - `mtls_allowlist` — Approved client certificate CNs
- **Auth:** mTLS with client cert
- **Indexes:**
  - `name` (unique)
  - `last_heartbeat` (TTL: 30 minutes; auto-cleanup)
  - `service_tag` (for filtering by tag)

## Configuration

```yaml
service:
  name: service-registry
  port: 8090
  tls_enabled: true
  tls_cert: /etc/certs/registry-server.pem
  tls_key: /etc/certs/registry-server-key.pem

mongodb:
  uri: mongodb+srv://mongo.trading.internal
  database: trading_registry
  client_cert: /etc/certs/registry-mongo-client.pem
  client_key: /etc/certs/registry-mongo-client-key.pem
  ca_bundle: /etc/certs/mongo-ca.pem
  collections:
    services: service registrations
    service_metadata: service capabilities
    mtls_allowlist: authorized client CNs

mtls:
  enabled: true
  ca_bundle: /etc/certs/client-ca.pem
  required: true
  cn_allowlist:
    - "order-validate.trading.svc.cluster.local"
    - "order-entry.trading.svc.cluster.local"
    - "order-router.trading.svc.cluster.local"
    - "fix-service.trading.svc.cluster.local"
    - "admin.trading.internal"

cache:
  enabled: true
  ttl_seconds: 300  # 5 minutes
  backend: "in-memory"  # or redis for distributed cache

health_check:
  enabled: true
  interval: 5m
  timeout: 10s
  endpoint_path: "/health"
```

## API Endpoints

### POST /register
Register a service instance.

**Request (with mTLS cert):**
```json
{
  "service_name": "order-entry",
  "host": "order-entry-1.trading.internal",
  "port": 8081,
  "version": "2.0.5",
  "tags": ["critical", "production"],
  "health_check_url": "http://order-entry-1.trading.internal:8081/health",
  "metadata": {
    "region": "us-east-1",
    "replica": 1,
    "capabilities": ["REST", "gRPC"]
  }
}
```

**Response (201 Created):**
```json
{
  "service_id": "order-entry-1",
  "registered_at": "2026-02-14T10:30:45Z",
  "next_heartbeat_due": "2026-02-14T10:35:45Z",
  "ttl_seconds": 1800
}
```

### GET /lookup/{serviceName}
Discover a service by name.

**Request (requires mTLS cert):**
```
GET /lookup/order-entry HTTP/1.1
Host: registry.trading.internal:8090
(mTLS cert CN validated)
```

**Response (200 OK):**
```json
{
  "service_name": "order-entry",
  "instances": [
    {
      "service_id": "order-entry-1",
      "host": "order-entry-1.trading.internal",
      "port": 8081,
      "version": "2.0.5",
      "health_status": "HEALTHY",
      "registered_at": "2026-02-14T09:00:00Z",
      "tags": ["critical", "production"]
    },
    {
      "service_id": "order-entry-2",
      "host": "order-entry-2.trading.internal",
      "port": 8081,
      "version": "2.0.5",
      "health_status": "HEALTHY"
    }
  ],
  "load_balance_strategy": "round-robin"
}
```

### POST /heartbeat/{serviceId}
Heartbeat to keep registration alive.

**Request:**
```json
{
  "health_status": "HEALTHY",
  "metrics": {
    "cpu_usage_pct": 45,
    "memory_usage_pct": 62,
    "request_rate": 1250
  }
}
```

**Response (200 OK):**
```json
{
  "service_id": "order-entry-1",
  "acknowledged_at": "2026-02-14T10:35:46Z",
  "next_heartbeat_due": "2026-02-14T10:40:46Z"
}
```

### GET /services
List all registered services.

**Response:**
```json
{
  "services": [
    {
      "name": "order-validate",
      "instances": 2,
      "healthy_instances": 2
    },
    {
      "name": "order-entry",
      "instances": 3,
      "healthy_instances": 3
    },
    {
      "name": "order-router",
      "instances": 2,
      "healthy_instances": 2
    }
  ],
  "total_instances": 7
}
```

### GET /health
Registry service health.

**Response:**
```json
{
  "status": "UP",
  "components": {
    "mongodb": "UP",
    "mtls": "OPERATIONAL"
  }
}
```

## mTLS Certificate Allowlist

**Configuration in MongoDB:**
```javascript
db.mtls_allowlist.find()
[
  {
    "_id": ObjectId(...),
    "cn": "order-validate.trading.svc.cluster.local",
    "description": "order-validate service",
    "authorized_lookups": ["order-entry", "service-registry"],
    "created_at": ISODate("2026-01-01T00:00:00Z"),
    "expires_at": ISODate("2027-01-01T00:00:00Z")
  },
  {
    "cn": "order-entry.trading.svc.cluster.local",
    "authorized_lookups": ["order-router", "service-registry"]
  },
  ...
]
```

**Lookup Flow:**
1. Client connects with mTLS cert
2. Extract CN from cert: `order-validate.trading.svc.cluster.local`
3. Verify CN in allowlist
4. Check if authorized for requested service lookup
5. Return endpoint or 403 Forbidden

## Data Flow

### Service Registration
1. Service starts up (e.g., order-entry replica 1)
2. Constructs registration payload (name, host, port, version)
3. Calls POST `/register` with mTLS client cert
4. Registry verifies CN is in allowlist
5. Stores registration in MongoDB with TTL (30 min)
6. Returns service_id and next heartbeat time
7. Service schedules heartbeat every 5 minutes

### Service Lookup
1. Service needs to call another service (e.g., order-validate calls order-entry)
2. Calls GET `/lookup/order-entry` with mTLS cert
3. Registry verifies CN authorization
4. Queries MongoDB for healthy instances of order-entry
5. Applies load balancing (round-robin)
6. Returns endpoint list
7. Caller caches for 5 minutes (or shorter if stale)
8. Caller connects directly to endpoint with mTLS

### Automatic Stale Removal
1. MongoDB TTL index on `last_heartbeat` field
2. Services without heartbeat > 30 minutes auto-deleted
3. Health check poller periodically verifies instances are responding
4. If health check fails 3x, mark as UNHEALTHY (but keep registered)
5. Caller receives UNHEALTHY status and can failover

## Error Handling

| Scenario | Response | Action |
|----------|----------|--------|
| CN not in allowlist | 403 Forbidden | Log; caller must provision cert |
| Service not found | 404 Not Found | Caller can retry or use fallback |
| MongoDB unavailable | 503 Service Unavailable | Circuit breaker; in-memory cache fallback |
| Heartbeat timeout | Mark UNHEALTHY | Caller uses other instances |
| Cert expired | TLS handshake fails | Manual cert rotation required |

## Monitoring & Observability

### Metrics
- `registered_services_total` — Number of registered services
- `service_instances_total` — Total instances across all services
- `healthy_instances_total` — Instances marked HEALTHY
- `lookup_requests_total` — Total lookups by service name
- `cn_auth_failures_total` — Unauthorized access attempts
- `mongodb_write_latency_ms` — Registration latency

### Logs
- `registry.log` — All registrations & lookups
- `mtls_access.log` — CN verification & auth decisions
- `health_check.log` — Health check results per instance

### Traces
- OpenTelemetry: service_name, service_id, CN
- Spans: [CN Verify] → [DB Query] → [Load Balance] → [Return]

## Security

- **mTLS Required:** All clients must present valid cert with CN in allowlist
- **Certificate Pinning:** Optional (pin MongoDB server cert)
- **Audit Log:** Every lookup and registration logged with timestamp & CN
- **Secrets:** No passwords stored; only cert-based auth
- **Network:** Service Registry should be in dedicated network namespace
- **Rate Limiting:** 1000 reqs/sec per CN; per-service limits

## Operational Notes

### Adding a New Service to Allowlist
1. Generate cert for new service (signed by CA)
2. Extract CN from cert: `my-service.trading.svc.cluster.local`
3. Add to allowlist in MongoDB:
   ```javascript
   db.mtls_allowlist.insertOne({
     cn: "my-service.trading.svc.cluster.local",
     description: "My new service",
     authorized_lookups: ["service1", "service2"],
     expires_at: ISODate("2027-01-01T00:00:00Z")
   })
   ```
4. Service can now register & lookup

### Debugging Service Discovery Issues
```bash
# 1. Check if service is registered
curl -k --cert client.pem --key client-key.pem \
  https://registry.trading.internal:8090/services

# 2. Look up specific service
curl -k --cert client.pem --key client-key.pem \
  https://registry.trading.internal:8090/lookup/order-entry

# 3. Check service health
curl http://order-entry-1.trading.internal:8081/health
```

### Cert Renewal Before Expiry
1. Issue new cert from CA
2. Trigger service restart (or graceful reload)
3. Service reconnects with new cert
4. Existing registrations persist (only cert auth changes)

## Runbook

### Check All Registered Services
```bash
curl -k --cert client.pem --key client-key.pem \
  https://registry.trading.internal:8090/services
```

### Find Order-Entry Endpoint
```bash
curl -k --cert client.pem --key client-key.pem \
  https://registry.trading.internal:8090/lookup/order-entry
# Use the returned host:port for service calls
```

### Force Unregister a Service (Admin)
```bash
# Direct MongoDB access (requires admin cert)
db.services.deleteOne({service_id: "order-entry-1"})
```

### View mTLS Allowlist
```bash
# Direct MongoDB access
db.mtls_allowlist.find()
```

### Check Registry Uptime
```bash
curl -k https://registry.trading.internal:8090/health
```
