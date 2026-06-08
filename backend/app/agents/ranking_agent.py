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
