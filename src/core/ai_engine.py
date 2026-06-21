"""Central intelligence engine for feedback analysis.

This module provides a high-level `AIEngine` facade that coordinates
analysis pipelines (sentiment, root cause, churn, scoring) by calling
provider adapters found in `src.services` and local rule fallbacks.
"""
from typing import Dict, Any, Optional
from dataclasses import dataclass

from ..services import providers


@dataclass
class AnalysisResult:
    sentiment_label: str
    sentiment_score: float
    category: Optional[str]
    severity: Optional[str]
    severity_score: Optional[float]
    root_cause: Optional[str]
    churn_risk: float
    business_impact_score: float
    recommendations: Dict[str, Any]


class AIEngine:
    """Facade for running analysis on normalized feedback text.

    Methods are intentionally small and orchestrate calls to provider
    adapters and local fallback logic.
    """

    def __init__(self, provider_manager=None, safe_mode=False):
        self.provider_manager = provider_manager or providers.ProviderManager()
        self.safe_mode = safe_mode

    def analyze_feedback(self, text: str, metadata: Dict[str, Any] = None) -> AnalysisResult:
        """Run full analysis pipeline for a single feedback item.

        Input: normalized text and optional metadata (source, user, language)
        Output: AnalysisResult dataclass
        """
        metadata = metadata or {}
        # Sentiment + classification
        sentiment_resp = self.provider_manager.route_text_task("sentiment", {"text": text}, safe_mode=self.safe_mode)
        category_resp = self.provider_manager.route_text_task("classification", {"text": text}, safe_mode=self.safe_mode)

        # Root cause and recommendations
        root_response = self.provider_manager.route_text_task("root_cause", {"text": text}, safe_mode=self.safe_mode)
        recs = self.provider_manager.route_text_task("recommendations", {"text": text, "metadata": metadata}, safe_mode=self.safe_mode)

        # Churn / impact heuristics (can be ML models)
        churn_score = self._predict_churn(text, metadata)
        impact = self._score_business_impact(text, metadata)

        return AnalysisResult(
            sentiment_label=sentiment_resp.get("label", "neutral"),
            sentiment_score=float(sentiment_resp.get("score", 0.0)),
            category=category_resp.get("category"),
            severity=root_response.get("severity"),
            severity_score=float(root_response.get("severity_score", 0.0)),
            root_cause=root_response.get("root_cause"),
            churn_risk=churn_score,
            business_impact_score=impact,
            recommendations=recs.get("recommendations", {}),
        )

    def _predict_churn(self, text: str, metadata: Dict[str, Any]) -> float:
        # Lightweight heuristic placeholder; production uses ML model in src.core.forecasting
        base = 0.05
        if "cancel" in text.lower() or "switch" in text.lower():
            base += 0.3
        return min(1.0, base)

    def _score_business_impact(self, text: str, metadata: Dict[str, Any]) -> float:
        # Heuristic scoring; replaced by more sophisticated model later
        score = 0.1
        if "outage" in text.lower() or "refund" in text.lower():
            score += 0.5
        return min(1.0, score)
