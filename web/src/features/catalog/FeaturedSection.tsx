import { useCallback, useState } from 'react'

import { CardCarousel } from '@/components/amicro/CardCarousel'
import { FadeIn } from '@/components/amicro/FadeIn'

import { skills } from './data'
import styles from './FeaturedSection.module.css'
import { SkillCard } from './SkillCard'
import { SkillDetailDialog } from './SkillDetailDialog'
import type { Skill } from './types'

/**
 * Fanned "featured browse" section. Any slide count works (currently 2);
 * prev/next disable at the ends and side cards come to the front on click.
 */
export function FeaturedSection() {
  const [selectedSkill, setSelectedSkill] = useState<Skill | null>(null)
  const closeDialog = useCallback(() => setSelectedSkill(null), [])

  return (
    <section className={styles.section} aria-labelledby="featured-title">
      <header className={styles.sectionHeader}>
        <h2 id="featured-title" className={styles.title}>
          精选浏览
        </h2>
        <p className={styles.description}>
          以扇形卡片架翻阅技能：点击两侧卡片将其移到前景，点击前景卡片查看完整详情。
        </p>
      </header>
      <FadeIn duration={0.6}>
        <CardCarousel
          label="精选技能卡片架"
          count={skills.length}
          getSlideLabel={(index) => skills[index].title}
          renderSlide={(index, isActive) => (
            <SkillCard
              skill={skills[index]}
              onOpen={setSelectedSkill}
              tabIndex={isActive ? 0 : -1}
            />
          )}
        />
      </FadeIn>
      {selectedSkill ? <SkillDetailDialog skill={selectedSkill} onClose={closeDialog} /> : null}
    </section>
  )
}
