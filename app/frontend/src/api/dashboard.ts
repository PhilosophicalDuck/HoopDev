import { api } from './client'

export interface RadarData {
  shooting: number | null
  consistency: number | null
  ball_handling: number | null
  footwork: number | null
  conditioning: number | null
}

export interface RecentSession {
  id: number
  drill_name: string
  drill_type: string
  started_at: string
  duration_s: number | null
  shot_percentage?: number | null
  shots_made?: number
  shots_attempted?: number
}

export interface DashboardData {
  radar: RadarData
  benchmark_history: Record<string, { value: number; recorded_at: string; session_id?: number }[]>
  latest_benchmarks: Record<string, number>
  recent_sessions: RecentSession[]
  total_sessions: number
}

export const getDashboard = () =>
  api.get<DashboardData>('/dashboard').then((r) => r.data)
