# RouteX

RouteX is a hackathon MVP for a multi-payment router built on top of the existing `x-aggregator` backend. It gives merchants one integration for collections and payouts, routes collections across multiple gateways, records routing decisions, normalizes webhooks, and exposes a branded frontend for the landing page, docs, playground, and demo dashboard.

## Implemented MVP

- Unified collections routing through `Paystack`, `Flutterwave`, `Korapay`, and `Interswitch Quickteller Business`
- Signed Interswitch transaction webhooks for asynchronous collection updates
- RouteX-owned Interswitch return flow with a branded verified payment-status page
- Unified payout flow through the routing core with conservative retry behavior
- Routing persistence with decision audits, attempt records, and gateway health snapshots
- Background gateway health refresh via Celery beat
- Normalized webhook handling plus reconciliation markers for ambiguous states
- Admin and analytics endpoints for gateway health, recent transactions, and failovers
- Global admin routing rules with allowlists, denylists, and forced priority order before score-based selection
- Neo-brutalist `Next.js` frontend with:
  - marketing landing page
  - embedded sandbox API console
  - public docs page backed by the sanitized OpenAPI contract
  - demo dashboard with gateway control overrides, health refresh visibility, global routing rule management, live-mode polling, and per-transaction observability drill-down

## Repo Layout

- [main.py](C:/Users/USER/Documents/routex/main.py): FastAPI app entrypoint
- [api](C:/Users/USER/Documents/routex/api): API routers and views
- [services](C:/Users/USER/Documents/routex/services): routing, analytics, webhook normalization, and support services
- [database/models](C:/Users/USER/Documents/routex/database/models): SQLAlchemy models, including routing tables
- [external_services/adapters](C:/Users/USER/Documents/routex/external_services/adapters): gateway adapter layer
- [frontend](C:/Users/USER/Documents/routex/frontend): landing page, docs, playground, dashboard, and Playwright tests
- [docs](C:/Users/USER/Documents/routex/docs): PRD and planning documents
- [tests](C:/Users/USER/Documents/routex/tests): backend pytest suites

## Key Routes

- Landing page: `/`
- Public docs page: `/docs`
- Demo dashboard: `/dashboard`
- Dashboard transaction detail: `/dashboard/transactions/{reference}`
- Public-safe OpenAPI export: `/public/openapi.json`
- Landing-page sandbox proxy: `/api/playground`
- Admin routing rules: `/admin/router/rules`, `/admin/router/rules/{rule_id}`
- Interswitch hosted checkout bridge: `/api/v1/checkout/interswitch/{processor_reference}`
- Interswitch return endpoint: `/api/v1/checkout/interswitch/return`
- Interswitch webhook endpoints: `/interswitch/webhook/test`, `/interswitch/webhook/live`
- RouteX payment-status page: `/pay/status`

## Environment

Start with [.env.example](C:/Users/USER/Documents/routex/.env.example) for backend configuration.

Frontend integrations also use these optional server-side variables:

- `ROUTEX_API_BASE_URL`: backend base URL used by the frontend docs page, dashboard, and playground proxy
- `ROUTEX_ADMIN_TOKEN`: admin bearer token used by the demo dashboard when calling backend analytics endpoints
- `ROUTEX_PLAYGROUND_SECRET_KEY`: sandbox merchant secret used by the landing-page playground proxy
- `NEXT_PUBLIC_ROUTEX_API_BASE_URL`: optional public fallback for read-only frontend fetches

Backend payment configuration now also includes Interswitch Quickteller Business variables:

- `INTERSWITCH_MERCHANT_CODE`
- `INTERSWITCH_PAY_ITEM_ID`
- `INTERSWITCH_CLIENT_ID`
- `INTERSWITCH_SECRET_KEY`

For the current hosted checkout slice:

- collections use a RouteX bridge page that auto-posts the required form fields to Interswitch
- Interswitch redirects back into RouteX first through `/api/v1/checkout/interswitch/return`
- RouteX verifies the payment server-side and then sends the customer to `/pay/status`
- verify uses a server-side transaction requery against Interswitch before RouteX returns the status
- `INTERSWITCH_MERCHANT_CODE` is required for verify and `INTERSWITCH_PAY_ITEM_ID` is required for hosted checkout
- `INTERSWITCH_SECRET_KEY` is used to validate `X-Interswitch-Signature` on incoming transaction webhooks

If the frontend vars are not set:

- `/docs` falls back to the static endpoint catalog
- `/dashboard` and `/dashboard/transactions/{reference}` fall back to demo data
- `/dashboard` routing-rule management falls back to seeded demo policy data
- the landing-page playground returns branded demo responses instead of live sandbox calls

## Local Development

### Backend

1. Install Python dependencies:

```powershell
pip install -r requirements.txt
```

2. Configure environment variables from [.env.example](C:/Users/USER/Documents/routex/.env.example).

3. Run the FastAPI app:

```powershell
uvicorn main:app --reload
```

4. Optional but recommended for live router-health refresh:

```powershell
celery -A celery_worker.celery_app worker --loglevel=info
celery -A celery_worker.celery_app beat --loglevel=info
```

### Frontend

1. Install frontend dependencies:

```powershell
Set-Location C:\Users\USER\Documents\routex\frontend
npm install
```

2. Run the frontend:

```powershell
npm run dev
```

## Verification

### Backend Router-Focused Suite

Use the test-only env overrides below for the routed backend suites:

```powershell
$env:DB_URL='sqlite+aiosqlite:///./pytest_app.db'
$env:REDIS_URL='redis://localhost:6379/0'
$env:AUTH_SECRET='test-secret'
$env:AGG_SECRET='<fernet-key>'
pytest tests/test_routing_models.py tests/test_routing_service.py tests/test_routing_api.py tests/test_webhook_normalization.py tests/test_v1_api.py tests/test_router_dashboard_api.py tests/test_openapi_public.py -v
pytest tests/test_transaction_endpoints.py -k WebhookWalletIntegration -v
pytest tests/test_gateway_health_refresh.py tests/test_routing_service.py tests/test_router_dashboard_api.py -v
pytest tests/test_interswitch_service.py tests/test_routing_api.py tests/test_routing_service.py -v
pytest tests/test_webhook_normalization.py tests/test_interswitch_webhooks.py tests/test_interswitch_service.py tests/test_routing_api.py -v
pytest tests/test_interswitch_service.py tests/test_interswitch_return_flow.py tests/test_routing_api.py -v
```

To generate a Fernet key for `AGG_SECRET`:

```powershell
@'
from cryptography.fernet import Fernet
print(Fernet.generate_key().decode())
'@ | python -
```

### Frontend Build and E2E

```powershell
Set-Location C:\Users\USER\Documents\routex\frontend
npm run build
npx playwright test
```

Note: the Playwright config already starts the built app. Run `npm run build` and `npx playwright test` sequentially, not at the same time.

## Hackathon Demo Flow

1. Open `/` and show the product story plus the embedded sandbox console.
2. Open `/docs` and show the public API contract backed by `/public/openapi.json`.
3. Use `/dashboard` to show gateway health, freshness timestamps, recent routed transactions, failovers, manual gateway overrides, and the `Refresh Health Now` action.
4. Create or pause a routing rule in the dashboard to show how operators can force gateway eligibility or ordering before scoring.
5. Open a routed transaction from the dashboard list and show `/dashboard/transactions/{reference}` with the routing reason, score breakdown, attempts timeline, failover summary, and webhook trace.
6. Show a collection routed to `Interswitch`, open the RouteX bridge checkout page, and explain that the user is being POSTed into Quickteller Business without changing the merchant API contract.
7. Complete the Interswitch payment and land on `/pay/status`, then show that RouteX verified the return server-side before the customer sees the final status.
8. Verify that same transaction through `GET /api/v1/transactions/verify` and show that RouteX requeries Interswitch server-side before returning the final status.
9. Deliver a signed `TRANSACTION.COMPLETED` webhook to `/interswitch/webhook/test` and show that RouteX updates the transaction asynchronously.
10. Demonstrate that the same frontend can run in fallback mode without backend env wiring or in live sandbox mode when the frontend env vars are configured.

## Planning Docs

- PRD: [multi-payment-router-prd.md](C:/Users/USER/Documents/routex/docs/multi-payment-router-prd.md)
- Landing page UI spec: [2026-03-25-routex-landing-page-ui-spec.md](C:/Users/USER/Documents/routex/docs/plans/2026-03-25-routex-landing-page-ui-spec.md)
- Platform implementation plan: [2026-03-25-routex-platform-implementation-plan.md](C:/Users/USER/Documents/routex/docs/plans/2026-03-25-routex-platform-implementation-plan.md)
