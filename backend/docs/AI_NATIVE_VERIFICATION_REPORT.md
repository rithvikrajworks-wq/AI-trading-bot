# AI Native Architecture Verification Report

## Executive Summary

| Component | PASS / FAIL | Reason |
|-----------|-------------|--------|
| **ScannerAgent** | **FAIL** | Returns a full `OpportunityResponse` (good) but later the pipeline discards many fields before ranking. The agent itself is AI‑native, however the overall flow loses data. |
| **RankingAgent** | **FAIL** | Implements its own reduced `RankedOpportunity` schema, discards the majority of `OpportunityResponse` fields, and contains a fallback block that synthesises investment‑related output in Python. |
| **Top Opportunities Endpoint** | **FAIL** | Strips the rich opportunity object to a minimal summary for ranking and then re‑injects only a subset, losing Patch V1/V2 fields. |
| **Overall Architecture** | **FAIL** | The architecture is **not** fully AI‑native because deterministic investment data is still generated in Python and important opportunity fields are lost during ranking. |

---

## 1. Complete Current Schemas

### OpportunityResponse
```python
from pydantic import BaseModel, Field, conint
from typing import List, Dict, Literal, Optional


class OpportunityResponse(BaseModel):
    # Core fields
    ticker: str = Field(..., description="The stock ticker symbol")
    confidence: conint(ge=0, le=100) = Field(..., description="Confidence score 0‑100")
    risk_level: Literal["Low", "Medium", "High", "Unknown"] = Field(
        ..., description="Risk assessment"
    )
    opportunity: str = Field(..., description="What opportunity exists?")
    why_interesting: str = Field(..., description="Why is it interesting?")
    catalyst: str = Field(..., description="What is the catalyst?")
    investor_appeal: str = Field(..., description="Why should an investor care?")
    risks: str = Field(..., description="What are the risks?")

    # ── Patch Detailing V1 ───────────────────────────────────────────────────────
    summary: str = Field(..., description="Executive summary")
    company_overview: str = Field(..., description="Company overview and market context")
    current_market_structure: str = Field(..., description="Current market structure description")
    chart_analysis: str = Field(..., description="Detailed chart analysis")
    volume_analysis: str = Field(..., description="Volume behavior analysis")
    current_price_position: str = Field(..., description="Current price position relative to range")
    trend_structure: str = Field(..., description="Trend and structure narrative")
    support_resistance_analysis: str = Field(..., description="Support/Resistance analysis")
    volume_profile_analysis: str = Field(..., description="Volume profile insights")
    technical_story: str = Field(..., description="Technical story narrative")
    investment_narrative: str = Field(..., description="Overall investment narrative")
    bull_thesis: str = Field(..., description="Bull thesis narrative")
    bear_thesis: str = Field(..., description="Bear thesis narrative")
    opportunity_thesis: str = Field(..., description="Overall opportunity thesis")
    risk_analysis: str = Field(..., description="Risk analysis narrative")
    catalysts: List[str] = Field(..., description="List of catalysts")
    institutional_activity: str = Field(..., description="Institutional activity narrative")
    trend_analysis: str = Field(..., description="Trend analysis narrative")
    momentum_analysis: str = Field(..., description="Momentum analysis narrative")
    market_sentiment: str = Field(..., description="Market sentiment narrative")
    warnings: List[str] = Field(..., description="Risk warnings or caveats")
    key_levels: List[str] = Field(..., description="Important support/resistance levels")

    # ── Trade‑setup fields ──────────────────────────────────────────────────────
    entry_strategy: str = Field(..., description="Entry strategy narrative")
    exit_strategy: str = Field(..., description="Exit strategy narrative")
    holding_period: str = Field(..., description="Suggested holding period")
    entry_zone: Dict[str, float] = Field(..., description="Entry price range with keys 'min' and 'max'")
    stop_loss: float = Field(..., description="Stop‑loss price")
    take_profit: Dict[str, float] = Field(..., description="Take‑profit targets with keys 'tp1' and 'tp2'")
    risk_reward_ratio: float = Field(..., description="Risk/Reward ratio")

    # ── Quantitative assessment ───────────────────────────────────────────────
    alignment_score: float = Field(..., description="Overall alignment score (0‑100)")

    # ── Patch Detailing V2 ─────────────────────────────────────────────────────
    bull_case_probability: conint(ge=0, le=100) = Field(..., description="Probability of bull case (0‑100)")
    base_case_probability: conint(ge=0, le=100) = Field(..., description="Probability of base case (0‑100)")
    bear_case_probability: conint(ge=0, le=100) = Field(..., description="Probability of bear case (0‑100)")
```

### RankedOpportunityResponse
```python
from pydantic import Field
from .opportunity_response import OpportunityResponse


class RankedOpportunityResponse(OpportunityResponse):
    """Opportunity response enriched with ranking metadata generated by RankingAgent."""

    rank: int = Field(..., description="Position in the ranked list (1 = top)")
    ranking_explanation: str = Field(..., description="Explanation for this specific rank")
    why_ranked_here: str = Field(..., description="Reason why the opportunity received this rank")
```

---

## 2. RankingAgent Verification

### Full current contents of `backend/app/agents/ranking_agent.py`
```python
import logging
import json
from typing import List, Dict, Any
from pydantic import BaseModel, Field

from ..services.base_agent import BaseAgent


class RankedOpportunity(BaseModel):
    ticker: str = Field(..., description="Stock ticker symbol")
    investment_thesis: str = Field(..., description="Investment thesis narrative")
    catalyst: str = Field(..., description="Catalyst driving the opportunity")
    risks: str = Field(..., description="Associated risks")
    confidence: int = Field(..., description="Confidence score")
    ranking_explanation: str = Field(..., description="Explanation for this specific rank")


class RankedOpportunitiesResponse(BaseModel):
    items: List[RankedOpportunity] = Field(..., description="List of ranked opportunities")


class RankingAgent(BaseAgent):
    """RankingAgent that ranks stock opportunities using Gemini."""

    def __init__(self):
        super().__init__(prompt_name="ranking_prompt", response_schema=RankedOpportunitiesResponse)
        self.logger = logging.getLogger(self.__class__.__name__)

    @property
    def system_prompt(self) -> str:
        return (
            "You are a senior portfolio manager. Evaluate the list of opportunities "
            "and rank them. Output a JSON object with a single key 'items' containing the list."
        )

    def post_process(self, model_instance: BaseModel) -> RankedOpportunitiesResponse:
        return model_instance

    async def rank(self, opportunities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Rank the given list of opportunities using Gemini."""
        if not opportunities:
            return []

        opportunities_json = json.dumps(opportunities, indent=2)
        await self.load_prompt()
        user_prompt = self.build_prompt(opportunities_json=opportunities_json)

        raw_response = await self.generate_response(self.system_prompt, user_prompt)

        # Extract JSON block
        json_start = raw_response.find("{")
        if json_start != -1:
            json_part = raw_response[json_start:]
        else:
            json_part = raw_response

        try:
            response_obj = self.validate_response(json_part)
            return [item.dict() for item in response_obj.items]
        except Exception as e:
            self.logger.error("RankingAgent failed to parse response: %s. Raw: %s", e, raw_response)
            # Safe fallback: return in original order
            return [
                {
                    "ticker": o["ticker"],
                    "investment_thesis": o.get("opportunity", "N/A"),
                    "catalyst": o.get("catalyst", "N/A"),
                    "risks": o.get("risks", "N/A"),
                    "confidence": o.get("confidence", 50),
                    "ranking_explanation": "Fallback ranking due to agent failure."
                }
                for o in opportunities
            ]
```

### Analysis
* **Schema actually used** – `RankingAgent` is instantiated with `response_schema=RankedOpportunitiesResponse` (the reduced schema defined at the top of this file). It does **not** use the full `OpportunityResponse` or the `RankedOpportunityResponse` model defined in `schemas/ranked_opportunity_response.py`.
* **Fields returned** – After a successful Gemini call the agent returns a list of objects containing exactly the six fields defined in `RankedOpportunity`:
  * `ticker`
  * `investment_thesis`
  * `catalyst`
  * `risks`
  * `confidence`
  * `ranking_explanation`
* **Does it operate on the full `OpportunityResponse`?** – **No.** The endpoint sends a *summary* dict to the agent (see section 4). The agent never receives the full set of Patch V1/V2 fields.
* **Field discarding** – All Patch V1 fields (`summary`, `company_overview`, … `warnings`, `key_levels`) and Patch V2 fields (`bull_case_probability`, `entry_zone`, `stop_loss`, `take_profit`, `risk_reward_ratio`, `alignment_score`, etc.) are **dropped** before ranking.
* **Fallback block** – When Gemini parsing fails the fallback code **synthesises** an `investment_thesis`, `catalyst`, `risks`, and `confidence` purely inside Python. This violates the “no investment logic in Python” rule.

---

## 3. Opportunity Preservation Audit

| Field | Present Before Ranking (ScannerAgent output) | Present After Ranking (RankingAgent output) | Preserved? |
|-------------------------------|----------------------------|----------------------------|------------|
| ticker | ✅ | ✅ | ✅ |
| confidence | ✅ | ✅ | ✅ |
| risk_level | ✅ | ❌ | ❌ |
| opportunity | ✅ | ❌ (renamed to `investment_thesis` in fallback) | ❌ |
| why_interesting | ✅ | ❌ | ❌ |
| catalyst | ✅ | ✅ | ✅ |
| investor_appeal | ✅ | ❌ | ❌ |
| risks | ✅ | ✅ | ✅ |
| summary | ✅ | ❌ | ❌ |
| company_overview | ✅ | ❌ | ❌ |
| current_market_structure | ✅ | ❌ | ❌ |
| chart_analysis | ✅ | ❌ | ❌ |
| volume_analysis | ✅ | ❌ | ❌ |
| current_price_position | ✅ | ❌ | ❌ |
| trend_structure | ✅ | ❌ | ❌ |
| support_resistance_analysis | ✅ | ❌ | ❌ |
| volume_profile_analysis | ✅ | ❌ | ❌ |
| technical_story | ✅ | ❌ | ❌ |
| investment_narrative | ✅ | ❌ | ❌ |
| bull_thesis | ✅ | ❌ | ❌ |
| bear_thesis | ✅ | ❌ | ❌ |
| opportunity_thesis | ✅ | ❌ | ❌ |
| risk_analysis | ✅ | ❌ | ❌ |
| catalysts | ✅ | ❌ | ❌ |
| institutional_activity | ✅ | ❌ | ❌ |
| trend_analysis | ✅ | ❌ | ❌ |
| momentum_analysis | ✅ | ❌ | ❌ |
| market_sentiment | ✅ | ❌ | ❌ |
| warnings | ✅ | ❌ | ❌ |
| key_levels | ✅ | ❌ | ❌ |
| entry_strategy | ✅ | ❌ | ❌ |
| exit_strategy | ✅ | ❌ | ❌ |
| holding_period | ✅ | ❌ | ❌ |
| entry_zone | ✅ | ❌ | ❌ |
| stop_loss | ✅ | ❌ | ❌ |
| take_profit | ✅ | ❌ | ❌ |
| risk_reward_ratio | ✅ | ❌ | ❌ |
| alignment_score | ✅ | ❌ | ❌ |
| bull_case_probability | ✅ | ❌ | ❌ |
| base_case_probability | ✅ | ❌ | ❌ |
| bear_case_probability | ✅ | ❌ | ❌ |

*✅ means the field exists in the JSON object; ❌ means it is missing.*

---

## 4. API Response Flow (Realistic Example)

### 4.1 ScannerAgent Output (full `OpportunityResponse`)
```json
{
  "ticker": "AAPL",
  "confidence": 92,
  "risk_level": "Medium",
  "opportunity": "Tech‑lead growth on bullish trend",
  "why_interesting": "Strong earnings beat, expanding margins",
  "catalyst": "Upcoming product launch",
  "investor_appeal": "High upside with limited downside",
  "risks": "Supply‑chain constraints",
  "summary": "Apple shows a clear up‑trend with robust fundamentals.",
  "company_overview": "Apple Inc. designs, manufactures …",
  "current_market_structure": "Bullish continuation pattern",
  "chart_analysis": "Higher highs‑higher lows on 4‑hour chart",
  "volume_analysis": "Volume spikes on breakout candles",
  "current_price_position": "Near 75% of 52‑wk range",
  "trend_structure": "Up‑trend with 3‑month EMA support",
  "support_resistance_analysis": "Support 125.5, Resistance 138.0",
  "volume_profile_analysis": "High volume node at 130.0",
  "technical_story": "Breakout from ascending triangle",
  "investment_narrative": "Long‑term growth driver",
  "bull_thesis": "Revenue acceleration",
  "bear_thesis": "Mac sales slowdown",
  "opportunity_thesis": "Catalyst‑driven upside",
  "risk_analysis": "Geopolitical exposure",
  "catalysts": ["Product launch", "Q3 earnings"],
  "institutional_activity": "Net inflow of $2B",
  "trend_analysis": "Momentum sustaining",
  "momentum_analysis": "RSI 68",
  "market_sentiment": "Positive",
  "warnings": ["Valuation premium"],
  "key_levels": ["125.5", "130.0", "138.0"],
  "entry_strategy": "Buy on pull‑back to support",
  "exit_strategy": "Target resistance, trail stop",
  "holding_period": "Medium term (3‑6 months)",
  "entry_zone": {"min": 125.50, "max": 129.00},
  "stop_loss": 122.00,
  "take_profit": {"tp1": 140.0, "tp2": 150.0},
  "risk_reward_ratio": 2.5,
  "alignment_score": 84.3,
  "bull_case_probability": 78,
  "base_case_probability": 15,
  "bear_case_probability": 7
}
```

### 4.2 RankingAgent Input (what the endpoint actually sends)
```json
[
  {
    "ticker": "AAPL",
    "signal": "BUY",
    "confidence": 92,
    "opportunity": "Tech‑lead growth on bullish trend",
    "risks": "Supply‑chain constraints",
    "catalyst": "Upcoming product launch"
  },
  {
    "ticker": "MSFT",
    "signal": "BUY",
    "confidence": 88,
    "opportunity": "Cloud services expansion",
    "risks": "Regulatory risk",
    "catalyst": "Azure contracts"
  }
]
```
*(Only the six fields defined in `RankedOpportunity` are sent.)*

### 4.3 RankingAgent Output (current implementation)
```json
[
  {
    "ticker": "AAPL",
    "investment_thesis": "Tech‑lead growth on bullish trend",
    "catalyst": "Upcoming product launch",
    "risks": "Supply‑chain constraints",
    "confidence": 92,
    "ranking_explanation": "Higher confidence and stronger catalyst than peers"
  },
  {
    "ticker": "MSFT",
    "investment_thesis": "Cloud services expansion",
    "catalyst": "Azure contracts",
    "risks": "Regulatory risk",
    "confidence": 88,
    "ranking_explanation": "Slightly lower confidence than AAPL"
  }
]
```

### 4.4 `/top‑opportunities` Response (what the client receives)
```json
[
  {
    "ticker": "AAPL",
    "price": 132.45,
    "signal": "BUY",
    "confidence": 92,
    "rsi": 66,
    "macd": "bullish",
    "ema_trend": "up",
    "pros": ["Tech‑lead growth on bullish trend"],
    "cons": ["Supply‑chain constraints"],
    "entry_zone": {"min": 125.5, "max": 129.0},
    "stop_loss": 122.0,
    "take_profit": {"tp1": 140.0, "tp2": 150.0},
    "holding_period": "Medium term (3‑6 months)",
    "risk_reward_ratio": 2.5,
    "atr": 1.34,
    "volatility_level": "medium",
    "setup_quality": "high",
    "nearest_support": 125.5,
    "nearest_resistance": 138.0,
    "entry_quality": "moderate",
    "breakout_probability": 80,
    "timeframes": {...},
    "timeframe_summary": "...",
    "alignment_score": 84.3,
    "ranking_explanation": "Higher confidence and stronger catalyst than peers",
    "investment_thesis": "Tech‑lead growth on bullish trend",
    "catalyst": "Upcoming product launch",
    "risks_list": ["Supply‑chain constraints"]
  },
  {
    "ticker": "MSFT",
    "price": 285.10,
    "signal": "BUY",
    "confidence": 88,
    "rsi": 62,
    "macd": "bullish",
    "ema_trend": "up",
    "pros": ["Cloud services expansion"],
    "cons": ["Regulatory risk"],
    "entry_zone": {"min": 270.0, "max": 275.0},
    "stop_loss": 265.0,
    "take_profit": {"tp1": 295.0, "tp2": 310.0},
    "holding_period": "Medium term (3‑6 months)",
    "risk_reward_ratio": 2.7,
    "atr": 2.12,
    "volatility_level": "medium",
    "setup_quality": "high",
    "nearest_support": 270.0,
    "nearest_resistance": 295.0,
    "entry_quality": "moderate",
    "breakout_probability": 70,
    "timeframes": {...},
    "timeframe_summary": "...",
    "alignment_score": 78.0,
    "ranking_explanation": "Slightly lower confidence than AAPL",
    "investment_thesis": "Cloud services expansion",
    "catalyst": "Azure contracts",
    "risks_list": ["Regulatory risk"]
  }
]
```
*Only the six ranking‑specific fields are added back; all other Patch V1/V2 fields are missing.

---

## 5️⃣ Deterministic Logic Audit

| File | Location (line numbers) | Deterministic logic found | Influence | Classification |
|------|------------------------|---------------------------|-----------|----------------|
| `backend/app/services/stock_service.py` | 99‑110 | **Alignment score** – weighted average of trend‑score & RSI‑factor across timeframes. | Influences *alignment_score* (used later for risk/confidence). | **Deterministic Investment Logic** |
| `backend/app/services/stock_service.py` | 143‑165 | **Trade‑setup calculations** (entry min/max, stop‑loss, take‑profit, risk‑reward ratio). | Generates *entry_zone*, *stop_loss*, *take_profit*, *risk_reward_ratio*. Infrastructure‑allowed, but still part of investment parameters. | **Analytics / Infrastructure Logic** |
| `backend/app/services/stock_service.py` | 168‑179 | **Breakout probability** heuristic based on price vs. support/resistance & ATR. | Produces *breakout_probability* (investment‑related probability). | **Deterministic Investment Logic** |
| `backend/app/agents/ranking_agent.py` | 60‑69 (fallback block) | **Synthetic investment fields** – constructs `investment_thesis`, `catalyst`, `risks`, and default `confidence` when Gemini fails. | Directly creates investment output inside Python. | **Deterministic Investment Logic** |
| `backend/app/agents/ranking_agent.py` | 24 (constructor) | **Prompt name `ranking_prompt` does not exist** – leads to empty prompt loading, forcing the agent to rely on the hard‑coded system_prompt. | No Gemini‑driven ranking prompt, reduces AI involvement. | **Infrastructure Logic** |
| `backend/app/api/endpoints/top_opportunities.py` | 71‑81 | **Summarisation step** – builds a *minimal* dict (`opp_summaries`) with only `ticker`, `signal`, `confidence`, `opportunity`, `risks`, `catalyst`. | Strips away all other fields before ranking. | **Data‑loss / Architectural Logic** |
| `backend/app/api/endpoints/top_opportunities.py` | 85‑102 | **Fallback ordering** – if ranking fails, the original order is kept; no additional AI logic. | Does not affect ranking outcome but hides failures. | **Infrastructure Logic** |

**No deterministic logic affecting ranking, confidence, risk, or recommendation is present in the RankingAgent beyond the fallback block.**

---

## 6️⃣ Fallback Behavior Audit

* **RankingAgent fallback (lines 60‑69)** – when Gemini JSON cannot be parsed, the code creates a dictionary with:
  ```python
  "investment_thesis": o.get("opportunity", "N/A"),
  "catalyst": o.get("catalyst", "N/A"),
  "risks": o.get("risks", "N/A"),
  "confidence": o.get("confidence", 50),
  "ranking_explanation": "Fallback ranking due to agent failure."
  ```
  This **generates investment‑related output** inside Python and therefore breaches the AI‑native rule.
* **ScannerAgent** – currently the scanner already delegates the narrative generation to Gemini; the only deterministic pieces are the math for entry zones, stop‑loss, TP, etc., which are allowed as infrastructure.
* No other fallback code was found that synthesises investment data.

---

## 7️⃣ AI‑Native Compliance Assessment

| Component | PASS / FAIL | Rationale |
|-----------|-------------|-----------|
| **ScannerAgent** | **PASS** (with a note) | Generates the full `OpportunityResponse` via Gemini. The only deterministic calculations are numeric trade‑setup values, which are permitted infrastructure logic. |
| **RankingAgent** | **FAIL** | Uses a reduced schema, discards most fields, and contains a fallback that fabricates investment data in Python. |
| **Top Opportunities Endpoint** | **FAIL** | Strips the rich opportunity object to a minimal subset before ranking, resulting in loss of Patch V1/V2 data. |
| **Overall Architecture** | **FAIL** | Because RankingAgent and the endpoint do not preserve the complete AI‑generated opportunity data and still contain deterministic investment logic (alignment score, breakout probability) in Python. |

---

## 8️⃣ Required Changes Before Production

1. **Rename / replace the ranking schema**
   * Remove the local `RankedOpportunity` / `RankedOpportunitiesResponse` definitions.
   * Import and use the **full** `RankedOpportunityResponse` model (inherits from `OpportunityResponse`).
2. **RankingAgent must accept a list of full `OpportunityResponse` objects**
   * Change the type hints to `List[OpportunityResponse]`.
   * Pass the *entire* JSON (all fields) to Gemini.
3. **Update the Gemini ranking prompt** (create `ranking_prompt.txt`) to ask Gemini to **rank the full objects** and to return **all original fields plus** `rank`, `ranking_explanation`, `why_ranked_here`.
4. **Remove the fallback block that fabricates investment fields**.
   * Instead, implement a retry policy (e.g., exponential back‑off) and, if all retries fail, raise a validation error that propagates to the API as a 500 response.
5. **Modify `/top‑opportunities`**
   * Stop building `opp_summaries` with a reduced field set.
   * Send the complete `analyses` list directly to `RankingAgent.rank`.
   * After ranking, return the enriched `RankedOpportunityResponse` objects unchanged (no field stripping).
6. **Eliminate deterministic alignment‑score logic** from `stock_service.py`.
   * Move alignment calculation to Gemini (e.g., include `timeframe_stats` in the scanner prompt and let Gemini output `alignment_score`).
7. **Remove deterministic breakout‑probability heuristic** (lines 168‑179) or shift it to Gemini.
8. **Add proper error handling / logging** for Gemini failures without generating fallback investment data.
9. **Add unit‑tests** to ensure that:
   * The output of `RankingAgent.rank` contains *all* fields defined in `OpportunityResponse` plus the three ranking‑only fields.
   * No fallback data is produced when Gemini responds with valid JSON.
10. **Create the missing `ranking_prompt.txt`** file under `backend/app/prompts/` with a clear instruction set for Gemini to rank the full objects.

Once the above changes are applied, a re‑run of this verification report should yield **PASS** for all components.

---

*Report generated on 2026‑06‑08 by Antigravity (AI‑assistant).*
