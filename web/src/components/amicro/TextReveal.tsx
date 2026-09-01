// Ported from @subhanhq/amicro (MIT) — https://github.com/Subhan-code/Amicro--Micro-transitions-
import { motion, useReducedMotion } from 'motion/react'

import styles from './TextReveal.module.css'

interface TextRevealProps {
  /** Lines are split on "\n" and revealed line by line (never char fragments). */
  text: string
  /** Seconds per line. Original default: 0.8. */
  duration?: number
  /** Seconds between lines. Original default: 0.15. */
  staggerDelay?: number
  className?: string
}

/**
 * Line-level text reveal with clip mask, triggered once on scroll into view.
 * Reduced motion renders the final state statically.
 */
export function TextReveal({
  text,
  duration = 0.8,
  staggerDelay = 0.15,
  className,
}: TextRevealProps) {
  const reducedMotion = useReducedMotion()
  const lines = text.split('\n')

  if (reducedMotion) {
    return (
      <div className={[styles.container, className].filter(Boolean).join(' ')}>
        {lines.map((line) => (
          <span key={line} className={styles.line}>
            <span className={styles.text}>{line}</span>
          </span>
        ))}
      </div>
    )
  }

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: { staggerChildren: staggerDelay },
    },
  }

  const itemVariants = {
    hidden: { y: '100%' },
    visible: {
      y: 0,
      // easeOutExpo — matches --amicro-ease-emphasized.
      transition: { duration, ease: [0.16, 1, 0.3, 1] as const },
    },
  }

  return (
    <motion.div
      variants={containerVariants}
      initial="hidden"
      whileInView="visible"
      viewport={{ once: true, margin: '-20%' }}
      className={[styles.container, className].filter(Boolean).join(' ')}
    >
      {lines.map((line) => (
        <span key={line} className={styles.line}>
          <motion.span variants={itemVariants} className={styles.text}>
            {line}
          </motion.span>
        </span>
      ))}
    </motion.div>
  )
}
