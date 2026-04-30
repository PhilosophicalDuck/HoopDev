import { useState, useRef, useEffect } from 'react'
import { sendChatMessage, type Persona } from '../../api/chat'
import { useSessionStore } from '../../stores/sessionStore'
import { useUserStore } from '../../stores/userStore'
import { callOllamaChat } from '../../demo/ollamaChat'
import { DEMO_CHAT_REPLIES } from '../../demo/mockData'
import { useSpeech } from '../../hooks/useSpeech'

interface Message {
  role: 'user' | 'coach'
  text: string
}

const PERSONA_KEY = 'coach_persona'

const PERSONA_META = {
  sully: { name: 'Coach Sully', icon: '🏆', color: 'text-blue-400', border: 'border-blue-500' },
  buddy: { name: 'Buddy',       icon: '🔥', color: 'text-orange-400', border: 'border-orange-500' },
}

export function CoachChat() {
  const [open, setOpen] = useState(false)
  const [persona, setPersona] = useState<Persona>(
    () => (localStorage.getItem(PERSONA_KEY) as Persona) ?? 'buddy'
  )
  const [messages, setMessages] = useState<Record<Persona, Message[]>>({ sully: [], buddy: [] })
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [ollamaMode, setOllamaMode] = useState(
    () => localStorage.getItem('chat_mode') === 'ollama'
  )
  const bottomRef = useRef<HTMLDivElement>(null)

  const { speak, toggle: toggleVoice, enabled: voiceEnabled } = useSpeech()
  const isDemo = useUserStore((s) => s.isDemo)
  const { shotCounts, drillType } = useSessionStore()

  function toggleChatMode() {
    const next = !ollamaMode
    setOllamaMode(next)
    localStorage.setItem('chat_mode', next ? 'ollama' : 'mock')
    setMessages({ sully: [], buddy: [] })
  }

  // Build session context from store — null when no active session data
  const sessionData = shotCounts.attempted > 0
    ? { shots_made: shotCounts.made, shots_attempted: shotCounts.attempted, drill_type: drillType }
    : null

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, persona, loading])

  function handlePersonaChange(p: Persona) {
    setPersona(p)
    localStorage.setItem(PERSONA_KEY, p)
  }

  async function handleSend() {
    const text = input.trim()
    if (!text || loading) return
    setInput('')
    setMessages(prev => ({ ...prev, [persona]: [...prev[persona], { role: 'user', text }] }))
    setLoading(true)
    try {
      let reply: string
      if (isDemo && ollamaMode) {
        // Live Ollama — call local model directly, no backend needed
        const history = messages[persona].map(m => ({
          role: (m.role === 'coach' ? 'assistant' : 'user') as 'user' | 'assistant',
          content: m.text,
        }))
        reply = await callOllamaChat(text, persona, sessionData as Record<string, unknown> | null, history)
      } else if (isDemo) {
        // Mock — return a random canned reply after a short delay
        await new Promise(r => setTimeout(r, 600))
        const pool = DEMO_CHAT_REPLIES[persona] ?? DEMO_CHAT_REPLIES.buddy
        reply = pool[Math.floor(Math.random() * pool.length)]
      } else {
        // Production — use the real backend API
        reply = await sendChatMessage(text, persona, sessionData)
      }
      setMessages(prev => ({ ...prev, [persona]: [...prev[persona], { role: 'coach', text: reply }] }))
      speak(reply, persona)
    } catch {
      const fallback = isDemo && ollamaMode
        ? 'Ollama is not reachable. Make sure it is running on your machine (ollama serve).'
        : 'Connection issue — try again.'
      setMessages(prev => ({ ...prev, [persona]: [...prev[persona], { role: 'coach', text: fallback }] }))
    } finally {
      setLoading(false)
    }
  }

  const meta = PERSONA_META[persona]

  return (
    <div className="fixed bottom-6 right-6 z-50 flex flex-col items-end gap-3">
      {/* Chat panel */}
      {open && (
        <div className="w-80 bg-gray-900 border border-gray-700 rounded-2xl shadow-2xl flex flex-col overflow-hidden">
          {/* Header */}
          <div className="p-3 border-b border-gray-800 flex flex-col gap-2">
            <div className="flex items-center justify-between">
              <span className={`text-sm font-semibold ${meta.color}`}>
                {meta.icon} {meta.name}
              </span>
              <div className="flex items-center gap-2">
                <button
                  onClick={toggleVoice}
                  title={voiceEnabled ? 'Mute coach voice' : 'Unmute coach voice'}
                  className={`text-base leading-none transition-colors ${voiceEnabled ? 'text-orange-400 hover:text-orange-300' : 'text-gray-600 hover:text-gray-400'}`}
                >
                  {voiceEnabled ? '🔊' : '🔇'}
                </button>
                <button
                  onClick={() => setOpen(false)}
                  className="text-gray-500 hover:text-white text-lg leading-none"
                >
                  ×
                </button>
              </div>
            </div>
            {/* Persona toggle */}
            <div className="flex gap-1 bg-gray-800 rounded-lg p-1">
              {(['sully', 'buddy'] as Persona[]).map(p => (
                <button
                  key={p}
                  onClick={() => handlePersonaChange(p)}
                  className={`flex-1 text-xs py-1 rounded-md font-medium transition-colors ${
                    persona === p
                      ? 'bg-orange-500 text-white'
                      : 'text-gray-400 hover:text-white'
                  }`}
                >
                  {PERSONA_META[p].icon} {PERSONA_META[p].name}
                </button>
              ))}
            </div>

            {/* Demo mode: Mock / Live Ollama toggle */}
            {isDemo && (
              <div className="flex items-center justify-between px-1">
                <span className="text-xs text-gray-600">AI source</span>
                <button
                  onClick={toggleChatMode}
                  className={`flex items-center gap-1.5 text-xs px-2 py-1 rounded-lg font-medium transition-colors ${
                    ollamaMode
                      ? 'bg-green-500/20 text-green-400 border border-green-500/30'
                      : 'bg-gray-800 text-gray-500 border border-gray-700'
                  }`}
                >
                  <span className={`w-1.5 h-1.5 rounded-full ${ollamaMode ? 'bg-green-400' : 'bg-gray-600'}`} />
                  {ollamaMode ? 'Live (Ollama)' : 'Mock'}
                </button>
              </div>
            )}
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-3 space-y-2 max-h-72 min-h-32">
            {messages[persona].length === 0 && (
              <p className="text-xs text-gray-600 text-center mt-6">
                Ask {meta.name} anything about your game.
              </p>
            )}
            {messages[persona].map((m, i) => (
              <div key={i} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div className={`max-w-[85%] px-3 py-2 rounded-xl text-sm ${
                  m.role === 'user'
                    ? 'bg-orange-500 text-white'
                    : 'bg-gray-800 text-gray-200'
                }`}>
                  {m.text}
                </div>
              </div>
            ))}
            {loading && (
              <div className="flex justify-start">
                <div className="bg-gray-800 px-3 py-2 rounded-xl text-sm text-gray-400 flex gap-1">
                  <span className="animate-bounce">•</span>
                  <span className="animate-bounce [animation-delay:0.15s]">•</span>
                  <span className="animate-bounce [animation-delay:0.3s]">•</span>
                </div>
              </div>
            )}
            <div ref={bottomRef} />
          </div>

          {/* Input */}
          <div className="p-3 border-t border-gray-800 flex gap-2">
            <input
              type="text"
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && handleSend()}
              placeholder="Ask your coach..."
              className="flex-1 bg-gray-800 text-white text-sm rounded-lg px-3 py-2 outline-none placeholder-gray-600 focus:ring-1 focus:ring-orange-500"
            />
            <button
              onClick={handleSend}
              disabled={loading || !input.trim()}
              className="bg-orange-500 hover:bg-orange-400 disabled:opacity-40 text-white text-sm px-3 py-2 rounded-lg font-medium transition-colors"
            >
              Send
            </button>
          </div>
        </div>
      )}

      {/* Voice + chat toggle row */}
      <div className="flex items-center gap-2">
        <button
          onClick={toggleVoice}
          title={voiceEnabled ? 'Mute coach voice' : 'Unmute coach voice'}
          className={`w-10 h-10 rounded-full shadow-lg flex items-center justify-center text-lg transition-colors ${
            voiceEnabled
              ? 'bg-orange-500/20 border border-orange-500/50 text-orange-400 hover:bg-orange-500/30'
              : 'bg-gray-800 border border-gray-700 text-gray-500 hover:text-gray-300'
          }`}
        >
          {voiceEnabled ? '🔊' : '🔇'}
        </button>
        <button
          onClick={() => setOpen(o => !o)}
          className="w-14 h-14 bg-orange-500 hover:bg-orange-400 text-white rounded-full shadow-lg flex items-center justify-center text-2xl transition-colors"
          title="Chat with your coach"
        >
          {open ? '×' : meta.icon}
        </button>
      </div>
    </div>
  )
}
