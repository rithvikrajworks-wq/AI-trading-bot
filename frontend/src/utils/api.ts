// Define types matching the FastAPI backend schemas

import { normalizeTickerForBackend } from "./tickerHelpers";

export type BackendMarket = "US" | "INDIA";

export interface StockAnalysisResponse {
  ticker: string;
  price: number;
  signal: "BUY" | "SELL" | "HOLD";
  confidence: number;
  rsi: number;
  macd: "bullish" | "bearish";
  ema_trend: "bullish" | "bearish";
  pros: string[];
  cons: string[];

  // AI-native fields
  breakout_probability?: number;
  risk_level?: string;
  summary?: string;
  company_overview?: string;
  technical_analysis?: string;
  chart_analysis?: string;
  trend_analysis?: string;
  momentum_analysis?: string;
  support_resistance_analysis?: string;
  bull_case?: string;
  bear_case?: string;
  investment_thesis?: string;
  position_assessment?: string;
  entry_strategy?: string;
  exit_strategy?: string;
  holding_period?: string;
  holding_period_rationale?: string;
  key_levels?: string[];
  warnings?: string[];
  setup_quality?: string;
  market_bias?: string;
  catalyst_summary?: string;
}

export interface BatchErrorDetail {
  ticker: string;
  error: string;
}

export interface BatchAnalysisResponse {
  results: StockAnalysisResponse[];
  errors: BatchErrorDetail[];
}

export interface RankedOpportunityResponse {
  ticker: string;
  display_ticker?: string;
  market: "US" | "INDIA";
  signal: "BUY" | "SELL" | "HOLD";
  confidence: number;
  expected_profit_pct: number;
  entry_range_min: number;
  entry_range_max: number;
  exit_range_min: number;
  exit_range_max: number;
  stop_loss: number;
  risk_reward_ratio: number;
  breakout_probability: number;
  holding_period: string;
  setup_quality: "weak" | "average" | "strong";
  pros: string[];
  cons: string[];
  reason: string;
  rank_score?: number;
}
// Low Token Check types
export interface LowTokenCheckResponse {
  ticker: string;
  worth_analysis: boolean;
  reason: string;
  estimated_setup_quality: "low" | "medium" | "high";
  suggested_next_mode: "normal_analysis" | "trading_committee" | "risk_reward" | "skip";
}

export interface AnalysisModeRequest {
  ticker: string;
  mode: "low_token";
}

/**
 * Run low‑token check for a ticker.
 * POST /analyze-stock-mode
 */
export async function runLowTokenCheck(
  ticker: string,
  market: BackendMarket = "US"
): Promise<LowTokenCheckResponse> {
  const cleanTicker = normalizeTickerForBackend(ticker, market);

  if (!cleanTicker) {
    throw new Error("Ticker symbol cannot be empty");
  }

  const response = await fetch(`${API_BASE_URL}/analyze-stock-mode`, {
    method: "POST",
    headers: {
      ...getAuthHeaders(),
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      ticker: cleanTicker,
      mode: "low_token",
    }),
  });

  checkResponseStatus(response);

  if (!response.ok) {
    let errorMessage = `Low token check failed for '${cleanTicker}'`;

    try {
      const errBody = await response.json();
      if (errBody?.detail) {
        errorMessage = errBody.detail;
      }
    } catch {}

    throw new Error(errorMessage);
  }

  return response.json();
}


const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

// Helper to get the auth headers
function getAuthHeaders(): HeadersInit {
  const headers: Record<string, string> = {
    "Accept": "application/json",
  };
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("access_token");
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }
  }
  return headers;
}

// Helper to handle response status checks (specifically 401/403)
function checkResponseStatus(response: Response) {
  if (response.status === 401 || response.status === 403) {
    if (typeof window !== "undefined") {
      localStorage.removeItem("access_token");
      window.dispatchEvent(new Event("auth-failed"));
    }
  }
}

// Login function using OAuth2 Password Flow (Form Data)
export async function loginUser(username: string, password: string): Promise<string> {
  const params = new URLSearchParams();
  params.append("username", username);
  params.append("password", password);

  const response = await fetch(`${API_BASE_URL}/auth/login`, {
    method: "POST",
    headers: {
      "Content-Type": "application/x-www-form-urlencoded",
      "Accept": "application/json",
    },
    body: params,
  });

  if (!response.ok) {
    let errorMessage = "Login failed";
    try {
      const errBody = await response.json();
      if (errBody && errBody.detail) {
        errorMessage = errBody.detail;
      }
    } catch { }
    throw new Error(errorMessage);
  }

  const data = await response.json();
  return data.access_token;
}

// New type for live price response
export interface LivePriceResponse {
  ticker: string;
  price: number;
  change: number;
  change_percent: number;
  timestamp: string;
}

/**
 * Fetch live price for a ticker.
 * GET /live-price/{ticker}
 */
export async function fetchLivePrice(ticker: string): Promise<LivePriceResponse> {
  const cleanTicker = ticker.trim().toUpperCase();
  if (!cleanTicker) {
    throw new Error("Ticker symbol cannot be empty");
  }
  const response = await fetch(`${API_BASE_URL}/live-price/${encodeURIComponent(cleanTicker)}`, {
    method: "GET",
    headers: getAuthHeaders(),
  });
  checkResponseStatus(response);
  if (!response.ok) {
    let errorMessage = `Failed to fetch live price for '${cleanTicker}'`;
    try {
      const errBody = await response.json();
      if (errBody && errBody.detail) {
        errorMessage = errBody.detail;
      }
    } catch { }
    throw new Error(errorMessage);
  }
  return response.json();
}


/**
 * Fetch technical analysis for a single stock ticker.
 * GET /analyze-stock?ticker=NVDA
 */
export async function fetchStockAnalysis(
  ticker: string,
  market: BackendMarket = "US"
): Promise<StockAnalysisResponse> {
  const cleanTicker = normalizeTickerForBackend(ticker, market);
  if (!cleanTicker) {
    throw new Error("Ticker symbol cannot be empty");
  }

  const response = await fetch(`${API_BASE_URL}/analyze-stock?ticker=${encodeURIComponent(cleanTicker)}`, {
    method: "GET",
    headers: getAuthHeaders(),
  });
  checkResponseStatus(response);

  if (!response.ok) {
    let errorMessage = `Failed to analyze ticker '${cleanTicker}'`;
    try {
      const errBody = await response.json();
      if (errBody && errBody.detail) {
        errorMessage = errBody.detail;
      }
    } catch {
      // Fallback if parsing JSON fails
    }
    throw new Error(errorMessage);
  }

  return response.json();
}

/**
 * Fetch AI-powered analysis for a ticker.
 * GET /ai-analysis/{ticker}
 */
export interface AIAnalysisResponse {
  ticker: string;
  analysis: string; // Natural language analysis from LLM
  confidence: number;
}

export async function fetchAIAnalysis(ticker: string): Promise<AIAnalysisResponse> {
  const cleanTicker = ticker.trim().toUpperCase();
  if (!cleanTicker) {
    throw new Error("Ticker symbol cannot be empty");
  }

  const response = await fetch(`${API_BASE_URL}/ai-analysis/${encodeURIComponent(cleanTicker)}`, {
    method: "GET",
    headers: getAuthHeaders(),
  });
  checkResponseStatus(response);

  if (!response.ok) {
    let errorMessage = `Failed to fetch AI analysis for '${cleanTicker}'`;
    try {
      const errBody = await response.json();
      if (errBody && errBody.detail) {
        errorMessage = errBody.detail;
      }
    } catch {
      // ignore parsing error
    }
    throw new Error(errorMessage);
  }

  return response.json();
}

/**
 * Fetch technical analysis for multiple stock tickers concurrently.
 * POST /analyze-stocks
 */
export async function fetchBatchAnalysis(tickers: string[]): Promise<BatchAnalysisResponse> {
  const cleanTickers = tickers
    .map((t) => t.trim().toUpperCase())
    .filter((t) => t.length > 0);

  if (cleanTickers.length === 0) {
    throw new Error("Tickers list cannot be empty");
  }

  if (cleanTickers.length > 10) {
    throw new Error("Batch requests are capped at 10 tickers maximum");
  }

  const headers = getAuthHeaders();
  const response = await fetch(`${API_BASE_URL}/analyze-stocks`, {
    method: "POST",
    headers: {
      ...headers,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ tickers: cleanTickers }),
  });
  checkResponseStatus(response);

  if (!response.ok) {
    let errorMessage = "Failed to run batch stock analysis";
    try {
      const errBody = await response.json();
      if (errBody && errBody.detail) {
        errorMessage = errBody.detail;
      }
    } catch {
      // Fallback
    }
    throw new Error(errorMessage);
  }

  return response.json();
}

// Real‑time scanner & market status helpers

/** Fetch top opportunities (real‑time scanner) */
export type Market = "US" | "INDIA" | "ALL";

/**
 * Fetch top opportunities (real‑time scanner) with optional filters.
 * GET /top-opportunities?market=US&limit=10&force_refresh=true
 */
export async function getTopOpportunities(
  market: Market = "ALL",
  limit: number = 10,
  forceRefresh: boolean = false
): Promise<RankedOpportunityResponse[]> {
  const url = `${API_BASE_URL}/top-opportunities?market=${market}&limit=${limit}&force_refresh=${forceRefresh}`;
  const response = await fetch(url, {
    method: "GET",
    headers: getAuthHeaders(),
  });
  checkResponseStatus(response);

  if (!response.ok) {
    let errorMessage = `Failed to fetch top opportunities`;
    try {
      const errBody = await response.json();
      if (errBody && errBody.detail) {
        errorMessage = errBody.detail;
      }
    } catch {}
    throw new Error(errorMessage);
  }
  const data: RankedOpportunityResponse[] = await response.json();
  return data;
}

/** Fetch market status strip data */
export interface MarketStatus {
  nse: string;
  nyse: string;
  nasdaq: string;
  local_time: string;
  next_change_in_seconds: number;
}

export async function fetchMarketStatus(): Promise<MarketStatus> {
  const response = await fetch(`${API_BASE_URL}/market-status`, {
    method: "GET",
    headers: getAuthHeaders(),
  });
  checkResponseStatus(response);

  if (!response.ok) {
    let errorMessage = `Failed to fetch market status`;
    try {
      const errBody = await response.json();
      if (errBody && errBody.detail) {
        errorMessage = errBody.detail;
      }
    } catch { }
    throw new Error(errorMessage);
  }
  const data: MarketStatus = await response.json();
  return data;
}

/*
 * Chat request/response types and fetch helper
 */
export interface ChatRequest {
  ticker: string;
  user_message: string;
  conversation_history?: { role: string; content: string }[];
  market_context?: Record<string, any>;
}

export interface ChatResponse {
  ticker: string;
  response: string;
  analysis_summary: any; // refined later
  risk_summary: any;
}

/**
 * Send a chat request to the backend.
 * POST /chat
 */
export async function fetchChat(request: ChatRequest): Promise<ChatResponse> {
  const headers = getAuthHeaders();
  const response = await fetch(`${API_BASE_URL}/chat`, {
    method: "POST",
    headers: {
      ...headers,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      ...request,
      ticker: request.ticker.trim().toUpperCase(),
    }),
  });
  checkResponseStatus(response);
  if (!response.ok) {
    let errorMessage = `Chat request failed`;
    try {
      const errBody = await response.json();
      if (errBody && errBody.detail) errorMessage = errBody.detail;
    } catch { }
    throw new Error(errorMessage);
  }
  return response.json();
}


