export interface InstallMethod {
  label: string
  description: string
  command?: string
}

export interface QuickStart {
  label: string
  command: string
}

/** Skill entry, aligned with the repository-root catalog.json schema. */
export interface Skill {
  name: string
  title: string
  version: string
  path: string
  category: string
  runtime: string
  npm: string
  license: string
  status: string
  description: string
  tags: string[]
  highlights: string[]
  use_cases: string[]
  install_methods: InstallMethod[]
  quick_start: QuickStart
  documentation_url: string
  repository_url: string
  /** Optional link to the skill's test suite. */
  tests_url?: string
  /** Optional link to the skill's security policy. */
  security_notes_url?: string
}

export interface Catalog {
  schema_version: string
  updated_at: string
  skills: Skill[]
}
