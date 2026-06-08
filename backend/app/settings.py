# backend/app/settings.py

"""Application settings loaded from .env.
All environment variables are accessed via this module. Uses pydantic
BaseSettings for type validation and defaults.
"""

from pydantic import Field
from pydantic_settings import BaseSettings
import uuid

class Settings(BaseSettings):
    # Core API configuration
    HOST: str = Field("0.0.0.0", description="FastAPI host")
    PORT: int = Field(8000, description="FastAPI port")
    ALLOWED_ORIGINS: list[str] = Field(["*"], description="CORS origins")
    DEBUG: bool = Field(False, description="FastAPI debug mode")
    PROJECT_NAME: str = Field("AI Trading Platform", description="Project name")

    # AI provider configuration
    AI_PROVIDER: str = Field("gemini", description="gemini or openai")
    GEMINI_API_KEY: str | None = Field(default=None, validation_alias="GOOGLE_API_KEY")
    OPENAI_API_KEY: str | None = Field(default=None, validation_alias="OPENAI_API_KEY")
    AI_MODEL: str = Field("gemini-1.5-flash", description="Default LLM model name")
    FALLBACK_AI_PROVIDERS: list[str] = Field(default_factory=lambda: ["openai"], description="Fallback providers in priority order")

    # Paths for persistence
    MEMORY_DB_PATH: str = Field("./memory.db", description="SQLite memory DB file")
    VECTOR_DB_PATH: str = Field("./faiss_index", description="Vector DB directory")

    # Cache TTLs (seconds)
    ANALYSIS_CACHE_TTL: int = Field(300, description="Cache TTL for analysis endpoint")
    SCANNER_CACHE_TTL: int = Field(180, description="Cache TTL for top‑opportunities endpoint")
    CHAT_MEMORY_LIMIT: int = Field(10, description="Number of recent chat turns to keep")

    # Analysis persistence settings
    ANALYSIS_RETENTION_DAYS: int = Field(30, description="Days to retain analysis records")
    ANALYSIS_RATE_LIMIT_PER_MINUTE: int = Field(5, description="Maximum Gemini calls per minute for analysis")

    # Concurrency limits
    MAX_CONCURRENT_LLM_CALLS: int = Field(5, description="Maximum concurrent LLM calls")

    # JWT configuration
    JWT_SECRET: str = Field(default_factory=lambda: uuid.uuid4().hex, env="JWT_SECRET")
    JWT_ALGORITHM: str = Field("HS256", env="JWT_ALGORITHM")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(60, env="ACCESS_TOKEN_EXPIRE_MINUTES")

    # Prompt versioning
    ANALYSIS_PROMPT_VERSION: str = Field("v1", env="ANALYSIS_PROMPT_VERSION")
    CHAT_PROMPT_VERSION: str = Field("v1", env="CHAT_PROMPT_VERSION")
    SCANNER_PROMPT_VERSION: str = Field("v1", env="SCANNER_PROMPT_VERSION")

    # Financial disclaimer
    FINANCIAL_DISCLAIMER: str = Field(
        "AI-generated analysis. Not financial advice. Always do your own research before making trading decisions.",
        env="FINANCIAL_DISCLAIMER",
    )

    # Cost protection settings
    ENABLE_COST_PROTECTION: bool = Field(True, env="ENABLE_COST_PROTECTION")
    MAX_DAILY_AI_REQUESTS: int = Field(500, env="MAX_DAILY_AI_REQUESTS")
    MAX_MONTHLY_AI_REQUESTS: int = Field(10000, env="MAX_MONTHLY_AI_REQUESTS")
    MAX_CONTEXT_TOKENS: int = Field(12000, env="MAX_CONTEXT_TOKENS")

    # Analytics retention (days)
    AI_USAGE_RETENTION_DAYS: int = Field(90, env="AI_USAGE_RETENTION_DAYS")

    # Feature toggles
    ENABLE_MEMORY: bool = Field(True, env="ENABLE_MEMORY")
    ENABLE_ANALYTICS: bool = Field(True, env="ENABLE_ANALYTICS")
    ENABLE_SUMMARIZATION: bool = Field(True, env="ENABLE_SUMMARIZATION")
    ENABLE_PROVIDER_FAILOVER: bool = Field(True, env="ENABLE_PROVIDER_FAILOVER")
    ENABLE_COST_GUARD: bool = Field(True, env="ENABLE_COST_GUARD")

    # Timeout settings (seconds)
    PROVIDER_TIMEOUT: float = Field(10.0, description="Timeout for LLM generation calls")
    EMBEDDING_TIMEOUT: float = Field(5.0, description="Timeout for embedding calls")
    FAISS_TIMEOUT: float = Field(3.0, description="Timeout for FAISS similarity searches")
    DB_TIMEOUT: float = Field(5.0, description="Timeout for DB operations")

    # Memory limits
    MAX_MEMORY_ENTRIES_PER_USER: int = Field(1000, description="Hard cap on episodic memory rows per user")
    MAX_SEMANTIC_RETRIEVAL: int = Field(5, description="Maximum number of FAISS results to return")
    MAX_SUMMARY_COUNT_PER_USER: int = Field(20, description="Maximum stored summary entries per user")

    # Circuit breaker settings
    CIRCUIT_BREAKER_COOLDOWN_MINUTES: int = Field(15, description="Cooldown period after provider is marked unhealthy")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

# Singleton instance
settings = Settings()
