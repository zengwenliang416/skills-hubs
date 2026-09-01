import { describe, expect, it } from 'vitest'

import realCatalogJson from '../../../../catalog.json'

import { safeExternalUrl, validateCatalog } from './schema'

function validSkill(overrides: Record<string, unknown> = {}): Record<string, unknown> {
  return {
    name: 'example-skill',
    title: 'Example Skill',
    version: '1.0.0',
    path: 'skills/example-skill',
    category: 'media',
    runtime: 'python>=3.9',
    npm: 'example-skill',
    license: 'MIT',
    status: 'active',
    description: 'Example description.',
    tags: ['tag'],
    highlights: ['highlight'],
    use_cases: ['use case'],
    install_methods: [{ label: 'npm', description: 'Install via npm.', command: 'npm i -g x' }],
    quick_start: { label: 'Run it', command: 'example --dry-run' },
    documentation_url: 'https://example.com/docs',
    repository_url: 'https://example.com/repo',
    ...overrides,
  }
}

function validCatalog(skills: unknown[] = [validSkill()]): Record<string, unknown> {
  return { schema_version: '1.1', updated_at: '2026-09-01', skills }
}

describe('validateCatalog', () => {
  it('accepts the real repository catalog.json', () => {
    const catalog = validateCatalog(realCatalogJson)
    expect(catalog.skills).toHaveLength(2)
    expect(catalog.skills.map((skill) => skill.name)).toEqual([
      'image-api-workbench',
      'amicro-universal-frontend-style',
    ])
  })

  it('rejects an empty skills array', () => {
    expect(() => validateCatalog(validCatalog([]))).toThrow(/skills/)
  })

  it('rejects a missing required string field', () => {
    const skill = validSkill()
    delete skill.description
    expect(() => validateCatalog(validCatalog([skill]))).toThrow(/description/)
  })

  it('rejects non-array tags', () => {
    const skill = validSkill({ tags: 'not-an-array' })
    expect(() => validateCatalog(validCatalog([skill]))).toThrow(/tags/)
  })

  it('rejects tags with empty strings', () => {
    const skill = validSkill({ tags: ['ok', '  '] })
    expect(() => validateCatalog(validCatalog([skill]))).toThrow(/tags/)
  })

  it('rejects a malformed quick_start', () => {
    const skill = validSkill({ quick_start: { label: 'Run it' } })
    expect(() => validateCatalog(validCatalog([skill]))).toThrow(/quick_start/)
  })

  it('rejects a non-http documentation_url', () => {
    const skill = validSkill({ documentation_url: 'javascript:alert(1)' })
    expect(() => validateCatalog(validCatalog([skill]))).toThrow(/documentation_url/)
  })

  it('rejects duplicate skill names', () => {
    const first = validSkill()
    const second = validSkill({ title: 'Duplicate Name' })
    expect(() => validateCatalog(validCatalog([first, second]))).toThrow(/duplicate/i)
  })

  it('accepts optional tests_url and security_notes_url when valid', () => {
    const skill = validSkill({
      tests_url: 'https://example.com/tests',
      security_notes_url: 'https://example.com/security',
    })
    const catalog = validateCatalog(validCatalog([skill]))
    expect(catalog.skills[0].tests_url).toBe('https://example.com/tests')
    expect(catalog.skills[0].security_notes_url).toBe('https://example.com/security')
  })

  it('rejects optional URLs with unsafe schemes', () => {
    const skill = validSkill({ tests_url: 'data:text/html,<script>' })
    expect(() => validateCatalog(validCatalog([skill]))).toThrow(/tests_url/)
  })
})

describe('safeExternalUrl', () => {
  it('accepts http and https URLs', () => {
    expect(safeExternalUrl('https://example.com/a?b=c')).toBe('https://example.com/a?b=c')
    expect(safeExternalUrl('http://example.com')).toBe('http://example.com')
  })

  it('rejects unsafe schemes, empty, and garbage values', () => {
    expect(safeExternalUrl('javascript:alert(1)')).toBeNull()
    expect(safeExternalUrl('data:text/html,<b>x</b>')).toBeNull()
    expect(safeExternalUrl('file:///etc/passwd')).toBeNull()
    expect(safeExternalUrl('')).toBeNull()
    expect(safeExternalUrl('not a url')).toBeNull()
    expect(safeExternalUrl(undefined)).toBeNull()
    expect(safeExternalUrl(null)).toBeNull()
  })
})
