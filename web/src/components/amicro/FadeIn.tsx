// Ported from @subhanhq/amicro (MIT) — https://github.com/Subhan-code/Amicro--Micro-transitions-
import { motion, useReducedMotion } from 'motion/react'
import type { ReactNode } from 'react'

interface FadeInProps {
  children: ReactNode
  /** Seconds. Original default: 0.5. */
  duration?: number
  /** Seconds. */
  delay?: number
  className?: string
}

/**
 * Entrance: pure opacity fade, once per scroll into view.
 * Reduced motion: static.
 */
export function FadeIn({ children, duration = 0.5, delay = 0, className }: FadeInProps) {
  const reducedMotion = useReducedMotion()

  if (reducedMotion) {
    return <div className={className}>{children}</div>
  }

  return (
    <motion.div
      initial={{ opacity: 0 }}
      whileInView={{ opacity: 1 }}
      viewport={{ once: true }}
      transition={{
        duration,
        delay,
        // easeOutCubic — original component easing.
        ease: [0.215, 0.61, 0.355, 1],
      }}
      className={className}
    >
      {children}
    </motion.div>
  )
}
