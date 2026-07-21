"""
AI Package

Provides factory getter for obtaining the active `AIProvider`.
Defaults to OpenAIProvider if OPENAI_API_KEY is configured,
otherwise falls back gracefully to MockProvider for offline dev.
"""

from app.ai.base import AIProvider
from app.ai.openai_provider import OpenAIProvider
from app.ai.mock_provider import MockProvider
from app.core.config import settings


def get_ai_provider() -> AIProvider:
    """
    Returns configured AI provider instance.
    """
    if settings.OPENAI_API_KEY and len(settings.OPENAI_API_KEY.strip()) > 5:
        return OpenAIProvider()
    return MockProvider()


__all__ = ["AIProvider", "OpenAIProvider", "MockProvider", "get_ai_provider"]
