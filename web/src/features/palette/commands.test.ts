import { describe, expect, it } from 'vitest'

import { filterActions, matchesAction, paletteActions } from './commands'

describe('matchesAction', () => {
  it('matches by Chinese label substring', () => {
    const light = paletteActions.find((action) => action.id === 'theme-light')!
    expect(matchesAction(light, '浅色')).toBe(true)
    expect(matchesAction(light, '深色')).toBe(false)
  })

  it('matches by keyword', () => {
    const github = paletteActions.find((action) => action.id === 'open-github')!
    expect(matchesAction(github, 'github')).toBe(true)
    expect(matchesAction(github, '源码')).toBe(true)
  })

  it('is case-insensitive for latin keywords', () => {
    const catalog = paletteActions.find((action) => action.id === 'go-catalog')!
    expect(matchesAction(catalog, 'CATALOG')).toBe(true)
  })

  it('matches everything on an empty query', () => {
    for (const action of paletteActions) {
      expect(matchesAction(action, '')).toBe(true)
    }
  })
})

describe('filterActions', () => {
  it('returns all actions for an empty query', () => {
    expect(filterActions(paletteActions, '')).toHaveLength(paletteActions.length)
  })

  it('narrows to matching actions only', () => {
    const results = filterActions(paletteActions, '主题')
    expect(results.length).toBeGreaterThan(0)
    expect(results.every((action) => action.action.kind === 'theme')).toBe(true)
  })

  it('returns an empty array when nothing matches', () => {
    expect(filterActions(paletteActions, 'zzz-no-such-command')).toHaveLength(0)
  })
})
