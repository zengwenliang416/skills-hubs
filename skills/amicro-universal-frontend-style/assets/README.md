# Bundled Style Assets

These files are opt-in implementation seeds. They are scoped, install no dependency, import no font, perform no global reset, and make no network request.

## Canonical source

`amicro-tokens.json` is the single machine-readable source for all public `--amicro-*` variables. The CSS and TypeScript files are generated from it.

```bash
python3 scripts/generate_token_assets.py .          # read-only parity check
python3 scripts/generate_token_assets.py . --write  # maintainer regeneration
```

## Files

- `amicro-tokens.json` — canonical light/dark/auto token data.
- `amicro-tokens.css` — generated variables under `.amicro`, `[data-amicro-scope]`, or `[data-amicro-root]`.
- `amicro-tokens.ts` — generated dependency-free TypeScript token maps.
- `amicro-primitives.css` — layout, card, stage, button, navigation, form, switch, toast, and metric primitives.
- `amicro-motion.css` — gated hover/press, entrance, icon/text swap, glare, pulse, shake, success, skeleton, and route utilities.
- `amicro-motion-presets.ts` — optional dependency-free timing, easing, spring, reduced-motion, and magnetic-offset helpers.

## Minimal use

```html
<link rel="stylesheet" href="amicro-tokens.css">
<link rel="stylesheet" href="amicro-primitives.css">
<link rel="stylesheet" href="amicro-motion.css">

<main class="amicro" data-amicro-root data-amicro-theme="auto">
  <article class="amicro-card amicro-hover-lift" data-interactive="true">
    <div class="amicro-card__stage">...</div>
    <footer class="amicro-card__footer">...</footer>
  </article>
</main>
```

Override variables at the scope root to preserve the target product's brand.
