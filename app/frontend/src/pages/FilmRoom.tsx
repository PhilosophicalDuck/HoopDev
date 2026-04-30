import { useState } from 'react'
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, ReferenceArea,
  BarChart, Bar, Cell,
} from 'recharts'
import { Layout } from '../components/shared/Layout'

// ── View data ─────────────────────────────────────────────────────────────────

type ViewKey = 'release_angle' | 'elbow_angle' | 'shot_arc' | 'fatigue' | 'overview'
type Range = 'all' | 'first' | 'last'

interface ViewConfig {
  label: string
  unit: string
  avg: number | null
  ideal: [number, number] | null
  yMin: number
  yMax: number
  data: number[]
}

const RAW_VIEWS: Record<ViewKey, ViewConfig> = {
  release_angle: {
    label: 'Release Angle',
    unit: '°',
    avg: 47.2,
    ideal: [42, 58],
    yMin: 30,
    yMax: 65,
    data: [45.2, 48.1, 46.8, 49.3, 51.0, 46.1, 48.7, 50.2, 47.4, 49.1,
           47.8, 45.9, 47.0, 50.1, 48.9, 44.8, 43.5, 42.9, 42.1, 46.3],
  },
  elbow_angle: {
    label: 'Elbow Angle',
    unit: '°',
    avg: 91.0,
    ideal: [75, 105],
    yMin: 60,
    yMax: 120,
    data: [88.2, 92.4, 90.1, 95.3, 91.7, 89.0, 93.2, 94.1, 91.5, 88.4,
           92.8, 95.0, 90.3, 88.1, 91.2, 87.3, 85.1, 89.4, 92.1, 90.7],
  },
  shot_arc: {
    label: 'Shot Arc',
    unit: '°',
    avg: 46.2,
    ideal: [42, 58],
    yMin: 30,
    yMax: 65,
    data: [44.1, 47.0, 45.8, 48.2, 50.1, 44.9, 47.6, 49.1, 46.3, 48.0,
           46.7, 44.8, 45.9, 49.0, 47.8, 43.7, 42.4, 41.8, 41.0, 45.2],
  },
  fatigue: {
    label: 'Fatigue Index',
    unit: '%',
    avg: 28.5,
    ideal: [0, 35],
    yMin: 0,
    yMax: 60,
    data: [8, 10, 12, 11, 14, 16, 18, 20, 22, 24,
           26, 30, 32, 33, 36, 40, 43, 46, 49, 52],
  },
  overview: {
    label: 'Session Overview',
    unit: '',
    avg: null,
    ideal: null,
    yMin: 0,
    yMax: 100,
    data: [],
  },
}

const OVERVIEW_BARS = [
  { name: 'FG %',       value: 91,  color: '#22c55e' },
  { name: 'Arc Avg°',   value: 47,  color: '#f97316' },
  { name: 'Elbow°/10',  value: 91,  color: '#f97316' },
  { name: 'Follow-Thru',value: 0,   color: '#ef4444' },
]

function buildChartData(view: ViewKey, range: Range) {
  const raw = RAW_VIEWS[view].data
  const n = raw.length
  let slice = raw
  if (range === 'first') slice = raw.slice(0, Math.ceil(n / 2))
  if (range === 'last')  slice = raw.slice(Math.floor(n / 2))
  return slice.map((v, i) => ({ shot: i + (range === 'last' ? Math.floor(n / 2) + 1 : 1), value: v }))
}


// ── Custom tooltip ────────────────────────────────────────────────────────────

function ChartTip({ active, payload, unit }: { active?: boolean; payload?: { value: number }[]; unit: string }) {
  if (!active || !payload?.length) return null
  return (
    <div className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-1.5 text-sm text-white">
      {payload[0].value.toFixed(1)}{unit}
    </div>
  )
}

// ── Main component ────────────────────────────────────────────────────────────

export function FilmRoom() {
  const [currentView, setCurrentView] = useState<ViewKey>('release_angle')
  const [range, setRange] = useState<Range>('all')

  const view = RAW_VIEWS[currentView]
  const chartData = buildChartData(currentView, range)
  const lastFive = view.data.slice(-5).map((v, i) => ({
    shot: view.data.length - 4 + i,
    value: v,
    inZone: view.ideal ? v >= view.ideal[0] && v <= view.ideal[1] : true,
  }))

  function handleViewChange(v: ViewKey) {
    setCurrentView(v)
    setRange('all')
  }

  return (
    <Layout title="Stat Box">
      <div className="max-w-3xl space-y-4">

        {/* ── Left: Chart panel ──────────────────────────────────── */}
        <div className="flex-1 space-y-4 min-w-0">

          {/* Controls row */}
          <div className="flex items-center gap-3 flex-wrap">
            <select
              value={currentView}
              onChange={e => handleViewChange(e.target.value as ViewKey)}
              className="bg-gray-900 border border-gray-700 text-white text-sm rounded-lg px-3 py-2 focus:outline-none focus:border-orange-500"
            >
              {(Object.keys(RAW_VIEWS) as ViewKey[]).map(k => (
                <option key={k} value={k}>{RAW_VIEWS[k].label}</option>
              ))}
            </select>

            {currentView !== 'overview' && (
              <div className="flex gap-1 bg-gray-900 border border-gray-700 rounded-lg p-1">
                {(['all', 'first', 'last'] as Range[]).map(r => (
                  <button
                    key={r}
                    onClick={() => setRange(r)}
                    className={`text-xs px-3 py-1 rounded-md transition-colors ${
                      range === r ? 'bg-orange-500 text-white' : 'text-gray-400 hover:text-white'
                    }`}
                  >
                    {r === 'all' ? 'All' : r === 'first' ? 'First Half' : 'Last Half'}
                  </button>
                ))}
              </div>
            )}

            {view.avg != null && (
              <span className="text-sm text-gray-400">
                Avg: <span className="text-white font-mono font-semibold">{view.avg.toFixed(1)}{view.unit}</span>
                {view.ideal && (
                  <span className="text-gray-600 ml-2">· ideal {view.ideal[0]}–{view.ideal[1]}{view.unit}</span>
                )}
              </span>
            )}
          </div>

          {/* Chart */}
          <div className="bg-gray-900 rounded-xl p-4" style={{ height: 300 }}>
            <p className="text-xs text-gray-500 uppercase tracking-wider mb-3">{view.label}</p>
            {currentView === 'overview' ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={OVERVIEW_BARS} margin={{ top: 4, right: 8, bottom: 4, left: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(55,65,81,0.5)" />
                  <XAxis dataKey="name" tick={{ fill: '#6b7280', fontSize: 11 }} />
                  <YAxis tick={{ fill: '#6b7280', fontSize: 11 }} domain={[0, 100]} />
                  <Tooltip content={<ChartTip unit="%" />} />
                  <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                    {OVERVIEW_BARS.map((entry, i) => (
                      <Cell key={i} fill={entry.color} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={chartData} margin={{ top: 4, right: 8, bottom: 4, left: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(55,65,81,0.5)" />
                  <XAxis
                    dataKey="shot"
                    tick={{ fill: '#6b7280', fontSize: 11 }}
                    label={{ value: 'Shot #', position: 'insideBottom', offset: -2, fill: '#4b5563', fontSize: 11 }}
                  />
                  <YAxis
                    domain={[view.yMin, view.yMax]}
                    tick={{ fill: '#6b7280', fontSize: 11 }}
                    tickFormatter={v => `${v}${view.unit}`}
                  />
                  <Tooltip content={<ChartTip unit={view.unit} />} />
                  {view.ideal && (
                    <ReferenceArea
                      y1={view.ideal[0]}
                      y2={view.ideal[1]}
                      fill="rgba(34,197,94,0.08)"
                      stroke="rgba(34,197,94,0.3)"
                      strokeDasharray="4 4"
                    />
                  )}
                  <Line
                    type="monotone"
                    dataKey="value"
                    stroke="#f97316"
                    strokeWidth={2}
                    dot={(props) => {
                      const { cx, cy, payload } = props
                      const inZone = view.ideal
                        ? payload.value >= view.ideal[0] && payload.value <= view.ideal[1]
                        : true
                      return <circle key={`dot-${payload.shot}`} cx={cx} cy={cy} r={3.5} fill={inZone ? '#22c55e' : '#f97316'} stroke="none" />
                    }}
                    activeDot={{ r: 5, fill: '#f97316' }}
                  />
                </LineChart>
              </ResponsiveContainer>
            )}
          </div>

          {/* Last 5 shots table */}
          {currentView !== 'overview' && (
            <div className="bg-gray-900 rounded-xl p-4">
              <p className="text-xs text-gray-500 uppercase tracking-wider mb-3">Last 5 Shots</p>
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-gray-600 text-xs">
                    <th className="text-left font-normal pb-2">Shot</th>
                    <th className="text-right font-normal pb-2">{view.label}</th>
                    <th className="text-right font-normal pb-2">Zone</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-800">
                  {lastFive.map(row => (
                    <tr key={row.shot}>
                      <td className="py-1.5 text-gray-400">#{row.shot}</td>
                      <td className="py-1.5 text-right font-mono text-white">
                        {row.value.toFixed(1)}{view.unit}
                      </td>
                      <td className="py-1.5 text-right">
                        <span className={`text-xs font-medium ${row.inZone ? 'text-green-400' : 'text-orange-400'}`}>
                          {row.inZone ? '✓ ideal' : '→ off'}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

      </div>
    </Layout>
  )
}
