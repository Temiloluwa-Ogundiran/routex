# RouteX Hyper-Saturated Redesign And Mintlify Docs Design

## Summary

RouteX will move to a single product-wide design system based on a hyper-saturated fluid brand language. The redesign applies to the public marketing site, all auth pages, the merchant dashboard, the admin dashboard, and all user-facing email templates. Public API docs will move fully to Mintlify and be served at `/docs`, replacing the current custom docs UI and the standalone sandbox page.

The result should feel like one premium fintech product instead of a stack of separate experiences. The app and emails should look branded, modern, and deliberate, while the docs should feel like a polished developer product with only the public MVP API surface.

## Goals

- Replace the current frontend visual system with the new hyper-saturated fluid design language everywhere.
- Remove the current custom docs UI and standalone sandbox page.
- Make Mintlify the only public docs and API testing experience.
- Limit docs to the public MVP API that external developers should actually use.
- Rewrite email templates so they match the new brand and remove old boxy visual patterns and internal implementation copy.
- Keep the current backend integrations and auth behavior intact while the frontend is redesigned.

## Non-Goals

- Redesigning internal backend admin APIs.
- Expanding the public API surface beyond the approved MVP endpoints.
- Introducing a separate docs domain.
- Maintaining duplicate sandbox functionality outside Mintlify.

## Product Structure

### Public surfaces

- `/`
  - New liquid, high-contrast marketing experience.
- `/docs`
  - Mintlify only.
  - Public API documentation and playground.
- `/login`
- `/signup`
- `/verify-otp`
- `/forgot-password`
- `/reset-password`

### Signed-in surfaces

- `/dashboard`
  - Merchant-facing workspace and payment operations.
- `/admin`
  - Admin routing control room with the same design language.

### Removed or redirected surfaces

- `/sandbox`
  - Retired as a standalone page.
  - Redirect into Mintlify docs.
- Existing custom docs page
  - Removed from the app shell and replaced by Mintlify.

## Visual System

### Core design tokens

- Primary shout color: `#FDE047`
- Background void: `#0A0A0A`
- Secondary dark surface: `#171717`
- Utility gray: `#262626`
- Primary light: `#FFFFFF`
- Type family: `Inter` or `General Sans`

### Shape language

- Large asymmetrical liquid section cuts on public pages and auth surfaces.
- Pill buttons and pill badges as the standard action language.
- Frosted glass summary cards using blur plus subtle white inner borders.
- Oversized radii on containers and no generic small rounded corners.

### Motion language

- Elastic upward entrances on page sections.
- Subtle glass drift on floating cards.
- Soft press/squish behavior on primary buttons.
- Motion should feel fluid and premium, never noisy or novelty-driven.

## Surface-Specific Design Behavior

### Landing page

- Loud hero dominated by cyber yellow.
- Massive typography as the main visual anchor.
- Black void sections for features, trust, and product proof.
- Floating glass finance panels and asymmetric liquid boundaries.

### Auth pages

- Single focused glass card over a strong branded background.
- Clean product copy only.
- No internal auth/session/system wording.
- OTP entry should feel premium but simple.

### Merchant dashboard

- Uses the same brand system but with calmer density than marketing.
- Dark surfaces dominate, with yellow reserved for active state, balances, CTAs, and highlights.
- Data modules use glass selectively, not everywhere.

### Admin dashboard

- Same system as merchant dashboard, but denser and more operational.
- Visual language should still feel premium while preserving control readability.

### Email templates

- Same black/yellow RouteX identity.
- Cleaner and more premium than the current rigid boxed template.
- Minimal, reliable layout with strong hierarchy and inbox-safe HTML.

## Mintlify Docs Design

### Deployment shape

- Mintlify is a separate tracked docs app in the repo at `mintlify-docs/`.
- Public docs remain available at `/docs` on the main domain through reverse proxying.
- The main frontend app no longer owns public docs rendering.
- `/sandbox` redirects into Mintlify instead of rendering a separate tester page.

### Docs scope

Only these public endpoints should appear:

- `POST /api/v1/initiate`
- `GET /api/v1/transactions/verify`
- `POST /api/v1/payout`

### Docs information architecture

- Introduction
- Authentication
- Collections
- Verification
- Payouts
- Webhooks
- Gateway behavior

### Docs content rules

- Explain merchant-facing behavior only.
- Do not expose internal admin or router control endpoints.
- Do not expose platform-only callback endpoints.
- Do not include internal architecture notes in public docs.

### Webhook docs requirements

The Mintlify docs must explain:

- Merchants pass `notification_url` in `initiate` and payout requests.
- RouteX receives gateway/provider webhooks on the backend first.
- RouteX then dispatches normalized events to the merchant `notification_url`.
- Public webhook signature header: `X-AGGREGATOR-SIGNATURE`
- Public event types:
  - `charge.success`
  - `charge.failed`
  - `transfer.success`
  - `transfer.failed`
- Webhook payload example with:
  - `event`
  - `reference`
  - `data.customer.email`
  - `data.amount`
  - `data.currency`
  - `data.metadata`

### Gateway behavior notes

The docs should explicitly state:

- Merchants send amounts in customer-facing currency units.
- RouteX handles gateway-specific unit conversion internally.
- `gateway_code` is optional and forces a gateway only when provided.
- When `gateway_code` is omitted, RouteX routes automatically.
- Some providers require RouteX webhook URLs in their provider dashboard.
- Some flows rely on payload-based callback and redirect configuration.

## Architecture

### Frontend application

The existing Next.js app remains the primary product frontend. Its current shared layout, component primitives, and section styles will be replaced with the new brand system. Existing auth and backend proxy flows stay in place, but the UI layer is rebuilt so the app feels coherent from landing through admin.

### Mintlify integration

Mintlify becomes the public docs product. The repo will include a tracked docs app with curated content and an OpenAPI-backed API reference. The live `/docs` path will proxy to Mintlify using Mintlify's official `/docs` hosting guidance.

### Email delivery

Email sending remains in the current backend delivery pipeline, but the HTML templates and copy are rewritten. OTP and receipt-related templates should be treated as branded product surfaces, not operational afterthoughts.

## Routing And Link Behavior

- Public header and footer links should route into the redesigned experiences only.
- Signed-in users should not see irrelevant public login CTAs.
- `/sandbox` should no longer be linked as a standalone frontend page.
- Any "Start Testing" action should route into Mintlify docs or the Mintlify playground entry point.

## Error Handling

- If Mintlify is unavailable, `/docs` should fail clearly rather than silently loading stale custom docs.
- If a signed-in user hits a removed page like `/sandbox`, redirect them into `/docs`.
- If auth state is unavailable, frontend behavior should remain stable and not expose mixed guest/user controls.
- Email templates should degrade safely in inboxes that do not fully support advanced CSS.

## Verification Criteria

The redesign is only complete when:

- Landing, auth, merchant dashboard, and admin all visibly follow the new design system.
- The app no longer mixes old and new visual primitives.
- `/docs` is Mintlify.
- `/sandbox` is removed or redirected.
- Public docs only contain the approved MVP endpoints.
- Webhook docs clearly explain merchant-facing webhook behavior and payloads.
- Email templates render cleanly and match the brand.
- Key routes and auth flows continue to pass Playwright coverage.
