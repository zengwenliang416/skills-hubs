// Ported from @subhanhq/amicro (MIT) — https://github.com/Subhan-code/Amicro--Micro-transitions-
import { motion, useMotionValue, useSpring, useTransform } from 'motion/react'
import { useRef } from 'react'
import type { ReactNode } from 'react'

import { useFinePointerMotion } from '@/lib/useFinePointerMotion'

import styles from './TiltCard.module.css'

interface TiltCardProps {
  children: ReactNode
  /** Maximum tilt in degrees. Registry default is 15; we default to a calmer 8. */
  maxTilt?: number
  className?: string
}

/**
 * 3D parallax tilt wrapper. Only active for fine, hover-capable pointers
 * without a reduced-motion request; otherwise renders a plain static div
 * and never attaches pointer listeners.
 */
export function TiltCard({ children, maxTilt = 8, className }: TiltCardProps) {
  const enabled = useFinePointerMotion()
  const cardRef = useRef<HTMLDivElement>(null)

  // Motion values for x/y pointer offset relative to card center (-0.5 to 0.5).
  const x = useMotionValue(0)
  const y = useMotionValue(0)

  // Original registry spring config: { damping: 20, stiffness: 200, mass: 0.5 }.
  const rotateX = useSpring(useTransform(y, [-0.5, 0.5], [maxTilt, -maxTilt]), {
    damping: 20,
    stiffness: 200,
    mass: 0.5,
  })
  const rotateY = useSpring(useTransform(x, [-0.5, 0.5], [-maxTilt, maxTilt]), {
    damping: 20,
    stiffness: 200,
    mass: 0.5,
  })

  if (!enabled) {
    const classes = [styles.root, className].filter(Boolean).join(' ')
    return <div className={classes}>{children}</div>
  }

  const handleMouseMove = (event: React.MouseEvent<HTMLDivElement>) => {
    if (!cardRef.current) {
      return
    }
    const rect = cardRef.current.getBoundingClientRect()
    x.set((event.clientX - rect.left) / rect.width - 0.5)
    y.set((event.clientY - rect.top) / rect.height - 0.5)
  }

  const handleMouseLeave = () => {
    x.set(0)
    y.set(0)
  }

  const classes = [styles.root, styles.perspective, className].filter(Boolean).join(' ')

  return (
    <div
      ref={cardRef}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
      className={classes}
    >
      <motion.div style={{ rotateX, rotateY }} className={styles.card3d}>
        <div className={styles.depth}>{children}</div>
      </motion.div>
    </div>
  )
}
