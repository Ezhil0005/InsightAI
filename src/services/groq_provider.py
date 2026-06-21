"""Adapter for Groq provider calls (placeholder)."""
from typing import Dict, Any


def call_groq(task: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    return {"provider": "groq", "task": task, "result": {}, "confidence": 0.8}
