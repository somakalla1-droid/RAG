# fix-service

**Alias:** FIX Gateway to Vendor

## Purpose
Consumes routed orders from MQ, communicates with external vendors using FIX protocol over TLS, collects execution results, and publishes confirmations back to the trading platform.

## Architecture

```
Routed Order (TRADE.ROUTED.ORDERS MQ)
    ↓
┌──────────────────────────────────┐
│  MQ Consumer                     │
│  - Consume ROUTED.ORDERS queue   │
│  - Parse order details           │
│  - Extract venue routing info    │
└──────────┬───────────────────────┘
           ↓
┌──────────────────────────────────┐
│  Translate Order to FIX           │
│  - Convert symbol format         │
│  - Map order type (LIMIT, MKT)   │
│  - Add client-specific tags      │
└──────────┬───────────────────────┘
           ↓
┌──────────────────────────────────┐
│  Send via FIX Protocol (TLS)     │
│  - Establish persistent socket   │
│  - Use vendor certificate        │
│  - Heartbeat every 30s           │
└──────────┬───────────────────────┘
           ↓
┌──────────────────────────────────┐
│  Receive FIX Executions          │
│  - Listen for ExecutionReport    │
│  - Partial fills, rejections     │
│  - Status updates                │
└──────────┬───────────────────────┘
           ↓
┌──────────────────────────────────┐
│  Translate to Internal Format    │
│  - Map FIX fields to our schema  │
│  - Parse execution price/qty     │
│  - Capture vendor order ID       │
└──────────┬───────────────────────┘
           ↓
┌──────────────────────────────────┐
│  Persist & Cache Results         │
│  - Write to SQL (audit)          │
│  - Update Aerospike cache        │
│  - Publish confirmations         │
└──────────────────────────────────┘
```

## Dependencies

### IBM MQ
- **Input Queue:** `TRADE.ROUTED.ORDERS`
- **Output Queues:**
  - `TRADE.EXECUTIONS` — Partial fill/full fill events
  - `TRADE.CONFIRMATIONS` — Final execution confirmations
- **Protocol:** AMQP with TLS
- **Client Cert:** `/etc/certs/mq-client.pem`

### FIX Vendor Connection
- **Protocol:** FIX 4.4 (or negotiated version) over TLS 1.3
- **Certificate:** Vendor-specific client cert (signed by vendor CA)
- **Cert Path:** `/etc/certs/vendor-fix-client.pem`
- **CA Bundle:** `/etc/certs/vendor-fix-ca.pem`
- **Hostname:** `fix.vendor.com` (SNI verification required)
- **Port:** 9999 (or negotiated)
- **Persistent Connection:** Maintain long-lived socket with heartbeats
- **Logon:** Username/password in FIX logon message (encrypted)

### SQL (via Safeguard)
- **Purpose:** Audit trail of FIX messages & executions
- **Tables:**
  - `fix_messages_sent` — All FIX messages sent to vendor
  - `fix_messages_received` — All FIX messages from vendor
  - `executions` — Aggregated execution records
  - `execution_audit` — Audit log for compliance
- **Credentials:** Retrieved from Safeguard at startup
- **Retention:** 7 years (regulatory requirement)

### Aerospike (Optional)
- **Key Pattern:** `execution:{vendorOrderId}`
- **Value:** Execution details (status, price, qty filled)
- **TTL:** 7 days (then archived to SQL)
- **Purpose:** Fast execution lookups

## Configuration

```yaml
service:
  name: fix-service
  port: 8083
  replicas: 2
  graceful_shutdown: 60s

mq:
  broker_url: amqp://mq.trading.internal:5672
  inbound_queue: TRADE.ROUTED.ORDERS
  executions_queue: TRADE.EXECUTIONS
  confirmations_queue: TRADE.CONFIRMATIONS
  client_cert: /etc/certs/mq-client.pem
  batch_size: 1
  ack_timeout: 30s

fix:
  vendor:
    name: "ACME-BROKER"
    host: "fix.vendor.com"
    port: 9999
    protocol: "FIX.4.4"
    tls_enabled: true
    client_cert: /etc/certs/vendor-fix-client.pem
    client_key: /etc/certs/vendor-fix-client-key.pem
    ca_bundle: /etc/certs/vendor-fix-ca.pem
    sni_hostname: "fix.vendor.com"
    heartbeat_interval: 30s
    timeout: 60s

  logon:
    username: "TRADING-ACME"
    password_source: safeguard  # Stored in Safeguard
    sender_comp_id: "TRADING-CORP"
    target_comp_id: "ACME-BROKER"

  session:
    reset_sequence: false
    persist_messages: true
    reconnect_strategy: "exponential-backoff"
    max_reconnect_attempts: 10

database:
  sql_host: db.trading.internal
  sql_port: 5432
  sql_database: trading_executions
  credentials_source: safeguard
  pool_size: 10

aerospike:
  enabled: true
  seed_hosts:
    - aerospike-1.trading.internal:3000
  namespace: executions
  ttl_seconds: 604800  # 7 days
```

## API Endpoints

### GET /health
Service health with vendor connection status.

**Response:**
```json
{
  "status": "UP",
  "components": {
    "mq": "UP",
    "fix_vendor_connection": "UP",
    "sql": "UP"
  },
  "fix_connection_details": {
    "connected": true,
    "vendor": "ACME-BROKER",
    "logon_time": "2026-02-14T09:30:00Z",
    "last_heartbeat": "2026-02-14T10:30:45Z",
    "messages_sent": 1250,
    "messages_received": 1248
  }
}
```

### GET /execution/{vendorOrderId}
Retrieve execution details.

**Response:**
```json
{
  "vendorOrderId": "FIX-12345",
  "orderId": "ORD-20260214-001",
  "symbol": "AAPL",
  "side": "BUY",
  "order_qty": 100,
  "executed_qty": 100,
  "average_price": 145.48,
  "execution_status": "FILLED",
  "executions": [
    {
      "exec_id": "E001",
      "exec_qty": 50,
      "exec_price": 145.45,
      "timestamp": "2026-02-14T10:30:46Z"
    },
    {
      "exec_id": "E002",
      "exec_qty": 50,
      "exec_price": 145.51,
      "timestamp": "2026-02-14T10:30:47Z"
    }
  ]
}
```

### POST /order
Manually send an order to vendor (test/override).

**Request:**
```json
{
  "orderId": "ORD-20260214-001",
  "symbol": "MSFT",
  "side": "BUY",
  "qty": 100,
  "price": 420.00,
  "order_type": "LIMIT"
}
```

## FIX Protocol Details

### Logon Message (35=A)
```
8=FIX.4.4|9=100|35=A|49=TRADING-CORP|56=ACME-BROKER|34=1|52=20260214-10:30:45|
108=30|141=Y|... (checksum)
```

### New Order Single (35=D)
```
8=FIX.4.4|9=150|35=D|49=TRADING-CORP|56=ACME-BROKER|
11=ORD-20260214-001|55=AAPL|54=1|38=100|40=2|44=145.50|...
```

### Execution Report (35=8)
```
8=FIX.4.4|9=200|35=8|49=ACME-BROKER|56=TRADING-CORP|
37=FIX-12345|11=ORD-20260214-001|55=AAPL|150=F|39=2|
40=2|150=2|151=0|14=100|17=E001|150=2|39=2|...
```

## Data Flow

1. **Consume** message from `TRADE.ROUTED.ORDERS`
2. **Parse** order details (orderId, symbol, side, qty, price)
3. **Maintain FIX session** with vendor (persistent socket with heartbeats)
4. **Translate** order to FIX message format (NewOrderSingle)
5. **Send** via FIX protocol over TLS
6. **Receive** ExecutionReport messages from vendor
7. **Parse** execution details (partial fills, rejections, status)
8. **Persist** execution to SQL (audit trail)
9. **Update** Aerospike cache with latest execution status
10. **Publish** execution events to `TRADE.EXECUTIONS` MQ
11. **Aggregate** and publish final confirmation to `TRADE.CONFIRMATIONS` when FILLED or REJECTED

## Error Handling

### FIX Connection Failures
- **Action:** Log error, attempt reconnect with exponential backoff (1s, 2s, 4s, ...)
- **Max Attempts:** 10 reconnects over ~17 minutes
- **Orders during outage:** Queued locally; retry on reconnect
- **Monitoring:** Alert if disconnected > 5 minutes

### Execution Rejections
- **FIX Status:** 39=8 (REJECTED)
- **Action:** Log rejection reason; publish to `TRADE.EXECUTIONS` with status REJECTED
- **Order Status:** Marked as REJECTED in SQL; customer notified
- **Retry:** Manual/via admin API only

### Certificate Expiry
- **Check:** Automatic daily (30-day warning)
- **Action:** Rotate cert before expiry (TLS handshake will fail otherwise)
- **Process:** Update `/etc/certs/vendor-fix-client.pem`; service continues (no restart required for TLS session resumption)

## Monitoring & Observability

### Metrics
- `fix_messages_sent_total` — Total FIX messages by type
- `fix_messages_received_total` — Total FIX responses
- `fix_executions_total` — Executions by status (FILLED, PARTIAL, REJECTED)
- `fix_latency_ms` — Time from order send to first execution
- `fix_connection_uptime_pct` — Percentage of time connected
- `execution_price_deviation_bps` — vs. expected (slippage tracking)

### Logs
- `fix_messages.log` — All FIX messages (fields sent/received)
- `executions.log` — Execution events with details
- `vendor_errors.log` — Vendor-specific errors & disconnections
- `audit.log` — Regulatory audit trail

### Traces
- OpenTelemetry: orderId, vendorOrderId, execution status
- Spans: [Receive Order] → [FIX Send] → [Execution Receive] → [MQ Publish]

## Security

- **Credentials:** FIX logon password stored in Safeguard A2A
- **TLS:** 1.3+; mutual authentication required
- **Certificates:** Vendor-approved certs; annual renewal
- **Message Encryption:** FIX messages encrypted over TLS (no additional encryption)
- **Audit:** All FIX messages logged for 7 years (regulatory)
- **Rate Limiting:** No built-in rate limit (vendor-controlled)

## Operational Notes

### Vendor Connection Pool
For multiple vendors, run separate instances:
```yaml
fix-service-1: ACME-BROKER (primary)
fix-service-2: BROKER-B (secondary)
fix-service-3: BROKER-C (backup)
```
Each with separate certs, credentials, MQ subscriptions.

### Testing Against Vendor
Use a test environment:
- Test cert (signed by vendor test CA)
- Test credentials
- Test symbol mappings
- Dry runs (no real execution)

### Execution Price Monitoring
Alert if execution price deviates > 5 basis points from order price:
```bash
# Check recent executions
SELECT orderId, price, average_price, 
  (ABS(average_price - price) * 10000 / price) as slippage_bps
FROM executions
WHERE execution_time > NOW() - INTERVAL '1 hour'
ORDER BY slippage_bps DESC;
```

## Runbook

### Check FIX Connection Status
```bash
curl http://fix-service:8083/health
```

### Get Execution Details for an Order
```bash
curl http://fix-service:8083/execution/FIX-12345
```

### Manually Reconnect to Vendor
```bash
# Service will auto-reconnect, but to force:
# Restart the service
kubectl rollout restart deployment fix-service
```

### Check Cert Expiry
```bash
openssl x509 -enddate -noout -in /etc/certs/vendor-fix-client.pem
```

### Resend an Order to Vendor
```bash
curl -X POST http://fix-service:8083/order \
  -H "Content-Type: application/json" \
  -d '{"orderId": "ORD-20260214-001", ...}'
```

### Query Execution Audit Log
```sql
SELECT * FROM fix_messages_received 
WHERE message_type = 'ExecutionReport' 
  AND timestamp > NOW() - INTERVAL '24 hours'
ORDER BY timestamp DESC;
```
