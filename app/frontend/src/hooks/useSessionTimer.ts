import { useEffect } from 'react'
import { useSessionStore } from '../stores/sessionStore'

export function useSessionTimer() {
  const { isActive, isPaused, tickTimer } = useSessionStore()

  useEffect(() => {
    if (!isActive || isPaused) return
    const interval = setInterval(tickTimer, 1000)
    return () => clearInterval(interval)
  }, [isActive, isPaused, tickTimer])
}
