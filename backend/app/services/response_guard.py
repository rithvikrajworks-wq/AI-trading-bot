# backend/app/services/response_guard.py

"""Response guard for AI outputs.
- JSON repair (basic)
- Clamp numeric fields (confidence 0-100)
- Remove hallucinated price statements
- Append financial disclaimer
"""

import json
import re
import logging
from typing import Any, Dict

from app.settings import settings

logger = logging.getLogger("response_guard")

class ResponseGuard:
    def __init__(self):
        # Pre‑compile regexes for performance
        self.price_regex = re.compile(r"\bprice is \$?\d+(?:\.\d+)?\b", re.IGNORECASE)
        self.disclaimer = settings.FINANCIAL_DISCLAIMER

    async def _repair_json(self, raw: str) -> str:
        """Attempt to fix common JSON issues.
        Very naive implementation – removes trailing commas and ensures proper braces.
        """
        try:
            # Try parsing directly first
            obj = json.loads(raw)
            return json.dumps(obj)
        except json.JSONDecodeError:
            # Simple repairs: remove trailing commas before closing braces/brackets
            cleaned = re.sub(r",(\s*[}\]])", r"\1", raw)
            try:
                obj = json.loads(cleaned)
                return json.dumps(obj)
            except json.JSONDecodeError as exc:
                logger.warning("Failed to repair JSON: %s", exc)
                # Return original raw if unrecoverable
                return raw

    def _clamp_confidence(self, data: Any) -> Any:
        """Recursively clamp any numeric field named 'confidence' to 0‑100."""
        if isinstance(data, dict):
            for k, v in data.items():
                if k.lower() == "confidence" and isinstance(v, (int, float)):
                    data[k] = max(0, min(100, v))
                else:
                    data[k] = self._clamp_confidence(v)
        elif isinstance(data, list):
            return [self._clamp_confidence(item) for item in data]
        return data

    def _remove_hallucinations(self, text: str) -> str:
        """Strip sentences that look like fabricated price statements."""
        return self.price_regex.sub("", text)

    async def guard(self, raw_response: str, context: Dict[str, Any] | None = None) -> str:
        """Apply all guard steps and return safe response string.
        Returns a JSON string if the original was JSON‑like, otherwise a plain string.
        """
        # Step 1: JSON repair (if looks like JSON)
        if raw_response.strip().startswith("{"):
            repaired = await self._repair_json(raw_response)
            try:
                data = json.loads(repaired)
                # Step 2: clamp confidence values
                data = self._clamp_confidence(data)
                # Step 3: add disclaimer if missing (in a top‑level "disclaimer" field if exists)
                if isinstance(data, dict):
                    if "disclaimer" not in data:
                        data["disclaimer"] = self.disclaimer
                return json.dumps(data)
            except json.JSONDecodeError:
                # Fallback to plain text handling
                pass
        # Non‑JSON or repair failed – treat as plain text
        cleaned = self._remove_hallucinations(raw_response)
        # Ensure disclaimer present at end of text
        if self.disclaimer not in cleaned:
            cleaned = cleaned.rstrip() + "\n" + self.disclaimer
        return cleaned

# Export singleton for easy import
response_guard = ResponseGuard()
