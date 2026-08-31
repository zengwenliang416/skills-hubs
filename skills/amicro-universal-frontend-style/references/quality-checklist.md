# Quality Checklist

## Scope and preservation

- [ ] Target repository, page/component, framework, theme system, and existing motion stack inspected.
- [ ] Behavior, copy, routes, form state, component APIs, semantics, and brand constraints preserved unless requested otherwise.
- [ ] No unapproved dependency, remote font, network installer, or package-manifest mutation.
- [ ] Amicro tokens/styles are scoped rather than global.

## Design and implementation

- [ ] Page/surface/stage/text/muted/border/focus/accent roles mapped before component styling.
- [ ] One dominant motion idea per component; dense workflows avoid theatrical transitions.
- [ ] `amicro-tokens.json`, generated CSS, and generated TypeScript agree.
- [ ] No `transition: all`, layout-thrashing animation, uncontrolled decorative loop, or blanket `will-change`.

## Accessibility

- [ ] Native semantics and keyboard activation retained.
- [ ] Focus-visible ring is visible and not clipped.
- [ ] Each control exposes one accessible name in every state.
- [ ] Selection/toggle/busy/error/success state has semantic communication independent of motion or color.
- [ ] Non-essential animation declarations live under `prefers-reduced-motion: no-preference`.
- [ ] Muted text, focus, icons, borders, and semantic states pass contrast checks on actual surfaces.

## Rendered verification

- [ ] 320, 360, 768, and 1440px checked; no document-level horizontal overflow.
- [ ] Light, dark, and auto/system theme checked where available.
- [ ] Keyboard, pointer, touch, reduced-motion, and RTL (when supported) checked.
- [ ] Long content, empty, loading, success, error, disabled, rapid repeat, and route interruption states checked as relevant.
- [ ] Console/page errors checked.
- [ ] Claims clearly distinguish static, automated browser, and human visual evidence.

## Safe tooling and release

- [ ] Report paths and installer destinations remain inside the explicit target after symlink resolution.
- [ ] Installer dry-run, install, update, drift rejection, force behavior, and uninstall tested.
- [ ] Runtime ZIP excludes tests/reports/evals; source/evidence and adapters are separate.
- [ ] ZIP paths are safe, checksums match, and links point to files that actually exist.
- [ ] Missing human blind review or production telemetry is labeled `missing evidence`, not inferred.
