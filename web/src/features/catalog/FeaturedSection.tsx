import { useCallback, useState } from 'react'

import { CardCarousel } from '@/components/amicro/CardCarousel'
import { FadeIn } from '@/components/amicro/FadeIn'

import { skills } from './data'
import styles from './FeaturedSection.module.css'
import { SkillCard } from './SkillCard'
import { SkillDetailDialog } from './SkillDetailDialog'
import type { Skill } from './types'

/**
 * Task-first "browse by task" section. Each slide pairs the skill's real
 * first use case ("我要…") with its card; prev/next disable at the ends and
 * side cards come to the front on click.
 */
export function FeaturedSection() {
  const [selectedSkill, setSelectedSkill] = useState<Skill | null>(null)
  const closeDialog = useCallback(() => setSelectedSkill(null), [])

  return (
    <section id="featured" className={styles.section} aria-labelledby="featured-title">
      <header className={styles.sectionHeader}>
        <h2 id="featured-title" className={styles.title}>
          按任务发现
        </h2>
        <p className={styles.description}>
          从你要完成的任务出发：每张卡片对应一个真实用例，点击前景卡片查看完整详情。
        </p>
      </header>
      <FadeIn duration={0.6}>
        <CardCarousel
          label="按任务浏览技能"
          count={skills.length}
          getSlideLabel={(index) => skills[index].title}
          renderSlide={(index, isActive) => {
            const skill = skills[index]
            // Trim the trailing full stop so the "我要…" line reads naturally.
            const task = (skill.use_cases[0] ?? '').replace(/。$/, '')
            return (
              <div className={styles.slide}>
                <p className={styles.taskIntro}>我要{task}</p>
                <SkillCard skill={skill} onOpen={setSelectedSkill} tabIndex={isActive ? 0 : -1} />
              </div>
            )
          }}
        />
      </FadeIn>
      {selectedSkill ? <SkillDetailDialog skill={selectedSkill} onClose={closeDialog} /> : null}
    </section>
  )
}
