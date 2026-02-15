# order-entry Service

**Alias:** orderPlaced / orderEntry

## Purpose
Consumes validated orders from MQ, persists them to SQL database, caches order status in Aerospike, and calls OrderRouter API to obtain routing decisions.

## Architecture

```
MQ Message (TRADE.VALIDATED.ORDERS)
    ↓
┌──────────────────────────────────┐
│  MQ Consumer                     │
│  - Listen on VALIDATED.ORDERS    │
│  - Parse JSON/Avro               │
│  - Idempotency check (orderId)   │
└──────────┬───────────────────────┘
           ↓
┌──────────────────────────────────┐
│  Persist to SQL                  │
│  - Write to orders table         │
│  - Write to order_events table   │
│  - Use transaction (ACID)        │
└──────────┬───────────────────────┘
           ↓
┌──────────────────────────────────┐
│  Update Aerospike Cache          │
│  - Key: orderStatus:{orderId}    │
│  - Value: status JSON            │
│  - TTL: 30 days                  │
└──────────┬───────────────────────┘
           ↓
┌──────────────────────────────────┐
│  Call OrderRouter API            │
│  - Lookup endpoint via Registry  │
│  - POST /route with order        │
│  - Receive routing decision      │
└──────────┬───────────────────────┘
           ↓
┌──────────────────────────────────┐
│  Update Order with Route         │
│  - Write route to SQL            │
│  - Update Aerospike              │
│  - Publish to ROUTED.ORDERS MQ   │
└──────────────────────────────────┘
```

## Dependencies

### IBM MQ
- **Queue:** `TRADE.VALIDATED.ORDERS` (consume)
- **Queue:** `TRADE.ROUTED.ORDERS` (produce, optional loop)
- **Protocol:** AMQP with TLS
- **Client Cert:** `/etc/certs/mq-client.pem`
- **Consumer Group:** `order-entry-consumer-group`
- **Offset:** Stored in Aerospike for high availability

### SQL (via Safeguard)
- **Purpose:** Persistent order book
- **Tables:**
  - `orders` — Order header (symbol, side, qty, price, status)
  - `order_events` — Event log (order placed, routed, executed, canceled)
  - `order_routes` — Route decision audit
- **Constraints:**
  - Primary key: `orderId`
  - Foreign key: `orderId` references `orders`
- **Indexes:** orderId, counterparty, status, created_at

### Aerospike
- **Namespace:** `orders_ns`
- **Key Pattern:** `orderStatus:{orderId}`
- **Value Example:**
  ```json
  {
    "orderId": "ORD-20260214-001",
    "status": "PLACED",
    "symbol": "AAPL",
    "side": "BUY",
    "quantity": 100,
    "price": 145.50,
    "route": null,
    "created_at": "2026-02-14T10:30:45Z",
    "updated_at": "2026-02-14T10:30:46Z"
  }
  ```
- **TTL:** 30 days
- **Replication:** 2 copies
- **Auth:** mTLS with client cert at `/etc/certs/aerospike-client.pem`

### Service Registry
- **Purpose:** Discover `order-router` endpoint
- **Lookup:** `registry.lookup("order-router").endpoint`
- **Retry:** 3 attempts with exponential backoff

## Configuration

```yaml
service:
  name: order-entry
  port: 8081
  replicas: 3

mq:
  broker_url: amqp://mq.trading.internal:5672
  consumer_queue: TRADE.VALIDATED.ORDERS
  producer_queue: TRADE.ROUTED.ORDERS
  consumer_group: order-entry-consumer-group
  batch_size: 10
  max_retries: 3
  client_cert: /etc/certs/mq-client.pem

database:
  sql_host: db.trading.internal
  sql_port: 5432
  sql_database: trading_orders
  credentials_source: safeguard
  pool_size: 20
  connection_timeout: 10s

aerospike:
  seed_hosts:
    - aerospike-1.trading.internal:3000
    - aerospike-2.trading.internal:3000
  namespace: orders_ns
  key_pattern: "orderStatus:{orderId}"
  ttl_seconds: 2592000  # 30 days
  client_cert: /etc/certs/aerospike-client.pem
  replication_factor: 2

service_registry:
  endpoint: registry.trading.internal:8090
  lookup_interval: 5m
  router_service: order-router

idempotency:
  store: aerospike  # or redis
  ttl: 86400  # 24 hours
```

## API Endpoints

### GET /health
Health check with component status.

**Response:**
```json
{
  "status": "UP",
  "components": {
    "mq": "UP",
    "sql": "UP",
    "aerospike": "UP",
    "service_registry": "UP"
  }
}
```

### GET /order/{orderId}
Retrieve order status.

**Response:**
```json
{
  "orderId": "ORD-20260214-001",
  "status": "ROUTED",
  "symbol": "AAPL",
  "side": "BUY",
  "quantity": 100,
  "price": 145.50,
  "route": "NASDAQ-EXECUTION-1",
  "created_at": "2026-02-14T10:30:45Z",
  "routed_at": "2026-02-14T10:30:48Z"
}
```

### POST /order
Create order manually (for testing).

**Request:**
```json
{
  "orderId": "TEST-001",
  "symbol": "MSFT",
  "side": "SELL",
  "quantity": 50,
  "price": 420.00
}
```

## Data Flow

1. **Consume** message from `TRADE.VALIDATED.ORDERS`
2. **Extract** orderId and check idempotency store
3. **Begin transaction** on SQL
4. **Insert** order row into `orders` table
5. **Insert** event row into `order_events` (status: PLACED)
6. **Commit** transaction
7. **Write** to Aerospike with key `orderStatus:{orderId}`
8. **Lookup** OrderRouter endpoint from Service Registry
9. **Call** OrderRouter POST /route with order details
10. **Receive** routing decision (e.g., "NASDAQ-EXECUTION-1")
11. **Update** order in SQL with route
12. **Update** Aerospike cache with route
13. **Publish** to `TRADE.ROUTED.ORDERS` (optional)
14. **Acknowledge** MQ message

## Error Handling

| Scenario | Action | Idempotent? |
|----------|--------|-------------|
| SQL write fails | Rollback; retry order | Yes (stored in Aerospike) |
| Aerospike unavailable | Log warning; continue | No (read may miss cache) |
| OrderRouter API timeout | Retry 3x; mark for manual review | No (may route twice) |
| MQ acknowledge fails | Requeue; may process again | Handled by idempotency |

**Idempotency Strategy:**
- Store (orderId, messageId) in Aerospike for 24h
- If orderId exists, skip processing and ack immediately
- Prevents duplicate order entries if MQ delivers twice

## Monitoring & Observability

### Metrics
- `orders_consumed_total` — Total orders from MQ
- `orders_routed_total` — Orders successfully routed
- `order_entry_latency_ms` — Histogram from consume to route
- `sql_write_errors_total` — DB write failures
- `router_api_latency_ms` — OrderRouter call duration
- `aerospike_write_latency_ms` — Cache write latency

### Logs
- `order_entry.log` — All orders processed
- `router_calls.log` — OrderRouter requests & responses
- `sql_errors.log` — Database errors

### Traces
- OpenTelemetry with orderId, messageId
- Spans: [Consume] → [SQL Write] → [Aerospike Write] → [Router Call]

## Security

- **Credentials:** Safeguard A2A for SQL username/password
- **Certs:** mTLS for MQ, Aerospike (client cert + key)
- **Idempotency:** Secure token to prevent replay
- **Rate Limits:** 10K orders/sec per instance
- **Audit:** All state changes logged with timestamps

## Operational Notes

### Order Stuck in Cache
Orders persist in Aerospike for 30 days. Monitor for stale orders:
```bash
# Check Aerospike for expired orders
aql> SELECT * FROM orders_ns WHERE created_at < (now - 2592000)
```

### OrderRouter Outage
If OrderRouter is unavailable:
- Orders marked as "PENDING_ROUTE" in SQL
- Scheduled retry job processes every 5 minutes
- Manual routing available via admin API

### Scaling
- Horizontal: Add replicas (each subscribes to MQ consumer group)
- Consumer group auto-balances partitions
- Aerospike replication ensures cache availability

## Runbook

### Check Order Status
```bash
curl http://order-entry:8081/order/ORD-20260214-001
```

### Verify MQ Queue Depth
```bash
mqsi queue-depth TRADE.VALIDATED.ORDERS
```

### Clear Idempotency Cache (Use Caution!)
```bash
aerospike> REMOVE orderStatus:ORD-20260214-001  # Expires after 24h automatically
```

### Monitor SQL Table Size
```sql
SELECT table_name, pg_size_pretty(pg_total_relation_size(table_name))
FROM information_schema.tables
WHERE table_name IN ('orders', 'order_events')
ORDER BY pg_total_relation_size(table_name) DESC;
```
