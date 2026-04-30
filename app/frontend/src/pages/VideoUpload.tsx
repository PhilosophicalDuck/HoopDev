import { useCallback, useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { getCatalog, type DrillCard } from '../api/workouts'
import { useVideoUpload } from '../hooks/useVideoUpload'
import { Layout } from '../components/shared/Layout'
import { Button } from '../components/shared/Button'
import { useUserStore } from '../stores/userStore'
import { DEMO_UPLOAD_RESULT } from '../demo/mockData'

const ALLOWED_TYPES = ['video/mp4', 'video/quicktime', 'video/x-msvideo', 'video/x-matroska', 'video/m4v']
const MAX_SIZE_MB = 500

// ── Dropzone ──────────────────────────────────────────────────────────────────

interface DropzoneProps {
  file: File | null
  onFile: (f: File) => void
  disabled: boolean
}

function Dropzone({ file, onFile, disabled }: DropzoneProps) {
  const [dragging, setDragging] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)

  const validate = (f: File): string | null => {
    if (!ALLOWED_TYPES.includes(f.type) && !f.name.match(/\.(mp4|mov|avi|mkv|m4v)$/i)) {
      return 'Unsupported file type. Use MP4, MOV, AVI, MKV, or M4V.'
    }
    if (f.size > MAX_SIZE_MB * 1024 * 1024) {
      return `File too large. Maximum is ${MAX_SIZE_MB} MB.`
    }
    return null
  }

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault()
      setDragging(false)
      if (disabled) return
      const f = e.dataTransfer.files[0]
      if (!f) return
      const err = validate(f)
      if (err) { alert(err); return }
      onFile(f)
    },
    [disabled, onFile],
  )

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0]
    if (!f) return
    const err = validate(f)
    if (err) { alert(err); return }
    onFile(f)
  }

  return (
    <div
      className={`border-2 border-dashed rounded-xl p-10 text-center transition-colors cursor-pointer
        ${dragging ? 'border-orange-400 bg-orange-500/10' : 'border-gray-700 hover:border-gray-500'}
        ${disabled ? 'opacity-50 cursor-not-allowed' : ''}`}
      onDragOver={(e) => { e.preventDefault(); if (!disabled) setDragging(true) }}
      onDragLeave={() => setDragging(false)}
      onDrop={handleDrop}
      onClick={() => !disabled && inputRef.current?.click()}
    >
      <input
        ref={inputRef}
        type="file"
        accept=".mp4,.mov,.avi,.mkv,.m4v,video/*"
        className="hidden"
        onChange={handleChange}
        disabled={disabled}
      />
      {file ? (
        <div>
          <p className="text-white font-medium">{file.name}</p>
          <p className="text-gray-500 text-sm mt-1">
            {(file.size / (1024 * 1024)).toFixed(1)} MB
          </p>
          <p className="text-gray-600 text-xs mt-2">Click or drag to replace</p>
        </div>
      ) : (
        <div>
          <p className="text-4xl mb-3">🎬</p>
          <p className="text-white font-medium">Drop your training video here</p>
          <p className="text-gray-500 text-sm mt-1">or click to browse</p>
          <p className="text-gray-600 text-xs mt-3">MP4, MOV, AVI, MKV · max {MAX_SIZE_MB} MB</p>
        </div>
      )}
    </div>
  )
}

// ── Progress bar ──────────────────────────────────────────────────────────────

function ProgressBar({ pct }: { pct: number }) {
  return (
    <div className="w-full bg-gray-800 rounded-full h-3 overflow-hidden">
      <div
        className="h-full bg-orange-500 rounded-full transition-all duration-500"
        style={{ width: `${pct}%` }}
      />
    </div>
  )
}

// ── Results section ───────────────────────────────────────────────────────────

interface Feedback {
  strengths?: string[]
  improvements?: string[]
  coaching_tips?: string[]
}

interface Summary {
  shots_made?: number
  shots_attempted?: number
  shot_percentage?: number
  avg_release_elbow_angle?: number
  avg_arc_angle_deg?: number
  follow_through_ratio?: number
  cue_log?: { text: string; severity: string; category: string }[]
}

function ResultsView({
  sessionId,
  summary,
  feedback,
}: {
  sessionId: number
  summary: Summary
  feedback: Feedback
}) {
  const navigate = useNavigate()
  const fgPct =
    summary.shot_percentage != null
      ? `${summary.shot_percentage.toFixed(0)}%`
      : summary.shots_attempted
      ? `${Math.round(((summary.shots_made ?? 0) / summary.shots_attempted) * 100)}%`
      : '—'

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <span className="text-3xl">✅</span>
        <div>
          <h3 className="text-xl font-bold text-white">Analysis Complete</h3>
          <p className="text-gray-500 text-sm">Your video has been processed</p>
        </div>
      </div>

      {/* Key stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          {
            label: 'Field Goal %',
            value: fgPct,
            sub: summary.shots_attempted ? `${summary.shots_made ?? 0}/${summary.shots_attempted}` : undefined,
          },
          {
            label: 'Elbow Angle',
            value: summary.avg_release_elbow_angle != null
              ? `${summary.avg_release_elbow_angle.toFixed(0)}°`
              : '—',
            sub: 'target: 75-105°',
          },
          {
            label: 'Arc Angle',
            value: summary.avg_arc_angle_deg != null
              ? `${summary.avg_arc_angle_deg.toFixed(0)}°`
              : '—',
            sub: 'target: 42-58°',
          },
          {
            label: 'Follow-through',
            value: summary.follow_through_ratio != null
              ? `${(summary.follow_through_ratio * 100).toFixed(0)}%`
              : '—',
          },
        ].map((stat) => (
          <div key={stat.label} className="bg-gray-900 rounded-xl p-4 text-center">
            <p className="text-xs text-gray-500 uppercase tracking-wider mb-1">{stat.label}</p>
            <p className="text-2xl font-bold font-mono text-white">{stat.value}</p>
            {stat.sub && <p className="text-xs text-gray-600 mt-0.5">{stat.sub}</p>}
          </div>
        ))}
      </div>

      {/* AI feedback */}
      <div className="grid md:grid-cols-2 gap-4">
        {feedback.strengths && feedback.strengths.length > 0 && (
          <div className="bg-green-500/10 border border-green-500/30 rounded-xl p-4">
            <h3 className="text-green-400 font-semibold mb-3">Strengths</h3>
            <ul className="space-y-2">
              {feedback.strengths.map((s, i) => (
                <li key={i} className="text-sm text-gray-300 flex gap-2">
                  <span className="text-green-500 shrink-0">✓</span>
                  {s}
                </li>
              ))}
            </ul>
          </div>
        )}
        {feedback.improvements && feedback.improvements.length > 0 && (
          <div className="bg-orange-500/10 border border-orange-500/30 rounded-xl p-4">
            <h3 className="text-orange-400 font-semibold mb-3">Work On</h3>
            <ul className="space-y-2">
              {feedback.improvements.map((s, i) => (
                <li key={i} className="text-sm text-gray-300 flex gap-2">
                  <span className="text-orange-500 shrink-0">→</span>
                  {s}
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>

      {/* Coaching tips */}
      {feedback.coaching_tips && feedback.coaching_tips.length > 0 && (
        <div className="bg-gray-900 rounded-xl p-4">
          <h3 className="text-white font-semibold mb-3">Developmental Tips</h3>
          <ul className="space-y-2">
            {feedback.coaching_tips.map((tip, i) => (
              <li key={i} className="text-sm text-gray-300 flex gap-2">
                <span className="text-orange-400 shrink-0">•</span>
                {tip}
              </li>
            ))}
          </ul>
        </div>
      )}

      <div className="flex gap-3">
        <Button onClick={() => navigate(`/review/${sessionId}`)}>
          Full Session Details
        </Button>
        <Button variant="ghost" onClick={() => navigate('/')}>
          Dashboard
        </Button>
      </div>
    </div>
  )
}

// ── Main page ──────────────────────────────────────────────────────────────────

export function VideoUpload() {
  const navigate = useNavigate()
  const { state, start, reset } = useVideoUpload()
  const { isDemo } = useUserStore()

  const [file, setFile] = useState<File | null>(null)
  const [drillType, setDrillType] = useState('shooting')
  const [drillName, setDrillName] = useState('')
  const [drills, setDrills] = useState<DrillCard[]>([])
  const [demoResult, setDemoResult] = useState<typeof DEMO_UPLOAD_RESULT | null>(null)

  useEffect(() => {
    getCatalog()
      .then((d) => setDrills(d.drills))
      .catch(() => null)
  }, [])

  const handleSubmit = () => {
    if (isDemo) {
      // In demo mode skip the upload and show pre-built results instantly
      setTimeout(() => setDemoResult(DEMO_UPLOAD_RESULT), 800)
      return
    }
    if (!file) return
    const name = drillName || file.name.replace(/\.[^.]+$/, '')
    start(file, drillType, name)
  }

  const isIdle = state.status === 'idle'
  const isUploading = state.status === 'uploading'
  const isProcessing = state.status === 'processing'
  const isComplete = state.status === 'complete'
  const isError = state.status === 'error'
  const isBusy = isUploading || isProcessing
  const isDemoBusy = isDemo && !demoResult && file !== null

  return (
    <Layout title="Upload Training Video">
      <div className="max-w-2xl space-y-6">

        {/* ── Upload form ─────────────────────────────────────────────── */}
        {(isIdle || isError) && !demoResult && (
          <>
            <p className="text-gray-400 text-sm">
              Upload a video of your training session and get AI-powered developmental feedback.
            </p>

            <Dropzone file={file} onFile={setFile} disabled={isBusy} />

            {/* Drill type */}
            <div>
              <label className="block text-sm font-medium text-gray-400 mb-2">
                Drill Type
              </label>
              <select
                value={drillType}
                onChange={(e) => setDrillType(e.target.value)}
                className="w-full bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-orange-500"
              >
                {[
                  { value: 'shooting', label: 'Shooting' },
                  { value: 'ball_handling', label: 'Dribbling / Ball Handling' },
                ].map(({ value, label }) => (
                  <option key={value} value={value}>{label}</option>
                ))}
              </select>
            </div>

            {/* Optional name */}
            <div>
              <label className="block text-sm font-medium text-gray-400 mb-2">
                Session Name <span className="text-gray-600">(optional)</span>
              </label>
              <input
                type="text"
                value={drillName}
                onChange={(e) => setDrillName(e.target.value)}
                placeholder="e.g. Tuesday morning shooting"
                className="w-full bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-orange-500 placeholder-gray-600"
              />
            </div>

            {isError && (
              <div className="bg-red-500/10 border border-red-500/30 rounded-xl p-4 text-red-400 text-sm">
                {state.error}
              </div>
            )}

            <div className="flex gap-3">
              <Button onClick={handleSubmit} disabled={!file}>
                Analyze Video
              </Button>
              <Button variant="ghost" onClick={() => navigate('/')}>
                Cancel
              </Button>
            </div>
          </>
        )}

        {/* ── Upload / processing progress ────────────────────────────── */}
        {(isBusy || isDemoBusy) && (
          <div className="space-y-6">
            <div className="text-center py-4">
              <p className="text-3xl mb-4">⚙️</p>
              <h3 className="text-lg font-semibold text-white mb-1">
                {isUploading ? 'Uploading…' : 'Analyzing your video…'}
              </h3>
              <p className="text-gray-500 text-sm">
                {isUploading
                  ? 'Sending your video to the server'
                  : 'Running YOLO detection, pose analysis, and shot tracking'}
              </p>
            </div>

            <ProgressBar pct={isUploading ? 5 : state.progress} />

            <p className="text-center text-gray-600 text-sm">
              {isUploading ? '' : `${state.progress}% complete`}
            </p>

            <p className="text-center text-xs text-gray-700">
              Processing time depends on video length. Please keep this tab open.
            </p>
          </div>
        )}

        {/* ── Results ─────────────────────────────────────────────────── */}
        {isComplete && state.sessionId && (
          <ResultsView
            sessionId={state.sessionId}
            summary={state.summary as Summary ?? {}}
            feedback={state.feedback as Feedback ?? {}}
          />
        )}

        {demoResult && (
          <>
            <video
              src={demoResult.summary.annotated_url}
              controls
              autoPlay
              muted
              loop
              className="w-full rounded-xl"
            />
            <ResultsView
              sessionId={1}
              summary={demoResult.summary as Summary}
              feedback={demoResult.feedback as Feedback}
            />
          </>
        )}
      </div>
    </Layout>
  )
}
