# Prototype Handoff: skill-product-foundation

Approval basis: the user explicitly instructed the team on 2026-09-01 to start
the first phase after requesting a Rust backend, IP persistence and
deduplication, visitor metrics, and npm download metrics.

## Approved Branch Variant

- Branch: `data-flow`
- Variant: first-party daily IP aggregate with best-effort client events.

## Screens Or Flows

- Shared Skill detail open, install command copy, documentation navigation, and
  repository navigation.
- Visit recording, event validation, daily IP aggregation, metrics aggregation,
  npm availability, and retention health reporting.

## Components To Create

- Centralized frontend event transport helper.
- Typed Skill engagement metrics panel.
- Rust event handler, bounded database work helper, retention health state, and
  health endpoint.

## Components To Reuse

- Existing shared Skill detail dialog, Button, IconButton, Chip, theme tokens,
  motion rules, catalog loader, metrics section, Axum router, and SQLite Store.

## Extraction Targets

- One install-method rendering path shared by all detail entry points.
- One event reporting utility used by detail views, copies, and outbound links.
- One database semaphore shared by read, write, and retention blocking work.

## API Contracts

- `POST /api/events` accepts only `skill_name` and one of four fixed
  `event_type` values and returns `204` on success.
- Invalid payloads preserve safe `413`, `415`, or `422`; capacity exhaustion
  returns `429`; unexpected failures return a generic `500`.
- `GET /api/metrics` returns visit totals, seven UTC days, npm availability,
  and one aggregate engagement row per catalog Skill.
- `GET /api/healthz` returns service and retention status without raw IP data.

## Data Flows

- The UI completes the primary action, then sends a non-blocking event request.
- The server resolves IP only through configured trusted proxies, applies the
  IP limiter and shared database capacity, and upserts a UTC daily aggregate.
- Metrics read aggregate SQLite values and fetch npm data with independent
  per-package cache and singleflight behavior.
- Startup and scheduled retention remove expired visit and Skill-event IP rows.

## State Behavior

- Loading: metrics use the existing loading surface; events add no loading UI.
- Empty: every catalog Skill receives a zero-filled engagement row.
- Error: event failure does not block the user; npm failure produces partial
  status; retention failure degrades health and writes a diagnostic.
- Disabled: analytics introduces no disabled primary actions.
- Permission: not applicable because the first phase is public and unauthenticated.

## Theme And Locale Policy

- Theme support: system-aware light and dark presentation.
- Theme modes shown in prototype: not visualized by the data-flow branch; the
  production UI must retain light, dark, and system behavior.
- Theme toggle: reuse the existing toggle; create no new toggle.
- Internationalization: disabled; the product copy is Simplified Chinese.
- Locales shown in prototype: none because this is a non-visual data-flow branch.
- Locale switcher: intentionally omitted.

## Out Of Scope Items

- Accounts, admin UI, analytics export, alerts, ratings, favorites, comments,
  recommendations, search tracking, referrers, user agents, devices, geography,
  cookies, deployment, publishing, tags, commits, and production cutover.

## Required Tests

- Rust format, unit tests, Clippy, schema migration, event validation,
  aggregation, proxy parsing, limiter capacity, retention health, and API E2E.
- Frontend typecheck, ESLint, Prettier, production build, Amicro strict check,
  shared-dialog behavior, partial npm rendering, responsive layout, themes,
  keyboard, touch, and reduced motion.
- OpenSpec and SpecNav owning contracts for development and verification.

## Open Risks

- Public event totals remain directional because accepted requests can be
  automated within the bounded limits.
- Raw IP daily aggregates require deployment access controls, retention
  monitoring, and careful backup handling.
- A future catalog Skill rename requires a deliberate analytics history decision.
- npm availability depends on an external service and must remain non-blocking.
