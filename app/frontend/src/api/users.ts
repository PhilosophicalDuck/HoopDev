import { api } from './client'

export interface UserProfile {
  id: number; user_id: number
  position: string | null; skill_level: string | null
  height_cm: number | null; weight_kg: number | null
  dominant_hand: string | null; goals: string[] | null
  updated_at: string
  user: { id: number; username: string; email: string; created_at: string }
}

export interface ProfileUpdate {
  position?: string; skill_level?: string
  height_cm?: number; weight_kg?: number
  dominant_hand?: string; goals?: string[]
}

export const getProfile = () => api.get<UserProfile>('/users/me').then(r => r.data)
export const updateProfile = (data: ProfileUpdate) =>
  api.put<UserProfile>('/users/me', data).then(r => r.data)
