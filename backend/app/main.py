from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from app.core.config import settings
from app.api.router import api_router

# Initialize the FastAPI Application
app = FastAPI(
    title=settings.PROJECT_NAME,
    description=(
        "FastAPI Backend for the AI-powered Stock Analysis Platform. "
        "Calculates RSI, MACD, and EMA 20/50, and generates trade recommendations."
    ),
    version="1.0.0",
    debug=settings.DEBUG,
)

# Configure CORS Middleware
# This is crucial so that the future Next.js frontend running on a different port (e.g. 3000) can make API calls.
if settings.ALLOWED_ORIGINS:
    origins = settings.ALLOWED_ORIGINS
    if isinstance(origins, str):
        origins = [origins]
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Register the main API router
app.include_router(api_router)

@app.get("/", include_in_schema=False)
async def root_redirect():
    """
    Redirect the root index URL to FastAPI's interactive /docs.
    """
    return RedirectResponse(url="/docs")
