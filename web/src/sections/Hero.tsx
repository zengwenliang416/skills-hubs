import type { FormEvent } from 'react'

import { CountUp } from '@/components/CountUp'
import { FadeUp } from '@/components/amicro/FadeUp'
import { TextReveal } from '@/components/amicro/TextReveal'
import { catalog, categories, skills } from '@/features/catalog/data'

import styles from './Hero.module.css'

interface HeroProps {
  /** Catalog query shared with CatalogSection (lifted to App). */
  query: string
  onQueryChange: (value: string) => void
}

/** Task-first page title, a catalog search form, CTAs, and catalog metadata. */
export function Hero({ query, onQueryChange }: HeroProps) {
  const stats = [
    { value: skills.length, label: '技能', numeric: true },
    { value: categories.length, label: '分类', numeric: true },
    { value: catalog.updated_at, label: '最近更新', numeric: false },
  ]

  // The query already lives in App state; submitting just brings the
  // (already filtered) catalog into view.
  const handleSearchSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    document.getElementById('catalog')?.scrollIntoView({ block: 'start' })
  }

  return (
    <section id="top" className={styles.hero} aria-labelledby="hero-title">
      <FadeUp delay={0}>
        <p className={styles.kicker}>开放 Agent Skills 注册库</p>
      </FadeUp>
      <h1 id="hero-title" className={styles.title}>
        <TextReveal text={'为真实任务找到\n可执行、可审阅的 Agent Skills'} />
      </h1>
      <FadeUp delay={0.25}>
        <p className={styles.lede}>
          按任务发现技能：查看安装方式、用例、许可证，以及文档与源码，采用前先理解它会做什么。
        </p>
      </FadeUp>
      <FadeUp delay={0.3}>
        <form
          className={styles.search}
          role="search"
          aria-label="搜索技能目录"
          onSubmit={handleSearchSubmit}
        >
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
            <label className={styles.visuallyHidden} htmlFor="hero-search">
              搜索任务、标签或包名
            </label>
            <input
              id="hero-search"
              type="search"
              className={styles.input}
              placeholder="搜索任务、标签或包名…"
              value={query}
              onChange={(event) => onQueryChange(event.target.value)}
            />
          </div>
          <button type="submit" className={styles.submit}>
            搜索
          </button>
        </form>
      </FadeUp>
      <FadeUp delay={0.35}>
        <div className={styles.actions}>
          <a className={styles.ctaPrimary} href="#catalog">
            浏览 Skills
          </a>
          <a className={styles.ctaSecondary} href="#contribute">
            贡献 Skill
          </a>
        </div>
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
