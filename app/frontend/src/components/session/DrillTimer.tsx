import { useSessionStore } from '../../stores/sessionStore'
import { useSessionTimer } from '../../hooks/useSessionTimer'

export function DrillTimer() {
  useSessionTimer()
  const { elapsedSeconds, drillName } = useSessionStore()

  const mins = Math.floor(elapsedSeconds / 60).toString().padStart(2, '0')
  const secs = (elapsedSeconds % 60).toString().padStart(2, '0')

  return (
    <div className="bg-gray-900 rounded-xl p-4 text-center">
      <p className="text-gray-400 text-xs uppercase tracking-wider mb-1">{drillName}</p>
      <p className="font-mono text-4xl font-bold text-white tracking-widest">
        {mins}:{secs}
      </p>
    </div>
  )
}
