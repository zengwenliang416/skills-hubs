import { useRef } from 'react'
import type { CSSProperties } from 'react'

import { Chip } from '@/components/Chip'
import { StageCard } from '@/components/StageCard'
import { useAmbientActive } from '@/lib/useAmbientActive'

import { categoryLabel, skillLinks, statusLabel } from './data'
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

interface TrustItem {
  key: string
  label: string
  icon: 'doc' | 'code' | 'check' | 'shield'
}

/**
 * Trust glyphs derived only from real catalog links: docs/repo from
 * sanitized skillLinks, tests/security from the optional URL fields.
 */
function trustItems(skill: Skill): TrustItem[] {
  const links = skillLinks(skill)
  const items: TrustItem[] = []
  if (links.documentationUrl) {
    items.push({ key: 'docs', label: '文档', icon: 'doc' })
  }
  if (links.repositoryUrl) {
    items.push({ key: 'repo', label: '源码', icon: 'code' })
  }
  if (links.testsUrl) {
    items.push({ key: 'tests', label: '测试', icon: 'check' })
  }
  if (links.securityNotesUrl) {
    items.push({ key: 'security', label: '安全', icon: 'shield' })
  }
  return items
}

/** Tiny 12px line icons; decorative only, the text label carries meaning. */
function TrustIcon({ icon }: { icon: TrustItem['icon'] }) {
  const shared = {
    width: 12,
    height: 12,
    viewBox: '0 0 12 12',
    fill: 'none',
    'aria-hidden': true,
  } as const

  if (icon === 'doc') {
    return (
      <svg {...shared}>
        <path
          d="M3 1.5h4L9.5 4v6.5h-6.5v-9Z"
          stroke="currentColor"
          strokeWidth="1.2"
          strokeLinejoin="round"
        />
        <path d="M7 1.5V4h2.5" stroke="currentColor" strokeWidth="1.2" strokeLinejoin="round" />
      </svg>
    )
  }

  if (icon === 'code') {
    return (
      <svg {...shared}>
        <path
          d="M4 3.5 1.5 6 4 8.5M8 3.5 10.5 6 8 8.5"
          stroke="currentColor"
          strokeWidth="1.2"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
    )
  }

  if (icon === 'check') {
    return (
      <svg {...shared}>
        <path
          d="M2 6.25 4.75 9 10 3"
          stroke="currentColor"
          strokeWidth="1.2"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
    )
  }

  return (
    <svg {...shared}>
      <path
        d="M6 1.25 10 2.75v3c0 2.5-1.75 4-4 5-2.25-1-4-2.5-4-5v-3L6 1.25Z"
        stroke="currentColor"
        strokeWidth="1.2"
        strokeLinejoin="round"
      />
    </svg>
  )
}

/** Whole card is a single-target control: one stretched button, no nested interactives. */
export function SkillCard({ skill, onOpen, tabIndex }: SkillCardProps) {
  const rootRef = useRef<HTMLElement>(null)
  const ambientActive = useAmbientActive(rootRef)

  const visibleTags = skill.tags.slice(0, 2)
  const overflowTags = skill.tags.length - visibleTags.length
  const trust = trustItems(skill)

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
        <div className={styles.details}>
          <p className={styles.description}>{skill.description}</p>
          <p className={styles.metaRow}>
            v{skill.version} · {skill.license} · {categoryLabel(skill.category)}
          </p>
          <div className={styles.tags}>
            {visibleTags.map((tag) => (
              <Chip key={tag}>{tag}</Chip>
            ))}
            {overflowTags > 0 ? <span className={styles.moreTags}>+{overflowTags}</span> : null}
          </div>
          {trust.length > 0 ? (
            <ul className={styles.trust} aria-label="可审阅材料">
              {trust.map((item) => (
                <li key={item.key} className={styles.trustItem}>
                  <TrustIcon icon={item.icon} />
                  {item.label}
                </li>
              ))}
            </ul>
          ) : null}
        </div>
      }
      action={
        <Chip tone={skill.status === 'active' ? 'success' : 'neutral'} showDot>
          {statusLabel(skill.status)}
        </Chip>
      }
    />
  )
}
