class InsightAIError(Exception):
    """Base exception for InsightAI."""


class ProviderError(InsightAIError):
    pass


class ValidationError(InsightAIError):
    pass
