import { useEffect, useRef, useCallback } from 'react'
import { useSessionStore } from '../stores/sessionStore'
import { useFeedbackStore } from '../stores/feedbackStore'
import { useSpeech, type SpeechPersona } from './useSpeech'

type OnComplete = (data: { summary: object; feedback: object; highlight_clip_ids: number[] }) => void

export function useLiveFeedback(sessionId: number | null, onComplete: OnComplete) {
  const wsRef = useRef<WebSocket | null>(null)
  const { setActive, setPaused, updateShots } = useSessionStore()
  const { setCue, setMetrics } = useFeedbackStore()
  const { speak } = useSpeech()

  const send = useCallback((msg: object) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(msg))
    }
  }, [])

  useEffect(() => {
    if (!sessionId) return

    const ws = new WebSocket(`/ws/session/${sessionId}`)
    wsRef.current = ws

    ws.onopen = () => {
      const drillType = useSessionStore.getState().drillType
      ws.send(JSON.stringify({ type: 'start_drill', drill_type: drillType }))
    }

    ws.onmessage = (event) => {
      const msg = JSON.parse(event.data)
      switch (msg.type) {
        case 'session_started':
          setActive(true)
          break

        case 'frame_data':
          setMetrics(msg.metrics)
          updateShots(msg.shot_counts)
          break

        case 'coaching_cue': {
          setCue(msg.cue)
          const persona = (localStorage.getItem('coach_persona') as SpeechPersona) ?? 'buddy'
          speak(msg.cue.text, persona)
          setTimeout(() => {
            useFeedbackStore.getState().dismissCue()
          }, msg.cue.duration_ms)
          break
        }

        case 'shot_event':
          // Handled via shot_counts update in frame_data
          break

        case 'session_complete':
          setActive(false)
          onComplete({
            summary: msg.summary,
            feedback: msg.feedback,
            highlight_clip_ids: msg.highlight_clip_ids,
          })
          break

        case 'error':
          console.error('WS error from server:', msg.detail)
          break
      }
    }

    ws.onclose = () => setActive(false)
    ws.onerror = () => setActive(false)

    return () => {
      ws.close()
    }
  }, [sessionId])

  return {
    pause: () => { setPaused(true); send({ type: 'pause' }) },
    resume: () => { setPaused(false); send({ type: 'resume' }) },
    stop: () => send({ type: 'stop' }),
  }
}
