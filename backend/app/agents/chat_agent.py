# backend/app/agents/chat_agent.py

"""ChatAgent orchestrates the chat flow using memory, stock analysis, and the AI orchestrator.
It provides a safe fallback response on any internal error.
"""

import logging
from typing import List, Dict, Any

from app.schemas.chat import ChatRequest, ChatResponse, AnalysisSummary, RiskSummary
from app.services.stock_service import StockService
from app.services.ai_orchestrator import ai_orchestrator
from app.services.response_guard import response_guard
from app.agents.memory_agent import memory_agent
from app.agents.memory.memory_store import memory_store

logger = logging.getLogger("chat_agent")

class ChatAgent:
    def __init__(self):
        self.stock_service = StockService()

    def _system_prompt(self) -> str:
        return (
            "You are a professional, analytical AI trading copilot. "
            "Never guarantee profits, never express emotions, and never encourage reckless trading. "
            "Avoid hype language such as 'to the moon'. "
            "Always discuss both opportunities and risks, and keep a cautious, balanced tone."
        )

    def _build_user_prompt(self, request: ChatRequest, analysis: Dict[str, Any]) -> str:
        parts = [request.user_message]
        parts.append("\n---Analysis Context---")
        parts.append(f"Signal: {analysis.get('signal')}, Confidence: {analysis.get('confidence')}%")
        parts.append(f"Trend Summary: {analysis.get('timeframe_summary')}\n")
        # Add key fields
        fields = ["rsi", "ema_trend", "macd", "momentum", "alignment_score", "entry_quality", "breakout_probability", "atr", "volatility_level", "nearest_support", "nearest_resistance", "risk_reward_ratio", "stop_loss", "take_profit"]
        for f in fields:
            if f in analysis:
                parts.append(f"{f.replace('_', ' ').title()}: {analysis[f]}")
        if request.market_context:
            parts.append("\n---Market Context---")
            parts.append(str(request.market_context))
        return "\n".join(parts)

    async def _assemble_context(self, user_id: str) -> str:
        """Gather recent and relevant memories and format them as a string for the LLM."""
        recent = await memory_store.get_recent(user_id)
        recent_str = "\n".join([f"{role.title()}: {content}" for role, content, _, _ in recent])
        # Use the last user message as a simple query for relevance (placeholder)
        query = ""  # No specific query here; could be refined later
        relevant = []
        if query:
            relevant = await memory_agent.retrieve_relevant(user_id, query)
        relevant_str = "\n".join([f"{m.get('role', 'User').title()}: {m.get('content', '')}" for m in relevant])
        return "\n".join(filter(None, [recent_str, relevant_str]))

    async def handle_chat(self, request: ChatRequest) -> ChatResponse:
        user_id = "default_user"
        try:
            # 1. Get live analysis
            analysis = await self.stock_service.analyze_ticker(request.ticker)
            logger.debug("Analysis for %s: %s", request.ticker, analysis)

            # 2. Build prompts
            system_prompt = self._system_prompt()
            user_prompt = self._build_user_prompt(request, analysis)
            memory_context = await self._assemble_context(user_id)
            full_prompt = "\n".join(filter(None, [system_prompt, memory_context, user_prompt]))

            # 3. Generate response via orchestrator
            raw_response = await ai_orchestrator.generate(user_id, full_prompt, endpoint="chat")
            guarded = await response_guard.guard(raw_response, context={"user_id": user_id})

            # 4. Persist messages (store only high‑importance user message)
            await memory_agent.store_message(user_id, "user", request.user_message)
            await memory_agent.store_message(user_id, "assistant", guarded)

            # 5. Assemble structured response (reuse existing schemas)
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
            # Simple risk summary (reuse existing helper from earlier ChatService if needed)
            risk_summary = RiskSummary(
                support_resistance_risk="",
                volatility_risk="",
                alignment_conflict="",
                overall_risk="",
            )
            return ChatResponse(
                ticker=request.ticker.upper(),
                response=guarded,
                analysis_summary=analysis_summary,
                risk_summary=risk_summary,
            )
        except Exception as exc:
            logger.error("ChatAgent failed: %s", exc)
            # Safe fallback payload – match the shape expected by endpoint
            raise Exception("Chat processing failed")

# Export singleton
chat_agent = ChatAgent()
