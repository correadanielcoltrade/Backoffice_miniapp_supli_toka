# Merchant Onboarding Guide & Checklist

Onboarding is handled by the Sales & Marketing team in the Tokapay back-office. The merchant does **NOT** self-register — the Toka team registers on their behalf.

**Flow**: commercial agreement signed offline → Toka enters merchant info → sign product contract → store/device setup → technical integration begins.

---

## Phase 1: Information Collection

### Basic
- [ ] Merchant Display Name (6–40 chars)
- [ ] Merchant Logo (JPG/PNG/JPEG, max 5MB)
- [ ] Merchant Secure Email (used for login/reset)
- [ ] Merchant Secure Mobile (Mexican number)
- [ ] Group (optional)

### KYB — Business License
- [ ] R.F.C. · Company Official Name (matches Constitutive Act) · English Name
- [ ] Merchant Category Code
- [ ] Constitutive Act (PDF, max 5MB)

### KYB — Registration Address
- [ ] Country (Mexico) · Zip · State/City (auto from postcode) · Neighborhood · Street
- [ ] Address Bill — utility bill max 90 days old (max 5MB)

### KYB — Legal Representative
- [ ] Full Name (6–40 chars) · Contact tel/mobile/email (optional)
- [ ] Certification Type (ID or Passport) · Certificate Number (CURP or passport) · Expiry
- [ ] ID/Passport photo (max 2 attachments, ≤5MB each)
- [ ] Power of Attorney (only if authorized representative)

### Financial
- [ ] Settlement Strategy: T+N, D+N, or Hourly
- [ ] Service Fee Mode: **Gross** (invoiced separately) or **Net** (deducted)
- [ ] Bank Account Number · Account Holder's Name · Bank/Branch codes (optional)
- [ ] Proof of Bank Account (max 5MB)

---

## Phase 2: Contract Signing

Services available:
- **CsB Static** — `CSB_DIRECTPAY_OFFLINE_TERMINALQR`
- **CsB Dynamic** — `CSB_DIRECTPAY_OFFLINE_STANDARD`
- **Standard JSAPI Payment (Miniapp)** — `STANDARD_MERCHANT_MINIAPP_DEV`

Contract fields: effective type (immediate/specified date), end date, payment methods, fee formula, max refund days.

**Contract statuses**:
- **Active** — merchant can transact
- **Pending Activation** — signed but effective date not reached; **cannot transact**
- **Expired** — terminated/ended; **cannot transact**

---

## Phase 3: Store & Device Setup

**Store**: merchant code (auto), store type, name (unique per merchant), business hours, contact phone, state + address, images (up to 9), lat/long (optional).

**Device** (Static/Static-Dynamic): Toka adds devices per store; each gets a Device ID and a QR (string or PNG) — the static code printed at the terminal.

**QRing Box**: POS speaker compatible with Static and Static/Dynamic. Announces the amount aloud on payment. **No extra API integration needed.**

---

## Phase 4: Technical Integration Kickoff

**Pre-Integration**:
- [ ] Received **MerchantId** and **ClientId** from Toka IT
- [ ] Received **Tokapay's public key**
- [ ] Generated own RSA key pair (public + private)
- [ ] Sent own **public key** to Tokapay (email)
- [ ] Received SIT (test) credentials: endpoint URL, ClientId, Tokapay SIT public key
- [ ] Knows ShopId(s) / TerminalId(s) (for Static/BsC)

**Validation Before Go-Live**:
- [ ] Created a test payment order
- [ ] Polled for payment result
- [ ] Closed a payment order
- [ ] Applied a refund + queried refund result
- [ ] Signature generation AND verification working (request + response)
- [ ] Unique ID scheme in place (`merchantTransId`)
- [ ] Error handling for all result statuses (S, F, U, A)
- [ ] Polling logic (every 5s, handles U/timeout)
- [ ] Webhook/notify endpoint implemented and tested (if applicable)

**For Mini-Program specifically** (see `miniapp-integration.md`):
- [ ] Mini Program created on the Mini Program Platform
- [ ] Feature permissions applied (User Information, User Payment)
- [ ] Received `appId`
