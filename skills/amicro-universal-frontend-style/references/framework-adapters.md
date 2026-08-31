# Framework Adapters

Select the target-native path. The bundled CSS is a portable seed, not a requirement to abandon the project's conventions.

## 1. Dependency Decision Tree

1. **Does the target already have a motion library?** Use it if healthy and appropriate.
2. **Can the effect be expressed with CSS transitions/keyframes?** Prefer CSS for hover, press, fade, icon swap, glare, and simple disclosure.
3. **Does the effect require coordinated mount/unmount, spring physics, drag, or layout interpolation?** Use the existing framework motion solution.
4. **Would adding a library materially increase bundle or maintenance cost?** Do not add it without explicit approval.
5. **Is the page server-rendered?** Keep initial HTML readable and avoid hydration-dependent hidden content.

## 2. Vanilla HTML/CSS/JS

Import the scoped layers:

```html
<link rel="stylesheet" href="/styles/amicro/amicro-tokens.css">
<link rel="stylesheet" href="/styles/amicro/amicro-primitives.css">
<link rel="stylesheet" href="/styles/amicro/amicro-motion.css">

<main class="amicro" data-amicro-theme="dark">
  ...
</main>
```

Use CSS for common states. Use the Web Animations API only when sequencing or interruption is easier than class toggles. Detect reduced motion with `matchMedia('(prefers-reduced-motion: reduce)')`.

Keep event listeners abortable or removable. Use semantic buttons and links rather than clickable divs.

## 3. React and Next.js

### CSS-first

- Import the three CSS layers from a global entrypoint or feature layout.
- Scope with `<main className="amicro" data-amicro-theme={theme}>`.
- Keep state transitions in component state and CSS classes.
- In Next.js, do not hide server-rendered content until hydration.

### Motion/Framer Motion already present

Use the installed import style (`motion/react` or `framer-motion`) consistently. Good candidates:

- `AnimatePresence` for mount/unmount
- layout IDs for active indicators
- motion values for magnetic/drag response
- reduced-motion hook plus CSS fallback

Do not wrap every element in `motion.*`. Keep semantics and component APIs intact.

```tsx
const ease = [0.16, 1, 0.3, 1] as const;

<motion.button
  whileHover={{ y: -1, scale: 1.01 }}
  whileTap={{ scale: 0.98 }}
  transition={{ duration: 0.18, ease }}
/>
```

Gate hover behavior for coarse pointers when the library does not do so automatically.

### React Server Components

Keep token/surface markup server-compatible. Isolate only interactive pieces behind a small client boundary. Do not convert an entire route to a client component for a decorative effect.

## 4. Vue and Nuxt

- Use scoped styles or a feature root plus CSS variables.
- Use `<Transition>`/`<TransitionGroup>` for simple enter/leave.
- Use computed classes for state; do not manually mutate the DOM behind Vue.
- In Nuxt, keep SSR output visible and deterministic.
- If `@vueuse/motion` is already present, map timing tokens rather than introducing a second motion system.

```vue
<Transition name="amicro-swap" mode="out-in">
  <span :key="state">{{ label }}</span>
</Transition>
```

## 5. Svelte and SvelteKit

- Use component styles or imported scoped layers.
- Svelte transitions are appropriate for mount/unmount; CSS handles persistent hover/press.
- Respect `prefersReducedMotion` through a store/media query.
- In SvelteKit, route transitions must not interfere with focus restoration or navigation lifecycle.

```svelte
{#key state}
  <span class="amicro-swap">{label}</span>
{/key}
```

Avoid JavaScript pointer loops when a CSS transform is enough.

## 6. Astro and Static Sites

- Keep the default solution CSS-only.
- Hydrate only components that need stateful interaction.
- Use `client:visible` or an equivalent delayed strategy for non-critical showcase effects.
- Ensure content is visible and usable when JavaScript is unavailable.

## 7. Tailwind CSS 3

Keep tokens in CSS variables and map only stable roles in `tailwind.config` if the project prefers utilities:

```js
theme: {
  extend: {
    colors: {
      'amicro-page': 'var(--amicro-page)',
      'amicro-surface': 'var(--amicro-surface)',
      'amicro-stage': 'var(--amicro-stage)'
    },
    borderRadius: {
      'amicro-card': 'var(--amicro-radius-card)',
      'amicro-stage': 'var(--amicro-radius-stage)'
    }
  }
}
```

Do not generate dozens of one-off arbitrary utilities when a component class is clearer.

## 8. Tailwind CSS 4

Keep variables in the CSS theme layer and use the project's existing Tailwind 4 conventions. The upstream project uses a custom dark variant; adopt the target's current dark-mode selector instead of forcing a new one.

```css
@theme inline {
  --color-amicro-page: var(--amicro-page);
  --color-amicro-surface: var(--amicro-surface);
}
```

If the target uses `data-theme`, keep that selector. Avoid both `.dark` and `data-theme` unless the product intentionally supports both.

## 9. CSS Modules

Place tokens at the page root/global theme boundary; keep component selectors local:

```tsx
<section className={`amicro ${styles.scope}`} data-amicro-theme="dark">
  <article className={styles.card}>...</article>
</section>
```

CSS variables cross module boundaries cleanly and are preferred over importing global component selectors everywhere.

## 10. Sass/Less

Expose the CSS variables at runtime and optionally mirror stable constants as preprocessor variables. Do not bake light/dark values into separate bundles when runtime theme switching is required.

## 11. styled-components / Emotion / Other CSS-in-JS

Create a token object that references CSS variables, not duplicated raw colors. Apply theme variables on a scoped provider/root. Reuse the existing `ThemeProvider` instead of nesting a competing provider solely for Amicro.

```ts
export const amicro = {
  page: 'var(--amicro-page)',
  surface: 'var(--amicro-surface)',
  ease: 'var(--amicro-ease-emphasized)'
};
```

## 12. Existing Component Libraries

For shadcn/ui, Radix, MUI, Chakra, Ant, or another library:

- preserve semantics and accessibility primitives
- style through supported variants, slots, theme overrides, or CSS variables
- do not replace mature dialogs, menus, tabs, or form controls with homegrown versions for visual fidelity
- add motion around the library's lifecycle, not against it

The upstream Amicro registry may be useful in a compatible React/shadcn project, but this Skill should not invoke network installation without the user's approval.

## 13. Browser and Runtime Fallbacks

- `backdrop-filter`: provide opaque background fallback
- `clip-path` route effects: provide opacity fallback
- View Transitions API: progressive enhancement only unless browser support is constrained and verified
- vibration/haptics: optional, permission/runtime dependent, never required
- pointer effects: gate with `(hover: hover) and (pointer: fine)`

## 14. Import Strategy

Preferred order:

1. target's reset/base
2. Amicro tokens or mapped target tokens
3. Amicro primitives or local component styles
4. Amicro motion utilities
5. page/component overrides

Avoid global specificity wars. Scope the imported baseline to `.amicro` or a feature root.


## v1.0.1 Scope Contract

Every standalone React, Vue, or Svelte example must include a scope root, for example `class="amicro" data-amicro-root data-amicro-theme="auto"`. Importing the CSS without such a root leaves scoped variables undefined. Keep the target application's existing theme attribute/provider and map Amicro roles into it when a dedicated scope is unnecessary.

Non-essential framework animation must resolve to an immediate state when reduced motion is requested. Do not rely only on a framework hook while leaving CSS keyframes active.
