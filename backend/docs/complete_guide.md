# Complete Project Build Guide (AI Trading Bot)

## 1️⃣ Project Initialization

1. **Create a Git repository**
   ```bash
   mkdir Tradingbotmk1 && cd Tradingbotmk1
   git init
   ```
2. **Folder layout** – separate *backend* and *frontend*:
   ```
   Tradingbotmk1/
   ├─ backend/
   └─ frontend/
   ```
3. **Add a `.gitignore`** for Python (`__pycache__`, `.venv`, `*.pyc`) and Node (`node_modules`, `.next`, `dist`).

---

## 2️⃣ Backend – FastAPI Service

### 2.1 Environment & Dependencies
| Action | Command |
|--------|--------|
|Create a virtual env|`python -m venv .venv && source .venv/bin/activate` (Windows: `.venv\\Scripts\\activate`)|
|Install core packages|`pip install fastapi uvicorn[standard] pydantic pydantic-settings yfinance pandas pandas-ta python-jose[cryptography] sqlalchemy passlib[bcrypt]`|
|Freeze requirements|`pip freeze > requirements.txt`|

### 2.2 Project Skeleton
```
backend/
├─ app/
│  ├─ api/
│  │   └─ endpoints/
│  ├─ services/
│  ├─ schemas/
│  ├─ core/
│  ├─ auth/
│  ├─ agents/
│  └─ database.py
├─ .env
└─ main.py   (or app/main.py)
```

### 2.3 Core Configuration (`app/core/config.py`)
- Use **pydantic‑settings** to load `.env`.
- Define:
  - CORS origins, host/port, debug flag.
  - Scanner limits:
    ```python
    MAX_SCAN_STOCKS = 100
    MIN_CONFIDENCE_THRESHOLD = 70
    RISK_REWARD_THRESHOLD = 1.5
    SCAN_CONCURRENCY_LIMIT = 5
    ```
  - Universal stock universes for US and Indian markets (sample tickers).

### 2.4 Database Layer
- Use SQLite for rapid iteration (`memory.db`).
- Set up SQLAlchemy `Base`, engine, and `SessionLocal`.
- Create models such as `Portfolio`, `Position`, `TradeJournalEntry`, etc.
- Run migrations manually or with Alembic if needed.

### 2.5 Authentication
- Password hashing with **passlib** (`bcrypt`).
- JWT creation/verification using **python‑jose**.
- Provide dependency `get_current_user` for protected routes.
- Expose `/auth/login` and `/auth/register` endpoints.

### 2.6 Pydantic Schemas (`app/schemas/analysis.py`)
```python
class StockAnalysisResponse(BaseModel):
    ticker: str
    price: float
    signal: str
    confidence: int = Field(..., ge=0, le=100)
    rsi: float
    macd: str
    ema_trend: str
    pros: List[str]
    cons: List[str]
    entry_zone: Dict[str, float]
    stop_loss: float
    take_profit: Dict[str, float]
    holding_period: str
    risk_reward_ratio: float
    timeframes: Dict[str, Any]
    alignment_score: float
```
- `BatchAnalysisRequest` caps at 10 tickers.
- `BatchAnalysisResponse` contains `results` and `errors` lists.

### 2.7 Service Layer (`app/services/stock_service.py`)
1. **Data fetching** – `_fetch_history(ticker, interval)` runs `yfinance` inside `asyncio.to_thread`.
2. **Multi‑timeframe analysis** – fetch `1d`, `4h`, `1h` concurrently, compute per‑timeframe indicators (RSI, EMA‑20/‑50, MACD trend, momentum).
3. **Daily trade‑setup** – compute ATR, Bollinger Bands, support/resistance, volume MA, entry zone, stop‑loss, TP1/TP2, holding period.
4. **Risk‑Reward ratio** – `((TP1‑entry) / (entry‑stop))` with divide‑by‑zero guard.
5. **Alignment score** – average EMA‑trend bullishness weighted by RSI distance from 50 across timeframes.
6. **Return dict** – includes all core fields plus the new `risk_reward_ratio`, `timeframes`, and `alignment_score`.

### 2.8 API Endpoints (`app/api/endpoints/*.py`)
| Endpoint | File | Purpose | Highlights |
|----------|------|---------|------------|
|`GET /analyze-stock`|`analysis.py`|Single‑ticker analysis|Uses `StockService.analyze_ticker` then passes data to `AnalysisAgent` for AI‑generated commentary.|
|`POST /analyze-stocks`|`analysis.py`|Batch analysis|Normalizes tickers, caps at 10, deduplicates, runs `asyncio.gather`, returns `BatchAnalysisResponse`.|
|`GET /top-opportunities`|`top_opportunities.py`|Scanner|Scans universal stock lists, respects concurrency limit, filters by `MIN_CONFIDENCE_THRESHOLD` and `RISK_REWARD_THRESHOLD`, sorts by confidence.|
|`GET /health`|`health.py`|Health check|Simple `{status:"ok"}` response.|

### 2.9 Caching (optional)
- Simple in‑memory cache (`app.utils.cache`) keyed by ticker to avoid repeat yfinance calls within a short window.
- Cache‑hit logging for observability.

### 2.10 Logging & Observability
- Configure a structured logger (`logging.getLogger("app")`).
- Add request‑level logs, cache hits/misses, analysis duration, and error traces.

### 2.11 Testing
- **Unit tests** for `StockService` (multi‑timeframe, risk/reward, alignment). Use `pytest` + `pytest‑asyncio`.
- **Integration tests** for endpoints using FastAPI's `TestClient`.
- CI pipeline (GitHub Actions) runs lint (`ruff`), type‑check (`mypy`), and tests on every push.

### 2.12 Deployment
- Create a **Dockerfile**:
  ```Dockerfile
  FROM python:3.11-slim
  WORKDIR /app
  COPY backend/requirements.txt .
  RUN pip install --no-cache-dir -r requirements.txt
  COPY backend/. .
  CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
  ```
- Add a `docker-compose.yml` to spin up the API and a SQLite volume.
- Set `DEBUG=False` via environment variable for production.

---

## 3️⃣ Frontend – Next.js MVP

### 3.1 Scaffold
```bash
cd ../frontend
npx create-next-app@latest . --typescript --eslint --tailwind
```
- Keep Tailwind config simple; add a custom color palette for a premium look.
- Install `axios` for API calls.

### 3.2 Core Pages / Components
| Component | Purpose |
|-----------|---------|
|`Dashboard`|Container for the whole UI. |
|`StockSearchBar`|Input for ticker symbols, triggers `/analyze-stock` or batch endpoint. |
|`AnalysisCard`|Displays fields from `StockAnalysisResponse` (signal, confidence, RSI, MACD, EMA trend, pros, cons, entry zone, stop‑loss, TP, risk/reward, alignment score). |
|`TradingViewChart`|Embeds TradingView widget for the ticker. |
|`TopOpportunities`|Fetches `/top-opportunities` and renders a grid of `AnalysisCard`s. |

### 3.3 State Management
- Use React hooks (`useState`, `useEffect`).
- Simple context/provider for the watch‑list.
- Loading spinners (`react-spinners`) and error toast notifications.

### 3.4 API Layer (`src/utils/api.ts`)
```ts
import axios from "axios";
export const api = axios.create({ baseURL: process.env.NEXT_PUBLIC_API_URL });
export const fetchAnalysis = (ticker: string) => api.get(`/analyze-stock`, { params: { ticker } });
export const fetchBatch = (tickers: string[]) => api.post(`/analyze-stocks`, { tickers });
export const fetchTop = () => api.get(`/top-opportunities`);
```

### 3.5 Styling & Premium Look
- Use a dark‑mode friendly palette (e.g., HSL values). 
- Apply glassmorphism to cards: `backdrop-filter: blur(8px);` 
- Animate hover states with `transition` for elevation.
- Use Google Font **Inter** for modern typography.

### 3.6 Deploy
- Production build: `npm run build && npm start`.
- Deploy to Vercel or any Node‑compatible host.
- Set environment variable `NEXT_PUBLIC_API_URL` pointing to the FastAPI service.

---

## 4️⃣ Ongoing / Future Work
- **Scheduler**: `scanner_agent.py` to run periodic scans (cron or background task). Push updates via WebSocket or polling.
- **Risk Management**: add configurable minimum risk‑reward threshold per user.
- **User Profiles**: store watch‑lists and preferences in the DB.
- **Advanced AI**: integrate a LLM for richer natural‑language explanations.
- **Metrics & Alerts**: expose Prometheus metrics, add email/SMS alerts for high‑confidence signals.

---

*All steps above reflect the current state of the repository (backend already contains the multi‑timeframe logic, batch endpoint, top‑opportunities endpoint, and a markdown project overview). Continue from the “Testing” section onward to solidify quality, then polish the frontend MVP.*
