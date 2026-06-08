import abc
import asyncio
import json
import logging
import os
import pathlib
from typing import Any, Dict, Optional, Type, List

import httpx
from pydantic import BaseModel, ValidationError

from .ai_provider import get_ai_provider, AIProvider

# ---------------------------------------------------------------------------
# Custom exception hierarchy
# ---------------------------------------------------------------------------

class AIProviderError(Exception):
    """Raised when the underlying AI provider fails unexpectedly."""

class InvalidAIResponseError(Exception):
    """Raised when the AI provider returns a response that cannot be parsed as JSON."""

class PromptLoadError(Exception):
    """Raised when a prompt file cannot be read or is missing."""

# ---------------------------------------------------------------------------
# BaseAgent definition
# ---------------------------------------------------------------------------

class BaseAgent(abc.ABC):
    """Abstract asynchronous agent that communicates with an LLM provider.

    Concrete agents (AnalysisAgent, ScannerAgent, ChatAgent, MemoryAgent) should
    inherit from this class and provide:
        * ``prompt_name`` – the base filename of the prompt template.
        * ``response_schema`` – a pydantic model defining the expected output.
    The base class handles prompt loading, provider interaction, retries,
    JSON sanitisation and schema validation.
    """

    #: Maximum number of attempts to make when an LLM call fails
    MAX_RETRIES = 3
    #: Base back‑off in seconds (exponential)
    BACKOFF_FACTOR = 0.5
    #: Timeout for a single provider call (seconds)
    CALL_TIMEOUT = 30

    def __init__(self, prompt_name: str, response_schema: Type[BaseModel]):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.prompt_name = prompt_name
        self.response_schema = response_schema
        # Re‑use a single provider instance for the lifetime of the agent
        self.provider: AIProvider = get_ai_provider()
        self._prompt_template: Optional[str] = None

    # ---------------------------------------------------------------------
    # Prompt handling utilities
    # ---------------------------------------------------------------------
    async def load_prompt(self, prompt_name: Optional[str] = None) -> str:
        """Load a raw prompt template from ``backend/app/agents/prompts``.

        The file must be a UTF‑8 ``.txt`` file. The method caches the content
        after the first successful load.
        """
        name = prompt_name or self.prompt_name
        if self._prompt_template is not None and prompt_name is None:
            return self._prompt_template
        prompt_path = (
            pathlib.Path(__file__).parents[1]
            / "agents"
            / "prompts"
            / f"{name}.txt"
        )
        if not prompt_path.is_file():
            raise PromptLoadError(f"Prompt file not found: {prompt_path}")
        try:
            # Use a thread pool to avoid blocking the event loop
            content = await asyncio.to_thread(prompt_path.read_text, encoding="utf-8")
        except Exception as exc:
            raise PromptLoadError(f"Failed to read prompt '{name}': {exc}") from exc
        # Cache if this is the default prompt for the instance
        if prompt_name is None:
            self._prompt_template = content
        return content

    def build_prompt(self, **kwargs: Any) -> str:
        """Inject variables into the loaded prompt template.

        ``kwargs`` are inserted via Python's ``str.format``. Missing keys raise a
        ``KeyError`` which bubbles up as a ``PromptLoadError`` for consistency.
        """
        if self._prompt_template is None:
            raise PromptLoadError("Prompt template not loaded – call load_prompt() first.")
        try:
            return self._prompt_template.format(**kwargs)
        except Exception as exc:
            raise PromptLoadError(f"Failed to format prompt: {exc}") from exc

    # ---------------------------------------------------------------------
    # LLM interaction helpers
    # ---------------------------------------------------------------------
    async def _call_provider(
        self,
        system_prompt: str,
        user_prompt: str,
        history: Optional[List[Dict[str, str]]] = None,
    ) -> str:
        """Perform a single async call to the underlying AI provider.

        The call is wrapped in ``asyncio.wait_for`` to enforce a timeout.
        """
        history = history or []
        try:
            coro = self.provider.chat_completion(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                history=history,
            )
            response = await asyncio.wait_for(coro, timeout=self.CALL_TIMEOUT)
            return response
        except asyncio.TimeoutError as exc:
            raise AIProviderError("AI provider call timed out") from exc
        except Exception as exc:
            raise AIProviderError(f"AI provider raised an exception: {exc}") from exc

    async def generate_response(
        self,
        system_prompt: str,
        user_prompt: str,
        history: Optional[List[Dict[str, str]]] = None,
    ) -> str:
        """Call the provider with exponential back‑off retry logic.

        Returns the raw text response from the LLM.
        """
        attempt = 0
        while attempt < self.MAX_RETRIES:
            try:
                return await self._call_provider(system_prompt, user_prompt, history)
            except AIProviderError as exc:
                attempt += 1
                backoff = self.BACKOFF_FACTOR * (2 ** (attempt - 1))
                self.logger.warning(
                    "AI provider error (attempt %d/%d): %s – backing off %.2fs",
                    attempt,
                    self.MAX_RETRIES,
                    exc,
                    backoff,
                )
                await asyncio.sleep(backoff)
        raise AIProviderError("All retries to AI provider have failed")

    # ---------------------------------------------------------------------
    # Response handling helpers
    # ---------------------------------------------------------------------
    def _sanitize_json(self, raw: str) -> str:
        """Attempt a lightweight cleanup of malformed JSON strings.

        * Replace single quotes with double quotes.
        * Remove stray back‑ticks or markdown code fences.
        * Trim any leading/trailing non‑JSON characters.
        """
        cleaned = raw.strip()
        if cleaned.startswith('```'):
            cleaned = cleaned.lstrip('`').strip()
        if cleaned.endswith('```'):
            cleaned = cleaned.rstrip('`').strip()
        cleaned = cleaned.replace("'", '"')
        return cleaned

    def validate_response(self, raw_response: str) -> BaseModel:
        """Parse the raw LLM response, coerce to JSON, and validate against the schema.

        If parsing fails, a single retry is attempted after sanitising the string.
        ``InvalidAIResponseError`` is raised when validation cannot succeed.
        """
        try:
            data = json.loads(raw_response)
        except json.JSONDecodeError:
            self.logger.debug("JSON decode failed – attempting sanitisation")
            sanitized = self._sanitize_json(raw_response)
            try:
                data = json.loads(sanitized)
            except json.JSONDecodeError as exc:
                raise InvalidAIResponseError(
                    f"Unable to parse AI response as JSON after sanitisation: {exc}"
                ) from exc
        try:
            return self.response_schema.parse_obj(data)
        except ValidationError as exc:
            raise InvalidAIResponseError(f"Response validation failed: {exc}") from exc

    # ---------------------------------------------------------------------
    # Public entry point
    # ---------------------------------------------------------------------
    async def run(self, **prompt_kwargs: Any) -> BaseModel:
        """High‑level orchestrator used by concrete agents.

        Steps performed:
        1. Load the prompt template (cached after first call).
        2. Build the final user prompt using ``prompt_kwargs``.
        3. Call the LLM with retry/back‑off handling.
        4. Validate and return a pydantic model instance.
        """
        await self.load_prompt()
        user_prompt = self.build_prompt(**prompt_kwargs)
        system_prompt = getattr(self, "system_prompt", "")
        raw = await self.generate_response(system_prompt, user_prompt)
        try:
            return self.validate_response(raw)
        except InvalidAIResponseError as exc:
            self.logger.error("Invalid AI response – returning safe fallback: %s", exc)
            try:
                return self.response_schema.parse_obj({})
            except Exception:
                raise

    # ---------------------------------------------------------------------
    # Extension points for subclasses
    # ---------------------------------------------------------------------
    @property
    def system_prompt(self) -> str:
        """Sub‑classes may override to supply a dedicated system prompt."""
        return ""

    @abc.abstractmethod
    def post_process(self, model_instance: BaseModel) -> Any:
        """Hook for agents that need extra post‑processing after validation.

        The base implementation should simply return ``model_instance``.
        """
        return model_instance
