# Component Recipes

Use these as behavioral recipes. Implement with the target project's component API and token system.

## 1. Signature Card

### Anatomy

```text
card (surface, radius 24)
├── stage (inset 12, radius 14)
│   └── primary visual or interaction
└── footer
    ├── title + metadata
    └── optional action/status
```

### States

- default: quiet surface and border
- hover/focus-within: surface hover, tiny lift, stage animation
- pressed/selected: stable selected border or accent
- disabled: no lift, lower contrast but readable

The whole card may be clickable only when it has one destination. Otherwise keep separate actions and do not nest interactive controls inside a link.

## 2. Primary Button

- Height: `36–44px`; use the larger end for mobile-heavy interfaces.
- Radius: pill or `10–14px`.
- Label: `13–14px`, medium weight, tight tracking.
- Icon: `14–18px`.
- Hover: surface shift and optional arrow/icon motion.
- Press: immediate scale `.97–.99`.
- Focus: visible ring independent of hover.
- Loading: retain width; show progress and disable duplicate submission.
- Success: swap icon/label without relying only on color.

Avoid moving the label so far that the pointer target feels unstable.

## 3. Icon Button

- Maintain at least a `40×40px` hit target where practical.
- Visual glyph may remain `16px` inside a larger transparent target.
- Provide `aria-label` or visible tooltip on focus and hover.
- For icon swap, update label/state semantics too.

## 4. Navigation Pill or Rail

- Stable item positions with one active indicator.
- Active state uses both surface and text contrast.
- Indicator motion is optional; without motion it should jump directly.
- Keyboard arrow behavior follows the component role: tabs use roving focus; normal links preserve normal tab order.
- On mobile, allow wrapping or horizontal scroll with visible affordance.

## 5. Chip and Status Badge

- Compact height around `24–28px`.
- Radius: pill.
- Use text plus icon or shape for semantic state.
- Interactive chips require focus and selected state; non-interactive badges should not receive button styling.

## 6. Text Field

- Label stays visible; placeholder is not a label.
- Control radius `10–12px`.
- Border and background change on hover/focus; focus ring remains high contrast.
- Error state includes message and `aria-describedby`/`aria-invalid` where supported.
- Avoid shake-only validation. A short shake may supplement the persistent error.

## 7. Toggle/Switch

- Track communicates on/off even without animation.
- Thumb uses transform for movement.
- Entire label row can be clickable when semantically connected.
- Use native checkbox semantics or a correctly implemented switch role.
- Respect reduced motion with immediate thumb positioning.

## 8. Disclosure, Accordion, and Menu

- Trigger remains in DOM and owns expanded state.
- Animate clip/opacity or measured height only when necessary.
- Content becomes interactive only after it is visible.
- Escape and outside-click behavior must match the component type.
- Do not trap focus in non-modal menus.

## 9. Tooltip

- Use only for supplemental information, never essential instructions.
- Show on keyboard focus and hover.
- Keep motion under `180ms` and remove travel under reduced motion.
- Prevent clipping at viewport edges.

## 10. Toast and Inline Feedback

### Toast

- Brief, non-blocking, and announced through an appropriate live region.
- Enter with small y/opacity change; exit faster.
- Do not use toast as the only record of an important error.

### Inline success

- Prefer near the initiating control for copy/save/add actions.
- Icon swap plus concise text is enough; haptics are optional and progressive.

## 11. Text Reveal

- Best for short titles, metrics, or label changes.
- Preserve readable fallback text before hydration.
- Do not split screen-reader output into meaningless fragments.
- Avoid animating long paragraphs word by word.

## 12. Metric and Chart Card

- Keep chart stage dominant and label/metric compact.
- Animate data change, not initial decoration alone.
- Provide textual values and trend labels.
- Do not animate every bar/point indefinitely.
- Respect reduced motion with immediate data state.

## 13. Modal and Dialog

- Backdrop opacity may transition; dialog can use opacity plus small scale/y.
- Use real modal semantics and focus management.
- Closing should remain immediate enough to feel responsive.
- Page-transition effects are not a substitute for dialog behavior.

## 14. Page Transition

- Preserve route focus management and announce the new page title.
- One outgoing and one incoming surface is sufficient.
- Keep navigation cancellable; do not hold the URL update for decoration.
- Use a fade fallback for reduced motion or unsupported masking.

## 15. Recipe Selection

| User goal | Preferred recipe |
| --- | --- |
| make controls feel responsive | press + surface shift |
| make state change legible | icon/text swap |
| add premium polish | subtle glare or ring, once |
| explain navigation | active indicator or short route fade |
| showcase motion | one spatial door/iris/curtain metaphor |
| fix dense enterprise UI | nested surfaces + focus + restrained control motion |
| improve mobile | larger targets + touch-visible states, no magnetic/tilt |

## 16. Completion Checklist per Component

- semantic element/role is correct
- keyboard and touch work
- hover is gated to capable pointers
- focus is visible
- disabled/loading/error/success states are defined when relevant
- reduced-motion state is defined
- transition can be interrupted
- no layout shift or clipped content
- text and icon remain understandable without animation
