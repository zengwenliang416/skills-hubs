import { MagneticButton } from '@/components/amicro/MagneticButton'

import styles from './Footer.module.css'

/** About text, license note, and the repository link. */
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
        <MagneticButton>
          <a
            className={styles.link}
            href="https://github.com/zengwenliang416/skills-hubs"
            target="_blank"
            rel="noreferrer"
          >
            GitHub 仓库 ↗
          </a>
        </MagneticButton>
      </div>
    </footer>
  )
}
