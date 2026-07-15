# Settlement & Reconciliation Guide

## Process Overview
1. Transactions occur throughout the day
2. Tokapay generates settlement files per the agreed strategy
3. Files placed on S3
4. Merchant downloads and reconciles
5. Finance initiates payment to merchant bank account

---

## Settlement Strategies

| Strategy | Behavior |
|---|---|
| D+0 (Hourly) | Settlement statement generated every hour |
| T+1 | Initiated at a set time the next calendar day (e.g. 5:00 AM) |
| T+4, T+7, T+N | Same as T+1 but N days after the transaction day |

## Service Fee Settlement Modes

| Mode | How it works |
|---|---|
| **Gross** | Full amount settled; fee invoiced separately |
| **Net** | Fee deducted before transfer; merchant receives net |

> The fee settlement mode can be edited **once per day**, effective **next day**.

---

## Reconciliation Files

- **Daily**: generated on T+1 for day T. CSV on S3. `POST /v1/acquiring/recon/get` with `settlePeriod: "day"`.
- **Hourly**: generated on H+1. `settlePeriod: "hour"` returns one file per hour of the requested day.

```json
// Request
{ "reconDate": "2024-01-10", "settlePeriod": "hour" }
// Response: array of S3 HTTPS links.
// Empty fileUrls = not generated yet — retry later.
```

---

## Reconciliation File Fields (CSV)

| Field | M/O | Description |
|---|---|---|
| SETTLE_BATCH_ID | M | Settlement batch identifier |
| TXN_ID | M | Tokapay's transaction ID |
| TXN_TYPE | M | `ACQUIRING_ORDER` or `REFUND` |
| MERCHANT_TRANS_ID | M | Merchant's own transaction ID |
| MID | M | Tokapay-assigned Merchant ID |
| SHOP_ID / TERMINAL_ID | M | Store / terminal |
| MERCHANT_NAME | M | Official merchant name |
| TXN_AMOUNT | M | Gross amount |
| TXN_FEE | M | Commission charged (always positive) |
| SETTLE_AMOUNT | M | Net amount after fee |
| TXN_CURRENCY | M | 3-letter ISO (MXN) |
| CHARGED | M | Whether fee was charged (Y) |
| TXN_DATE | M | ISO-8601 with timezone |
| SETTLE_DATE | M | `YYYYMMDD` |
| ORIGINAL_TXN_ID / ORIGINAL_TXN_DATE | C | For refund rows |
| PAY_METHOD | O | VIRTUAL_ACCOUNT, PHYSICAL_CARD, BALANCE |

`SETTLE_AMOUNT = TXN_AMOUNT - MERCHANT_COMMISSION` (both for orders and refunds).

---

## Dispute Process
1. Merchant prepares dispute with specific transaction evidence
2. Sends by **email** to the Toka business operations team
3. Toka ops + bank investigate
4. Adjustments made

---

## Best Practices
- **Reconcile daily** against the T+1 file
- **Match on** `MERCHANT_TRANS_ID` (yours) ↔ `TXN_ID` (Tokapay's)
- **Watch for gaps**: any transaction in your records missing from the file should be investigated
- **Refund rows**: `TXN_TYPE = REFUND`, linked via `ORIGINAL_TXN_ID`
- **File not available**: empty S3 link → retry later (especially hourly files right after the hour)
- Your `merchantTransId` is the **bridge** between Tokapay's system and yours — store it against every transaction
