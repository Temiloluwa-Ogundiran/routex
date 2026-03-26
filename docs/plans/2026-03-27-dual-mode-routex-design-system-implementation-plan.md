# RouteX Dual-Mode Design System Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Rebuild RouteX into a synchronized two-mode product system where public, auth, pay, docs branding, and email use acid neo-brutalism while merchant/admin operational surfaces use a monochrome JetBrains Mono blueprint system.

**Architecture:** Keep the current Next.js routing, backend proxy model, auth model, and Mintlify hosting flow intact, but replace the visual system and page composition across all frontend surfaces. Public and signed-in experiences will share tokens, logo rules, spacing rhythm, and interaction logic while diverging at the surface layer through two explicit themes.

**Tech Stack:** Next.js App Router, React, CSS modules/global CSS, `next/font/google`, FastAPI backend, Resend email delivery, Mintlify hosted docs, Playwright, pytest.

---

### Task 1: Establish Shared Tokens And Font Infrastructure

**Files:**
- Modify: `C:/Users/USER/Documents/routex/frontend/app/layout.tsx`
- Modify: `C:/Users/USER/Documents/routex/frontend/app/globals.css`
- Test: `C:/Users/USER/Documents/routex/frontend/tests/design-system.spec.ts`

**Step 1: Write the failing test**

Add a Playwright test that asserts:
- public surfaces no longer use the current mixed liquid tokens
- the root font stack exposes `Dela Gothic One`, `Space Grotesk`, and `JetBrains Mono`
- the app shell is not still rendering the previous yellow/void hybrid CSS treatment

**Step 2: Run test to verify it fails**

Run: `cd frontend; npx playwright test tests/design-system.spec.ts`
Expected: FAIL because the old system is still in place.

**Step 3: Write minimal implementation**

- Replace the current root font loading with:
  - `Dela Gothic One`
  - `Space Grotesk`
  - `JetBrains Mono`
- Replace the current mixed token block in `globals.css` with:
  - shared core RouteX tokens
  - public theme tokens
  - ops theme tokens
- Add route-level utility classes for:
  - acid brutalist surfaces
  - blueprint ops surfaces

**Step 4: Run test to verify it passes**

Run: `cd frontend; npx playwright test tests/design-system.spec.ts`
Expected: PASS

**Step 5: Commit**

```bash
git add frontend/app/layout.tsx frontend/app/globals.css frontend/tests/design-system.spec.ts
git commit -m "feat: add dual-mode routex design foundation"
```

### Task 2: Rebuild Public Header, Footer, And Shared Brand Primitives

**Files:**
- Modify: `C:/Users/USER/Documents/routex/frontend/components/layout/site-header.tsx`
- Modify: `C:/Users/USER/Documents/routex/frontend/components/layout/site-header-client.tsx`
- Modify: `C:/Users/USER/Documents/routex/frontend/components/layout/site-footer.tsx`
- Modify: `C:/Users/USER/Documents/routex/frontend/components/ui/push-button.tsx`
- Create: `C:/Users/USER/Documents/routex/frontend/components/ui/brutalist-badge.tsx`
- Test: `C:/Users/USER/Documents/routex/frontend/tests/navigation.spec.ts`

**Step 1: Write the failing test**

Add assertions that:
- the public header is a brutalist sticky bar
- guest CTAs are correct
- signed-in users do not see guest-only login/signup actions
- footer links are pruned to useful working destinations

**Step 2: Run test to verify it fails**

Run: `cd frontend; npx playwright test tests/navigation.spec.ts`
Expected: FAIL

**Step 3: Write minimal implementation**

- Rebuild the public shell using:
  - brutalist top bar
  - hard-shadow buttons
  - clearer RouteX mark/wordmark treatment
- Remove redundant footer links
- Keep signed-in action routing correct

**Step 4: Run test to verify it passes**

Run: `cd frontend; npx playwright test tests/navigation.spec.ts`
Expected: PASS

**Step 5: Commit**

```bash
git add frontend/components/layout/site-header.tsx frontend/components/layout/site-header-client.tsx frontend/components/layout/site-footer.tsx frontend/components/ui/push-button.tsx frontend/components/ui/brutalist-badge.tsx frontend/tests/navigation.spec.ts
git commit -m "feat: rebuild public routex shell"
```

### Task 3: Rebuild The Landing Page In Acid Neo-Brutalist Mode

**Files:**
- Modify: `C:/Users/USER/Documents/routex/frontend/app/page.tsx`
- Modify: `C:/Users/USER/Documents/routex/frontend/components/sections/hero-section.tsx`
- Modify: `C:/Users/USER/Documents/routex/frontend/components/sections/feature-grid.tsx`
- Modify: `C:/Users/USER/Documents/routex/frontend/components/sections/final-cta.tsx`
- Modify: `C:/Users/USER/Documents/routex/frontend/components/ui/browser-mockup.tsx`
- Create: `C:/Users/USER/Documents/routex/frontend/components/sections/highlight-marquee.tsx`
- Create: `C:/Users/USER/Documents/routex/frontend/components/sections/choose-your-stack.tsx`
- Create: `C:/Users/USER/Documents/routex/frontend/components/sections/value-pillars.tsx`
- Test: `C:/Users/USER/Documents/routex/frontend/tests/landing-shell.spec.ts`
- Test: `C:/Users/USER/Documents/routex/frontend/tests/landing-sections.spec.ts`

**Step 1: Write the failing test**

Add assertions that the landing page now includes:
- brutalist hero typography
- marquee highlight rail
- editorial bento grid
- dark value section
- no fake operational banner content like gateway score or pseudo-dashboard stats

**Step 2: Run test to verify it fails**

Run: `cd frontend; npx playwright test tests/landing-shell.spec.ts tests/landing-sections.spec.ts`
Expected: FAIL

**Step 3: Write minimal implementation**

- Replace the current homepage composition with the acid brutalist editorial flow
- Remove the old “fluid fintech” hero assets and fake operational metrics
- Add glitch-capable display text and tactile CTA buttons
- Keep the copy concise and product-forward

**Step 4: Run test to verify it passes**

Run: `cd frontend; npx playwright test tests/landing-shell.spec.ts tests/landing-sections.spec.ts`
Expected: PASS

**Step 5: Commit**

```bash
git add frontend/app/page.tsx frontend/components/sections/hero-section.tsx frontend/components/sections/feature-grid.tsx frontend/components/sections/final-cta.tsx frontend/components/ui/browser-mockup.tsx frontend/components/sections/highlight-marquee.tsx frontend/components/sections/choose-your-stack.tsx frontend/components/sections/value-pillars.tsx frontend/tests/landing-shell.spec.ts frontend/tests/landing-sections.spec.ts
git commit -m "feat: redesign landing in acid brutalist mode"
```

### Task 4: Redesign Auth And OTP Pages

**Files:**
- Modify: `C:/Users/USER/Documents/routex/frontend/app/login/page.tsx`
- Modify: `C:/Users/USER/Documents/routex/frontend/app/signup/page.tsx`
- Modify: `C:/Users/USER/Documents/routex/frontend/app/verify-otp/page.tsx`
- Modify: `C:/Users/USER/Documents/routex/frontend/app/forgot-password/page.tsx`
- Modify: `C:/Users/USER/Documents/routex/frontend/app/reset-password/page.tsx`
- Modify: `C:/Users/USER/Documents/routex/frontend/components/auth/auth-form-shell.tsx`
- Modify: `C:/Users/USER/Documents/routex/frontend/components/auth/otp-form-shell.tsx`
- Test: `C:/Users/USER/Documents/routex/frontend/tests/auth.spec.ts`

**Step 1: Write the failing test**

Add assertions that:
- auth screens use the public acid brutalist system
- the top badge and headings are formatted correctly
- no internal session/jwt/auth implementation copy appears
- OTP screen remains usable and clear

**Step 2: Run test to verify it fails**

Run: `cd frontend; npx playwright test tests/auth.spec.ts`
Expected: FAIL

**Step 3: Write minimal implementation**

- Rebuild the auth shell around:
  - editorial intro panel
  - tactile brutalist form card
- Remove all internal auth wording
- Keep current auth behavior intact while improving layout and copy

**Step 4: Run test to verify it passes**

Run: `cd frontend; npx playwright test tests/auth.spec.ts`
Expected: PASS

**Step 5: Commit**

```bash
git add frontend/app/login/page.tsx frontend/app/signup/page.tsx frontend/app/verify-otp/page.tsx frontend/app/forgot-password/page.tsx frontend/app/reset-password/page.tsx frontend/components/auth/auth-form-shell.tsx frontend/components/auth/otp-form-shell.tsx frontend/tests/auth.spec.ts
git commit -m "feat: redesign auth experience"
```

### Task 5: Rebuild Payment Status In Public Mode

**Files:**
- Modify: `C:/Users/USER/Documents/routex/frontend/app/pay/status/page.tsx`
- Modify: `C:/Users/USER/Documents/routex/frontend/components/pay/payment-status-shell.tsx`
- Test: `C:/Users/USER/Documents/routex/frontend/tests/payment-status.spec.ts`

**Step 1: Write the failing test**

Add assertions that success, pending, and failed states render using the acid public system rather than a generic utility card layout.

**Step 2: Run test to verify it fails**

Run: `cd frontend; npx playwright test tests/payment-status.spec.ts`
Expected: FAIL

**Step 3: Write minimal implementation**

- Rebuild the payment status shell as a public brand surface
- Keep the current state logic
- Improve hierarchy, CTA placement, and status emphasis

**Step 4: Run test to verify it passes**

Run: `cd frontend; npx playwright test tests/payment-status.spec.ts`
Expected: PASS

**Step 5: Commit**

```bash
git add frontend/app/pay/status/page.tsx frontend/components/pay/payment-status-shell.tsx frontend/tests/payment-status.spec.ts
git commit -m "feat: redesign payment status surface"
```

### Task 6: Rebuild Merchant Dashboard In Blueprint Ops Mode

**Files:**
- Modify: `C:/Users/USER/Documents/routex/frontend/app/dashboard/page.tsx`
- Modify: `C:/Users/USER/Documents/routex/frontend/components/app/merchant-dashboard-shell.tsx`
- Create: `C:/Users/USER/Documents/routex/frontend/components/app/merchant-sidebar.tsx`
- Create: `C:/Users/USER/Documents/routex/frontend/components/app/merchant-topbar.tsx`
- Create: `C:/Users/USER/Documents/routex/frontend/components/ui/geometric-panel.tsx`
- Test: `C:/Users/USER/Documents/routex/frontend/tests/dashboard.spec.ts`

**Step 1: Write the failing test**

Add assertions that the merchant dashboard now has:
- fixed ops sidebar
- sticky ops topbar
- JetBrains Mono text treatment
- clean white cards on gray background
- no sandbox action inside the dashboard

**Step 2: Run test to verify it fails**

Run: `cd frontend; npx playwright test tests/dashboard.spec.ts`
Expected: FAIL

**Step 3: Write minimal implementation**

- Replace the merchant dashboard shell with the blueprint operations layout
- Keep current live data wiring
- Reorganize key panels, metrics, and transactions for stronger hierarchy
- Preserve sign-out and docs access

**Step 4: Run test to verify it passes**

Run: `cd frontend; npx playwright test tests/dashboard.spec.ts`
Expected: PASS

**Step 5: Commit**

```bash
git add frontend/app/dashboard/page.tsx frontend/components/app/merchant-dashboard-shell.tsx frontend/components/app/merchant-sidebar.tsx frontend/components/app/merchant-topbar.tsx frontend/components/ui/geometric-panel.tsx frontend/tests/dashboard.spec.ts
git commit -m "feat: redesign merchant dashboard in blueprint mode"
```

### Task 7: Rebuild Admin Dashboard In Blueprint Ops Mode

**Files:**
- Modify: `C:/Users/USER/Documents/routex/frontend/app/admin/page.tsx`
- Modify: `C:/Users/USER/Documents/routex/frontend/app/admin/login/page.tsx`
- Modify: `C:/Users/USER/Documents/routex/frontend/components/dashboard/dashboard-console.tsx`
- Modify: `C:/Users/USER/Documents/routex/frontend/components/dashboard/transaction-detail-shell.tsx`
- Modify: `C:/Users/USER/Documents/routex/frontend/components/dashboard/routing-rules-panel.tsx`
- Modify: `C:/Users/USER/Documents/routex/frontend/components/dashboard/gateway-control-panel.tsx`
- Modify: `C:/Users/USER/Documents/routex/frontend/components/dashboard/gateway-health-grid.tsx`
- Modify: `C:/Users/USER/Documents/routex/frontend/components/dashboard/failover-feed.tsx`
- Modify: `C:/Users/USER/Documents/routex/frontend/components/dashboard/recent-transactions.tsx`
- Test: `C:/Users/USER/Documents/routex/frontend/tests/admin.spec.ts`

**Step 1: Write the failing test**

Add assertions that the admin login and control room now render in the blueprint ops system and that router controls remain accessible.

**Step 2: Run test to verify it fails**

Run: `cd frontend; npx playwright test tests/admin.spec.ts`
Expected: FAIL

**Step 3: Write minimal implementation**

- Rebuild admin login copy and layout
- Move admin operational views into the same blueprint shell as merchant, but denser
- Add geometric illustration panels where they help hierarchy

**Step 4: Run test to verify it passes**

Run: `cd frontend; npx playwright test tests/admin.spec.ts`
Expected: PASS

**Step 5: Commit**

```bash
git add frontend/app/admin/page.tsx frontend/app/admin/login/page.tsx frontend/components/dashboard/dashboard-console.tsx frontend/components/dashboard/transaction-detail-shell.tsx frontend/components/dashboard/routing-rules-panel.tsx frontend/components/dashboard/gateway-control-panel.tsx frontend/components/dashboard/gateway-health-grid.tsx frontend/components/dashboard/failover-feed.tsx frontend/components/dashboard/recent-transactions.tsx frontend/tests/admin.spec.ts
git commit -m "feat: redesign admin ops experience"
```

### Task 8: Redesign Email Templates

**Files:**
- Modify: `C:/Users/USER/Documents/routex/templates/otp.html`
- Modify: `C:/Users/USER/Documents/routex/services/emailService.py`
- Test: `C:/Users/USER/Documents/routex/tests/test_email_service.py`

**Step 1: Write the failing test**

Add or update an email render test that checks:
- RouteX branding is current
- no internal implementation text appears
- OTP hierarchy is clear

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_email_service.py -q`
Expected: FAIL or missing assertions for the new visual structure.

**Step 3: Write minimal implementation**

- Rebuild the OTP email in an inbox-safe acid neo-brutalist style
- Keep table-safe markup and simple CSS
- Update subject/copy alignment if needed

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_email_service.py -q`
Expected: PASS

**Step 5: Commit**

```bash
git add templates/otp.html services/emailService.py tests/test_email_service.py
git commit -m "feat: redesign routex email template"
```

### Task 9: Align Mintlify Content And Hosted Theme Inputs

**Files:**
- Modify: `C:/Users/USER/Documents/routex/mintlify-docs/docs.json`
- Modify: `C:/Users/USER/Documents/routex/mintlify-docs/index.mdx`
- Modify: `C:/Users/USER/Documents/routex/mintlify-docs/authentication.mdx`
- Modify: `C:/Users/USER/Documents/routex/mintlify-docs/collections.mdx`
- Modify: `C:/Users/USER/Documents/routex/mintlify-docs/verification.mdx`
- Modify: `C:/Users/USER/Documents/routex/mintlify-docs/payouts.mdx`
- Modify: `C:/Users/USER/Documents/routex/mintlify-docs/webhooks.mdx`
- Modify: `C:/Users/USER/Documents/routex/mintlify-docs/gateway-behavior.mdx`
- Test: `C:/Users/USER/Documents/routex/tests/test_mintlify_docs.py`
- Test: `C:/Users/USER/Documents/routex/tests/test_openapi_public.py`

**Step 1: Write the failing test**

Add assertions that:
- the docs keep only the approved MVP endpoints
- webhook docs mention `X-AGGREGATOR-SIGNATURE`
- wording aligns with external developer usage

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_mintlify_docs.py tests/test_openapi_public.py -q`
Expected: FAIL if docs still use outdated copy or expose extra concepts.

**Step 3: Write minimal implementation**

- Refine page copy and examples
- Keep Mintlify hosted theme settings aligned with the acid public brand where docs.json supports it
- Ensure webhook payload docs are concise and external-facing

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_mintlify_docs.py tests/test_openapi_public.py -q`
Expected: PASS

**Step 5: Commit**

```bash
git add mintlify-docs tests/test_mintlify_docs.py tests/test_openapi_public.py
git commit -m "docs: align mintlify docs with routex brand"
```

### Task 10: Full Verification

**Files:**
- Test: `C:/Users/USER/Documents/routex/frontend/tests/navigation.spec.ts`
- Test: `C:/Users/USER/Documents/routex/frontend/tests/auth.spec.ts`
- Test: `C:/Users/USER/Documents/routex/frontend/tests/dashboard.spec.ts`
- Test: `C:/Users/USER/Documents/routex/frontend/tests/admin.spec.ts`
- Test: `C:/Users/USER/Documents/routex/frontend/tests/payment-status.spec.ts`
- Test: `C:/Users/USER/Documents/routex/tests/test_openapi_public.py`
- Test: `C:/Users/USER/Documents/routex/tests/test_router_dashboard_api.py`
- Test: `C:/Users/USER/Documents/routex/tests/test_routing_api.py`
- Test: `C:/Users/USER/Documents/routex/tests/test_email_service.py`

**Step 1: Run backend verification**

Run:

```bash
pytest tests/test_openapi_public.py tests/test_router_dashboard_api.py tests/test_routing_api.py tests/test_email_service.py -q
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

**Step 3: Perform live browser verification**

Use Playwright to verify:
- `/`
- `/login`
- `/signup`
- `/dashboard`
- `/admin`
- hosted docs link behavior

Expected:
- public pages use acid brutalist mode
- signed-in pages use blueprint ops mode
- links and buttons route correctly

**Step 4: Commit**

```bash
git commit --allow-empty -m "chore: verify dual-mode redesign"
```

