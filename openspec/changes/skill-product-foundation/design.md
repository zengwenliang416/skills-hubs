## Context

The current site imports a small root catalog at build time, displays metadata in
one shared native dialog, and reads visitor/npm metrics from a Rust service.
SQLite schema v2 stores daily IP/PV aggregates. The change crosses catalog
content, React UI, API validation, persistence, aggregation, privacy, and schema
migration while retaining the existing no-auth public topology.

## Goals / Non-Goals

**Goals:**

- Make each Skill detail sufficient for initial evaluation and installation.
- Capture four high-value product actions with a fixed first-party event schema.
- Preserve raw IP only in server-side daily aggregate rows and expose aggregates.
- Upgrade existing schema v2 databases without losing visitor data.
- Keep analytics best effort so it never blocks the primary interaction.

**Non-Goals:**

- General-purpose analytics, arbitrary event metadata, search-query tracking, or
  visitor profiling.
- Accounts, administration, data export, alerting, recommendations, or realtime updates.
- New UI, state, routing, analytics, or database dependencies.

## Decisions

1. **Catalog remains the content authority.** The root JSON gains typed fields
   instead of fetching or parsing Markdown at runtime. This keeps builds
   deterministic and lets maintainers review public copy explicitly. Runtime
   Markdown rendering was rejected because it adds parsing/sanitization and
   makes presentation depend on documentation structure.

2. **Events use a closed enum and known-Skill allowlist.** Requests contain only
   `skill_name` and `event_type`; Axum resolves IP separately. Arbitrary event
   names/metadata were rejected because they weaken privacy and validation.

3. **SQLite stores daily IP aggregates.** The primary key is UTC
   date+IP+Skill+event and repeated actions increment `event_count`. Raw event
   rows were rejected because they provide unnecessary timestamp-level tracking.

4. **Schema v3 migrates incrementally.** v2 retains `daily_visits` and adds the
   event table; legacy v0/v1 still rebuilds the incompatible UUID visit schema.
   A blanket rebuild was rejected because it would discard valid IP visit data.

5. **Event reporting is fire-and-forget from the UI.** Dialogs, copy feedback,
   and outbound navigation proceed without awaiting analytics. Optimistic metric
   updates and retries were rejected because they introduce state drift and may
   double count.

6. **Metrics return a stable row for every catalog Skill.** Skills without
   events receive zeros, allowing deterministic rendering. npm availability is
   summarized separately so a missing item is not folded into a confirmed zero.

7. **Public writes have bounded capacity.** A per-IP fixed window limits write
   volume and a Tokio semaphore prevents unbounded blocking work. Trusted proxy
   CIDRs are explicit and proxy chains are peeled from the right.

8. **Raw IP aggregates expire.** The default retention is 90 days, enforced at
   startup and every 24 hours. npm failures use a short negative cache and
   singleflight to prevent upstream amplification.

## Risks / Trade-offs

- [Public event API can be inflated] -> constrain values, aggregate by daily IP,
  and state clearly that metrics are directional rather than audited billing data.
- [Raw IP is personal data] -> keep it server-side, Git-ignore the database,
  collect no extra metadata, and document deployment retention obligations.
- [UTC day differs from visitor local day] -> retain the existing UTC contract
  for consistency and label it in the UI.
- [A catalog Skill rename splits history] -> treat `name` as the stable analytics
  identifier and require deliberate migration for future renames.
- [Outbound analytics can be lost during page navigation] -> use `keepalive`
  requests but never block the link.

## Migration Plan

1. Stop the v2 server and back up the SQLite database if production data exists.
2. Start the v3 binary; it creates `daily_skill_events` and sets user version 3
   while preserving `daily_visits`.
3. Build and serve the expanded frontend.
4. Verify visit behavior, each event type, aggregate metrics, and proxy handling.
5. Rollback requires restoring the pre-v3 database backup because v2 rejects a
   newer schema version.

## Open Questions

- None for this phase.
