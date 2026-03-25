# RouteX

RouteX is a Nigeria-first multi-payment router built for the hackathon MVP. It gives merchants one integration for collections and payouts, routes transactions across multiple gateways, and gives operators a live control room for health, failover, and routing policy.

## What Problem We Solved

Payment teams lose revenue when a single gateway slows down, fails, or behaves inconsistently. Most teams either hard-code one provider or switch manually during incidents. RouteX solves that by introducing a unified payment API, explainable gateway routing, fallback visibility, and a separate merchant and admin experience.

## What We Built

- Unified collections, payouts, and verification APIs
- Intelligent routing across `Paystack`, `Flutterwave`, `Korapay`, and `Interswitch`
- Gateway health monitoring, failover tracking, and routing rule controls
- Merchant auth with OTP delivery by email using Resend
- Merchant dashboard for balances, transactions, payment links, and API keys
- Admin control room for gateway controls, health refresh, routing rules, and transaction observability
- Public docs and a live API tester on the landing page
- Interswitch hosted checkout bridge, return flow, and signed webhooks
- Optional PostHog analytics in the Next.js frontend

## Submission Scope

This submission is **test mode only**.

That means:

- all gateway credentials should be sandbox/test credentials
- all webhook URLs below are test endpoints
- the merchant demo flow, admin control room, docs, and playground are all wired for MVP validation, not production settlement operations

## Product Surfaces

- `/` landing page and API tester
- `/docs` public API documentation
- `/login`, `/signup`, `/verify-otp`, `/forgot-password`, `/reset-password`
- `/dashboard` merchant workspace
- `/admin/login`, `/admin` router control room
- `/pay/status` hosted checkout return status page

## Why It Is Hackathon-Ready

- one backend contract for merchants
- one frontend that shows both merchant and control-plane value
- clear live demo story: route, fail over, verify, observe
- test-mode deployment with Docker Compose on Dokploy
- judges can inspect team ownership directly in this README

## Team Contributions

Judges should use this section to verify participation.

### Temiloluwa Ogundiran

- Backend architecture and FastAPI implementation
- Routing engine, gateway adapters, webhook normalization, and persistence
- Collections and payout orchestration across supported gateways
- Interswitch integration, hosted checkout bridge, verification, and return flow
- Celery workers, health refresh jobs, and deployment/container configuration
- Backend tests, provider integration research, and webhook setup validation

### Kwaghuter Raphael

- Frontend architecture and neo-brutalist design implementation
- Landing page, docs experience, and live API tester
- Merchant auth flows, OTP UX, and dashboard experience
- Admin dashboard UX, routing observability pages, and controls
- Frontend-backend proxy integration, navigation, and route wiring
- Frontend analytics integration, end-to-end testing, and submission presentation polish

## Architecture

- **Backend:** FastAPI, PostgreSQL, Redis, Celery
- **Frontend:** Next.js App Router
- **Routing data:** transactions, routing attempts, decision audits, health snapshots, routing rules
- **Deployment:** Docker Compose for Dokploy

## Environment Variables

Only the important variables are kept in [.env.example](/C:/Users/USER/Documents/routex/.env.example).

### Core backend

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
- `PAYSTACK_LIVE_SECRET_KEY`
- `FLTW_SECRET_KEY`
- `FLTW_SECRET_HASH`
- `KORA_SECRET_KEY`
- `KORA_LIVE_SECRET_KEY`
- `INTERSWITCH_MERCHANT_CODE`
- `INTERSWITCH_PAY_ITEM_ID`
- `INTERSWITCH_CLIENT_ID`
- `INTERSWITCH_SECRET_KEY`

### Frontend bridge

- `ROUTEX_API_BASE_URL=https://routexapi.xoroai.cloud`
- `ROUTEX_PLAYGROUND_SECRET_KEY`

### Optional product analytics

- `NEXT_PUBLIC_POSTHOG_KEY`
- `NEXT_PUBLIC_POSTHOG_HOST=https://us.i.posthog.com`

## Dokploy Deployment

RouteX is designed to be deployed in Dokploy using [docker-compose.yml](/C:/Users/USER/Documents/routex/docker-compose.yml).

### Step 1. Create the Dokploy compose app

1. Create a new `Compose` application in Dokploy.
2. Connect this Git repository.
3. Set the compose path to `docker-compose.yml`.
4. Trigger the first deploy so Dokploy provisions:
   - `postgres`
   - `redis`
   - `api`
   - `worker`
   - `beat`
   - `frontend`

### Step 2. Fill the compose environment

Use the keys from [.env.example](/C:/Users/USER/Documents/routex/.env.example) and fill the real sandbox values in Dokploy.

Important public URLs for this MVP:

- `SERVER_URL=https://routexapi.xoroai.cloud`
- `FRONTEND_BASE_URL=https://routex.xoroai.cloud`
- `CHECKOUT_URL=https://routex.xoroai.cloud`
- `ROUTEX_API_BASE_URL=https://routexapi.xoroai.cloud`

If you want frontend analytics:

- `NEXT_PUBLIC_POSTHOG_KEY`
- `NEXT_PUBLIC_POSTHOG_HOST=https://us.i.posthog.com`

### Step 3. Attach domains

Attach these domains in Dokploy:

- `routex.xoroai.cloud` -> `frontend` service on port `3000`
- `routexapi.xoroai.cloud` -> `api` service on port `8000`

Then:

1. enable HTTPS / Let's Encrypt for both
2. point your DNS records to the Dokploy server
3. redeploy if Dokploy asks after domain attachment

### Step 4. Understand what the URL vars do

- `SERVER_URL`
  - canonical public backend URL
  - used for backend-generated provider-facing URLs
- `FRONTEND_BASE_URL`
  - canonical public frontend URL
  - used for user-facing auth and app links
- `CHECKOUT_URL`
  - public host used in hosted checkout and redirect flows
- `ROUTEX_API_BASE_URL`
  - backend base URL used by the frontend server-side proxy routes

## Gateway Test-Mode Webhook And Redirect Setup

Not every gateway is configured the same way.

Some require:

- a webhook URL saved in the provider dashboard

Some also require:

- a callback, redirect, notification, or return URL passed in the checkout payload

For this MVP, the correct split is:

### Paystack

- Configure this test webhook in the Paystack dashboard:
  - `https://routexapi.xoroai.cloud/paystack/webhook/test`
- RouteX also passes `callback_url` in the initialize payload.

### Flutterwave

- Configure this test webhook in the Flutterwave dashboard:
  - `https://routexapi.xoroai.cloud/flutterwave/webhook/test`
- Keep the dashboard secret hash aligned with `FLTW_SECRET_HASH`.
- RouteX also passes `redirect_url` in the checkout payload.

### Korapay

- For this MVP flow, RouteX provides the webhook destination in the payload through `notification_url`.
- RouteX also provides the customer redirect through `redirect_url`.
- RouteX test webhook receiver:
  - `https://routexapi.xoroai.cloud/kora/webhook/test`

### Interswitch

- Configure this test transaction webhook in the Interswitch dashboard:
  - `https://routexapi.xoroai.cloud/interswitch/webhook/test`
- RouteX sends the hosted checkout return URL in the payload:
  - `https://routexapi.xoroai.cloud/api/v1/checkout/interswitch/return`

### Provider Matrix

| Provider | Webhook set in provider dashboard? | Redirect/return passed in payload? | Test endpoint |
|---|---|---|---|
| Paystack | Yes | Yes | `https://routexapi.xoroai.cloud/paystack/webhook/test` |
| Flutterwave | Yes | Yes | `https://routexapi.xoroai.cloud/flutterwave/webhook/test` |
| Korapay | No for this MVP flow | Yes | `https://routexapi.xoroai.cloud/kora/webhook/test` |
| Interswitch | Yes | Yes | `https://routexapi.xoroai.cloud/interswitch/webhook/test` and `https://routexapi.xoroai.cloud/api/v1/checkout/interswitch/return` |

## Local Verification

### Backend

```powershell
$env:DB_URL='sqlite+aiosqlite:///./pytest_app.db'
$env:REDIS_URL='redis://localhost:6379/0'
$env:AUTH_SECRET='test-secret'
$env:AGG_SECRET='nCNO7CutF7uhjRvkHxUlB1zJVEz-PvWQ_KFraeckYMs='
pytest tests/test_auth_flow.py tests/test_routing_api.py tests/test_router_dashboard_api.py tests/test_interswitch_service.py tests/test_interswitch_webhooks.py -v
```

### Frontend

```powershell
Set-Location C:\Users\USER\Documents\routex\frontend
npm run build
npx playwright test
```
