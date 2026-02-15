# Trading Platform – System Documentation (Mock)

## Services

### 1) order-validate (OrderGetValidated / orderValidate)
- Publishes to IBM MQ queue: `TRADE.VALIDATED.ORDERS`
- Uses MongoDB via certificate (mTLS) for validation rules & audit.
- Uses SQL via Safeguard (username/password retrieved from Safeguard A2A).
- Uses Service Registry to find `order-entry`.

### 2) order-entry (orderPlaced / orderEntry)
- Consumes IBM MQ: `TRADE.VALIDATED.ORDERS`
- Writes orders to SQL via Safeguard credentials.
- Writes status cache to Aerospike via certificate (mTLS).
- Uses Service Registry to call `order-router`.

### 3) order-router (orderRouter)
- Publishes to IBM MQ: `TRADE.ROUTED.ORDERS`
- Uses MongoDB via certificate (mTLS) for routing policies.
- Uses Aerospike via certificate (mTLS) for routing cache.
- Uses Service Registry to discover `fix-service` and vendor-health.

### 4) fix-service (FIX gateway to vendor)
- Consumes IBM MQ: `TRADE.ROUTED.ORDERS`
- Sends orders to vendor using FIX over TLS (vendor certificate).
- Publishes execution results to IBM MQ: `TRADE.EXECUTIONS` and `TRADE.CONFIRMATIONS`
- Uses SQL via Safeguard for session audit (optional).

### 5) service-registry
- Provides endpoints and metadata for internal services.
- Uses MongoDB via certificate (mTLS) for registry storage.
- Enforces client mTLS CN allowlist.

## Safeguard usage
- SQL credentials are retrieved at startup using Safeguard A2A.
- If SQL passwords rotate in Safeguard, services must either refresh secrets (if supported) or restart safely.

## Certificate usage
- IBM MQ client TLS requires valid client cert + CA chain.
- MongoDB and Aerospike require client mTLS.
- FIX vendor requires vendor-approved client cert + vendor CA.

## Common Failure Scenarios
- MQ cert expired → MQ TLS handshake fails → message publish/consume stops → backlog grows → downstream order flow halted.
- Safeguard API unreachable → services cannot fetch SQL credentials → startup failure or DB auth failures.
- Mongo/Aerospike cert mismatch → mTLS fails → policy/cache unavailable → routing/validation may degrade or fail safe.

## Runbook Quick Checks
- Check `/actuator/health` for MQ/Mongo/SQL/Aerospike components.
- Check MQ depths for `TRADE.VALIDATED.ORDERS`, `TRADE.ROUTED.ORDERS`, DLQ.
- Verify cert expiry dates and CA bundles.
- Validate Safeguard credential retrieval logs at startup.
