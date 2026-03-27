# RouteX

**RouteX is a payment orchestration layer that helps merchants accept payments through one integration while RouteX routes each transaction through the best available gateway.**

Instead of depending on a single provider and losing revenue during downtime, merchants connect once, initiate a payment once, and let RouteX handle gateway selection, failover, verification, webhooks, and operational visibility.

## Live Product

- Frontend: [routex.xoroai.cloud](https://routex.xoroai.cloud)
- Docs: [docs.routex.xoroai.cloud](https://docs.routex.xoroai.cloud)
- API: [routexapi.xoroai.cloud](https://routexapi.xoroai.cloud)

## The Problem

Online businesses in Nigeria often rely on a single payment gateway.

When that gateway slows down, fails, or degrades, the business feels it immediately:

- failed checkouts
- lost revenue
- manual gateway switching
- poor visibility into what went wrong
- extra engineering work to maintain multiple provider integrations

Most teams either hard-code one provider or build fragile gateway-by-gateway logic themselves.

## Our Solution

RouteX gives merchants one unified payment layer.

A merchant sends one request to RouteX, and RouteX:

1. evaluates the available gateways
2. chooses the healthiest eligible route
3. returns a hosted checkout link
4. tracks the transaction lifecycle
5. verifies the final result
6. dispatches a normalized webhook back to the merchant

The result is a simpler integration for merchants and a more resilient payment flow for end users.

## What RouteX Does

- unified collections API
- unified payout API
- transaction verification API
- dynamic routing across multiple gateways
- health-aware gateway selection
- direct gateway checkout handoff
- normalized merchant webhooks
- merchant dashboard for balances, transactions, and API keys
- admin control room for gateway health, routing visibility, and operations

## Supported Gateways

RouteX currently integrates with:

- Paystack
- Flutterwave
- Korapay
- Interswitch

## Why This Product Is Strong

### 1. One integration, many gateways

Merchants do not need to build and maintain separate checkout flows for every provider.

### 2. Better reliability

RouteX can choose a healthier route instead of forcing all traffic through one gateway.

### 3. Operational clarity

Every routed transaction has a visible gateway decision, reference trail, and final status.

### 4. Cleaner merchant experience

Merchants get a single dashboard, one set of API keys, one webhook contract, and one verification flow.

### 5. Real product, not a static demo

This submission includes a live frontend, live backend, live docs, merchant auth, admin tools, gateway integrations, background workers, and webhook handling.

## How It Works

### Collections

The merchant calls `POST /api/v1/initiate` with:

- amount
- customer
- reference
- optional `gateway_code`
- optional `redirect_url`
- optional `notification_url`

If `gateway_code` is omitted, RouteX routes automatically.

If `gateway_code` is provided, RouteX respects the merchant override when that gateway is eligible.

RouteX then returns a checkout link for the selected gateway.

### Verification

The merchant calls the verification endpoint once and gets a normalized response, regardless of the underlying provider.

### Webhooks

Providers call RouteX first.

RouteX verifies and normalizes the event, updates the transaction state, and then sends a signed merchant webhook to the merchant’s `notification_url`.

### Admin Operations

The admin control room shows:

- gateway health
- latency
- routing outcomes
- transaction visibility
- failover posture

## Product Surfaces

### Public site

The public site explains the product, drives signups, and links to the hosted developer docs.

### Developer docs

The docs focus only on the core MVP endpoints external developers should use:

- initiate collection
- verify transaction
- payout
- webhook handling

### Merchant workspace

The merchant dashboard provides:

- transaction overview
- balances
- payment links
- API key access
- mode switching

### Admin control room

The admin area is built for platform operations and routing visibility.

## MVP Scope

This hackathon version is intentionally focused:

- Nigeria-first
- NGN-first
- test-mode oriented
- fast to demo
- structured for production expansion

## Architecture

### Backend

- FastAPI
- PostgreSQL
- Redis
- Celery workers and beat

### Frontend

- Next.js App Router

### Product Infrastructure

- gateway adapters for Paystack, Flutterwave, Korapay, and Interswitch
- webhook normalization layer
- routing engine based on live gateway health and latency
- OTP authentication with email delivery
- hosted developer docs with API playground

## Why RouteX Matters

Payments are too important to leave to a single provider.

RouteX turns payment routing into a product instead of a hidden workaround. It gives merchants higher resilience, clearer visibility, and a simpler integration model, all through one clean platform.

## Team

### Temiloluwa Ogundiran

- backend architecture
- API design and gateway integrations
- routing engine
- webhook normalization
- workers and deployment

### Kwaghuter Raphael

- frontend architecture
- product UI and dashboards
- auth flows
- docs experience
- presentation polish

## Built With

- FastAPI
- PostgreSQL
- Redis
- Celery
- Next.js
- Resend
- PostHog
- Docker Compose
