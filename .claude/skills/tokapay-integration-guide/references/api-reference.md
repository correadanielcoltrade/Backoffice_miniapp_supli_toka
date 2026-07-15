# API Reference — Tokapay POS Integration

**Base URL**: `https://openapi.paypay.mx/` (UAT de este proyecto: `https://openapi.uat.toka.whalecloud.ltd`)
**All requests**: POST, JSON body, signed headers required

## Required Headers (All APIs)

| Header | Required | Example |
|---|---|---|
| Signature | Yes | `algorithm=RSA256, keyVersion=1, signature=****` |
| Client-Id | Yes | Your assigned Client ID |
| Request-Time | Yes | Unix timestamp in milliseconds |
| Content-Type | No | `application/json; charset=UTF-8` |

Always verify the response `Signature` header before processing.

---

## Result Object (All Responses)

| Field | Type | Description |
|---|---|---|
| resultStatus | String | `S`=Success, `F`=Failed, `U`=Unknown, `A`=Accepted/Processing |
| resultCode | String | Specific code |
| resultMessage | String | Human-readable message |

**Key distinction**: `resultStatus` = did the API call succeed? `paymentStatus` = did the payment transaction succeed? **These are different.**

---

## 1. Create Payment Order — `POST /v1/acquiring/payment/create`

For **CsB Static** and **BsC (Payment Code)**.

| Field | Type | Req | Description |
|---|---|---|---|
| productCode | String | M | `CSB_DIRECTPAY_OFFLINE_TERMINALQR` (Static) or `BSC_PAYMENT_CODE` (BsC) |
| shopId | String | M | Provided by Tokapay |
| terminalId | String | M | Provided by Tokapay |
| paymentCode | String | C | **BsC only** — code scanned from user's app |
| order.orderTitle | String | M | Shown on cashier page (max 256) |
| order.merchantTransId | String | M | Unique merchant transaction ID (max 64) |
| order.orderAmount.value | String | M | Integer in centavos (1503 = 15.03 MXN) |
| order.orderAmount.currency | String | M | e.g. `MXN` |
| order.expiryTime | String | O | `YYYY-MM-DD hh:mm:ssZ` — defaults to 15 min |
| order.allowPantryCard / allowFuelCard | String | O | `Y`/`N` |

Response: `result`, `paymentId` (**store for polling/refund**), `merchantTransId`.

Errors: `20000006` A accept · `20000002` param illegal · `20000003` client id invalid · `20000004` signature wrong · `20000005` access denied · `20030001` repeated submission · `20030003` amount exceeds limit (100,000 pesos) · `20030005` shop/terminal doesn't exist · `20030006` **terminal has unpaid orders** · `20030012` no valid contract · `20030014` payment code invalid

---

## 2. Create Dynamic QR Code — `POST /v1/acquiring/qr/create`

For **CsB Dynamic**. `productCode: CSB_DIRECTPAY_OFFLINE_STANDARD`.

Response adds `qrCode` (string → render as QR image). QR expires in **15 minutes**.

---

## 3. Payment Result Inquiry — `POST /v1/acquiring/payment/inquiry`

**Poll every 5 seconds. Keep polling on `U` or network errors.**
Also used by **Mini-Program** payments.

Request: `paymentId` (M).

Response: `paymentId`, `paymentRequestId` (= merchant's merchantTransId), `paymentAmount`, `paymentTime`, `paymentCreateTime`, `paymentStatus`, `paymentResultCode`, `paymentResultMessage`, `paymentMethod`, `cardNumber` (masked).

| paymentStatus | Meaning | Action |
|---|---|---|
| PROCESSING | Not yet paid | Keep polling |
| SUCCESS | Payment completed | Finalize transaction |
| FAILED | Canceled or timed out | Handle failure |

| paymentResultCode | Meaning |
|---|---|
| 20000000 | Paid successfully |
| 20000003 | Awaiting payment |
| 20030105 | Order was canceled |
| 20030106 | Order timed out |

API errors: `20030101` order doesn't exist.

---

## 4. Close Payment Order — `POST /v1/acquiring/payment/close`

Cancel a pending order. **Required if a terminal has an unpaid order before creating a new one.**
Request: `paymentId`.
Errors: `20030301` doesn't exist · `20030302` already closed · `20030303` already succeeded → use Refund instead.

---

## 5. Refund Apply — `POST /v1/acquiring/refund/apply`

| Field | Type | Req | Description |
|---|---|---|---|
| paymentId | String | M | Original Tokapay payment ID |
| refundRequestId | String | M | Unique refund ID from merchant (**store this**) |
| refundAmount.value | String | M | In centavos |
| refundAmount.currency | String | M | e.g. `MXN` |
| refundReason | String | O | |

Response: `refundId` → use for Refund Result Query.

Errors: `20000006` A processing → poll · `20030201` original order doesn't exist · `20030202` amount illegal · `20030205` original not successfully paid · `20030206` exceeds original · `20030207` existing in-progress refund · `20030211` partial refund not allowed · `20030212` user deleted account

---

## 6. Refund Result Query — `POST /v1/acquiring/refund/inquiry`

Request: `refundId` (M), `refundRequestId` (O).
Response: `refundStatus` (`PROCESSING`/`SUCCESS`/`FAILED`), `refundResultCode`, `refundTime`, `refundAmount`.

---

## 7. Get Recon File Link — `POST /v1/acquiring/recon/get`

Request: `reconDate` (`YYYY-MM-DD`), `settlePeriod` (`day` or `hour`).
Response: `fileUrls` — list of S3 HTTPS links. Empty = file not yet generated, try later.

---

## Product Code Reference

| Product Code | Flow | API |
|---|---|---|
| `CSB_DIRECTPAY_OFFLINE_TERMINALQR` | CsB Static | Create Payment Order |
| `CSB_DIRECTPAY_OFFLINE_STANDARD` | CsB Dynamic | Create Dynamic QR Code |
| `BSC_PAYMENT_CODE` | BsC / Payment Code | Create Payment Order (with paymentCode) |
| `MINI_PROGRAM_DIRECT_PAY` | Mini-Program | `POST /v2/acquiring/miniprogram/create` |

---

## IT Best Practices

**Idempotency**: `merchantTransId` and `refundRequestId` must be globally unique. On retry, reuse the **same** ID to avoid duplicates (`20030001` confirms dedup works).

**Error handling**:
| resultStatus | Action |
|---|---|
| `S` | Success → proceed |
| `F` | Failure → read resultCode |
| `U` | Unknown → **POLL**. Never assume. |
| `A` | Accepted/Processing → **POLL** for final result |
| Network timeout | **POLL**. Always. |

**Signature**: ALWAYS verify response and webhook signatures before processing. Failure to verify opens the system to spoofed payment confirmations.

**Order lifecycle**: `[Created] → [PROCESSING] → [SUCCESS] or [FAILED/CLOSED]`. Once SUCCESS, only Refund is possible.
