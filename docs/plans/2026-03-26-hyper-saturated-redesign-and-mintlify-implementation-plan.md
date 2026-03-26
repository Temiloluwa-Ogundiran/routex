# RouteX Hyper-Saturated Redesign And Mintlify Migration Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Rebuild the full RouteX product experience around the new hyper-saturated fluid design system, migrate public docs and API testing to Mintlify at `/docs`, and redesign user-facing email templates.

**Architecture:** Keep the current backend contracts and frontend proxy/auth model, but replace the UI system across landing, auth, dashboard, and admin. Introduce a tracked `mintlify-docs/` app for curated public developer docs and reverse-proxy `/docs` to Mintlify using the official subpath setup. Remove the standalone sandbox page and route users into Mintlify for API testing.

**Tech Stack:** Next.js app router, React, existing frontend proxy routes, FastAPI backend, Resend email delivery, Mintlify docs app, Playwright, pytest.

---

### Task 1: Establish The Shared Brand Foundation

**Files:**
- Modify: `C:/Users/USER/Documents/routex/frontend/app/globals.css`
- Modify: `C:/Users/USER/Documents/routex/frontend/app/layout.tsx`
- Test: `C:/Users/USER/Documents/routex/frontend/tests/design-system.spec.ts`
- Test: `C:/Users/USER/Documents/routex/frontend/tests/landing-shell.spec.ts`

**Step 1: Write the failing test**

Add Playwright assertions that the landing shell exposes the new yellow/void composition, pill CTAs, and high-contrast typography instead of the old boxed layout.

**Step 2: Run test to verify it fails**

Run: `npx playwright test tests/design-system.spec.ts tests/landing-shell.spec.ts`
Expected: FAIL because the old global tokens and shell are still present.

**Step 3: Write minimal implementation**

- Replace the current color tokens with the new yellow/onyx/charcoal system.
- Swap the root font to `Inter`.
- Add reusable utilities for liquid sections, glass cards, pill buttons, and dark void panels.
- Update global selection, focus, and scrollbar styling so the design system feels consistent across pages.

**Step 4: Run test to verify it passes**

Run: `npx playwright test tests/design-system.spec.ts tests/landing-shell.spec.ts`
Expected: PASS

**Step 5: Commit**

```bash
git add frontend/app/globals.css frontend/app/layout.tsx frontend/tests/design-system.spec.ts frontend/tests/landing-shell.spec.ts
git commit -m "feat: add routex hyper-saturated design foundation"
```

### Task 2: Rebuild The Global Header And Footer

**Files:**
- Modify: `C:/Users/USER/Documents/routex/frontend/components/layout/site-header.tsx`
- Modify: `C:/Users/USER/Documents/routex/frontend/components/layout/site-header-client.tsx`
- Modify: `C:/Users/USER/Documents/routex/frontend/components/layout/site-footer.tsx`
- Test: `C:/Users/USER/Documents/routex/frontend/tests/navigation.spec.ts`

**Step 1: Write the failing test**

Add assertions that:
- guests see concise public CTAs
- signed-in merchants no longer see `Log in`
- the footer only exposes useful, working links
- sandbox navigation points to docs instead of a standalone tester page

**Step 2: Run test to verify it fails**

Run: `npx playwright test tests/navigation.spec.ts`
Expected: FAIL

**Step 3: Write minimal implementation**

- Rebuild the header and footer in the new brand system.
- Remove redundant or broken footer links.
- Make signed-in actions route to `/dashboard`, `/admin`, `/docs`, and sign-out correctly.
- Replace any remaining standalone sandbox CTA with a docs CTA.

**Step 4: Run test to verify it passes**

Run: `npx playwright test tests/navigation.spec.ts`
Expected: PASS

**Step 5: Commit**

```bash
git add frontend/components/layout/site-header.tsx frontend/components/layout/site-header-client.tsx frontend/components/layout/site-footer.tsx frontend/tests/navigation.spec.ts
git commit -m "feat: rebuild routex global shell"
```

### Task 3: Rebuild The Marketing Landing Experience

**Files:**
- Modify: `C:/Users/USER/Documents/routex/frontend/app/page.tsx`
- Modify: `C:/Users/USER/Documents/routex/frontend/components/sections/hero-section.tsx`
- Modify: `C:/Users/USER/Documents/routex/frontend/components/sections/problem-solution.tsx`
- Modify: `C:/Users/USER/Documents/routex/frontend/components/sections/how-it-works.tsx`
- Modify: `C:/Users/USER/Documents/routex/frontend/components/sections/feature-grid.tsx`
- Modify: `C:/Users/USER/Documents/routex/frontend/components/sections/use-cases.tsx`
- Modify: `C:/Users/USER/Documents/routex/frontend/components/sections/proof-section.tsx`
- Modify: `C:/Users/USER/Documents/routex/frontend/components/sections/trust-marquee.tsx`
- Modify: `C:/Users/USER/Documents/routex/frontend/components/sections/final-cta.tsx`
- Test: `C:/Users/USER/Documents/routex/frontend/tests/landing-sections.spec.ts`

**Step 1: Write the failing test**

Add assertions that the landing page now exposes:
- a loud yellow hero
- dark void feature sections
- concise copy
- docs and signup CTAs
- no embedded sandbox or custom docs widgets

**Step 2: Run test to verify it fails**

Run: `npx playwright test tests/landing-sections.spec.ts`
Expected: FAIL

**Step 3: Write minimal implementation**

- Replace the current stacked sections with liquid, asymmetrical composition.
- Introduce glassmorphic product cards and bold hero typography.
- Keep copy tight and product-forward.
- Remove any lingering inline API tester or verbose developer explainer content from the public homepage.

**Step 4: Run test to verify it passes**

Run: `npx playwright test tests/landing-sections.spec.ts`
Expected: PASS

**Step 5: Commit**

```bash
git add frontend/app/page.tsx frontend/components/sections/hero-section.tsx frontend/components/sections/problem-solution.tsx frontend/components/sections/how-it-works.tsx frontend/components/sections/feature-grid.tsx frontend/components/sections/use-cases.tsx frontend/components/sections/proof-section.tsx frontend/components/sections/trust-marquee.tsx frontend/components/sections/final-cta.tsx frontend/tests/landing-sections.spec.ts
git commit -m "feat: redesign routex landing page"
```

### Task 4: Redesign The Auth Journey

**Files:**
- Modify: `C:/Users/USER/Documents/routex/frontend/app/login/page.tsx`
- Modify: `C:/Users/USER/Documents/routex/frontend/app/signup/page.tsx`
- Modify: `C:/Users/USER/Documents/routex/frontend/app/verify-otp/page.tsx`
- Modify: `C:/Users/USER/Documents/routex/frontend/app/forgot-password/page.tsx`
- Modify: `C:/Users/USER/Documents/routex/frontend/app/reset-password/page.tsx`
- Modify: `C:/Users/USER/Documents/routex/frontend/components/auth/auth-form-shell.tsx`
- Modify: `C:/Users/USER/Documents/routex/frontend/components/auth/otp-form-shell.tsx`
- Modify: `C:/Users/USER/Documents/routex/frontend/lib/auth-session.ts`
- Test: `C:/Users/USER/Documents/routex/frontend/tests/auth.spec.ts`

**Step 1: Write the failing test**

Add assertions that:
- auth pages use clean product copy
- the `User access` badge renders correctly
- no internal session/jwt wording is exposed
- signed-in users stay authenticated across navigation after OTP verification

**Step 2: Run test to verify it fails**

Run: `npx playwright test tests/auth.spec.ts`
Expected: FAIL

**Step 3: Write minimal implementation**

- Rebuild auth pages around a single glass-card pattern on a liquid background.
- Simplify login/signup/OTP copy so it reads like product UI, not internal implementation notes.
- Keep the existing secure cookie-backed auth flow intact through route changes.
- Fix any layout bugs around the top badge, subcopy, and CTA alignment.

**Step 4: Run test to verify it passes**

Run: `npx playwright test tests/auth.spec.ts`
Expected: PASS

**Step 5: Commit**

```bash
git add frontend/app/login/page.tsx frontend/app/signup/page.tsx frontend/app/verify-otp/page.tsx frontend/app/forgot-password/page.tsx frontend/app/reset-password/page.tsx frontend/components/auth/auth-form-shell.tsx frontend/components/auth/otp-form-shell.tsx frontend/lib/auth-session.ts frontend/tests/auth.spec.ts
git commit -m "feat: redesign routex auth flow"
```

### Task 5: Redesign The Merchant Dashboard

**Files:**
- Modify: `C:/Users/USER/Documents/routex/frontend/app/dashboard/page.tsx`
- Modify: `C:/Users/USER/Documents/routex/frontend/components/app/merchant-dashboard-shell.tsx`
- Modify: `C:/Users/USER/Documents/routex/frontend/lib/app-dashboard.ts`
- Test: `C:/Users/USER/Documents/routex/frontend/tests/dashboard.spec.ts`

**Step 1: Write the failing test**

Add assertions that:
- the merchant dashboard uses the new dark/yellow glass design
- top actions show `API docs`, `Sandbox`, and `Sign out` in the correct form
- users remain signed in while navigating to docs and back

**Step 2: Run test to verify it fails**

Run: `npx playwright test tests/dashboard.spec.ts`
Expected: FAIL

**Step 3: Write minimal implementation**

- Rebuild the merchant dashboard shell with calmer but consistent brand styling.
- Keep the current live backend data wiring.
- Route docs/testing actions into Mintlify instead of the old standalone sandbox.
- Preserve merchant mode switching and workspace navigation.

**Step 4: Run test to verify it passes**

Run: `npx playwright test tests/dashboard.spec.ts`
Expected: PASS

**Step 5: Commit**

```bash
git add frontend/app/dashboard/page.tsx frontend/components/app/merchant-dashboard-shell.tsx frontend/lib/app-dashboard.ts frontend/tests/dashboard.spec.ts
git commit -m "feat: redesign merchant dashboard experience"
```

### Task 6: Redesign The Admin Control Room

**Files:**
- Modify: `C:/Users/USER/Documents/routex/frontend/app/admin/page.tsx`
- Modify: `C:/Users/USER/Documents/routex/frontend/app/admin/login/page.tsx`
- Modify: `C:/Users/USER/Documents/routex/frontend/components/dashboard/dashboard-console.tsx`
- Modify: `C:/Users/USER/Documents/routex/frontend/components/dashboard/gateway-health-grid.tsx`
- Modify: `C:/Users/USER/Documents/routex/frontend/components/dashboard/gateway-control-panel.tsx`
- Modify: `C:/Users/USER/Documents/routex/frontend/components/dashboard/routing-rules-panel.tsx`
- Modify: `C:/Users/USER/Documents/routex/frontend/components/dashboard/failover-feed.tsx`
- Modify: `C:/Users/USER/Documents/routex/frontend/components/dashboard/recent-transactions.tsx`
- Modify: `C:/Users/USER/Documents/routex/frontend/components/dashboard/score-breakdown-card.tsx`
- Modify: `C:/Users/USER/Documents/routex/frontend/components/dashboard/transaction-detail-shell.tsx`
- Test: `C:/Users/USER/Documents/routex/frontend/tests/admin.spec.ts`

**Step 1: Write the failing test**

Add assertions that the admin login page no longer exposes internal copy and that the admin dashboard renders in the new high-contrast system without losing access to router controls.

**Step 2: Run test to verify it fails**

Run: `npx playwright test tests/admin.spec.ts`
Expected: FAIL

**Step 3: Write minimal implementation**

- Redesign the admin login and control room to match the shared brand system.
- Keep gateway health, routing rules, recent transactions, and drill-downs readable.
- Preserve the admin auth split from the merchant dashboard.

**Step 4: Run test to verify it passes**

Run: `npx playwright test tests/admin.spec.ts`
Expected: PASS

**Step 5: Commit**

```bash
git add frontend/app/admin/page.tsx frontend/app/admin/login/page.tsx frontend/components/dashboard/dashboard-console.tsx frontend/components/dashboard/gateway-health-grid.tsx frontend/components/dashboard/gateway-control-panel.tsx frontend/components/dashboard/routing-rules-panel.tsx frontend/components/dashboard/failover-feed.tsx frontend/components/dashboard/recent-transactions.tsx frontend/components/dashboard/score-breakdown-card.tsx frontend/components/dashboard/transaction-detail-shell.tsx frontend/tests/admin.spec.ts
git commit -m "feat: redesign admin control room"
```

### Task 7: Retire The Standalone Sandbox And Old Docs UI

**Files:**
- Modify: `C:/Users/USER/Documents/routex/frontend/app/sandbox/page.tsx`
- Modify: `C:/Users/USER/Documents/routex/frontend/app/docs/page.tsx`
- Modify: `C:/Users/USER/Documents/routex/frontend/app/api/playground/route.ts`
- Modify: `C:/Users/USER/Documents/routex/frontend/app/api/playground/status/route.ts`
- Modify: `C:/Users/USER/Documents/routex/frontend/lib/playground-access.ts`
- Modify: `C:/Users/USER/Documents/routex/frontend/lib/playground-endpoints.ts`
- Modify: `C:/Users/USER/Documents/routex/frontend/components/docs/reference-shell.tsx`
- Test: `C:/Users/USER/Documents/routex/frontend/tests/docs.spec.ts`
- Test: `C:/Users/USER/Documents/routex/frontend/tests/playground.spec.ts`

**Step 1: Write the failing test**

Add assertions that:
- `/sandbox` redirects into `/docs`
- `/docs` no longer renders the old custom docs UI
- the old custom playground is no longer the primary public testing experience

**Step 2: Run test to verify it fails**

Run: `npx playwright test tests/docs.spec.ts tests/playground.spec.ts`
Expected: FAIL

**Step 3: Write minimal implementation**

- Replace `/sandbox` with a redirect or handoff page into Mintlify docs.
- Strip the existing custom docs shell down to a temporary bridge layer only.
- Remove obsolete playground messaging from the old docs surface.
- Keep only the minimum code needed until Mintlify is fully wired in.

**Step 4: Run test to verify it passes**

Run: `npx playwright test tests/docs.spec.ts tests/playground.spec.ts`
Expected: PASS

**Step 5: Commit**

```bash
git add frontend/app/sandbox/page.tsx frontend/app/docs/page.tsx frontend/app/api/playground/route.ts frontend/app/api/playground/status/route.ts frontend/lib/playground-access.ts frontend/lib/playground-endpoints.ts frontend/components/docs/reference-shell.tsx frontend/tests/docs.spec.ts frontend/tests/playground.spec.ts
git commit -m "feat: retire legacy docs and sandbox surfaces"
```

### Task 8: Redesign The RouteX Email Template

**Files:**
- Modify: `C:/Users/USER/Documents/routex/templates/otp.html`
- Modify: `C:/Users/USER/Documents/routex/services/emailService.py`
- Modify: `C:/Users/USER/Documents/routex/services/receiptService.py`
- Test: `C:/Users/USER/Documents/routex/tests/test_email_service.py`

**Step 1: Write the failing test**

Add or update a template render check that verifies the OTP email uses RouteX branding, clean product copy, and no leftover template tags or old-brand references.

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_email_service.py -q`
Expected: FAIL or missing coverage that reflects the new template structure.

**Step 3: Write minimal implementation**

- Replace the current OTP email with a black/yellow premium layout that still renders safely across inboxes.
- Fix the copy so it is concise, branded, and free of internal implementation language.
- Align email subjects and any receipt-facing helpers in the backend with the new RouteX language.

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_email_service.py -q`
Expected: PASS

**Step 5: Commit**

```bash
git add templates/otp.html services/emailService.py services/receiptService.py tests/test_email_service.py
git commit -m "feat: redesign routex email template"
```

### Task 9: Create The Mintlify Docs App

**Files:**
- Create: `C:/Users/USER/Documents/routex/mintlify-docs/docs.json`
- Create: `C:/Users/USER/Documents/routex/mintlify-docs/index.mdx`
- Create: `C:/Users/USER/Documents/routex/mintlify-docs/authentication.mdx`
- Create: `C:/Users/USER/Documents/routex/mintlify-docs/collections.mdx`
- Create: `C:/Users/USER/Documents/routex/mintlify-docs/verification.mdx`
- Create: `C:/Users/USER/Documents/routex/mintlify-docs/payouts.mdx`
- Create: `C:/Users/USER/Documents/routex/mintlify-docs/webhooks.mdx`
- Create: `C:/Users/USER/Documents/routex/mintlify-docs/gateway-behavior.mdx`
- Modify: `C:/Users/USER/Documents/routex/.gitignore`
- Test: Mintlify validation/build command

**Step 1: Write the failing test**

Add a docs validation step that fails when the Mintlify app files are missing.

**Step 2: Run test to verify it fails**

Run: `npx mintlify dev --help`
Expected: the project has no Mintlify app structure yet, so docs validation is not ready.

**Step 3: Write minimal implementation**

- Add a tracked `mintlify-docs/` app with navigation and page metadata.
- Create curated public pages for introduction, auth, collections, verification, payouts, webhooks, and gateway behavior.
- Set the tone and examples for test mode only.

**Step 4: Run test to verify it passes**

Run: `npx mintlify-openapi-check@latest mintlify-docs/docs.json`
Expected: PASS or clean structural validation for the new docs app.

**Step 5: Commit**

```bash
git add .gitignore mintlify-docs
git commit -m "feat: add mintlify public docs app"
```

### Task 10: Curate Public API And Webhook Content

**Files:**
- Modify: `C:/Users/USER/Documents/routex/mintlify-docs/collections.mdx`
- Modify: `C:/Users/USER/Documents/routex/mintlify-docs/verification.mdx`
- Modify: `C:/Users/USER/Documents/routex/mintlify-docs/payouts.mdx`
- Modify: `C:/Users/USER/Documents/routex/mintlify-docs/webhooks.mdx`
- Modify: `C:/Users/USER/Documents/routex/mintlify-docs/gateway-behavior.mdx`
- Modify: `C:/Users/USER/Documents/routex/frontend/lib/openapi.ts`
- Modify: `C:/Users/USER/Documents/routex/services/openapiService.py`
- Test: `C:/Users/USER/Documents/routex/tests/test_openapi_public.py`

**Step 1: Write the failing test**

Add assertions that the public API contract and curated docs expose only the approved MVP endpoints and the `X-AGGREGATOR-SIGNATURE` webhook header.

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_openapi_public.py -q`
Expected: FAIL if any old endpoints, legacy wording, or wrong signature headers remain in the public contract.

**Step 3: Write minimal implementation**

- Limit public docs and spec wiring to:
  - `POST /api/v1/initiate`
  - `GET /api/v1/transactions/verify`
  - `POST /api/v1/payout`
- Explain `gateway_code`, automatic routing, amount units, `notification_url`, and webhook payload shape.
- Add clear webhook examples using `X-AGGREGATOR-SIGNATURE` only.

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_openapi_public.py -q`
Expected: PASS

**Step 5: Commit**

```bash
git add mintlify-docs frontend/lib/openapi.ts services/openapiService.py tests/test_openapi_public.py
git commit -m "feat: curate mintlify mvp api docs"
```

### Task 11: Route `/docs` To Mintlify

**Files:**
- Modify: `C:/Users/USER/Documents/routex/frontend/app/docs/page.tsx`
- Modify: `C:/Users/USER/Documents/routex/frontend/next.config.ts`
- Modify: `C:/Users/USER/Documents/routex/frontend/Dockerfile`
- Modify: `C:/Users/USER/Documents/routex/docker-compose.yml`
- Test: `C:/Users/USER/Documents/routex/frontend/tests/docs.spec.ts`

**Step 1: Write the failing test**

Add assertions that `/docs` now lands in the Mintlify experience instead of the legacy Next.js docs shell.

**Step 2: Run test to verify it fails**

Run: `npx playwright test tests/docs.spec.ts`
Expected: FAIL

**Step 3: Write minimal implementation**

- Replace the old `/docs` page with the Mintlify handoff/proxy integration.
- Update local container wiring so the app and docs can coexist at `/docs`.
- Keep docs traffic on the main frontend domain while serving Mintlify underneath.

**Step 4: Run test to verify it passes**

Run: `npx playwright test tests/docs.spec.ts`
Expected: PASS

**Step 5: Commit**

```bash
git add frontend/app/docs/page.tsx frontend/next.config.ts frontend/Dockerfile docker-compose.yml frontend/tests/docs.spec.ts
git commit -m "feat: serve mintlify docs at /docs"
```

### Task 12: Full Verification And Submission Polish

**Files:**
- Modify: `C:/Users/USER/Documents/routex/README.md`
- Test: `C:/Users/USER/Documents/routex/frontend/tests/navigation.spec.ts`
- Test: `C:/Users/USER/Documents/routex/frontend/tests/auth.spec.ts`
- Test: `C:/Users/USER/Documents/routex/frontend/tests/dashboard.spec.ts`
- Test: `C:/Users/USER/Documents/routex/frontend/tests/admin.spec.ts`
- Test: `C:/Users/USER/Documents/routex/frontend/tests/docs.spec.ts`
- Test: `C:/Users/USER/Documents/routex/tests/test_routing_api.py`
- Test: `C:/Users/USER/Documents/routex/tests/test_openapi_public.py`
- Test: `C:/Users/USER/Documents/routex/tests/test_router_dashboard_api.py`
- Test: `C:/Users/USER/Documents/routex/tests/test_webhook_delivery.py`

**Step 1: Run focused backend verification**

Run:

```bash
pytest tests/test_routing_api.py tests/test_openapi_public.py tests/test_router_dashboard_api.py tests/test_webhook_delivery.py -q
```

Expected: PASS

**Step 2: Run frontend verification**

Run:

```bash
cd frontend
npm run build
npx playwright test
```

Expected: PASS

**Step 3: Verify the final routes with browser automation**

Use Playwright to open and verify:
- `/`
- `/login`
- `/signup`
- `/dashboard`
- `/admin`
- `/docs`
- `/sandbox`

Expected:
- every surface uses the new design system
- `/docs` is Mintlify-backed
- `/sandbox` redirects into docs
- signed-in users keep auth state across route changes

**Step 4: Commit**

```bash
git add README.md
git commit -m "docs: finalize routex redesign rollout"
```
