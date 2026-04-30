import { useState, useEffect } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import {
  RadarChart, PolarGrid, PolarAngleAxis, Radar, ResponsiveContainer,
  LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid,
} from 'recharts'
import { getDashboard, type DashboardData, type RecentSession } from '../api/dashboard'
import { useUserStore } from '../stores/userStore'
import { Layout } from '../components/shared/Layout'
import { Button } from '../components/shared/Button'
import { SkeletonCard } from '../components/shared/SkeletonLoader'

const RADAR_AXES = ['shooting', 'consistency', 'ball_handling', 'footwork', 'conditioning']

function SkillRadar({ data }: { data: DashboardData['radar'] }) {
  const chartData = RADAR_AXES.map((key) => ({
    axis: key.replace('_', ' '),
    value: data[key as keyof typeof data] ?? 0,
  }))

  return (
    <div className="bg-gray-900 rounded-xl p-4">
      <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-4">Skill Radar</h3>
      <ResponsiveContainer width="100%" height={220}>
        <RadarChart data={chartData} cx="50%" cy="50%" outerRadius="70%">
          <PolarGrid stroke="#374151" />
          <PolarAngleAxis dataKey="axis" tick={{ fill: '#9ca3af', fontSize: 11 }} />
          <Radar
            dataKey="value"
            stroke="#f97316"
            fill="#f97316"
            fillOpacity={0.25}
            dot={{ fill: '#f97316', r: 3 }}
          />
        </RadarChart>
      </ResponsiveContainer>
    </div>
  )
}

function ProgressLine({
  title,
  data,
}: {
  title: string
  data: { value: number; recorded_at: string }[]
}) {
  if (data.length < 2) return null
  const chartData = data.map((d) => ({
    date: new Date(d.recorded_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
    value: Math.round(d.value * 10) / 10,
  }))

  return (
    <div className="bg-gray-900 rounded-xl p-4">
      <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-3">{title}</h3>
      <ResponsiveContainer width="100%" height={120}>
        <LineChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
          <XAxis dataKey="date" tick={{ fill: '#6b7280', fontSize: 10 }} />
          <YAxis tick={{ fill: '#6b7280', fontSize: 10 }} width={32} />
          <Tooltip
            contentStyle={{ background: '#111827', border: '1px solid #374151', borderRadius: 8 }}
            labelStyle={{ color: '#9ca3af' }}
            itemStyle={{ color: '#f97316' }}
          />
          <Line type="monotone" dataKey="value" stroke="#f97316" strokeWidth={2} dot={{ r: 3 }} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}

function RecentSessionRow({ session }: { session: RecentSession }) {
  const date = new Date(session.started_at).toLocaleDateString('en-US', {
    month: 'short', day: 'numeric',
  })
  const duration = session.duration_s ? `${Math.round(session.duration_s / 60)}m` : '—'

  return (
    <Link
      to={`/review/${session.id}`}
      className="flex items-center justify-between px-4 py-3 hover:bg-gray-800 transition-colors rounded-lg"
    >
      <div>
        <p className="text-sm font-medium text-white">{session.drill_name}</p>
        <p className="text-xs text-gray-500 capitalize">{session.drill_type} · {date} · {duration}</p>
      </div>
      {session.shot_percentage != null && (
        <span className="font-mono text-sm font-bold text-orange-400">
          {session.shot_percentage.toFixed(0)}%
        </span>
      )}
    </Link>
  )
}

export function Dashboard() {
  const navigate = useNavigate()
  const profile = useUserStore((s) => s.profile)
  const [data, setData] = useState<DashboardData | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getDashboard()
      .then(setData)
      .catch(() => null)
      .finally(() => setLoading(false))
  }, [])

  const greeting = profile?.user?.username ? `Hey, ${profile.user.username}` : 'Dashboard'

  return (
    <Layout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold text-white">{greeting}</h2>
            <p className="text-gray-500 text-sm">
              {data ? `${data.total_sessions} sessions completed` : 'Track your progress'}
            </p>
          </div>
          <div className="flex gap-2">
            <Button onClick={() => navigate('/workouts')}>Start Workout</Button>
            <Button variant="ghost" onClick={() => navigate('/upload')}>Upload Video</Button>
          </div>
        </div>

        {loading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {Array.from({ length: 6 }).map((_, i) => <SkeletonCard key={i} />)}
          </div>
        ) : data ? (
          <>
            {/* Charts row */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              <SkillRadar data={data.radar} />

              {Object.entries(data.benchmark_history)
                .filter(([, entries]) => entries.length >= 2)
                .slice(0, 2)
                .map(([type, entries]) => (
                  <ProgressLine
                    key={type}
                    title={type.replace(/_/g, ' ')}
                    data={entries}
                  />
                ))}
            </div>

            {/* Quick benchmarks */}
            {Object.keys(data.latest_benchmarks).length > 0 && (
              <div className="bg-gray-900 rounded-xl p-4">
                <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-3">
                  Latest Benchmarks
                </h3>
                <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3">
                  {Object.entries(data.latest_benchmarks).map(([type, value]) => (
                    <div key={type} className="text-center">
                      <p className="text-xs text-gray-500 capitalize mb-1">
                        {type.replace(/_/g, ' ')}
                      </p>
                      <p className="text-lg font-bold font-mono text-white">
                        {Math.round(value * 10) / 10}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Recent sessions */}
            {data.recent_sessions.length > 0 && (
              <div className="bg-gray-900 rounded-xl overflow-hidden">
                <div className="px-4 py-3 border-b border-gray-800">
                  <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider">
                    Recent Sessions
                  </h3>
                </div>
                <div className="divide-y divide-gray-800/50">
                  {data.recent_sessions.map((s) => (
                    <RecentSessionRow key={s.id} session={s} />
                  ))}
                </div>
              </div>
            )}

            {data.total_sessions === 0 && (
              <div className="text-center py-16">
                <p className="text-gray-600 text-lg mb-4">No sessions yet</p>
                <Button onClick={() => navigate('/workouts')}>Start Your First Drill</Button>
              </div>
            )}
          </>
        ) : (
          <div className="text-center py-16">
            <p className="text-gray-600">Could not load dashboard.</p>
          </div>
        )}
      </div>
    </Layout>
  )
}
