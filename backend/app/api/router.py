from fastapi import APIRouter, Depends
from app.api.endpoints import health, analysis, top_opportunities, chat, market_status, live_price, ai_analysis
from app.auth.dependencies import get_current_user

api_router = APIRouter(dependencies=[Depends(get_current_user)])

# Register endpoint routers
# Putting tags helps group them beautifully in the FastAPI auto-generated /docs interactive interface
api_router.include_router(health.router, tags=["System"])
api_router.include_router(analysis.router, tags=["Stock Analysis"])
api_router.include_router(top_opportunities.router, tags=["Top Opportunities"])
api_router.include_router(chat.router, tags=["Chat"])
api_router.include_router(market_status.router, tags=["Market Status"])
api_router.include_router(live_price.router, tags=["Live Price"])
api_router.include_router(ai_analysis.router, tags=["AI Analysis"])
