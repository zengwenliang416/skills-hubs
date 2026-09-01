import { useCallback, useEffect, useState } from 'react'
import type { CSSProperties } from 'react'

import { Button } from '@/components/Button'
import { CountUp } from '@/components/CountUp'
import { FadeUp } from '@/components/amicro/FadeUp'
import { skills } from '@/features/catalog/data'

import { fetchMetrics, recordVisit } from './api'
import styles from './MetricsSection.module.css'
import { downloadProgressProps, summarizeNpmDownloads } from './presentation'
import type { MetricsResponse, NpmDownloads } from './types'

type MetricsStatus = 'loading' | 'ready' | 'error'

const numberFormat = new Intl.NumberFormat('zh-CN')

function packageTitle(packageName: string): string {
  return skills.find((skill) => skill.npm === packageName)?.title ?? packageName
}

function skillTitle(skillName: string): string {
  return skills.find((skill) => skill.name === skillName)?.title ?? skillName
}

function weekdayLabel(date: string): string {
  return new Date(`${date}T00:00:00Z`).toLocaleDateString('zh-CN', {
    weekday: 'short',
    timeZone: 'UTC',
  })
}

function packageStatus(download: NpmDownloads): string {
  if (download.downloads === null) {
    return '暂无数据'
  }
  if (download.stale) {
    return '缓存数据'
  }
  return 'npm 实时数据'
}

/** Live visitor and npm download metrics backed by the Rust service. */
export function MetricsSection() {
  const [status, setStatus] = useState<MetricsStatus>('loading')
  const [metrics, setMetrics] = useState<MetricsResponse | null>(null)

  useEffect(() => {
    let active = true
    recordVisit()
      .then((response) => {
        if (active) {
          setMetrics(response)
          setStatus('ready')
        }
      })
      .catch(() => {
        if (active) {
          setStatus('error')
        }
      })
    return () => {
      active = false
    }
  }, [])

  const retry = useCallback(() => {
    setStatus('loading')
    fetchMetrics()
      .then((response) => {
        setMetrics(response)
        setStatus('ready')
      })
      .catch(() => setStatus('error'))
  }, [])

  if (status === 'error') {
    return (
      <section id="metrics" className={styles.section} aria-labelledby="metrics-title">
        <header className={styles.sectionHeader}>
          <p className={styles.kicker}>LIVE METRICS</p>
          <h2 id="metrics-title" className={styles.title}>
            运行数据
          </h2>
          <p className={styles.description}>访客与 npm 下载数据由 Rust 统计服务实时提供。</p>
        </header>
        <div className={styles.errorPanel} role="status">
          <div>
            <p className={styles.errorTitle}>统计服务暂时不可用</p>
            <p className={styles.errorHint}>页面其他功能不受影响，可以稍后重试。</p>
          </div>
          <Button variant="ghost" onClick={retry}>
            重新加载
          </Button>
        </div>
      </section>
    )
  }

  if (status === 'loading' || !metrics) {
    return (
      <section
        id="metrics"
        className={styles.section}
        aria-labelledby="metrics-title"
        aria-busy="true"
      >
        <header className={styles.sectionHeader}>
          <p className={styles.kicker}>LIVE METRICS</p>
          <h2 id="metrics-title" className={styles.title}>
            运行数据
          </h2>
          <p className={styles.description}>正在汇总访客与 npm 下载数据。</p>
        </header>
        <div className={styles.loadingGrid} aria-label="正在加载统计数据">
          {Array.from({ length: 4 }, (_, index) => (
            <span key={index} className={styles.skeleton} />
          ))}
        </div>
      </section>
    )
  }

  const npmSummary = summarizeNpmDownloads(metrics.npm_downloads)
  const skillEngagement = metrics.skill_engagement ?? []
  const maxVisitors = Math.max(1, ...metrics.daily_visitors.map((item) => item.visitors))
  const maxDownloads = Math.max(1, ...metrics.npm_downloads.map((item) => item.downloads ?? 0))
  const summary = [
    {
      label: '累计访客',
      value: metrics.total_visitors,
      caption: '按 IP 去重的全部访客',
      note: null,
    },
    {
      label: '今日访客',
      value: metrics.today_visitors,
      caption: 'UTC 当日按 IP 去重',
      note: null,
    },
    {
      label: '页面访问',
      value: metrics.total_page_views,
      caption: '累计页面加载次数',
      note: null,
    },
    {
      label: 'npm 周下载',
      value: npmSummary.value,
      caption: 'npm 官方 API 最近 7 天',
      note: npmSummary.note,
    },
  ]

  return (
    <section id="metrics" className={styles.section} aria-labelledby="metrics-title">
      <header className={styles.sectionHeader}>
        <div>
          <p className={styles.kicker}>LIVE METRICS</p>
          <h2 id="metrics-title" className={styles.title}>
            运行数据
          </h2>
        </div>
        <p className={styles.description}>
          真实访客趋势与 npm 最近一周下载量。服务端保存访问 IP，用于按日去重统计。
        </p>
      </header>

      <FadeUp yOffset={12}>
        <div className={styles.dashboard}>
          <dl className={styles.summaryGrid}>
            {summary.map((item) => (
              <div key={item.label} className={styles.metricCard}>
                <dt className={styles.metricLabel}>{item.label}</dt>
                <dd className={styles.metricValue}>
                  {item.value === null ? '—' : <CountUp value={item.value} />}
                </dd>
                <span className={styles.metricCaption}>{item.caption}</span>
                {item.note ? <span className={styles.metricNote}>{item.note}</span> : null}
              </div>
            ))}
          </dl>

          <div className={styles.detailGrid}>
            <article className={styles.trendCard}>
              <div className={styles.cardHeader}>
                <div>
                  <h3 className={styles.cardTitle}>近 7 天访客</h3>
                  <p className={styles.cardHint}>每日唯一访客</p>
                </div>
                <span className={styles.liveBadge}>
                  <span className={styles.liveDot} aria-hidden="true" />
                  LIVE
                </span>
              </div>
              <ol className={styles.chart} aria-label="近 7 天每日唯一访客柱状图">
                {metrics.daily_visitors.map((item) => {
                  const scale = item.visitors / maxVisitors
                  const barStyle = { '--bar-scale': scale } as CSSProperties
                  return (
                    <li
                      key={item.date}
                      className={styles.chartItem}
                      aria-label={`${item.date}：${item.visitors} 位访客`}
                    >
                      <span className={styles.chartValue}>
                        {numberFormat.format(item.visitors)}
                      </span>
                      <span className={styles.barTrack} aria-hidden="true">
                        <span className={styles.barFill} style={barStyle} />
                      </span>
                      <span className={styles.chartLabel}>{weekdayLabel(item.date)}</span>
                    </li>
                  )
                })}
              </ol>
            </article>

            <article className={styles.downloadCard}>
              <div className={styles.cardHeader}>
                <div>
                  <h3 className={styles.cardTitle}>npm 下载</h3>
                  <p className={styles.cardHint}>最近完整 7 天</p>
                </div>
                <svg
                  className={styles.downloadIcon}
                  width="24"
                  height="24"
                  viewBox="0 0 24 24"
                  fill="none"
                  aria-hidden="true"
                >
                  <path d="M4 7.5h16v9H4z" stroke="currentColor" strokeWidth="1.8" />
                  <path
                    d="M7.5 10.5v3M11 13.5v-3h2v3M16.5 10.5v3"
                    stroke="currentColor"
                    strokeWidth="1.8"
                    strokeLinecap="round"
                  />
                </svg>
              </div>
              <ul className={styles.downloadList}>
                {metrics.npm_downloads.map((item) => {
                  const progress = (item.downloads ?? 0) / maxDownloads
                  const progressStyle = { '--download-scale': progress } as CSSProperties
                  return (
                    <li key={item.package_name} className={styles.downloadItem}>
                      <div className={styles.downloadHeading}>
                        <div>
                          <p className={styles.packageTitle}>{packageTitle(item.package_name)}</p>
                          <p className={styles.packageName}>{item.package_name}</p>
                        </div>
                        <div className={styles.downloadValue}>
                          {item.downloads === null ? '—' : numberFormat.format(item.downloads)}
                        </div>
                      </div>
                      <div
                        className={styles.downloadTrack}
                        {...downloadProgressProps(item, maxDownloads)}
                      >
                        <span className={styles.downloadFill} style={progressStyle} />
                      </div>
                      <div className={styles.downloadMeta}>
                        <span>{packageStatus(item)}</span>
                        {item.period_start && item.period_end ? (
                          <span>
                            {item.period_start} 至 {item.period_end}
                          </span>
                        ) : null}
                      </div>
                    </li>
                  )
                })}
              </ul>
            </article>

            <article className={styles.engagementCard}>
              <div className={styles.cardHeader}>
                <div>
                  <h3 className={styles.cardTitle}>Skill 热度</h3>
                  <p className={styles.cardHint}>详情评估与安装意向的累计行为</p>
                </div>
                <span className={styles.privacyBadge}>仅聚合值</span>
              </div>
              {skillEngagement.length > 0 ? (
                <ul className={styles.engagementList}>
                  {skillEngagement.map((item) => {
                    const actions = [
                      { label: '详情', value: item.views },
                      { label: '复制安装', value: item.install_copies },
                      { label: '文档', value: item.documentation_clicks },
                      { label: '源码', value: item.repository_clicks },
                    ]
                    return (
                      <li key={item.skill_name} className={styles.engagementItem}>
                        <div className={styles.engagementHeading}>
                          <div>
                            <p className={styles.packageTitle}>{skillTitle(item.skill_name)}</p>
                            <p className={styles.packageName}>{item.skill_name}</p>
                          </div>
                          <p className={styles.interestedVisitors}>
                            {numberFormat.format(item.unique_visitors)}
                            <span> 位兴趣访客</span>
                          </p>
                        </div>
                        <dl className={styles.engagementStats}>
                          {actions.map((action) => (
                            <div key={action.label} className={styles.engagementStat}>
                              <dt>{action.label}</dt>
                              <dd>{numberFormat.format(action.value)}</dd>
                            </div>
                          ))}
                        </dl>
                      </li>
                    )
                  })}
                </ul>
              ) : (
                <p className={styles.engagementEmpty}>尚无 Skill 行为数据。</p>
              )}
            </article>
          </div>
        </div>
      </FadeUp>
    </section>
  )
}
