// Ported from @subhanhq/amicro (MIT) — https://github.com/Subhan-code/Amicro--Micro-transitions-
import { motion, useReducedMotion } from 'motion/react'
import { useState } from 'react'
import type { ReactNode } from 'react'

import { IconButton } from '@/components/IconButton'
import { springs } from '@/lib/springs'
import { useMediaQuery } from '@/lib/useMediaQuery'

import styles from './CardCarousel.module.css'

/*
 * Fan geometry, scaled up from the registry original (110px cards, 52px step,
 * 12deg fan, 0.1 scale falloff) to fit our wider stage cards. Compact
 * screens use a tighter fan to avoid horizontal overflow.
 */
const FAN = {
  xStep: 150,
  xStepCompact: 64,
  rotateStep: 8,
  rotateStepCompact: 5,
  yStep: 12,
  scaleStep: 0.08,
} as const

interface CardCarouselProps {
  /** Accessible name for the carousel region. */
  label: string
  count: number
  getSlideLabel: (index: number) => string
  /** isActive lets callers wire tab order / interactivity of slide content. */
  renderSlide: (index: number, isActive: boolean) => ReactNode
  className?: string
}

/**
 * Fanned card carousel with spring motion (original: stiffness 260,
 * damping 22). Reduced motion keeps every control working but switches
 * instantly. Prev/next are real buttons with disabled states; dots carry
 * aria-current and are keyboard operable.
 */
export function CardCarousel({
  label,
  count,
  getSlideLabel,
  renderSlide,
  className,
}: CardCarouselProps) {
  const [activeIndex, setActiveIndex] = useState(0)
  const reducedMotion = useReducedMotion()
  const compact = useMediaQuery('(max-width: 40rem)')

  // Reduced motion keeps every control working but switches instantly;
  // otherwise the shared card slide spring (registry: stiffness 260,
  // damping 22) drives the fan geometry.
  const transition = reducedMotion ? { duration: 0 } : springs.card

  const xStep = compact ? FAN.xStepCompact : FAN.xStep
  const rotateStep = compact ? FAN.rotateStepCompact : FAN.rotateStep

  const classes = [styles.carousel, className].filter(Boolean).join(' ')

  // Arrow/Home/End work from anywhere inside the carousel group (buttons,
  // dots, slide overlays), clamped to the same bounds as the prev/next
  // buttons. Other keys pass through untouched.
  const handleKeyDown = (event: React.KeyboardEvent<HTMLDivElement>) => {
    if (event.key === 'ArrowLeft') {
      event.preventDefault()
      setActiveIndex((prev) => Math.max(0, prev - 1))
    } else if (event.key === 'ArrowRight') {
      event.preventDefault()
      setActiveIndex((prev) => Math.min(count - 1, prev + 1))
    } else if (event.key === 'Home') {
      event.preventDefault()
      setActiveIndex(0)
    } else if (event.key === 'End') {
      event.preventDefault()
      setActiveIndex(count - 1)
    }
  }

  return (
    // APG carousel regions handle arrow keys on the group itself; the role
    // stays non-interactive because the interactive parts are the buttons.
    // eslint-disable-next-line jsx-a11y/no-noninteractive-element-interactions
    <div
      className={classes}
      role="group"
      aria-roledescription="carousel"
      aria-label={label}
      onKeyDown={handleKeyDown}
    >
      <div className={styles.frame}>
        {Array.from({ length: count }, (_, index) => {
          const offset = index - activeIndex
          const absOffset = Math.abs(offset)
          return (
            <motion.div
              key={index}
              className={styles.slide}
              initial={false}
              animate={{
                x: offset * xStep,
                y: absOffset * FAN.yStep,
                rotateZ: offset * rotateStep,
                scale: 1 - absOffset * FAN.scaleStep,
                zIndex: count - absOffset,
              }}
              transition={transition}
            >
              {renderSlide(index, index === activeIndex)}
              {index !== activeIndex ? (
                <button
                  type="button"
                  className={styles.slideFocus}
                  aria-label={`将「${getSlideLabel(index)}」移到前景`}
                  onClick={() => setActiveIndex(index)}
                />
              ) : null}
            </motion.div>
          )
        })}
      </div>

      <div className={styles.controls}>
        <IconButton
          label="上一张"
          disabled={activeIndex === 0}
          onClick={() => setActiveIndex((prev) => Math.max(0, prev - 1))}
        >
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
            <path
              d="M10 3L5 8l5 5"
              stroke="currentColor"
              strokeWidth="1.8"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
        </IconButton>
        <div className={styles.dots} role="group" aria-label="选择卡片">
          {Array.from({ length: count }, (_, index) => (
            <button
              key={index}
              type="button"
              className={styles.dot}
              data-current={index === activeIndex ? 'true' : undefined}
              aria-label={`查看第 ${index + 1} 张`}
              aria-current={index === activeIndex ? 'true' : undefined}
              onClick={() => setActiveIndex(index)}
            />
          ))}
        </div>
        <IconButton
          label="下一张"
          disabled={activeIndex === count - 1}
          onClick={() => setActiveIndex((prev) => Math.min(count - 1, prev + 1))}
        >
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
            <path
              d="M6 3l5 5-5 5"
              stroke="currentColor"
              strokeWidth="1.8"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
        </IconButton>
      </div>
    </div>
  )
}
