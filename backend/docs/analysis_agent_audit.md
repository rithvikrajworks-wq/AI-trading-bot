# AnalysisAgent Deterministic Logic Audit

**File:** `backend/app/agents/analysis_agent.py`

## 1️⃣ Deterministic Investment‑Related Logic Found
| Line(s) | Function / Code Block | What It Does | Reason for Existence | Category |
|--------|----------------------|--------------|----------------------|----------|
| 23‑25 | `def _clamp_confidence(value: int) -> int:` | Ensures confidence stays within 0‑100 range. | Prevents out‑of‑bounds values from downstream processing. | **Infrastructure** (numeric validation) |
| 28‑36 | `def _deduplicate(seq: List[str]) -> List[str]:` | Removes duplicate entries while preserving order for list fields. | Guarantees clean output lists for downstream consumers. | **Infrastructure** (data cleaning) |
| 57‑64 | `def _prepare_prompt_data(self, ticker: str, indicators: Dict[str, Any]) -> Dict[str, Any]:` | Packages raw indicator dict into a JSON string for the prompt. | Purely a data‑shaping helper; no investment reasoning. | **Infrastructure** (payload construction) |
| 144‑169 | `def post_process(self, model_instance: BaseModel) -> AnalysisResponse:` | * Normalises strings, * clamps confidence, * upper‑cases the `signal`, * deduplicates `key_levels` and `warnings`. | Guarantees schema‑compliant, tidy output before persisting. | **Infrastructure** (validation & cleaning) |
| 72‑78 | `async def analyze(self, ticker: str, market_data: Dict[str, Any]) -> AnalysisResponse:` | Calls `_prepare_prompt_data` then invokes `self.run`. No deterministic investment logic; just delegation. | Boilerplate orchestration. | **Infrastructure** |
| 80‑122 | `async def run(self, ticker: str, **indicators: Any) -> AnalysisResponse:` | Splits raw LLM response into prose and JSON, persists prose via `save_analysis`, validates JSON, logs duration. | Handles LLM plumbing, persistence, and error handling. | **Infrastructure** |
| 127‑139 | `_fallback_response` | Provides a deterministic fallback JSON when Gemini fails. | Guarantees a safe response shape. | **Infrastructure** |

**Note:** The agent does **not** contain any deterministic signal generation, position sizing, entry/exit calculations, volatility classification, or weighting formulas. All such investment reasoning is currently delegated to the Gemini LLM (via `self.generate_response`).

## 2️⃣ Why This Logic Exists
- **_clamp_confidence** and **_deduplicate** ensure the data returned from Gemini conforms to the expected schema and is free of duplicates or out‑of‑range values.
- **_prepare_prompt_data** simply transforms the indicator dict into a JSON string that the prompt can interpolate; it does not embed any trading heuristics.
- **post_process** sanitises the model output (string trimming, signal normalisation) before it is persisted.
- **run** handles splitting the LLM response, persisting the narrative, and validating the JSON – all required for reliable API behaviour.
- **_fallback_response** guarantees a well‑shaped response when the LLM is unavailable.

These pieces are **infrastructure / validation** concerns, not investment reasoning.

## 3️⃣ What Gemini Prompt Should Replace
Since no deterministic investment calculations remain, the only prompt changes required are to **ensure the LLM outputs the needed fields** directly, removing any need for Python‑side computation. The prompt (located in `backend/app/agents/prompts/analysis_prompt.txt`) should explicitly request:
- `signal` (BUY/SELL/HOLD)
- `confidence` (0‑100 integer)
- `risk_level` (e.g., Low/Medium/High)
- `key_levels` and `warnings` (list of strings)
- Any other fields already defined in `AnalysisResponse` (e.g., `summary`, `technical_analysis`, `entry_strategy`, `exit_strategy`, `holding_period`, etc.)

The prompt can also ask the model to **respect numeric ranges** (e.g., “confidence must be between 0 and 100”) so the post‑process clamping becomes a safety net rather than core logic.

### Example Prompt Additions
```
Provide the following JSON structure exactly as shown:
{
  "signal": "BUY|SELL|HOLD",
  "confidence": <integer 0‑100>,
  "risk_level": "Low|Medium|High",
  "key_levels": ["..."],
  "warnings": ["..."],
  ... (other required fields)
}

Make sure the values respect the indicated ranges. Do not perform any additional calculations; simply report the values based on the supplied market data.
```

## 4️⃣ Migration Summary
- **Deterministic logic to keep:** schema validation, enum/ numeric range checks, logging, error handling, persistence, caching, rate‑limiting, and the fallback response.
- **Deterministic investment logic to replace:** none (already absent). All investment reasoning is LLM‑driven.
- **Next step:** Update the analysis prompt to request all required fields explicitly and rely on the existing `post_process` for final sanitisation.

---
*Report generated on 2026‑06‑08.*
