import { useRef } from 'react'
import type { ReactNode, Ref } from 'react'

import { useFinePointerMotion } from '@/lib/useFinePointerMotion'

import styles from './StageCard.module.css'

interface StageCardProps {
  /** Dominant inset visual or interaction area. */
  stage: ReactNode
  title: ReactNode
  meta?: ReactNode
  action?: ReactNode
  className?: string
  /** Ref to the root element, for IntersectionObserver-based effects. */
  rootRef?: Ref<HTMLElement>
  /** Pause decorative stage loops (offscreen, hidden tab, modal coverage). */
  ambientPaused?: boolean
}

/**
 * Signature card: outer surface (r24) + inset stage (r14) + footer.
 * Adds a pointer-tracking radial glow inside the stage, rendered only for
 * fine hover-capable pointers without a reduced-motion request.
 */
export function StageCard({
  stage,
  title,
  meta,
  action,
  className,
  rootRef,
  ambientPaused = false,
}: StageCardProps) {
  const spotlightEnabled = useFinePointerMotion()
  const stageRef = useRef<HTMLDivElement>(null)

  const classes = [styles.card, className].filter(Boolean).join(' ')

  // Track the pointer via CSS variables only — no re-render per frame.
  const handlePointerMove = (event: React.PointerEvent<HTMLElement>) => {
    const stageEl = stageRef.current
    if (!stageEl) {
      return
    }
    const rect = stageEl.getBoundingClientRect()
    stageEl.style.setProperty('--spotlight-x', `${event.clientX - rect.left}px`)
    stageEl.style.setProperty('--spotlight-y', `${event.clientY - rect.top}px`)
  }

  return (
    <article
      ref={rootRef}
      className={classes}
      data-ambient-paused={ambientPaused ? 'true' : undefined}
    >
      <div
        ref={stageRef}
        className={styles.stage}
        onPointerMove={spotlightEnabled ? handlePointerMove : undefined}
      >
        {stage}
        {spotlightEnabled ? <span className={styles.spotlight} aria-hidden="true" /> : null}
      </div>
      <div className={styles.footer}>
        <div className={styles.heading}>
          <h3 className={styles.title}>{title}</h3>
          {meta ? <div className={styles.meta}>{meta}</div> : null}
        </div>
        {action ? <div className={styles.action}>{action}</div> : null}
      </div>
    </article>
  )
}
