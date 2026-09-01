import { CopyButton } from '@/components/CopyButton'

import styles from './CodeBlock.module.css'

interface CodeBlockProps {
  /** Command or code shown verbatim inside the block. */
  code: string
  /** Accessible name for the integrated copy button. */
  label?: string
  className?: string
  /** Called after a successful copy, e.g. for analytics. */
  onCopied?: () => void
}

/** Monospace code block with horizontal scroll and an integrated copy button. */
export function CodeBlock({ code, label = '复制代码', className, onCopied }: CodeBlockProps) {
  const classes = [styles.codeBlock, className].filter(Boolean).join(' ')
  return (
    <div className={classes}>
      <pre className={styles.pre}>
        <code>{code}</code>
      </pre>
      <CopyButton
        text={code}
        label={label}
        variant="icon"
        className={styles.copy}
        onCopied={onCopied}
      />
    </div>
  )
}
