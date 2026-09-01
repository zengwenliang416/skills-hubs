// Ported from @subhanhq/amicro (MIT) — https://github.com/Subhan-code/Amicro--Micro-transitions-
import type { Transition } from 'motion/react'

/**
 * Motion spring presets for premium micro-interactions.
 * Shared library for ported components; components that carried their own
 * tuned spring numbers keep them inline and documented instead.
 */
export const springs = {
  /** Ultra-responsive, crisp snappy feel. */
  snappy: { type: 'spring', stiffness: 400, damping: 28, mass: 0.8 },
  /** Bouncy, playful bounce transition. */
  bouncy: { type: 'spring', stiffness: 300, damping: 15, mass: 1 },
  /** Smooth, elegant default easing transition. */
  smooth: { type: 'spring', stiffness: 220, damping: 24, mass: 1 },
  /** Gentle, low-speed movement. */
  gentle: { type: 'spring', stiffness: 120, damping: 14, mass: 1 },
  /** Stiff, high tension movement. */
  stiff: { type: 'spring', stiffness: 500, damping: 40, mass: 0.5 },
} as const satisfies Record<string, Transition>
