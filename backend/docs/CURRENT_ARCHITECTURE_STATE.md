# CURRENT_ARCHITECTURE_STATE

## 1️⃣ Database Models
| Model | Purpose | Status |
|-------|---------|--------|
| **AnalysisRecord** (`analysis_record.py`) | Stores AI‑generated analysis text, structured Gemini JSON output and extracted metadata (signal, confidence, risk level). | ✅ Complete – actively used by `analysis_repo.save_analysis` and API endpoints. |
| **AttributionRecord** (`attribution_record.py`) | Links analysis, thesis, portfolio positions, and trade‑journal entries for attribution tracking. | ❓ Partial – model defined but not yet referenced in current code paths. |
| **InvestorProfile** (`investor_profile.py`) | Captures user‑level preferences, risk tolerance, style, and other profile data. | ❓ Partial – model exists; no service/repo currently manipulates it. |
| **PortfolioPosition** (`portfolio_position.py`) | Represents a user’s position in a ticker (quantity, cost, status, notes, etc.). | ✅ Complete – used by `portfolio_repo` for CRUD operations. |
| **PositionOutcome** (`position_outcome.py`) | Records outcome of a position (WINNER/LOSER/NEUTRAL) with returns and holding period. | ❓ Partial – defined but not consumed yet. |
| **ThesisRecord** (`thesis_record.py`) | Stores AI‑generated thesis narratives per position with versioning and status. | ❓ Partial – model defined; no repository/service yet. |
| **ThesisReviewRecord** (`thesis_review_record.py`) | Holds review status and confidence for thesis updates. | ❓ Partial – defined but not integrated. |
| **TradeJournalEntry** (`trade_journal_entry.py`) | Logs individual trade actions (BUY/SELL/HOLD) with execution details and links to analysis/thesis. | ❓ Partial – model exists; not yet wired into workflow. |

## 2️⃣ Repositories
| Repository | Served Model(s) | CRUD Methods |
|-----------|----------------|--------------|
| **analysis_repo.py** | `AnalysisRecord` | `save_analysis`, `get_latest_analysis`, `purge_old_records`, `get_recent_analyses`, `get_analyses_by_signal`, `get_analyses_by_date_range` |
| **portfolio_repo.py** | `PortfolioPosition` | `add_position`, `update_position`, `remove_position`, `get_position`, `get_all_positions`, `get_watchlist` |

## 3️⃣ Memory Layer (`MemoryAgent`)
| Helper Method | Description | Supported Context Types |
|--------------|-------------|------------------------|
| `store_message(user_id, role, content)` | Scores importance, filters prompt‑injection, stores text in `memory_store`; embeds high‑importance messages in vector store. | **analyses** (via later retrieval), **trade journal** (if stored as user messages), others indirectly via stored content. |
| `retrieve_relevant(user_id, query)` | Embeds query, searches `vector_store`, returns matching metadata entries. | All stored contexts (currently only messages stored via `store_message`). |
| `get_latest_analysis_context(ticker)` | Loads most recent `AnalysisRecord` for a ticker and returns a short formatted string. | **analyses** |
| `get_recent_analysis_context(ticker, limit=5)` | Returns formatted block of up to `limit` recent analyses for a ticker. | **analyses** |
| `get_analysis_context(ticker)` | Wrapper that calls `get_recent_analysis_context`. | **analyses** |

*The memory layer currently does **not** expose explicit helpers for thesis, portfolio, trade‑journal, attribution, or investor‑profile contexts.*

## 4️⃣ AI Agents / Services
| Agent / Service | Retrieves Data? | Performs Deterministic Logic? | Calls Gemini? | Stores Narrative Output |
|----------------|----------------|----------------------------|--------------|------------------------|
| **AnalysisAgent** (`analysis_agent.py`) | Yes – receives market indicator dict from `StockService`. | Minimal post‑processing (clamp confidence, deduplicate lists). | ✅ Yes – uses Gemini provider via `BaseAgent`. | ✅ Persists prose via `save_analysis` (narrative stored in `AnalysisRecord`). |
| **RankingAgent** (`ranking_agent.py`) | Yes – receives a list of opportunity dicts from caller. | No (just passes through Gemini result). | ✅ Yes – Gemini JSON generation. | No (only returns ranked JSON, not persisted). |
| **ScannerAgent** (`scanner_agent.py`) | Yes – fetches full analysis via `StockService.analyze_ticker` and raw indicators. | No deterministic work; only merges scanner narrative into analysis dict. | ✅ Yes – Gemini generation of opportunity narrative. | No (narrative merged into response, not persisted). |
| **ChatAgent** (`chat_agent.py`) | Yes – obtains live analysis from `StockService`. Also reads from `MemoryAgent`. | No deterministic calculations; only assembles prompts. | ✅ Yes – delegates to `ai_orchestrator` (which uses Gemini). | No (chat response not stored persistently). |
| **MemoryAgent** (`memory_agent.py`) | No external data retrieval (operates on stored messages). | Yes – importance scoring & injection filtering. | No – purely deterministic. | No (stores raw messages, not AI output). |
| **AI Orchestrator** (`ai_orchestrator.py`) | No – just forwards prompts. | No. | ✅ Yes – central Gemini call for chat. | No. |

## 5️⃣ Deterministic Logic Audit
| File / Function | Purpose | Influences |
|------------------|---------|-----------|
| `stock_service.py::_fetch_history` | Pulls raw OHLCV data from yfinance (I/O). | – |
| `stock_service.py::get_raw_analysis_data` | Orchestrates multi‑timeframe fetch, computes technical indicators via `compute_indicators`, builds `timeframe_stats`, `timeframe_summary`, `alignment_score`. | **signal** (via downstream AI), **confidence** (via AI), **ranking** (via alignment_score), **risk** (alignment_score), **thesis status** (none), **portfolio evaluation** (alignment_score used later). |
| `stock_service.py::analyze_ticker` | Calls `AnalysisAgent` for AI narrative, then performs deterministic trade‑setup calculations: entry zone, stop‑loss, TP1/TP2, risk‑reward ratio, breakout probability. | **signal** (passed from AI), **confidence** (AI), **risk** (stop‑loss, risk‑reward), **ranking** (via `alignment_score` from raw data), **portfolio evaluation** (provides numbers used by UI). |
| `stock_service.py::fetch_market_data` | Simple delegate – no extra logic. | – |
| `memory_agent.py::_score_importance` | Scores importance of a message for storage. | **risk** (only affects what gets embedded). |
| `memory_agent.py::_filter_injection` | Strips disallowed prompt‑injection phrases. | – |
| `analysis_agent.py::_clamp_confidence` | Ensures confidence stays 0‑100. | **confidence** |
| `analysis_agent.py::_deduplicate` | Removes duplicate entries in list fields. | **confidence** / **signal** (clean output). |
| `analysis_agent.py::post_process` | Normalises strings, caps confidence, dedupes lists, upper‑cases signal. | **signal**, **confidence** |
| `ranking_agent.py::rank` | Constructs prompt and parses Gemini JSON for ranking. Deterministic part only JSON extraction. | **ranking** (final order). |
| `scanner_agent.py::scan_single` | Merges scanner narrative into analysis dict; fallback builds minimal safe dict. | **signal**, **confidence** (via underlying analysis), **risk** (fallback values). |
| `chat_agent.py::_build_user_prompt` / `_assemble_context` | Assembles strings for chat; no core trading logic. | – |

## 6️⃣ AI‑Native Components (Powered by Gemini)
- **AnalysisAgent** – full stock analysis generation.
- **RankingAgent** – opportunity ranking.
- **ScannerAgent** – opportunity narrative generation.
- **ChatAgent** (via `ai_orchestrator`) – chat response generation.
- **AI Orchestrator** – generic Gemini wrapper used by ChatAgent.

## 7️⃣ Migration Priority (Deterministic Systems – highest impact first)
1. **Risk‑Reward Ratio Calculation** (`stock_service.analyze_ticker` – line 166) – critical for trade‑setup sanity and filtering low‑RR trades.
2. **Alignment Score & Multi‑Timeframe Scoring** (`stock_service.get_raw_analysis_data` – lines 99‑109) – drives confidence/ranking across horizons.
3. **Trade‑Setup Logic (Entry Zone, Stop‑Loss, TP1/TP2, Breakout Probability)** (`stock_service.analyze_ticker` – lines 150‑180) – core to downstream position sizing and risk management.
4. **Deterministic Post‑Processing in AnalysisAgent** (`post_process` – lines 144‑169) – ensures clean, clamped output for downstream consumers.
5. **Importance Scoring / Prompt‑Injection Filtering** (`memory_agent._score_importance` & `_filter_injection`) – improves memory relevance and security.
6. **Fallback Logic in ScannerAgent & RankingAgent** – ensure graceful degradation when Gemini fails.

---
*All sections are based on the current repository state as of 2026‑06‑08.*
