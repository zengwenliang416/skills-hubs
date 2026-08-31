---
name: amicro-universal-frontend-style
description: Apply or port the Amicro-inspired visual language, scoped design tokens, component surfaces, and restrained micro-transitions to an existing frontend. Use for React, Next.js, Vue, Nuxt, Svelte, Astro, Tailwind, CSS Modules, CSS-in-JS, or vanilla HTML/CSS/JS when the user asks for Amicro styling, tactile motion, a style migration, or an implementation audit. Preserve product behavior, content, component APIs, accessibility, branding, and the target stack. Exclude backend work, generic brand identity design, install-only support, visual critique without implementation, and verbatim cloning of Amicro product content.
---

# Amicro Universal Frontend Style

Apply Amicro as an adaptable style grammar, not a product clone.

## Contract

- Preserve behavior, semantics, content, component APIs, and brand constraints unless explicitly changed.
- Reuse the target stack and existing design system. New dependencies require approval.
- Scope all tokens and styles; inspect before writing and patch narrowly.
- Keep essential behavior available to keyboard, pointer, and touch users without relying on hover.
- Put non-essential animation inside `prefers-reduced-motion: no-preference`.
- Never claim visual verification from static scanning.

## Exclusions

Do not use this Skill for backend work, installation-only support, generic visual critique, general accessibility audits that do not request Amicro adaptation, broad brand identity work, one-off animation snippets, summaries, or verbatim product cloning.

## Workflow

1. Identify the target slice, framework, style entrypoint, theme model, existing motion library, checks, and contracts to preserve.
2. Inventory the target before editing:
   ```bash
   python3 scripts/inspect_frontend.py <target> --format markdown
   ```
3. Read `references/design-language.md` and `references/migration-workflow.md`. Add motion or framework references only when needed.
4. Pilot the smallest useful layer: token roles, surfaces, geometry, focus, component states, then optional motion.
5. Run the target project's format, type, lint, test, and build commands, followed by:
   ```bash
   python3 scripts/verify_amicro_style.py <target> --strict
   ```
6. Render relevant states at 320, 360, 768, and 1440px. Check focus, touch, exact accessible names, themes, reduced motion, clipping, overflow, RTL when relevant, and runtime errors.
7. Report changed files, preserved contracts, checks actually run, rendered states actually inspected, and unresolved caveats.

## Optional Style Layer

Dry-run is the default. Writes require `--apply` and remain inside the explicit target:

```bash
python3 scripts/install_style_layer.py <target> --destination src/styles/amicro
python3 scripts/install_style_layer.py <target> --destination src/styles/amicro --apply
python3 scripts/install_style_layer.py <target> --destination src/styles/amicro --update --apply
python3 scripts/install_style_layer.py <target> --destination src/styles/amicro --uninstall --apply
```

## Output Contract

Return working target-native files, a concise compatibility summary, commands actually run, rendered evidence actually inspected, and explicit remaining risks. The bundled `assets/` are optional seeds, not mandatory global CSS.

Routing evidence and packaging expectations live in `evals/`; they are maintenance inputs, not runtime instructions.
