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
        # Debug: show the prompt that will be sent to Gemini (first 500 chars)
        self.logger.debug("Prompt preview (first 500 chars): %s", user_prompt[:500])
        system_prompt = self.system_prompt

        # Call the LLM (with retry/back‑off handled by BaseAgent)
        raw_response = await self.generate_response(system_prompt, user_prompt)
        # Debug: raw Gemini response preview (first 500 chars)
        self.logger.debug("Raw Gemini response preview (first 500 chars): %s", raw_response[:500])

        # Attempt to validate the full response; BaseAgent will extract JSON safely
        try:
            response_obj = self.validate_response(raw_response)
            # Debug: extracted JSON keys after validation
            self.logger.debug("Extracted JSON keys: %s", list(response_obj.dict().keys()))
            # Separate prose for persistence: everything before the first JSON object
            json_start = raw_response.find('{')
            prose = raw_response[:json_start].strip() if json_start != -1 else raw_response.strip()
        except Exception as exc:
            # If validation fails, log and return a fallback response
            self.logger.error("AI response validation failed: %s", exc)
            response_obj = self._fallback_response()
            prose = raw_response  # store whatever was received as prose
            # Debug: indicate fallback is used
            self.logger.debug("Using fallback AnalysisResponse due to validation failure.")

        # ---- Placeholder quality guard ----
        placeholder_fields = self._detect_placeholders(response_obj)
        if placeholder_fields:
            self.logger.warning("Detected placeholder fields: %s", placeholder_fields)
            # Retry once with a corrective instruction
            corrective_prompt = user_prompt + "\n\nPlease rewrite the JSON with real analysis based on the indicators. Do NOT use any placeholder text such as 'No summary available.'"
            self.logger.info("Retrying Gemini with corrective prompt for %s", ticker)
            raw_response_retry = await self.generate_response(system_prompt, corrective_prompt)
            self.logger.debug("Raw Gemini retry response preview (first 500 chars): %s", raw_response_retry[:500])
            try:
                response_obj = self.validate_response(raw_response_retry)
                json_start = raw_response_retry.find('{')
                prose = raw_response_retry[:json_start].strip() if json_start != -1 else raw_response_retry.strip()
                # Re‑check placeholders after retry
                placeholder_fields = self._detect_placeholders(response_obj)
                if placeholder_fields:
                    self.logger.error("Retry still returned placeholders: %s", placeholder_fields)
                    response_obj = self._fallback_response()
                else:
                    self.logger.info("Retry succeeded with real analysis for %s", ticker)
            except Exception as exc:
                self.logger.error("Retry validation failed: %s", exc)
                response_obj = self._fallback_response()

        # Persist the narrative analysis text using schema‑compatible arguments
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

    # ---- Helper to detect placeholder strings ----
    def _detect_placeholders(self, response_obj: "AnalysisResponse") -> list:
        """Return a list of field names that contain known placeholder text.

        If the list is empty, the response is considered real.
        """
        placeholder_texts = {
            "summary": "No summary available.",
            "company_overview": "No company overview available.",
            "technical_analysis": "No technical analysis available.",
            "chart_analysis": "No chart analysis available.",
            "trend_analysis": "No trend analysis available.",
            "momentum_analysis": "No momentum analysis available.",
            "support_resistance_analysis": "No support/resistance analysis available.",
            "bull_case": "No bull case available.",
            "bear_case": "No bear case available.",
            "investment_thesis": "No investment thesis available.",
            "position_assessment": "No position assessment available.",
            "entry_strategy": "No entry strategy available.",
            "exit_strategy": "No exit strategy available.",
            "holding_period_rationale": "No holding period rationale available.",
        }
        detected = []
        for field, placeholder in placeholder_texts.items():
            if getattr(response_obj, field, None) == placeholder:
                detected.append(field)
        return detected

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
