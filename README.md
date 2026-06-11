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

