import { useCallback, useState } from 'react'

import { Button } from '@/components/Button'
import { Chip } from '@/components/Chip'
import { FadeUp } from '@/components/amicro/FadeUp'
import { TiltCard } from '@/components/amicro/TiltCard'

import { categories, matchesSkill, skills } from './data'
import styles from './CatalogSection.module.css'
import { SkillCard } from './SkillCard'
import { SkillDetailDialog } from './SkillDetailDialog'
import type { Skill } from './types'

/** Search box + category chip filters + skill card grid. */
export function CatalogSection() {
  const [query, setQuery] = useState('')
  const [activeCategory, setActiveCategory] = useState<string>('all')
  const [selectedSkill, setSelectedSkill] = useState<Skill | null>(null)

  const closeDialog = useCallback(() => setSelectedSkill(null), [])
  const resetFilters = useCallback(() => {
    setQuery('')
    setActiveCategory('all')
  }, [])

  const normalizedQuery = query.trim().toLowerCase()
  const filteredSkills = skills.filter((skill) => {
    if (activeCategory !== 'all' && skill.category !== activeCategory) {
      return false
    }
    if (!normalizedQuery) {
      return true
    }
    return matchesSkill(skill, normalizedQuery)
  })

  return (
    <section id="catalog" className={styles.section} aria-labelledby="catalog-title">
      <header className={styles.sectionHeader}>
        <h2 id="catalog-title" className={styles.title}>
          技能目录
        </h2>
        <p className={styles.description}>
          按名称、标题或分类搜索，或使用分类筛选器浏览仓库中的全部技能。
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
              placeholder="输入名称、标题或分类…"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
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
        <div className={styles.empty} role="status">
          <p className={styles.emptyTitle}>没有找到匹配的技能</p>
          <p className={styles.emptyHint}>尝试更换关键词，或清除搜索与分类筛选。</p>
          <Button variant="primary" onClick={resetFilters}>
            清除筛选
          </Button>
        </div>
      )}

      {selectedSkill ? <SkillDetailDialog skill={selectedSkill} onClose={closeDialog} /> : null}
    </section>
  )
}
