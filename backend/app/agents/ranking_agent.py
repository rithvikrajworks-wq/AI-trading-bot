import logging
import json
from typing import List, Dict, Any
from pydantic import BaseModel, Field

# Custom exception for ranking failures
class RankingAgentError(Exception):
    """Raised when RankingAgent cannot obtain a valid Gemini ranking after retries."""
    pass

from ..services.base_agent import BaseAgent
from ..schemas.ranked_opportunity_response import RankedOpportunityResponse


class RankedOpportunitiesResponse(BaseModel):
    items: List[RankedOpportunityResponse] = Field(..., description="List of ranked opportunities with full payload")


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
            
        # Attempt Gemini up to 3 times
        for attempt in range(3):
            try:
                response_obj = self.validate_response(json_part)
                return [item.model_dump() for item in response_obj.items]
            except Exception as e:
                self.logger.error(
                    "RankingAgent attempt %d failed to parse response: %s. Raw: %s",
                    attempt + 1,
                    e,
                    raw_response,
                )
                # Re‑generate response for next attempt
                raw_response = await self.generate_response(self.system_prompt, user_prompt)
                json_start = raw_response.find("{")
                json_part = raw_response[json_start:] if json_start != -1 else raw_response
        # All attempts exhausted – propagate error
        raise RankingAgentError(
            "RankingAgent could not obtain a valid Gemini ranking after 3 attempts."
        )
