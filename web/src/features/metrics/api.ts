import type { MetricsResponse } from './types'

let initialMetricsRequest: Promise<MetricsResponse> | null = null

/** Budget for a metrics fetch before it is aborted as a timeout. */
const FETCH_TIMEOUT_MS = 8000

async function readMetricsResponse(response: Response): Promise<MetricsResponse> {
  if (!response.ok) {
    throw new Error(`统计服务返回 ${response.status}`)
  }
  return (await response.json()) as MetricsResponse
}

async function postVisit(): Promise<MetricsResponse> {
  const response = await fetch('/api/visits', {
    method: 'POST',
  })
  return readMetricsResponse(response)
}

export function recordVisit(): Promise<MetricsResponse> {
  if (!initialMetricsRequest) {
    initialMetricsRequest = postVisit().catch((error: unknown) => {
      initialMetricsRequest = null
      throw error
    })
  }
  return initialMetricsRequest
}

export async function fetchMetrics(): Promise<MetricsResponse> {
  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), FETCH_TIMEOUT_MS)
  try {
    const response = await fetch('/api/metrics', { signal: controller.signal })
    return await readMetricsResponse(response)
  } catch (error) {
    if (error instanceof DOMException && error.name === 'AbortError') {
      throw new Error(`统计服务请求超时（${FETCH_TIMEOUT_MS / 1000} 秒）`)
    }
    throw error
  } finally {
    clearTimeout(timer)
  }
}
