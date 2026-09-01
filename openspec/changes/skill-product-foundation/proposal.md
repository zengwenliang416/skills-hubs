## Why

Skills Hub currently presents a polished catalog shell, but its two Skill
entries do not provide enough decision or usage context and the runtime can only
measure generic site traffic. The first product phase should connect discovery,
evaluation, installation intent, and aggregate maintainer insight without adding
third-party tracking.

## What Changes

- Extend catalog entries with factual descriptions, tags, highlights, use cases,
  install methods, and documentation/source links.
- Expand the shared Skill detail dialog into a complete evaluation and install
  surface used by every entry path.
- Add a fixed, validated first-party Skill event API for detail views, successful
  install-command copies, documentation clicks, and repository clicks.
- Store daily per-IP Skill event aggregates in SQLite and expose only per-Skill
  aggregate metrics.
- Add a Skill engagement panel and represent incomplete npm metrics as partial
  data instead of confirmed zero.
- Preserve existing visitor IP/PV behavior, proxy safety, themes, accessibility,
  and reduced-motion support.

## Capabilities

### New Capabilities

- `skill-product-content`: Catalog-backed Skill evaluation content, install
  methods, documentation/source actions, and complete detail presentation.
- `skill-engagement-analytics`: Validated first-party Skill interaction capture,
  daily IP aggregation, aggregate API output, and engagement visualization.

### Modified Capabilities

- None.

## Impact

- Data: `catalog.json` schema expands and SQLite moves from schema v2 to v3.
- Backend: new catalog allowlist parsing, `POST /api/events`, event aggregates,
  and expanded `GET /api/metrics`.
- Frontend: catalog types/detail UI, an event client, and metrics rendering.
- Documentation: root, web, and server contracts describe the product content,
  analytics events, privacy boundary, and migration.
- Dependencies: no new frontend or backend package is required.
