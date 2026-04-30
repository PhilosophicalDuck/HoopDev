import { useCallback, useEffect, useState } from 'react'
import { useVoiceStore } from '../stores/voiceStore'

export type SpeechPersona = 'sully' | 'buddy'

const PERSONA_SETTINGS: Record<SpeechPersona, { rate: number; pitch: number; preferMale: boolean }> = {
  sully: { rate: 0.88, pitch: 0.75, preferMale: true  },
  buddy: { rate: 1.15, pitch: 1.25, preferMale: false },
}

function pickVoice(preferMale: boolean): SpeechSynthesisVoice | null {
  const voices = window.speechSynthesis.getVoices()
  if (!voices.length) return null
  const pool = voices.filter(v => v.lang.startsWith('en'))
  const maleKeywords  = ['male', 'david', 'daniel', 'james', 'mark', 'fred', 'alex', 'tom', 'george', 'ryan']
  const femaleKeywords = ['female', 'samantha', 'victoria', 'karen', 'moira', 'fiona', 'allison', 'ava']
  const keywords = preferMale ? maleKeywords : femaleKeywords
  return pool.find(v => keywords.some(k => v.name.toLowerCase().includes(k))) ?? pool[0] ?? null
}

export function useSpeech() {
  const { enabled, toggle } = useVoiceStore()
  const [voicesReady, setVoicesReady] = useState(false)
  const supported = typeof window !== 'undefined' && 'speechSynthesis' in window

  useEffect(() => {
    if (!supported) return
    if (window.speechSynthesis.getVoices().length) {
      setVoicesReady(true)
    } else {
      window.speechSynthesis.addEventListener('voiceschanged', () => setVoicesReady(true), { once: true })
    }
  }, [supported])

  const speak = useCallback((text: string, persona: SpeechPersona = 'buddy') => {
    if (!supported || !enabled || !voicesReady) return
    window.speechSynthesis.cancel()
    const utterance = new SpeechSynthesisUtterance(text)
    const settings = PERSONA_SETTINGS[persona]
    const voice = pickVoice(settings.preferMale)
    if (voice) utterance.voice = voice
    utterance.rate  = settings.rate
    utterance.pitch = settings.pitch
    window.speechSynthesis.speak(utterance)
  }, [supported, enabled, voicesReady])

  const stop = useCallback(() => {
    if (supported) window.speechSynthesis.cancel()
  }, [supported])

  return { speak, stop, toggle, enabled, supported }
}
