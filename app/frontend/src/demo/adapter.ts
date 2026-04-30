/**
 * Custom axios adapter used in demo mode.
 * Intercepts every request and returns mock data — no network calls made.
 */
import type { AxiosRequestConfig, AxiosResponse } from 'axios'
import {
  DEMO_PROFILE,
  DEMO_DASHBOARD,
  DEMO_CATALOG,
  DEMO_WORKOUT_PLAN,
  DEMO_SESSION,
  DEMO_HIGHLIGHTS,
  DEMO_CHAT_REPLY,
} from './data'

function ok(data: unknown, config: AxiosRequestConfig): Promise<AxiosResponse> {
  return Promise.resolve({
    data,
    status: 200,
    statusText: 'OK',
    headers: { 'content-type': 'application/json' },
    config: config as any,
    request: {},
  } as AxiosResponse)
}

export function demoAdapter(config: AxiosRequestConfig): Promise<AxiosResponse> {
  const url = config.url ?? ''
  const method = (config.method ?? 'get').toLowerCase()

  // Profile
  if (url.includes('/users/me')) return ok(DEMO_PROFILE, config)

  // Dashboard
  if (url.includes('/dashboard')) return ok(DEMO_DASHBOARD, config)

  // Workouts
  if (url.includes('/workouts/catalog')) return ok(DEMO_CATALOG, config)
  if (url.includes('/workouts/recommend')) return ok(DEMO_WORKOUT_PLAN, config)

  // Sessions — POST creates a new one, GET retrieves it
  if (url.match(/\/sessions\/\d+/) && method === 'get') return ok(DEMO_SESSION, config)
  if (url.match(/\/sessions\/\d+/) && method === 'patch') return ok(DEMO_SESSION, config)
  if (url.endsWith('/sessions') && method === 'post') return ok(DEMO_SESSION, config)
  if (url.endsWith('/sessions') && method === 'get') return ok([DEMO_SESSION], config)

  // Highlights
  if (url.includes('/highlights')) return ok(DEMO_HIGHLIGHTS, config)

  // Chat
  if (url.includes('/chat/message') && method === 'post') {
    const body = config.data ? JSON.parse(config.data) : {}
    const persona: 'sully' | 'buddy' = body.persona === 'sully' ? 'sully' : 'buddy'
    return ok({ reply: DEMO_CHAT_REPLY[persona] }, config)
  }

  // Benchmarks — return empty list
  if (url.includes('/benchmarks')) return ok([], config)

  // Camera / live session endpoints — return neutral responses
  if (url.includes('/camera') || url.includes('/live')) {
    return ok({ status: 'demo' }, config)
  }

  // Fallback — return empty object so the app doesn't crash
  return ok({}, config)
}
