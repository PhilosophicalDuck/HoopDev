import { useEffect, useRef } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { useSessionStore } from '../stores/sessionStore'
import { useFeedbackStore } from '../stores/feedbackStore'
import { DrillTimer } from '../components/session/DrillTimer'
import { MetricsTicker } from '../components/session/MetricsTicker'
import { CoachingCueOverlay } from '../components/session/CoachingCueOverlay'
import { SessionControls } from '../components/session/SessionControls'
import { DEMO_SESSION_DETAIL } from '../demo/mockData'
import { Layout } from '../components/shared/Layout'

interface LocationState {
  drillName?: string
  drillType?: string
}

const SHOOTING_CUES = [
  { id: 'c1', text: 'Tuck your elbow in', detail: 'Flare detected on release — keep elbow under the ball.', severity: 'warning' as const, category: 'form', duration_ms: 4000 },
  { id: 'c2', text: 'Good arc!', detail: 'Shot arc 47° — right in the ideal range. Keep it up.', severity: 'success' as const, category: 'arc', duration_ms: 3500 },
  { id: 'c3', text: 'Hold follow-through', detail: 'Snap the wrist and hold the goose-neck for 2 seconds.', severity: 'warning' as const, category: 'form', duration_ms: 4000 },
  { id: 'c4', text: 'Excellent rhythm!', detail: 'Consistent shooting cadence — your timing looks locked in.', severity: 'success' as const, category: 'rhythm', duration_ms: 3500 },
  { id: 'c5', text: 'Fatigue detected', detail: 'Last 3 shots dipping below 42° — stay focused on mechanics.', severity: 'warning' as const, category: 'fatigue', duration_ms: 4500 },
  { id: 'c6', text: 'Session complete', detail: '91% FG today — outstanding work.', severity: 'info' as const, category: 'summary', duration_ms: 5000 },
]

const DRIBBLE_CUES = [
  { id: 'c1', text: 'Keep your eyes up', detail: 'Ball-watching detected — train your court vision.', severity: 'warning' as const, category: 'form', duration_ms: 4000 },
  { id: 'c2', text: 'Good hand speed!', detail: 'Dribble frequency up — you\'re in rhythm now.', severity: 'success' as const, category: 'speed', duration_ms: 3500 },
  { id: 'c3', text: 'Switch hands', detail: 'Work your weak hand — alternate every 5 dribbles.', severity: 'info' as const, category: 'drill', duration_ms: 4000 },
  { id: 'c4', text: 'Low and tight', detail: 'Keep the ball below your knee for better control.', severity: 'warning' as const, category: 'form', duration_ms: 4000 },
  { id: 'c5', text: 'Great crossover!', detail: 'Clean hand switch with good body lean — keep going.', severity: 'success' as const, category: 'form', duration_ms: 3500 },
  { id: 'c6', text: 'Session complete', detail: 'Solid dribbling session — consistency is your edge.', severity: 'info' as const, category: 'summary', duration_ms: 5000 },
]

const CUE_TIMES = [5000, 14000, 22000, 31000, 40000, 50000]
const SHOT_TIMES = [9000, 17000, 26000, 34000, 43000, 53000]
const SHOT_RESULTS: Array<{ made: boolean; made_total: number; attempted_total: number }> = [
  { made: true,  made_total: 1,  attempted_total: 1 },
  { made: true,  made_total: 2,  attempted_total: 2 },
  { made: false, made_total: 2,  attempted_total: 3 },
  { made: true,  made_total: 3,  attempted_total: 4 },
  { made: true,  made_total: 4,  attempted_total: 5 },
  { made: true,  made_total: 5,  attempted_total: 6 },
]

export function DemoLiveSession() {
  const location = useLocation()
  const navigate = useNavigate()
  const state = location.state as LocationState | null

  const drillType = state?.drillType ?? 'shooting'
  const drillName = state?.drillName ?? 'Free Throw Shooting'

  const { setSession, setActive, setPaused, updateShots, reset } = useSessionStore()
  const { setCue, dismissCue, setMetrics, reset: resetFeedback } = useFeedbackStore()

  const videoRef = useRef<HTMLVideoElement>(null)
  const timersRef = useRef<ReturnType<typeof setTimeout>[]>([])
  const metricsIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const metricsTickRef = useRef(0)

  const videoSrc = drillType === 'shooting'
    ? '/demo/shooting_h264.mp4'
    : '/demo/dribbling_h264.mp4'

  const cues = drillType === 'shooting' ? SHOOTING_CUES : DRIBBLE_CUES

  function clearAllTimers() {
    timersRef.current.forEach(clearTimeout)
    timersRef.current = []
    if (metricsIntervalRef.current) {
      clearInterval(metricsIntervalRef.current)
      metricsIntervalRef.current = null
    }
  }

  function startSimulation() {
    videoRef.current?.play().catch(() => null)

    metricsIntervalRef.current = setInterval(() => {
      metricsTickRef.current += 1
      const t = metricsTickRef.current
      const speed = 200 + Math.sin(t * 0.3) * 80 + Math.random() * 40
      const elbowAngle = 88 + Math.sin(t * 0.2) * 8 + Math.random() * 4
      setMetrics({
        shot_state: 'dribbling',
        speed_px_s: speed,
        elbow_angle: elbowAngle,
        is_release_frame: false,
        ball_detected: true,
        hoop_detected: drillType === 'shooting',
      })
    }, 250)

    cues.forEach((cue, i) => {
      const t = timersRef.current[timersRef.current.length] ?? null
      const id = setTimeout(() => {
        setCue(cue)
        setTimeout(() => dismissCue(), cue.duration_ms)
      }, CUE_TIMES[i])
      timersRef.current.push(id)
    })

    SHOT_TIMES.forEach((time, i) => {
      const id = setTimeout(() => {
        const result = SHOT_RESULTS[i]
        updateShots({ made: result.made_total, attempted: result.attempted_total })
        setMetrics({
          shot_state: 'release',
          speed_px_s: 800 + Math.random() * 200,
          elbow_angle: 90 + Math.random() * 10,
          is_release_frame: true,
          ball_detected: true,
          hoop_detected: true,
        })
      }, time)
      timersRef.current.push(id)
    })
  }

  useEffect(() => {
    reset()
    resetFeedback()
    setSession(0, drillType, drillName)

    const startId = setTimeout(() => {
      setActive(true)
      startSimulation()
    }, 2000)
    timersRef.current.push(startId)

    return () => {
      clearAllTimers()
    }
  }, [])

  function handlePause() {
    setPaused(true)
    videoRef.current?.pause()
    if (metricsIntervalRef.current) {
      clearInterval(metricsIntervalRef.current)
      metricsIntervalRef.current = null
    }
  }

  function handleResume() {
    setPaused(false)
    videoRef.current?.play().catch(() => null)
    metricsIntervalRef.current = setInterval(() => {
      metricsTickRef.current += 1
      const t = metricsTickRef.current
      setMetrics({
        shot_state: 'dribbling',
        speed_px_s: 200 + Math.sin(t * 0.3) * 80 + Math.random() * 40,
        elbow_angle: 88 + Math.sin(t * 0.2) * 8 + Math.random() * 4,
        is_release_frame: false,
        ball_detected: true,
        hoop_detected: drillType === 'shooting',
      })
    }, 250)
  }

  function handleStop() {
    clearAllTimers()
    reset()
    resetFeedback()
    const d = DEMO_SESSION_DETAIL
    navigate('/review/demo', {
      state: {
        drill_name: drillName,
        drill_type: drillType,
        summary: d.metrics,
        feedback: d.metrics.coaching_feedback_json,
        highlight_clip_ids: [],
        demo_metrics: {
          ...d.metrics,
          shot_percentage: d.metrics.shot_percentage * 100,
        },
      },
    })
  }

  return (
    <Layout title={drillName}>
      <div className="flex gap-6 max-w-5xl">
        {/* Camera feed */}
        <div className="flex-1 min-w-0 space-y-4">
          <div className="relative bg-black rounded-xl overflow-hidden" style={{ aspectRatio: '16/9' }}>
            <video
              ref={videoRef}
              src={videoSrc}
              loop
              muted
              playsInline
              className="w-full h-full object-cover"
            />
            <CoachingCueOverlay />
          </div>

          <SessionControls
            onPause={handlePause}
            onResume={handleResume}
            onStop={handleStop}
          />
        </div>

        {/* Right sidebar */}
        <div className="w-56 shrink-0 space-y-4">
          <DrillTimer />
          <MetricsTicker />
        </div>
      </div>
    </Layout>
  )
}
