import { useCallback, useEffect, useId, useRef, useState } from 'react'
import type { SyntheticEvent } from 'react'

import { Chip } from '@/components/Chip'
import { IconButton } from '@/components/IconButton'
import { useMediaQuery } from '@/lib/useMediaQuery'

import { reportSkillEvent } from './analytics'
import { categoryLabel, statusLabel } from './data'
import styles from './SkillDetailDialog.module.css'
import type { InstallMethod, Skill } from './types'

interface SkillDetailDialogProps {
  skill: Skill
  onClose: () => void
}

// Safety net slightly beyond the 180ms exit animation, in case animationend never fires.
const CLOSE_FALLBACK_MS = 300
const COPY_FEEDBACK_MS = 1500

type CopyState = 'idle' | 'copied' | 'failed'

/** Clipboard API with an execCommand fallback; returns success. */
async function copyText(text: string): Promise<boolean> {
  try {
    await navigator.clipboard.writeText(text)
    return true
  } catch {
    let textarea: HTMLTextAreaElement | null = null
    try {
      textarea = document.createElement('textarea')
      textarea.value = text
      textarea.style.position = 'fixed'
      textarea.style.opacity = '0'
      document.body.appendChild(textarea)
      textarea.select()
      return document.execCommand('copy')
    } catch {
      return false
    } finally {
      textarea?.remove()
    }
  }
}

interface InstallMethodCardProps {
  method: InstallMethod
  skillName: string
}

function InstallMethodCard({ method, skillName }: InstallMethodCardProps) {
  const copyTimerRef = useRef<number | undefined>(undefined)
  const [copyState, setCopyState] = useState<CopyState>('idle')

  useEffect(
    () => () => {
      window.clearTimeout(copyTimerRef.current)
    },
    [],
  )

  const handleCopy = async () => {
    if (!method.command) {
      return
    }
    const ok = await copyText(method.command)
    setCopyState(ok ? 'copied' : 'failed')
    window.clearTimeout(copyTimerRef.current)
    copyTimerRef.current = window.setTimeout(() => setCopyState('idle'), COPY_FEEDBACK_MS)
    if (ok) {
      reportSkillEvent(skillName, 'install_copy')
    }
  }

  return (
    <article className={styles.installMethod}>
      <div>
        <h4 className={styles.installTitle}>{method.label}</h4>
        <p className={styles.installDescription}>{method.description}</p>
      </div>
      {method.command ? (
        <div className={styles.commandRow}>
          <code className={styles.command}>{method.command}</code>
          <IconButton
            label={copyState === 'copied' ? '已复制' : `复制${method.label}命令`}
            className={styles.copyButton}
            onClick={handleCopy}
          >
            {copyState === 'copied' ? (
              <svg
                key="check"
                className={styles.copyIcon}
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
            ) : (
              <svg
                key="clipboard"
                className={styles.copyIcon}
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
          <span
            className={styles.copyFeedback}
            data-tone={copyState === 'failed' ? 'failed' : undefined}
            role="status"
          >
            {copyState === 'copied' ? '已复制' : copyState === 'failed' ? '复制失败' : ''}
          </span>
        </div>
      ) : (
        <p className={styles.manualNote}>该方法由宿主目录或发布包完成，不提供虚构命令。</p>
      )}
    </article>
  )
}

/** Native <dialog>: modal semantics, Esc cancel, backdrop click, focus return. */
export function SkillDetailDialog({ skill, onClose }: SkillDetailDialogProps) {
  const dialogRef = useRef<HTMLDialogElement>(null)
  const closingRef = useRef(false)
  const reportedSkillRef = useRef<string | null>(null)
  const [closing, setClosing] = useState(false)
  const titleId = useId()
  const reducedMotion = useMediaQuery('(prefers-reduced-motion: reduce)')

  const finishClose = useCallback(() => {
    const dialog = dialogRef.current
    if (dialog?.open) {
      dialog.close()
    }
    onClose()
  }, [onClose])

  // Play the exit animation first; only then close for real and return focus.
  const requestClose = useCallback(() => {
    if (closingRef.current) {
      return
    }
    const dialog = dialogRef.current
    if (!dialog || reducedMotion) {
      finishClose()
      return
    }
    closingRef.current = true
    setClosing(true)
    let settled = false
    const settle = () => {
      if (settled) {
        return
      }
      settled = true
      window.clearTimeout(fallbackTimer)
      dialog.removeEventListener('animationend', onAnimationEnd)
      finishClose()
    }
    const onAnimationEnd = (event: AnimationEvent) => {
      if (event.target === dialog) {
        settle()
      }
    }
    const fallbackTimer = window.setTimeout(settle, CLOSE_FALLBACK_MS)
    dialog.addEventListener('animationend', onAnimationEnd)
  }, [reducedMotion, finishClose])

  useEffect(() => {
    const dialog = dialogRef.current
    if (!dialog) {
      return
    }
    if (!dialog.open) {
      dialog.showModal()
    }
    // Clicking the backdrop (the dialog element itself) closes the dialog.
    const handleBackdropClick = (event: MouseEvent) => {
      if (event.target === dialog) {
        requestClose()
      }
    }
    dialog.addEventListener('click', handleBackdropClick)
    return () => dialog.removeEventListener('click', handleBackdropClick)
  }, [requestClose])

  useEffect(() => {
    if (reportedSkillRef.current === skill.name) {
      return
    }
    reportedSkillRef.current = skill.name
    reportSkillEvent(skill.name, 'skill_view')
  }, [skill.name])

  // Intercept Esc so React state stays the single source of truth for closing.
  const handleCancel = (event: SyntheticEvent<HTMLDialogElement>) => {
    event.preventDefault()
    requestClose()
  }

  const fields: Array<{ term: string; value: string }> = [
    { term: '名称', value: skill.name },
    { term: '版本', value: `v${skill.version}` },
    { term: '路径', value: skill.path },
    { term: '运行时', value: skill.runtime },
    { term: 'npm 包', value: skill.npm },
    { term: '许可证', value: skill.license },
  ]

  const dialogClass = closing ? `${styles.dialog} ${styles.closing}` : styles.dialog

  return (
    <dialog
      ref={dialogRef}
      className={dialogClass}
      aria-labelledby={titleId}
      onCancel={handleCancel}
    >
      <div className={styles.header}>
        <div className={styles.heading}>
          <h3 id={titleId} className={styles.title}>
            {skill.title}
          </h3>
          <div className={styles.badges}>
            <Chip>{categoryLabel(skill.category)}</Chip>
            <Chip tone={skill.status === 'active' ? 'success' : 'neutral'} showDot>
              {statusLabel(skill.status)}
            </Chip>
          </div>
        </div>
        <IconButton label="关闭详情" onClick={requestClose}>
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
            <path
              d="M4 4l8 8M12 4l-8 8"
              stroke="currentColor"
              strokeWidth="1.8"
              strokeLinecap="round"
            />
          </svg>
        </IconButton>
      </div>
      <p className={styles.description}>{skill.description}</p>
      <div className={styles.tags} aria-label="技能标签">
        {skill.tags.map((tag) => (
          <Chip key={tag}>{tag}</Chip>
        ))}
      </div>

      <div className={styles.contentGrid}>
        <section className={styles.contentSection} aria-labelledby={`${titleId}-highlights`}>
          <h4 id={`${titleId}-highlights`} className={styles.sectionTitle}>
            核心能力
          </h4>
          <ul className={styles.featureList}>
            {skill.highlights.map((highlight) => (
              <li key={highlight}>{highlight}</li>
            ))}
          </ul>
        </section>
        <section className={styles.contentSection} aria-labelledby={`${titleId}-use-cases`}>
          <h4 id={`${titleId}-use-cases`} className={styles.sectionTitle}>
            适用场景
          </h4>
          <ul className={styles.featureList}>
            {skill.use_cases.map((useCase) => (
              <li key={useCase}>{useCase}</li>
            ))}
          </ul>
        </section>
      </div>

      <section className={styles.sectionBlock} aria-labelledby={`${titleId}-install`}>
        <h4 id={`${titleId}-install`} className={styles.sectionTitle}>
          安装方式
        </h4>
        <div className={styles.installList}>
          {skill.install_methods.map((method) => (
            <InstallMethodCard key={method.label} method={method} skillName={skill.name} />
          ))}
        </div>
      </section>

      <section className={styles.quickStart} aria-labelledby={`${titleId}-quick-start`}>
        <div>
          <h4 id={`${titleId}-quick-start`} className={styles.sectionTitle}>
            快速开始
          </h4>
          <p className={styles.quickStartLabel}>{skill.quick_start.label}</p>
        </div>
        <pre className={styles.quickStartCode}>
          <code>{skill.quick_start.command}</code>
        </pre>
      </section>

      <div className={styles.lowerGrid}>
        <dl className={styles.fields}>
          {fields.map((field) => (
            <div key={field.term} className={styles.fieldRow}>
              <dt className={styles.term}>{field.term}</dt>
              <dd className={styles.value}>{field.value}</dd>
            </div>
          ))}
        </dl>
        <nav className={styles.actions} aria-label="技能资源">
          <a
            className={styles.resourceLink}
            href={skill.documentation_url}
            target="_blank"
            rel="noreferrer"
            onClick={() => reportSkillEvent(skill.name, 'documentation_click')}
          >
            阅读完整文档
            <span aria-hidden="true">↗</span>
          </a>
          <a
            className={styles.resourceLink}
            href={skill.repository_url}
            target="_blank"
            rel="noreferrer"
            onClick={() => reportSkillEvent(skill.name, 'repository_click')}
          >
            查看 Skill 源码
            <span aria-hidden="true">↗</span>
          </a>
        </nav>
      </div>
    </dialog>
  )
}
