import os
import logging
import httpx
import json
import re
from typing import Dict, Any, List, Optional
from openai import AsyncOpenAI

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------

def _redact_secrets(text: str) -> str:
    """Redact any API key values found in a URL query string or raw text.

    The function looks for patterns like ``key=...`` or known environment variable
    names (``GEMINI_API_KEY``, ``GOOGLE_API_KEY``, ``OPENAI_API_KEY``) and replaces
    the actual secret with ``[REDACTED]``.
    """
    # Redact generic ``key=...`` query parameters (non‑greedy up to & or end)
    text = re.sub(r"(?i)(key=)[^&\s]+", r"\1[REDACTED]", text)
    # Redact explicit env‑var placeholders in logged content
    for var in ["GEMINI_API_KEY", "GOOGLE_API_KEY", "OPENAI_API_KEY"]:
        text = re.sub(rf"(?i)({var}=)[^&\s]+", r"\1[REDACTED]", text)
        # Also remove the raw value if the variable name appears alone
        text = re.sub(rf"(?i){var}\s*[:=]\s*[^\s,]+", f"{var}=[REDACTED]", text)
    return text


class AIProvider:
    """Abstract AI provider interface.
    Implementations must provide an async `chat_completion` method returning a string response.
    """

    async def chat_completion(self, system_prompt: str, user_prompt: str, history: List[Dict[str, str]]) -> str:
        raise NotImplementedError


class OpenAIProvider(AIProvider):
    """OpenAI Chat Completion provider using official OpenAI SDK."""

    def __init__(self, api_key: str | None = None, model: str = "gpt-4.1-mini"):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model or os.getenv("AI_MODEL")
        if not self.api_key:
            self.enabled = False
            self.client = None
        else:
            self.enabled = True
            self.client = AsyncOpenAI(api_key=self.api_key)

    async def chat_completion(self, system_prompt: str, user_prompt: str, history: List[Dict[str, str]]) -> str:
        if not getattr(self, "enabled", False) or not self.client:
            return "AI provider not configured yet."
        messages = [{"role": "system", "content": system_prompt}]
        for entry in history:
            role = entry.get("role", "user")
            content = entry.get("content", "")
            messages.append({"role": role, "content": content})
        messages.append({"role": "user", "content": user_prompt})

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.2,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"OpenAI API call failed: {e}")
            return "AI provider encountered an error."


class GeminiProvider(AIProvider):
    """Google Gemini provider using async httpx."""

    def __init__(self, api_key: str | None = None, model: str = "gemini-2.5-flash"):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            logger.warning("GEMINI_API_KEY / GOOGLE_API_KEY not set; GeminiProvider disabled.")
            self.enabled = False
        else:
            self.enabled = True

        self.model = model
        self.endpoint = f"https://generativelanguage.googleapis.com/v1/models/{self.model}:generateContent"

    def _is_stock_analysis_prompt(self, user_prompt: str) -> bool:
        return (
            "breakout_probability" in user_prompt
            and "investment_thesis" in user_prompt
            and "support_resistance_analysis" in user_prompt
        )

    def _stock_analysis_schema(self) -> Dict[str, Any]:
        text_field = {
            "type": "string",
            "description": "Ticker-specific reasoning. Must not be placeholder text.",
        }

        return {
            "type": "object",

            "required": [
                "signal",
                "confidence",
                "breakout_probability",
                "risk_level",
                "summary",
                "company_overview",
                "technical_analysis",
                "chart_analysis",
                "trend_analysis",
                "momentum_analysis",
                "support_resistance_analysis",
                "bull_case",
                "bear_case",
                "investment_thesis",
                "position_assessment",
                "entry_strategy",
                "exit_strategy",
                "holding_period",
                "holding_period_rationale",
                "key_levels",
                "warnings",
                "setup_quality",
                "market_bias",
                "catalyst_summary",
            ],
            "properties": {
                "signal": {
                    "type": "string",
                    "enum": ["BUY", "SELL", "HOLD"],
                    "description": "Final trading signal.",
                },
                "confidence": {
                    "type": "integer",
                    "description": "Confidence score from 0 to 100."
                },
                "breakout_probability": {
                    "type": "integer",
                    "description": "Estimated breakout probability from 0 to 100."
                },
                "risk_level": {
                    "type": "string",
                    "enum": ["Low", "Medium", "High", "Unknown"],
                },
                "summary": text_field,
                "company_overview": text_field,
                "technical_analysis": text_field,
                "chart_analysis": text_field,
                "trend_analysis": text_field,
                "momentum_analysis": text_field,
                "support_resistance_analysis": text_field,
                "bull_case": text_field,
                "bear_case": text_field,
                "investment_thesis": text_field,
                "position_assessment": text_field,
                "entry_strategy": text_field,
                "exit_strategy": text_field,
                "holding_period": text_field,
                "holding_period_rationale": text_field,
                "key_levels": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Support/resistance/entry/exit levels as strings.",
                },
                "warnings": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Important risk warnings.",
                },
                "setup_quality": {
                    "type": "string",
                    "enum": ["weak", "average", "strong"],
                },
                "market_bias": {
                    "type": "string",
                    "enum": ["bearish", "neutral", "bullish"],
                },
                "catalyst_summary": text_field,
            },
        }

    async def chat_completion(
        self,
        system_prompt: str,
        user_prompt: str,
        history: List[Dict[str, str]],
    ) -> str:
        if not getattr(self, "enabled", False):
            raise RuntimeError("Gemini provider is not configured.")

        full_prompt = system_prompt.strip() + "\n\n" + user_prompt.strip()

        generation_config: Dict[str, Any] = {
            "temperature": 0.35,
            "topP": 0.9,
            "maxOutputTokens": 4096,
        }

        # Force real structured JSON for Normal Analysis only.
        if self._is_stock_analysis_prompt(user_prompt):
            # Use v1beta endpoint for structured output as required
            self.endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"
            generation_config.update(
                {
                    "responseMimeType": "application/json",
                    "responseSchema": self._stock_analysis_schema(),
                }
            )

        payload = {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": full_prompt}],
                }
            ],
            "generationConfig": generation_config,
        }

        params = {"key": self.api_key}

        async with httpx.AsyncClient() as client:
            try:
                resp = await client.post(
                    self.endpoint,
                    params=params,
                    json=payload,
                    timeout=30.0,
                )
                resp.raise_for_status()
                data = resp.json()

                parts = (
                    data.get("candidates", [{}])[0]
                    .get("content", {})
                    .get("parts", [])
                )

                answer = "".join(part.get("text", "") for part in parts).strip()

                if not answer:
                    logger.error("Gemini returned empty response. Full response: %s", data)
                    raise RuntimeError("Gemini returned empty response.")

                return answer

            except httpx.HTTPStatusError as e:
                # Sanitize any secret values before logging
                safe_body = _redact_secrets(e.response.text[:1000])
                logger.error(
                    "Gemini API HTTP error %s for model %s (endpoint %s): %s",
                    e.response.status_code,
                    self.model,
                    self.endpoint.split("googleapis.com")[-1],
                    safe_body,
                )
                # Raise a generic RuntimeError without the raw URL or key
                raise RuntimeError(
                    f"Gemini API HTTP error {e.response.status_code}: {safe_body}"
                ) from None
            except Exception as e:
                # Ensure no raw URL with query parameters is leaked
                safe_msg = _redact_secrets(str(e))
                logger.error(f"Gemini API call failed: {safe_msg}")
                raise RuntimeError(safe_msg) from None

def get_ai_provider() -> AIProvider:
    """Factory to select AI provider based on settings."""
    provider_name = os.getenv("AI_PROVIDER")
    if not provider_name:
        raise RuntimeError("AI_PROVIDER environment variable is required.")

    provider_name = provider_name.strip().lower()
    
    model = os.getenv("AI_MODEL")
    if not model:
        raise RuntimeError("AI_MODEL environment variable is required.")

    if provider_name == "openai":
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY environment variable is required.")
        return OpenAIProvider(api_key=api_key, model=model)
    elif provider_name == "gemini":
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY environment variable is required.")
        return GeminiProvider(api_key=api_key, model=model)
    else:
        raise RuntimeError(f"Unknown AI_PROVIDER: {provider_name}")

