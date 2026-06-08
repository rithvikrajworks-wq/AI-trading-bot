# backend/app/services/circuit_breaker.py

"""Simple circuit breaker implementation for AI providers.
Tracks consecutive failures; when threshold exceeded, the provider is marked unhealthy
for a cooldown period defined in settings.CIRCUIT_BREAKER_COOLDOWN_MINUTES.
"""

import time
from collections import defaultdict
from typing import Dict

from app.settings import settings

class CircuitBreaker:
    def __init__(self, failure_threshold: int = 3):
        self.failure_threshold = failure_threshold
        # Store counts and timestamps per provider name
        self.failure_counts: Dict[str, int] = defaultdict(int)
        self.unhealthy_until: Dict[str, float] = {}

    def record_success(self, provider_name: str) -> None:
        self.failure_counts[provider_name] = 0
        if provider_name in self.unhealthy_until:
            del self.unhealthy_until[provider_name]

    def record_failure(self, provider_name: str) -> None:
        self.failure_counts[provider_name] += 1
        if self.failure_counts[provider_name] >= self.failure_threshold:
            cooldown = settings.CIRCUIT_BREAKER_COOLDOWN_MINUTES * 60
            self.unhealthy_until[provider_name] = time.time() + cooldown
            self.failure_counts[provider_name] = 0  # reset after tripping

    def is_healthy(self, provider_name: str) -> bool:
        until = self.unhealthy_until.get(provider_name)
        if until is None:
            return True
        if time.time() >= until:
            # cooldown expired, provider becomes healthy again
            del self.unhealthy_until[provider_name]
            return True
        return False

# Export a singleton for global use
circuit_breaker = CircuitBreaker()
