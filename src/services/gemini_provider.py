"""Adapter for Gemini provider calls (placeholder)."""
from typing import Dict, Any


def call_gemini(task: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    return {"provider": "gemini", "task": task, "result": {}, "confidence": 0.88}
