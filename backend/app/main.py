# backend/app/main.py

"""FastAPI application entry point.
Includes CORS, logging, auth router, and startup DB migrations.
"""

from pathlib import Path
from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(__file__).resolve().parents[1] / ".env")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
import aiosqlite
import logging

from app.settings import settings
from app.api.router import api_router
from app.auth.auth import router as auth_router

# Configure logger
logger = logging.getLogger("tradingbot")
logger.setLevel(logging.INFO)

# Initialize FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    description=(
        "FastAPI Backend for the AI-powered Stock Analysis Platform. "
        "Calculates RSI, MACD, and EMA 20/50, and generates trade recommendations."
    ),
    version="1.0.0",
    debug=settings.DEBUG,
)

# CORS configuration
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

# Register routers
app.include_router(api_router)
app.include_router(auth_router)

# Startup event – create tables if they don't exist
@app.on_event("startup")
async def create_tables() -> None:
    """Create all required database tables at application startup.
    This includes SQLAlchemy ORM tables and raw SQLite tables used by the app.
    Also seeds an admin user if not present.
    """
    # SQLAlchemy tables
    from .database import Base, engine
    from .models.analysis_record import AnalysisRecord
    Base.metadata.create_all(bind=engine)

    # SQLite tables
    async with aiosqlite.connect(settings.MEMORY_DB_PATH) as db:
        await db.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                hashed_password TEXT NOT NULL,
                created_at REAL NOT NULL
            );
            CREATE TABLE IF NOT EXISTS episodic_memory (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp REAL NOT NULL,
                metadata TEXT,
                embedding BLOB
            );
            CREATE TABLE IF NOT EXISTS memory_summaries (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                summary TEXT NOT NULL,
                created_at REAL NOT NULL
            );
            CREATE TABLE IF NOT EXISTS user_settings (
                user_id TEXT PRIMARY KEY,
                memory_enabled INTEGER DEFAULT 1,
                max_memories INTEGER DEFAULT 1000,
                ai_cost_saver INTEGER DEFAULT 1
            );
            CREATE TABLE IF NOT EXISTS user_profiles (
                user_id TEXT PRIMARY KEY,
                risk_tolerance TEXT,
                strategy_style TEXT,
                preferred_sectors TEXT,
                favorite_tickers TEXT,
                experience_level TEXT,
                updated_at REAL
            );
            CREATE TABLE IF NOT EXISTS ai_usage (
                id TEXT PRIMARY KEY,
                user_id TEXT,
                endpoint TEXT,
                provider TEXT,
                tokens INTEGER,
                latency REAL,
                success INTEGER,
                created_at REAL
            );
            """
        )
        # Seed the Rithvik(admin) user account if it doesn't exist
        from app.auth.password_utils import hash_password
        import uuid
        import time
        email = "Rithvik(admin)"
        cursor = await db.execute("SELECT id FROM users WHERE email = ?", (email,))
        row = await cursor.fetchone()
        await cursor.close()
        if not row:
            user_id = uuid.uuid4().hex
            hashed_password = hash_password("lets do this!!!")
            created_at = time.time()
            await db.execute(
                "INSERT INTO users (id, email, hashed_password, created_at) VALUES (?, ?, ?, ?)",
                (user_id, email, hashed_password, created_at)
            )
            await db.commit()
            logger.info("Successfully seeded user: Rithvik(admin)")
        await db.commit()
    logger.info("Database tables ensured at startup")

# Root redirect to /docs
@app.get("/", include_in_schema=False)
async def root_redirect():
    """Redirect the root URL to FastAPI's interactive docs."""
    return RedirectResponse(url="/docs")
