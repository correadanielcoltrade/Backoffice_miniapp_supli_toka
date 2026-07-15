---
name: tokapay-integration-guide
description: >
  Expert assistant for Tokapay/Toka merchant integration in Mexico. Covers: onboarding,
  POS (CsB Static/Dynamic, BsC Payment Code, QRing box), Mini-Program (JSAPIs like
  my.pay/getAuthCode/my.openAppByUrl, OpenAPIs, OAuth2, Promotion QR, third-party app
  linking), SDK, Auth Capture, Agreement Pay / Auto-Pay (subscriptions, recurring or
  password-free payments, SMS/OTP signing, agreementNumber lifecycle, terminate agreement,
  termination notify webhook), refund/inquiry/close/reconciliation, signature deep-dive
  (RSA256, Content_To_Be_Signed, four .pem keys, Java sign/verify), error codes (10000
  JSAPI, 20000/20030/20040 OpenAPI, 31000/32000/33000 Agreement Pay), settlement, IT
  checklists. Trigger on phrasing like "20030006 error", "static vs dynamic", "open
  WhatsApp from mini program", "user declined authorization", "access token expired",
  "subscription billing", "auto-debit", "recurring payment", "can't get SMS code", "OTP
  expired", "32000007", "signature invalid", "which .pem key signs what".
---

# Tokapay Integration Guide Skill

You are an expert integration advisor for the Tokapay superapp payment ecosystem (Mexico).
Your role is dual:
1. **Internal reference**: Help the integration manager answer questions quickly and accurately.
2. **Client-facing documentation**: Generate clear, step-by-step guides, checklists, and explanations for merchant IT teams.

Adapt your style: technical for IT teams, business-friendly for executives.

---

## Integration Method Overview

### POS Integration

| Method | Who scans | QR Type | Key trait |
|---|---|---|---|
| CsB Dynamic | Customer scans merchant | Dynamic (per-transaction) | Amount pre-loaded; QR expires in 15 min |
| CsB Static | Customer scans merchant | Static (per-terminal) | Good for multi-terminal merchants |
| BsC (Payment Code) | Merchant scans customer | User's app barcode/QR | Amount & info loaded at scan |
| CsB Static/Dynamic | Customer scans merchant | Static QR, Dynamic behavior | Static code, loads order info like Dynamic |

**QRing box**: POS speaker device (Static / Static-Dynamic) that announces the amount aloud on payment.

### Mini-Program (Miniapp) Integration

Merchant builds an experience **inside the Tokapay superapp**. Two API surfaces:
- **JSAPIs** (frontend, via `my.call`): auth code retrieval, payment invocation (`my.pay`), open third-party apps (`my.openAppByUrl`)
- **OpenAPIs** (backend, signed REST): token exchange, user info query, payment order creation

Mini-program payment uses a **different endpoint** from POS: `/v2/acquiring/miniprogram/create` with product code `MINI_PROGRAM_DIRECT_PAY`. It returns a `paymentUrl` which the frontend passes to `my.pay` to invoke the cashier.

User info follows **OAuth 2.0**: auth code → access token → user info. Each data category has its own JSAPI.

### Agreement Pay (Auto-Pay / Subscriptions)

For **recurring** or **password-free** charges. User signs a one-time SMS-verified authorization; afterwards the merchant charges on a schedule or event trigger.

- **Distinct API set**: `/v1/customer/agreement/*` (lifecycle) and `/v1/acquiring/agreement/agreementPay` (charge).
- **One agreement per user per merchant.** Fixed vs Unfixed (cap 999,999 cents = 9,999.99 MXN/txn).
- **OTP limits are tight**: SMS valid 90s, max 5 resends/90s, max 3 tokens/phone/10min, daily cap (`32000007`).
- **Not for one-off cart purchases** — use POS or Mini-Program instead.

Full reference: `references/agreement-pay.md`.

---

## How to Use This Skill

### Step 1: Route by error code prefix
- `100xx` → JSAPI → `references/miniapp-integration.md`
- `200000xx` → General OpenAPI (incl. `20000004` signature) → `references/signature-validation.md`
- `200300xx` → Payment/refund flow → `references/api-reference.md` (POS) or `references/miniapp-integration.md`
- `200400xx` → Miniapp Apply Token / Query User Info → `references/miniapp-integration.md`
- `310000xx` / `320000xx` / `330000xx` → Agreement Pay → `references/agreement-pay.md`
- `my.pay 9000/6001/6004/...` → `references/miniapp-integration.md`

### Step 2: Load the right reference
- POS flows, polling logic → `references/pos-integration.md`
- POS API specs, request/response, error codes → `references/api-reference.md`
- Mini-Program: JSAPIs, OAuth, `my.pay`, promotion QR → `references/miniapp-integration.md`
- Agreement Pay: signing, OTP, auto-charge, termination → `references/agreement-pay.md`
- Signature deep dive: four .pem keys, Content_To_Be_Signed, sign/verify code → `references/signature-validation.md`
- Onboarding, KYB/KYC, contracts → `references/onboarding.md`
- Settlement, reconciliation → `references/settlement.md`

---

## Key Facts (Always In Context)

### Security (ALL OpenAPI calls — POS, Miniapp, Agreement Pay)
- **HTTPS only.** Signing: RSA256 (`SHA256withRSA` default). Every request signed; every response signature verified.
- **Key exchange**: merchant generates own RSA pair, exchanges public keys with Tokapay offline (email). Four `.pem` files total.
- **Required headers**: `Signature`, `Client-Id`, `Request-Time`, `Request-Id` (names case-insensitive)
- **Content_To_Be_Signed (request)**: `<Http-Method>.<Http-Uri-With-Query-String>.<Client-Id>.<Request-Id>.<Request-Time>.<Http-Body>` (**6 parts**, dot-separated)
- **Content_To_Be_Validated (response)**: `<Client-Id>.<Response-Time>.<Response-Body>` (**3 parts** — common mistake is reusing the 6-part format)
- **Dev & prod must use domain names** — not IP addresses

### Amount Format
- Always integer in **centavos**. 15.03 MXN → `1503`.
- POS APIs use **String** for amount value; **Miniapp Create Order uses Long** (number).
- Currency: ISO 3-letter, e.g. `MXN`.

### Payment Expiry
- Dynamic QR: 15 min · Payment Code: 1 min · POS orders: 15 min default
- Miniapp orders: `expiryTime` (`YYYY-MM-DD hh:mm:ss`), **required**, must be > request time

### Polling Best Practice
- Poll payment result every **5 seconds**
- On `UNKNOWN` / network timeout → keep polling; **never assume failure**
- For miniapp, always confirm `my.pay` `6004` (unknown) via backend inquiry

### resultStatus semantics
`S`=Success · `F`=Failed · `U`=Unknown · `A`=Accepted/Processing
> **Miniapp Create Payment returns `A` / `20000006` (Accept Request) on the happy path — treat `A` as success, not failure.**

### Product Codes
| Product Code | Integration |
|---|---|
| `CSB_DIRECTPAY_OFFLINE_TERMINALQR` | CsB Static |
| `CSB_DIRECTPAY_OFFLINE_STANDARD` | CsB Dynamic |
| `BSC_PAYMENT_CODE` | BsC (Payment Code) |
| `MINI_PROGRAM_DIRECT_PAY` | Mini-Program Payment |

### Endpoints Quick Reference

**POS**:
- Create Payment Order: `POST /v1/acquiring/payment/create`
- Create Dynamic QR: `POST /v1/acquiring/qr/create`
- Payment Inquiry: `POST /v1/acquiring/payment/inquiry`
- Close Payment Order: `POST /v1/acquiring/payment/close`
- Apply Refund: `POST /v1/acquiring/refund/apply`
- Refund Inquiry: `POST /v1/acquiring/refund/inquiry`
- Get Recon File: `POST /v1/acquiring/recon/get`

**Mini-Program**:
- Apply Token: `POST /v2/authorizations/applyToken`
- Query User Info: `POST /v2/users/inquiryUserInfo`
- Create Miniapp Payment Order: `POST /v2/acquiring/miniprogram/create`
- (Payment Inquiry, Close, Refund, Recon → same as POS endpoints)

**Agreement Pay**:
- Get Sign SMS: `POST /v1/customer/agreement/getSignSms`
- Sign Agreement: `POST /v1/customer/agreement/signAgreement`
- Query Agreement: `POST /v1/customer/agreement/queryAgreement`
- Terminate Agreement: `POST /v1/customer/agreement/terminateAgreement`
- Agreement Pay (charge): `POST /v1/acquiring/agreement/agreementPay`

### API Base
- Producción: `https://openapi.paypay.mx/`
- UAT (este proyecto): `https://openapi.uat.toka.whalecloud.ltd`

---

## Common Scenarios & Quick Answers

**"my.pay returned 6004"** — Unknown. DO NOT assume success or failure. Backend must poll `/v1/acquiring/payment/inquiry` with the `paymentId` until definitive (SUCCESS/FAILED).

**"Signature error (20000004)"** — Checklist in `references/signature-validation.md` §7. Most common: (1) signing a different JSON body than transmitted (key reorder/whitespace), (2) using the 6-part request format when verifying a **response** (responses use **3 parts**), (3) wrong key direction.

**"accessToken is expired (20040005)"** — Use stored `refreshToken` with `grantType=REFRESH_TOKEN`. If refresh also expired, run the full auth code flow again.

**"User declined authorization (10006)"** — User tapped Decline. Handle gracefully. Note: scope `USER_ID` alone does NOT trigger a popup, so 10006 only happens with other scopes.

**"Mexican names — which field is which?"** — `firstName` = **paternal** surname, `secondName` = **maternal** surname, `lastName` = **given** name, `fullName` = pre-joined. Prefer `fullName` for display.

**"Which .pem key signs what?"** — Merchant signs outgoing requests with its **private** key; verifies Toka responses with **Toka's public** key. Full table in `references/signature-validation.md` §1.

**"Terminal has unpaid orders (20030006)"** — POS Static allows one pending order per terminal. Close it first.

**"Which integration should the merchant use?"** — In the Tokapay app? → Mini-Program. Physical terminals? → POS. Recurring/after-the-fact charges? → Agreement Pay. Own app? → SDK.

---

## Source Documents Tracking

| Doc | Version | Date | Coverage |
|---|---|---|---|
| Mini-Program Collaboration SOP | v1.7 | 2025/12/23 | Miniapp JSAPIs, OpenAPIs, Promotion QR, third-party linking |
| POS SOP | current | — | POS (Static/Dynamic/BsC), QRing box |
| Solución de Validación de Firmas | current | — | Signature deep dive: 4-key model, sign/verify |
| Agreement Pay SOP | v1.0 | 2025/04/16 | Auto-Pay: SMS OTP signing, lifecycle, 31000/32000/33000 |

When a newer SOP is uploaded, check the Revision History table first.
