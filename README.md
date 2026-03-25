# RouteX - Hackathon Submission

RouteX is a multi-payment router for Nigeria that gives merchants one integration for collections and payouts while routing across multiple gateways for higher success rates.

## Team Contributions

GitHub README documents every team member's contribution - technical and non-technical. This includes code, design, research, documentation, or any other form of involvement.

- **Temiloluwa Ogundiran (Backend)**
  - Routing core and adapter architecture
  - FastAPI APIs for collections, payouts, verify, admin analytics, and routing rules
  - Interswitch collections + verify + webhook + return orchestration
  - Gateway health snapshots and Celery refresh pipeline
  - Data models, migrations, and backend tests
  - Deployment architecture and gateway webhook mapping

- **Kwaghuter Raphael (Frontend)**
  - Landing page, product UX, and visual system
  - User auth flows (login/signup/OTP/recovery) and app route guards
  - Merchant dashboard UX and admin control room UX
  - Public API docs UI and landing-page API tester UX
  - Frontend API proxy routes and end-to-end testing
  - Hackathon submission polish and demonstration flow

## Core Features

- One API for collections, verification, and payouts
- Smart routing across Paystack, Flutterwave, Korapay, and Interswitch
- Admin controls for gateway toggles, health, and routing rules
- Signed webhook normalization and transaction observability
- Public docs + API testing surface on the landing app

## Runtime URLs

- Frontend app: `https://app.yourdomain.com`
- Backend API: `https://api.yourdomain.com`
- Interswitch checkout return endpoint: `https://api.yourdomain.com/api/v1/checkout/interswitch/return`

## Environment Variables (compacted)

Only keep these keys:

- Backend core:
  - `DB_URL`
  - `REDIS_URL`
  - `AGG_SECRET`
  - `AUTH_SECRET`
  - `SERVER_URL`
  - `FRONTEND_BASE_URL`
  - `CHECKOUT_URL`
- Email:
  - `RESEND_API_KEY`
  - `AUTH_EMAIL`
  - `RECEIPT_EMAIL`
- Gateways:
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
- Frontend server integration:
  - `ROUTEX_API_BASE_URL`
  - `ROUTEX_PLAYGROUND_SECRET_KEY`

## Dokploy Deployment Guide (Step by Step)

### 1) Create infrastructure services

1. Create a `PostgreSQL` service in Dokploy.
2. Create a `Redis` service in Dokploy.
3. Copy internal connection values for both (host, port, user, password, db).

### 2) Deploy API container

1. New app service: `routex-api`.
2. Build context: repo root.
3. Dockerfile path: `Dockerfile.api`.
4. Exposed port: `8000`.
5. Set env vars:
   - all backend core/email/gateway vars listed above
   - `DB_URL` should use Dokploy postgres internal host
   - `REDIS_URL` should use Dokploy redis internal host
6. Add domain: `api.yourdomain.com`.
7. Enable TLS in Dokploy.

### 3) Deploy frontend container

1. New app service: `routex-frontend`.
2. Build context: `frontend`.
3. Dockerfile path: `frontend/Dockerfile`.
4. Exposed port: `3000`.
5. Set env vars:
   - `ROUTEX_API_BASE_URL=https://api.yourdomain.com`
   - `ROUTEX_PLAYGROUND_SECRET_KEY=<sandbox merchant secret key>`
6. Add domain: `app.yourdomain.com`.
7. Enable TLS in Dokploy.

### 4) Deploy worker container

1. New app service: `routex-worker`.
2. Build context: repo root.
3. Dockerfile path: `Dockerfile.worker`.
4. No public domain required.
5. Use same backend env vars as API.

### 5) Deploy beat container

1. New app service: `routex-beat`.
2. Build context: repo root.
3. Dockerfile path: `Dockerfile.beat`.
4. No public domain required.
5. Use same backend env vars as API.

## Domain setup in Dokploy

For each public service:

1. Open service -> `Domains`.
2. Add domain (`api.yourdomain.com` or `app.yourdomain.com`).
3. Point DNS `A`/`CNAME` to your Dokploy host.
4. Enable HTTPS/Let's Encrypt.
5. Redeploy service.

## Gateway Webhook URLs to Configure

Use API domain only (`https://api.yourdomain.com`).

- **Paystack** (dashboard-configured)
  - `https://api.yourdomain.com/paystack/webhook/test`

- **Flutterwave** (dashboard-configured)
  - `https://api.yourdomain.com/flutterwave/webhook/test`

- **Korapay** (dashboard-configured)
  - `https://api.yourdomain.com/kora/webhook/test`
  - `https://api.yourdomain.com/kora/webhook/live`

- **Interswitch**
  - Dashboard webhook:
    - `https://api.yourdomain.com/interswitch/webhook/test`
    - `https://api.yourdomain.com/interswitch/webhook/live`
  - Checkout return URL:
    - Payload-driven by RouteX (not manual dashboard config):
    - `https://api.yourdomain.com/api/v1/checkout/interswitch/return`

## Local Verification

```powershell
# backend
$env:DB_URL='sqlite+aiosqlite:///./pytest_app.db'
$env:REDIS_URL='redis://localhost:6379/0'
$env:AUTH_SECRET='test-secret'
$env:AGG_SECRET='nCNO7CutF7uhjRvkHxUlB1zJVEz-PvWQ_KFraeckYMs='
pytest tests/test_auth_flow.py tests/test_routing_api.py tests/test_router_dashboard_api.py tests/test_interswitch_service.py tests/test_interswitch_webhooks.py -v

# frontend
Set-Location C:\Users\USER\Documents\routex\frontend
npm run build
npx playwright test
```
