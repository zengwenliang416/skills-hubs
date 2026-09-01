import { useCallback, useState } from 'react'

import { Button } from '@/components/Button'
import { Chip } from '@/components/Chip'
import { EmptyState } from '@/components/EmptyState'
import { FadeUp } from '@/components/amicro/FadeUp'
import { TiltCard } from '@/components/amicro/TiltCard'

import { categories, matchesSkill, skills } from './data'
import styles from './CatalogSection.module.css'
import { SkillCard } from './SkillCard'
import { SkillDetailDialog } from './SkillDetailDialog'
import type { Skill } from './types'

interface CatalogSectionProps {
  /** Query shared with the hero search form (lifted to App). */
  query: string
  onQueryChange: (value: string) => void
}

/** Search box + category chip filters + skill card grid. */
export function CatalogSection({ query, onQueryChange }: CatalogSectionProps) {
  const [activeCategory, setActiveCategory] = useState<string>('all')
  const [selectedSkill, setSelectedSkill] = useState<Skill | null>(null)

  const closeDialog = useCallback(() => setSelectedSkill(null), [])
  const clearQuery = useCallback(() => onQueryChange(''), [onQueryChange])
  const clearCategory = useCallback(() => setActiveCategory('all'), [])
  const resetFilters = useCallback(() => {
    onQueryChange('')
    setActiveCategory('all')
  }, [onQueryChange])

  const normalizedQuery = query.trim().toLowerCase()
  const hasQuery = normalizedQuery.length > 0
  const hasCategory = activeCategory !== 'all'
  const filtersActive = hasQuery || hasCategory

  const filteredSkills = skills.filter((skill) => {
    if (hasCategory && skill.category !== activeCategory) {
      return false
    }
    if (!normalizedQuery) {
      return true
    }
    return matchesSkill(skill, normalizedQuery)
  })

  const resultCount = filtersActive
    ? `共 ${filteredSkills.length} / ${skills.length} 个 Skill`
    : `${skills.length} 个 Skill`

  return (
    <section id="catalog" className={styles.section} aria-labelledby="catalog-title">
      <header className={styles.sectionHeader}>
        <h2 id="catalog-title" className={styles.title}>
          技能目录
        </h2>
        <p className={styles.description}>
          按名称、任务、标签或包名搜索，或使用分类筛选器浏览仓库中的全部技能。
        </p>
      </header>

      <div className={styles.controls}>
        <div className={styles.searchField}>
          <label className={styles.label} htmlFor="skill-search">
            搜索技能
          </label>
          <div className={styles.inputWrap}>
            <svg
              className={styles.searchIcon}
              width="16"
              height="16"
              viewBox="0 0 16 16"
              fill="none"
              aria-hidden="true"
            >
              <circle cx="7" cy="7" r="4.5" stroke="currentColor" strokeWidth="1.8" />
              <path
                d="M10.5 10.5L14 14"
                stroke="currentColor"
                strokeWidth="1.8"
                strokeLinecap="round"
              />
            </svg>
            <input
              id="skill-search"
              type="search"
              className={styles.input}
              placeholder="搜索名称、任务、标签或包名…"
              value={query}
              onChange={(event) => onQueryChange(event.target.value)}
            />
          </div>
        </div>

        <div className={styles.chips} role="group" aria-label="按分类筛选">
          <Chip selected={activeCategory === 'all'} onClick={() => setActiveCategory('all')}>
            全部 {skills.length}
          </Chip>
          {categories.map((category) => (
            <Chip
              key={category.id}
              selected={activeCategory === category.id}
              onClick={() => setActiveCategory(category.id)}
            >
              {category.label} {category.count}
            </Chip>
          ))}
        </div>
      </div>

      <div className={styles.resultRow}>
        {/* The visible count doubles as the polite live region. */}
        <p className={styles.resultCount} aria-live="polite">
          {resultCount}
        </p>
        {filtersActive ? (
          <Button variant="ghost" onClick={resetFilters}>
            一键清除
          </Button>
        ) : null}
      </div>

      {filteredSkills.length > 0 ? (
        <div className={styles.grid}>
          {filteredSkills.map((skill, index) => (
            // One-shot scroll-in entrance (fade-up), capped stagger for long lists.
            <FadeUp
              key={skill.name}
              className={styles.gridItem}
              delay={Math.min(index, 6) * 0.07}
              yOffset={16}
            >
              <TiltCard maxTilt={8}>
                <SkillCard skill={skill} onOpen={setSelectedSkill} />
              </TiltCard>
            </FadeUp>
          ))}
        </div>
      ) : (
        <EmptyState
          title="没有找到匹配的技能"
          description="尝试更换关键词，或使用下面的操作恢复浏览。"
        >
          {hasQuery ? (
            <Button variant="primary" onClick={clearQuery}>
              清除搜索
            </Button>
          ) : null}
          {hasCategory ? (
            <Button variant="primary" onClick={clearCategory}>
              清除分类筛选
            </Button>
          ) : null}
          <Button variant="ghost" onClick={resetFilters}>
            查看全部
          </Button>
          <a className={styles.guideLink} href="#contribute">
            贡献指南
          </a>
        </EmptyState>
      )}

      {selectedSkill ? <SkillDetailDialog skill={selectedSkill} onClose={closeDialog} /> : null}
    </section>
  )
}
