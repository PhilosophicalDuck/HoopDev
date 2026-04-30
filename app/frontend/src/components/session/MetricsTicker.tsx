import { useFeedbackStore } from '../../stores/feedbackStore'
import { useSessionStore } from '../../stores/sessionStore'

function colorByRange(value: number | undefined, min: number, max: number) {
  if (value === undefined || value === null) return 'text-gray-500'
  if (value >= min && value <= max) return 'text-green-400'
  const pct = value < min ? (min - value) / min : (value - max) / max
  return pct > 0.25 ? 'text-red-400' : 'text-yellow-400'
}

interface MetricRowProps {
  label: string
  value: string
  colorClass: string
  icon?: string
}

function MetricRow({ label, value, colorClass, icon }: MetricRowProps) {
  return (
    <div className="flex justify-between items-center py-2 border-b border-gray-800">
      <span className="text-gray-400 text-sm">{icon} {label}</span>
      <span className={`font-mono font-bold text-base ${colorClass}`}>{value}</span>
    </div>
  )
}

export function MetricsTicker() {
  const metrics = useFeedbackStore((s) => s.latestMetrics)
  const shots = useSessionStore((s) => s.shotCounts)

  const fgPct = shots.attempted > 0
    ? Math.round((shots.made / shots.attempted) * 100)
    : null

  return (
    <div className="bg-gray-900 rounded-xl p-4 space-y-0.5">
      <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">
        Live Metrics
      </h3>

      <MetricRow
        label="Field Goal %"
        value={fgPct !== null ? `${shots.made}/${shots.attempted} (${fgPct}%)` : '—'}
        colorClass={colorByRange(fgPct, 40, 100)}
        icon="🏀"
      />

      <MetricRow
        label="Elbow Angle"
        value={metrics?.elbow_angle != null ? `${metrics.elbow_angle.toFixed(0)}°` : '—'}
        colorClass={colorByRange(metrics?.elbow_angle, 75, 105)}
        icon="💪"
      />

      <MetricRow
        label="Shot State"
        value={metrics?.shot_state ?? '—'}
        colorClass={metrics?.shot_state === 'TRACKING' ? 'text-yellow-400' : 'text-gray-400'}
        icon="🎯"
      />

      <MetricRow
        label="Speed"
        value={metrics?.speed_px_s != null ? `${metrics.speed_px_s.toFixed(0)} px/s` : '—'}
        colorClass={colorByRange(metrics?.speed_px_s, 30, 300)}
        icon="⚡"
      />

      <MetricRow
        label="Ball"
        value={metrics?.ball_detected ? 'Detected ✓' : 'Not found'}
        colorClass={metrics?.ball_detected ? 'text-green-400' : 'text-gray-500'}
        icon="🟠"
      />

      <MetricRow
        label="Hoop"
        value={metrics?.hoop_detected ? 'In frame ✓' : 'Not visible'}
        colorClass={metrics?.hoop_detected ? 'text-green-400' : 'text-gray-500'}
        icon="🔵"
      />
    </div>
  )
}
