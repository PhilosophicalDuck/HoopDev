import { create } from 'zustand'

export interface CoachingCue {
  id: string; text: string; detail: string
  severity: 'info' | 'warning' | 'success'
  category: string; duration_ms: number
}

export interface FrameMetrics {
  shot_state: string; elbow_angle?: number; arc_angle?: number
  follow_through?: boolean; speed_px_s: number
  is_release_frame: boolean; ball_detected: boolean; hoop_detected: boolean
}

interface FeedbackState {
  latestCue: CoachingCue | null
  cueVisible: boolean
  latestMetrics: FrameMetrics | null
  cueHistory: CoachingCue[]
  setCue: (cue: CoachingCue) => void
  dismissCue: () => void
  setMetrics: (metrics: FrameMetrics) => void
  reset: () => void
}

export const useFeedbackStore = create<FeedbackState>((set) => ({
  latestCue: null,
  cueVisible: false,
  latestMetrics: null,
  cueHistory: [],
  setCue: (cue) =>
    set((s) => ({
      latestCue: cue,
      cueVisible: true,
      cueHistory: [cue, ...s.cueHistory].slice(0, 20),
    })),
  dismissCue: () => set({ cueVisible: false }),
  setMetrics: (latestMetrics) => set({ latestMetrics }),
  reset: () => set({ latestCue: null, cueVisible: false, latestMetrics: null, cueHistory: [] }),
}))
