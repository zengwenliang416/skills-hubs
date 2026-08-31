# Amicro Design Language

Use this reference to translate the visual grammar into the target product. Values are starting points, not a command to erase an existing design system.

## 1. Core Character

Amicro's visual language is quiet, tactile, and stage-like:

1. **Low-noise canvas** — near-white or near-black page backgrounds with restrained contrast.
2. **Nested surfaces** — a large card contains a slightly smaller inset stage, creating depth without heavy shadows.
3. **Generous geometry** — large outer radii, smaller inner radii, pill controls, and compact iconography.
4. **Compact typography** — medium weights, tight tracking, short labels, and muted supporting text.
5. **Purposeful state change** — motion explains hover, press, swap, success, or navigation rather than decorating every element.
6. **One product accent** — neutral surfaces dominate; the target brand's accent identifies action or status.

## 2. Canonical Token Roles

The bundled `assets/amicro-tokens.css` is scoped and safe to copy. Map existing product tokens to these roles instead of duplicating colors when possible.

### Dark theme

| Role | Starting value | Use |
| --- | --- | --- |
| page | `#121212` | app/page canvas |
| surface | `#181818` | cards and panels |
| surface hover | `#202020` | hover or selected neutral surface |
| stage | `#131313` | inset demo/content area |
| text | `#f5f5f5` | primary content |
| muted text | `#767676` | captions and secondary labels |
| border | `rgba(255,255,255,.06)` | quiet boundaries |
| border strong | `rgba(255,255,255,.12)` | focus-adjacent or selected boundaries |
| glass | `rgba(20,20,20,.75)` | floating glass panel before blur |

### Light theme

| Role | Starting value | Use |
| --- | --- | --- |
| page | `#f8f9fa` | app/page canvas |
| surface | `#ffffff` | cards and panels |
| surface hover | `#f1f1f3` | hover or selected neutral surface |
| stage | `#f4f4f6` | inset demo/content area |
| text | `#111111` | primary content |
| muted text | `#767676` | captions and secondary labels |
| border | `rgba(17,17,17,.08)` | quiet boundaries |
| border strong | `rgba(17,17,17,.16)` | selected boundaries |
| glass | `rgba(255,255,255,.75)` | floating glass panel before blur |

### Semantic extension

Keep the target's existing semantic colors. Only provide fallbacks when none exist:

- `--amicro-accent`: target product accent; neutral black/white is acceptable for monochrome products.
- `--amicro-success`: success confirmation.
- `--amicro-warning`: warning state.
- `--amicro-danger`: destructive or error state.
- `--amicro-focus`: visible focus ring; may reuse the product accent.

Do not communicate status with color alone.

## 3. Typography

### Family

Preferred: `Outfit`, with a local/system fallback chain. Do not import a remote font without considering privacy, performance, CSP, and the target's existing brand font.

```css
font-family: "Outfit", Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
```

When the target already has a strong type system, preserve it and borrow only the compact hierarchy.

### Weights and tracking

| Role | Weight | Tracking | Typical size |
| --- | ---: | ---: | ---: |
| page title | 600 | `-0.035em` | `clamp(2rem, 5vw, 4.5rem)` |
| section title | 600 | `-0.025em` | `1.5rem–2.25rem` |
| card title | 500–600 | `-0.02em` | `0.95rem–1.125rem` |
| body | 400 | `-0.01em` | `0.875rem–1rem` |
| control label | 500 | `-0.015em` | `0.8125rem–0.875rem` |
| metadata | 400–500 | `0` | `0.75rem–0.8125rem` |

Avoid large blocks of very light text on low-contrast surfaces. Muted text still needs readable contrast.

## 4. Geometry

### Radius ladder

- small detail: `8px`
- control/input: `10–12px`
- inset stage: `14px`
- panel: `18–20px`
- signature card: `24px`
- pill: `999px`

Use a clear nested relationship: outer radius larger than inner radius by roughly `6–10px`.

### Reference card proportion

The upstream design notes use a `320 × 268` card with `24px` outer radius and a stage inset by `12px` with `14px` radius. Treat that as a visual rhythm, not a fixed production size:

```css
.amicro-card {
  inline-size: min(100%, 20rem);
  min-block-size: 16.75rem;
}
```

For content-heavy products, let height grow. Never clip real content just to preserve the reference ratio.

### Spacing ladder

Use a compact eight-point-biased ladder:

`4, 8, 12, 16, 20, 24, 32, 40, 48, 64, 80, 96px`

Common patterns:

- card inset: `12px`
- card footer: `14–16px`
- control horizontal padding: `14–18px`
- page gutter: `clamp(16px, 4vw, 48px)`
- section gap: `clamp(48px, 8vw, 96px)`

## 5. Surface Hierarchy

Use contrast in this order:

1. page canvas
2. card/panel surface
3. inset stage
4. hover/selected surface
5. border or ring
6. shadow only when spatial separation still needs help

Dark mode should not be a stack of identical near-black rectangles. Use small luminance differences and quiet borders. Light mode should avoid pure gray-on-gray mud; keep main cards white and stage areas slightly tinted.

### Shadows

Use broad, low-opacity shadows:

```css
box-shadow:
  0 1px 2px rgb(0 0 0 / .05),
  0 18px 50px rgb(0 0 0 / .08);
```

Dark surfaces often need border contrast more than a black shadow.

### Glass

Use glass only for floating navigation, transient overlays, or control docks:

```css
background: var(--amicro-glass);
backdrop-filter: blur(16px);
border: 1px solid var(--amicro-border);
```

Provide an opaque fallback and avoid stacking multiple blurred layers.

## 6. Layout Patterns

### Card grid

```css
display: grid;
grid-template-columns: repeat(auto-fit, minmax(min(100%, 17rem), 1fr));
gap: clamp(1rem, 2vw, 1.5rem);
```

### Stage card anatomy

1. outer card surface
2. inset stage for interaction or visualization
3. footer with title/metadata/action
4. optional quiet status chip

Keep the interactive stage visually dominant. Footer copy should be short.

### Navigation

Use a compact pill or rounded rail with one moving/filled active state. Active state should remain clear without motion.

### Forms

Group label, control, hint/error, and feedback. Inputs use restrained surfaces and visible focus; errors should not rely only on a shake animation.

## 7. Iconography

- Prefer simple line icons with consistent stroke.
- Typical size: `14–18px`; major actions may use `20px`.
- Keep icon and label gaps around `6–8px`.
- An icon swap should preserve button width unless expansion communicates a deliberate success state.
- Do not use decorative icons as the only accessible label.

## 8. Responsive Translation

- Preserve surface hierarchy at every width; do not simply scale the desktop card down.
- Collapse multi-column card grids before text or controls become cramped.
- Disable or simplify perspective/magnetic effects on coarse pointers.
- Ensure page transitions do not trap scroll or hide the route's accessible name.
- Test long translated labels and dynamic text expansion.

## 9. Visual Decision Rules

Use Amicro literally when the page is a showcase, portfolio, creative tool, or interaction demo. Adapt more conservatively for dashboards, commerce, admin, healthcare, finance, or dense enterprise workflows.

When in doubt:

- preserve the product's information architecture
- keep its accent and semantic colors
- borrow nested surfaces and geometry
- add one purposeful state transition
- stop before the interface becomes theatrical

## 10. Anti-Patterns

- applying `24px` radius to every element
- pure black and pure white everywhere with no surface hierarchy
- blur on every floating element
- tiny muted text below readable contrast
- hover-only actions
- simultaneous scale, rotate, blur, glow, and color morph on one control
- fixed card heights that clip real content
- replacing a mature token system with isolated hard-coded values
- global selectors that leak into unrelated pages
