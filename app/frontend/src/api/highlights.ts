import { api } from './client'

export interface HighlightClipMeta {
  id: number; session_id: number; user_id: number
  file_path: string; duration_s?: number
  shot_frame?: number; thumbnail_path?: string; created_at: string
}

export const listHighlights = (session_id?: number) =>
  api.get<HighlightClipMeta[]>('/highlights', { params: session_id ? { session_id } : {} })
    .then(r => r.data)

export const deleteHighlight = (id: number) =>
  api.delete(`/highlights/${id}`)

export const streamUrl = (id: number): string =>
  localStorage.getItem('demo_mode') === 'true'
    ? '/demo/highlight.mp4'
    : `/api/highlights/${id}/stream`

export const thumbnailUrl = (id: number): string =>
  `/api/highlights/${id}/thumbnail`
