# Accessibility and Performance

## Interaction and focus

- Prefer native controls. Every pointer action needs a keyboard path.
- Essential content and actions must not exist only on hover.
- Gate pointer travel with `(hover: hover) and (pointer: fine)`.
- Use `:focus-visible` with a persistent, unclipped, high-contrast ring.
- Keep logical focus order; route changes and dialogs need correct focus movement independent of animation.

## Motion safety

Declare non-essential transitions and keyframe animation only when the user has not requested reduced motion:

```css
@media (prefers-reduced-motion: no-preference) {
  .amicro-reveal {
    animation: amicro-reveal var(--amicro-duration-card) var(--amicro-ease-emphasized) both;
  }
}

@media (prefers-reduced-motion: reduce) {
  .amicro-reveal {
    animation: none !important;
    transform: none !important;
  }
}
```

Reduce or remove large translation, zoom, perspective, parallax, repeated pulsing, continuous movement, and smooth scrolling. Preserve immediate selected, focus, success/error, loading, and disclosure state. Never require a user to watch an animation before acting.

## Names and announcements

- Each control exposes one coherent accessible name. Do not leave old and new animated labels simultaneously in the accessibility tree.
- Prefer updating one text node. When two visual nodes are unavoidable, synchronize `hidden` and `aria-hidden`.
- Icon-only controls need labels. Loading controls expose busy/disabled state.
- Toasts and asynchronous success/error changes use an appropriate live region without stealing focus.
- A shake, color, or icon alone never replaces an error message.

## Contrast and themes

- Validate text, icons, focus, borders, and semantic states in light and dark themes.
- The bundled light muted token is `#6f6f6f`; still retest it against every target surface and actual text size.
- Intermediate animated colors must stay usable. Preserve forced-colors behavior where supported.

## Performance

Prefer `transform` and `opacity`, short interruptible transitions, requestAnimationFrame-batched pointer work, and progressive enhancement. Avoid `transition: all`, frequent animation of layout properties, continuous large blur/backdrop-filter/shadow animation, global `will-change`, many 3D layers, and hidden server-rendered content waiting for hydration.

## Browser evidence boundary

Static checks can detect code clues, not prove runtime semantics or visual quality. Minimum rendered checks:

| Area | Minimum check |
| --- | --- |
| responsive | 320, 360, 768, 1440px; no document-level horizontal overflow |
| keyboard | tab order, focus visibility, activation, escape where relevant |
| touch | usable controls; no hover-only content or accidental drag |
| reduced motion | trigger each interaction; inspect active animations and retained state |
| accessible names | exact role/name query before and after animated state changes |
| theme | light/dark/system; focus and semantic colors visible |
| direction | RTL when the product supports it |
| content | long labels, empty, loading, success, error, disabled |
| runtime | console/page errors, input latency, layout shift, excessive paint |

Report rendered checks separately from static scans and do not infer evidence that was not collected.
