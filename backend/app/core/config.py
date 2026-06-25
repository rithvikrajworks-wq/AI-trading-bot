import os
from typing import List, Union, Dict
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Stock Analysis API"
    PORT: int = 8000
    HOST: str = "0.0.0.0"  # Bind to all interfaces for LAN access
    DEBUG: bool = True
    ENVIRONMENT: str = "development"
    
    # CORS Origins: comma separated in env, parsed to list
    ALLOWED_ORIGINS: Union[List[str], str] = ["*"]  # Allow any origin (both localhost and remote devices)

    # ==== New scanner configuration ====
    # Maximum number of stocks to scan in a single request (pre‑cap to avoid overload)
    # Maximum number of stocks to scan in a single request (pre‑cap to avoid overload)
    # Token safety cap: do not increase without user confirmation.
    MAX_SCAN_STOCKS: int = 5
    # Minimum confidence score required for a setup to be considered "high quality"
    MIN_CONFIDENCE_THRESHOLD: int = 60
    # Minimum acceptable risk/reward ratio for a setup to be considered viable
    RISK_REWARD_THRESHOLD: float = 1.5
    # Concurrency limit for async scanning (semaphore)
    SCAN_CONCURRENCY_LIMIT: int = 5
    # ==== ATR and volatility settings ====
    ATR_PERIOD: int = 14
    STOP_LOSS_BUY_MULTIPLIER: float = 1.5
    STOP_LOSS_SELL_MULTIPLIER: float = 1.5
    TAKE_PROFIT_BUY_MULTIPLIER: float = 2.0
    TAKE_PROFIT_SELL_MULTIPLIER: float = 2.0
    VOLATILITY_HIGH_RATIO: float = 0.02  # 2% of price
    VOLATILITY_MEDIUM_RATIO: float = 0.01  # 1% of price
    # Define stock universes – groups of tickers to scan per market
    UNIVERSAL_STOCKS: Dict[str, List[str]] = {
        "US": [
            # NASDAQ 100 (sample subset)
            "AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META", "ADBE", "TSLA",
            # S&P 500 (sample subset)
            "JPM", "BAC", "XOM", "V", "UNH",
            # Semiconductor focused
            "AMD", "INTC", "QCOM",
            # AI‑related (sample)
            "GOOG", "IBM", "CRM"
        ],
        "India": [
            # NIFTY 50 (sample subset)
            "RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS",
            # BANKNIFTY (sample)
            "KOTAKBANK.NS", "AXISBANK.NS",
            # IT sector
            "WIPRO.NS", "HCLTECH.NS",
            # High‑volume NSE stocks
            "SBIN.NS", "ITC.NS"
        ]
    }
    # ----- Caching configuration -----
    CACHE_ENABLED: bool = bool(os.getenv("CACHE_ENABLED", "true"))
    CACHE_TTL_SECONDS: int = int(os.getenv("CACHE_TTL_SECONDS", "600"))  # global default 10 min
    ANALYSIS_CACHE_TTL: int = int(os.getenv("ANALYSIS_CACHE_TTL", "300"))  # seconds for analysis cache TTL
    BACKTEST_CACHE_TTL: int = int(os.getenv("BACKTEST_CACHE_TTL", "1800"))  # 30 min for backtest
    # -----------------------------------
    
    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    # Tell pydantic settings to load from .env file
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
