import { useEffect, useRef, useState } from 'react'

import { Button } from '@/components/Button'
import { IconButton } from '@/components/IconButton'
import { copyTextToClipboard } from '@/lib/clipboard'

import styles from './CopyButton.module.css'

const COPY_FEEDBACK_MS = 1500

type CopyState = 'idle' | 'copied' | 'failed'

interface CopyButtonProps {
  /** Text copied to the clipboard on activation. */
  text: string
  /** Accessible name in the idle state; also the button variant's text. */
  label: string
  copiedLabel?: string
  failedLabel?: string
  /** Called after a successful copy, e.g. for analytics. */
  onCopied?: () => void
  className?: string
  variant?: 'icon' | 'button'
}

/** Copy-to-clipboard control with copied/failed feedback and a live region. */
export function CopyButton({
  text,
  label,
  copiedLabel = '已复制',
  failedLabel = '复制失败',
  onCopied,
  className,
  variant = 'icon',
}: CopyButtonProps) {
  const timerRef = useRef<number | undefined>(undefined)
  const [state, setState] = useState<CopyState>('idle')

  useEffect(
    () => () => {
      window.clearTimeout(timerRef.current)
    },
    [],
  )

  const handleCopy = async () => {
    const ok = await copyTextToClipboard(text)
    setState(ok ? 'copied' : 'failed')
    window.clearTimeout(timerRef.current)
    timerRef.current = window.setTimeout(() => setState('idle'), COPY_FEEDBACK_MS)
    if (ok) {
      onCopied?.()
    }
  }

  const feedback = state === 'copied' ? copiedLabel : state === 'failed' ? failedLabel : ''
  const rootClass = [styles.root, variant === 'icon' ? className : undefined]
    .filter(Boolean)
    .join(' ')

  return (
    <span className={rootClass} data-state={state}>
      {variant === 'icon' ? (
        <IconButton
          label={state === 'idle' ? label : feedback}
          className={state === 'failed' ? styles.failed : undefined}
          onClick={handleCopy}
        >
          {state === 'copied' ? (
            <svg
              key="check"
              className={styles.icon}
              width="16"
              height="16"
              viewBox="0 0 16 16"
              fill="none"
              aria-hidden="true"
            >
              <path
                d="M3 8.5l3.5 3.5L13 4.5"
                stroke="currentColor"
                strokeWidth="1.8"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
          ) : state === 'failed' ? (
            <svg
              key="alert"
              className={styles.icon}
              width="16"
              height="16"
              viewBox="0 0 16 16"
              fill="none"
              aria-hidden="true"
            >
              <path
                d="M8 2.6 14.4 13H1.6L8 2.6Z"
                stroke="currentColor"
                strokeWidth="1.6"
                strokeLinejoin="round"
              />
              <path d="M8 6.6v3" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
              <circle cx="8" cy="11.3" r="0.9" fill="currentColor" />
            </svg>
          ) : (
            <svg
              key="clipboard"
              className={styles.icon}
              width="16"
              height="16"
              viewBox="0 0 16 16"
              fill="none"
              aria-hidden="true"
            >
              <rect
                x="4.5"
                y="4.5"
                width="8"
                height="9"
                rx="1.5"
                stroke="currentColor"
                strokeWidth="1.6"
              />
              <path
                d="M5.5 3.5h5a1 1 0 0 1 1 1v1h-7v-1a1 1 0 0 1 1-1Z"
                stroke="currentColor"
                strokeWidth="1.6"
              />
            </svg>
          )}
        </IconButton>
      ) : (
        <Button className={className} onClick={handleCopy}>
          {state === 'idle' ? label : feedback}
        </Button>
      )}
      <span className={styles.visuallyHidden} role="status">
        {feedback}
      </span>
    </span>
  )
}
