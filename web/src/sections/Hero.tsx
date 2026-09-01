import { CountUp } from '@/components/CountUp'
import { FadeUp } from '@/components/amicro/FadeUp'
import { TextReveal } from '@/components/amicro/TextReveal'
import { catalog, categories, skills } from '@/features/catalog/data'

import styles from './Hero.module.css'

/** Page title with fluid type, a short pitch, and catalog metadata. */
export function Hero() {
  const stats = [
    { value: skills.length, label: '技能', numeric: true },
    { value: categories.length, label: '分类', numeric: true },
    { value: catalog.updated_at, label: '最近更新', numeric: false },
  ]

  return (
    <section id="top" className={styles.hero} aria-labelledby="hero-title">
      <FadeUp delay={0}>
        <p className={styles.kicker}>SKILLS HUB</p>
      </FadeUp>
      <h1 id="hero-title" className={styles.title}>
        <TextReveal text={'精心打造的\nAgent 技能集'} />
      </h1>
      <FadeUp delay={0.25}>
        <p className={styles.lede}>
          一组可复用、可组合的 Agent 技能，从仓库目录直接生成，随版本一同发布。
        </p>
      </FadeUp>
      <FadeUp delay={0.4}>
        <dl className={styles.stats}>
          {stats.map((stat) => (
            <div key={stat.label} className={styles.stat}>
              <dd className={styles.statValue}>
                {stat.numeric ? <CountUp value={stat.value as number} /> : stat.value}
              </dd>
              <dt className={styles.statLabel}>{stat.label}</dt>
            </div>
          ))}
        </dl>
      </FadeUp>
    </section>
  )
}
