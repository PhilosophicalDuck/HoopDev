/**
 * Calls the local Ollama REST API directly from the browser.
 * Used in demo mode when VITE_OLLAMA_DEMO_CHAT=true so no backend is needed.
 */

const OLLAMA_HOST  = import.meta.env.VITE_OLLAMA_HOST  ?? 'http://localhost:11434'
const OLLAMA_MODEL = import.meta.env.VITE_OLLAMA_MODEL ?? 'llama3.2'

const PERSONA_PROMPTS: Record<string, string> = {
  sully: [
    'You are Coach Old School Sully, a Hall-of-Fame basketball coach.',
    'You are authoritative, direct, calm, and focused on discipline and execution.',
    'You do not give compliments easily. You hold athletes to a high standard.',
    'If session data is provided, reference the specific numbers directly and bluntly.',
    'Keep every response to 2-3 sentences maximum. No fluff, no emojis.',
    'Example style: "Execute the follow-through. Discipline wins games, not luck."',
  ].join(' '),

  buddy: [
    'You are Buddy, the athlete\'s biggest fan and personal hype coach.',
    'You are warm, energetic, and extremely encouraging. You celebrate every small win.',
    'If session data is provided, reference the specific numbers positively and focus on progress.',
    'Keep every response to 2-3 sentences maximum. Be enthusiastic but specific. Use occasional emojis.',
    'Example style: "Look at that arc! You\'re getting so much more height today. Keep that fire going! 🔥"',
  ].join(' '),
}

function buildSystemPrompt(persona: string, sessionData: Record<string, unknown> | null): string {
  const base = PERSONA_PROMPTS[persona] ?? PERSONA_PROMPTS.buddy
  if (!sessionData) return base

  const lines: string[] = ['\n\nATHLETE SESSION DATA (reference this naturally):']

  if (sessionData.drill_type)     lines.push(`- Drill: ${sessionData.drill_type}`)
  if (sessionData.shots_made != null && sessionData.shots_attempted) {
    const made = sessionData.shots_made as number
    const att  = sessionData.shots_attempted as number
    lines.push(`- Shooting: ${made}/${att} FG (${att > 0 ? Math.round(made / att * 100) : 0}%)`)
  }
  if (sessionData.avg_arc_angle_deg)
    lines.push(`- Arc angle: ${(sessionData.avg_arc_angle_deg as number).toFixed(1)}° (target 42-58°)`)
  if (sessionData.avg_release_elbow_angle)
    lines.push(`- Elbow angle: ${(sessionData.avg_release_elbow_angle as number).toFixed(1)}° (target 75-105°)`)
  if (sessionData.follow_through_ratio)
    lines.push(`- Follow-through: ${((sessionData.follow_through_ratio as number) * 100).toFixed(0)}% of shots`)
  if (sessionData.current_view) {
    const view    = sessionData.current_view as string
    const label   = (sessionData.view_label as string | undefined) ?? view
    const avg     = sessionData.view_avg as number | undefined
    const unit    = (sessionData.view_unit as string | undefined) ?? ''
    const ideal   = (sessionData.view_ideal as string | undefined) ?? 'n/a'
    lines.push(`- Athlete is currently reviewing: ${label}`)
    if (avg != null) lines.push(`  → Session average: ${avg}${unit} (ideal range: ${ideal})`)
    lines.push('  → Focus your coaching response on this specific metric.')
  }

  return base + lines.join('\n')
}

export async function callOllamaChat(
  message: string,
  persona: string,
  sessionData: Record<string, unknown> | null = null,
  history: { role: 'user' | 'assistant'; content: string }[] = [],
): Promise<string> {
  const system = buildSystemPrompt(persona, sessionData)

  const res = await fetch(`${OLLAMA_HOST}/api/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      model: OLLAMA_MODEL,
      stream: false,
      messages: [
        { role: 'system', content: system },
        ...history,
        { role: 'user', content: message },
      ],
    }),
  })

  if (!res.ok) throw new Error(`Ollama error: ${res.status}`)

  const data = await res.json()
  return data.message?.content ?? 'No response from model.'
}
