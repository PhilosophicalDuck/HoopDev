import { api } from './client'

export interface DrillCard {
  name: string; category: string; duration_min: number
  cv_supported: boolean; description?: string
}

export interface WorkoutPlan {
  recommended: DrillCard[]; total_duration_min: number
  rationale: string; skill_level: string; primary_focus: string
}

export const recommend = (duration_min: number, focus?: string) =>
  api.get<WorkoutPlan>('/workouts/recommend', { params: { duration_min, focus } })
    .then(r => r.data)

export const getCatalog = () =>
  api.get<{ drills: DrillCard[] }>('/workouts/catalog').then(r => r.data)
