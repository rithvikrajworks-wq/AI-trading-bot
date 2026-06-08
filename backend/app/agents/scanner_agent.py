import asyncio
import logging
import json
from typing import List, Dict, Any
from pydantic import BaseModel
from typing import Literal

from ..services.base_agent import BaseAgent
from ..services.stock_service import StockService
from ..schemas.opportunity_response import OpportunityResponse



class ScannerAgent(BaseAgent):
    """ScannerAgent that asks Gemini to identify and generate opportunity narratives."""

    def __init__(self):
        super().__init__(prompt_name="scanner_prompt", response_schema=OpportunityResponse)
        self.stock_service = StockService()
        self.logger = logging.getLogger(self.__class__.__name__)

    @property
    def system_prompt(self) -> str:
        return (
            "You are a professional investment scanner. Identify trading opportunities "
            "based strictly on the provided indicators and output clean JSON matching the schema."
        )

    def post_process(self, model_instance: BaseModel) -> OpportunityResponse:
        return model_instance

    async def scan_single(self, ticker: str) -> Dict[str, Any]:
        """Scan a single ticker and return opportunity details."""
        for attempt in range(3):
            try:
                # 1. Fetch full analysis (uses AnalysisAgent under the hood)
                analysis = await self.stock_service.analyze_ticker(ticker)
                
                # 2. Get raw indicators and query ScannerAgent prompt for the narrative
                raw_data = await self.stock_service.get_raw_analysis_data(ticker)
                indicators_json = json.dumps(raw_data, indent=2, sort_keys=True)
                
                await self.load_prompt()
                user_prompt = self.build_prompt(ticker=ticker, indicators_json=indicators_json)
                system_prompt = self.system_prompt
                
                raw_response = await self.generate_response(system_prompt, user_prompt)
                
                # Extract JSON block
                json_start = raw_response.find("{")
                if json_start != -1:
                    json_part = raw_response[json_start:]
                else:
                    json_part = raw_response
                    
                scanner_opp = self.validate_response(json_part)
                
                # 3. Merge opportunity narratives into the analysis response
                analysis["investment_thesis"] = scanner_opp.opportunity
                analysis["catalyst"] = scanner_opp.catalyst
                analysis["risks_list"] = [scanner_opp.risks]
                analysis["pros"] = [scanner_opp.opportunity, scanner_opp.why_interesting]
                analysis["cons"] = [scanner_opp.risks]
                
                return analysis
            except Exception as e:
                self.logger.warning("Attempt %d failed for ticker %s: %s", attempt + 1, ticker, e)
                if attempt == 2:
                    self.logger.error("ScannerAgent failed for ticker %s after 3 attempts", ticker)
                    raise e
                await asyncio.sleep(1)

    async def scan(self, tickers: List[str]) -> List[Dict[str, Any]]:
        """Scan multiple tickers concurrently."""
        tasks = [self.scan_single(t) for t in tickers]
        results = await asyncio.gather(*tasks)
        return results
