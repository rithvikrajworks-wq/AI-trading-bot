# AI Trading Bot

A **real‑time AI‑enhanced stock analysis platform** built with:

- **Backend**: FastAPI + asyncio, yfinance, pandas‑ta, OpenAI chat integration.
- **Frontend**: Next.js 14, TypeScript, Tailwind CSS, TradingView charts, premium dark‑glass UI.
- **Features**:
  - Live ticker price streaming (polling → WebSocket future).
  - Top‑opportunity scanner with confidence scoring.
  - Persistent watchlist (localStorage, server‑side planned).
  - AI chat assistant that grounds responses in live technical analysis.
  - Market widgets (Fear & Greed, Movers, Heatmap, Economic Calendar – placeholders).

## How to run locally
```bash
# Backend
cd backend
python -m venv .venv && .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Frontend
cd ../frontend
npm install
# set backend URL (edit .env.local) – e.g. NEXT_PUBLIC_API_URL=http://<LAN_IP>:8000
npm run dev -- --hostname 0.0.0.0 --port 3001
```

Open `http://localhost:3001` (or `http://<LAN_IP>:3001` from another device) to see the dashboard.

## Repository structure
```
Tradingbotmk1/
├─ backend/   # FastAPI service
├─ frontend/  # Next.js UI
├─ .gitignore
└─ README.md
```

---

*Made with ❤️ by the Antigravity team.*






# AI Stock Analysis Platform - Backend Foundation

Welcome to the backend foundation for your AI-powered stock analysis platform. This service is built with **FastAPI** (Python) and uses quantitative finance libraries like **yfinance** and **pandas-ta** to fetch market data and calculate indicators.

---

## 📂 Folder & File Architecture

The backend code is organized into a modular, production-style, clean architecture structure.

```
backend/
├── app/
│   ├── __init__.py             # Makes the app directory a Python package
│   ├── main.py                 # Application entry point (initializes FastAPI, CORS, router)
│   ├── api/
│   │   ├── __init__.py         # Makes api directory a package
│   │   ├── router.py           # Main routing register (combines all sub-routers)
│   │   └── endpoints/
│   │       ├── __init__.py     # Makes endpoints directory a package
│   │       ├── health.py       # Health check endpoints for infrastructure monitoring
│   │       └── analysis.py     # Endpoints related to stock data and analysis
│   ├── core/
│   │   ├── __init__.py         # Makes core directory a package
│   │   └── config.py           # Configuration management (Pydantic settings)
│   ├── schemas/
│   │   ├── __init__.py         # Makes schemas directory a package
│   │   └── analysis.py         # Request and response models (data contracts/Pydantic)
│   └── services/
│       ├── __init__.py         # Makes services directory a package
│       └── stock_service.py    # Core business logic (yfinance fetching & technical calculations)
├── requirements.txt            # Python dependencies lists
├── .env                        # Active environment configurations (not tracked in Git)
├── .env.example                # Example template for environment configurations
└── README.md                   # System documentation (you are here)
```

### Explanation of Folders
* **`app/main.py`**: The entrypoint of the FastAPI app. Configures CORS (for Next.js frontend connection) and registers routers.
* **`app/api/`**: Handles incoming HTTP requests. Contains routers and endpoint definitions. It separates the routes themselves from business logic.
* **`app/core/`**: Houses global configurations, security settings, database initializations, etc. It reads configurations from the environment and `.env` files via Pydantic.
* **`app/schemas/`**: Stores data schemas (Pydantic models) defining the input validations and output shapes of API responses.
* **`app/services/`**: The core "brain" of the application containing the business logic. It does calculations, calls third-party APIs (like Yahoo Finance), and operates independently of FastAPI's request/response layer. This decoupling keeps the code highly testable.

---

## 🛠️ Installation & Setup

Follow these steps to run the backend on your Windows machine:

### 1. Prerequisites
Ensure you have **Python 3.9+** installed on your system.

### 2. Set Up a Virtual Environment
A virtual environment isolates this project's dependencies from your global Python installation.

Open a terminal (e.g., PowerShell) in the `backend/` directory and run:
```powershell
python -m venv venv
```

### 3. Activate the Virtual Environment
Activate the environment to start using the isolated environment's Python and pip:

```powershell
.\venv\Scripts\activate
```
*(Your terminal prompt should now be prefixed with `(venv)`)*

### 4. Install Dependencies
Install all required libraries specified in `requirements.txt`:
```powershell
pip install -r requirements.txt
```

---

## 🚀 Running the Server

To start the FastAPI development server, run:
```powershell
uvicorn app.main:app --reload
```

* **`app.main:app`**: Refers to the `app` instance inside `app/main.py`.
* **`--reload`**: Enables auto-reload, which restarts the server automatically whenever you save code changes.

By default, the server runs on: **`http://127.0.0.1:8000`**

---

## 🧪 Testing the Endpoints

FastAPI automatically generates interactive Swagger documentation, making it incredibly easy to test endpoints.

1. **Interactive UI Docs**: Open your browser and navigate to **[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)**. Here you can click on any route, click "Try it out", fill in parameters, and run it.
2. **Health Check Route**:
   * **URL**: `http://127.0.0.1:8000/health`
   * **Method**: `GET`
   * **Expected Response**:
     ```json
     {
       "status": "healthy",
       "service": "Stock Analysis API"
     }
     ```
3. **Stock Analysis Route**:
   * **URL**: `http://127.0.0.1:8000/analyze-stock?ticker=NVDA`
   * **Method**: `GET`
   * **Expected Response**:
     ```json
     {
       "ticker": "NVDA",
       "price": 924.21,
       "signal": "BUY",
       "confidence": 84,
       "rsi": 38,
       "macd": "bullish",
       "ema_trend": "bullish",
       "pros": [
         "Bullish long-term trend (20 EMA above 50 EMA)",
         "Bullish MACD crossover (MACD line above signal line)"
       ],
       "cons": [
         "Short-term momentum is negative (Price is below 20 EMA)"
       ]
     }
     ```
4. **Batch Stock Analysis Route**:
   * **URL**: `http://127.0.0.1:8000/analyze-stocks`
   * **Method**: `POST`
   * **Request Body**:
     ```json
     {
       "tickers": ["NVDA", "AAPL", "INVALID_TICKER"]
     }
     ```
   * **Expected Response**:
     ```json
     {
       "results": [
         {
           "ticker": "NVDA",
           "price": 924.21,
           "signal": "BUY",
           "confidence": 84,
           "rsi": 38.0,
           "macd": "bullish",
           "ema_trend": "bullish",
           "pros": [
             "Bullish long-term trend (20 EMA above 50 EMA)",
             "Bullish MACD crossover (MACD line above signal line)"
           ],
           "cons": [
             "Short-term momentum is negative (Price is below 20 EMA)"
           ]
         },
         {
           "ticker": "AAPL",
           "price": 182.52,
           "signal": "HOLD",
           "confidence": 90,
           "rsi": 49.5,
           "macd": "bearish",
           "ema_trend": "bullish",
           "pros": [
             "Bullish long-term trend (20 EMA above 50 EMA)"
           ],
           "cons": [
             "Bearish MACD crossover (MACD line below signal line)"
           ]
         }
       ],
       "errors": [
         {
           "ticker": "INVALID_TICKER",
           "error": "No historical data found for ticker 'INVALID_TICKER'. The ticker may be invalid or delisted."
         }
       ]
     }
     ```



---

## 🧠 System Architecture & Data Flow

### 1. Request Lifecycle
When a request is made to `GET /analyze-stock?ticker=NVDA`:
1. **Routing**: FastAPI intercepts the request, validates that the query parameter `ticker` is a string (lengths 1 to 10), and forwards it to the route function in `app/api/endpoints/analysis.py`.
2. **Service Delegation**: The route function calls `StockService().analyze_ticker(ticker)`.
3. **Fetching Data**: `StockService` fetches historical daily data for `NVDA` from Yahoo Finance using `yfinance`. This blocking network call is run asynchronously using `asyncio.to_thread` to maintain a non-blocking server loop.
4. **Calculations**: Using `pandas-ta`, the service calculates the Relative Strength Index (RSI), Exponential Moving Averages (EMA 20 & 50), and Moving Average Convergence Divergence (MACD).
5. **Logic Engine**: The indicators are evaluated through a quantitative scoring algorithm to decide the `BUY/SELL/HOLD` recommendation, calculate a confidence score, and build dynamic pros/cons lists.
6. **Serialization & Response**: The resulting Python dictionary is verified against the Pydantic schema `StockAnalysisResponse`, converted to JSON, and returned to the client.

### 2. Future AI Chat Integration
When adding the AI Chatbot feature to discuss stocks:
1. **New API endpoint**: We will add a router in `app/api/endpoints/chat.py` (e.g. `POST /chat`).
2. **New Schema**: We will define request schemas for chat inputs (user question, current stock context) and response schemas.
3. **New AI Service**: We will create `app/services/ai_service.py` to handle LLM calls (e.g., Gemini API, OpenAI API).
4. **Context Injection**: When a user chats about NVDA, the frontend/backend can query `StockService` first to get the latest metrics, inject those metrics into the LLM prompt, and stream the LLM response back to the user. This ensures the AI is grounded in real data and doesn't hallucinate metrics.
