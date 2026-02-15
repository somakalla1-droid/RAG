# order-validate Service

**Alias:** OrderGetValidated / orderValidate

## Purpose
Validates incoming orders against business rules and reference data, then publishes validated orders to IBM MQ for downstream processing.

## Architecture

```
Order Request (HTTP/gRPC)
    ↓
┌─────────────────────────────────┐
│  Input Validation               │
│  - Schema checks                │
│  - Field format validation      │
│  - Quantity/price bounds        │
└──────────┬──────────────────────┘
           ↓
┌─────────────────────────────────┐
│  Business Rule Validation       │
│  - Fetch rules from MongoDB     │
│  - Risk limits (notional, qty)  │
│  - Trading hours check          │
│  - Settlement viability         │
└──────────┬──────────────────────┘
           ↓
┌─────────────────────────────────┐
│  Audit & Logging                │
│  - Write validation event to SQL│
│  - Log rule violations          │
│  - Store for compliance         │
└──────────┬──────────────────────┘
           ↓
┌─────────────────────────────────┐
│  Publish to MQ                  │
│  - Topic: TRADE.VALIDATED.ORDERS│
│  - Serialization: JSON/Avro     │
│  - Idempotency: messageId dedup │
└─────────────────────────────────┘
```

## Dependencies

### IBM MQ
- **Topic/Queue:** `TRADE.VALIDATED.ORDERS`
- **Protocol:** AMQP with TLS
- **Client Cert:** `/etc/certs/mq-client.pem`
- **Purpose:** Publish validated orders

### MongoDB
- **Motive:** Store validation rules & audit logs
- **Authentication:** mTLS (client certificate)
- **Cert Path:** `/etc/certs/mongo-client.pem`
- **Collections:**
  - `validation_rules` — Business rules by product/counterparty
  - `validation_audit` — Audit trail of validation decisions
- **Operations:**
  - Read: `O(1)` lookup of rules by orderId
  - Write: Audit log for every order

### SQL (via Safeguard)
- **Motive:** Store order events & compliance records
- **Credentials:** Retrieved from Safeguard A2A at startup
- **Tables:**
  - `order_events` — Immutable log of order lifecycle
  - `validation_events` — Detailed validation results
- **Constraints:**
  - Unique index on `orderId`
  - Foreign key to `counterparties`

### Service Registry
- **Purpose:** Discover downstream `order-entry` endpoint
- **Discovery:** At startup + periodic refresh (5min)
- **Lookup:** `registry.lookup("order-entry").endpoint`

## Configuration

```yaml
service:
  name: order-validate
  port: 8080
  graceful_shutdown: 30s

mq:
  broker_url: amqp://mq.trading.internal:5672
  topic: TRADE.VALIDATED.ORDERS
  client_cert: /etc/certs/mq-client.pem
  client_key: /etc/certs/mq-client-key.pem
  ca_bundle: /etc/certs/mq-ca.pem

mongodb:
  uri: mongodb+srv://mongo.trading.internal
  database: trading_validation
  client_cert: /etc/certs/mongo-client.pem
  client_key: /etc/certs/mongo-client-key.pem
  ca_bundle: /etc/certs/mongo-ca.pem

database:
  sql_host: db.trading.internal
  sql_port: 5432
  sql_database: trading_audit
  credentials_source: safeguard
  credentials_path: /secret/sql-credentials

service_registry:
  endpoint: registry.trading.internal:8090
  lookup_interval: 5m
```

## API Endpoints

### POST /validate
Validate and publish an order.

**Request:**
```json
{
  "orderId": "ORD-20260214-001",
  "symbol": "AAPL",
  "side": "BUY",
  "quantity": 100,
  "price": 145.50,
  "counterparty": "ACME-TRADING",
  "settlement_date": "2026-02-16"
}
```

**Response (Success 202):**
```json
{
  "orderId": "ORD-20260214-001",
  "status": "VALIDATED",
  "message": "Order passed all validations",
  "published_to_mq": true,
  "timestamp": "2026-02-14T10:30:45Z"
}
```

**Response (Failure 400):**
```json
{
  "orderId": "ORD-20260214-001",
  "status": "REJECTED",
  "errors": [
    "Notional exceeds risk limit (50M limit, got 145.5M)",
    "Trading hours: market closed"
  ],
  "timestamp": "2026-02-14T10:30:45Z"
}
```

### GET /health
Health check endpoint.

**Response:**
```json
{
  "status": "UP",
  "components": {
    "mq": "UP",
    "mongodb": "UP",
    "sql": "UP",
    "service_registry": "UP"
  }
}
```

## Data Flow

1. **Receive** order via HTTP POST
2. **Parse & validate** input schema
3. **Query MongoDB** for validation rules (counterparty, product)
4. **Check risk limits** (notional, quantity, settlement)
5. **Fetch reference data** from SQL (holidays, settlement rules)
6. **Log validation** event to SQL (compliance)
7. **Publish** to MQ if valid, else return error
8. **Return** 202 Accepted with orderId

## Error Handling

| Error | Action | Retry? |
|-------|--------|--------|
| MQ publish fails | Log to SQL; return 503 | Yes (exponential backoff) |
| MongoDB unavailable | Return 503 Service Unavailable | Yes (circuit breaker) |
| SQL write fails | Log warning; continue publish | No (best-effort) |
| Safeguard auth fails | Service startup fails | Manual restart required |

## Monitoring & Observability

### Metrics
- `order_validation_total` — Counter by status (valid, rejected, error)
- `order_validation_duration_ms` — Histogram of validation time
- `mq_publish_errors_total` — Failed publishes
- `mongodb_query_duration_ms` — Rule lookup latency

### Logs
- `order_validate.log` — All orders processed
- `validation_rules.log` — Rule cache hits/misses
- `mq_errors.log` — MQ connectivity issues

### Traces
- OpenTelemetry: Request ID propagated through all services
- Span tags: `orderId`, `counterparty`, `symbol`, `side`

## Security

- **Credentials:** Safeguard A2A for SQL; mTLS certs for MongoDB & MQ
- **Validation Rules:** Read-only at runtime; updated via admin API
- **Audit:** All validation decisions logged with timestamps & user context
- **Rate Limiting:** 1000 req/sec per counterparty
- **TLS:** 1.3+; mutual authentication required for MQ & Mongo

## Runbook

### Order Stuck in Validation
```bash
# Check service health
curl http://order-validate:8080/health

# Check MQ connectivity
mqsilist TRADE.VALIDATED.ORDERS

# Check MongoDB connection
mongo --tls --tlsCAFile ca.pem --host mongo.internal
```

### High Rejection Rate
```bash
# Check validation rules are up-to-date
curl http://order-validate:8080/rules?counterparty=ACME-TRADING

# Check risk limits in MongoDB
db.validation_rules.find({counterparty: "ACME-TRADING"})
```

### Cert Expiry Approaching
```bash
# Check cert expiry
openssl x509 -enddate -noout -in /etc/certs/mq-client.pem

# Replace before expiry
# Restart service after cert update
```
