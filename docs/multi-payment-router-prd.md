# Multi-Payment Router PRD

## Document Summary

- Product: Multi-Payment Router
- Codebase foundation: `x-aggregator`
- Market focus: Nigeria-first
- MVP currency: `NGN`
- Gateways in MVP: `Paystack`, `Flutterwave`, `Korapay`, `Interswitch Quickteller Business`
- Routing style: rules-based eligibility plus weighted scoring
- Dashboard scope: lightweight demo dashboard
- Payout scope: in MVP, but routing intelligence is deeper for collections than payouts

## Product Overview

The Multi-Payment Router is a payment orchestration layer built on top of the existing `x-aggregator` backend. It gives merchants, internal ops teams, and platform operators a single integration for collections and payouts while intelligently selecting the best payment gateway for each request.

For the MVP, the system will:

- Route `NGN` collections across `Paystack`, `Flutterwave`, `Korapay`, and `Interswitch Quickteller Business`
- Support unified payouts from the same platform
- Reuse the current `FastAPI + PostgreSQL + Redis/Celery` backend foundation
- Expose a lightweight demo dashboard for routing visibility
- Provide a polished developer-facing landing page with API documentation and interactive testing

The goal is to build something fast enough for a hackathon, but robust and thoughtful enough to feel like the foundation of a real payment infrastructure product.

## Problem Statement

Businesses that depend on a single payment gateway often lose revenue when that gateway experiences downtime, degraded performance, bank-specific issues, or poor approval rates. Teams then need to switch providers manually, maintain multiple integrations, and explain failures across fragmented systems.

The existing `x-aggregator` codebase already includes:

- Merchant and transaction APIs
- Wallet support
- Analytics endpoints
- Existing service adapters for `Paystack`, `Flutterwave`, and `Korapay`
- Webhook processing
- Dashboard-oriented backend routes

However, the current product behaves more like a multi-gateway payment backend than a true router. The missing layer is a first-class routing engine that can:

- Evaluate gateway health and recent performance
- Select the best gateway per request
- Fail over safely
- Explain routing decisions
- Surface gateway status through a demo-ready dashboard

## Assumptions

- The MVP is Nigeria-first and supports `NGN` only.
- The current backend stack remains the system of record for the MVP.
- The router is implemented inside the existing `x-aggregator` project, not as a new backend service.
- All four gateways are expected to be supported in MVP scope.
- Collections are the primary intelligent-routing surface.
- Payouts are in scope for MVP, but failover is more conservative because duplicate disbursement risk is high.
- A lightweight dashboard is enough for the MVP. It does not need to be a full enterprise control plane.
- The landing page, API docs, and API testing experience should be impressive, developer-friendly, and fast to build.

## Goals

- Provide a single API surface for merchant collections and payouts.
- Support four gateways behind one router abstraction.
- Improve collection reliability through gateway routing and failover.
- Make routing decisions explainable and visible.
- Reuse existing `x-aggregator` capabilities to accelerate delivery.
- Ship an MVP that feels polished enough for a hackathon demo.

## Non-Goals

- ML-based routing in MVP
- Multi-currency support
- Full settlement and treasury orchestration
- Refunds and chargebacks
- Dispute management
- Merchant-managed PSP credentials
- Deep reconciliation tooling beyond MVP-level operational visibility
- A fully customized merchant dashboard for all roles

## Target Users

### Merchant Developers

- Need one stable API instead of multiple PSP integrations
- Need quick onboarding, docs, and testable endpoints

### Merchant Operations and Finance Teams

- Need transaction visibility
- Need payout visibility
- Need confidence that routing improves uptime

### Platform Operators and Admins

- Need to see gateway health and routing decisions
- Need to disable or deprioritize failing gateways quickly

### Demo Stakeholders and Judges

- Need a clear story: one integration, smart routing, visible failover, clear metrics

## User Stories

- As a merchant developer, I want one collection API so I do not need to integrate each gateway separately.
- As a merchant developer, I want one payout API so I can move funds through one platform.
- As a merchant, I want the router to choose the best gateway automatically so my payment success rate improves.
- As an operator, I want to see which gateway was selected and why so routing is explainable.
- As an operator, I want to disable a failing gateway quickly so new transactions avoid it.
- As a merchant, I want unified verification and webhook callbacks so my backend stays simple.
- As a demo user, I want to watch a payment fail over to another provider so the product visibly proves its value.

## MVP Scope

### In Scope

- Unified collections API
- Unified payouts API
- Routing engine for collections
- Safe gateway selection and fallback
- Four gateway adapters
- Routing attempt tracking
- Gateway health monitoring
- Unified verification endpoint
- Unified webhook normalization
- Lightweight routing dashboard
- Landing page with docs and interactive API testing

### Out of Scope

- Refund workflows
- Chargeback/dispute operations
- Multi-currency support
- Merchant-level gateway credential management
- Advanced fraud detection
- ML routing
- Settlement automation

## High-Level Architecture

```text
Merchant / Platform Client
        |
        v
Unified Router API (FastAPI)
        |
        +--> Auth + Merchant Context
        |
        +--> Routing Engine
        |       |
        |       +--> Rules / Eligibility Filters
        |       +--> Weighted Scoring
        |       +--> Gateway Health Cache
        |
        +--> Gateway Adapter Layer
        |       |
        |       +--> Paystack Adapter
        |       +--> Flutterwave Adapter
        |       +--> Korapay Adapter
        |       +--> Interswitch Adapter
        |
        +--> Transaction + Attempt Persistence
        +--> Wallet Service
        +--> Analytics / Dashboard APIs
        +--> Webhook Ingestion / Normalization
        +--> Merchant Webhook Dispatcher
```

## System Components

### 1. Unified Router API Layer

The API layer receives merchant requests, authenticates them, validates payloads, persists the transaction shell, invokes the routing engine, and delegates the outbound request to the chosen gateway adapter.

### 2. Routing Engine

The routing engine decides which gateway should handle a given collection request. It does this in two stages:

- Stage 1: hard eligibility filtering
- Stage 2: weighted scoring among eligible gateways

### 3. Gateway Adapter Layer

Each gateway adapter provides a normalized internal interface for:

- `initialize_collection`
- `verify_transaction`
- `initiate_payout`
- `handle_webhook`
- `health_check`

The existing `Paystack`, `Flutterwave`, and `Korapay` service modules can be refactored under this adapter interface. `Interswitch Quickteller Business` should be added with the same contract.

### 4. Transaction Orchestration Layer

The router must create a canonical internal transaction record before calling any gateway and then create one or more routing attempt records during gateway selection and failover.

### 5. Webhook Processing Layer

Provider-specific webhook signatures are verified, normalized into internal events, and then used to update transactions, attempts, wallets, and outbound merchant notifications.

### 6. Dashboard and Analytics Layer

The dashboard exposes:

- Gateway health
- Recent transactions
- Routing attempt history
- Failover activity
- Top-level success and failure metrics

## Core Features and Requirements

### Unified Collections

- One endpoint for payment initiation
- Merchant sends reference, amount, currency, customer info, redirect URL, notification URL, and metadata
- Router chooses the best eligible gateway
- System returns checkout URL plus selected gateway

### Intelligent Routing

- Filter out ineligible gateways first
- Score eligible gateways using recent performance and admin preferences
- Persist the selected gateway, ranking, and reason

### Safe Failover

- If collection initialization fails before acceptance, try the next eligible gateway
- If state is ambiguous, verify first before failing over
- Payouts must use stricter failover rules to avoid duplicate transfers

### Unified Verification

- One verification endpoint for merchants
- Response abstracts away provider-specific verification logic

### Unified Webhooks

- Normalize events from all gateways
- Enforce idempotent processing
- Trigger merchant webhook callbacks using one consistent format

### Routing Observability

- Log every decision
- Save per-gateway attempt metadata
- Show routing detail in dashboard

### Demo Dashboard

- Show gateway health cards
- Show recent transactions and selected gateways
- Show failovers and fallback ordering
- Show per-transaction routing detail
- Allow quick admin toggles such as enable, disable, or weight adjustment

## Functional Requirements

- The platform must support `NGN` collections routing across four gateways.
- The platform must support unified payout initiation through the router.
- The router must reject any gateway that is disabled, unhealthy, unsupported for the requested operation, or missing required configuration.
- The router must persist every routing attempt.
- The router must preserve idempotency for merchant references.
- The webhook processor must be idempotent and signature-verified.
- The dashboard must show routing decisions with minimal delay.
- Admin users must be able to override gateway availability manually.

## Non-Functional Requirements

- Route selection should complete in under `100ms` excluding provider API time.
- Collection initiation should remain responsive under degraded gateway conditions.
- Dashboard updates should feel near-real-time for demo purposes.
- Logs must be structured enough to explain decisions during the hackathon demo.
- Security controls must prevent accidental exposure of live secrets in browser-based testing.

## API Design

### 1. Initiate Collection

- Method: `POST`
- Path: `/api/v1/initiate`
- Auth: merchant secret key

#### Sample Request

```json
{
  "reference": "ORD_20260324_1001",
  "amount": 25000,
  "currency": "NGN",
  "channel": "card",
  "customer": {
    "email": "buyer@example.com",
    "name": "Ada Obi"
  },
  "redirect_url": "https://merchant.example.com/payments/callback",
  "notification_url": "https://merchant.example.com/webhooks/payments",
  "metadata": {
    "order_id": "1001"
  },
  "routing_preferences": {
    "preferred_gateways": ["pstk", "fltw", "kora", "isw"],
    "allow_failover": true,
    "debug": true
  }
}
```

#### Sample Response

```json
{
  "status": true,
  "message": "Charge created successfully",
  "reference": "ORD_20260324_1001",
  "checkout_url": "https://checkout.provider.com/session/abc123",
  "selected_gateway": "fltw",
  "gateway_reference": "fltw_7f32a1",
  "routing": {
    "decision_id": "route_dec_001",
    "selection_reason": "highest score among healthy gateways",
    "fallback_order": ["fltw", "pstk", "kora", "isw"]
  }
}
```

### 2. Verify Transaction

- Method: `GET`
- Path: `/api/v1/transactions/verify?reference={reference}`
- Auth: merchant secret key

#### Sample Response

```json
{
  "status": true,
  "message": "verification successful",
  "data": {
    "reference": "ORD_20260324_1001",
    "status": "success",
    "type": "credit",
    "amount": 25000,
    "currency": "NGN",
    "selected_gateway": "fltw",
    "gateway_reference": "fltw_7f32a1",
    "attempts": [
      {
        "attempt_no": 1,
        "gateway": "fltw",
        "status": "success",
        "latency_ms": 1180
      }
    ]
  }
}
```

### 3. Initiate Payout

- Method: `POST`
- Path: `/api/v1/payout`
- Auth: merchant secret key

#### Sample Request

```json
{
  "reference": "PO_20260324_9001",
  "amount": 15000,
  "currency": "NGN",
  "customer": {
    "email": "vendor@example.com",
    "name": "Tunde Bello"
  },
  "destination": {
    "bank_code": "058",
    "account_number": "0123456789"
  },
  "narration": "Vendor payout",
  "metadata": {
    "invoice_id": "INV_9001"
  }
}
```

#### Sample Response

```json
{
  "status": true,
  "message": "Payout accepted",
  "reference": "PO_20260324_9001",
  "selected_gateway": "kora",
  "gateway_reference": "kora_99aa2b",
  "data": {
    "amount": 15000,
    "fee": 50
  }
}
```

### 4. Dashboard Endpoints

- `GET /analytics/router/dashboard`
- `GET /analytics/router/gateways`
- `GET /analytics/router/transactions`
- `GET /analytics/router/transactions/{id}`
- `PATCH /admin/router/gateways/{gateway_code}`
- `POST /admin/router/rules`

## Data Models

### Existing Models to Reuse

#### Merchant

- `id`
- `name`
- `email`
- `is_active`

#### Processor

- `id`
- `code`
- `charge`
- `markup`

#### Transaction

- `id`
- `type`
- `mode`
- `processor`
- `merchant_id`
- `customer_id`
- `wallet_id`
- `processor_reference`
- `reference`
- `amount`
- `charge`
- `processor_charge`
- `currency`
- `status`
- `redirect_url`
- `notification_url`
- `metadata_payload`
- `created_at`
- `updated_at`

#### Wallet

- `merchant_id`
- `currency`
- `mode`
- `balance`
- `percentage_charge`
- `flat_charge`
- `payout_percentage_charge`
- `payout_flat_charge`

### New Tables Recommended for MVP

#### RoutingAttempt

- `id`
- `transaction_id`
- `attempt_no`
- `operation`
- `gateway_code`
- `status`
- `latency_ms`
- `gateway_reference`
- `error_code`
- `error_message`
- `score_snapshot`
- `request_payload_hash`
- `created_at`

#### GatewayHealthSnapshot

- `gateway_code`
- `success_rate_5m`
- `success_rate_1h`
- `timeout_rate_5m`
- `p95_latency_ms`
- `circuit_state`
- `last_checked_at`

#### RoutingDecisionAudit

- `decision_id`
- `transaction_id`
- `eligible_gateways`
- `rejected_gateways`
- `selected_gateway`
- `selection_reason`
- `score_breakdown`
- `fallback_order`
- `created_at`

#### MerchantGatewaySetting

- `merchant_id`
- `gateway_code`
- `enabled`
- `weight_adjustment`
- `channel_allowlist`

## Routing Logic

### Stage 1: Eligibility Filters

A gateway is eligible only if all of the following are true:

- Gateway is globally enabled
- Gateway is enabled for the merchant
- Gateway supports the requested operation
- Gateway supports the requested channel
- Gateway supports `NGN`
- Gateway credentials are available for the requested environment
- Gateway is not under maintenance
- Gateway circuit breaker is not open
- Transaction amount passes configured min and max thresholds

### Stage 2: Weighted Scoring

Each eligible gateway receives a score out of `100`.

Suggested scoring weights:

- `40%` recent success rate
- `20%` longer-window stability score
- `15%` latency score
- `10%` merchant or admin preference weight
- `10%` current availability score
- `5%` cost score

#### Example Formula

```text
score =
0.40 * recent_success_rate +
0.20 * stability_score +
0.15 * latency_score +
0.10 * preference_weight +
0.10 * availability_score +
0.05 * cost_score
```

### Fallback Logic for Collections

- Pick highest score first
- Save a ranked fallback list
- If initialization fails safely before provider acceptance, try the next eligible gateway
- If timeout or ambiguous acceptance occurs, verify first before failover

### Payout Routing Logic

- Use stricter rules than collections
- Prefer one selected payout gateway and verify state before retrying
- Do not auto-failover across gateways when provider acceptance is uncertain

### Gateway Health States

- `healthy`
- `degraded`
- `down`
- `maintenance`

### Circuit Breaker Guidance

- Mark `degraded` when failures or latency spike beyond threshold
- Mark `down` when consecutive failures exceed a threshold
- Temporarily stop new traffic
- Periodically probe for recovery

## Failure Handling and Retries

### Collection Failures

- Validation failure: reject immediately
- Gateway initialization failure before acceptance: retry next eligible gateway
- Timeout with uncertain result: move to verification flow first
- Missing webhook: poll verify endpoint and mark for reconciliation

### Payout Failures

- Validation failure: reject immediately
- Insufficient balance: reject immediately
- Network failure before confirmed acceptance: verify state before retry
- Ambiguous acceptance: block auto-failover and mark as reconciling

### Webhook Reliability

- All webhooks must be idempotent
- Duplicate events must be ignored
- Signature verification is mandatory
- Merchant webhook dispatch should use background retries with backoff

## Security Considerations

- Continue using bearer secret keys for merchant API auth
- Add `Idempotency-Key` support for client-side safety
- Never expose live secrets directly in browser-based testing
- Encrypt provider secrets at rest
- Verify gateway webhook signatures before state changes
- Keep logs free of sensitive card or secret material
- Use transactional wallet updates for payouts
- Record audit logs for admin routing changes

## Metrics for Success

- Collection success rate uplift versus single static gateway
- Collection initiation availability
- Fallback recovery rate
- Payout success clarity, meaning successful or safely reconciled outcomes
- Duplicate transaction count
- Duplicate payout count
- Average routing decision latency
- Gateway incident detection time
- Dashboard freshness

## Landing Page, API Docs, and Interactive API Testing

### Product Goal

The landing experience should do three jobs well:

- Explain the value of the router quickly
- Let developers understand the API without friction
- Let judges, developers, and demo users test the API immediately in a safe environment

### Recommended Experience

For the hackathon MVP, the best overall approach is:

- Marketing landing page on a modern frontend such as `Next.js`
- API documentation generated from the backend `OpenAPI` spec
- Interactive API testing against a sandbox environment only
- A strong call-to-action from the landing page hero into the docs and playground

### Tooling Options

#### Option A: Mintlify for docs and API playground

Best for:

- Fastest polished developer portal
- Strong out-of-the-box docs UX
- A unified docs experience with API playground support

Pros:

- Great for hackathon polish
- Clean API reference experience from OpenAPI
- Supports custom pages and developer portal style content
- Good fit if docs and testing live on `/docs`

Cons:

- Less flexible if you want a deeply custom embedded tester in the main landing page body

#### Option B: Scalar embedded into a custom landing site

Best for:

- A custom marketing site that wants the API reference or tester embedded directly in-page

Pros:

- Very strong embeddable API reference experience
- Good if you want an inline `Try the API` section inside the site

Cons:

- Slightly more assembly than using a docs-first product
- Narrative docs and marketing polish may require more custom work

#### Option C: Swagger UI or Redoc

Best for:

- Fast backend-driven documentation with minimal setup

Pros:

- Simple
- Cheap
- Easy to wire from FastAPI

Cons:

- Less polished for a hackathon landing experience
- Weaker product storytelling

### Recommendation

Recommended MVP choice:

- Use `Mintlify` for the docs and API playground
- Keep the actual marketing landing page separate, but within the same site or clearly linked
- Put interactive API testing on a dedicated `Docs` or `Playground` section rather than directly inside the homepage hero

This is the best balance of speed, polish, and low implementation risk.

If a truly embedded API tester inside the homepage is non-negotiable, then `Scalar` is the better technical fit for the embedded component.

### Best Method for Browser-Based API Testing

Do not expose live merchant secret keys directly in the browser.

Use this model instead:

1. Expose the FastAPI `OpenAPI` spec from the backend
2. Point Mintlify or Scalar to that spec
3. Provide a sandbox API base URL
4. Use short-lived demo keys or a sandbox-only test key
5. Limit browser testing to safe demo endpoints or test-mode operations

### Recommended Testing Architecture

```text
Landing Page
   |
   +--> Docs CTA --> Developer Docs / Playground
                           |
                           +--> OpenAPI spec from FastAPI
                           +--> Sandbox base URL
                           +--> Prefilled demo API key
                           +--> Browser-based "Try It" requests
```

### Practical MVP Recommendation

- Homepage CTA: `View Docs` and `Try API`
- Docs area: hosted with `Mintlify`
- Playground environment: sandbox only
- Auth for playground: disposable or short-lived test credentials
- Dangerous endpoints: either sandbox only or gated behind a server-side demo proxy

This gives the project a strong product feel without creating security problems.

## Future Improvements

- Merchant-specific gateway credentials
- Multi-currency routing
- Refunds
- Chargeback management
- Smarter routing experimentation
- ML-assisted recommendations
- Advanced reconciliation workflows
- Full merchant self-service dashboard
- Role-based access control for platform ops

## Delivery Recommendations

### Phase 1: Router Foundation

- Introduce gateway adapter abstraction
- Add routing attempt and decision tracking
- Add gateway health snapshots

### Phase 2: Collections Routing

- Refactor `/api/v1/initiate` to call the routing engine
- Add failover logic
- Normalize verification responses

### Phase 3: Payout Routing

- Extend payout routing with safe retry rules
- Add payout attempt tracking
- Add reconciliation states for uncertain outcomes

### Phase 4: Demo Layer

- Add dashboard views for gateway health and routed transactions
- Add developer landing page, docs, and sandbox API testing

## Summary

This MVP turns `x-aggregator` from a multi-gateway payment backend into a true payment router. The core differentiator is not just having multiple provider integrations, but making gateway choice dynamic, observable, and operationally useful.

For the hackathon, the strongest product story is:

- one integration
- four gateways
- visible smart routing
- safe failover
- a polished developer portal with real API testing
