# POS Integration: Payment Flows

## CsB Static Code Flow

Each merchant terminal has a fixed, printed QR. The customer scans it and the Tokapay app loads a pending order.

**Best for**: multi-terminal merchants (supermarkets, retail chains).
**Constraint**: only **ONE pending order per terminal** at a time.

1. **Pre-checkout**: `POST /v1/acquiring/payment/create` with `productCode: CSB_DIRECTPAY_OFFLINE_TERMINALQR`, `shopId`, `terminalId`, `order.merchantTransId` (unique), `order.orderAmount.value` (centavos). → returns `paymentId`, store it.
2. **Customer scans** the terminal's static QR; Tokapay looks up the latest pending order.
3. **Customer pays** in the Tokapay app.
4. **Poll** `POST /v1/acquiring/payment/inquiry` with `paymentId`, every 5s.
   - `SUCCESS` → finalize · `FAILED` → close/handle · `U`/timeout → keep polling
5. **Alternative**: provide a `notifyUrl` webhook for push notification.

> If a terminal has an unpaid order, **close it first** (error `20030006`). Tokapay sends the static QR to the merchant offline.

---

## CsB Dynamic Code Flow

Merchant generates a new QR per transaction, shown on a screen.

**Best for**: digital displays, per-transaction amounts.

1. **At checkout**: `POST /v1/acquiring/qr/create` with `productCode: CSB_DIRECTPAY_OFFLINE_STANDARD`, `order.merchantTransId`, `order.orderAmount.value`. → returns `qrCode` + `paymentId`.
2. **Display** the `qrCode` string as a QR image. **Expires in 15 minutes.**
3. **Customer scans** and pays.
4. **Poll** `/v1/acquiring/payment/inquiry` every 5s.

> Set `order.expiryTime` greater than the QR expiry if the order should outlast the QR. Re-generate with a **new** `merchantTransId` if expired.

---

## BsC — Payment Code (Business Scans Customer)

The customer shows their personal payment barcode; the merchant scans it.

**Best for**: high-speed checkout (coffee shops, convenience stores).

1. **Cashier scans** the customer's payment code.
2. **Create order**: `POST /v1/acquiring/payment/create` with `productCode: BSC_PAYMENT_CODE`, `paymentCode` (**required for BsC**), `shopId`, `terminalId`, `order.*`.
3. **Payment processes** immediately.
4. **Poll** `/v1/acquiring/payment/inquiry` every 5s.

> The customer's payment code **expires in 1 minute** — scan promptly. If the customer deleted their account, refund is impossible (`20030212`).

---

## Refund Flow (All POS Types)

Full and partial refunds (partial depends on contract). Max 7 days after transaction (configurable).

1. `POST /v1/acquiring/refund/apply` with `paymentId`, `refundRequestId` (unique, store it), `refundAmount.value`/`currency`.
2. Handle response: `S` → done · `A` → poll · `U`/timeout → poll · `F` → handle failure.
3. Poll `POST /v1/acquiring/refund/inquiry` with `refundId` every 5s until `SUCCESS`/`FAILED`.

> Once you invoke a refund you **MUST** obtain a final result before updating your records. Never assume based on a timeout.

---

## IT Best Practices

### Idempotency
- `merchantTransId` globally unique per payment order (max 64 chars)
- `refundRequestId` globally unique per refund attempt
- On retry, reuse the **same** ID (error `20030001` if fields differ — confirms dedup works)

### Error Handling
| Scenario | Action |
|---|---|
| `resultStatus: S` | Success → proceed |
| `resultStatus: F` | Failure → read resultCode |
| `resultStatus: U` | Unknown → **POLL**. Never assume. |
| `resultStatus: A` | Accepted/Processing → **POLL** |
| Network timeout | **POLL**. Always. |

### Signature Verification
- ALWAYS verify response **and webhook** signatures before processing business logic.
- Failure to verify opens the system to **spoofed payment confirmations**.

### Order Lifecycle
```
[Created] → [PROCESSING] → [SUCCESS] or [FAILED/CLOSED]
```
PROCESSING can be closed via Close Payment Order. Once SUCCESS, only Refund. Once FAILED/CLOSED, terminal — create a new order.

### Key Exchange Checklist
- [ ] Merchant generates RSA key pair
- [ ] Merchant sends **public key** to Tokapay (email)
- [ ] Tokapay sends **their public key** to merchant
- [ ] Merchant stores Toka's public key (verify responses) + own private key (sign requests)
- [ ] **Never share private keys**
