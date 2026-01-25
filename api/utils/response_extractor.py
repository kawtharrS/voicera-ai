from typing import Any, Dict, List, Optional
from .helpers import _get_val


def extract_ai_response(result: Dict[str, Any]) -> str:
    response = result.get("ai_response")
    if not response:
        interaction = result.get("current_interaction")
        if interaction:
            response = _get_val(interaction, "ai_response", "")
    if response and isinstance(response, str) and response.startswith("I noticed you're feeling"):
        response = response.split(". ", 1)[-1]
    return response or "How can I help you today?"


def extract_recommendations(result: Dict[str, Any]) -> List[str]:
    recs = result.get("recommendations")
    if not recs:
        interaction = result.get("current_interaction")
        if interaction:
            recs = _get_val(interaction, "recommendations", [])
    return recs or []


def extract_emotion(result: Dict[str, Any]) -> Optional[str]:
    emotion = result.get("emotion")
    if not emotion:
        detected = result.get("detected_emotion")
        if detected:
            emotion = getattr(detected, "value", str(detected))
    if not emotion:
        emotion_output = result.get("emotion_output", {})
        emotion = emotion_output.get("emotion")
    return emotion or "unknown"
