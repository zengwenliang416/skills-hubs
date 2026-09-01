# Task Brief: 001-product-foundation

## Goal

Visitors can evaluate and install a Skill while first-party visit and engagement
metrics are recorded and rendered without exposing raw IPs.

## Parent Artifacts

- `openspec/changes/skill-product-foundation/requirements.md`
- `openspec/changes/skill-product-foundation/acceptance.md`
- `openspec/changes/skill-product-foundation/prototype/handoff.md`

## Vertical Slice

Extend factual catalog content, render it in the shared detail dialog, report
four best-effort actions, persist daily IP aggregates in Rust/SQLite, and show
stable per-Skill metrics with truthful npm availability.

## In Scope

- Existing task items `1.1` through `5.2`.
- Catalog schema/content, shared Skill detail, analytics client, metrics UI,
  Axum APIs, trusted proxy handling, rate/capacity limits, SQLite schema v3,
  retention health, documentation, tests, and local runtime verification.

## Out Of Scope

- Skills runtime content, generated data/build output, authentication, admin
  tools, arbitrary tracking metadata, deployment, publishing, tags, commits,
  and production cutover.

## Files Allowed

- `catalog.json`, `README.md`, `.gitignore`, `server/**`, and `web/**`.

## Interfaces / Seams

- `catalog.json` is the content and Skill allowlist authority.
- The frontend event client owns transport; the shared detail owns invocation.
- Axum handlers own request semantics and bounded blocking work.
- `Store` owns migration, retention, upsert, and aggregate queries.
- `NpmDownloads` owns cache and per-package singleflight.

## Components To Create

- Event API helper, engagement panel, retention health state, and health route.

## Components To Reuse

- Shared Skill detail, existing controls/tokens/motion, catalog loader, metrics
  section, Axum router, and SQLite Store.

## Components To Extract

- One event transport helper and one install-method rendering path.
- One semaphore path for all database blocking work.

## API / Data Flow Contracts

- Event requests contain only a catalog Skill name and fixed event enum.
- Successful writes return `204`; safe request errors preserve
  `413/415/422`; saturation returns `429`; internal failures return generic
  `500`.
- Metrics return aggregates only and retain a zero row for every catalog Skill.
- npm failures remain partial/unavailable and never block first-party metrics.

## State / Error / Empty / Loading Behavior

- Loading: metrics reuse the existing loading surface; events add no loading UI.
- Empty: every catalog Skill renders a zero-filled engagement row.
- Error: event failure is silent to the primary action; npm failure is partial;
  retention failure degrades health.
- Disabled: analytics never disables copy or outbound navigation.
- Permission: not applicable for the public unauthenticated phase.

## TDD Requirement

- Write or update focused behavior tests before or alongside implementation.

## Verification Commands

- `cargo fmt --manifest-path server/Cargo.toml --check`
- `cargo test --manifest-path server/Cargo.toml`
- `cargo clippy --manifest-path server/Cargo.toml --all-targets -- -D warnings`
- `npm run test`, `npm run typecheck`, `npm run lint`, `npm run format:check`, and
  `npm run build` from `web/`.
- Amicro strict validation, OpenSpec/SpecNav contracts, and local API E2E.

## Stop Conditions

- Scope lock mismatch.
- Missing product, architecture, data-flow, or component decision.
- Component duplication that should be extracted.

## Unsafe Assumptions

- Proxy headers are not trusted unless the peer matches configured CIDRs.
- Missing npm values are not zero.
- Raw IPs are private server-side retention data and never API output.
