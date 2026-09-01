# Data Flow Prototype: Skill Product Foundation

## Primary Event Flow

1. User action: visitor opens a Skill detail, copies a supported install command,
   or opens documentation/source.
2. UI state transition: the dialog, copy confirmation, or outbound navigation
   completes immediately. Analytics is not awaited.
3. Request payload: the centralized event client sends only
   `{"skill_name":"<catalog name>","event_type":"<fixed enum>"}` with
   `keepalive: true`.
4. Backend validation: Axum enforces the 1 KiB body limit, JSON content type and
   shape, closed event enum, catalog Skill allowlist, resolved-IP rate limit, and
   shared database blocking-work capacity.
5. Database effect: SQLite upserts one row keyed by UTC date, resolved IP, Skill
   name, and event type; repeated actions increment `event_count`.
6. Response: accepted writes return `204`; capacity exhaustion returns `429`;
   invalid requests preserve safe `413`, `415`, or `422` semantics; unexpected
   failures return a generic `500`.
7. UI result: success and failure produce no analytics-specific UI state and do
   not cancel the primary user action.
8. Privacy/operations signal: raw IP remains only in server-side daily aggregate
   rows, expires after the configured retention period, and never appears in an
   API response.

## Visit And Metrics Flow

1. The frontend posts `/api/visits`; the backend resolves the client IP with the
   same trusted-proxy policy and upserts the daily visit row.
2. `/api/metrics` reads visit and Skill aggregates under the shared database
   work limit while npm requests run independently per package.
3. The response always includes one engagement row per catalog Skill.
4. Missing npm package data remains unavailable or stale and makes the UI label
   totals as partial; it is never converted to a confirmed zero.
5. `/api/healthz` reports whether the last retention run succeeded without
   exposing IPs, database contents, or upstream credentials.

## Trust Boundaries

- Direct clients cannot influence the resolved IP with forwarding headers.
- Only peers inside configured proxy CIDRs may supply `Forwarded`,
  `X-Forwarded-For`, or `X-Real-IP`; trusted hops are removed from the right.
- IPv4-mapped IPv6 addresses normalize to IPv4. Native IPv6 rate-limit keys are
  grouped by `/64` to bound trivial address rotation.
- Catalog names are the only accepted analytics identifiers. Arbitrary
  metadata, timestamps, referrers, user agents, search terms, and cookies are
  rejected or not collected.

## Component Boundaries

- `catalog.json` is the public content and Skill allowlist authority.
- The shared Skill detail owns presentation and invokes one event client.
- Low-level visual primitives remain analytics-free.
- Axum handlers own transport validation and capacity handling.
- `Store` owns schema migration, upserts, retention, and aggregate queries.
- `NpmDownloads` owns per-package cache, negative cache, and singleflight.

## Review Focus

- Loading behavior: metrics keep the existing loading surface; event writes do
  not add loading state.
- Empty behavior: every catalog Skill renders a zero-filled engagement row.
- Error behavior: first-party metrics survive npm failure; event failure is
  intentionally silent to the visitor; retention failure degrades health.
- Permission behavior: not applicable because this public phase has no account
  or admin surface.
- Retry behavior: the UI does not retry events; npm uses bounded cache and
  per-package singleflight; retention retries on the next scheduled run.
