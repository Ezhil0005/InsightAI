"""Global constants for InsightAI."""
SUPPORTED_LANGUAGES = ["en", "ta", "hi", "tanglish", "hinglish"]
SENTIMENT_LABELS = ["positive", "neutral", "negative"]
SEVERITY_BANDS = ["low", "medium", "high", "critical"]
PROVIDERS = ["openai", "gemini", "groq", "fallback"]
UI_ROUTES = [
    "landing",
    "upload",
    "feature_hub",
    "executive_dashboard",
    "voice_center",
    "forecasting_center",
    "risk_center",
    "reports_center",
    "settings",
]
