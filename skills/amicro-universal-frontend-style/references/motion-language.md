# Amicro Motion Language

Motion should acknowledge input, explain state continuity, and preserve spatial orientation. Use one dominant idea per component. Decorative atmosphere is optional and lowest priority.

## Timing

| Intent | Duration | Typical use |
| --- | ---: | --- |
| instant | `120ms` | press, focus, tiny opacity shift |
| fast | `180ms` | hover, icon nudge, chip change |
| control | `240ms` | icon/text swap, toggle, compact disclosure |
| card | `320ms` | elevation, content reveal |
| section | `480ms` | coordinated panel entrance |
| route | `650ms` | page/scene transition |
| maximum blocking | `850ms` | rare full transition; never routine task UI |

Primary emphasized easing: `cubic-bezier(.16, 1, .3, 1)`. Curtain/door effects may use `cubic-bezier(.83, 0, .17, 1)`. Press-down should be faster than release.

## State recipes

| State | Visual change | Reduced-motion equivalent |
| --- | --- | --- |
| hover | `translateY(-1px)` or `scale(1.01–1.02)` plus surface shift | surface/border change only |
| press | `scale(.97–.99)` | immediate surface shift |
| focus | ring and border | same ring |
| enter | opacity plus y `8→0` | opacity only or immediate |
| icon/text swap | opacity/scale/blur crossfade | immediate replacement |
| success | compact semantic icon/label change | immediate semantic state |
| route | opacity plus small perspective or mask | immediate navigation or short opacity |

## CSS baseline

Non-essential movement is opt-in for users who have not requested reduction:

```css
.amicro-control {
  background: var(--amicro-surface);
}

@media (prefers-reduced-motion: no-preference) {
  .amicro-control {
    transition: transform var(--amicro-duration-fast) var(--amicro-ease-emphasized),
                background-color var(--amicro-duration-fast) ease;
  }

  @media (hover: hover) and (pointer: fine) {
    .amicro-control:hover { transform: translateY(-1px); }
  }
}

@media (prefers-reduced-motion: reduce) {
  .amicro-control,
  .amicro-control::before,
  .amicro-control::after {
    animation: none !important;
    transition-duration: 0.01ms !important;
    transform: none !important;
  }
}
```

Do not rely on a later, lower-specificity reduced-motion selector to override an active animation selector. Prefer putting the original declaration inside `no-preference`.

## Interaction rules

- Hover: fine-pointer enhancement only; never expose essential content exclusively on hover.
- Press: immediate, interruptible, and small enough not to move the hit target.
- Text/icon swap: keep one accessible label; hidden visual nodes must also be absent from the accessibility tree.
- Magnetic motion: clamp to a few pixels, use rAF, reset on leave/blur/cancel, and disable for touch and reduced motion.
- Glare/pulse/shake: decorative or supplementary only; short, trigger-bound, never infinite by default.
- Route transitions: navigation remains immediate/cancellable; preserve title and focus restoration; avoid blur-heavy full-screen layers in dense task UI.

## Library adapters

Translate intent into the target animation library rather than copying spring numbers mechanically. Reuse the project's existing Motion, GSAP, Web Animations, or transition primitives. Native CSS remains the dependency-free baseline.

## Performance and verification

Prefer transforms/opacity, avoid layout animation and `transition: all`, and inspect `document.getAnimations()` after triggering states under reduced motion. Test mobile width, long labels, rapid repeated activation, navigation interruption, and console/runtime errors.
