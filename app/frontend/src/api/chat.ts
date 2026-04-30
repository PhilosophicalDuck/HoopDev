import { api } from './client'

export type Persona = 'sully' | 'buddy'

export async function sendChatMessage(
  message: string,
  persona: Persona,
  sessionData?: object | null,
): Promise<string> {
  const res = await api.post<{ reply: string }>('/chat/message', {
    message,
    persona,
    session_data: sessionData ?? null,
  })
  return res.data.reply
}
