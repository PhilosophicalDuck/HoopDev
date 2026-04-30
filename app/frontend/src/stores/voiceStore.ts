import { create } from 'zustand'

interface VoiceState {
  enabled: boolean
  toggle: () => void
}

const STORAGE_KEY = 'coach_voice_enabled'

export const useVoiceStore = create<VoiceState>((set) => ({
  enabled: localStorage.getItem(STORAGE_KEY) !== 'false',
  toggle: () =>
    set((s) => {
      const next = !s.enabled
      localStorage.setItem(STORAGE_KEY, String(next))
      return { enabled: next }
    }),
}))
