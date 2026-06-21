"""Provider manager wrapper that bridges legacy `src.providers` and
new provider adapters in `src.services`.

This module keeps backwards compatibility by delegating to the existing
`src.providers` module when available, while providing a place to add
advanced routing/scoring logic.
"""
from typing import Dict, Any
try:
    from .. import providers as legacy_providers
except Exception:
    legacy_providers = None


class ProviderManager:
    """Simple manager delegating to legacy providers module when present.

    Production-quality routing and scoring lives in dedicated adapters
    (`openai_provider.py`, etc.).
    """

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}

    def route_text_task(self, task_type: str, payload: Dict[str, Any], safe_mode: bool = False) -> Dict[str, Any]:
        # Prefer new adapters (not implemented) then fall back to legacy module
        if safe_mode:
            return {"label": "neutral", "score": 0.0, "fallback_used": True}
        if legacy_providers and hasattr(legacy_providers, "route_text_task"):
            return legacy_providers.route_text_task(task_type, payload)
        return {"label": "neutral", "score": 0.0}
