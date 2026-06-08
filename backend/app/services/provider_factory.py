# backend/app/services/provider_factory.py

"""Factory that abstracts LLM providers and embedding services.
Provides failover between Gemini (primary) and OpenAI (fallback).
All calls are async and return the same schema.
"""

import logging
from typing import List
import asyncio

from app.settings import settings
from .ai_provider import GeminiProvider, OpenAIProvider
from app.utils.async_timeout import with_timeout
from app.services.circuit_breaker import circuit_breaker

logger = logging.getLogger("provider_factory")

class ProviderFactory:
    def __init__(self):
        self.primary = GeminiProvider()
        self.fallbacks = []
        if settings.ENABLE_PROVIDER_FAILOVER and settings.FALLBACK_AI_PROVIDERS:
            for name in settings.FALLBACK_AI_PROVIDERS:
                if name.lower() == "openai":
                    self.fallbacks.append(OpenAIProvider())
                # Additional providers can be added here
        self.providers = [self.primary] + self.fallbacks

    async def generate(self, prompt: str, **kwargs) -> str:
        """Generate text using the provider chain with retries and failover.
        Returns the first successful response, applying circuit breaker and timeout.
        """
        for provider in self.providers:
            # Skip provider if circuit breaker marks it unhealthy
            if not circuit_breaker.is_healthy(provider.name):
                logger.warning("Skipping unhealthy provider %s", provider.name)
                continue
            try:
                logger.info("Attempting generation with %s", provider.name)
                # Apply timeout
                response = await with_timeout(provider.generate(prompt, **kwargs), settings.PROVIDER_TIMEOUT)
                logger.info("Generation succeeded with %s", provider.name)
                circuit_breaker.record_success(provider.name)
                return response
            except Exception as exc:
                logger.warning("Provider %s failed: %s", provider.name, exc)
                circuit_breaker.record_failure(provider.name)
                # continue to next fallback
        raise RuntimeError("All AI providers failed to generate a response")

    async def embed(self, text: str) -> List[float]:
        """Generate embedding using the provider chain with failover.
        Returns a list of floats.
        """
        for provider in self.providers:
            # Skip provider if circuit breaker marks it unhealthy
            if not circuit_breaker.is_healthy(provider.name):
                logger.warning("Skipping unhealthy provider %s", provider.name)
                continue
            try:
                logger.info("Attempting embedding with %s", provider.name)
                # Apply timeout
                embedding = await with_timeout(provider.embed(text), settings.EMBEDDING_TIMEOUT)
                logger.info("Embedding succeeded with %s", provider.name)
                circuit_breaker.record_success(provider.name)
                return embedding
            except Exception as exc:
                logger.warning("Embedding provider %s failed: %s", provider.name, exc)
                circuit_breaker.record_failure(provider.name)
                # continue to next fallback
        raise RuntimeError("All embedding providers failed")

# Export a singleton for easy import
provider_factory = ProviderFactory()
