import { useCallback, useEffect, useId, useRef, useState } from 'react'
import type { SyntheticEvent } from 'react'

import { categoryLabel, matchesSkill, skills } from '@/features/catalog/data'
import { SkillDetailDialog } from '@/features/catalog/SkillDetailDialog'
import type { Skill } from '@/features/catalog/types'

import styles from './CommandPalette.module.css'

interface CommandPaletteProps {
  onClose: () => void
}

/**
 * ⌘K command palette. Native <dialog> with the same discipline as
 * SkillDetailDialog: intercepted Esc, backdrop click, focus return to the
 * trigger. Selecting a skill closes the palette first, then opens the
 * detail dialog, so the two are never open at once and the focus chain
 * stays intact.
 */
export function CommandPalette({ onClose }: CommandPaletteProps) {
  const dialogRef = useRef<HTMLDialogElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)
  const returnFocusRef = useRef<HTMLElement | null>(null)
  const listId = useId()
  const [query, setQuery] = useState('')
  const [activeIndex, setActiveIndex] = useState(0)
  const [selectedSkill, setSelectedSkill] = useState<Skill | null>(null)

  const normalizedQuery = query.trim().toLowerCase()
  const results = skills.filter((skill) => matchesSkill(skill, normalizedQuery))
  const clampedIndex = Math.min(activeIndex, Math.max(results.length - 1, 0))

  // Every close path goes through the native close() so focus is restored.
  const closePalette = useCallback(() => {
    const dialog = dialogRef.current
    if (dialog?.open) {
      dialog.close()
    }
    onClose()
  }, [onClose])

  useEffect(() => {
    const dialog = dialogRef.current
    if (!dialog) {
      return
    }
    if (!returnFocusRef.current) {
      const activeElement =
        document.activeElement instanceof HTMLElement ? document.activeElement : null
      returnFocusRef.current =
        activeElement &&
        activeElement !== document.body &&
        activeElement !== document.documentElement
          ? activeElement
          : document.getElementById('skill-command-trigger')
    }
    if (!dialog.open) {
      dialog.showModal()
    }
    inputRef.current?.focus()

    // Clicking the backdrop (the dialog element itself) closes the palette.
    const handleBackdropClick = (event: MouseEvent) => {
      if (event.target === dialog) {
        closePalette()
      }
    }
    // ⌘K / Ctrl+K toggles only the palette itself. Once a skill is selected,
    // the palette stays mounted behind the detail dialog but is no longer open.
    const handleKeyDown = (event: KeyboardEvent) => {
      if (dialog.open && (event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 'k') {
        event.preventDefault()
        closePalette()
      }
    }
    dialog.addEventListener('click', handleBackdropClick)
    window.addEventListener('keydown', handleKeyDown)
    return () => {
      dialog.removeEventListener('click', handleBackdropClick)
      window.removeEventListener('keydown', handleKeyDown)
    }
  }, [closePalette])

  // Intercept Esc so React state stays the single source of truth for closing.
  const handleCancel = (event: SyntheticEvent<HTMLDialogElement>) => {
    event.preventDefault()
    closePalette()
  }

  // Close the palette first (focus returns to the trigger), then open detail.
  const handleSelect = (skill: Skill) => {
    const dialog = dialogRef.current
    if (dialog?.open) {
      dialog.close()
    }
    setSelectedSkill(skill)
  }

  const handleDetailClose = useCallback(() => {
    const returnFocus = returnFocusRef.current ?? document.getElementById('skill-command-trigger')
    setSelectedSkill(null)
    onClose()
    window.requestAnimationFrame(() => returnFocus?.focus())
  }, [onClose])

  const handleInputKeyDown = (event: React.KeyboardEvent<HTMLInputElement>) => {
    if (event.key === 'ArrowDown') {
      event.preventDefault()
      setActiveIndex((prev) => Math.min(prev + 1, results.length - 1))
    } else if (event.key === 'ArrowUp') {
      event.preventDefault()
      setActiveIndex((prev) => Math.max(prev - 1, 0))
    } else if (event.key === 'Enter') {
      event.preventDefault()
      const skill = results[clampedIndex]
      if (skill) {
        handleSelect(skill)
      }
    }
  }

  return (
    <>
      <dialog
        ref={dialogRef}
        className={styles.palette}
        aria-label="命令面板"
        onCancel={handleCancel}
      >
        <div className={styles.inputRow}>
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
            <circle cx="7" cy="7" r="4.5" stroke="currentColor" strokeWidth="1.8" />
            <path
              d="M10.5 10.5L14 14"
              stroke="currentColor"
              strokeWidth="1.8"
              strokeLinecap="round"
            />
          </svg>
          <input
            ref={inputRef}
            type="text"
            role="combobox"
            aria-expanded="true"
            aria-controls={listId}
            aria-activedescendant={results.length > 0 ? `${listId}-${clampedIndex}` : undefined}
            aria-label="搜索技能"
            className={styles.input}
            placeholder="输入名称、标题或分类…"
            value={query}
            onChange={(event) => {
              setQuery(event.target.value)
              setActiveIndex(0)
            }}
            onKeyDown={handleInputKeyDown}
          />
          <kbd className={styles.kbd}>esc</kbd>
        </div>

        {results.length > 0 ? (
          <ul className={styles.list} role="listbox" id={listId} aria-label="技能">
            {results.map((skill, index) => (
              <li
                key={skill.name}
                id={`${listId}-${index}`}
                role="option"
                aria-selected={index === clampedIndex}
                className={styles.option}
                data-active={index === clampedIndex ? 'true' : undefined}
                tabIndex={-1}
                onMouseEnter={() => setActiveIndex(index)}
                onKeyDown={(event) => {
                  if (event.key === 'Enter' || event.key === ' ') {
                    event.preventDefault()
                    handleSelect(skill)
                  }
                }}
                onClick={() => handleSelect(skill)}
              >
                <span className={styles.optionTitle}>{skill.title}</span>
                <span className={styles.optionMeta}>
                  v{skill.version} · {categoryLabel(skill.category)}
                </span>
              </li>
            ))}
          </ul>
        ) : (
          <div className={styles.empty} role="status">
            <p className={styles.emptyTitle}>没有找到匹配的技能</p>
            <p className={styles.emptyHint}>尝试更换关键词。</p>
          </div>
        )}
      </dialog>

      {selectedSkill ? (
        <SkillDetailDialog skill={selectedSkill} onClose={handleDetailClose} />
      ) : null}
    </>
  )
}
