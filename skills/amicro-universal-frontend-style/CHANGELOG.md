# Changelog

## 1.1.0 — 2026-08-31

- Reworked the Skill entrypoint to fit the Yao Library context budget and tightened route exclusions.
- Moved Skill IR out of the always-loaded `agents/` directory.
- Added reproducible standard-library tests, trigger-routing evals, and six recorded-fixture Output Lab cases covering file-backed, near-neighbor, and boundary behavior.
- Added npm runtime packaging with explicit file allowlists, Python cache exclusions, and CLI entrypoints.
- Fixed uninstall planning so managed-file symlinks are blocked before path resolution and cannot delete their targets under `--force`.
- Fixed Python 3.11 Markdown rendering compatibility by moving pipe escaping outside the f-string expression.
- Fixed the browser preview copy feedback after asynchronous clipboard access and added an explicit input `id`/`name`.
- Removed references to absent companion archives, browser suites, and generated release reports.
- Preserved missing human review and production telemetry as explicit evidence gaps.

## 1.0.1 — 2026-08-30

- Moved non-essential CSS animation and transition declarations under `prefers-reduced-motion: no-preference` and added an exact emergency stop for reduced motion.
- Fixed 320px horizontal overflow, narrow toolbar/nav wrapping, RTL switch positioning, and logical sizing.
- Reworked text/icon swap examples so each control exposes one accessible name and selection state is reflected with ARIA.
- Enforced target-scoped `--output` paths for inspection and verification, including absolute path, parent traversal, and symlink escape rejection.
- Added safe install/update/uninstall lifecycle with `.amicro-install.json`, hashes, drift detection, atomic writes, dry-run, and explicit force semantics.
- Changed the light muted token to `#6f6f6f` and added semantic contrast checks.
- Made `amicro-tokens.json` the canonical 66-variable source and generated CSS/TypeScript artifacts deterministically.
- Added conservative animation-context verification, deliberately unsafe regression fixtures, and self-scoped React/Vue/Svelte examples.
- Added 19 standard-library unit tests and a 10-check Chromium smoke suite covering 320/360/768/1440px, reduced motion, accessible names, focus, RTL, and console errors.
- Split runtime, source/evidence, and five host-layout adapter distributions.
- Removed unsupported world-class/adoption claims; independent human blind review and production telemetry remain missing evidence.

## 1.0.0 — 2026-08-28

- Rebuilt the repository-local Amicro design notes as a cross-framework Library-mode Skill.
- Added scoped design tokens, primitive components, motion utilities, and machine-readable tokens.
- Added migration guidance for vanilla, React/Next, Vue/Nuxt, Svelte/SvelteKit, Astro, Tailwind, CSS Modules, Sass, and CSS-in-JS.
- Added deterministic frontend inspection, safe asset installation, and static style verification scripts.
- Added runnable preview, framework examples, trigger cases, output cases, tests, attribution, and initial validation artifacts.
