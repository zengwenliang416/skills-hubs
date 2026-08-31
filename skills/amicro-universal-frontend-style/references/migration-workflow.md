# Migration Workflow

## 1. Inventory before editing

Inspect the explicit target, framework, style entry points, theme mechanism, existing component library, motion dependencies, target page/component, and nearby tests. Use:

```bash
python3 scripts/inspect_frontend.py <target> --format markdown
```

Optional reports must use a target-relative path.

## 2. Preserve contracts

Record behavior, routes, form state, content, component props/events, brand accent, accessibility semantics, and dependency constraints that must not change. Do not replace mature dialog/menu/form primitives merely for visual fidelity.

## 3. Map roles, then components

Map the target's page, surface, stage, text, muted text, border, focus, accent, radius, shadow, and motion roles. Scope them to `.amicro`, `[data-amicro-scope]`, or `[data-amicro-root]`; do not create a competing global design system.

## 4. Pilot the smallest slice

Apply tokens and one representative component. Validate readability, hierarchy, theme inheritance, focus, touch, reduced motion, and branding before broad rollout.

## 5. Add motion by intent

Use one motion idea per component. Put non-essential animation declarations inside `prefers-reduced-motion: no-preference`; preserve immediate state under `reduce`. Prefer CSS for persistent simple states and the target's existing library for sequencing/layout continuity.

## 6. Optional bundled layer

Dry-run, install, update, and uninstall are explicit lifecycle operations:

```bash
python3 scripts/install_style_layer.py <target> --destination src/styles/amicro
python3 scripts/install_style_layer.py <target> --destination src/styles/amicro --apply
python3 scripts/install_style_layer.py <target> --destination src/styles/amicro --update --apply
python3 scripts/install_style_layer.py <target> --destination src/styles/amicro --uninstall --apply
```

The installer records hashes in `.amicro-install.json`. Local drift blocks update/uninstall unless the user explicitly supplies `--force`. All paths must remain inside the target after symlink resolution.

## 7. Static and project verification

Run the target's format, type, lint, unit, integration, and build commands when available, then:

```bash
python3 scripts/generate_token_assets.py <skill-dir>
python3 scripts/verify_amicro_style.py <target> --strict
```

Treat static verification as evidence about source patterns, not rendered quality.

## 8. Rendered matrix

At minimum inspect:

- widths 320, 360, 768, and 1440px; document-level `scrollWidth <= clientWidth`
- light, dark, and system/auto theme where supported
- keyboard focus and exact role/name before and after animated label/icon changes
- pointer and touch behavior, including no hover-only information
- reduced-motion after triggering every relevant interaction; inspect active animations
- RTL when supported
- long labels, loading, success, error, disabled, empty and rapid repeated states
- console/page errors and obvious input latency/layout shift

## 9. Handoff

Report changed files, preserved contracts, dependencies added (normally none), commands actually run, viewport/state/theme checks actually observed, and unresolved caveats. Never convert a static scan into a visual claim.
