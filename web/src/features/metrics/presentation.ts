import type { NpmDownloads } from './types'

type UnavailableProgressProps = {
  'aria-hidden': true
}

type AvailableProgressProps = {
  role: 'progressbar'
  'aria-label': string
  'aria-valuemin': number
  'aria-valuemax': number
  'aria-valuenow': number
}

export interface NpmSummary {
  value: number | null
  note: string
}

export function isNpmDataComplete(downloads: NpmDownloads[]): boolean {
  return (
    downloads.length > 0 &&
    downloads.every((item) => item.downloads !== null && !item.stale && item.error === null)
  )
}

export function summarizeNpmDownloads(downloads: NpmDownloads[]): NpmSummary {
  if (downloads.length === 0) {
    return { value: null, note: '暂无 npm 包数据' }
  }

  const available = downloads.filter((item) => item.downloads !== null)
  const value =
    available.length > 0
      ? available.reduce((total, item) => total + (item.downloads ?? 0), 0)
      : null

  if (isNpmDataComplete(downloads)) {
    return { value, note: '全部 npm 包合计' }
  }

  const degradedCount = downloads.filter(
    (item) => item.downloads !== null && (item.stale || item.error !== null),
  ).length
  const degradedNote = degradedCount > 0 ? `，含 ${degradedCount} 个缓存或失败值` : ''

  return {
    value,
    note: `部分数据 · ${available.length}/${downloads.length} 个包有数值${degradedNote}`,
  }
}

export function downloadProgressProps(
  download: NpmDownloads,
  maxDownloads: number,
): UnavailableProgressProps | AvailableProgressProps {
  if (download.downloads === null) {
    return { 'aria-hidden': true }
  }

  return {
    role: 'progressbar',
    'aria-label': `${download.package_name} 最近一周下载量`,
    'aria-valuemin': 0,
    'aria-valuemax': maxDownloads,
    'aria-valuenow': download.downloads,
  }
}
