// Ported from @subhanhq/amicro (MIT) — https://github.com/Subhan-code/Amicro--Micro-transitions-
import { motion, useReducedMotion } from 'motion/react'
import type { ReactNode } from 'react'

interface FadeUpProps {
  children: ReactNode
  /** Seconds. Original default: 0.6. */
  duration?: number
  /** Seconds. */
  delay?: number
  /** Pixels. Original default: 20. */
  yOffset?: number
  className?: string
}

/**
 * Entrance: fade + rise, once per scroll into view (framer's own
 * IntersectionObserver with `once` semantics). Reduced motion: static.
 */
export function FadeUp({
  children,
  duration = 0.6,
  delay = 0,
  yOffset = 20,
  className,
}: FadeUpProps) {
  const reducedMotion = useReducedMotion()

  if (reducedMotion) {
    return <div className={className}>{children}</div>
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: yOffset }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      transition={{
        duration,
        delay,
        // easeOutExpo — matches --amicro-ease-emphasized.
        ease: [0.16, 1, 0.3, 1],
      }}
      className={className}
    >
      {children}
    </motion.div>
  )
}
