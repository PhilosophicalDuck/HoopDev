import { api } from './client'

export interface SessionSummary {
  id: number; drill_type: string; drill_name: string; status: string
  started_at: string; ended_at: string | null; duration_s: number | null
  shots_made?: number; shot_percentage?: number
}

export interface SessionDetail extends SessionSummary {
  total_frames?: number; fps?: number
  metrics?: SessionMetrics
  highlights: HighlightMini[]
}

export interface SessionMetrics {
  shots_made: number; shots_attempted: number; shot_percentage?: number
  avg_release_elbow_angle?: number; avg_arc_angle_deg?: number
  release_consistency_cv?: number; follow_through_ratio?: number
  hand_switches: number; dribble_rhythm_cv?: number
  avg_speed_px_per_s?: number; top_speed_px_per_s?: number
  active_ratio?: number; coaching_feedback_json?: CoachingFeedback
  speed_history_json?: number[]; shot_events_json?: ShotEvent[]
}

export interface CoachingFeedback {
  drill_type: string; strengths: string[]; improvements: string[]
  coaching_tips: Record<string, string>
}

export interface ShotEvent { frame: number; event: 'MADE' | 'MISS' }

export interface HighlightMini {
  id: number; file_path: string; duration_s?: number; thumbnail_path?: string
}

export const createSession = (drill_type: string, drill_name: string) =>
  api.post<SessionDetail>('/sessions', { drill_type, drill_name }).then(r => r.data)

export const listSessions = () =>
  api.get<SessionSummary[]>('/sessions').then(r => r.data)

export const getSession = (id: number) =>
  api.get<SessionDetail>(`/sessions/${id}`).then(r => r.data)

export const updateSession = (id: number, status: string) =>
  api.patch<SessionDetail>(`/sessions/${id}`, { status }).then(r => r.data)
