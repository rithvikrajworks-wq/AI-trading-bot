# Remaining Tasks (2026-06-08 16:31)

## Backend
- Unit tests for multi‑timeframe logic, risk/reward ratio, alignment score.
- Integration tests for `/analyze-stocks` and `/top-opportunities` (confidence & risk‑reward filtering).
- Pagination / limit handling for `/top‑opportunities`.
- Optional cache / rate‑limit for repeated ticker requests.
- Enhanced error handling for yfinance (invalid ticker → 400).
- Update OpenAPI docs to include `timeframes` and `alignment_score`.
- CI/CD pipeline (GitHub Actions) for lint, tests, and frontend build.

## Auth & Security
- Enforce JWT authentication on protected routes.
- Add production CORS configuration.

## Frontend MVP
- Show `timeframes` and `alignment_score` on analysis cards.
- Add loading spinners / skeleton UI for batch requests.
- Implement paginated or infinite‑scroll UI for Top Opportunities.
- Persist user watch‑list (local storage or backend).
- Mobile‑responsive design tweaks (Tailwind breakpoints).
- Friendly error UI with fallback/mock data.

## Scanner Agent
- Schedule `scanner_agent.py` (cron / background task) and push updates to UI (WebSocket or polling).
- Add detailed logging for scan runs.

## Documentation
- Expand README with local run instructions for backend & frontend.
- Document environment variables (`.env.example`).
- Provide Postman/OpenAPI collection.

## Deployment
- Dockerize backend (Dockerfile, docker‑compose.yml).
- Production config: disable DEBUG, set proper host/port.

## Misc / Polish
- Run static analysis (`ruff`, `mypy`) for type safety.
- Keep `project_overview.md` up‑to‑date as features evolve.
- Ongoing maintenance tasks.
