import { CodeBlock } from '@/components/CodeBlock'

import { reportSkillEvent } from './analytics'
import styles from './InstallMethodCard.module.css'
import type { InstallMethod } from './types'

interface InstallMethodCardProps {
  method: InstallMethod
  skillName: string
}

/** One install method: a copyable CodeBlock when a command exists, honest text otherwise. */
export function InstallMethodCard({ method, skillName }: InstallMethodCardProps) {
  return (
    <article className={styles.installMethod}>
      <div>
        <h4 className={styles.installTitle}>{method.label}</h4>
        <p className={styles.installDescription}>{method.description}</p>
      </div>
      {method.command ? (
        <CodeBlock
          code={method.command}
          label={`复制${method.label}命令`}
          onCopied={() => reportSkillEvent(skillName, 'install_copy')}
        />
      ) : (
        <p className={styles.manualNote}>该方法由宿主目录或发布包完成，不提供虚构命令。</p>
      )}
    </article>
  )
}
