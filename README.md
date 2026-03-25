# RouteX

RouteX is a multi-payment router MVP built on FastAPI + PostgreSQL + Redis/Celery with a Next.js frontend.

## What is live

- Unified collections routing with `Paystack`, `Flutterwave`, `Korapay`, and `Interswitch`.
- Unified payout API.
- Interswitch hosted checkout bridge, return flow, and signed transaction webhook handling.
- User auth with existing email + OTP backend flow.
- User app at `/dashboard` and separate admin control room at `/admin`.
- Public docs at `/docs` generated from backend public OpenAPI.
- Landing-page sandbox tester at `/` via server-side proxy (`/api/playground`).

## Frontend route map

- `/` landing page + API tester.
- `/docs` public API reference.
- `/login`, `/signup`, `/verify-otp`, `/forgot-password`, `/reset-password`.
- `/dashboard` user app (auth required).
- `/admin/login`, `/admin`, `/admin/transactions/{reference}` admin app (admin auth required).
- `/pay/status` checkout return status page.

## Required environment

Use [.env.example](/C:/Users/USER/Documents/routex/.env.example). Keep only these keys in deployment:

- Core backend:
  - `DB_URL`
  - `REDIS_URL`
  - `AGG_SECRET`
  - `AUTH_SECRET`
  - `SERVER_URL`
  - `FRONTEND_BASE_URL`
  - `PUBLIC_SITE_URL`
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
  - `NEXT_PUBLIC_ROUTEX_API_BASE_URL`

## Local run

```powershell
docker compose up --build
```

This starts:

- API on `http://localhost:8000`
- Frontend on `http://localhost:3000`
- Postgres on `localhost:5432`
- Redis on `localhost:6379`
- Celery worker + beat

## Dokploy deployment

Deploy **5 services** plus managed Postgres/Redis.

### 1) `routex-api`

- Build context: repo root.
- Dockerfile: `Dockerfile.api`.
- Port: `8000`.
- Command: use image default.
- Required env:
  - all backend core/env/gateway/email vars listed above.
  - `DB_URL` and `REDIS_URL` must point to Dokploy internal service hosts.
- Domain example: `https://api.yourdomain.com`.

### 2) `routex-frontend`

- Build context: `frontend`.
- Dockerfile: `frontend/Dockerfile`.
- Port: `3000`.
- Required env:
  - `ROUTEX_API_BASE_URL=https://api.yourdomain.com`
  - `NEXT_PUBLIC_ROUTEX_API_BASE_URL=https://api.yourdomain.com`
  - `ROUTEX_PLAYGROUND_SECRET_KEY=<sandbox merchant secret>`
- Domain example: `https://app.yourdomain.com`.

### 3) `routex-worker`

- Build context: repo root.
- Dockerfile: `Dockerfile.worker`.
- Command: image default (`celery ... worker`).
- Env:
  - same backend env as API.

### 4) `routex-beat`

- Build context: repo root.
- Dockerfile: `Dockerfile.beat`.
- Command: image default (`celery ... beat`).
- Env:
  - same backend env as API.

### 5) (optional) Flower

- Not required for MVP submission.
- If needed, run a separate service from `Dockerfile.worker` with command:
  - `celery -A celery_worker.celery_app flower --port=5555`

## Gateway webhook and return URLs

Set URLs against your **API domain** (`https://api.yourdomain.com`), not frontend domain.

### Paystack

- Dashboard webhook URL:
  - `https://api.yourdomain.com/paystack/webhook/test`
- Current backend route surface includes only the test webhook path for Paystack.

### Flutterwave

- Dashboard webhook URL:
  - `https://api.yourdomain.com/flutterwave/webhook/test`
- Current backend route surface includes only the test webhook path for Flutterwave.

### Korapay

- Dashboard webhook URL:
  - `https://api.yourdomain.com/kora/webhook/test`
  - `https://api.yourdomain.com/kora/webhook/live`

### Interswitch

- Transaction webhook (dashboard-configured):
  - `https://api.yourdomain.com/interswitch/webhook/test`
  - `https://api.yourdomain.com/interswitch/webhook/live`
- Hosted checkout return URL (payload-driven by RouteX, not manual):
  - `https://api.yourdomain.com/api/v1/checkout/interswitch/return`

## Verification commands

Backend focused:

```powershell
$env:DB_URL='sqlite+aiosqlite:///./pytest_app.db'
$env:REDIS_URL='redis://localhost:6379/0'
$env:AUTH_SECRET='test-secret'
$env:AGG_SECRET='<fernet-key>'
pytest tests/test_auth_flow.py tests/test_routing_api.py tests/test_router_dashboard_api.py tests/test_interswitch_service.py tests/test_interswitch_webhooks.py -v
```

Frontend:

```powershell
Set-Location C:\Users\USER\Documents\routex\frontend
npm run build
npx playwright test
```
