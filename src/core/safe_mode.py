"""Safe Mode helpers and simple rules-based fallback engine."""
from typing import Dict, Any


def rules_fallback(text: str) -> Dict[str, Any]:
    """Simple keyword-based fallback for sentiment/category/severity.

    This is intentionally conservative and interpretable for demos.
    """
    lower = text.lower()
    sentiment = "neutral"
    score = 0.0
    if any(k in lower for k in ["bad", "terrible", "awful", "hate"]):
        sentiment = "negative"
        score = 0.8
    if any(k in lower for k in ["good", "great", "love", "happy"]):
        sentiment = "positive"
        score = 0.8

    category = None
    if "delivery" in lower:
        category = "delivery"
    if "billing" in lower:
        category = "billing"

    return {"label": sentiment, "score": score, "category": category, "fallback_used": True}
