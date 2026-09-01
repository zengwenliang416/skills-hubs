import { useCallback, useEffect, useId, useRef, useState } from 'react'
import type { ReactNode, SyntheticEvent } from 'react'

import { Chip } from '@/components/Chip'
import { CodeBlock } from '@/components/CodeBlock'
import { IconButton } from '@/components/IconButton'
import { useMediaQuery } from '@/lib/useMediaQuery'

import { reportSkillEvent } from './analytics'
import { categoryLabel, skillLinks, statusLabel } from './data'
import { InstallMethodCard } from './InstallMethodCard'
import styles from './SkillDetailDialog.module.css'
import type { Skill } from './types'

interface SkillDetailDialogProps {
  skill: Skill
  onClose: () => void
}

// Safety net slightly beyond the 180ms exit animation, in case animationend never fires.
const CLOSE_FALLBACK_MS = 300

const UNDECLARED = '未声明'

interface TrustRow {
  term: string
  value: ReactNode
  /** Monospace value for identifiers, versions and paths. */
  mono?: boolean
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

  // A different skill reuses the same dialog: start reading from the top.
  useEffect(() => {
    const dialog = dialogRef.current
    if (dialog) {
      dialog.scrollTop = 0
    }
  }, [skill.name])

  // Intercept Esc so React state stays the single source of truth for closing.
  const handleCancel = (event: SyntheticEvent<HTMLDialogElement>) => {
    event.preventDefault()
    requestClose()
  }

  const links = skillLinks(skill)
  // Deterministic registry URL derived from the declared package name.
  const npmPackageUrl = `https://www.npmjs.com/package/${skill.npm}`

  /** Plain-text external link: new-window aria label, optional best-effort reporting. */
  const renderExternalLink = (
    href: string,
    label: string,
    ariaLabel: string,
    onClick?: () => void,
  ): ReactNode => (
    <a
      className={styles.valueLink}
      href={href}
      target="_blank"
      rel="noopener noreferrer"
      aria-label={ariaLabel}
      onClick={onClick}
    >
      {label}
      <span aria-hidden="true"> ↗</span>
    </a>
  )

  const undeclared = <span className={styles.undeclared}>{UNDECLARED}</span>

  const trustRows: TrustRow[] = [
    { term: '名称', value: skill.name, mono: true },
    { term: '版本', value: `v${skill.version}`, mono: true },
    { term: '路径', value: skill.path, mono: true },
    { term: '运行时', value: skill.runtime, mono: true },
    {
      term: 'npm 包',
      value: renderExternalLink(
        npmPackageUrl,
        skill.npm,
        `查看 npm 包 ${skill.npm}（在新窗口打开）`,
      ),
      mono: true,
    },
    { term: '许可证', value: skill.license, mono: true },
    {
      term: '文档',
      value: links.documentationUrl
        ? renderExternalLink(links.documentationUrl, '查看文档', '查看文档（在新窗口打开）', () =>
            reportSkillEvent(skill.name, 'documentation_click'),
          )
        : undeclared,
    },
    {
      term: '源码',
      value: links.repositoryUrl
        ? renderExternalLink(links.repositoryUrl, '查看源码', '查看源码（在新窗口打开）', () =>
            reportSkillEvent(skill.name, 'repository_click'),
          )
        : undeclared,
    },
    {
      term: '测试',
      value: links.testsUrl
        ? renderExternalLink(links.testsUrl, '查看测试', '查看测试（在新窗口打开）')
        : undeclared,
    },
    {
      term: '安全说明',
      value: links.securityNotesUrl
        ? renderExternalLink(links.securityNotesUrl, '查看安全说明', '查看安全说明（在新窗口打开）')
        : undeclared,
    },
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
      {skill.tags.length > 0 ? (
        <div className={styles.tags} aria-label="技能标签">
          {skill.tags.map((tag) => (
            <Chip key={tag}>{tag}</Chip>
          ))}
        </div>
      ) : null}

      <section className={styles.sectionBlock} aria-labelledby={`${titleId}-overview`}>
        <h4 id={`${titleId}-overview`} className={styles.sectionTitle}>
          概述
        </h4>
        {skill.description ? <p className={styles.description}>{skill.description}</p> : null}
        {skill.highlights.length > 0 ? (
          <div className={styles.highlightGroup}>
            <h5 className={styles.subTitle}>核心亮点</h5>
            <ul className={styles.featureList}>
              {skill.highlights.map((highlight) => (
                <li key={highlight}>{highlight}</li>
              ))}
            </ul>
          </div>
        ) : null}
      </section>

      {skill.use_cases.length > 0 ? (
        <section className={styles.sectionBlock} aria-labelledby={`${titleId}-use-cases`}>
          <h4 id={`${titleId}-use-cases`} className={styles.sectionTitle}>
            适用场景
          </h4>
          <ul className={styles.featureList}>
            {skill.use_cases.map((useCase) => (
              <li key={useCase}>{useCase}</li>
            ))}
          </ul>
        </section>
      ) : null}

      {skill.install_methods.length > 0 ? (
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
      ) : null}

      <section className={styles.sectionBlock} aria-labelledby={`${titleId}-quick-start`}>
        <h4 id={`${titleId}-quick-start`} className={styles.sectionTitle}>
          快速开始
        </h4>
        <p className={styles.quickStartLabel}>{skill.quick_start.label}</p>
        <CodeBlock
          code={skill.quick_start.command}
          label="复制快速开始命令"
          className={styles.blockCode}
          onCopied={() => reportSkillEvent(skill.name, 'install_copy')}
        />
      </section>

      <section className={styles.sectionBlock} aria-labelledby={`${titleId}-trust`}>
        <h4 id={`${titleId}-trust`} className={styles.sectionTitle}>
          信任与质量
        </h4>
        <dl className={styles.fields}>
          {trustRows.map((row) => (
            <div key={row.term} className={styles.fieldRow}>
              <dt className={styles.term}>{row.term}</dt>
              <dd className={row.mono ? styles.value : styles.valuePlain}>{row.value}</dd>
            </div>
          ))}
        </dl>
      </section>
    </dialog>
  )
}
