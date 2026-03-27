# RouteX

**RouteX is a payment orchestration platform for businesses that want one simple way to accept payments, track results, and stay online when a gateway has issues.**

Instead of building a separate flow for every provider, a merchant connects to RouteX once. RouteX then helps choose the best gateway, sends the customer to checkout, verifies the result, and sends one clear update back to the merchant.

## Live links

- Product: [routex.xoroai.cloud](https://routex.xoroai.cloud)
- Docs: [docs.routex.xoroai.cloud](https://docs.routex.xoroai.cloud)
- API: [routexapi.xoroai.cloud](https://routexapi.xoroai.cloud)

## What problem RouteX solves

Many online businesses depend on one payment gateway.

When that gateway slows down or fails, the business immediately feels it:

- lost checkouts
- poor customer experience
- manual switching between providers
- extra engineering work
- limited visibility into what actually happened

RouteX fixes that by giving the merchant one payment layer instead of one gateway.

## What RouteX does

- Accepts payments through one API
- Routes payments through supported gateways
- Lets merchants choose a gateway manually when needed
- Returns the direct provider checkout link to the customer
- Verifies the final transaction result
- Sends one signed webhook update to the merchant
- Gives merchants one dashboard for balances, transactions, keys, and operations
- Gives admins one control room for gateway health and routing visibility

## Why this matters

RouteX makes payments easier to understand and easier to trust.

For a business owner, that means:

- fewer moving parts
- one dashboard instead of many
- clearer payment updates
- easier testing
- a better fallback story when one provider is having a bad day

## Core product features

### 1. Unified collections

The merchant sends one request to RouteX to start a payment.

RouteX can:

- route automatically based on gateway health and latency
- respect a merchant gateway override
- return a direct checkout link from the selected provider

### 2. Unified verification

The merchant checks one verification endpoint and gets a normalized answer, no matter which provider handled the payment.

### 3. Signed merchant webhooks

Providers notify RouteX first.

RouteX then:

- normalizes the event
- updates the transaction
- sends one signed merchant webhook to the merchant `notification_url`

### 4. Merchant dashboard

The merchant workspace shows:

- balances
- API keys
- recent transactions
- payment links

### 5. Admin control room

The admin area shows:

- gateway health
- latency
- routing decisions
- platform visibility for operations

## notes

- RouteX is live, not just mock screens
- The public docs are live and hosted separately
- Merchant auth and admin auth are both implemented
- Multiple payment gateways are integrated
- Webhook normalization is implemented
- Routing decisions are based on live health and latency
- Payouts are currently **simulated from merchant balance** for demo reliability

That payout choice is intentional for the MVP:

- it removes bank-transfer instability during demos
- it keeps the merchant experience consistent
- it still shows how payout deductions and reporting work

## Supported gateways

RouteX currently works with:

- Flutterwave
- Paystack
- Korapay
- Interswitch

## Quick walkthrough

If you want to evaluate RouteX quickly:

1. Open the landing page and docs
2. Create a merchant account
3. Open the dashboard
4. Review balances, transactions, and API keys
5. Start a collection through the docs or API
6. Confirm the routed transaction and webhook behavior

## How the system works

1. A merchant starts a payment with one RouteX request
2. RouteX selects a gateway or respects the merchant override
3. RouteX returns the provider checkout link
4. The customer pays on the provider page
5. RouteX verifies the outcome
6. RouteX updates the transaction record
7. RouteX sends one signed webhook back to the merchant

## Technical highlights

### Backend

- FastAPI API layer
- PostgreSQL for transactional storage
- Redis for async orchestration support
- Celery workers for background processing
- Gateway adapter pattern for provider integrations
- Routing engine driven by gateway health and latency
- Webhook normalization layer for provider-specific events

### Frontend

- Next.js App Router
- Public product site
- Merchant dashboard
- Admin control room
- Hosted Mintlify docs

## Team COntribution
Temiloluwa Ogundiran
- Backend Developer

Kwaghuter Raphael
-Frontend Developer





### Product architecture

- Single merchant-facing API surface
- Single merchant webhook contract
- Direct provider checkout handoff
- Operational visibility for admins

## Built with

- FastAPI
- PostgreSQL
- Redis
- Celery
- Next.js
- Mintlify
- Resend
- PostHog
- Docker Compose
