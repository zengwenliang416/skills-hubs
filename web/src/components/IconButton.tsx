import type { ButtonHTMLAttributes, ReactNode } from 'react'

import styles from './IconButton.module.css'

interface IconButtonProps extends Omit<
  ButtonHTMLAttributes<HTMLButtonElement>,
  'aria-label' | 'children'
> {
  /** Accessible name; icon-only buttons must always be labelled. */
  label: string
  children: ReactNode
}

export function IconButton({
  label,
  className,
  children,
  type = 'button',
  ...rest
}: IconButtonProps) {
  const classes = [styles.iconButton, className].filter(Boolean).join(' ')
  return (
    <button type={type} aria-label={label} className={classes} {...rest}>
      {children}
    </button>
  )
}
