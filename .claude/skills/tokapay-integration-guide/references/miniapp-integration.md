# Mini-Program (Miniapp) Integration

This reference covers the Tokapay Mini-Program ("miniapp") collaboration SOP — for merchants building experiences **inside the Tokapay superapp** rather than scanning QR codes at a physical POS.

> **Source**: Mini-Program Collaboration SOP v1.7 (2025/12/23).
> **Key change in v1.7**: Added Open Third-party App's link JSAPI (`my.openAppByUrl`).

---

## Architecture: JSAPIs vs OpenAPIs

| Surface | Where it runs | Called from | Example |
|---|---|---|---|
| **JSAPI** | Inside the Tokapay app's mini-program container | Mini-program **frontend** (JS) | `my.call('getUserDigitalIdentityAuthCode', {...})` |
| **OpenAPI** | Tokapay backend (HTTP REST, signed) | Mini-program **backend** server | `POST /v2/authorizations/applyToken` |

- JSAPIs get **auth codes** and **trigger UI** (cashier popup, app linking).
- OpenAPIs exchange **auth codes for access tokens**, **create payment orders**, **query user info**.
- **Access tokens MUST stay on the merchant server.** Never return an access token to the frontend.

---

## Request / Response Structure

### Required Request Headers (OpenAPI, all calls)

| Header | Required | Example |
|---|---|---|
| Signature | Yes | `algorithm=RSA256, keyVersion=1, signature=****` |
| Client-Id | Yes | Merchant's assigned Client ID |
| Request-Time | Yes | Unix timestamp in ms |
| Request-Id | Yes | Unique request ID from merchant |
| Content-Type | No | `application/json; charset=UTF-8` |

### Response Structure

```json
{
  "result": {
    "resultStatus": "S",      // S=Success, F=Failed, U=Unknown, A=Accept/Processing
    "resultCode": "20000000",
    "resultMessage": "successful"
  }
}
```

Always verify the response Signature before processing business logic.

---

## User Information (OAuth2 Flow)

```
Frontend: getAuthCode JSAPI -> authCode
Frontend -> Backend: pass authCode
Backend -> Tokapay: POST /v2/authorizations/applyToken  (authCode -> accessToken + userId)
Backend -> Tokapay: POST /v2/users/inquiryUserInfo      (accessToken -> user data)
```

### Step 1 — Get Auth Code (JSAPI)

| JSAPI | What it authorizes | Valid `scopes` |
|---|---|---|
| `my.getUserDigitalIdentityAuthCode` | Identity | `USER_ID`, `USER_AVATAR`, `USER_NICKNAME` |
| `my.getUserContactInformationAuthCode` | Contact | `PLAINTEXT_MOBILE_PHONE`, `PLAINTEXT_EMAIL_ADDRESS` |
| `my.getUserAddressInformationAuthCode` | Address | `USER_ADDRESS` |
| `my.getUserPersonalInformationAuthCode` | Personal | `USER_NAME`, `USER_FIRST_SURNAME`, `USER_SECOND_SURNAME`, `USER_GENDER`, `USER_BIRTHDAY`, `USER_STATE_OF_BIRTH`, `USER_NATIONALITY` |
| `my.getUserKYCStatusAuthCode` | KYC | `USER_KYC_STATUS` |

Result codes: `10000` success, `10001` param illegal, `10002` mini program does not exist, `10004` system error, `10006` user declined.

> If the requested scope is just `USER_ID`, no popup is shown — auth code returned silently. Any other scope triggers the consent popup.

```javascript
my.call('getUserDigitalIdentityAuthCode', {
  usage: 'Show your profile in the app',
  scopes: ['USER_ID', 'USER_NICKNAME'],
  success: async (apiRes) => {
    if (apiRes.resultCode === 10000) {
      const authCode = apiRes.result;  // send to backend
    }
  }
});
```

### Step 2 — Apply Token (OpenAPI)

**`POST /v2/authorizations/applyToken`**

| Parameter | Type | Req | Description |
|---|---|---|---|
| `appId` | String | Yes | Mini-program ID |
| `grantType` | String | Yes | `AUTHORIZATION_CODE` or `REFRESH_TOKEN` |
| `authCode` | String | When `AUTHORIZATION_CODE` | Auth code from Step 1 |
| `refreshToken` | String | When `REFRESH_TOKEN` | Existing refresh token |

Response: `accessToken`, `accessTokenExpiryTime`, `refreshToken`, `refreshTokenExpiryTime`, `userId`.

Errors: `20040001` auth code doesn't exist/used, `20040002` refresh token doesn't exist, `20040003` merchant not onboarded, `20040004` appId error, `20000005` access denied.

```json
// Request
{ "appId": "3500020208396321", "grantType": "AUTHORIZATION_CODE", "authCode": "VkvxZE" }

// Response
{
  "result": { "resultStatus": "S", "resultCode": "20000000", "resultMessage": "successful" },
  "accessToken": "eyJhbGciOi...",
  "accessTokenExpiryTime": "1747280655570",
  "refreshToken": "eyJhbGciOi...",
  "refreshTokenExpiryTime": "1749786255569",
  "userId": "1010000010775026"
}
```

### Step 3 — Query User Info (OpenAPI)

**`POST /v2/users/inquiryUserInfo`** — request: `appId`, `accessToken`.

Response fields (all optional, depend on scopes): `userId`, `nickName`, `avatar`, `fullName`, `firstName`, `secondName`, `lastName`, `gender` (F/M/X), `birthday` (ms), `nationality`, `birthState`, `email`, `mobilePhone`, `address`, `kycState`.

> **⚠️ Mexican naming**: `firstName` = **paternal surname**, `secondName` = **maternal surname**, `lastName` = **given name**. Opposite of English usage. Prefer `fullName` for display.

Errors: `20040004` appId error, `20040005` accessToken expired, `20040006` accessToken not available.

---

## User Payment Flow

**Different endpoint from POS!** Mini-program payments use `/v2/acquiring/miniprogram/create` and trigger the cashier with the `my.pay` JSAPI.

```
1. User places order in mini-program
2. Frontend -> Backend: send order
3. Backend -> Tokapay: POST /v2/acquiring/miniprogram/create -> returns paymentUrl
4. Backend -> Frontend: return paymentUrl
5. Frontend: my.call('pay', { paymentUrl }) -> opens cashier
6. User confirms payment in Tokapay cashier UI
7. Tokapay returns control to mini-program
8. Backend polls: POST /v1/acquiring/payment/inquiry (every 5s) until SUCCESS/FAILED
```

### Step 1 — Create Payment Order (OpenAPI)

**`POST /v2/acquiring/miniprogram/create`**

| Parameter | Type | Req | Description |
|---|---|---|---|
| `productCode` | String | Yes | Fixed: `"MINI_PROGRAM_DIRECT_PAY"` |
| `appId` | String | Yes | Mini-program ID |
| `userId` | String | Yes | Tokapay user ID (from Apply Token response) |
| `order.orderTitle` | String | Yes | Shown on cashier page (max 256) |
| `order.merchantTransId` | String | Yes | Unique transaction ID from merchant (max 64) |
| `order.orderAmount.value` | Long | Yes | Amount in **centavos** (1000 = 10.00 MXN) |
| `order.orderAmount.currency` | String | Yes | Fixed: `"MXN"` |
| `order.expiryTime` | String | Yes | `YYYY-MM-DD hh:mm:ss`. Must be > request time. |
| `order.allowPantryCard` | String | No | `Y`/`N` |
| `order.allowFuelCard` | String | No | `Y`/`N` |
| `order.goodsDetail` | Array | No | 1–1000 items: `goodId`, `goodName`, `goodQuantity`, `goodPrice`, `goodDetails` |

Response: `result`, `merchantTransId`, `paymentId` (**store for inquiry/refund**), `paymentUrl` (**pass to `my.pay`**).

Errors: `20030001` repeated submission (payment order already exists), `20030002` expiry invalid, `20030003` product code invalid, `20030004` currency not supported, `20030007` merchant does not exist, `20030011` merchant status abnormal, `20030012` no valid contract, `20030013` amount exceeds limit, `20030015` mini program does not exist, `20030017` user does not exist, `20030018` user status abnormal.

```json
// Request
{
  "productCode": "MINI_PROGRAM_DIRECT_PAY",
  "userId": "1010000010700053",
  "appId": "3500020208396321",
  "order": {
    "merchantTransId": "devOpenApiCsbPre20250513113605",
    "orderAmount": { "value": 1000, "currency": "MXN" },
    "expiryTime": "2025-05-14 00:00:00",
    "orderTitle": "Buy something",
    "allowPantryCard": "Y",
    "allowFuelCard": "N"
  }
}

// Response  <-- NOTE resultStatus "A" (Accept) is the happy path, not "S"
{
  "result": { "resultStatus": "A", "resultCode": "20000006", "resultMessage": "Accept Request." },
  "paymentId": "202505131001100100011110500129007",
  "merchantTransId": "devOpenApiCsbPre20250513113605",
  "paymentUrl": "https://h5.manager.yak.toka.test.com/miniProgrammePayment?bizId=...&sign=..."
}
```

### Step 2 — Request Payment (JSAPI)

Frontend calls `my.pay` with the `paymentUrl`.

| Code | Meaning |
|---|---|
| 9000 | Payment successful |
| 4000 | Payment failed |
| 8001 | Parameter illegal |
| 6001 | User cancelled |
| 6004 | **Unknown payment result** — may have succeeded; verify via inquiry |
| 4001 | Declined by risk control |
| 4002 | Declined by user risk authentication |

> **⚠️ Always confirm via the backend Inquiry API.** The frontend result is informational; the source of truth is the Tokapay backend.

```javascript
my.call('pay', {
  paymentUrl: paymentUrlFromBackend,
  success(res) { /* 9000 = success, 6004 = unknown -> backend polls inquiry */ },
  fail(res) { my.alert({ title: 'pay failed', content: JSON.stringify(res) }); }
});
```

### Step 3 — Query Payment Result (OpenAPI)

**`POST /v1/acquiring/payment/inquiry`** — same endpoint as POS. Request: `paymentId`.

Response: `paymentId`, `paymentRequestId` (= your merchantTransId), `paymentAmount`, `paymentTime`, `paymentCreateTime`, `paymentStatus`, `paymentResultCode`, `paymentResultMessage`, `paymentMethod`, `cardNumber`.

- `paymentStatus`: `PROCESSING` (keep polling), `SUCCESS` (finalize), `FAILED` (handle failure)
- `paymentResultCode`: `20000000`=SUCCESS, `20000003`=processing, `20030105`=canceled, `20030106`=timed out

Poll every 5 seconds, especially when the frontend reports `6004`.

---

## Refunds in Miniapp

Shared with POS: `POST /v1/acquiring/refund/apply` and `POST /v1/acquiring/refund/inquiry`.

Miniapp-specific refund error codes: `20030213` risk control reject, `20030214` risk control reject w/ verification required, `20030215` risk consultation failed (retry).

---

## Reconciliation

Same endpoint as POS: `POST /v1/acquiring/recon/get`.

---

## Promotion QR Code

```
miniapp://aplus?appId={appId}&screenOrientation=landscape&query=a%3D123%26b%3D456&showTitleBar=1
```

Encode as a QR image. Tokapay users scanning it land straight in the mini-program.

Parameters: `appId` (required), `query` (URL-encoded k=v passed on launch), `showTitleBar`, `showLoading`, `showTitleLoading`, `titleColor`, `titleBarColor`, `screenOrientation`, `titleAlignment`.

---

## Third-party App Linking (v1.7)

**JSAPI `my.openAppByUrl`** — opens a third-party app (WhatsApp, browser, native app) via Universal Link or custom scheme.

Request: `url`. Result codes: `10000` opened, `10001` missing url, `10002` invalid url format, `10003` failed to open (usually app not installed).

```javascript
my.call('openAppByUrl', { url: 'https://wa.me', success: (res) => my.alert(JSON.stringify(res)) });
```

---

## Error Code Index

### JSAPI (frontend)
`10000` success · `10001` param illegal · `10002` mini program doesn't exist · `10004` system error · `10006` user declined
`my.pay`: `9000` success · `4000` failed · `4001`/`4002` risk declined · `6001` cancelled · `6004` unknown · `8001` param illegal

### OpenAPI general
`20000000` S success · `20000001` U unknown · `20000002` F param illegal · `20000003` F client id invalid · `20000004` F signature wrong · `20000005` F access denied · `20000006` A accept request

### Apply Token / Query User Info
`20040001` auth code doesn't exist/used · `20040002` refresh token doesn't exist · `20040003` merchant not onboarded · `20040004` appId error · `20040005` accessToken expired · `20040006` accessToken not available

### Create Payment Order (miniapp)
`20030001` repeated submission · `20030002` expiry invalid · `20030003` product code invalid · `20030004` currency not supported · `20030007` merchant doesn't exist · `20030011` merchant status abnormal · `20030012` no valid contract · `20030013` amount exceeds limit · `20030015` mini program doesn't exist · `20030017` user doesn't exist · `20030018` user status abnormal

---

## Integration Checklist (Mini-Program)

**Pre-Integration**:
- [ ] Mini Program Dev product contract signed
- [ ] Mini Program created on Mini Program Platform
- [ ] Feature permission applied (User Information, User Payment)
- [ ] Received `appId`, `ClientId`, Tokapay public key
- [ ] Generated own RSA key pair; exchanged public keys
- [ ] Received SIT environment credentials

**User Info**:
- [ ] `getAuthCode` JSAPI(s) on frontend
- [ ] Backend `/v2/authorizations/applyToken`
- [ ] Backend `/v2/users/inquiryUserInfo`
- [ ] Access tokens on backend ONLY
- [ ] Refresh token flow
- [ ] User declined (10006) handled

**Payment**:
- [ ] Backend `/v2/acquiring/miniprogram/create` (productCode `MINI_PROGRAM_DIRECT_PAY`)
- [ ] Frontend `my.pay` with returned `paymentUrl`
- [ ] All `my.pay` result codes handled (9000/4000/6001/6004/4001/4002/8001)
- [ ] Backend polls `/v1/acquiring/payment/inquiry` (esp. on 6004)
- [ ] Refund flow
- [ ] Idempotent `merchantTransId` / `refundRequestId`

**Production Readiness**:
- [ ] Request + response signatures generated/verified
- [ ] Domain names (no IPs)
- [ ] Error handling for all `resultStatus` values (S, F, U, A)
- [ ] Logging/monitoring on all OpenAPI calls
- [ ] Tested user-declined and timeout paths
