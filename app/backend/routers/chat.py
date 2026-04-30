"""
Chat router — AI coach chat with Sully or Buddy personas.

POST /api/chat/message
  Body: { message, persona, session_data? }
  Returns: { reply }

Environment variables:
  MOCK_CHAT=true       Return canned responses without hitting Ollama (UI testing).
  OLLAMA_MODEL=...     Which Ollama model to use (default: llama3.2).
  OLLAMA_HOST=...      Ollama base URL (default: http://localhost:11434).
"""
import logging
import os
import random
from typing import Literal

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.backend.auth import get_current_user
from app.backend.models.user import User

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/chat", tags=["chat"])

MOCK_CHAT    = os.getenv("MOCK_CHAT", "false").lower() == "true"
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")
OLLAMA_HOST  = os.getenv("OLLAMA_HOST", "http://localhost:11434")

# ── Mock replies (used when MOCK_CHAT=true) ───────────────────────────────────

MOCK_REPLIES = {
    "sully": [
        "Execute the follow-through every single time. That's not optional — that's the standard.",
        "Discipline wins games, not talent. Get your arc consistent before you worry about anything else.",
        "I've seen the numbers. You have potential. Now stop wasting it and put in the work.",
        "Your release needs to be the same every time. Every. Single. Time. That's how champions are built.",
    ],
    "buddy": [
        "You're out there putting in the work and that's everything! Keep that energy going!",
        "Look at you grinding! Every rep is making you better — trust the process!",
        "You've got this! Small wins every day add up to something huge. I believe in you!",
        "That's the fire I love to see! Keep pushing and the results will follow!",
    ],
}

# ── Persona system prompts ────────────────────────────────────────────────────

PERSONA_PROMPTS = {
    "sully": (
        "You are Coach Old School Sully, a Hall-of-Fame basketball coach. "
        "You are authoritative, direct, calm, and focused on discipline and execution. "
        "You do not give compliments easily. You hold athletes to a high standard. "
        "If session data is provided, reference the specific numbers directly and bluntly. "
        "Keep every response to 2-3 sentences maximum. No fluff, no emojis. "
        'Example style: "Execute the follow-through. Discipline wins games, not luck."'
    ),
    "buddy": (
        "You are Buddy, the athlete's biggest fan and personal hype coach. "
        "You are warm, energetic, and extremely encouraging. You celebrate every small win. "
        "If session data is provided, reference the specific numbers positively and focus on progress. "
        "Keep every response to 2-3 sentences maximum. Be enthusiastic but specific. Use occasional emojis. "
        'Example style: "Look at that arc! You\'re getting so much more height today. Keep that fire going! 🔥"'
    ),
}


# ── Context builder ───────────────────────────────────────────────────────────

def _build_system_prompt(persona: str, session_data: dict | None) -> str:
    prompt = PERSONA_PROMPTS[persona]
    if not session_data:
        return prompt

    lines = ["\n\nATHLETE SESSION DATA (reference this naturally):"]
    if dt := session_data.get("drill_type"):
        lines.append(f"- Drill: {dt}")
    if (made := session_data.get("shots_made")) is not None and (att := session_data.get("shots_attempted")):
        pct = f"{made/att:.0%}" if att > 0 else "n/a"
        lines.append(f"- Shooting: {made}/{att} FG ({pct})")
    if arc := session_data.get("avg_arc_angle_deg"):
        lines.append(f"- Arc angle: {arc:.1f}° (target 42-58°)")
    if elbow := session_data.get("avg_release_elbow_angle"):
        lines.append(f"- Elbow angle at release: {elbow:.1f}° (target 75-105°)")
    if spd := session_data.get("avg_speed_px_per_s"):
        lines.append(f"- Avg movement speed: {spd:.0f} px/s")
    if ft := session_data.get("follow_through_ratio"):
        lines.append(f"- Follow-through: {ft*100:.0f}% of shots")
    if cv := session_data.get("current_view"):
        view_label = session_data.get("view_label", cv)
        view_avg   = session_data.get("view_avg")
        view_unit  = session_data.get("view_unit", "")
        view_ideal = session_data.get("view_ideal", "n/a")
        lines.append(f"- Athlete is currently reviewing: {view_label}")
        if view_avg is not None:
            lines.append(f"  → Session average: {view_avg}{view_unit} (ideal range: {view_ideal})")
        lines.append("  → Focus your coaching response on this specific metric.")

    return prompt + "\n".join(lines)


# ── Request/response models ───────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str
    persona: Literal["sully", "buddy"]
    session_data: dict | None = None


# ── Ollama client (lazy init) ─────────────────────────────────────────────────

_ollama_client = None

def _get_ollama():
    global _ollama_client
    if _ollama_client is None:
        import ollama
        _ollama_client = ollama.Client(host=OLLAMA_HOST)
    return _ollama_client


# ── Route ─────────────────────────────────────────────────────────────────────

@router.post("/message")
def chat_message(
    req: ChatRequest,
    current_user: User = Depends(get_current_user),
):
    if MOCK_CHAT:
        logger.info("MOCK_CHAT enabled — returning canned response")
        return {"reply": random.choice(MOCK_REPLIES[req.persona])}

    system = _build_system_prompt(req.persona, req.session_data)
    try:
        client = _get_ollama()
        response = client.chat(
            model=OLLAMA_MODEL,
            messages=[
                {"role": "system", "content": system},
                {"role": "user",   "content": req.message},
            ],
        )
        reply = response.message.content
    except Exception as exc:
        logger.error("Ollama error: %s", exc)
        reply = "I'm having trouble connecting to the AI right now. Make sure Ollama is running."
    return {"reply": reply}
