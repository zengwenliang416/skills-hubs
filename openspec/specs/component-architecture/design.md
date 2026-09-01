# Component Architecture & Reuse Spec

## Overview

Skills Hub organizes React code by feature and keeps Rust HTTP, persistence, and
external integrations separate. Phase-one product work extends these boundaries
without introducing a new shared framework.

## Component Taxonomy

- Page/screen components: `App`.
- Layout components: Header, Hero, Footer and section components.
- Domain components: SkillCard, SkillDetailDialog, FeaturedSection,
  MetricsSection, CommandPalette.
- Form components: catalog and command-palette search inputs.
- Data display components: StageCard, CountUp, metrics cards and charts.
- Feedback components: loading skeletons, empty/error panels, copy feedback.
- Headless hooks: theme/media/viewport/motion hooks under `web/src/lib`.
- Domain utilities/services: catalog derivation and feature API clients.

## Cohesion Rules

- Catalog content rendering belongs to the catalog feature.
- Behavior event transport belongs to a catalog analytics client, not to Button
  or IconButton.
- Metrics aggregation rendering belongs to the metrics feature.
- HTTP validation, IP resolution, persistence, and npm integration remain
  separate backend responsibilities.

## Coupling Rules

- Sections may compose feature components.
- Shared primitives must not import catalog or metrics features.
- Catalog components may consume catalog types and analytics helpers.
- Metrics components may map aggregate Skill names to catalog display titles.
- Backend storage must not parse frontend component state.

## Shared Component Extraction Rules

- Extract install-method rendering when more than one method shares copy/status behavior.
- Keep the expanded Skill detail as one domain component until independent reuse
  or multiple responsibilities justify smaller catalog-local components.
- Extract event request code because four interactions share one transport and schema.
- Do not create repository-wide abstractions for only one backend query.

## Component Public API Rules

- Props describe user behavior, such as `onOpen` and `onClose`.
- Skill components receive the typed catalog Skill, not raw JSON fragments.
- Event helpers accept only the fixed event union and a Skill name.
- Shared controls do not know analytics event names.

## State Ownership Rules

- Local state: filters, dialogs, active command result, copy feedback.
- Shared UI state: theme only.
- Server/cache state: metrics response and npm cache.
- Form state: local controlled inputs.
- URL state: anchors only.
- Derived state: filtered Skills, category counts, aggregate ranking and labels.

## Composition Patterns

- Preferred composition patterns: feature sections composed by App; domain
  components composed from repository primitives; small feature-local helpers.
- Forbidden composition patterns: API calls in shared visual primitives,
  database-shaped props, global event bus, duplicate dialogs for each entry path.
- Approved provider/context boundaries: ThemeProvider.
- Approved headless hook patterns: capability/media/viewport hooks without domain I/O.

## File & Naming Conventions

- Component file naming: PascalCase component plus matching CSS Module.
- Hook naming: `useX`.
- Test naming: Rust inline `#[cfg(test)]`; frontend tests are feature-local if a
  test runner is introduced.
- Story/prototype naming: no story runtime in phase one.
- Barrel/export rules: direct imports; no new barrels.

## Testing Expectations

- Shared component tests: preserve existing lint, type, and accessibility rules.
- Hook tests: required only for new stateful reusable hooks.
- Integration tests: Rust storage tests cover migration, validation aggregates,
  unique visitors, and event counts.
- Accessibility checks: dialog semantics, link names, copy feedback, focus, and
  narrow-screen scrolling.
- Visual/prototype review: light/dark/auto at mobile and desktop widths.

## Refactor Triggers

- Duplicate logic detected: extract within the owning feature.
- Cross-boundary import detected: move transport/domain logic out of primitives.
- Props become data-source-specific: introduce a feature view model.
- Component grows multiple responsibilities: split rendering groups locally.
- Test setup requires unrelated modules: reduce coupling before expanding setup.

## Component Do's and Don'ts

- Do keep event transport best effort and centralized.
- Do reuse existing Button, IconButton, Chip, and dialog behavior.
- Do keep typed catalog fields aligned with `catalog.json`.
- Don't add a router, state library, UI library, or analytics SDK.
- Don't duplicate Skill detail implementations between catalog and command palette.
