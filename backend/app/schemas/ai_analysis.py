from pydantic import BaseModel

class AIAnalysisResponse(BaseModel):
    ticker: str
    analysis: str
    confidence: float | None = None  # optional confidence score from AI if desired
