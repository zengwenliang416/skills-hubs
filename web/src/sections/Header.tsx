import { flushSync } from 'react-dom'

import { IconButton } from '@/components/IconButton'
import { MagneticButton } from '@/components/amicro/MagneticButton'
import { useMediaQuery } from '@/lib/useMediaQuery'
import { useScrollProgress } from '@/lib/useScrollProgress'
import { useTheme } from '@/lib/theme'
import type { ThemeSetting } from '@/lib/theme'

import styles from './Header.module.css'

const THEME_LABELS: Record<ThemeSetting, string> = {
  light: '浅色',
  dark: '深色',
  auto: '跟随系统',
}

/** Compact line icon for the current theme setting. */
function ThemeIcon({ theme }: { theme: ThemeSetting }) {
  const shared = {
    width: 16,
    height: 16,
    viewBox: '0 0 16 16',
    fill: 'none',
    'aria-hidden': true,
    className: styles.themeIcon,
  } as const

  if (theme === 'light') {
    return (
      <svg {...shared}>
        <circle cx="8" cy="8" r="3.25" stroke="currentColor" strokeWidth="1.6" />
        <path
          d="M8 1.5v2M8 12.5v2M1.5 8h2M12.5 8h2M3.4 3.4l1.4 1.4M11.2 11.2l1.4 1.4M12.6 3.4l-1.4 1.4M4.8 11.2l-1.4 1.4"
          stroke="currentColor"
          strokeWidth="1.6"
          strokeLinecap="round"
        />
      </svg>
    )
  }

  if (theme === 'dark') {
    return (
      <svg {...shared}>
        <path
          d="M13.5 9.5A6 6 0 0 1 6.5 2.5a6 6 0 1 0 7 7Z"
          stroke="currentColor"
          strokeWidth="1.6"
          strokeLinejoin="round"
        />
      </svg>
    )
  }

  return (
    <svg {...shared}>
      <circle cx="8" cy="8" r="6" stroke="currentColor" strokeWidth="1.6" />
      <path d="M8 2a6 6 0 0 1 0 12V2Z" fill="currentColor" />
    </svg>
  )
}

interface HeaderProps {
  onOpenPalette: () => void
}

/** Floating glass pill navigation with search, theme toggle, and scroll progress. */
export function Header({ onOpenPalette }: HeaderProps) {
  const { theme, cycleTheme } = useTheme()
  const scrollProgress = useScrollProgress()
  const reducedMotion = useMediaQuery('(prefers-reduced-motion: reduce)')

  // Signature circular reveal: grow the new theme from the toggle's position.
  const handleThemeClick = (event: React.MouseEvent<HTMLButtonElement>) => {
    if (reducedMotion || typeof document.startViewTransition !== 'function') {
      cycleTheme()
      return
    }
    const rect = event.currentTarget.getBoundingClientRect()
    const root = document.documentElement
    const revealX = rect.left + rect.width / 2
    const revealY = rect.top + rect.height / 2
    const revealRadius = Math.hypot(
      Math.max(revealX, window.innerWidth - revealX),
      Math.max(revealY, window.innerHeight - revealY),
    )
    root.style.setProperty('--theme-reveal-x', `${revealX}px`)
    root.style.setProperty('--theme-reveal-y', `${revealY}px`)
    root.style.setProperty('--theme-reveal-radius', `${revealRadius}px`)
    document.startViewTransition(() => {
      // flushSync forces the commit (and the layout effect that flips
      // data-amicro-theme) before the new snapshot is captured.
      flushSync(() => cycleTheme())
    })
  }

  return (
    <header className={styles.header}>
      {/* State indicator only, so it stays visible under reduced motion. */}
      <span
        className={styles.progress}
        style={{ transform: `scaleX(${scrollProgress})` }}
        aria-hidden="true"
      />
      <nav className={styles.nav} aria-label="站点导航">
        <a className={styles.brand} href="#top">
          Skills Hub
        </a>
        <div className={styles.links}>
          <a className={styles.link} href="#catalog">
            目录
          </a>
          <a className={styles.link} href="#about">
            关于
          </a>
        </div>
        <IconButton id="skill-command-trigger" label="搜索技能（⌘K）" onClick={onOpenPalette}>
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
            <circle cx="7" cy="7" r="4.5" stroke="currentColor" strokeWidth="1.8" />
            <path
              d="M10.5 10.5L14 14"
              stroke="currentColor"
              strokeWidth="1.8"
              strokeLinecap="round"
            />
          </svg>
        </IconButton>
        <MagneticButton>
          <IconButton label={`切换主题（当前：${THEME_LABELS[theme]}）`} onClick={handleThemeClick}>
            {/* key forces a remount so the swap animation replays on every change. */}
            <ThemeIcon key={theme} theme={theme} />
          </IconButton>
        </MagneticButton>
      </nav>
    </header>
  )
}
