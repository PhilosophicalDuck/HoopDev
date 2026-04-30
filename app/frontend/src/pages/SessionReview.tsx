import { useEffect, useState } from 'react'
import { useParams, useLocation, useNavigate, Link } from 'react-router-dom'
import { getSession, type SessionDetail } from '../api/sessions'
import { Layout } from '../components/shared/Layout'
import { Button } from '../components/shared/Button'
import { Skeleton } from '../components/shared/SkeletonLoader'

interface LocationState {
  drill_name?: string
  drill_type?: string
  summary?: object
  feedback?: { strengths?: string[]; improvements?: string[] }
  highlight_clip_ids?: number[]
  demo_metrics?: {
    shots_made: number; shots_attempted: number; shot_percentage: number
    avg_release_elbow_angle: number | null; avg_arc_angle_deg: number | null
    follow_through_ratio: number | null
  }
}

function StatCard({ label, value, sub }: { label: string; value: string; sub?: string }) {
  return (
    <div className="bg-gray-900 rounded-xl p-4 text-center">
      <p className="text-xs text-gray-500 uppercase tracking-wider mb-1">{label}</p>
      <p className="text-2xl font-bold font-mono text-white">{value}</p>
      {sub && <p className="text-xs text-gray-600 mt-0.5">{sub}</p>}
    </div>
  )
}

export function SessionReview() {
  const { sessionId } = useParams<{ sessionId: string }>()
  const location = useLocation()
  const navigate = useNavigate()
  const state = location.state as LocationState | null

  const [session, setSession] = useState<SessionDetail | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!sessionId || sessionId === 'demo') {
      setLoading(false)
      return
    }
    getSession(parseInt(sessionId, 10))
      .then(setSession)
      .catch(() => null)
      .finally(() => setLoading(false))
  }, [sessionId])

  const metrics = state?.demo_metrics ?? session?.metrics
  const feedback = state?.feedback ?? (session?.metrics as { coaching_feedback_json?: { strengths?: string[]; improvements?: string[] } } | undefined)?.coaching_feedback_json

  if (loading) {
    return (
      <Layout title="Session Review">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          {Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-24" />)}
        </div>
      </Layout>
    )
  }

  const fgPct = metrics?.shot_percentage != null
    ? `${metrics.shot_percentage.toFixed(0)}%`
    : '—'

  return (
    <Layout title="Session Review">
      <div className="max-w-3xl space-y-6">
        {/* Session info */}
        {(state?.drill_name ?? session?.drill_name) && (
          <div className="flex items-center gap-3 text-sm text-gray-500">
            <span className="text-white font-medium">
              {state?.drill_name ?? session?.drill_name}
            </span>
            <span>·</span>
            <span>{state?.drill_type ?? session?.drill_type}</span>
            {session?.duration_s && (
              <>
                <span>·</span>
                <span>{Math.round(session.duration_s / 60)} min</span>
              </>
            )}
          </div>
        )}

        {/* Key metrics */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <StatCard
            label="Field Goal %"
            value={fgPct}
            sub={metrics ? `${metrics.shots_made}/${metrics.shots_attempted}` : undefined}
          />
          <StatCard
            label="Elbow Angle"
            value={metrics?.avg_release_elbow_angle != null
              ? `${metrics.avg_release_elbow_angle.toFixed(0)}°`
              : '—'}
            sub="target: 75-105°"
          />
          <StatCard
            label="Arc Angle"
            value={metrics?.avg_arc_angle_deg != null
              ? `${metrics.avg_arc_angle_deg.toFixed(0)}°`
              : '—'}
            sub="target: 42-58°"
          />
          <StatCard
            label="Follow-through"
            value={metrics?.follow_through_ratio != null
              ? `${(metrics.follow_through_ratio * 100).toFixed(0)}%`
              : '—'}
          />
        </div>

        {/* Feedback */}
        {feedback && (
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
        )}

        {/* Highlights */}
        {state?.highlight_clip_ids && state.highlight_clip_ids.length > 0 && (
          <div className="bg-gray-900 rounded-xl p-4">
            <h3 className="font-semibold text-white mb-2">
              {state.highlight_clip_ids.length} highlight{state.highlight_clip_ids.length > 1 ? 's' : ''} saved
            </h3>
            <Link to="/highlights" className="text-sm text-orange-400 hover:text-orange-300">
              View in Highlights →
            </Link>
          </div>
        )}

        {/* Actions */}
        <div className="flex gap-3">
          <Button onClick={() => navigate('/workouts')}>Train Again</Button>
          <Button variant="ghost" onClick={() => navigate('/')}>Dashboard</Button>
        </div>
      </div>
    </Layout>
  )
}
