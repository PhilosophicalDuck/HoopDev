import { useEffect, useRef } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useSessionStore } from '../stores/sessionStore'
import { useLiveFeedback } from '../hooks/useLiveFeedback'
import { useCameraStream } from '../hooks/useCameraStream'
import { CameraFeed } from '../components/session/CameraFeed'
import { CoachingCueOverlay } from '../components/session/CoachingCueOverlay'
import { MetricsTicker } from '../components/session/MetricsTicker'
import { DrillTimer } from '../components/session/DrillTimer'
import { SessionControls } from '../components/session/SessionControls'
import { updateSession } from '../api/sessions'

export function LiveSession() {
  const { sessionId: sessionIdParam } = useParams<{ sessionId: string }>()
  const navigate = useNavigate()
  const sessionId = sessionIdParam ? parseInt(sessionIdParam, 10) : null

  const { drillName, isActive, reset } = useSessionStore()
  const streamUrl = useCameraStream()

  const completionDataRef = useRef<{
    summary: object
    feedback: object
    highlight_clip_ids: number[]
  } | null>(null)

  const { pause, resume, stop } = useLiveFeedback(sessionId, (data) => {
    completionDataRef.current = data
    handleSessionEnd('completed')
  })

  async function handleSessionEnd(status: 'completed' | 'abandoned') {
    if (sessionId) {
      await updateSession(sessionId, status).catch(() => null)
    }
    reset()
    navigate(`/review/${sessionId}`, {
      state: completionDataRef.current,
    })
  }

  function handleStop() {
    stop()
    // Navigation will happen once session_complete message arrives
    // If WS doesn't send it within 5s, abandon the session
    setTimeout(() => {
      if (!completionDataRef.current) {
        handleSessionEnd('abandoned')
      }
    }, 5000)
  }

  // Clean up if user navigates away
  useEffect(() => {
    return () => {
      reset()
    }
  }, [])

  return (
    <div className="min-h-screen bg-gray-950 text-white flex flex-col">
      {/* Top bar */}
      <header className="bg-gray-900 border-b border-gray-800 px-6 py-3 flex items-center justify-between shrink-0">
        <div className="flex items-center gap-3">
          <span className="text-orange-400 font-bold text-lg">HoopDev</span>
          {drillName && (
            <>
              <span className="text-gray-600">/</span>
              <span className="text-white font-medium">{drillName}</span>
            </>
          )}
        </div>
        <div className="flex items-center gap-2">
          {isActive && (
            <span className="flex items-center gap-1.5 text-green-400 text-sm font-medium">
              <span className="w-2 h-2 bg-green-400 rounded-full animate-pulse" />
              Live
            </span>
          )}
        </div>
      </header>

      {/* Main content */}
      <div className="flex flex-1 overflow-hidden">
        {/* Camera feed — 2/3 width */}
        <div className="flex-1 relative bg-black">
          <CameraFeed streamUrl={streamUrl} className="w-full h-full object-cover" />
          <CoachingCueOverlay />
        </div>

        {/* Right sidebar — metrics + controls */}
        <aside className="w-72 bg-gray-950 border-l border-gray-800 flex flex-col gap-4 p-4 overflow-y-auto shrink-0">
          <DrillTimer />
          <MetricsTicker />
          <SessionControls
            onPause={pause}
            onResume={resume}
            onStop={handleStop}
          />

          {/* Quick tip */}
          <div className="bg-gray-900 rounded-xl p-3 mt-auto">
            <p className="text-xs text-gray-500">
              Development tips appear automatically above the camera feed. Tap any tip for details.
            </p>
          </div>
        </aside>
      </div>
    </div>
  )
}
