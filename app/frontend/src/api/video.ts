import { api } from './client'

export interface VideoUploadResponse {
  task_id: string
  session_id: number
  message: string
}

export interface VideoStatusResponse {
  task_id: string
  status: 'processing' | 'complete' | 'error'
  progress: number
  session_id: number | null
  error: string | null
}

export const uploadVideo = (
  file: File,
  drillType: string,
  drillName: string,
): Promise<VideoUploadResponse> => {
  const form = new FormData()
  form.append('file', file)
  form.append('drill_type', drillType)
  form.append('drill_name', drillName)
  return api
    .post<VideoUploadResponse>('/video/upload', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    .then((r) => r.data)
}

export const getVideoStatus = (taskId: string): Promise<VideoStatusResponse> =>
  api.get<VideoStatusResponse>(`/video/${taskId}/status`).then((r) => r.data)
