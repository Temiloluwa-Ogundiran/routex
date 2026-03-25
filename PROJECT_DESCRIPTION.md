# RouteX - Complete Project Description

## Overview

RouteX is a multi-payment router that unifies payment operations for Nigerian merchants by integrating multiple gateways behind one API contract.

It handles:

- collections
- payouts
- transaction verification
- gateway failover
- health-aware routing
- webhook normalization
- routing observability

## Product Surfaces

- Public app:
  - Landing page
  - Public docs (`/docs`)
  - API tester on landing page
- User app:
  - OTP auth
  - Merchant dashboard (`/dashboard`)
  - Wallets, transactions, payment links, API keys
- Admin app:
  - Admin auth
  - Gateway controls
  - Health refresh
  - Routing rules
  - Transaction observability

## Routing Model

Routing follows:

1. Eligibility filtering (supported op, channel, mode, gateway state)
2. Score-based ranking by health/performance
3. Decision + fallback order persistence
4. Attempt logging per transaction

Core routing entities:

- `RoutingAttempt`
- `RoutingDecisionAudit`
- `GatewayHealthSnapshot`
- `RoutingRule`

## Gateway Coverage

- Paystack
- Flutterwave
- Korapay
- Interswitch (hosted checkout bridge + verify + signed webhooks)

## Reliability

- Background health refresh via Celery beat
- Idempotent webhook normalization
- Conservative payout behavior for ambiguous states
- Admin override controls for gateway availability and priority

## Docs and API Testing

- Public OpenAPI contract: `/public/openapi.json`
- Docs page generated from contract with request/response examples
- Landing-page tester proxies requests server-side to backend sandbox key
- If sandbox config is missing, tester is disabled (no fake response fallback)

## Deployment Model

Containers:

- `routex-api` (FastAPI + migrations)
- `routex-frontend` (Next.js)
- `routex-worker` (Celery worker)
- `routex-beat` (Celery beat scheduler)

Dependencies:

- PostgreSQL
- Redis

## Security Notes

- Merchant API keys via Bearer auth
- User and admin auth split
- Signed webhook verification per gateway
- OTP delivery via Resend (OTP not returned in auth API responses)
