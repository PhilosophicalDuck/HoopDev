import { create } from 'zustand'

interface ShotCounts { made: number; attempted: number }

interface SessionState {
  sessionId: number | null
  drillType: string
  drillName: string
  isActive: boolean
  isPaused: boolean
  shotCounts: ShotCounts
  elapsedSeconds: number
  setSession: (id: number, drillType: string, drillName: string) => void
  setActive: (active: boolean) => void
  setPaused: (paused: boolean) => void
  updateShots: (counts: ShotCounts) => void
  tickTimer: () => void
  reset: () => void
}

export const useSessionStore = create<SessionState>((set) => ({
  sessionId: null,
  drillType: 'shooting',
  drillName: '',
  isActive: false,
  isPaused: false,
  shotCounts: { made: 0, attempted: 0 },
  elapsedSeconds: 0,
  setSession: (id, drillType, drillName) =>
    set({ sessionId: id, drillType, drillName }),
  setActive: (isActive) => set({ isActive }),
  setPaused: (isPaused) => set({ isPaused }),
  updateShots: (shotCounts) => set({ shotCounts }),
  tickTimer: () => set((s) => ({ elapsedSeconds: s.elapsedSeconds + 1 })),
  reset: () =>
    set({
      sessionId: null, isActive: false, isPaused: false,
      shotCounts: { made: 0, attempted: 0 }, elapsedSeconds: 0,
    }),
}))
