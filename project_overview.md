# Project Overview

**Repository:** `C:/Users/Dell/Tradingbotmk1`

## Architecture
- **FastAPI** backend providing async endpoints.
- **Service layer** (`app/services/*`) performs technical analysis using **yfinance**, **pandas**, **pandas‑ta**.
- **Pydantic schemas** (`app/schemas/analysis.py`) define request/response models and include multi‑timeframe data, risk/reward ratio, and alignment score.
- **Config** (`app/core/config.py`) holds CORS, scanner limits, universal stock lists for US and Indian markets, and risk‑reward threshold.
- **Endpoints** (`app/api/endpoints/*`):
  - `GET /analyze-stock` – single ticker analysis.
  - `POST /analyze-stocks` – batch analysis (max 10 tickers, deduplication, concurrency via `asyncio.gather`).
  - `GET /top‑opportunities` – scans configured universes, returns high‑confidence setups filtered by confidence and risk‑reward ratio.
  - `GET /health` – simple health check.
- **Agents** (`app/agents/*`) handle background tasks such as memory summarization and scanning.
- **Auth** (`app/auth/jwt_handler.py`) provides JWT generation/verification for protected routes.
- **Database** (`memory.db`, SQLAlchemy models) stores portfolio/position data.

## Core Technologies & Libraries
- **FastAPI** – async web framework.
- **Uvicorn** – ASGI server.
- **asyncio**, `asyncio.to_thread` – non‑blocking I/O for yfinance calls.
- **yfinance** – market data retrieval.
- **pandas**, **pandas‑ta** – technical indicator calculations (RSI, EMA, MACD, ATR, Bollinger Bands, support/resistance).
- **pydantic**, **pydantic‑settings** – data validation and config loading.
- **SQLAlchemy** (SQLite) – persistence layer.
- **python‑jwt** – token handling.
- **Logging** – structured endpoint logs.
- **Frontend (MVP)** – built with **Next.js**, **React**, **TypeScript**, **Tailwind CSS** (connects to the FastAPI backend).

## Important Endpoints Detail
```
GET  /analyze-stock?ticker=NVDA          → StockAnalysisResponse
POST /analyze-stocks                     → BatchAnalysisResponse (results + errors)
GET  /top-opportunities                  → List[StockAnalysisResponse] (high‑quality setups)
GET  /health                             → {status: "ok"}
```

## Data Models (key fields)
- `StockAnalysisResponse` includes ticker, price, signal, confidence, RSI, MACD, EMA trend, pros/cons, entry zone, stop‑loss, take‑profit, holding period, **risk_reward_ratio**, **timeframes** (1D/4H/1H indicator dicts), **alignment_score**.
- `BatchAnalysisRequest` caps at 10 tickers, normalizes to uppercase, deduplicates while preserving order.
- `BatchAnalysisResponse` separates successful `results` from `errors`.

## Scanner Configuration (`app/core/config.py`)
- `MAX_SCAN_STOCKS = 100`
- `MIN_CONFIDENCE_THRESHOLD = 70`
- `RISK_REWARD_THRESHOLD = 1.5`
- `SCAN_CONCURRENCY_LIMIT = 5`
- `UNIVERSAL_STOCKS` defines US and India stock universes (NASDAQ‑100, S&P‑500, NIFTY‑50, etc.).

---
*All code lives under `C:/Users/Dell/Tradingbotmk1/backend/app`.*
