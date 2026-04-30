import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { UserProfile } from '../api/users'
import { DEMO_PROFILE } from '../demo/data'

interface UserState {
  token: string | null
  profile: UserProfile | null
  isDemo: boolean
  setToken: (token: string) => void
  setProfile: (profile: UserProfile) => void
  enterDemo: () => void
  logout: () => void
}

export const useUserStore = create<UserState>()(
  persist(
    (set) => ({
      token: null,
      profile: null,
      isDemo: false,
      setToken: (token) => {
        localStorage.setItem('access_token', token)
        set({ token })
      },
      setProfile: (profile) => set({ profile }),
      enterDemo: () => {
        localStorage.setItem('demo_mode', 'true')
        localStorage.setItem('access_token', 'demo-token')
        set({ token: 'demo-token', profile: DEMO_PROFILE as unknown as UserProfile, isDemo: true })
      },
      logout: () => {
        localStorage.removeItem('access_token')
        localStorage.removeItem('demo_mode')
        set({ token: null, profile: null, isDemo: false })
      },
    }),
    {
      name: 'user-store',
      onRehydrateStorage: () => (state) => {
        if (state?.isDemo) {
          state.profile = DEMO_PROFILE as unknown as UserProfile
        }
      },
    }
  )
)
