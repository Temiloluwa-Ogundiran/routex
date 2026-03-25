# RouteX

RouteX is a smart multi-payment router built for merchants and payment teams that need higher payment success rates without managing separate gateway integrations. One integration gives access to collections, payouts, verification, routing intelligence, failover visibility, and an admin control room that explains every routing decision.

## The Problem

Businesses in Nigeria regularly lose revenue when a single payment gateway slows down, times out, or goes offline. Most teams respond by hard-coding one provider, manually switching during incidents, or maintaining multiple brittle integrations. That creates failed payments, operational overhead, and poor visibility when something goes wrong.

## Our Solution

RouteX introduces a unified payment layer that sits between merchants and multiple gateways. For every transaction, it evaluates the available providers, selects the healthiest eligible route, records why that decision was made, and exposes the outcome through both merchant-facing and admin-facing interfaces.

Instead of forcing teams to choose one gateway and hope it stays healthy, RouteX makes routing an active system:

- one API for collections, payouts, and verification
- explainable routing across `Paystack`, `Flutterwave`, `Korapay`, and `Interswitch`
- health-aware failover and gateway prioritization
- webhook normalization across providers
- merchant dashboard for balances, transactions, payment links, and API keys
- admin control room for health, rules, failovers, and transaction observability

## Why RouteX Stands Out

- It is not just a payment form. It is an orchestration layer with routing logic, decision audit trails, and failover controls.
- It is not just backend infrastructure. It includes a polished public landing page, live docs, API testing, merchant workflows, and an operator control room.
- It is not a static demo. The frontend is wired to the backend, auth is live, dashboards are live, docs are live, and provider integrations follow real test-mode behavior.

## What We Built For This MVP

This hackathon submission is focused on a strong, test-mode-first product that is fast to demonstrate and technically credible.

- Unified collections API
- Unified payout API
- Verification API
- OTP-based authentication with email delivery through Resend
- Public API docs and landing-page tester
- Merchant workspace at `/dashboard`
- Separate admin control room at `/admin`
- Interswitch hosted checkout bridge and return flow
- Signed webhook handling and normalized transaction updates
- Optional PostHog frontend analytics

## Demo Story

RouteX is built to demonstrate a complete payment operations story in a few minutes:

1. A merchant signs in once and gets a unified workspace.
2. A payment is initiated through one API instead of a gateway-specific integration.
3. RouteX selects the best gateway based on health and routing rules.
4. If a provider is degraded, traffic can move and failovers are visible.
5. The admin control room shows why the route was chosen and what happened afterward.
6. Webhooks, verification, and return flows keep the transaction lifecycle consistent.

## Scope

This submission is intentionally **test mode only**. The product is shaped for MVP credibility, live demo clarity, and clean extensibility into a full production orchestration platform.

## Team Contributions

Judges should use this section to verify participation.

### Temiloluwa Ogundiran

- Backend architecture and API implementation
- Routing engine, gateway adapters, webhook normalization, and persistence
- Collections and payout orchestration across supported gateways
- Interswitch integration, hosted checkout bridge, verification, and return flow
- Celery workers, health refresh jobs, and deployment/container configuration
- Backend testing, provider integration research, and webhook setup validation

### Kwaghuter Raphael

- Frontend architecture and neo-brutalist design implementation
- Landing page, docs experience, and live API tester
- Merchant auth flows, OTP UX, and dashboard experience
- Admin dashboard UX, routing observability pages, and control interfaces
- Frontend-backend proxy integration, navigation, and route wiring
- Frontend analytics integration, end-to-end testing, and submission presentation polish

## Built With

- **Backend:** FastAPI, PostgreSQL, Redis, Celery
- **Frontend:** Next.js App Router
- **Gateways:** Paystack, Flutterwave, Korapay, Interswitch
- **Email:** Resend
- **Analytics:** PostHog
- **Deployment:** Docker Compose on Dokploy
