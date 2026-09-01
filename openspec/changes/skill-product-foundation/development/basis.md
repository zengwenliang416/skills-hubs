# Development Basis: skill-product-foundation

## Requirements Reference

- `openspec/changes/skill-product-foundation/requirements.md`
- `openspec/changes/skill-product-foundation/acceptance.md`
- `openspec/changes/skill-product-foundation/spec-map.json`
- `openspec/changes/skill-product-foundation/component-impact-map.json`
- `openspec/specs/ui-design/design.md`
- `openspec/specs/system-architecture/design.md`
- `openspec/specs/frontend-backend-data-flow/design.md`
- `openspec/specs/component-architecture/design.md`

## Prototype Reference

- `openspec/changes/skill-product-foundation/prototype/data-flow-map.md`
- `openspec/changes/skill-product-foundation/prototype/handoff.md`
- `openspec/changes/skill-product-foundation/prototype/decision.json`

## Handoff Reference

Development is allowed only after the prototype handoff and decision are valid.

## Component Architecture Constraint

Implementation must preserve high cohesion and low coupling. Any duplicated UI,
state, validation, formatting, or domain behavior that meets the extraction rule
must become a shared component, hook, utility, or service.
