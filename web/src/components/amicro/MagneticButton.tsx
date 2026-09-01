// Ported from @subhanhq/amicro (MIT) — https://github.com/Subhan-code/Amicro--Micro-transitions-
import { motion, useSpring } from 'motion/react'
import { useRef } from 'react'
import type { ReactNode } from 'react'

import { useFinePointerMotion } from '@/lib/useFinePointerMotion'

import styles from './MagneticButton.module.css'

interface MagneticButtonProps {
  children: ReactNode
  /** Pull radius in px. Original default: 45. */
  range?: number
  /** Pull factor (0–1). Original default: 0.35. */
  strength?: number
  className?: string
}

/**
 * Magnetic hover wrapper: the control is gently pulled toward the pointer.
 * Only active for fine, hover-capable pointers without a reduced-motion
 * request; otherwise renders a plain static wrapper (no listeners, no
 * transform) so the child control behaves exactly like an unwrapped one.
 */
export function MagneticButton({
  children,
  range = 45,
  strength = 0.35,
  className,
}: MagneticButtonProps) {
  const enabled = useFinePointerMotion()
  const ref = useRef<HTMLDivElement>(null)

  // Original registry spring config: { stiffness: 150, damping: 15, mass: 0.6 }.
  const x = useSpring(0, { stiffness: 150, damping: 15, mass: 0.6 })
  const y = useSpring(0, { stiffness: 150, damping: 15, mass: 0.6 })

  const classes = [styles.root, className].filter(Boolean).join(' ')

  if (!enabled) {
    return <div className={classes}>{children}</div>
  }

  const handleMouseMove = (event: React.MouseEvent<HTMLDivElement>) => {
    if (!ref.current) {
      return
    }
    const { left, top, width, height } = ref.current.getBoundingClientRect()
    const centerX = left + width / 2
    const centerY = top + height / 2
    const distance = Math.hypot(event.clientX - centerX, event.clientY - centerY)

    if (distance < range) {
      x.set((event.clientX - centerX) * strength)
      y.set((event.clientY - centerY) * strength)
    } else {
      x.set(0)
      y.set(0)
    }
  }

  const handleMouseLeave = () => {
    x.set(0)
    y.set(0)
  }

  return (
    <motion.div
      ref={ref}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
      style={{ x, y }}
      className={classes}
    >
      {children}
    </motion.div>
  )
}
