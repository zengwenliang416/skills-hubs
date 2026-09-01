# Frontend-Backend Data Flow Spec

## Overview

The frontend renders product content from the build-time catalog and uses
same-origin APIs for first-party visitor, behavior, and npm metrics. Analytics
are non-blocking enhancements; core Skill discovery and outbound navigation
remain usable when analytics fail.

## Flow Index

| Flow ID | Trigger | Entry UI | API/Service | Persistence | User Result |
| --- | --- | --- | --- | --- | --- |
| `FLOW-VISIT` | metrics section mounts | MetricsSection | `POST /api/visits` | `daily_visits` | live metrics render |
| `FLOW-SKILL-VIEW` | Skill detail opens | catalog/palette | `POST /api/events` | `daily_skill_events` | detail opens immediately |
| `FLOW-INSTALL-COPY` | command copy succeeds | Skill detail | `POST /api/events` | `daily_skill_events` | copied feedback |
| `FLOW-DOC-CLICK` | documentation link activates | Skill detail | `POST /api/events` | `daily_skill_events` | documentation opens |
| `FLOW-REPO-CLICK` | source link activates | Skill detail | `POST /api/events` | `daily_skill_events` | repository opens |
| `FLOW-METRICS` | initial/retry metrics load | MetricsSection | `GET /api/metrics` | read aggregates; npm cache | visitor/npm/engagement panels |

## Boundary Contracts

- UI event contract: one fixed event type plus one catalog `skill_name`.
- Client state contract: event reporting has no optimistic counter and does not
  mutate catalog content.
- Request schema: `{ "skill_name": string, "event_type": fixed enum }`.
- Response schema: event writes return `204`; metrics include aggregate
  `skill_engagement`.
- Error schema: `{ "error": string }`.
- Permission contract: public endpoint, strict server allowlist.

## State Ownership

- URL state: section anchors only.
- Local component state: dialog, search, category, copy feedback, metrics status.
- Shared client cache: the initial visit request is deduplicated per page load.
- Server state: npm response cache.
- Database state: visit and behavior daily aggregates including resolved IP.
- Derived state: totals, ranking, chart scales, package and Skill labels.

## Validation Ownership

- Client-side validation: only typed event helpers are exported.
- Server-side validation: enum parsing and known-Skill membership.
- Database constraints: composite keys, fixed event check, positive counters.
- Cross-field rules: every event references a current catalog Skill.
- Error copy source: frontend feature components; backend returns generic safe
  validation/internal messages.

## Error & Empty States

- Empty state: no engagement rows displays a neutral no-activity message.
- Permission denied: not applicable in phase one.
- Validation error: backend preserves safe HTTP `413`, `415`, and `422` status
  semantics; user action continues.
- Network/server error: analytics fail silently for user actions; metrics panel
  provides retry.
- Conflict/stale data: SQLite upsert resolves duplicate daily keys; npm stale
  status is displayed explicitly.

## Loading / Optimistic / Retry Behavior

- Initial loading: metrics skeleton.
- Partial loading: npm items may be unavailable while first-party metrics render.
- Optimistic update: none.
- Retry rule: explicit metrics retry; event reporting is best effort with no retry.
- Cancellation rule: component mount guards prevent stale metrics state writes.
- Idempotency rule: visit request is deduplicated in the frontend; database
  composite keys aggregate repeated actions rather than duplicate rows.

## End-to-End Flow Details

1. A Skill detail opens and renders catalog content immediately.
2. The UI posts `skill_view` with the catalog name.
3. Axum resolves the client IP under the configured proxy policy.
4. Serde validates the event enum and the catalog allowlist validates the Skill.
5. SQLite upserts the daily IP/Skill/event row and increments `event_count`.
6. The endpoint returns `204`; failures do not close or alter the detail.
7. Successful copy and outbound-link activations use the same path with their
   corresponding fixed event types.
8. `GET /api/metrics` aggregates event counts and distinct visitor IPs by Skill.
9. The frontend maps aggregates to known catalog titles and renders engagement.
10. No raw IP or per-visitor row is returned or logged by the feature.
11. Rollback: failed analytics writes have no UI rollback because no optimistic
    state is applied; database transactions leave the prior aggregate unchanged.

## Async / Realtime Flows

- Queue/event source: none.
- Subscriber: none.
- Retry/dead-letter behavior: none.
- Realtime update channel: none; refresh or retry reloads aggregates.
- Consistency expectation: SQLite writes are immediately visible to subsequent
  metrics requests in the same process.

## Flow Do's and Don'ts

- Do make analytics best effort and interaction-preserving.
- Do reject arbitrary names and payload fields.
- Do distinguish unavailable npm data from real zero.
- Don't collect search text, referrer, user agent, or arbitrary metadata in phase one.
- Don't expose raw IP data to the browser.
