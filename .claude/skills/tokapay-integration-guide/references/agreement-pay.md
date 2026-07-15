# Agreement Pay (Auto-Pay / Subscriptions)

Tokapay's **Agreement Pay** — also called **Auto-Pay** or **password-free agreement-based payment**. Charges a user automatically based on a pre-signed authorization, without prompting for a password each time.

> **Source**: *Agreement Pay SOP v1.0* (2025-04-16).
> **Distinct from POS and Mini-Program payments** — separate API set, error codes, and flow.
> **Not for**: one-off purchases where the user is present (cart checkout) — use **POS or Mini-Program** instead.

---

## 1. What It Is

The user signs a one-time SMS-OTP-verified authorization. The merchant receives an `agreementNumber` and can then charge — without further user action — up to the agreed limits.

**Use cases**: monthly subscriptions, usage-based auto-charge at end of service (ride-share, delivery), any "charge later without re-engaging the user" scenario.

---

## 2. End-to-End Flow

### 2.1 Agreement Sign (one-time)
```
User → Merchant App  : Apply for sign authorization
Merchant Page        : Display terms (URL provided by Tokapay)
User → Merchant      : Confirms; taps "Get SMS code"
Merchant → Tokapay   : POST /v1/customer/agreement/getSignSms
Tokapay              : Verifies user info against its records
Tokapay → User       : Sends SMS code
Tokapay → Merchant   : Returns smsToken
User → Merchant      : Inputs the SMS code
Merchant → Tokapay   : POST /v1/customer/agreement/signAgreement
Tokapay → Merchant   : Returns agreementNumber  ← STORE THIS IMMEDIATELY
```

### 2.2 Auto-Charge
```
Trigger (cron / event) → Merchant Backend
Merchant → Tokapay : POST /v1/acquiring/agreement/agreementPay
                     (orderID, agreementNumber, orderAmount, currency)
Tokapay → Merchant : Returns paymentId + result
If pending (33000005): poll acquiringApi.paymentResult.query every 5s
```

> **Never assume the result.** Treat `UNKNOWN`/pending as "keep polling".

### 2.3 Termination (merchant-initiated)
`POST /v1/customer/agreement/terminateAgreement` with `agreementNumber`. Then stop all scheduled charges.

### 2.4 Termination (user-initiated, via webhook)
If a `terminalAgreementNotifyUrl` was registered at signing, Tokapay POSTs to it when the user cancels inside the Tokapay app. The merchant must: stop charges immediately, verify the RSA256 signature, respond HTTP 200.

> Continuing to charge a terminated agreement returns `31000007`. **Stop scheduling immediately.**

### 2.5 Refund
Standard APIs (same as POS): `acquiring.acq.refundApply`, `acquiringApi.refundResult.query`.
Rules: one refund in progress at a time per payment; original must be `SUCCESS`; refundable amount must cover the request.

---

## 3. Roles

| Role | Responsibilities |
|---|---|
| **User** | Submits personal info, confirms terms, enters SMS OTP, can terminate from the Tokapay app |
| **Merchant** | Builds the signing UI (**Tokapay does NOT host it**), calls the 5 agreement APIs, **persists `agreementNumber`**, schedules charges, handles termination webhook |
| **Tokapay** | Verifies user info, issues OTPs, generates `agreementNumber`, processes charges, sends termination notices |

---

## 4. Critical Business Rules

- **One agreement per user per merchant.** A second sign attempt returns `32000002`.
- **Fixed vs Unfixed**:
  - `Fixed` → each charge must equal `amount` **exactly**. Otherwise `33000002`.
  - `Unfixed` → charge can vary but must not exceed `maxAmount`. Otherwise `33000003`.
- **Amounts always in centavos.** `maxAmount` cap: **999,999 cents = 9,999.99 MXN per transaction**.
- Changing Fixed↔Unfixed requires **terminate and re-sign** (with the user).

### OTP / SMS rate limits
| Limit | Value |
|---|---|
| SMS re-send (same `smsToken` + phone) | up to **5 times / 90 seconds** |
| `smsToken`s issued per phone | up to **3 / 10 minutes** |
| SMS code validity | **90 seconds** |
| Daily attempt cap | Hitting it → `32000007` (retry tomorrow) |

### Mexican naming
`firstName`/`firstSurname` = **paternal** surname · `secondSurname` = **maternal** surname · `name` = given name(s) · `curp` = optional but improves match accuracy.
During `getSignSms`, Tokapay cross-checks name/CURP/phone. Mismatch → `31000003` ("not a Tokapay user") or `31000004` (inactive/invalid).

---

## 5. API Reference

All POST, JSON body, signed headers. Base: `https://openapi.paypay.mx/`

| # | API | Endpoint |
|---|---|---|
| 1 | Get sign SMS | `POST /v1/customer/agreement/getSignSms` |
| 2 | Sign agreement | `POST /v1/customer/agreement/signAgreement` |
| 3 | Query agreement | `POST /v1/customer/agreement/queryAgreement` |
| 4 | Terminate agreement | `POST /v1/customer/agreement/terminateAgreement` |
| 5 | Agreement pay (charge) | `POST /v1/acquiring/agreement/agreementPay` |
| 6 | Payment inquiry | see `api-reference.md` |
| 7–8 | Refund apply / inquiry | see `api-reference.md` |
| 9 | Termination webhook (inbound) | merchant's `terminalAgreementNotifyUrl` (optional) |

### 5.1 getSignSms
Request: `firstSurname` (M), `secondSurname` (O), `name` (M), `curp` (O), `phoneNumber` (M), `agreementAmountFixed` (M: `Fixed`/`Unfixed`), `amount` (O, cents, for Fixed), `maxAmount` (M, cents, ≤999,999), `url` (M, merchant link shown on Toka's agreement page), `serviceDescription` (O), `terminalAgreementNotifyUrl` (O).

Response: `result.smsToken`.

### 5.2 signAgreement
Request: `phoneNumber`, `smsToken`, `smsCode`, `firstSurname`, `name` (M); `secondSurname`, `curp`, `deductionPeriod`, `serviceDescription` (O); `agreementAmountFixed`, `maxAmount`, `url` (M); `amount` (O).

Response: `result.agreementNumber` ← **persist immediately**.

### 5.3 queryAgreement
Request: `firstSurname` (M), `name` (M), plus **at least one** of `phoneNumber` / `userName`. Optional `agreementNumber`.
If it doesn't exist → `31000007`.

### 5.4 terminateAgreement
Request: `agreementNumber` (M). Afterwards `agreementPay` returns `31000007`.

### 5.5 agreementPay
Request: `orderID` (M, merchant-side unique), `agreementNumber` (M), `orderAmount` (M, **cents**, respects Fixed/Unfixed and ≤ `maxAmount`), `currency` (M, `MXN`).
Response: `result.paymentId` (for inquiry/refund).
If `33000005` (processing) → poll `acquiringApi.paymentResult.query` every 5s.

---

## 6. Error Code Index

### 31000xxx — Parameter / user
| Code | Meaning |
|---|---|
| 31000001 | Param {field} is null |
| 31000002 | Param {field} is invalid |
| 31000003 | Not a Tokapay user (name/CURP/phone mismatch) |
| 31000004 | User inactive or invalid |
| 31000005 | Agreement expired |
| 31000007 | User agreement does not exist (terminated or wrong number) |
| 31000010 | No authority to terminate the agreement |
| 31000011 | Phone and username cannot both be empty |

### 32000xxx — Merchant / OTP
| Code | Meaning |
|---|---|
| 32000001 | Merchant account disabled |
| 32000002 | Merchant has signed a contract (user already has an active agreement) |
| 32000003 | Merchant hasn't enabled the Agreement Pay product |
| 32000004 | Wait one minute (OTP rate limit) |
| 32000005 | Attempt limit reached — resend the code |
| 32000006 | Verification code expired (90s window) |
| 32000007 | Max attempts — try again tomorrow (daily cap) |
| 32000008 | Incorrect code, {0} attempt(s) left |
| 32000009 | Exceeds max amount per transaction (`maxAmount` > 999,999 cents) |

### 33000xxx — Payment (Agreement Pay only)
| Code | Meaning |
|---|---|
| 33000001 | Currency not supported (use `MXN`) |
| 33000002 | Amount doesn't match the agreement (Fixed) |
| 33000003 | Amount exceeds the contract limit (> `maxAmount`) |
| 33000004 | Payment failed — insufficient funds |
| 33000005 | Payment is processing → poll |

Shared with POS: `20000000` success, `20030018` user status abnormal.

---

## 7. Common Pitfalls

1. **Forgetting to persist `agreementNumber`.** It only appears once (in `signAgreement`). Recoverable via `queryAgreement`, but that's an extra round-trip.
2. **Continuing to charge after termination.** Check `31000007`; webhook terminations are silent unless you subscribe.
3. **Mixing up `amount` vs `maxAmount`.** Fixed → `amount` (charge exactly). Unfixed → `maxAmount` (charge up to).
4. **OTP UX too aggressive.** Hitting `32000007` locks the user out for the day. Add countdown timers and sensible resend.
5. **Name field confusion.** Split Mexican surnames into the right slots.
6. **Treating Agreement Pay errors like POS errors.** The 31000/32000/33000 families are new and specific.
7. **Wrong signing format.** Same as all OpenAPIs: 6-part request / 3-part response. See `signature-validation.md`.
