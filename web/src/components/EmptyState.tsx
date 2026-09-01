import type { ReactNode } from 'react'

import styles from './EmptyState.module.css'

interface EmptyStateProps {
  title: string
  description?: string
  /** Recovery actions, e.g. a button clearing the active filter. */
  children?: ReactNode
  role?: 'status' | 'region'
}

/** Centered placeholder for empty lists or missing content. */
export function EmptyState({ title, description, children, role = 'status' }: EmptyStateProps) {
  return (
    <div className={styles.emptyState} role={role}>
      <h3 className={styles.title}>{title}</h3>
      {description ? <p className={styles.description}>{description}</p> : null}
      {children ? <div className={styles.actions}>{children}</div> : null}
    </div>
  )
}
