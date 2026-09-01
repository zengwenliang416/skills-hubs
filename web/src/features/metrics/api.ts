import type { MetricsResponse } from './types'

let initialMetricsRequest: Promise<MetricsResponse> | null = null

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
  const response = await fetch('/api/metrics')
  return readMetricsResponse(response)
}
