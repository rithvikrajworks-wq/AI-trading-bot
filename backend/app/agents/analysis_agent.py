"""AnalysisAgent implementation – AI‑native stock analysis.

The agent inherits from :class:`BaseAgent` and uses the Gemini provider by
default.  It loads the prompt from ``backend/app/agents/prompts/analysis_prompt.txt``
and validates the LLM output against :class:`AnalysisResponse`.
"""

import json
import logging
import time
from ..services.stock_service import StockService
from typing import Any, Dict, List

from pydantic import BaseModel

from ..services.base_agent import BaseAgent, AIProviderError, InvalidAIResponseError, PromptLoadError
from .analysis_response import AnalysisResponse

# ---------------------------------------------------------------------------
# Helper utilities specific to analysis generation
# ---------------------------------------------------------------------------

def _clamp_confidence(value: int) -> int:
    """Clamp confidence score to the 0‑100 range."""
    return max(0, min(100, value))


def _deduplicate(seq: List[str]) -> List[str]:
    """Return a list preserving order but removing duplicates."""
    seen = set()
    result = []
    for item in seq:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result


class AnalysisAgent(BaseAgent):
    """Agent that produces a structured stock analysis.

    Parameters
    ----------
    prompt_name: ``analysis_prompt`` – the template file located in
        ``backend/app/agents/prompts/``.
    response_schema: :class:`AnalysisResponse` – strict JSON schema that the
        Gemini model must obey.
    """

    def __init__(self):
        super().__init__(prompt_name="analysis_prompt", response_schema=AnalysisResponse)
        self.logger = logging.getLogger(self.__class__.__name__)

    # ---------------------------------------------------------------------
    # Prompt construction – callers pass raw indicator dicts
    # ---------------------------------------------------------------------
    def _prepare_prompt_data(self, ticker: str, indicators: Dict[str, Any]) -> Dict[str, Any]:
        """Collect data that will be interpolated into the prompt.

        The ``indicators`` dict is expected to contain the numeric market data
        fetched by ``stock_service`` (OHLCV, RSI, MACD, EMA, ATR, volume, etc.).
        ``json.dumps`` is used so the LLM receives a deterministic JSON block.
        """
        return {
            "ticker": ticker,
            "indicators_json": json.dumps(indicators, indent=2, sort_keys=True),
        }

    # ---------------------------------------------------------------------
    # Public API – the entry point used by callers
    # ---------------------------------------------------------------------
    async def analyze(self, ticker: str, market_data: Dict[str, Any]) -> AnalysisResponse:
        """Generate AI‑native analysis for *ticker* using Gemini.

        Helper wrapper called by API endpoints.
        """
        indicators = {k: v for k, v in market_data.items() if k != "ticker"}
        return await self.run(ticker, **indicators)

    async def run(self, ticker: str, **indicators: Any) -> AnalysisResponse:
        """Generate AI‑native analysis for *ticker* using Gemini.

        The LLM produces natural‑language prose followed by a JSON block.
        The prose is persisted for later reuse, and the JSON is validated
        against ``AnalysisResponse``.
        """
        start = time.time()
        # Prepare prompt data (raw indicator dict is passed directly)
        prompt_data = self._prepare_prompt_data(ticker, indicators)
        await self.load_prompt()
        user_prompt = self.build_prompt(**prompt_data)
        system_prompt = self.system_prompt

        # Call the LLM (with retry/back‑off handled by BaseAgent)
        raw_response = await self.generate_response(system_prompt, user_prompt)

        # Split into prose (text before the first "{") and JSON part
        json_start = raw_response.find("{")
        if json_start != -1:
            prose = raw_response[:json_start].strip()
            json_part = raw_response[json_start:]
        else:
            prose = raw_response.strip()
            json_part = raw_response

        # Validate and parse the JSON block
        response_obj = self.validate_response(json_part)

        # Persist the narrative analysis text using schema-compatible arguments
        try:
            from ..database import SessionLocal
            from ..repositories.analysis_repo import save_analysis
            db = SessionLocal()
            try:
                save_analysis(
                    db=db,
                    ticker=ticker,
                    analysis_text=prose,
                    structured_output=response_obj.model_dump_json(),
                    signal=response_obj.signal,
                    confidence=response_obj.confidence,
                    risk_level=response_obj.risk_level,
                )
            finally:
                db.close()
        except Exception as exc:
            self.logger.error("Failed to persist analysis text for %s: %s", ticker, exc)

        duration = time.time() - start
        self.logger.info("AnalysisAgent completed for %s in %.2f s", ticker, duration)
        return self.post_process(response_obj)

    # ---------------------------------------------------------------------
    # Fallback response – used when the LLM pipeline fails
    # ---------------------------------------------------------------------
    def _fallback_response(self) -> AnalysisResponse:
        fallback = {
            "signal": "HOLD",
            "confidence": 0,
            "risk_level": "Unknown",
            "summary": "AI analysis temporarily unavailable.",
            "technical_analysis": "",
            "entry_strategy": "",
            "exit_strategy": "",
            "key_levels": [],
            "warnings": [],
        }
        return AnalysisResponse.parse_obj(fallback)

    # ---------------------------------------------------------------------
    # Post‑processing implementation required by the spec
    # ---------------------------------------------------------------------
    def post_process(self, model_instance: BaseModel) -> AnalysisResponse:
        """Apply domain‑specific clean‑up before returning the model.

        * Confidence is clamped to 0‑100.
        * Whitespace is stripped from string fields.
        * Duplicate entries in ``key_levels`` and ``warnings`` are removed.
        * ``signal`` is normalised to upper‑case (BUY/SELL/HOLD).
        """
        data = model_instance.dict()
        # Clamp confidence
        data["confidence"] = _clamp_confidence(int(data.get("confidence", 0)))
        # Normalise strings
        for field in ["signal", "summary", "technical_analysis", "entry_strategy", "exit_strategy", "risk_level"]:
            if isinstance(data.get(field), str):
                data[field] = data[field].strip()
        # Normalise signal capitalization and enforce allowed literals
        signal = data.get("signal", "HOLD").upper()
        if signal not in {"BUY", "SELL", "HOLD"}:
            signal = "HOLD"
        data["signal"] = signal
        # Deduplicate list fields
        for list_field in ["key_levels", "warnings"]:
            lst = data.get(list_field, [])
            if isinstance(lst, list):
                data[list_field] = _deduplicate([str(item).strip() for item in lst])
        return AnalysisResponse.parse_obj(data)

    # ---------------------------------------------------------------------
    # Optional system prompt – can be overridden later
    # ---------------------------------------------------------------------
    @property
    def system_prompt(self) -> str:
        return (
            "You are a professional hedge‑fund analyst. Generate a concise, "
            "structured JSON response strictly following the provided schema. "
            "Do not fabricate data; use only the indicators supplied."
        )

    # ---------------------------------------------------------------------
    # The BaseAgent defines ``build_prompt`` which expects a ``{ticker}`` and
    # ``{indicators_json}`` placeholder in the template file.  No further
    # overrides are required.
    # ---------------------------------------------------------------------
