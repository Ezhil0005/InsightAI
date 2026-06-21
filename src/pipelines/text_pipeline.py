"""Text analysis pipeline orchestration.

This file exposes a `run_text_pipeline` function that performs normalization,
language detection, translation, and delegates to `src.core.ai_engine`.
"""
from typing import Dict, Any
from ..pipelines.preprocessing import normalize_text
from ..core.ai_engine import AIEngine


def run_text_pipeline(text: str, metadata: Dict[str, Any] = None, engine: AIEngine = None) -> Dict[str, Any]:
    metadata = metadata or {}
    norm = normalize_text(text)
    engine = engine or AIEngine()
    result = engine.analyze_feedback(norm, metadata)
    return result.__dict__
