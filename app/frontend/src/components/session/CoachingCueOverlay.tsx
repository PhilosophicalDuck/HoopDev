import { useEffect, useState } from 'react'
import { useFeedbackStore, type CoachingCue } from '../../stores/feedbackStore'

const SEVERITY_STYLES = {
  success: 'bg-green-500 text-white border-green-400',
  warning: 'bg-orange-500 text-white border-orange-400',
  info: 'bg-blue-500 text-white border-blue-400',
}

function CueBanner({ cue }: { cue: CoachingCue }) {
  const [expanded, setExpanded] = useState(false)
  const style = SEVERITY_STYLES[cue.severity] ?? SEVERITY_STYLES.info

  return (
    <div
      className={`rounded-xl border px-4 py-3 shadow-2xl cursor-pointer transition-all ${style}`}
      onClick={() => setExpanded(!expanded)}
    >
      <p className="font-bold text-lg leading-tight">{cue.text}</p>
      {expanded && (
        <p className="text-sm mt-1 opacity-90">{cue.detail}</p>
      )}
      {!expanded && <p className="text-xs opacity-70 mt-0.5">Tap for details</p>}
    </div>
  )
}

export function CoachingCueOverlay() {
  const { latestCue, cueVisible, cueHistory } = useFeedbackStore()

  return (
    <div className="absolute inset-0 pointer-events-none flex flex-col justify-between p-4 z-10">
      {/* Main cue banner — top center */}
      <div className="flex justify-center pointer-events-auto">
        {cueVisible && latestCue ? (
          <div className="animate-bounce">
            <CueBanner cue={latestCue} />
          </div>
        ) : (
          <div className="h-16" /> /* placeholder height */
        )}
      </div>

      {/* Recent cue history — bottom left, small */}
      <div className="flex flex-col gap-1 pointer-events-none">
        {cueHistory.slice(1, 4).map((cue, i) => (
          <div
            key={`${cue.id}-${i}`}
            className="text-xs bg-black/50 text-gray-300 px-2 py-1 rounded backdrop-blur-sm w-fit"
          >
            {cue.text}
          </div>
        ))}
      </div>
    </div>
  )
}
