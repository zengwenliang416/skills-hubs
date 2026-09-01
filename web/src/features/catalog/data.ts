import catalogJson from '@catalog'

import { safeExternalUrl, validateCatalog } from './schema'
import type { Catalog, Skill } from './types'

export const catalog: Catalog = validateCatalog(catalogJson)
export const skills: Skill[] = catalog.skills

/** External links for a skill, sanitized to http(s) URLs only. */
export interface SkillLinks {
  documentationUrl: string | null
  repositoryUrl: string | null
  testsUrl: string | null
  securityNotesUrl: string | null
}

/** Returns sanitized external links for a skill; unsafe URLs become null. */
export function skillLinks(skill: Skill): SkillLinks {
  return {
    documentationUrl: safeExternalUrl(skill.documentation_url),
    repositoryUrl: safeExternalUrl(skill.repository_url),
    testsUrl: safeExternalUrl(skill.tests_url),
    securityNotesUrl: safeExternalUrl(skill.security_notes_url),
  }
}

export interface CategoryInfo {
  id: string
  label: string
  count: number
}

/** Chinese display labels for known category ids; unknown ids pass through. */
const CATEGORY_LABELS: Record<string, string> = {
  media: '媒体生成',
  'frontend-design': '前端设计',
}

export function categoryLabel(id: string): string {
  return CATEGORY_LABELS[id] ?? id
}

/** Chinese display labels for known status values; unknown values pass through. */
const STATUS_LABELS: Record<string, string> = {
  active: '活跃',
  deprecated: '已弃用',
  archived: '已归档',
}

export function statusLabel(status: string): string {
  return STATUS_LABELS[status] ?? status
}

/** Shared search matcher for the catalog and command palette. */
export function matchesSkill(skill: Skill, normalizedQuery: string): boolean {
  if (!normalizedQuery) {
    return true
  }
  const haystack = [
    skill.name,
    skill.title,
    skill.category,
    categoryLabel(skill.category),
    skill.description,
    skill.npm,
    skill.runtime,
    ...skill.tags,
    ...skill.highlights,
    ...skill.use_cases,
  ]
    .join(' ')
    .toLowerCase()
  // Callers pre-normalize; lowercasing here too keeps the matcher total.
  return haystack.includes(normalizedQuery.toLowerCase())
}

/** Categories derived from the catalog, sorted for a stable filter order. */
export const categories: CategoryInfo[] = Array.from(new Set(skills.map((skill) => skill.category)))
  .sort()
  .map((id) => ({
    id,
    label: categoryLabel(id),
    count: skills.filter((skill) => skill.category === id).length,
  }))
