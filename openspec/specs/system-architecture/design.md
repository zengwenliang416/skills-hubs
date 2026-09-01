# System Architecture & Database Spec

## Overview

Skills Hub is a repository-backed catalog with a Vite/React frontend and a
Rust/Axum/SQLite runtime service. The root `catalog.json` is the build-time
product-content source and supplies the backend allowlist for npm metrics and
Skill behavior events.

## Application Topology

- Frontend runtime: React 18 single-page application built by Vite.
- Backend runtime: one Tokio/Axum process.
- API gateway or edge layer: optional trusted reverse proxy CIDR allowlist;
  empty by default.
- Background workers: none.
- External services: npm downloads API.
- Local development entrypoints: Vite on `127.0.0.1:5173`, Axum on
  `127.0.0.1:8080`.
- Production deployment shape: Axum serves `web/dist` and same-origin `/api`.

## Module Boundaries

- Responsibility: each feature or backend module owns one domain concern.
- Public contract: typed React props/helpers or Rust functions and HTTP schemas.
- Owned data: catalog view models, metrics response state, SQLite aggregates, or
  npm cache according to the module list below.
- UI modules: page sections and reusable controls under `web/src`.
- Catalog domain: catalog types, derived categories, Skill cards, details, and
  event client under `web/src/features/catalog`.
- Metrics domain: visitor, npm, and Skill engagement rendering under
  `web/src/features/metrics`.
- Backend HTTP application: routing, proxy/IP resolution, and response mapping
  in `server/src/main.rs`.
- Backend persistence: SQLite schema and aggregate queries in
  `server/src/store.rs`.
- Backend integrations: npm HTTP client/cache in `server/src/npm.rs`.
- Catalog validation: backend catalog parsing and known-Skill allowlist.
- Forbidden dependencies: presentational components do not call SQLite or npm;
  storage does not know frontend component structure.
- Extension points: catalog fields, fixed behavior-event enum, aggregate metrics.

## Frontend Architecture

- Routing: hash anchors and local dialog state; no route library.
- Rendering mode: client-rendered SPA from build-time catalog JSON.
- State management: local React state and the existing Theme context.
- Form handling: controlled search inputs.
- Data fetching: small typed `fetch` clients under feature folders.
- Error handling: feature-local loading, unavailable, and retry states.
- Design system source: scoped Amicro tokens plus repository primitives.

## Backend Architecture

- API style: same-origin JSON HTTP endpoints.
- Request validation: serde schema, fixed event enum, catalog Skill allowlist.
- Auth/session model: public, unauthenticated read and event endpoints.
- Domain service boundaries: visitor storage, behavior storage, npm integration.
- Background jobs: none; npm cache refreshes on demand.
- File/object storage: none.
- Observability: process startup/errors plus aggregate API results; raw IP is
  never returned.

## API Surface

| Route or RPC | Owner | Input | Output | Auth | Side Effects |
| --- | --- | --- | --- | --- | --- |
| `POST /api/visits` | HTTP/store | no body; peer/proxy IP | `MetricsResponse` | public | upsert daily visit and PV |
| `GET /api/metrics` | HTTP/store/npm | none | `MetricsResponse` | public | may refresh npm cache |
| `POST /api/events` | HTTP/store | `{skill_name,event_type}` plus resolved IP | `204` or error JSON | public | upsert daily Skill event |

## Database Model

| Entity | Purpose | Owner | Fields | Relationships | Indexes | Constraints | Lifecycle | Migration | Retention/Deletion |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `daily_visits` | daily UV/PV | store | `visit_date`, `visitor_ip`, `page_views` | none | PK date+IP, IP index | positive PV | upsert per visit | schema v2 retained | deployment-controlled |
| `daily_skill_events` | per-Skill behavior totals and unique actors | store | `event_date`, `visitor_ip`, `skill_name`, `event_type`, `event_count` | logical Skill name to catalog | PK date+IP+Skill+type, Skill/type index | fixed event values, positive count | upsert per action | introduced in schema v3 | deployment-controlled |

## Permissions & Security

- User roles: none; public catalog site.
- Permission checks: no privileged endpoint in phase one.
- Data isolation: database remains server-side and Git-ignored.
- Secret handling: no credentials in catalog, database responses, or frontend.
- Audit logging: behavior aggregates are analytics, not security audit records.
- Abuse cases: forged proxy headers, unknown Skill names, unknown event types,
  oversized or unexpected JSON, and write flooding. Trusted proxy CIDRs,
  per-IP fixed-window limits, DB write permits, and server validation constrain
  these paths.

## Integration Boundaries

- Third-party APIs: npm downloads point API with timeout and in-memory cache.
- Webhooks, queues, email/SMS/push, payments: none.
- Analytics: first-party SQLite only; no third-party tracker.

## Operational Constraints

- Performance constraints: SQLite writes are short blocking tasks moved off the
  async executor; aggregate queries cover small tables.
- Availability expectations: npm failure degrades only npm data; catalog and
  first-party metrics remain available.
- Migration rules: incremental schema versions preserve valid IP visit data.
- Backup/restore: copy the SQLite database while respecting WAL sidecars or use
  SQLite backup tooling.
- Feature flag rules: trusted proxy CIDRs, write limits, DB concurrency, and IP
  retention are environment-controlled.
- Rollback constraints: binaries older than schema v3 must not open a v3 database.

## Architecture Do's and Don'ts

- Do validate events against fixed enums and catalog names.
- Do expose only aggregates, never raw visitor IPs.
- Do keep npm failure independent from first-party analytics.
- Don't add auth, an admin panel, third-party analytics, or a job system in this phase.
- Don't accept arbitrary event names or metadata.
