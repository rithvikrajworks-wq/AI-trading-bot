from fastapi import APIRouter, HTTPException
from app.schemas.ai_analysis import AIAnalysisResponse
from app.services.stock_service import StockService
from app.services.ai_provider import OpenAIProvider

router = APIRouter()

stock_service = StockService()
ai_provider = OpenAIProvider()

@router.get("/ai-analysis/{ticker}", response_model=AIAnalysisResponse)
async def ai_analysis_endpoint(ticker: str) -> AIAnalysisResponse:
    """Generate an AI‑driven natural‑language analysis for a ticker.
    The endpoint:
    1. Retrieves technical analysis data via StockService.
    2. Builds a concise system prompt that tells the LLM to act as a professional trading copilot.
    3. Sends the data as user‑prompt context to OpenAI.
    4. Returns the generated text.
    """
    # 1️⃣ Get live technical analysis (cached inside StockService)
    try:
        analysis = await stock_service.analyze_ticker(ticker)
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Failed to analyse ticker") from exc

    # 2️⃣ Build prompts
    system_prompt = (
        "You are a professional, analytical AI trading copilot. "
        "Provide a concise, data‑driven summary for the given ticker, "
        "including key technical indicators, confidence, risks, and actionable insight. "
        "Never guarantee profit or use hype language."
    )
    # Convert analysis dict to a readable bullet list
    bullets = []
    for key, value in analysis.items():
        bullets.append(f"- {key}: {value}")
    user_prompt = "\n".join(bullets)

    # 3️⃣ Call OpenAI provider
    result = await ai_provider.chat_completion(system_prompt, user_prompt, history=[])

    # 4️⃣ Return response
    return AIAnalysisResponse(ticker=ticker.upper(), analysis=result)
