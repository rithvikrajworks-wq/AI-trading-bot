import logging
from typing import List, Dict, Any

from app.services.stock_service import StockService
from app.services.ai_provider import OpenAIProvider, AIProvider
from app.schemas.chat import ChatRequest, ChatResponse, AnalysisSummary, RiskSummary

logger = logging.getLogger(__name__)


class ChatService:
    """Service handling AI‑driven stock discussion.
    It grounds the conversation in the live analysis from :class:`StockService`.
    """

    def __init__(self, provider: AIProvider | None = None):
        # Provider abstraction – default to OpenAI if none supplied.
        # Lazy initialization: instantiate only when needed to avoid unnecessary env checks.
        self._provider = provider
        self.stock_service = StockService()

    @property
    def provider(self) -> AIProvider:
        # Instantiate default OpenAIProvider on first use if not already set.
        if self._provider is None:
            self._provider = OpenAIProvider()
        return self._provider


    def _system_prompt(self) -> str:
        """Static system prompt enforcing safety and tone.
        This is used for every chat request.
        """
        return (
            "You are a professional, analytical AI trading copilot. "
            "Never guarantee profits, never express emotions, and never encourage reckless trading. "
            "Avoid hype language such as \"to the moon\". "
            "Always discuss both opportunities and risks, and keep a cautious, balanced tone."
        )

    def _build_user_prompt(self, request: ChatRequest, analysis: Dict[str, Any]) -> str:
        """Combine the user message with relevant analysis data.
        The prompt includes the requested ticker's technical factors so the model can ground its response.
        """
        parts = [request.user_message]
        # Append key analysis fields for grounding
        parts.append("\n---Analysis Context---")
        parts.append(f"Signal: {analysis.get('signal')}, Confidence: {analysis.get('confidence')}%")
        parts.append(f"Trend Summary: {analysis.get('timeframe_summary')}")
        parts.append(f"RSI: {analysis.get('rsi')}, EMA Trend: {analysis.get('ema_trend')}, MACD: {analysis.get('macd')}")
        parts.append(f"Momentum: {analysis.get('momentum')}, Alignment Score: {analysis.get('alignment_score')}")
        parts.append(f"ATR: {analysis.get('atr')}, Volatility Level: {analysis.get('volatility_level')}")
        parts.append(f"Support: {analysis.get('nearest_support')}, Resistance: {analysis.get('nearest_resistance')}")
        parts.append(f"Entry Quality: {analysis.get('entry_quality')}, Breakout Probability: {analysis.get('breakout_probability')}%")
        parts.append(f"Stop Loss: {analysis.get('stop_loss')}, Take Profit: {analysis.get('take_profit')}")
        parts.append(f"Risk/Reward Ratio: {analysis.get('risk_reward_ratio')}")
        if request.market_context:
            parts.append("\n---Market Context---")
            parts.append(str(request.market_context))
        return "\n".join(parts)

    def _risk_summary(self, analysis: Dict[str, Any]) -> RiskSummary:
        """Derive a concise risk summary from analysis data.
        This is a deterministic piece of information, not AI‑generated.
        """
        # Simple heuristic strings – can be expanded later.
        support_resistance_risk = (
            "price close to resistance" if analysis.get('price', 0) > analysis.get('nearest_resistance', 0) * 0.98
            else "price close to support" if analysis.get('price', 0) < analysis.get('nearest_support', 0) * 1.02
            else "within normal range"
        )
        volatility_risk = (
            "high volatility" if analysis.get('volatility_level') == "high"
            else "medium volatility" if analysis.get('volatility_level') == "medium"
            else "low volatility"
        )
        # Conflict between timeframes when alignment_score is low
        alignment_conflict = (
            "timeframe alignment conflict" if analysis.get('alignment_score', 0) < 50 else "aligned across timeframes"
        )
        overall_risk = (
            "high risk" if any([support_resistance_risk != "within normal range", volatility_risk == "high volatility", alignment_conflict == "timeframe alignment conflict"]) else "moderate/low risk"
        )
        return RiskSummary(
            support_resistance_risk=support_resistance_risk,
            volatility_risk=volatility_risk,
            alignment_conflict=alignment_conflict,
            overall_risk=overall_risk,
        )

    async def chat(self, request: ChatRequest) -> ChatResponse:
        # Get live analysis (cached inside StockService)
        analysis = await self.stock_service.analyze_ticker(request.ticker)
        logger.debug(f"Analysis for {request.ticker}: {analysis}")

        system_prompt = self._system_prompt()
        user_prompt = self._build_user_prompt(request, analysis)
        history = request.conversation_history or []

        # Call the LLM provider
        response_text = await self.provider.chat_completion(system_prompt, user_prompt, history)

        # Assemble structured response
        analysis_summary = AnalysisSummary(
            timeframe_summary=analysis.get("timeframe_summary", {}),
            rsi=analysis.get("rsi", 0),
            ema_trend=analysis.get("ema_trend", "neutral"),
            macd=analysis.get("macd", "neutral"),
            momentum=analysis.get("momentum", 0),
            alignment_score=analysis.get("alignment_score", 0),
            confidence=analysis.get("confidence", 0),
            entry_quality=analysis.get("entry_quality", "moderate"),
            breakout_probability=analysis.get("breakout_probability", 0),
            atr=analysis.get("atr", 0),
            volatility_level=analysis.get("volatility_level", "low"),
            nearest_support=analysis.get("nearest_support", 0),
            nearest_resistance=analysis.get("nearest_resistance", 0),
            risk_reward_ratio=analysis.get("risk_reward_ratio", 0),
            stop_loss=analysis.get("stop_loss", 0),
            take_profit=analysis.get("take_profit", {}),
        )
        risk_summary = self._risk_summary(analysis)
        return ChatResponse(
            ticker=request.ticker.upper(),
            response=response_text,
            analysis_summary=analysis_summary,
            risk_summary=risk_summary,
        )
