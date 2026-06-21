"""Voice intelligence pipeline wrapper that delegates to existing `src.voice`.

This module provides the `VoicePipeline` class expected by the new
repository layout while reusing the legacy implementation in `src/voice.py`.
"""
from typing import Dict, Any
try:
    from .. import voice as legacy_voice
except Exception:
    legacy_voice = None


class VoicePipeline:
    def __init__(self, provider_manager=None):
        self.provider_manager = provider_manager

    def process_voice_file(self, file_path: str, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        metadata = metadata or {}
        if legacy_voice and hasattr(legacy_voice, "process_voice_file"):
            return legacy_voice.process_voice_file(file_path, metadata)
        # Minimal fallback behavior
        return {"transcript": "", "language": "en", "emotion": "neutral", "confidence": 0.0}
