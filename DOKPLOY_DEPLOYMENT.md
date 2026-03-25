# Dokploy Deployment Guide

This guide is for the **test-mode MVP** only.

It assumes:

- frontend domain: `routex.xoroai.cloud`
- backend API domain: `routexapi.xoroai.cloud`
- checkout host: `routex.xoroai.cloud`

## 1. Deploy with Docker Compose in Dokploy

Use [docker-compose.yml](/C:/Users/USER/Documents/routex/docker-compose.yml).

### Step-by-step

1. Create a new **Compose** app in Dokploy.
2. Connect the Git repository.
3. Set the compose file path to `docker-compose.yml`.
4. Deploy once so Dokploy creates:
   - `postgres`
   - `redis`
   - `api`
   - `worker`
   - `beat`
   - `frontend`
5. Open the compose app environment section and fill the variables below.

## 2. Environment Variables to Fill

### Core

- `DB_URL`
- `REDIS_URL`
- `AGG_SECRET`
- `AUTH_SECRET`
- `SERVER_URL=https://routexapi.xoroai.cloud`
- `FRONTEND_BASE_URL=https://routex.xoroai.cloud`
- `CHECKOUT_URL=https://routex.xoroai.cloud`

### Email

- `RESEND_API_KEY`
- `AUTH_EMAIL`
- `RECEIPT_EMAIL`

### Gateways

- `PAYSTACK_SECRET_KEY`
- `FLTW_SECRET_KEY`
- `FLTW_SECRET_HASH`
- `KORA_SECRET_KEY`
- `INTERSWITCH_MERCHANT_CODE`
- `INTERSWITCH_PAY_ITEM_ID`
- `INTERSWITCH_CLIENT_ID`
- `INTERSWITCH_SECRET_KEY`

### Frontend bridge

- `ROUTEX_API_BASE_URL=https://routexapi.xoroai.cloud`
- `ROUTEX_PLAYGROUND_SECRET_KEY=<sandbox merchant secret key>`

## 3. Add Domains in Dokploy

1. Open the compose app in Dokploy.
2. Go to the service/domain section.
3. Attach `routex.xoroai.cloud` to the `frontend` service on port `3000`.
4. Attach `routexapi.xoroai.cloud` to the `api` service on port `8000`.
5. Enable HTTPS / Let's Encrypt for both.
6. Point your DNS records to the Dokploy host.
7. Redeploy if Dokploy asks for it after domain attachment.

## 4. What Each URL Does

- `SERVER_URL`
  - backend public base URL
  - used in backend-generated links and provider-facing backend references
- `FRONTEND_BASE_URL`
  - frontend public URL
  - used for user-facing auth/reset links
- `CHECKOUT_URL`
  - public checkout host used in checkout/redirect flows
- `ROUTEX_API_BASE_URL`
  - frontend server-side backend API base URL

## 5. Provider Webhook and Redirect Setup

Important distinction:

- some providers require **webhook URLs configured in their dashboard**
- some flows also require **redirect or return URLs sent in the payment payload**

This section is **test mode only**.

### Paystack

Dashboard-configured:

- webhook URL in Paystack dashboard

Test webhook URL:

- `https://routexapi.xoroai.cloud/paystack/webhook/test`

Payload-configured:

- `callback_url` / redirect URL on initialize

Meaning:

- webhook is configured in Paystack dashboard
- redirect/callback can be passed per transaction in payload

### Flutterwave

Dashboard-configured:

- webhook URL in Flutterwave dashboard
- secret hash in Flutterwave dashboard

Test webhook URL:

- `https://routexapi.xoroai.cloud/flutterwave/webhook/test`

Payload-configured:

- `redirect_url` in payment initialization payload

Meaning:

- webhook is configured in Flutterwave dashboard
- customer redirect URL is sent in payload

### Korapay

Payload-configured for this RouteX MVP flow:

- `notification_url` in the initiation payload
- `redirect_url` in the initiation payload

Test payload URLs used by RouteX:

- webhook receiver: `https://routexapi.xoroai.cloud/kora/webhook/test`
- redirect destination: merchant-provided `redirect_url`

Meaning:

- for this MVP flow, RouteX sends Korapay webhook delivery through `notification_url`
- customer redirect is also sent in payload through `redirect_url`

### Interswitch

Dashboard-configured:

- transaction webhook URL in Interswitch / Quickteller Business settings

Test webhook URL:

- `https://routexapi.xoroai.cloud/interswitch/webhook/test`

Payload-configured:

- hosted checkout return URL

Test return URL used by RouteX:

- `https://routexapi.xoroai.cloud/api/v1/checkout/interswitch/return`

Meaning:

- webhook is configured in Interswitch dashboard
- return URL is sent by RouteX during checkout flow

## 6. Quick Reference Table

| Provider | Webhook set in provider dashboard? | Redirect/return passed in payload? | Test URL |
|---|---|---|---|
| Paystack | Yes | Yes | `https://routexapi.xoroai.cloud/paystack/webhook/test` |
| Flutterwave | Yes | Yes | `https://routexapi.xoroai.cloud/flutterwave/webhook/test` |
| Korapay | No for this MVP flow | Yes | `https://routexapi.xoroai.cloud/kora/webhook/test` |
| Interswitch | Yes | Yes | `https://routexapi.xoroai.cloud/interswitch/webhook/test` + `https://routexapi.xoroai.cloud/api/v1/checkout/interswitch/return` |

## 7. Notes

- This submission is **test mode only**.
- Use sandbox/test credentials for every provider.
- The landing-page tester depends on `ROUTEX_API_BASE_URL` and `ROUTEX_PLAYGROUND_SECRET_KEY`.
- If `ROUTEX_PLAYGROUND_SECRET_KEY` is missing, the tester stays disabled instead of returning fake data.
- The provider split above reflects both the official provider docs and the current RouteX integration behavior in this repo.
