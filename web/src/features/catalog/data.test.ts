import { describe, expect, it } from 'vitest'

import { matchesSkill, skills } from './data'
import type { Skill } from './types'

function skillWith(overrides: Partial<Skill> = {}): Skill {
  const base = skills.find((skill) => skill.name === 'image-api-workbench') as Skill
  return { ...base, ...overrides }
}

describe('matchesSkill', () => {
  it('matches an empty query against every skill', () => {
    expect(skills.every((skill) => matchesSkill(skill, ''))).toBe(true)
  })

  it('matches by title', () => {
    expect(matchesSkill(skillWith(), 'image api workbench')).toBe(true)
  })

  it('matches by tag', () => {
    expect(matchesSkill(skillWith(), '图片生成')).toBe(true)
  })

  it('matches by use case', () => {
    expect(matchesSkill(skillWith(), '透明图标')).toBe(true)
  })

  it('matches by highlight', () => {
    expect(matchesSkill(skillWith(), '元数据旁车')).toBe(true)
  })

  it('matches by npm package name', () => {
    expect(matchesSkill(skillWith(), 'image-api-workbench')).toBe(true)
  })

  it('matches by runtime', () => {
    expect(matchesSkill(skillWith(), 'python>=3.9')).toBe(true)
  })

  it('matches by Chinese category label', () => {
    expect(matchesSkill(skillWith(), '媒体生成')).toBe(true)
  })

  it('is case-insensitive', () => {
    expect(matchesSkill(skillWith(), 'IMAGE-API-WORKBENCH')).toBe(true)
    expect(matchesSkill(skillWith(), 'GPT IMAGE')).toBe(true)
  })

  it('rejects a query present in no searched field', () => {
    expect(matchesSkill(skillWith(), '不存在的词')).toBe(false)
  })
})
