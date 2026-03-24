# RouteX Platform Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build the RouteX MVP across the existing backend plus a new branded frontend for the landing page, sandbox playground, docs, and demo dashboard.

**Architecture:** Keep the current FastAPI backend as the source of truth for transactions, wallets, and gateway communication. Add a routing core, routing persistence tables, gateway health tracking, and dashboard APIs on the backend. Add a separate `Next.js` frontend inside the repo for the marketing site, embedded sandbox tester, full API reference shell, and lightweight demo dashboard.

**Tech Stack:** FastAPI, SQLAlchemy, Alembic, Redis, Celery, PostgreSQL, Next.js, React, Tailwind CSS, Scalar API Reference, Playwright, pytest

---

## Assumptions

- Backend remains at repository root
- New frontend app will live in `frontend/`
- Full API reference uses `Scalar`
- Landing-page testing uses a custom branded sandbox tester backed by a server-side proxy
- Dashboard is demo-grade, not a full production ops console

### Task 1: Scaffold the frontend app shell

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/next.config.ts`
- Create: `frontend/tsconfig.json`
- Create: `frontend/postcss.config.js`
- Create: `frontend/tailwind.config.ts`
- Create: `frontend/app/layout.tsx`
- Create: `frontend/app/page.tsx`
- Create: `frontend/app/globals.css`
- Test: `frontend/tests/landing-shell.spec.ts`

**Step 1: Write the failing smoke test**

```ts
import { test, expect } from '@playwright/test'

test('landing page renders RouteX hero shell', async ({ page }) => {
  await page.goto('http://localhost:3000')
  await expect(page.getByText('ROUTE EVERY PAYMENT')).toBeVisible()
})
```

**Step 2: Run test to verify it fails**

Run: `cd frontend; npx playwright test tests/landing-shell.spec.ts`
Expected: FAIL because the frontend app does not exist yet.

**Step 3: Scaffold the minimal Next.js app**

```tsx
export default function Page() {
  return <main>ROUTE EVERY PAYMENT</main>
}
```

**Step 4: Run test to verify it passes**

Run: `cd frontend; npx playwright test tests/landing-shell.spec.ts`
Expected: PASS

**Step 5: Commit**

```bash
git add frontend
git commit -m "feat: scaffold routex frontend shell"
```

### Task 2: Add the RouteX visual system and shared layout components

**Files:**
- Modify: `frontend/app/globals.css`
- Create: `frontend/components/layout/site-header.tsx`
- Create: `frontend/components/layout/site-footer.tsx`
- Create: `frontend/components/ui/push-button.tsx`
- Create: `frontend/components/ui/section-badge.tsx`
- Create: `frontend/components/ui/browser-mockup.tsx`
- Test: `frontend/tests/design-system.spec.ts`

**Step 1: Write the failing test**

```ts
import { test, expect } from '@playwright/test'

test('header and CTA use the branded visual system', async ({ page }) => {
  await page.goto('http://localhost:3000')
  await expect(page.getByRole('button', { name: 'Start Testing' })).toBeVisible()
  await expect(page.getByText('RouteX')).toBeVisible()
})
```

**Step 2: Run test to verify it fails**

Run: `cd frontend; npx playwright test tests/design-system.spec.ts`
Expected: FAIL because shared components are not implemented yet.

**Step 3: Implement the design tokens and shared components**

```css
:root {
  --routex-yellow: #ffe17c;
  --routex-charcoal: #171e19;
  --routex-sage: #b7c6c2;
  --routex-black: #000000;
  --shadow-hard: 4px 4px 0 0 #000000;
  --shadow-hard-lg: 8px 8px 0 0 #000000;
}
```

**Step 4: Run test to verify it passes**

Run: `cd frontend; npx playwright test tests/design-system.spec.ts`
Expected: PASS

**Step 5: Commit**

```bash
git add frontend/app/globals.css frontend/components
git commit -m "feat: add routex landing page design system"
```

### Task 3: Build the full marketing landing page sections

**Files:**
- Modify: `frontend/app/page.tsx`
- Create: `frontend/components/sections/hero-section.tsx`
- Create: `frontend/components/sections/trust-marquee.tsx`
- Create: `frontend/components/sections/problem-solution.tsx`
- Create: `frontend/components/sections/feature-grid.tsx`
- Create: `frontend/components/sections/how-it-works.tsx`
- Create: `frontend/components/sections/use-cases.tsx`
- Create: `frontend/components/sections/proof-section.tsx`
- Create: `frontend/components/sections/final-cta.tsx`
- Test: `frontend/tests/landing-sections.spec.ts`

**Step 1: Write the failing test**

```ts
import { test, expect } from '@playwright/test'

test('landing page includes the key product sections', async ({ page }) => {
  await page.goto('http://localhost:3000')
  await expect(page.getByText('Smart Routing')).toBeVisible()
  await expect(page.getByText('How It Works')).toBeVisible()
  await expect(page.getByText('READY TO ROUTE SMARTER?')).toBeVisible()
})
```

**Step 2: Run test to verify it fails**

Run: `cd frontend; npx playwright test tests/landing-sections.spec.ts`
Expected: FAIL

**Step 3: Implement the landing page sections**

```tsx
export default function Page() {
  return (
    <>
      <SiteHeader />
      <HeroSection />
      <TrustMarquee />
      <ProblemSolution />
      <FeatureGrid />
      <HowItWorks />
      <UseCases />
      <ProofSection />
      <FinalCta />
      <SiteFooter />
    </>
  )
}
```

**Step 4: Run test to verify it passes**

Run: `cd frontend; npx playwright test tests/landing-sections.spec.ts`
Expected: PASS

**Step 5: Commit**

```bash
git add frontend/app/page.tsx frontend/components/sections
git commit -m "feat: build routex landing page sections"
```

### Task 4: Add the branded sandbox playground and full docs route

**Files:**
- Create: `frontend/app/docs/page.tsx`
- Create: `frontend/app/api/playground/route.ts`
- Create: `frontend/components/playground/api-playground.tsx`
- Create: `frontend/components/playground/request-panel.tsx`
- Create: `frontend/components/playground/response-panel.tsx`
- Create: `frontend/components/docs/reference-shell.tsx`
- Create: `frontend/lib/playground-endpoints.ts`
- Create: `frontend/lib/openapi.ts`
- Modify: `frontend/app/page.tsx`
- Test: `frontend/tests/playground.spec.ts`

**Step 1: Write the failing test**

```ts
import { test, expect } from '@playwright/test'

test('sandbox playground renders on the landing page', async ({ page }) => {
  await page.goto('http://localhost:3000')
  await expect(page.getByText('Sandbox only')).toBeVisible()
  await expect(page.getByRole('button', { name: 'Send Request' })).toBeVisible()
})
```

**Step 2: Run test to verify it fails**

Run: `cd frontend; npx playwright test tests/playground.spec.ts`
Expected: FAIL

**Step 3: Implement the playground and docs shell**

```ts
export const ALLOWED_PLAYGROUND_ENDPOINTS = [
  '/api/v1/initiate',
  '/api/v1/transactions/verify',
  '/api/v1/payout',
]
```

**Step 4: Run test to verify it passes**

Run: `cd frontend; npx playwright test tests/playground.spec.ts`
Expected: PASS

**Step 5: Commit**

```bash
git add frontend/app/docs frontend/app/api/playground frontend/components/playground frontend/components/docs frontend/lib
git commit -m "feat: add routex playground and docs shell"
```

### Task 5: Add routing persistence models and the database migration

**Files:**
- Create: `database/models/RoutingAttempt.py`
- Create: `database/models/GatewayHealthSnapshot.py`
- Create: `database/models/RoutingDecisionAudit.py`
- Modify: `database/models/__init__.py`
- Modify: `database/models/Processor.py`
- Modify: `database/models/Transaction.py`
- Create: `alembic/versions/20260325_01_add_routing_tables.py`
- Test: `tests/test_routing_models.py`

**Step 1: Write the failing test**

```python
def test_can_create_routing_attempt_record(session, seeded_transaction):
    attempt = RoutingAttempt(transaction_id=seeded_transaction.id, attempt_no=1, gateway_code="pstk")
    session.add(attempt)
    session.commit()
    assert attempt.id is not None
```

**Step 2: Run test to verify it fails**

Run: `cd .; pytest tests/test_routing_models.py -v`
Expected: FAIL because the routing models do not exist yet.

**Step 3: Implement the models and migration**

```python
class RoutingAttempt(Base):
    __tablename__ = "routing_attempts"
```

**Step 4: Run test to verify it passes**

Run: `cd .; pytest tests/test_routing_models.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add database/models alembic/versions/20260325_01_add_routing_tables.py tests/test_routing_models.py
git commit -m "feat: add routing persistence models"
```

### Task 6: Build the gateway adapter abstraction and routing service

**Files:**
- Create: `external_services/adapters/base.py`
- Create: `external_services/adapters/paystack_adapter.py`
- Create: `external_services/adapters/flutterwave_adapter.py`
- Create: `external_services/adapters/korapay_adapter.py`
- Create: `external_services/adapters/interswitch_adapter.py`
- Create: `services/routingService.py`
- Create: `services/gatewayHealthService.py`
- Modify: `services/transactionService.py`
- Test: `tests/test_routing_service.py`

**Step 1: Write the failing test**

```python
async def test_selects_highest_scoring_eligible_gateway(async_session):
    selected, ranked = await routingService.select_gateway(
        session=async_session,
        operation="collection",
        currency="NGN",
        amount=5000,
        merchant_id="m_123",
    )
    assert selected in ["pstk", "fltw", "kora", "isw"]
    assert ranked[0] == selected
```

**Step 2: Run test to verify it fails**

Run: `cd .; pytest tests/test_routing_service.py -v`
Expected: FAIL

**Step 3: Implement the adapter contract and routing service**

```python
class GatewayAdapter(Protocol):
    async def initialize_collection(self, **kwargs): ...
    async def initiate_payout(self, **kwargs): ...
    async def verify_transaction(self, **kwargs): ...
```

**Step 4: Run test to verify it passes**

Run: `cd .; pytest tests/test_routing_service.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add external_services/adapters services/routingService.py services/gatewayHealthService.py tests/test_routing_service.py
git commit -m "feat: add gateway adapters and routing service"
```

### Task 7: Refactor collections and payouts to use the router

**Files:**
- Modify: `api/v1/initialize.py`
- Modify: `api/v1/payout.py`
- Modify: `api/v1/verify_transaction.py`
- Modify: `schemas/v1Schema.py`
- Create: `schemas/routerSchema.py`
- Test: `tests/test_routing_api.py`

**Step 1: Write the failing API tests**

```python
def test_initiate_returns_selected_gateway(client, merchant_headers):
    response = client.post("/api/v1/initiate", json=sample_init_payload, headers=merchant_headers)
    assert response.status_code == 200
    assert "selected_gateway" in response.json()
```

**Step 2: Run test to verify it fails**

Run: `cd .; pytest tests/test_routing_api.py -v`
Expected: FAIL because the response does not include router metadata yet.

**Step 3: Wire the endpoints through the routing service**

```python
decision = await routingService.route_collection(...)
return JSONResponse(content=decision.to_response(), status_code=200)
```

**Step 4: Run test to verify it passes**

Run: `cd .; pytest tests/test_routing_api.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add api/v1/initialize.py api/v1/payout.py api/v1/verify_transaction.py schemas
git commit -m "feat: route collections and payouts through routing core"
```

### Task 8: Normalize webhooks and reconciliation behavior

**Files:**
- Modify: `api/v1/webhooks.py`
- Create: `services/webhookNormalizationService.py`
- Create: `services/reconciliationService.py`
- Test: `tests/test_webhook_normalization.py`

**Step 1: Write the failing webhook test**

```python
async def test_duplicate_webhook_is_idempotent(async_session, seeded_transaction):
    await webhookNormalizationService.handle_event("pstk", sample_payload, async_session)
    await webhookNormalizationService.handle_event("pstk", sample_payload, async_session)
    updated = await transactionService.get_transaction_by_id(async_session, seeded_transaction.id)
    assert updated.status == "success"
```

**Step 2: Run test to verify it fails**

Run: `cd .; pytest tests/test_webhook_normalization.py -v`
Expected: FAIL

**Step 3: Implement normalization and idempotent reconciliation**

```python
if transaction.status != TransactionStatus.PENDING.value:
    return
```

**Step 4: Run test to verify it passes**

Run: `cd .; pytest tests/test_webhook_normalization.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add api/v1/webhooks.py services/webhookNormalizationService.py services/reconciliationService.py tests/test_webhook_normalization.py
git commit -m "feat: normalize router webhooks and reconciliation"
```

### Task 9: Add router analytics and admin control endpoints

**Files:**
- Create: `api/views/routerView.py`
- Create: `services/routerAnalyticsService.py`
- Create: `services/routerAdminService.py`
- Create: `schemas/routerAnalyticsSchema.py`
- Modify: `api/urls/router.py`
- Test: `tests/test_router_dashboard_api.py`

**Step 1: Write the failing test**

```python
def test_router_dashboard_summary_requires_auth(client):
    response = client.get("/analytics/router/dashboard")
    assert response.status_code in [401, 403]
```

**Step 2: Run test to verify it fails**

Run: `cd .; pytest tests/test_router_dashboard_api.py -v`
Expected: FAIL because the endpoint does not exist yet.

**Step 3: Implement router dashboard and admin APIs**

```python
@router_analytics.get("/analytics/router/dashboard")
async def get_router_dashboard(...):
    return {"gateway_health": [], "recent_failovers": []}
```

**Step 4: Run test to verify it passes**

Run: `cd .; pytest tests/test_router_dashboard_api.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add api/views/routerView.py services/routerAnalyticsService.py services/routerAdminService.py schemas/routerAnalyticsSchema.py api/urls/router.py tests/test_router_dashboard_api.py
git commit -m "feat: add router analytics and admin endpoints"
```

### Task 10: Build the demo dashboard frontend

**Files:**
- Create: `frontend/app/dashboard/page.tsx`
- Create: `frontend/components/dashboard/gateway-health-grid.tsx`
- Create: `frontend/components/dashboard/recent-transactions.tsx`
- Create: `frontend/components/dashboard/failover-feed.tsx`
- Create: `frontend/components/dashboard/score-breakdown-card.tsx`
- Create: `frontend/lib/dashboard-api.ts`
- Test: `frontend/tests/dashboard.spec.ts`

**Step 1: Write the failing test**

```ts
import { test, expect } from '@playwright/test'

test('dashboard shows gateway health and recent transactions', async ({ page }) => {
  await page.goto('http://localhost:3000/dashboard')
  await expect(page.getByText('Gateway Health')).toBeVisible()
  await expect(page.getByText('Recent Transactions')).toBeVisible()
})
```

**Step 2: Run test to verify it fails**

Run: `cd frontend; npx playwright test tests/dashboard.spec.ts`
Expected: FAIL

**Step 3: Implement the dashboard page**

```tsx
export default function DashboardPage() {
  return (
    <main>
      <GatewayHealthGrid />
      <RecentTransactions />
      <FailoverFeed />
    </main>
  )
}
```

**Step 4: Run test to verify it passes**

Run: `cd frontend; npx playwright test tests/dashboard.spec.ts`
Expected: PASS

**Step 5: Commit**

```bash
git add frontend/app/dashboard frontend/components/dashboard frontend/lib/dashboard-api.ts frontend/tests/dashboard.spec.ts
git commit -m "feat: add routex demo dashboard frontend"
```

### Task 11: Expose a public-safe OpenAPI source for docs and playground

**Files:**
- Modify: `api/views/docs.py`
- Modify: `main.py`
- Create: `services/openapiService.py`
- Test: `tests/test_openapi_public.py`

**Step 1: Write the failing test**

```python
def test_public_openapi_hides_private_dashboard_routes(client):
    response = client.get("/public/openapi.json")
    assert response.status_code == 200
    paths = response.json()["paths"]
    assert "/login" not in paths
```

**Step 2: Run test to verify it fails**

Run: `cd .; pytest tests/test_openapi_public.py -v`
Expected: FAIL because the endpoint does not exist yet.

**Step 3: Implement a sanitized public OpenAPI endpoint**

```python
@docs_router.get("/public/openapi.json")
def public_openapi():
    return JSONResponse(build_public_openapi())
```

**Step 4: Run test to verify it passes**

Run: `cd .; pytest tests/test_openapi_public.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add api/views/docs.py main.py services/openapiService.py tests/test_openapi_public.py
git commit -m "feat: expose public-safe openapi for docs and playground"
```

### Task 12: Run integrated verification and write final docs

**Files:**
- Modify: `README.md`
- Modify: `docs/multi-payment-router-prd.md`
- Modify: `tasks/todo.md`

**Step 1: Add final verification commands to the docs**

```md
- Backend tests: `pytest`
- Frontend tests: `npx playwright test`
- Frontend build: `npm run build`
```

**Step 2: Run backend verification**

Run: `cd .; pytest`
Expected: PASS with `0` failures.

**Step 3: Run frontend verification**

Run: `cd frontend; npm run build`
Expected: PASS

**Step 4: Run smoke E2E**

Run: `cd frontend; npx playwright test`
Expected: PASS

**Step 5: Commit**

```bash
git add README.md docs/multi-payment-router-prd.md tasks/todo.md
git commit -m "docs: finalize routex implementation guidance"
```

## Execution Notes

- Build the frontend and backend in parallel only after the public API contract and routing models are stable.
- Prioritize the custom sandbox playground early, because it is part of the landing page value proposition.
- Keep the first dashboard version read-only.
- Treat payout failover as a controlled flow, not an aggressive retry system.

## Recommended Delivery Order

1. Backend routing persistence
2. Routing service and adapters
3. Collections API refactor
4. Webhook normalization
5. Public OpenAPI endpoint
6. Frontend landing page
7. Playground and docs
8. Dashboard
9. Final verification

Plan complete and saved to `docs/plans/2026-03-25-routex-platform-implementation-plan.md`. Two execution options:

**1. Subagent-Driven (this session)** - I dispatch fresh subagent per task, review between tasks, fast iteration

**2. Parallel Session (separate)** - Open new session with executing-plans, batch execution with checkpoints

**Which approach?**

