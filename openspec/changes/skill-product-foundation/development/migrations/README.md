# Development Migrations: skill-product-foundation

## Execution Order

1. Back up the production SQLite database and its WAL/SHM sidecars while the
   old service is stopped.
2. Apply `001-schema-v3.sql`, or start the Rust service and allow `Store` to
   perform the equivalent guarded migration.
3. Verify `PRAGMA user_version` is `3`, `daily_visits` rows remain present, and
   `daily_skill_events` accepts only the four fixed event names.

## Validation

- Run both in-memory commands listed in `manifest.json`.
- Run `cargo test --manifest-path server/Cargo.toml`; the Store tests cover v2
  preservation, legacy UUID repair, event upsert/aggregation, and retention.
- Before production use, compare visitor totals before and after startup and
  query `PRAGMA integrity_check`.

## Rollback

- Preferred production rollback is restoring the pre-v3 backup because older
  binaries reject schema version `3`.
- `001-schema-v3-rollback.sql` is an explicit destructive fallback that drops
  Skill event aggregates, preserves `daily_visits`, and resets the version to
  `2`; use it only when losing first-phase event data is acceptable.
