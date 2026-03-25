# Task Tracker

## Goal

Create a repo-ready PRD for the Multi-Payment Router MVP, grounded in the existing backend codebase, and include a recommendation for the landing page, API documentation, and interactive API testing experience.

## Plan

- [x] Review the existing backend structure, APIs, models, and integrations.
- [x] Clarify MVP scope, user types, currencies, routing intelligence, payouts scope, and dashboard needs.
- [x] Research current developer portal options for API docs and browser-based API testing.
- [x] Draft and save the PRD in the repository.
- [x] Verify the written deliverables and capture the result here.

## Review

- Verified that `tasks/todo.md` and `docs/multi-payment-router-prd.md` were created successfully.
- Reviewed the PRD content to confirm it includes the routing architecture, API design, data model guidance, failure handling, security, metrics, and the landing page/docs/playground recommendation.

---

## Goal

Create:

- a landing page UI spec for `RouteX` based on the provided neo-brutalist reference design
- a detailed implementation plan for the router backend, demo dashboard, landing page, docs, and API testing flow

## Plan

- [x] Review the existing repo structure and prior PRD context.
- [x] Map the provided visual reference to a RouteX-specific landing page structure.
- [x] Choose the best technical method for embedded API docs and testing within the branded site.
- [x] Draft a landing page UI spec document.
- [x] Draft a detailed implementation plan document with exact proposed file paths.
- [x] Verify the new documents and capture the result here.

## Review

- Verified that both planning documents were written successfully under `docs/plans/`.
- Reviewed the landing page UI spec to confirm it maps the provided neo-brutalist reference to RouteX-specific messaging, sections, and component behavior.
- Reviewed the implementation plan to confirm it covers backend routing, dashboard APIs, frontend landing page work, embedded sandbox testing, full docs routing, verification, and commit checkpoints.

---

## Goal

Implement the RouteX MVP in tracked hackathon-sized feature commits, starting with the frontend landing experience and then moving into the routing backend and dashboard.

## Assumptions

- The repo root is now the product root after flattening `x-aggregator`.
- Feature work continues on a dedicated `codex/` branch after the baseline `first commit`.
- Generated frontend artifacts stay out of git; only source, tests, and lockfiles are committed.

## Plan

- [x] Clean the current frontend shell changes into a single source-only commit.
- [x] Add the RouteX visual system and shared landing page layout components.
- [x] Build the full landing page sections based on the approved neo-brutalist design spec.
- [x] Add the embedded sandbox playground and docs shell.
- [x] Add backend routing persistence, gateway adapters, and the core routing service.
- [x] Refactor collections, payouts, and verification APIs to use the routing core.
- [x] Normalize webhook handling and reconciliation markers for routed transactions.
- [x] Add router analytics/admin APIs for the demo dashboard backend.
- [x] Build the frontend demo dashboard and wire it to the router analytics endpoints.
- [x] Expose a public-safe OpenAPI source for docs and playground.
- [x] Wire the frontend docs and sandbox playground to the public API contract.
- [x] Finalize implementation docs and verification guidance.

## Review

- Verified `frontend/tests/landing-shell.spec.ts` passes against the built Next.js app via Playwright.
- Verified `frontend` production build completes successfully with `npm run build`.
- Verified `frontend/tests/design-system.spec.ts` passes against the built Next.js app via Playwright.
- Verified `frontend/tests/landing-sections.spec.ts` passes against the built Next.js app via Playwright.
- Verified the full frontend suite passes with `npx playwright test` after serializing workers for stable built-app E2E startup.
- Verified `tests/test_routing_models.py` passes with async SQLite plus test-only env overrides for `DB_URL`, `REDIS_URL`, `AGG_SECRET`, and `AUTH_SECRET`.
- Verified `tests/test_routing_models.py` and `tests/test_routing_service.py` pass together with the same test-only backend env overrides.
- Verified the routing service now returns ranked gateways, score breakdowns, rejection reasons, and adapter lookup coverage with `4` passing backend tests.
- Verified routed collection, payout, and verification API coverage with `tests/test_routing_api.py`.
- Verified the routing and legacy v1 backend suites pass together with `14` passing tests after updating the async client fixture for modern `httpx`.
- Verified webhook normalization, idempotence, and reconciliation markers with `tests/test_webhook_normalization.py`.
- Verified the router-relevant backend suites pass sequentially with `16` passing tests plus `2` existing webhook wallet integration tests.
- Verified router analytics/admin coverage with `tests/test_router_dashboard_api.py`.
- Verified the router backend bundle passes sequentially with `19` backend tests plus `2` webhook wallet integration tests.
- Verified the dashboard frontend with `frontend/tests/dashboard.spec.ts`.
- Verified the full frontend build plus Playwright suite pass with `5` green specs after adding the dashboard page.
- Verified the sanitized public OpenAPI export with `tests/test_openapi_public.py`.
- Verified the docs and playground contract slice with `frontend/tests/docs.spec.ts` and `frontend/tests/playground.spec.ts`.
- Verified the refreshed frontend production build with `npm run build`.
- Verified the full frontend Playwright suite with `7` green specs after wiring the docs page and verify playground tab to the public API contract.
- Verified the final implementation guidance by reviewing `README.md`, `.env.example`, and the updated PRD sections for the shipped custom frontend, public OpenAPI, and server-side sandbox proxy approach.

---

## Goal

Add a demo-friendly gateway control panel to the RouteX dashboard so admins can enable or pause gateways and adjust priority weights from the frontend without exposing backend admin tokens.

## Plan

- [x] Review the current dashboard frontend and router admin endpoint.
- [x] Define the control-panel approach: client-side dashboard state plus a safe frontend proxy with demo fallback.
- [x] Add a failing dashboard E2E test for the control panel.
- [x] Implement the dashboard control panel and frontend proxy.
- [x] Verify the dashboard flow and record the result here.

## Review

- Verified the red-green loop for the dashboard controls with `frontend/tests/dashboard.spec.ts`.
- Verified the refreshed frontend production build with `npm run build`.
- Verified the full frontend Playwright suite with `8` green specs after adding the gateway control panel.

---

## Goal

Add background gateway health refresh so routing and dashboard analytics use automatically updated health snapshots instead of static or manually seeded data.

## Plan

- [x] Review the current snapshot model, analytics readers, adapter health hooks, and Celery setup.
- [x] Choose the implementation approach: periodic Celery refresh backed primarily by recent routing-attempt data.
- [x] Add failing backend tests for snapshot refresh behavior and circuit-state computation.
- [x] Implement gateway health refresh logic and Celery periodic task wiring.
- [x] Verify router compatibility and record the result here.

## Review

- Verified the red-green loop for gateway health refresh with `tests/test_gateway_health_refresh.py`.
- Verified router compatibility with `tests/test_gateway_health_refresh.py tests/test_routing_service.py tests/test_router_dashboard_api.py -v`.

---

## Goal

Make gateway health refresh visible in the dashboard with a manual refresh action, freshness timestamps, and lightweight live polling.

## Plan

- [x] Review the refreshed backend health pipeline and current dashboard data flow.
- [x] Choose the implementation approach: backend admin refresh endpoint plus frontend proxy routes and live-mode polling.
- [x] Add failing backend and frontend tests for dashboard health refresh visibility.
- [x] Implement the backend refresh endpoint, dashboard proxies, and UI state.
- [x] Verify backend/frontend behavior and record the result here.

## Review

- Verified the red-green loop for the backend refresh endpoint with `tests/test_router_dashboard_api.py`.
- Verified the red-green loop for the dashboard refresh UI with `frontend/tests/dashboard.spec.ts`.
- Verified focused backend compatibility with `tests/test_router_dashboard_api.py tests/test_gateway_health_refresh.py -v`.
- Verified the refreshed frontend production build with `npm run build`.
- Verified the full frontend Playwright suite with `9` green specs after adding dashboard health visibility and refresh controls.

---

## Goal

Add real Interswitch Quickteller Business support for routed collections and authoritative server-side verification while preserving the existing RouteX `checkout_url` API contract.

## Plan

- [x] Review the current adapter/router flow and the official Interswitch hosted checkout and requery docs.
- [x] Choose the implementation approach: RouteX-hosted bridge checkout page plus server-side transaction requery.
- [x] Add failing backend tests for Interswitch initialize, hosted checkout bridge rendering, routed initialize, and verify behavior.
- [x] Implement the Interswitch service, checkout bridge route, adapter wiring, and configuration.
- [x] Integrate Interswitch requery into the verify endpoint and make `isw` eligible for collection routing.
- [x] Verify the focused backend suites and record the result here.

## Review

- Verified the red-green loop for Interswitch hosted checkout with `tests/test_interswitch_service.py` plus the routed initialize test.
- Verified authoritative Interswitch verify-by-requery with `tests/test_routing_api.py::TestRoutingApi::test_verify_requeries_interswitch_transactions -v`.
- Verified the focused backend slice with `pytest tests/test_interswitch_service.py tests/test_routing_api.py tests/test_routing_service.py -v`.

---

## Goal

Add signed Interswitch transaction webhook support so RouteX can update Interswitch collection transactions asynchronously and complete the gateway’s live collection lifecycle.

## Plan

- [x] Review the official Interswitch webhook rules and the current RouteX webhook/normalization flow.
- [x] Choose the implementation approach: `TRANSACTION.*` webhook support only, with terminal handling on `TRANSACTION.COMPLETED`.
- [x] Add failing tests for Interswitch webhook normalization and signed webhook endpoints.
- [x] Implement Interswitch webhook normalization for pending, success, and failed transaction events.
- [x] Implement test/live Interswitch webhook endpoints with signature verification and merchant notification dispatch.
- [x] Verify the focused backend suites and record the result here.

## Review

- Verified the red-green loop for Interswitch webhook normalization with `tests/test_webhook_normalization.py -v`.
- Verified the signed endpoint behavior with `tests/test_interswitch_webhooks.py -v`.
- Verified the focused end-to-end slice with `pytest tests/test_webhook_normalization.py tests/test_interswitch_webhooks.py tests/test_interswitch_service.py tests/test_routing_api.py -v`.

---

## Goal

Add a RouteX-owned Interswitch return flow so customers land on a verified RouteX status page before optionally continuing to the merchant callback URL.

## Plan

- [x] Review the current Interswitch bridge and redirect handling.
- [x] Choose the implementation approach: RouteX backend return endpoint plus frontend payment status page.
- [x] Add failing backend and frontend tests for the Interswitch return flow.
- [x] Implement the backend return endpoint and normalized frontend redirect behavior.
- [x] Build the RouteX payment status page with success, pending, and failed states.
- [x] Verify the focused backend and frontend suites and record the result here.

## Review

- Verified the red-green loop for the backend return flow with `pytest tests/test_interswitch_service.py tests/test_interswitch_return_flow.py -v`.
- Verified the focused backend bundle with `pytest tests/test_interswitch_service.py tests/test_interswitch_return_flow.py tests/test_routing_api.py -v`.
- Verified the new frontend payment-status page with `npx playwright test tests/payment-status.spec.ts`.
- Verified the refreshed frontend production build with `npm run build`.
- Verified the full frontend Playwright suite with `12` green specs after adding the RouteX payment-status page and Interswitch return flow UX.

---

## Goal

Add admin-only dashboard transaction observability so RouteX operators can open a routed transaction and inspect the routing decision, attempt timeline, failover outcome, and webhook or reconciliation hints.

## Plan

- [x] Add failing backend and frontend tests for the transaction detail route.
- [x] Implement the backend router analytics detail endpoint and schemas.
- [x] Add frontend transaction detail data plumbing and the safe proxy route.
- [x] Build the dedicated `/dashboard/transactions/[reference]` observability page.
- [x] Verify the focused backend and frontend suites and record the result here.

## Review

- Backend verification passed: `pytest tests/test_router_dashboard_api.py tests/test_routing_api.py -v` -> `14 passed`.
- Frontend build passed: `npm run build`.
- Focused dashboard verification passed: `npx playwright test tests/dashboard.spec.ts` -> `5 passed`.
- Full frontend verification passed: `npx playwright test` -> `14 passed`.
- Outcome: the dashboard now supports admin-only transaction drill-down with routing reasons, score visualization, attempt history, failover summary, webhook trace, and branded fallback states.

---

## Goal

Add global admin-only routing rules so RouteX operators can shape gateway eligibility and forced ordering from the dashboard before the router applies its normal scoring.

## Plan

- [x] Add failing backend and frontend tests for routing rules.
- [x] Add the routing rule model and migration.
- [x] Add backend rule schemas and admin CRUD endpoints.
- [x] Add rule evaluation and router enforcement.
- [x] Add dashboard rule data plumbing and safe proxy routes.
- [x] Build the dashboard routing rules panel.
- [x] Verify the focused backend and frontend suites and record the result here.

## Review

- Backend verification passed: `pytest tests/test_router_dashboard_api.py tests/test_routing_service.py tests/test_routing_api.py -v` -> `23 passed`.
- Frontend build passed: `npm run build`.
- Focused dashboard verification passed: `npx playwright test tests/dashboard.spec.ts` -> `8 passed`.
- Full frontend verification passed: `npx playwright test` -> `17 passed`.
- Outcome: the dashboard now supports admin-managed global routing rules with demo-safe fallback, live admin proxy routes, seeded rule data, and rule toggles that shape gateway policy before score-based routing.

---

## Goal

Harden RouteX into a fully live, deployable product by removing demo-only frontend behavior, wiring the frontend to the existing backend, splitting user and admin apps, tightening configuration, and documenting Dokploy deployment plus gateway webhook setup.

## Plan

- [x] Harden backend auth delivery, switch auth mail to Resend, and add identity endpoints.
- [x] Add frontend user auth session routes, pages, and route guards.
- [x] Split the admin control room into `/admin` with real admin login.
- [x] Rebuild `/dashboard` as the live user dashboard backed by existing APIs.
- [x] Remove dummy data and env-token shortcuts from frontend product surfaces.
- [x] Upgrade `/docs` into standard reference docs with payloads and examples.
- [x] Clean tracked junk, tighten `.env.example`, and add Dokploy-ready Dockerfiles and deployment docs.
- [x] Run full backend and frontend verification and record the result here.

## Review

- Backend auth hardening passed with `pytest tests/test_auth_flow.py tests/test_admin_endpoints.py::TestAdminAuthentication tests/test_v1_api.py -v` -> `16 passed`.
- Frontend auth shell passed with `npm run build` and `npx playwright test tests/auth.spec.ts` -> `6 passed`.
- Admin split passed with `npm run build` and `npx playwright test tests/admin.spec.ts tests/dashboard.spec.ts` -> `5 passed`.
- Live user dashboard wiring passed with `npm run build` and `npx playwright test tests/dashboard.spec.ts` -> `2 passed`.
- Frontend live-surface cleanup passed with `npm run build` and `npx playwright test tests/admin.spec.ts tests/dashboard.spec.ts` -> `5 passed`.
- Outcome: the admin control room now runs only through authenticated `/api/admin/*` proxies, legacy `/api/dashboard/*` routes are removed, demo data is no longer used for product surfaces, and the user/admin apps are cleanly separated.
- Docs hardening passed with:
  - `npm run build`
  - `npx playwright test tests/docs.spec.ts tests/playground.spec.ts tests/navigation.spec.ts` -> `6 passed`
- Deployment and config cleanup passed with:
  - `docker compose config` (valid)
  - new per-container Dockerfiles for API, worker, beat, and frontend
  - `.env.example` reduced to required MVP variables (core, Resend, gateways, frontend bridge)
- Full-stack closeout verification passed with:
  - `pytest tests/test_auth_flow.py tests/test_routing_api.py tests/test_router_dashboard_api.py tests/test_interswitch_service.py tests/test_interswitch_webhooks.py -v` -> `27 passed`
  - `npx playwright test` -> `23 passed`
- Outcome: TODO is complete. Frontend uses live backend integrations only (no mock playground fallback), docs are payload-first and OpenAPI-driven, links/buttons route correctly, and the repo is deployment-ready for Dokploy.
