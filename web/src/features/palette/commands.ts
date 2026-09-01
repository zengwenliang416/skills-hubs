import type { ThemeSetting } from '@/lib/theme'

/**
 * Action commands for the command palette. Pure data + matching logic so the
 * palette component only wires each id to its real effect (scroll, theme,
 * navigation). Labels are Chinese UI copy; keywords extend the match surface.
 */

export type PaletteActionId =
  | { kind: 'anchor'; targetId: string }
  | { kind: 'theme'; theme: ThemeSetting }
  | { kind: 'external'; url: string; newTab: boolean }

export interface PaletteAction {
  id: string
  label: string
  /** Secondary hint shown on the right of the option. */
  hint: string
  keywords: string[]
  action: PaletteActionId
}

export const paletteActions: readonly PaletteAction[] = [
  {
    id: 'go-catalog',
    label: '前往目录',
    hint: '#catalog',
    keywords: ['目录', '技能列表', 'catalog', '搜索'],
    action: { kind: 'anchor', targetId: 'catalog' },
  },
  {
    id: 'go-how-it-works',
    label: '前往如何开始',
    hint: '#how-it-works',
    keywords: ['如何开始', '入门', '教程', 'how'],
    action: { kind: 'anchor', targetId: 'how-it-works' },
  },
  {
    id: 'go-contribute',
    label: '前往贡献指南',
    hint: '#contribute',
    keywords: ['贡献', '指南', '提交', 'contribute'],
    action: { kind: 'anchor', targetId: 'contribute' },
  },
  {
    id: 'go-featured',
    label: '查看精选',
    hint: '#featured',
    keywords: ['精选', '推荐', '任务', 'featured'],
    action: { kind: 'anchor', targetId: 'featured' },
  },
  {
    id: 'theme-light',
    label: '切换为浅色主题',
    hint: '外观',
    keywords: ['浅色', '亮色', '主题', 'light', 'theme'],
    action: { kind: 'theme', theme: 'light' },
  },
  {
    id: 'theme-dark',
    label: '切换为深色主题',
    hint: '外观',
    keywords: ['深色', '暗色', '主题', 'dark', 'theme'],
    action: { kind: 'theme', theme: 'dark' },
  },
  {
    id: 'theme-auto',
    label: '跟随系统主题',
    hint: '外观',
    keywords: ['系统', '自动', '主题', 'auto', 'system', 'theme'],
    action: { kind: 'theme', theme: 'auto' },
  },
  {
    id: 'open-github',
    label: '打开 GitHub 源码仓库',
    hint: '新标签页',
    keywords: ['github', '源码', '仓库', '开源'],
    action: {
      kind: 'external',
      url: 'https://github.com/zengwenliang416/skills-hubs',
      newTab: true,
    },
  },
  {
    id: 'open-releasing',
    label: '查看发布指南',
    hint: 'RELEASING.md',
    keywords: ['发布', '指南', 'release', 'releasing', '文档'],
    action: {
      kind: 'external',
      url: 'https://github.com/zengwenliang416/skills-hubs/blob/main/docs/RELEASING.md',
      newTab: false,
    },
  },
]

/** Matches an action against a pre-normalized (trimmed, lowercased) query. */
export function matchesAction(action: PaletteAction, normalizedQuery: string): boolean {
  if (!normalizedQuery) {
    return true
  }
  const query = normalizedQuery.toLowerCase()
  const haystack = [action.label, action.hint, ...action.keywords].join(' ').toLowerCase()
  return haystack.includes(query)
}

/** Empty query returns every action so the palette is useful without typing. */
export function filterActions(
  actions: readonly PaletteAction[],
  normalizedQuery: string,
): PaletteAction[] {
  return actions.filter((action) => matchesAction(action, normalizedQuery))
}
