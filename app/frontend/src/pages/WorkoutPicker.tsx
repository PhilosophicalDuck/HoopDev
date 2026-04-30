import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { recommend, getCatalog, type DrillCard, type WorkoutPlan } from '../api/workouts'
import { createSession } from '../api/sessions'
import { useSessionStore } from '../stores/sessionStore'
import { useUserStore } from '../stores/userStore'
import { DEMO_SESSION_DETAIL } from '../demo/mockData'
import { Layout } from '../components/shared/Layout'
import { Button } from '../components/shared/Button'
import { Badge } from '../components/shared/Badge'
import { Skeleton } from '../components/shared/SkeletonLoader'

const DURATIONS = [30, 60, 90]
const FOCUS_OPTIONS = ['shooting', 'ball_handling', 'footwork', 'conditioning']

const categoryColors: Record<string, 'orange' | 'green' | 'blue' | 'yellow' | 'red' | 'gray'> = {
  shooting: 'orange',
  ball_handling: 'blue',
  footwork: 'green',
  conditioning: 'red',
}

function DrillCardItem({ drill, onStart }: { drill: DrillCard; onStart: (d: DrillCard) => void }) {
  return (
    <div className="bg-gray-900 rounded-xl p-4 flex flex-col gap-3 hover:bg-gray-800 transition-colors">
      <div className="flex items-start justify-between gap-2">
        <div>
          <p className="font-semibold text-white">{drill.name}</p>
          {drill.description && (
            <p className="text-xs text-gray-500 mt-0.5">{drill.description}</p>
          )}
        </div>
        <Badge
          label={drill.category.replace('_', ' ')}
          color={categoryColors[drill.category] ?? 'gray'}
        />
      </div>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3 text-xs text-gray-500">
          <span>{drill.duration_min} min</span>
          {drill.cv_supported && (
            <span className="text-green-400">CV tracked</span>
          )}
        </div>
        <Button size="sm" onClick={() => onStart(drill)}>
          Start
        </Button>
      </div>
    </div>
  )
}

export function WorkoutPicker() {
  const navigate = useNavigate()
  const { setSession } = useSessionStore()
  const isDemo = useUserStore((s) => s.isDemo)
  const [tab, setTab] = useState<'recommended' | 'browse'>('recommended')
  const [duration, setDuration] = useState(60)
  const [focus, setFocus] = useState('')
  const [plan, setPlan] = useState<WorkoutPlan | null>(null)
  const [catalog, setCatalog] = useState<DrillCard[]>([])
  const [loadingPlan, setLoadingPlan] = useState(false)
  const [starting, setStarting] = useState(false)

  useEffect(() => {
    getCatalog().then((d) => setCatalog(d.drills)).catch(() => null)
  }, [])

  useEffect(() => {
    if (tab !== 'recommended') return
    setLoadingPlan(true)
    recommend(duration, focus || undefined)
      .then(setPlan)
      .catch(() => null)
      .finally(() => setLoadingPlan(false))
  }, [tab, duration, focus])

  async function startDrill(drill: DrillCard) {
    if (isDemo) {
      navigate('/session/demo', {
        state: { drillName: drill.name, drillType: drill.category },
      })
      return
    }

    setStarting(true)
    try {
      const session = await createSession(drill.category, drill.name)
      setSession(session.id, drill.category, drill.name)
      navigate(`/session/${session.id}`)
    } catch {
      setStarting(false)
    }
  }

  const displayedDrills = tab === 'recommended' ? (plan?.recommended ?? []) : catalog

  return (
    <Layout title="Choose Your Workout">
      {/* Controls */}
      <div className="flex flex-wrap items-center gap-4 mb-6">
        {/* Tab toggle */}
        <div className="flex bg-gray-900 rounded-lg p-1">
          {(['recommended', 'browse'] as const).map((t) => (
            <button
              key={t}
              onClick={() => setTab(t)}
              className={`px-4 py-1.5 rounded-md text-sm font-medium capitalize transition-colors ${
                tab === t ? 'bg-orange-500 text-white' : 'text-gray-400 hover:text-white'
              }`}
            >
              {t}
            </button>
          ))}
        </div>

        {tab === 'recommended' && (
          <>
            {/* Duration */}
            <div className="flex items-center gap-1">
              {DURATIONS.map((d) => (
                <button
                  key={d}
                  onClick={() => setDuration(d)}
                  className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                    duration === d
                      ? 'bg-gray-700 text-white'
                      : 'text-gray-500 hover:text-white'
                  }`}
                >
                  {d}m
                </button>
              ))}
            </div>

            {/* Focus */}
            <select
              value={focus}
              onChange={(e) => setFocus(e.target.value)}
              className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-1.5 text-sm text-white focus:outline-none"
            >
              <option value="">All focus areas</option>
              {FOCUS_OPTIONS.map((f) => (
                <option key={f} value={f}>{f.replace('_', ' ')}</option>
              ))}
            </select>
          </>
        )}
      </div>

      {/* Rationale */}
      {tab === 'recommended' && plan && (
        <div className="bg-orange-500/10 border border-orange-500/30 rounded-xl p-4 mb-6">
          <p className="text-sm text-orange-300">{plan.rationale}</p>
          <p className="text-xs text-gray-500 mt-1">
            {plan.total_duration_min} min total · focus: {plan.primary_focus.replace('_', ' ')} · {plan.skill_level}
          </p>
        </div>
      )}

      {/* Drill grid */}
      {loadingPlan ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {Array.from({ length: 6 }).map((_, i) => (
            <Skeleton key={i} className="h-32 w-full" />
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {displayedDrills.map((drill, i) => (
            <DrillCardItem
              key={`${drill.name}-${i}`}
              drill={drill}
              onStart={starting ? () => null : startDrill}
            />
          ))}
          {displayedDrills.length === 0 && (
            <p className="text-gray-600 col-span-3 text-center py-12">No drills found.</p>
          )}
        </div>
      )}
    </Layout>
  )
}
