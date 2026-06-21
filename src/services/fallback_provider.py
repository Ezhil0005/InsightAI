"""Rules-based fallback provider for offline/demo mode."""
from typing import Dict, Any
from ..core.safe_mode import rules_fallback


def fallback_task(task: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    text = payload.get("text", "")
    if task in ("sentiment", "classification"):
        return rules_fallback(text)
    return {"result": {}, "fallback_used": True}
