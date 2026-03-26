# RouteX Dual-Mode Design System Design

## Summary

RouteX will move to a synchronized two-mode design system instead of a single visual language forced across every surface.

- Public-facing surfaces will use an acid neo-brutalist system:
  - landing
  - auth
  - payment status
  - hosted docs branding
  - HTML emails
- Signed-in product surfaces will use a monochrome blueprint operations system:
  - merchant dashboard
  - admin dashboard
  - transaction detail and routing operations views

The two modes will share brand DNA, spacing rhythm, border logic, icon language, motion timing, and copy tone so they still read as one product.

## Goals

- Replace the current mixed frontend styling with a disciplined, route-aware design system.
- Make the public experience feel loud, memorable, and branded.
- Make signed-in merchant and admin surfaces feel precise, technical, and easier to scan.
- Redesign all HTML templates so email visuals match the new RouteX identity.
- Keep Mintlify hosted, but align its hosted theme and content structure with the public RouteX brand.

## Non-Goals

- Rebuilding Mintlify inside the Next.js app.
- Changing backend business logic unless a UI or docs pass uncovers a real product bug.
- Forcing acid neo-brutalism onto dense dashboard tables and controls.
- Introducing realistic photography into operational surfaces.

## Design Decision

When the public prompt and dashboard prompt conflict, use this precedence:

- Public, auth, pay, docs, and email:
  - acid neo-brutalist rules win
- Merchant and admin dashboards:
  - blueprint ops rules win
- Shared interaction, spacing, iconography, and branding:
  - common RouteX foundation wins

## Route Map

### Acid neo-brutalist layer

- `/`
- `/login`
- `/signup`
- `/verify-otp`
- `/forgot-password`
- `/reset-password`
- `/pay/status`
- `docs.routex.xoroai.cloud`
- HTML templates in backend email delivery

### Blueprint ops layer

- `/dashboard`
- `/dashboard/transactions/[reference]`
- `/admin`
- `/admin/login`
- `/admin/transactions/[reference]`
- router controls
- gateway health
- routing rules
- observability panels

## Shared RouteX Foundation

### Core brand tokens

- `--rx-ink: #09090B`
- `--rx-paper: #F8F4E8`
- `--rx-acid: #D2E823`
- `--rx-white: #FFFFFF`
- `--rx-gray-50: #FAFAFA`
- `--rx-gray-100: #F3F4F6`
- `--rx-gray-200: #E5E7EB`
- `--rx-gray-400: #9CA3AF`
- `--rx-gray-500: #6B7280`
- `--rx-gray-900: #111827`

### Shared spacing rhythm

- Tight UI increments should still align to a shared spacing scale.
- Cards and page shells should use deliberate whitespace, not ad-hoc padding per section.
- Section spacing should follow a clear hierarchy:
  - hero spacing largest
  - content spacing medium
  - control spacing tightest

### Shared interaction rules

- Primary actions must always feel tactile.
- Focus states must be obvious and keyboard-safe.
- Icon stroke language stays geometric and outlined.
- Motion timing should feel crisp and deliberate across both systems.

### Shared copy rules

- Product-facing only.
- No internal architecture wording on the frontend.
- No implementation details such as session storage, temporary browser state, or internal routing mechanics.
- Tone should be bold, clear, technical, and concise.

## Acid Neo-Brutalist System

### Typography

- Display and hero headings:
  - `Dela Gothic One`
  - uppercase or near-uppercase emphasis where appropriate
  - tight tracking
- Body and interface text:
  - `Space Grotesk`
  - weights `400` to `700`

### Visual language

- Paper-like background using `#F8F4E8`
- Heavy black borders
- Acid yellow-green used as the signature accent
- Hard shadows only:
  - no blur shadows
  - offset-box shadows only
- Subtle noise overlay at low opacity
- Sticker badges, ticker strips, marquee rails, and glitch display interactions

### Buttons

- Every public interactive element keeps a `2px` solid `#09090B` border.
- Hard shadow default:
  - `4px 4px 0 0 #09090B`
- Active press:
  - translate and collapse shadow
- Primary buttons:
  - black fill with acid or paper contrast
- Secondary buttons:
  - paper or transparent fill with strong outline

### Cards

- Borders:
  - `2px` solid `#09090B`
- Radius:
  - `12px` to `32px`
- Hover:
  - slight positional movement with shadow reduction
- Decorative cards may float or overlap in hero compositions

### Motion

- Glitch hover only on select display text
- Continuous marquee loop for highlight strips
- Floating motion for accent cards only
- No gratuitous motion on forms or docs content

## Blueprint Ops System

### Typography

- Every text element uses `JetBrains Mono`
- Section labels:
  - uppercase
  - `9px` to `10px`
  - tracking widest
- Body and interface text:
  - `11px` to `12px`
- Hero and section headings:
  - `20px` to `24px`

### Visual language

- App background:
  - `#F3F4F6`
- Card/surface background:
  - `#FFFFFF`
- Borders:
  - `1px solid #E5E7EB`
- Shadows:
  - only subtle `shadow-sm`
- Decorative assets:
  - abstract SVGs
  - grids
  - circles
  - triangles
  - wave paths
  - crosshair geometry

### Layout

- Fixed left sidebar
- Sticky top header
- Scrollable content region
- Structured grid sections
- White cards with predictable spacing and low-noise hierarchy

### Interaction

- Border darkens on hover
- Active nav items become white surfaced panels
- Motion remains minimal and precise
- No glitch, no marquee, no sticker treatment in dashboard surfaces

## Landing Page Redesign

### Structure

- Sticky brutalist top bar with:
  - RouteX wordmark
  - compact navigation
  - strong CTA
- Hero split:
  - oversized statement headline on the left
  - layered product card/mock asset on the right
- Followed by:
  - marquee strip
  - bento-style product storytelling
  - dark value section
  - closing CTA
  - dark footer

### Content rules

- Remove fake operational metrics on the public homepage
- Remove generic fintech filler copy
- Replace pseudo-dashboard preview blocks with editorial product storytelling
- Make the homepage feel like a premium developer-fintech brand, not an admin app preview

## Auth Redesign

### Layout

- Split layout:
  - editorial introduction panel
  - brutalist form card
- Strong display headline
- Tighter form controls
- Simpler product instructions

### Copy rules

- Remove internal session or auth implementation references
- Keep focus on:
  - enter email
  - receive code
  - complete sign-in

## Merchant Dashboard Redesign

### Layout

- Fixed-width left sidebar
- Sticky technical header
- Merchant hero summary
- Stats row
- Structured content modules for:
  - wallet balances
  - API keys
  - transactions
  - payment links
  - mode summary

### Visual behavior

- White cards
- fine borders
- blueprint SVG panels
- technical labels
- readable tables

### Cleanup

- Remove any sandbox CTA from the dashboard
- Remove public navigation confusion from signed-in views
- Keep docs access available as a concise action only

## Admin Dashboard Redesign

### Layout

- Same blueprint shell as merchant dashboard
- Slightly denser data layout
- Strong emphasis on:
  - gateway health
  - routing rules
  - failover feed
  - transaction observability

### Rules

- Keep dense controls readable
- Keep decorative assets subdued and structural
- Use geometry as support, never as noise

## Payment Status Redesign

- Use the public acid neo-brutalist layer
- One confident centered status composition
- Strong CTA and status badge treatment
- Cleaner success, pending, and failure presentation

## Email Template Redesign

### System

- Acid neo-brutalist styling adapted for inbox-safe HTML
- Table-based structure
- Bold black framing
- acid highlights
- simple hierarchy

### Rules

- No brittle advanced CSS that breaks major inboxes
- No internal implementation wording
- Strong emphasis on:
  - code
  - call to action
  - expiry or safety note

## Mintlify Alignment

### Hosting

- Keep Mintlify hosted
- Do not embed or rebuild it inside the Next.js frontend

### Theme direction

- Match the public RouteX acid brand within Mintlify’s hosted theming limits
- Keep content concise, external-facing, and technically clean

### Content boundaries

Expose only the external MVP endpoints:

- `POST /api/v1/initiate`
- `GET /api/v1/transactions/verify`
- `POST /api/v1/payout`

Include:

- request examples
- response examples
- webhook payload docs
- `X-AGGREGATOR-SIGNATURE`
- `gateway_code` override behavior
- automatic routing behavior when omitted

Do not include:

- admin routes
- router operations internals
- platform-only implementation details

## Testing And Verification

The redesign is complete only when:

- landing matches the acid neo-brutalist system
- auth matches the acid neo-brutalist system
- emails match the acid neo-brutalist system
- merchant and admin match the blueprint ops system
- all signed-in surfaces remain functional
- docs stay hosted via Mintlify
- links and buttons route correctly
- Playwright coverage confirms core guest and signed-in flows
- targeted backend tests still pass where UI work depends on backend contracts

