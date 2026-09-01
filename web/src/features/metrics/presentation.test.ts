import { describe, expect, it } from 'vitest'

import { downloadProgressProps, isNpmDataComplete, summarizeNpmDownloads } from './presentation'
import type { NpmDownloads } from './types'

function npmDownload(overrides: Partial<NpmDownloads> = {}): NpmDownloads {
  return {
    package_name: 'example-package',
    downloads: 12,
    period_start: '2026-08-23',
    period_end: '2026-08-29',
    stale: false,
    error: null,
    ...overrides,
  }
}

describe('npm metrics presentation', () => {
  it('marks stale, failed, or unavailable package values as partial', () => {
    expect(isNpmDataComplete([npmDownload()])).toBe(true)
    expect(isNpmDataComplete([npmDownload({ stale: true })])).toBe(false)
    expect(isNpmDataComplete([npmDownload({ error: 'refresh failed' })])).toBe(false)
    expect(isNpmDataComplete([npmDownload({ downloads: null })])).toBe(false)
  })

  it('renders exact complete and partial summary states', () => {
    expect(
      summarizeNpmDownloads([
        npmDownload({ package_name: 'first', downloads: 12 }),
        npmDownload({ package_name: 'second', downloads: 8 }),
      ]),
    ).toEqual({ value: 20, note: '全部 npm 包合计' })

    expect(
      summarizeNpmDownloads([
        npmDownload({ package_name: 'first', stale: true }),
        npmDownload({ package_name: 'second', error: 'refresh failed' }),
      ]),
    ).toEqual({
      value: 24,
      note: '部分数据 · 2/2 个包有数值，含 2 个缓存或失败值',
    })

    expect(
      summarizeNpmDownloads([
        npmDownload({ package_name: 'first' }),
        npmDownload({ package_name: 'second', downloads: null }),
      ]),
    ).toEqual({ value: 12, note: '部分数据 · 1/2 个包有数值' })
  })

  it('does not expose an unavailable package as a zero-valued progressbar', () => {
    const unavailable = downloadProgressProps(npmDownload({ downloads: null }), 12)

    expect(unavailable).toEqual({ 'aria-hidden': true })
    expect(unavailable).not.toHaveProperty('role')
    expect(unavailable).not.toHaveProperty('aria-valuenow')
  })

  it('keeps numeric progress semantics for available package values', () => {
    expect(downloadProgressProps(npmDownload({ downloads: 0 }), 12)).toEqual({
      role: 'progressbar',
      'aria-label': 'example-package 最近一周下载量',
      'aria-valuemin': 0,
      'aria-valuemax': 12,
      'aria-valuenow': 0,
    })
  })
})
