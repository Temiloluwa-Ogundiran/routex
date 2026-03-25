# RouteX

RouteX is a Nigeria-first multi-payment router for collections and payouts. The MVP gives merchants one integration, routes transactions across multiple gateways, and exposes both a merchant app and an admin control room.

## Why this project matters

Payment teams lose revenue when one gateway slows down or fails. RouteX reduces that risk by selecting the healthiest eligible gateway, recording routing decisions, and giving operators visibility into failover, health, and transaction flow from one place.

## What we built

- Unified collections API, payout API, and verification API
- Intelligent routing across `Paystack`, `Flutterwave`, `Korapay`, and `Interswitch`
- Gateway health tracking, failover visibility, and admin routing rules
- Public API docs and landing-page API tester
- OTP-based user auth, merchant dashboard, and separate admin dashboard
- Interswitch hosted checkout bridge, return flow, and signed webhook handling

## MVP Scope

This submission is **test mode only**. All deployment and provider setup below assume sandbox/test credentials and test webhook endpoints.

## Product Surfaces

- `/` landing page and API tester
- `/docs` public API docs
- `/login`, `/signup`, `/verify-otp`, `/forgot-password`, `/reset-password`
- `/dashboard` merchant app
- `/admin/login`, `/admin` admin control room
- `/pay/status` payment return status page

## Team Contributions

Judges should use this section to verify team participation.

- **Temiloluwa Ogundiran**
  - Backend architecture and API implementation
  - Routing engine, gateway adapters, webhook normalization, and persistence
  - Interswitch integration, return flow, and backend verification
  - Database models, migrations, worker scheduling, and deployment configuration
  - Backend testing and provider integration research

- **Kwaghuter Raphael**
  - Frontend design system and landing page experience
  - Public docs UI and API testing UX
  - Merchant auth flows and dashboard UX
  - Admin dashboard UX and observability screens
  - Frontend routing, API proxy integration, and end-to-end testing
  - Submission polish, README presentation, and demo flow preparation

## Architecture

- **Backend:** FastAPI, PostgreSQL, Redis, Celery
- **Frontend:** Next.js
- **Routing storage:** transaction attempts, routing decisions, health snapshots, routing rules
- **Deployment shape:** Docker Compose stack for Dokploy

## Important Environment Variables

Only the compact set below is needed:

- `DB_URL`: PostgreSQL connection string for backend, worker, and beat
- `REDIS_URL`: Redis connection string for backend, worker, and beat
- `AGG_SECRET`: encryption secret for merchant token storage
- `AUTH_SECRET`: JWT signing secret
- `SERVER_URL`: public backend API base URL, for example `https://routexapi.xoroai.cloud`
- `FRONTEND_BASE_URL`: public frontend app URL, for example `https://routex.xoroai.cloud`
- `CHECKOUT_URL`: public checkout host used in hosted checkout flows
- `RESEND_API_KEY`: Resend API key for OTP and receipt emails
- `AUTH_EMAIL`: sender email for auth emails
- `RECEIPT_EMAIL`: sender email for receipts
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
- `ROUTEX_API_BASE_URL`: backend API base URL used by the frontend server
- `ROUTEX_PLAYGROUND_SECRET_KEY`: sandbox merchant secret key used by the landing-page tester

## Deployment

Dokploy deployment now uses the repository's [docker-compose.yml](/C:/Users/USER/Documents/routex/docker-compose.yml).

The full deployment guide lives in [DOKPLOY_DEPLOYMENT.md](/C:/Users/USER/Documents/routex/DOKPLOY_DEPLOYMENT.md). It includes:

- step-by-step Dokploy setup with Docker Compose
- domain attachment for frontend and backend
- exact env vars to fill
- test-mode webhook URLs
- which providers need dashboard webhook configuration
- which providers need redirect/return URLs passed in payloads

## Local Verification

Backend:

```powershell
$env:DB_URL='sqlite+aiosqlite:///./pytest_app.db'
$env:REDIS_URL='redis://localhost:6379/0'
$env:AUTH_SECRET='test-secret'
$env:AGG_SECRET='nCNO7CutF7uhjRvkHxUlB1zJVEz-PvWQ_KFraeckYMs='
pytest tests/test_auth_flow.py tests/test_routing_api.py tests/test_router_dashboard_api.py tests/test_interswitch_service.py tests/test_interswitch_webhooks.py -v
```

Frontend:

```powershell
Set-Location C:\Users\USER\Documents\routex\frontend
npm run build
npx playwright test
```
