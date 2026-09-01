import { FadeUp } from '@/components/amicro/FadeUp'

import styles from './HowItWorks.module.css'

const STEPS = [
  {
    label: '发现',
    description: '按任务、标签或包名搜索，找到与手头工作匹配的技能。',
  },
  {
    label: '评估',
    description: '查看用例、许可证、测试与安全说明，先理解它会做什么。',
  },
  {
    label: '安装',
    description: '复制 npm 或目录安装命令，按技能的安装说明执行。',
  },
  {
    label: '开始使用',
    description: '按快速开始做一次 dry-run，确认行为符合预期再正式采用。',
  },
] as const

/** Static four-step onboarding: discover → evaluate → install → dry-run. */
export function HowItWorks() {
  return (
    <section id="how-it-works" className={styles.section} aria-labelledby="how-it-works-title">
      <header className={styles.sectionHeader}>
        <h2 id="how-it-works-title" className={styles.title}>
          如何开始使用
        </h2>
        <p className={styles.description}>从发现到第一次运行，每个技能都遵循同样的四步路径。</p>
      </header>
      <ol className={styles.steps}>
        {STEPS.map((step, index) => (
          <FadeUp
            key={step.label}
            className={styles.stepItem}
            delay={Math.min(index, 6) * 0.07}
            yOffset={16}
          >
            <li className={styles.step}>
              <span className={styles.stepNumber} aria-hidden="true">
                {index + 1}
              </span>
              <h3 className={styles.stepLabel}>{step.label}</h3>
              <p className={styles.stepDescription}>{step.description}</p>
            </li>
          </FadeUp>
        ))}
      </ol>
    </section>
  )
}
