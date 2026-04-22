# RouteX

RouteX is a payment orchestration platform that gives merchants a single integration layer for collecting payments, verifying transactions, and receiving normalized webhook updates while multiple payment gateways run underneath.

Instead of wiring a product directly to one provider, RouteX sits in front of supported gateways, applies routing logic, returns the selected checkout experience, tracks the transaction lifecycle, and exposes a unified merchant-facing API and dashboard.

## What the project does

RouteX is designed to reduce the operational pain of depending on a single gateway.

With RouteX, a merchant can:

- initialize payments through one API
- route payments across supported gateways
- override gateway selection when needed
- verify transactions through one normalized flow
- receive signed webhook notifications in a consistent format
- monitor transactions, wallet activity, and routing behavior from a central dashboard

For platform operators, RouteX also includes admin tooling for visibility into gateway health, analytics, and routing controls.

## Core capabilities

### Unified payment initialization

The backend exposes a single API surface for starting collections. RouteX chooses the gateway based on routing logic and returns the provider checkout link or checkout flow needed to complete the payment.

### Gateway-aware routing

The platform includes routing and health services that support gateway selection using operational signals such as availability and latency.

### Transaction verification

Merchants verify transactions through RouteX instead of handling provider-specific verification logic themselves.

### Webhook normalization

Providers send events into RouteX first. RouteX standardizes those events, updates internal transaction state, and forwards a signed webhook to the merchant's configured notification endpoint.

### Merchant and admin surfaces

The repository includes:

- a public-facing frontend
- merchant authentication and workspace flows
- admin controls for routing and monitoring
- separate hosted documentation content under `mintlify-docs`

### Background processing

Celery workers and scheduled jobs support asynchronous tasks such as lifecycle updates, operational jobs, and balance-related flows.

## Supported gateways

Current integrations in the codebase include:

- Paystack
- Flutterwave
- Korapay
- Interswitch

## Product scope and MVP constraints

This project is currently shaped as a Nigeria-first MVP with these constraints:

- NGN-focused flows
- test-mode oriented integrations
- payout behavior that is partially simulated for demo reliability

The payout simulation is intentional in the current version: it allows the system to demonstrate payout deductions, balance movement, and reporting without depending on unstable bank-transfer behavior during demos and testing.

## Repository architecture

### Backend

The backend is a FastAPI application with supporting services for routing, transactions, wallets, analytics, webhooks, and admin operations.

Main pieces:

- `main.py`: FastAPI entrypoint
- `api/`: route registration and HTTP views
- `services/`: business logic and gateway/routing services
- `schemas/`: request and response models
- `database/`: database setup and persistence helpers
- `alembic/`: database migrations
- `crons/`: scheduled jobs
- `websocket/`: websocket support

Key backend technologies:

- FastAPI
- PostgreSQL
- Redis
- Celery
- SQLAlchemy and Tortoise ORM components
- Alembic

### Frontend

The `frontend/` app is a Next.js application that powers the web interface for the product experience and dashboard flows.

Key frontend technologies:

- Next.js
- React
- TypeScript
- Playwright for frontend tests
- PostHog for analytics instrumentation

### Documentation

The repository also contains a Mintlify documentation site in `mintlify-docs/`.

## High-level request flow

1. A merchant calls RouteX to initialize a payment.
2. RouteX selects a gateway or honors an explicit gateway override.
3. RouteX returns the provider checkout destination.
4. The customer completes payment on the provider side.
5. RouteX verifies and records the transaction outcome.
6. RouteX emits a normalized signed webhook back to the merchant.
7. Merchant and admin users can review activity in the dashboard.

## Local development

### Prerequisites

- Python 3.11+ recommended
- Node.js 20+ recommended
- PostgreSQL
- Redis
- Docker and Docker Compose for containerized setup

### Backend setup

1. Create and activate a Python virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Copy `.env.example` to `.env` and fill in the required secrets and service URLs.
4. Run database migrations.
5. Start the API server:

```bash
python main.py
```

You can also run the app with Uvicorn directly if preferred.

### Frontend setup

```bash
cd frontend
npm install
npm run dev
```

### Docker setup

The repository includes a `docker-compose.yml` that starts:

- PostgreSQL
- Redis
- FastAPI API service
- Celery worker
- Celery beat scheduler
- Next.js frontend

Start everything with:

```bash
docker compose up --build
```

## Environment and configuration

Important environment variables referenced by the project include:

- `DB_URL`
- `REDIS_URL`
- `SERVER_URL`
- `FRONTEND_BASE_URL`
- `CHECKOUT_URL`
- `AUTH_SECRET`
- `AGG_SECRET`
- gateway credentials such as Paystack, Flutterwave, Korapay, and Interswitch secrets
- email and notification credentials such as Resend configuration

Use `.env.example` as the starting point for local configuration.

## API and operational areas in the codebase

The registered backend routes cover areas such as:

- authentication
- merchants and users
- wallets
- analytics
- router controls
- payment links
- categories and beneficiaries
- transactions
- v1 initialize and verification flows
- payouts
- checkout flows
- provider webhooks
- websocket updates

## Project structure

```text
routex/
|-- api/
|-- alembic/
|-- crons/
|-- database/
|-- frontend/
|-- mintlify-docs/
|-- schemas/
|-- services/
|-- tests/
|-- websocket/
|-- docker-compose.yml
|-- main.py
|-- requirements.txt
|-- settings.py
```

## Tests

Backend test configuration is present through `pytest`.

Typical backend test run:

```bash
pytest
```

Frontend test assets and Playwright configuration are present in `frontend/tests` and `frontend/playwright.config.ts`.
