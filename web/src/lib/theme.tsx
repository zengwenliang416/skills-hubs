import { createContext, useCallback, useContext, useLayoutEffect, useMemo, useState } from 'react'
import type { ReactNode } from 'react'

import { useMediaQuery } from './useMediaQuery'

export type ThemeSetting = 'light' | 'dark' | 'auto'
export type ResolvedTheme = 'light' | 'dark'

// Keep in sync with the pre-paint script in index.html.
const STORAGE_KEY = 'skills-hub-theme'
const THEME_ORDER: readonly ThemeSetting[] = ['light', 'dark', 'auto']

interface ThemeContextValue {
  theme: ThemeSetting
  resolvedTheme: ResolvedTheme
  setTheme: (theme: ThemeSetting) => void
  cycleTheme: () => void
}

const ThemeContext = createContext<ThemeContextValue | null>(null)

function isThemeSetting(value: unknown): value is ThemeSetting {
  return value === 'light' || value === 'dark' || value === 'auto'
}

function readStoredTheme(): ThemeSetting {
  try {
    const stored = window.localStorage.getItem(STORAGE_KEY)
    if (isThemeSetting(stored)) {
      return stored
    }
  } catch {
    // Storage may be unavailable (private mode); fall back to auto.
  }
  return 'auto'
}

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [theme, setThemeState] = useState<ThemeSetting>(readStoredTheme)
  const systemDark = useMediaQuery('(prefers-color-scheme: dark)')
  const resolvedTheme: ResolvedTheme = theme === 'auto' ? (systemDark ? 'dark' : 'light') : theme

  // Layout effect so the attribute lands synchronously at commit time —
  // required for correct document.startViewTransition snapshot timing.
  useLayoutEffect(() => {
    // The token stylesheet resolves "auto" via prefers-color-scheme itself.
    document.documentElement.setAttribute('data-amicro-theme', theme)
    try {
      window.localStorage.setItem(STORAGE_KEY, theme)
    } catch {
      // Persisting is best-effort only.
    }
  }, [theme])

  const setTheme = useCallback((next: ThemeSetting) => {
    setThemeState(next)
  }, [])

  const cycleTheme = useCallback(() => {
    setThemeState((current) => {
      const index = THEME_ORDER.indexOf(current)
      return THEME_ORDER[(index + 1) % THEME_ORDER.length]
    })
  }, [])

  const value = useMemo<ThemeContextValue>(
    () => ({ theme, resolvedTheme, setTheme, cycleTheme }),
    [theme, resolvedTheme, setTheme, cycleTheme],
  )

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>
}

export function useTheme(): ThemeContextValue {
  const context = useContext(ThemeContext)
  if (!context) {
    throw new Error('useTheme must be used within a ThemeProvider')
  }
  return context
}
