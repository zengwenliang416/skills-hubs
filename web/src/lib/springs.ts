// Ported from @subhanhq/amicro (MIT) — https://github.com/Subhan-code/Amicro--Micro-transitions-
import type { Transition } from 'motion/react'

/**
 * Shared motion spring presets for the ported micro-interaction components.
 * Each preset carries the exact numbers its component shipped with, so
 * behavior is unchanged — only centralized. The `type: 'spring'` marker keeps
 * presets usable directly as a Transition; useSpring() callers pass the same
 * object as spring options (extra keys are ignored structurally).
 */
export const springs = {
  /** Fanned card slide — CardCarousel (registry: stiffness 260, damping 22). */
  card: { type: 'spring', stiffness: 260, damping: 22 },
  /** 3D pointer tilt — TiltCard (registry: stiffness 200, damping 20, mass 0.5). */
  tilt: { type: 'spring', stiffness: 200, damping: 20, mass: 0.5 },
  /** Magnetic hover pull — MagneticButton (registry: stiffness 150, damping 15, mass 0.6). */
  magnetic: { type: 'spring', stiffness: 150, damping: 15, mass: 0.6 },
} as const satisfies Record<string, Transition>
