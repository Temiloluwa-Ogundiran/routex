# RouteX Landing Page UI Spec

## Purpose

This document translates the provided neo-brutalist reference style into a RouteX-specific landing page and developer experience for a multi-payment router product.

The page should do four jobs clearly:

- make RouteX feel bold, modern, and credible
- explain the product in under 10 seconds
- demonstrate the routing/dashboard story visually
- let developers explore the API and test sandbox requests without leaving the branded experience

## Assumptions

- Brand/product name: `RouteX`
- Primary frontend: `Next.js`
- Styling system: `Tailwind CSS` with custom CSS variables for branded tokens
- Full API reference: embedded `Scalar` reference page fed from FastAPI OpenAPI
- Landing-page API testing: custom-styled sandbox playground component, not a raw third-party embed
- API docs/testing must visually match the neo-brutalist brand language rather than look like a generic docs portal

## Design Direction

The page should preserve the strong geometry and color blocking from the reference while shifting the message from creator SaaS to financial infrastructure.

The tone should feel:

- technically sharp
- operationally confident
- slightly playful
- demo-friendly

This is not a soft fintech aesthetic. It should feel like an infrastructure product with personality.

## Visual System

### Brand Tokens

- Primary yellow: `#ffe17c`
- Background charcoal: `#171e19`
- Accent sage: `#b7c6c2`
- White UI surface: `#ffffff`
- Black text/border: `#000000`
- Dark gray support: `#272727`

### Typography

- Headings: `Cabinet Grotesk`
- Body/UI labels: `Satoshi`
- Heading weights: `700-800`
- Body weight: `500`
- Tight tracking on hero and section titles

### Border and Shadow Language

- All interactive elements use `2px solid #000000`
- Standard hard shadow: `4px 4px 0px 0px #000000`
- Large card/container hard shadow: `8px 8px 0px 0px #000000`
- No blur shadows
- No gradients

### Motion Language

- Buttons visually "press" into their own shadow on hover
- Cards lift slightly using `translate(-2px, -2px)` or icon color swaps
- Avoid floaty or soft motion
- Transitions should feel tactile, short, and physical

### Patterning

- Use the radial dot pattern on yellow sections only
- Keep pattern opacity around `10%`
- Avoid patterns on dark sections unless extremely subtle

## Information Architecture

```text
1. Fixed Header
2. Hero
3. Gateway / Trust Marquee
4. Problem vs RouteX
5. Feature Grid
6. How It Works
7. Use Cases
8. API Quickstart + Sandbox Playground
9. Demo Dashboard Teaser
10. Proof / Metrics or Testimonials
11. Final CTA
12. Footer
```

## Page Narrative

The story should move in this order:

1. RouteX gives you one payment API.
2. It routes across multiple gateways automatically.
3. It improves reliability and visibility.
4. Developers can test it immediately.
5. Operators can monitor it visually.

## Header

### Structure

- Fixed top navigation
- Height: `80px`
- Background: `#ffe17c`
- Bottom border: `2px solid black`

### Left

- RouteX wordmark
- Square icon with lightning or split-route mark

### Center Nav

- `Product`
- `How It Works`
- `Dashboard`
- `Docs`
- `Sandbox`

### Right

- Secondary text link: `Log In`
- Primary push button: `Start Testing`

## Hero Section

### Layout

- Two-column desktop grid
- Stacked on mobile
- Background: `#ffe17c`
- Includes radial dot pattern

### Left Column Content

- Top badge: `NEW: Intelligent gateway failover is live`
- Main heading:
  - `ROUTE EVERY PAYMENT`
  - `THROUGH THE`
  - `SMARTEST PATH.`
- One keyword should use outlined text styling
- Supporting copy:
  - One API for collections and payouts
  - Smart routing across Paystack, Flutterwave, Korapay, and Interswitch
  - Visibility for merchants, platforms, and ops teams

### Hero CTA Group

- Primary button: `Try Sandbox`
- Secondary button: `View API Docs`
- Small note row:
  - `NGN-first`
  - `Sandbox-ready`
  - `No live key required`

### Right Column Visual

Use a branded browser mockup showing:

- gateway score cards
- transaction success chart
- active gateway chip row
- a failover event badge
- payout queue or wallet balance card

The mockup should imply live system behavior, not generic SaaS analytics.

### Example Hero Copy

`ROUTE EVERY PAYMENT THROUGH THE SMARTEST PATH.`

`One integration for collections and payouts, smart gateway failover, and routing visibility across Nigeria's leading payment rails.`

## Gateway / Trust Marquee

### Purpose

Immediately establish that RouteX is a multi-gateway orchestration layer.

### Content Options

Use either:

- gateway names: `PAYSTACK`, `FLUTTERWAVE`, `KORAPAY`, `INTERSWITCH`
- or operator labels: `MERCHANTS`, `PLATFORMS`, `FINOPS`, `OPS TEAMS`, `CHECKOUT`, `PAYOUTS`

### Visual Style

- Full-width charcoal band
- Sage text at low opacity
- Slow horizontal movement
- Strong section contrast after hero

## Problem vs RouteX Section

### Section Goal

Translate the core product pain into a simple before/after story.

### Layout

- White background
- Centered heading
- Two large side-by-side cards

### Left Card: The Old Way

- Light gray or faded white panel
- Dashed border
- Reduced opacity
- Problems list:
  - Single gateway downtime kills conversion
  - Manual switching during incidents
  - Separate integrations for collections and payouts
  - No visibility into why a payment failed

### Right Card: The RouteX Way

- Yellow card
- Hard shadow
- Strong black border
- Benefits list:
  - One integration across four gateways
  - Smart routing based on health and performance
  - Unified verification and webhooks
  - Dashboard visibility for failovers and trends

## Feature Grid

### Section Goal

Give the product concrete substance after the emotional positioning.

### Layout

- Yellow background
- 3-column desktop grid
- White cards with hard shadows

### Recommended Feature Cards

1. `Smart Routing`
2. `Automatic Failover`
3. `Unified Payouts`
4. `Routing Analytics`
5. `Webhook Normalization`
6. `Sandbox-First API`

### Card Behavior

- Icon tile uses sage by default
- On hover, icon tile shifts to yellow
- Card raises slightly

## How It Works

### Section Goal

Make the product feel straightforward to adopt.

### Background

- Charcoal

### Steps

1. `Connect`
   - Add one RouteX key
2. `Route`
   - RouteX scores gateways and selects the best path
3. `Monitor`
   - Watch transactions, failovers, and payout activity in one dashboard

### Supporting CTA

- Right-aligned text link: `See full API docs`

## Use Cases

### Section Goal

Show that RouteX serves different operational personas, not just developers.

### Cards

1. `For Merchants`
   - Improve checkout reliability
   - Keep one integration

2. `For Platforms`
   - Manage many merchants through one routing layer
   - Centralize payment orchestration

3. `For Ops & Finance`
   - See gateway incidents fast
   - Track payouts and wallet movement

### Styling

- One sage card
- One yellow card with stronger shadow
- One charcoal card with white text

## API Quickstart + Sandbox Playground

### This Section Is Critical

Because the user explicitly wants API documentation and testing on the landing page, this section should be productized, not tacked on.

### Best Method

For this design system, the best approach is:

- build a custom-branded sandbox playground section directly in the landing page
- use `Scalar` for the full reference docs on a dedicated docs route
- avoid embedding a full Mintlify experience inside the hero-driven marketing page

### Why

- Mintlify is excellent for a standalone docs portal, but it will visually diverge from this neo-brutalist landing page unless heavily separated
- Scalar is more embeddable for reference views
- a custom playground component gives full control over layout, color, motion, and sandbox safety

### Section Layout

- Background: white or charcoal depending on page rhythm
- Two-column layout

#### Left Column

- `Quickstart` heading
- Copyable request snippets
- Step list:
  1. Use sandbox key
  2. Call `/api/v1/initiate`
  3. Verify with `/api/v1/transactions/verify`

#### Right Column

- Interactive tester card with tabs:
  - `Initiate`
  - `Verify`
  - `Payout`
- Request editor
- Send button
- Response pane
- Demo auth chip showing `Sandbox mode`

### Playground Guardrails

- Browser never sees live secrets
- Requests go through a server-side playground proxy or short-lived demo-token route
- Only whitelisted test-mode endpoints are callable from the landing page playground
- Add visible badge: `Sandbox only`

### Full Docs Link

Include a clear CTA:

- `Open Full API Reference`

This links to a full docs route that uses the same brand shell and a deeper reference experience.

## Demo Dashboard Teaser

### Goal

The landing page should hint at the dashboard without requiring users to understand every metric immediately.

### Recommended Layout

- Charcoal section
- Left copy block
- Right large mockup or screenshot-style panel

### Highlighted Dashboard Elements

- gateway health cards
- success-rate sparkline
- recent routed transaction list
- failover event timeline
- payout status widget

## Proof Section

### Recommended Direction

Because RouteX is early-stage, use proof cards or metrics if real testimonials do not exist yet.

### Preferred Option for MVP

Three proof cards:

- `4 Gateways. 1 API.`
- `Collections + Payouts`
- `Real-time routing visibility`

### Alternative

If you want testimonials, use them in the same card shapes as the reference, but avoid fake enterprise claims.

## Final CTA

### Goal

Push users into either sandbox testing or docs exploration.

### Copy Direction

- `READY TO ROUTE SMARTER?`
- Subcopy:
  - `Test collections, payouts, and verification in the RouteX sandbox before you wire in production.`

### Buttons

- Primary: `Start in Sandbox`
- Secondary: `View API Docs`

## Footer

### Columns

- Product
- Developers
- Company
- Social

### Must-Include Links

- `API Reference`
- `Sandbox`
- `Status`
- `Privacy`
- `Terms`

## Component Notes

### Neo-Brutalist Push Button

- black background by default
- white text
- `2px` border
- `8px` hard shadow
- hover shifts into its own shadow

### Browser Mockup

- white card
- black border
- large shadow
- internal cards in sage, charcoal, and yellow

### Playground Console Card

- two-pane layout
- left request block
- right response block
- top utility row with endpoint selector and sandbox status chip

### Gateway Chips

- small pill or square badges for `PSTK`, `FLTW`, `KORA`, `ISW`
- active gateway highlighted in yellow
- degraded gateway uses white chip with alert icon

## Responsive Rules

### Mobile

- Collapse hero to one column
- Turn feature grids into stacked cards
- Turn how-it-works steps into vertical stack
- Keep playground as tabbed card with scrollable code area

### Tablet

- Preserve two-column hero if there is enough space
- Collapse 3-column layouts into 2 columns where needed

### Desktop

- Use full-width, high-contrast section transitions
- Keep dashboard and playground visuals large and legible

## Content Tone

All copy should sound:

- direct
- slightly punchy
- technically competent
- not fluffy

Preferred words:

- route
- failover
- visibility
- gateway health
- sandbox
- unified API

Avoid:

- vague productivity language
- generic "AI" phrasing
- soft consumer-fintech language

## Recommended Technical UX for Docs and Testing

### Best Fit

For this exact visual direction and requirement set:

- Landing page + sandbox tester: custom `Next.js` implementation
- Full API reference: `Scalar` page fed from FastAPI OpenAPI
- Future standalone developer portal option: `Mintlify`, if a separate docs experience becomes more important than brand continuity

### Final Recommendation

If the requirement is truly "API testing on the landing page," do not use Mintlify as the main in-page testing surface.

Use:

- custom landing page section for the branded tester
- sandbox proxy route for safety
- Scalar for deeper reference docs

That approach is the best combination of:

- visual consistency
- developer usability
- hackathon speed
- security control

