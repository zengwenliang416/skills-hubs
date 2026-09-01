export interface DailyVisitors {
  date: string
  visitors: number
}

export interface NpmDownloads {
  package_name: string
  downloads: number | null
  period_start: string | null
  period_end: string | null
  stale: boolean
  error: string | null
}

export interface SkillEngagement {
  skill_name: string
  unique_visitors: number
  views: number
  install_copies: number
  documentation_clicks: number
  repository_clicks: number
}

export interface MetricsResponse {
  total_visitors: number
  today_visitors: number
  total_page_views: number
  daily_visitors: DailyVisitors[]
  npm_downloads: NpmDownloads[]
  skill_engagement: SkillEngagement[]
}
