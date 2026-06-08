import os
import logging
from typing import Dict, Any, List
import httpx

logger = logging.getLogger(__name__)


class AIProvider:
    """Abstract AI provider interface.
    Implementations must provide an async `chat_completion` method returning a string response.
    """

    async def chat_completion(self, system_prompt: str, user_prompt: str, history: List[Dict[str, str]]) -> str:
        raise NotImplementedError


class OpenAIProvider(AIProvider):
    """Simple OpenAI Chat Completion provider using async httpx.
    Reads `OPENAI_API_KEY` from environment. Uses `gpt-3.5-turbo` model.
    """

    def __init__(self, api_key: str | None = None, model: str = "gpt-3.5-turbo"):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            logger.warning("OPENAI_API_KEY not set; OpenAIProvider disabled.")
            self.enabled = False
        else:
            self.enabled = True
        self.model = model
        self.endpoint = "https://api.openai.com/v1/chat/completions"
        self.headers = (
            {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
            if self.enabled
            else {}
        )

    async def chat_completion(self, system_prompt: str, user_prompt: str, history: List[Dict[str, str]]) -> str:
        if not getattr(self, "enabled", False):
            # Graceful fallback when provider is not configured
            return "AI provider not configured yet."
        messages = [{"role": "system", "content": system_prompt}]
        # Append conversation history if provided
        for entry in history:
            role = entry.get("role", "user")
            content = entry.get("content", "")
            messages.append({"role": role, "content": content})
        # Add current user prompt
        messages.append({"role": "user", "content": user_prompt})
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.2,
        }
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.post(self.endpoint, headers=self.headers, json=payload, timeout=30.0)
                resp.raise_for_status()
                data = resp.json()
                answer = data["choices"][0]["message"]["content"].strip()
                return answer
            except Exception as e:
                logger.error(f"OpenAI API call failed: {e}")
                # Return a friendly fallback instead of propagating the exception
                return "AI provider encountered an error."


class GeminiProvider(AIProvider):
    """Google Gemini provider using async httpx."""

    def __init__(self, api_key: str | None = None, model: str = "gemini-1.5-flash"):
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            logger.warning("GOOGLE_API_KEY not set; GeminiProvider disabled.")
            self.enabled = False
        else:
            self.enabled = True
        self.model = model
        self.endpoint = f"https://generativelanguage.googleapis.com/v1/models/{self.model}:generateContent"

    async def chat_completion(self, system_prompt: str, user_prompt: str, history: List[Dict[str, str]]) -> str:
        if not getattr(self, "enabled", False):
            return "AI provider not configured yet."
        
        contents = [{"role": "user", "parts": [{"text": system_prompt + "\n" + user_prompt}]}]
        payload = {"contents": contents}
        params = {"key": self.api_key}

        async with httpx.AsyncClient() as client:
            try:
                resp = await client.post(self.endpoint, params=params, json=payload, timeout=30.0)
                resp.raise_for_status()
                data = resp.json()
                answer = data["candidates"][0]["content"]["parts"][0]["text"].strip()
                return answer
            except Exception as e:
                logger.error(f"Gemini API call failed: {e}")
                return "AI provider encountered an error."


def get_ai_provider() -> AIProvider:
    """Factory to select AI provider based on settings."""
    try:
        from ..settings import settings
    except Exception:
        from settings import settings
    provider_name = getattr(settings, "AI_PROVIDER", "openai").lower()
    model = getattr(settings, "AI_MODEL", "gpt-3.5-turbo")
    if provider_name == "gemini":
        return GeminiProvider(api_key=settings.GEMINI_API_KEY, model=model)
    return OpenAIProvider(api_key=settings.OPENAI_API_KEY, model=model)
