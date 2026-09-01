# Requirements: skill-product-foundation

## Summary

Turn the existing catalog showcase into the first working product loop by
adding decision-ready Skill content, a complete detail experience, and
first-party behavior analytics backed by the Rust service.

## Users & Actors

- Visitors evaluating whether a Skill fits their task.
- Visitors copying a supported installation command or opening documentation.
- Repository maintainers reviewing aggregate interest without exposing raw IPs.

## In Scope

- Extend every catalog Skill with a Chinese description, tags, highlights, use
  cases, supported install methods, documentation URL, and repository URL.
- Render the added content in one reusable Skill detail dialog used by both the
  catalog and command palette.
- Report `skill_view`, `install_copy`, `documentation_click`, and
  `repository_click` through one best-effort event client.
- Resolve IP under the existing trusted-proxy policy, validate fixed event names
  and catalog Skill names, and aggregate events by UTC date and IP in SQLite.
- Limit public statistics writes per resolved IP, cap concurrent DB write work,
  and trust forwarding headers only from configured proxy CIDRs.
- Retain raw IP aggregates for a configurable period, defaulting to 90 days.
- Return per-Skill aggregate event totals and unique visitors in `/api/metrics`.
- Show a Skill engagement panel and accurately distinguish partial/unavailable
  npm data from a confirmed zero.

## Out of Scope

- Search-query, referrer, user-agent, geography, device, account, or cookie tracking.
- Authentication, an admin dashboard, third-party analytics, exports, alerts,
  favorites, ratings, comments, or automated recommendations.
- Invented release dates, undocumented installation commands, or registry claims.
- Deployment, publishing, tag creation, or repository commit.

## UI Design Impact

- Foundation spec: `openspec/specs/ui-design/design.md`
- Required UI decisions: widen the existing native dialog, add internally
  scrollable structured content, reuse current tokens/primitives, and retain
  responsive, focus, touch, and reduced-motion behavior.

## Theme & Locale Capability Impact

- Theme support: `system` with light, dark, and auto.
- Theme toggle policy: show the existing toggle; create no new toggle.
- Internationalization: `disabled`.
- Supported locales: `zh-CN`.
- Default locale: `zh-CN`.
- Prototype coverage: light, dark, and auto behavior at mobile and desktop widths.

## Architecture & Database Impact

- Foundation spec: `openspec/specs/system-architecture/design.md`
- Required architecture/database decisions: schema v3 incrementally adds
  `daily_skill_events` without deleting valid v2 visit rows; the backend loads a
  catalog Skill allowlist; APIs expose aggregates only.

## Frontend-Backend Data Flow Impact

- Foundation spec: `openspec/specs/frontend-backend-data-flow/design.md`
- Required data-flow decisions: analytics never block the user action, event
  writes return `204`, invalid values preserve safe Axum rejection status,
  saturation returns `429`, internal failures return generic `500`, and metrics
  refresh returns aggregate engagement.

## Component Architecture Impact

- Foundation spec: `openspec/specs/component-architecture/design.md`
- Cohesion/coupling impact: catalog content stays in the catalog feature, event
  transport is centralized, and shared visual primitives remain analytics-free.
- Shared extraction requirement: one event API helper and one install-method
  rendering path; do not duplicate detail dialogs.

## Unresolved Gaps

- None.
