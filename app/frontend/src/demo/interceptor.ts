import type { AxiosInstance, InternalAxiosRequestConfig } from 'axios'
import { DEMO_PROFILE, DEMO_DASHBOARD, DEMO_CATALOG, DEMO_WORKOUT_PLAN } from './data'
import {
  DEMO_SESSION_DETAIL,
  DEMO_UPLOAD_RESULT,
  DEMO_CHAT_REPLIES,
  DEMO_FILM_ROOM_REPLIES,
} from './mockData'
import { callOllamaChat } from './ollamaChat'

function isDemo() {
  return localStorage.getItem('demo_mode') === 'true'
}

function delay(ms: number) {
  return new Promise((r) => setTimeout(r, ms))
}

function randomFrom<T>(arr: T[]): T {
  return arr[Math.floor(Math.random() * arr.length)]
}

function mockResponse(data: unknown, ms = 600) {
  return delay(ms).then(() => ({ data, status: 200, statusText: 'OK', headers: {}, config: {} as InternalAxiosRequestConfig }))
}

export function registerDemoInterceptor(api: AxiosInstance) {
  api.interceptors.request.use(async (config) => {
    if (!isDemo()) return config

    const url = config.url ?? ''
    const method = (config.method ?? 'get').toLowerCase()

    // Profile
    if (url.includes('/users/me')) {
      throw Object.assign(new Error('demo'), { response: await mockResponse(DEMO_PROFILE) })
    }

    // Dashboard
    if (url.includes('/dashboard')) {
      throw Object.assign(new Error('demo'), { response: await mockResponse(DEMO_DASHBOARD) })
    }

    // Sessions
    if (url.match(/\/sessions\/\d+/)) {
      throw Object.assign(new Error('demo'), { response: await mockResponse(DEMO_SESSION_DETAIL) })
    }
    if (url.includes('/sessions') && method === 'post') {
      throw Object.assign(new Error('demo'), { response: await mockResponse(DEMO_SESSION_DETAIL) })
    }
    if (url.includes('/sessions') && method === 'get') {
      throw Object.assign(new Error('demo'), { response: await mockResponse([DEMO_SESSION_DETAIL]) })
    }

    // Workouts
    if (url.includes('/workouts/recommend')) {
      const focus: string | undefined = config.params?.focus
      if (!focus) {
        throw Object.assign(new Error('demo'), { response: await mockResponse(DEMO_WORKOUT_PLAN) })
      }
      const durationMin: number = config.params?.duration_min ?? 60
      const primary = DEMO_CATALOG.drills.filter(d => d.category === focus)
      const others = DEMO_CATALOG.drills.filter(d => d.category !== focus)
      const selected: typeof primary = []
      let total = 0
      for (const drill of [...primary, ...others]) {
        if (total + drill.duration_min > durationMin) continue
        selected.push(drill)
        total += drill.duration_min
        if (total >= durationMin - 5) break
      }
      const filteredPlan = {
        recommended: selected,
        total_duration_min: total,
        rationale: `Focusing on ${focus.replace('_', ' ')} — as requested.`,
        skill_level: 'intermediate',
        primary_focus: focus,
      }
      throw Object.assign(new Error('demo'), { response: await mockResponse(filteredPlan) })
    }
    if (url.includes('/workouts')) {
      throw Object.assign(new Error('demo'), { response: await mockResponse(DEMO_CATALOG) })
    }

    // Video upload — return instant complete result
    if (url.includes('/video')) {
      throw Object.assign(new Error('demo'), { response: await mockResponse(DEMO_UPLOAD_RESULT, 1200) })
    }

    // Coach chat — call Ollama directly from the browser (no backend needed)
    // when VITE_OLLAMA_DEMO_CHAT=true, otherwise return canned replies.
    if (url.includes('/chat/message')) {
      const body = config.data ? JSON.parse(config.data) : {}
      const persona: 'sully' | 'buddy' = body.persona ?? 'buddy'

      if (import.meta.env.VITE_OLLAMA_DEMO_CHAT === 'true') {
        try {
          const reply = await callOllamaChat(body.message ?? '', persona, body.session_data ?? null)
          throw Object.assign(new Error('demo'), { response: await mockResponse({ reply }, 0) })
        } catch (err: unknown) {
          // Re-throw demo responses; wrap Ollama errors as a graceful reply
          if ((err as { message?: string }).message === 'demo') throw err
          const reply = 'Ollama is not reachable. Make sure it is running on your machine.'
          throw Object.assign(new Error('demo'), { response: await mockResponse({ reply }, 0) })
        }
      }

      const currentView: string = body.session_data?.current_view ?? ''
      let reply: string
      if (currentView && DEMO_FILM_ROOM_REPLIES[persona]?.[currentView]) {
        reply = DEMO_FILM_ROOM_REPLIES[persona][currentView]
      } else if (currentView && DEMO_FILM_ROOM_REPLIES[persona]) {
        reply = DEMO_FILM_ROOM_REPLIES[persona].default
      } else {
        reply = randomFrom(DEMO_CHAT_REPLIES[persona])
      }
      throw Object.assign(new Error('demo'), { response: await mockResponse({ reply }, 800) })
    }

    // Highlights — return one demo clip backed by the static public/demo/highlight.mp4
    if (url.includes('/highlights') && !url.match(/\/highlights\/\d/)) {
      const demoClip = {
        id: 1, session_id: 1, user_id: 1,
        file_path: 'demo/highlight.mp4',
        duration_s: 18.4,
        thumbnail_path: null,
        created_at: '2026-04-14T10:30:00Z',
      }
      throw Object.assign(new Error('demo'), { response: await mockResponse([demoClip]) })
    }

    // Auth endpoints — let them pass (we bypass auth in demo login anyway)
    if (url.includes('/auth')) return config

    // Everything else — empty 200
    throw Object.assign(new Error('demo'), { response: await mockResponse({}) })
  })

  // Unwrap the fake "thrown" responses so axios resolves them normally
  api.interceptors.response.use(
    (res) => res,
    (err) => {
      if (err?.message === 'demo' && err?.response) {
        return Promise.resolve(err.response)
      }
      return Promise.reject(err)
    },
  )
}
