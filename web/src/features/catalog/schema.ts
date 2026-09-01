import type { Catalog, InstallMethod, QuickStart, Skill } from './types'

/**
 * Returns the URL only for http: and https: schemes, otherwise null.
 * Used to keep javascript:/data: URLs from catalog data out of hrefs.
 */
export function safeExternalUrl(value: string | undefined | null): string | null {
  if (!value) {
    return null
  }
  try {
    const url = new URL(value)
    return url.protocol === 'http:' || url.protocol === 'https:' ? value : null
  } catch {
    return null
  }
}

function fail(context: string, field: string, expectation: string): never {
  throw new Error(`Invalid catalog: ${context} field "${field}" ${expectation}`)
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
}

function requireNonEmptyString(
  record: Record<string, unknown>,
  field: string,
  context: string,
): string {
  const value = record[field]
  if (typeof value !== 'string' || value.trim() === '') {
    fail(context, field, 'must be a non-empty string')
  }
  return value
}

function requireStringArray(
  record: Record<string, unknown>,
  field: string,
  context: string,
): string[] {
  const value = record[field]
  if (
    !Array.isArray(value) ||
    value.some((item) => typeof item !== 'string' || item.trim() === '')
  ) {
    fail(context, field, 'must be an array of non-empty strings')
  }
  return value as string[]
}

function requireHttpUrl(record: Record<string, unknown>, field: string, context: string): string {
  const value = requireNonEmptyString(record, field, context)
  if (safeExternalUrl(value) === null) {
    fail(context, field, 'must be an http(s) URL')
  }
  return value
}

function optionalHttpUrl(
  record: Record<string, unknown>,
  field: string,
  context: string,
): string | undefined {
  const value = record[field]
  if (value === undefined) {
    return undefined
  }
  if (typeof value !== 'string' || value.trim() === '' || safeExternalUrl(value) === null) {
    fail(context, field, 'must be an http(s) URL when present')
  }
  return value
}

function validateInstallMethod(value: unknown, context: string): InstallMethod {
  const methodContext = `${context} install_methods[]`
  if (!isRecord(value)) {
    fail(methodContext, '(entry)', 'must be an object')
  }
  const method: InstallMethod = {
    label: requireNonEmptyString(value, 'label', methodContext),
    description: requireNonEmptyString(value, 'description', methodContext),
  }
  const command = value.command
  if (command !== undefined) {
    if (typeof command !== 'string' || command.trim() === '') {
      fail(methodContext, 'command', 'must be a non-empty string when present')
    }
    method.command = command
  }
  return method
}

function validateQuickStart(value: unknown, context: string): QuickStart {
  const quickStartContext = `${context} quick_start`
  if (!isRecord(value)) {
    fail(quickStartContext, '(entry)', 'must be an object')
  }
  return {
    label: requireNonEmptyString(value, 'label', quickStartContext),
    command: requireNonEmptyString(value, 'command', quickStartContext),
  }
}

const REQUIRED_TEXT_FIELDS = [
  'name',
  'title',
  'version',
  'path',
  'category',
  'runtime',
  'npm',
  'license',
  'status',
  'description',
] as const

function validateSkill(value: unknown, index: number): Skill {
  const context =
    isRecord(value) && typeof value.name === 'string' && value.name
      ? `skill "${value.name}"`
      : `skills[${index}]`
  if (!isRecord(value)) {
    fail(`skills[${index}]`, '(entry)', 'must be an object')
  }
  const skill: Record<string, unknown> = {}
  for (const field of REQUIRED_TEXT_FIELDS) {
    skill[field] = requireNonEmptyString(value, field, context)
  }
  skill.tags = requireStringArray(value, 'tags', context)
  skill.highlights = requireStringArray(value, 'highlights', context)
  skill.use_cases = requireStringArray(value, 'use_cases', context)
  const installMethods = value.install_methods
  if (!Array.isArray(installMethods)) {
    fail(context, 'install_methods', 'must be an array')
  }
  skill.install_methods = installMethods.map((method) => validateInstallMethod(method, context))
  skill.quick_start = validateQuickStart(value.quick_start, context)
  skill.documentation_url = requireHttpUrl(value, 'documentation_url', context)
  skill.repository_url = requireHttpUrl(value, 'repository_url', context)
  const testsUrl = optionalHttpUrl(value, 'tests_url', context)
  if (testsUrl !== undefined) {
    skill.tests_url = testsUrl
  }
  const securityNotesUrl = optionalHttpUrl(value, 'security_notes_url', context)
  if (securityNotesUrl !== undefined) {
    skill.security_notes_url = securityNotesUrl
  }
  return skill as unknown as Skill
}

/**
 * Validates unknown JSON against the catalog contract and returns a typed
 * Catalog. Throws an Error naming the offending skill and field. Runs at
 * build/dev time, so messages stay in English.
 */
export function validateCatalog(input: unknown): Catalog {
  if (!isRecord(input)) {
    throw new Error('Invalid catalog: top-level value must be an object')
  }
  const schemaVersion = requireNonEmptyString(input, 'schema_version', 'catalog')
  const updatedAt = requireNonEmptyString(input, 'updated_at', 'catalog')
  const rawSkills = input.skills
  if (!Array.isArray(rawSkills) || rawSkills.length === 0) {
    fail('catalog', 'skills', 'must be a non-empty array')
  }
  const skills = rawSkills.map((skill, index) => validateSkill(skill, index))
  const names = new Set<string>()
  for (const skill of skills) {
    if (names.has(skill.name)) {
      throw new Error(`Invalid catalog: duplicate skill name "${skill.name}"`)
    }
    names.add(skill.name)
  }
  return { schema_version: schemaVersion, updated_at: updatedAt, skills }
}
