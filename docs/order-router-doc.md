# order-router Service

**Alias:** orderRouter

## Purpose
Routes orders to appropriate execution venues based on routing policies, caches routing decisions, and publishes routed orders to downstream services.

## Architecture

```
Order from order-entry (HTTP POST /route)
    ↓
┌──────────────────────────────────┐
│  Input Validation                │
│  - Verify order fields           │
│  - Check symbol validity         │
└──────────┬───────────────────────┘
           ↓
┌──────────────────────────────────┐
│  Fetch Routing Policies          │
│  - Query MongoDB routing rules   │
│  - Filter by symbol, side        │
│  - Check venue availability      │
└──────────┬───────────────────────┘
           ↓
┌──────────────────────────────────┐
│  Evaluate Routing Conditions     │
│  - Liquidity preferences         │
│  - Execution cost analysis       │
│  - Smart order routing (SOR)     │
│  - Venue rankings                │
└──────────┬───────────────────────┘
           ↓
┌──────────────────────────────────┐
│  Select Venue                    │
│  - Best execution check          │
│  - Fee calculation               │
│  - Regulatory compliance         │
└──────────┬───────────────────────┘
           ↓
┌──────────────────────────────────┐
│  Cache Decision                  │
│  - Write to Aerospike            │
│  - Key: orderRoute:{orderId}     │
│  - TTL: 24 hours                 │
└──────────┬───────────────────────┘
           ↓
┌──────────────────────────────────┐
│  Publish to MQ                   │
│  - Topic: TRADE.ROUTED.ORDERS    │
│  - Include venue + route details │
└─────────────────────────────────┘
```

## Dependencies

### MongoDB
- **Purpose:** Store routing policies & decision audit
- **Collections:**
  - `routing_policies` — Rules by symbol/side (JSON query format)
  - `routing_audit` — Audit log of all routing decisions
  - `venue_availability` — Real-time venue status
- **Auth:** mTLS with client cert
- **Operations:**
  - Read: O(1) policy lookup by symbol
  - Write: Audit log for compliance

### Aerospike
- **Namespace:** `orders_ns` (shared with order-entry)
- **Key Pattern:** `orderRoute:{orderId}`
- **Value Example:**
  ```json
  {
    "orderId": "ORD-20260214-001",
    "venue": "NASDAQ-EXECUTION-1",
    "route_algorithm": "smart-order-routing",
    "liquidity_score": 0.95,
    "estimated_cost_bps": 1.25,
    "executed_at": "2026-02-14T10:30:48Z"
  }
  ```
- **TTL:** 24 hours
- **Auth:** mTLS

### IBM MQ
- **Queue:** `TRADE.ROUTED.ORDERS`
- **Protocol:** AMQP with TLS
- **Purpose:** Publish routed orders to fix-service & vendor-health
- **Serialization:** JSON/Avro
- **Client Cert:** `/etc/certs/mq-client.pem`

### Service Registry
- **Purpose:** Discover fix-service and vendor-health endpoints
- **Lookups:**
  - `registry.lookup("fix-service").endpoint`
  - `registry.lookup("vendor-health").endpoint`

## Configuration

```yaml
service:
  name: order-router
  port: 8082
  replicas: 2

mongodb:
  uri: mongodb+srv://mongo.trading.internal
  database: trading_routing
  client_cert: /etc/certs/mongo-client.pem
  collections:
    - routing_policies
    - routing_audit
    - venue_availability

aerospike:
  seed_hosts:
    - aerospike-1.trading.internal:3000
  namespace: orders_ns
  key_pattern: "orderRoute:{orderId}"
  ttl_seconds: 86400  # 24 hours
  client_cert: /etc/certs/aerospike-client.pem

mq:
  broker_url: amqp://mq.trading.internal:5672
  routed_orders_queue: TRADE.ROUTED.ORDERS
  client_cert: /etc/certs/mq-client.pem

routing:
  algorithm: "smart-order-routing"  # or "venue-selection", "liquidity-pool"
  max_venues_per_order: 3
  best_execution_check: true
  cost_model: "black-litterman"

service_registry:
  endpoint: registry.trading.internal:8090
  lookup_interval: 5m
```

## API Endpoints

### POST /route
Route an order to a venue.

**Request:**
```json
{
  "orderId": "ORD-20260214-001",
  "symbol": "AAPL",
  "side": "BUY",
  "quantity": 100,
  "price": 145.50,
  "counterparty": "ACME-TRADING"
}
```

**Response (200 OK):**
```json
{
  "orderId": "ORD-20260214-001",
  "venue": "NASDAQ-EXECUTION-1",
  "route_algorithm": "smart-order-routing",
  "liquidity_score": 0.95,
  "estimated_cost_bps": 1.25,
  "published_to_mq": true,
  "timestamp": "2026-02-14T10:30:48Z"
}
```

**Response (400 Bad Request - No Route Found):**
```json
{
  "orderId": "ORD-20260214-001",
  "error": "No routing policy found for symbol INVALID",
  "status": "NO_ROUTE"
}
```

### GET /venues
List available venues and their status.

**Response:**
```json
{
  "venues": [
    {
      "name": "NASDAQ-EXECUTION-1",
      "status": "ONLINE",
      "liquidity_score": 0.95,
      "avg_spread_bps": 0.8,
      "uptime_pct": 99.98
    },
    {
      "name": "NYSE-EXECUTION-1",
      "status": "ONLINE",
      "liquidity_score": 0.92,
      "avg_spread_bps": 1.2,
      "uptime_pct": 99.95
    }
  ]
}
```

### GET /policies/{symbol}
Get routing policies for a symbol.

**Response:**
```json
{
  "symbol": "AAPL",
  "policies": [
    {
      "id": "POLICY-001",
      "condition": { "side": "BUY", "quantity_min": 0 },
      "venues": ["NASDAQ-EXECUTION-1", "NYSE-EXECUTION-1"],
      "weights": [0.6, 0.4]
    }
  ]
}
```

### GET /health
Service health.

**Response:**
```json
{
  "status": "UP",
  "components": {
    "mongodb": "UP",
    "aerospike": "UP",
    "mq": "UP",
    "service_registry": "UP"
  }
}
```

## Data Flow

1. **Receive** POST /route from order-entry
2. **Validate** order fields (symbol, side, qty)
3. **Query MongoDB** for routing policies matching symbol + side
4. **Evaluate policies** (liquidity, cost, regulatory)
5. **Rank venues** based on scoring algorithm
6. **Calculate fees** & estimated execution cost
7. **Select venue** with best execution opportunity
8. **Check venue availability** (via Service Registry + heartbeat)
9. **Write decision** to Aerospike (caching layer)
10. **Publish** to `TRADE.ROUTED.ORDERS` MQ queue
11. **Log audit** trail to MongoDB
12. **Return** routing decision to caller

## Routing Algorithms

### Smart Order Routing (SOR)
- Analyzes multiple venues simultaneously
- Optimizes for: liquidity, spread, execution probability
- Uses machine learning model (black-litterman) for venue ranking
- Returns top-k venues sorted by expected cost

### Venue Selection
- Simple rule-based routing by symbol
- Configurable weights (e.g., 60% NASDAQ, 40% NYSE)
- Deterministic; no randomization

### Liquidity Pool
- Check dark pools & block trading venues first
- Fallback to lit exchanges if no dark pool match
- Risk-averse for institutional orders

## Error Handling

| Error | Action | Fallback |
|-------|--------|----------|
| MongoDB unavailable | Return 503 | Cache venue list in memory |
| No routing policy found | Return 400 "No route" | Manual routing required |
| MQ publish fails | Log error; return 207 Partial | Retry queue |
| Venue unavailable | Select next-best venue | Return multiple options |

## Monitoring & Observability

### Metrics
- `routing_decisions_total` — Total routes by venue
- `routing_latency_ms` — Time to compute route
- `venue_selection_histogram` — Distribution across venues
- `best_execution_failures_total` — Compliance violations
- `aerospike_cache_hits` — Cache hit rate %

### Logs
- `routing.log` — All routing decisions
- `policy_changes.log` — When policies are updated
- `venue_status.log` — Venue availability changes

### Traces
- OpenTelemetry: orderId, symbol, venue, algorithm
- Spans: [Input Validate] → [Policy Lookup] → [Venue Score] → [MQ Publish]

## Security

- **Credentials:** mTLS certs for MongoDB, Aerospike, MQ
- **Policies:** Access control on policy updates (admin only)
- **Audit:** Every routing decision logged with timestamp & user
- **Best Execution:** Compliance checks for regulatory requirements
- **Rate Limiting:** 50K routes/sec per instance

## Operational Notes

### Venue Capacity Limits
Monitor venue queue lengths:
```bash
# Check if venue is reaching capacity
curl http://vendor-health:9090/venues/NASDAQ-EXECUTION-1/queue_depth
# If > 10K orders, increase SOR weight to alternate venue
```

### Routing Policy Updates
Policies are versioned in MongoDB; rollback available:
```bash
# List policy versions
db.routing_policies.find({symbol: "AAPL", _deleted: false})

# Rollback to previous version
db.routing_policies.findByIdAndUpdate(policyId, {version: oldVersion})
```

### Troubleshoot High Execution Costs
```bash
# Check if spread is wider than expected
curl http://order-router:8082/venues | grep avg_spread_bps

# Verify cost model coefficients
db.routing_policies.findOne({symbol: "AAPL"}).cost_model
```

## Runbook

### Check Routing Decision for an Order
```bash
# Get from Aerospike
aerospike> GET orderRoute:ORD-20260214-001
```

### Force Reroute an Order
```bash
# Call /route endpoint again with same orderId
curl -X POST http://order-router:8082/route \
  -H "Content-Type: application/json" \
  -d '{"orderId": "ORD-20260214-001", ...}'
```

### Update Venue Availability
```bash
# Mark venue as offline
db.venue_availability.updateOne(
  {name: "NASDAQ-EXECUTION-1"},
  {$set: {status: "OFFLINE"}}
)
# Routing will skip this venue until status = ONLINE
```

### Check SOR Model Performance
```bash
# Analyze recent routing decisions
db.routing_audit.aggregate([
  {$match: {timestamp: {$gt: new Date(Date.now() - 3600000)}}},
  {$group: {_id: "$venue", count: {$sum: 1}, avg_cost_bps: {$avg: "$estimated_cost"}}}
])
```
