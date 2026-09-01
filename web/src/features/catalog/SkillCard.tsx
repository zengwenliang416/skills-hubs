import { useRef } from 'react'
import type { CSSProperties } from 'react'

import { Chip } from '@/components/Chip'
import { StageCard } from '@/components/StageCard'
import { useAmbientActive } from '@/lib/useAmbientActive'

import { categoryLabel, statusLabel } from './data'
import styles from './SkillCard.module.css'
import type { Skill } from './types'

interface SkillCardProps {
  skill: Skill
  onOpen: (skill: Skill) => void
  /** Carousel passes -1 for background slides to keep them out of tab order. */
  tabIndex?: number
}

function swatchStyle(index: number): CSSProperties {
  return { '--swatch-index': index } as CSSProperties
}

/**
 * Minimal living glyph per category; purely visual and hidden from AT.
 * Animated layers carry data-ambient so they can be paused offscreen.
 */
function CategoryVisual({ category }: { category: string }) {
  if (category === 'media') {
    return (
      <div className={styles.visual} aria-hidden="true">
        <svg className={styles.glyph} viewBox="0 0 64 64" fill="none">
          <rect
            x="10"
            y="14"
            width="44"
            height="36"
            rx="8"
            stroke="currentColor"
            strokeWidth="2.5"
          />
          <circle cx="24" cy="28" r="5" stroke="currentColor" strokeWidth="2.5" />
          <path
            d="M14 46l12-12 8 8 8-10 8 14"
            stroke="currentColor"
            strokeWidth="2.5"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
        <span className={styles.mediaGlow} data-ambient />
        <span className={styles.mediaShimmer} data-ambient />
      </div>
    )
  }

  if (category === 'frontend-design') {
    return (
      <div className={styles.visual} aria-hidden="true">
        <svg className={styles.glyph} viewBox="0 0 64 64" fill="none">
          <rect
            x="12"
            y="10"
            width="40"
            height="26"
            rx="6"
            stroke="currentColor"
            strokeWidth="2.5"
          />
          <rect
            x="18"
            y="42"
            width="28"
            height="12"
            rx="6"
            stroke="currentColor"
            strokeWidth="2.5"
          />
          <path d="M12 22h40" stroke="currentColor" strokeWidth="2.5" />
          <circle cx="20" cy="16" r="1.75" fill="currentColor" />
          <circle cx="27" cy="16" r="1.75" fill="currentColor" />
        </svg>
        <span className={styles.swatches}>
          {[0, 1, 2, 3].map((index) => (
            <span key={index} className={styles.swatch} style={swatchStyle(index)} data-ambient />
          ))}
        </span>
      </div>
    )
  }

  return (
    <div className={styles.visual} aria-hidden="true">
      <svg className={styles.glyph} viewBox="0 0 64 64" fill="none">
        <rect
          x="12"
          y="12"
          width="40"
          height="40"
          rx="10"
          stroke="currentColor"
          strokeWidth="2.5"
        />
        <path
          d="M32 22v20M22 32h20"
          stroke="currentColor"
          strokeWidth="2.5"
          strokeLinecap="round"
        />
      </svg>
    </div>
  )
}

/** Whole card is a single-target control: one stretched button, no nested interactives. */
export function SkillCard({ skill, onOpen, tabIndex }: SkillCardProps) {
  const rootRef = useRef<HTMLElement>(null)
  const ambientActive = useAmbientActive(rootRef)

  return (
    <StageCard
      className={styles.card}
      rootRef={rootRef}
      ambientPaused={!ambientActive}
      stage={<CategoryVisual category={skill.category} />}
      title={
        <button
          type="button"
          className={styles.openButton}
          aria-haspopup="dialog"
          tabIndex={tabIndex}
          onClick={() => onOpen(skill)}
        >
          {skill.title}
        </button>
      }
      meta={
        <span>
          v{skill.version} · {categoryLabel(skill.category)}
        </span>
      }
      action={
        <Chip tone={skill.status === 'active' ? 'success' : 'neutral'} showDot>
          {statusLabel(skill.status)}
        </Chip>
      }
    />
  )
}
