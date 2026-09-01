import { MagneticButton } from '@/components/amicro/MagneticButton'

import styles from './Footer.module.css'

const REPO = 'https://github.com/zengwenliang416/skills-hubs'

const FOOTER_LINKS = [
  { label: '文档', href: `${REPO}/blob/main/README.md` },
  { label: '发布指南', href: `${REPO}/blob/main/docs/RELEASING.md` },
  { label: '源码', href: REPO },
] as const

/** About text, license note, and links to the repository docs. */
export function Footer() {
  return (
    <footer id="about" className={styles.footer}>
      <div className={styles.inner}>
        <div className={styles.about}>
          <h2 className={styles.heading}>关于 Skills Hub</h2>
          <p className={styles.text}>
            这里集中展示仓库中随版本发布的 Agent
            技能。每个技能目录下保留其原始许可证文件，使用许可以各技能自身的 LICENSE 为准。
          </p>
        </div>
        <nav className={styles.links} aria-label="仓库链接">
          {FOOTER_LINKS.map((link) => (
            <MagneticButton key={link.href}>
              <a
                className={styles.link}
                href={link.href}
                target="_blank"
                rel="noopener noreferrer"
                aria-label={`${link.label}（新窗口打开）`}
              >
                {link.label} ↗
              </a>
            </MagneticButton>
          ))}
        </nav>
      </div>
    </footer>
  )
}
