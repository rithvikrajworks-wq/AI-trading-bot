/**
 * File path: Tradingbotmk1/frontend/src/utils/portfolioApi.ts
 *
 * All portfolio API calls.  No AI calls, no scanner calls.
 * Base URL reads from NEXT_PUBLIC_API_URL env var (falls back to localhost:8000).
 */

const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export type Market = "US" | "INDIA";
export type HoldingStatus = "holding" | "watching" | "sold";

export interface Holding {
  id: number;
  ticker: string;
  market: Market;
  quantity: number;
  average_cost: number;
  current_price: number;
  status: HoldingStatus;
  notes: string | null;
  created_at: string;
  updated_at: string;
  // computed – returned by backend
  invested_amount: number;
  current_value: number;
  profit_loss: number;
  profit_loss_pct: number;
}

export interface HoldingCreate {
  ticker: string;
  market: Market;
  quantity: number;
  average_cost: number;
  current_price: number;
  status?: HoldingStatus;
  notes?: string;
}

export interface HoldingUpdate {
  market?: Market;
  quantity?: number;
  average_cost?: number;
  current_price?: number;
  status?: HoldingStatus;
  notes?: string;
}

export interface PortfolioSummary {
  total_invested: number;
  total_current_value: number;
  total_profit_loss: number;
  total_profit_loss_pct: number;
  holdings_count: number;
  watching_count: number;
  sold_count: number;
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (res.status === 204) return undefined as unknown as T;
  const data = await res.json();
  if (!res.ok) {
    throw new Error(data?.detail ?? `Request failed: ${res.status}`);
  }
  return data as T;
}

// ---------------------------------------------------------------------------
// API calls
// ---------------------------------------------------------------------------

/** GET /portfolio – list all holdings */
export async function fetchHoldings(): Promise<Holding[]> {
  return apiFetch<Holding[]>("/portfolio/");
}

/** GET /portfolio/summary – aggregate stats */
export async function fetchSummary(): Promise<PortfolioSummary> {
  return apiFetch<PortfolioSummary>("/portfolio/summary");
}

/** POST /portfolio – add a new holding */
export async function createHolding(payload: HoldingCreate): Promise<Holding> {
  return apiFetch<Holding>("/portfolio/", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

/** PATCH /portfolio/{ticker} – update a holding */
export async function updateHolding(
  ticker: string,
  payload: HoldingUpdate
): Promise<Holding> {
  return apiFetch<Holding>(`/portfolio/${ticker}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

/** DELETE /portfolio/{ticker} – remove a holding */
export async function deleteHolding(ticker: string): Promise<void> {
  return apiFetch<void>(`/portfolio/${ticker}`, { method: "DELETE" });
}
