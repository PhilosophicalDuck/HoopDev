import { useSessionStore } from '../../stores/sessionStore'

interface SessionControlsProps {
  onPause: () => void
  onResume: () => void
  onStop: () => void
}

export function SessionControls({ onPause, onResume, onStop }: SessionControlsProps) {
  const { isActive, isPaused } = useSessionStore()

  if (!isActive) {
    return (
      <div className="bg-gray-900 rounded-xl p-4 text-center">
        <p className="text-gray-500 text-sm">Connecting to camera...</p>
      </div>
    )
  }

  return (
    <div className="bg-gray-900 rounded-xl p-4 flex gap-3">
      {isPaused ? (
        <button
          onClick={onResume}
          className="flex-1 bg-green-600 hover:bg-green-500 text-white font-semibold py-3 rounded-lg transition-colors"
        >
          ▶ Resume
        </button>
      ) : (
        <button
          onClick={onPause}
          className="flex-1 bg-yellow-600 hover:bg-yellow-500 text-white font-semibold py-3 rounded-lg transition-colors"
        >
          ⏸ Pause
        </button>
      )}
      <button
        onClick={onStop}
        className="flex-1 bg-red-700 hover:bg-red-600 text-white font-semibold py-3 rounded-lg transition-colors"
      >
        ⏹ Stop
      </button>
    </div>
  )
}
