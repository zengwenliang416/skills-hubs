import type { ReactNode } from 'react'

import styles from './Chip.module.css'

export type ChipTone = 'neutral' | 'success'

interface ChipProps {
  children: ReactNode
  tone?: ChipTone
  /** Render as an interactive filter chip when an onClick handler is given. */
  onClick?: () => void
  selected?: boolean
  /** Leading status dot; the label text still carries the meaning. */
  showDot?: boolean
}

export function Chip({
  children,
  tone = 'neutral',
  onClick,
  selected = false,
  showDot = false,
}: ChipProps) {
  const classes = [
    styles.chip,
    tone === 'success' ? styles.success : '',
    onClick && selected ? styles.selected : '',
  ]
    .filter(Boolean)
    .join(' ')

  const content = (
    <>
      {showDot ? <span className={styles.dot} aria-hidden="true" /> : null}
      {children}
    </>
  )

  if (onClick) {
    return (
      <button type="button" className={classes} aria-pressed={selected} onClick={onClick}>
        {content}
      </button>
    )
  }

  return <span className={classes}>{content}</span>
}
