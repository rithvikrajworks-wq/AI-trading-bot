from fastapi import APIRouter, HTTPException
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.chat_service import ChatService

router = APIRouter()

chat_service = ChatService()

@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest) -> ChatResponse:
    """AI‑driven stock discussion endpoint.
    Grounds the response in live analysis from ``StockService`` and returns a structured
    summary of the analysis and risk factors.
    """
    try:
        response = await chat_service.chat(request)
        return response
    except Exception as exc:
        # Unexpected errors are returned as 500 – avoid leaking internal details
        raise HTTPException(status_code=500, detail="Chat processing failed") from exc
