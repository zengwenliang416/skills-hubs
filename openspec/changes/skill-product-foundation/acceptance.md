# Acceptance Criteria: skill-product-foundation

## User-Visible Criteria

- Every Skill detail shows a description, tags, highlights, use cases, factual
  metadata, supported installation methods, documentation, and source links.
- A successful command copy shows accessible success feedback and records one
  `install_copy` action without delaying the feedback.
- Documentation and source links open even if event reporting fails.
- The metrics section shows per-Skill views, install copies, documentation
  clicks, source clicks, and unique interested visitors.
- If one or more npm packages have unavailable data, the summary states that
  data is partial instead of presenting the missing value as a confirmed zero.
- The dialog remains usable at 320px and in light, dark, auto, keyboard, touch,
  and reduced-motion conditions.

## System Criteria

- `POST /api/events` accepts only the four fixed events and current catalog Skill names.
- Invalid event types, unknown Skills, and unexpected request fields return a
  safe client error while preserving `413`, `415`, or `422` semantics.
- Requests beyond the per-IP or DB write capacity return `429`.
- Raw visitor IPs never appear in API responses.
- Existing visitor endpoints continue to behave as before.
- npm API failure does not prevent first-party metrics or catalog rendering.

## Data Criteria

- Schema v2 upgrades to v3 without deleting `daily_visits`.
- Repeated actions from the same IP, Skill, event type, and UTC date increment
  `event_count` in one row.
- Metrics aggregate total event counts and distinct IPs per Skill.
- Direct mode ignores forged forwarding headers; trusted-proxy mode uses the
  configured CIDR allowlist and removes trusted hops from the right.
- Expired raw IP rows are removed from both visit and Skill event tables.

## Component Criteria

- Both entry paths reuse the same Skill detail component.
- Shared Button, IconButton, Chip, and Amicro motion/token behavior is preserved.
- Event transport is not embedded in low-level visual primitives.

## Verification Surfaces

- Facticity: compare catalog content with each Skill README/SKILL.md.
- Static: TypeScript, ESLint, Prettier, Amicro strict check, Rust fmt and clippy.
- Unit: Rust catalog validation, schema migration, event upsert, and aggregates.
- Redteam: unknown Skill/event, unexpected JSON, forged proxy header.
- E2E: open detail, copy command, click outbound links, query aggregate metrics.
- Sensory: mobile/desktop, themes, focus, scrolling, and reduced motion.

## Unresolved Gaps

- None.
