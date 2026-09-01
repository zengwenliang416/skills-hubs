import { FadeUp } from '@/components/amicro/FadeUp'

import styles from './Contribute.module.css'

const REPO = 'https://github.com/zengwenliang416/skills-hubs'

// Only link docs that exist on origin/main; web/README.md is unpublished until
// the web/server commits are pushed — restore a "前端架构" entry after that.
const DOC_LINKS = [
  { label: '收录原则', note: 'README.md', href: `${REPO}/blob/main/README.md` },
  { label: '发布流程', note: 'docs/RELEASING.md', href: `${REPO}/blob/main/docs/RELEASING.md` },
  { label: '仓库规范', note: 'AGENTS.md', href: `${REPO}/blob/main/AGENTS.md` },
] as const

/** Contribution and governance pointers; all links go to real repo docs. */
export function Contribute() {
  return (
    <section id="contribute" className={styles.section} aria-labelledby="contribute-title">
      <header className={styles.sectionHeader}>
        <h2 id="contribute-title" className={styles.title}>
          贡献与质量治理
        </h2>
        <p className={styles.description}>
          贡献通过仓库的 Pull Request 与发布流程进行，不设单独的在线提交入口。
        </p>
      </header>
      <FadeUp delay={0.1} yOffset={16}>
        <div className={styles.body}>
          <p className={styles.text}>
            每个技能在仓库中自包含一个目录，包含运行代码、SKILL.md、测试、安全说明与各自的
            LICENSE。提交前请先阅读收录原则与仓库规范，并通过仓库的 CI
            校验；版本发布只经由发布流水线完成，不从个人环境直接推送。
          </p>
          <ul className={styles.links}>
            {DOC_LINKS.map((link) => (
              <li key={link.href}>
                <a
                  className={styles.link}
                  href={link.href}
                  target="_blank"
                  rel="noopener noreferrer"
                  aria-label={`${link.label}（${link.note}，新窗口打开）`}
                >
                  <span className={styles.linkLabel}>{link.label}</span>
                  <span className={styles.linkNote}>{link.note}</span>
                  <span className={styles.linkArrow} aria-hidden="true">
                    ↗
                  </span>
                </a>
              </li>
            ))}
          </ul>
        </div>
      </FadeUp>
    </section>
  )
}
