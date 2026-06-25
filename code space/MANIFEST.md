# Portfolio Feature – MANIFEST.md

## Files generated

| Generated file | Place it at |
|---|---|
| `portfolio_schemas.py` | `Tradingbotmk1/backend/app/schemas/portfolio.py` |
| `portfolio_endpoints.py` | `Tradingbotmk1/backend/app/api/endpoints/portfolio.py` |
| `portfolioApi.ts` | `Tradingbotmk1/frontend/src/utils/portfolioApi.ts` |
| `PortfolioManager.tsx` | `Tradingbotmk1/frontend/src/components/PortfolioManager.tsx` |

---

## backend/app/main.py – router registration

Add these two lines to your existing `main.py`.  
Find the block where you include other routers and add:

```python
# At the top of main.py, with your other imports:
from app.api.endpoints.portfolio import router as portfolio_router

# Inside your create_app() function or at module level,
# after you create `app = FastAPI(...)`:
app.include_router(portfolio_router)
```

That's it – no prefix is needed here because the router already declares
`prefix="/portfolio"` internally.

---

## Endpoints summary

| Method | Path | What it does |
|---|---|---|
| GET | `/portfolio/` | List all holdings |
| POST | `/portfolio/` | Add a new holding |
| PATCH | `/portfolio/{ticker}` | Edit a holding by ticker |
| DELETE | `/portfolio/{ticker}` | Remove a holding |
| GET | `/portfolio/summary` | Aggregate stats (total invested, P/L, etc.) |

---

## Frontend usage

Drop `<PortfolioManager />` anywhere in your dashboard:

```tsx
import PortfolioManager from "@/components/PortfolioManager";

export default function DashboardPage() {
  return (
    <main>
      {/* ...your existing dashboard cards... */}
      <PortfolioManager />
    </main>
  );
}
```

---

## Environment variable

The frontend reads `NEXT_PUBLIC_API_URL` for the backend base URL.  
If not set it falls back to `http://localhost:8000`.

Add to `Tradingbotmk1/frontend/.env.local`:
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## Database

The endpoint file auto-creates a `portfolio` table in `tradingbot.db`
on first run using `Base.metadata.create_all(bind=engine)`.

If your project already has a central SQLAlchemy `engine` / `Base`,
you can remove the `engine`, `SessionLocal`, `Base`, and `get_db`
blocks from `portfolio.py` and import them from your existing db module instead.

---

## What is computed vs stored

| Field | Stored in DB | Computed on-the-fly |
|---|---|---|
| `ticker`, `market`, `quantity`, `average_cost`, `current_price`, `status`, `notes` | ✅ | – |
| `invested_amount` = qty × avg_cost | – | ✅ |
| `current_value` = qty × current_price | – | ✅ |
| `profit_loss` = current_value − invested_amount | – | ✅ |
| `profit_loss_pct` = P/L ÷ invested_amount × 100 | – | ✅ |

All math is deterministic. No AI, no external price feeds.
