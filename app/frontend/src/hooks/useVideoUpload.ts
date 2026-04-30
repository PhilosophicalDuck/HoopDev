import { useCallback, useRef, useState } from 'react'
import { uploadVideo } from '../api/video'

export type UploadStatus = 'idle' | 'uploading' | 'processing' | 'complete' | 'error'

interface VideoUploadState {
  status: UploadStatus
  progress: number          // 0–100
  sessionId: number | null
  summary: Record<string, unknown> | null
  feedback: Record<string, unknown> | null
  error: string | null
}

interface UseVideoUpload {
  state: VideoUploadState
  start: (file: File, drillType: string, drillName: string) => void
  reset: () => void
}

const INITIAL_STATE: VideoUploadState = {
  status: 'idle',
  progress: 0,
  sessionId: null,
  summary: null,
  feedback: null,
  error: null,
}

export function useVideoUpload(): UseVideoUpload {
  const [state, setState] = useState<VideoUploadState>(INITIAL_STATE)
  const wsRef = useRef<WebSocket | null>(null)

  const reset = useCallback(() => {
    wsRef.current?.close()
    wsRef.current = null
    setState(INITIAL_STATE)
  }, [])

  const start = useCallback(
    (file: File, drillType: string, drillName: string) => {
      setState({ ...INITIAL_STATE, status: 'uploading' })

      uploadVideo(file, drillType, drillName)
        .then(({ task_id, session_id }) => {
          setState((s) => ({ ...s, status: 'processing', sessionId: session_id }))

          // Open WebSocket for progress updates
          const wsProto = window.location.protocol === 'https:' ? 'wss' : 'ws'
          const ws = new WebSocket(`${wsProto}://${window.location.host}/ws/video/${task_id}/progress`)
          wsRef.current = ws

          ws.onmessage = (evt) => {
            const msg = JSON.parse(evt.data) as {
              type: string
              pct?: number
              session_id?: number
              summary?: Record<string, unknown>
              feedback?: Record<string, unknown>
              message?: string
            }

            if (msg.type === 'progress') {
              setState((s) => ({ ...s, progress: msg.pct ?? s.progress }))
            } else if (msg.type === 'complete') {
              setState({
                status: 'complete',
                progress: 100,
                sessionId: msg.session_id ?? session_id,
                summary: msg.summary ?? null,
                feedback: msg.feedback ?? null,
                error: null,
              })
              ws.close()
            } else if (msg.type === 'error') {
              setState((s) => ({
                ...s,
                status: 'error',
                error: msg.message ?? 'Processing failed',
              }))
              ws.close()
            }
          }

          ws.onerror = () => {
            setState((s) => ({
              ...s,
              status: 'error',
              error: 'Lost connection to server',
            }))
          }
        })
        .catch((err: unknown) => {
          const message =
            err instanceof Error ? err.message : 'Upload failed'
          setState((s) => ({ ...s, status: 'error', error: message }))
        })
    },
    [],
  )

  return { state, start, reset }
}
