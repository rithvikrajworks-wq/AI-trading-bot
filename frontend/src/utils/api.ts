// Define types matching the FastAPI backend schemas

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
}

export interface BatchErrorDetail {
  ticker: string;
  error: string;
}

export interface BatchAnalysisResponse {
  results: StockAnalysisResponse[];
  errors: BatchErrorDetail[];
}
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

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
    headers: {
      "Accept": "application/json",
    },
  });
  if (!response.ok) {
    let errorMessage = `Failed to fetch live price for '${cleanTicker}'`;
    try {
      const errBody = await response.json();
      if (errBody && errBody.detail) {
        errorMessage = errBody.detail;
      }
    } catch {}
    throw new Error(errorMessage);
  }
  return response.json();
}


/**
 * Fetch technical analysis for a single stock ticker.
 * GET /analyze-stock?ticker=NVDA
 */
export async function fetchStockAnalysis(ticker: string): Promise<StockAnalysisResponse> {
  const cleanTicker = ticker.trim().toUpperCase();
  if (!cleanTicker) {
    throw new Error("Ticker symbol cannot be empty");
  }

  const response = await fetch(`${API_BASE_URL}/analyze-stock?ticker=${encodeURIComponent(cleanTicker)}`, {
    method: "GET",
    headers: {
      "Accept": "application/json",
    },
  });

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

  const response = await fetch(`${API_BASE_URL}/analyze-stocks`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Accept": "application/json",
    },
    body: JSON.stringify({ tickers: cleanTickers }),
  });

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
export async function fetchTopOpportunities(): Promise<StockAnalysisResponse[]> {
  const response = await fetch(`${API_BASE_URL}/top-opportunities`, {
    method: "GET",
    headers: {
      "Accept": "application/json",
    },
  });

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
  const data: StockAnalysisResponse[] = await response.json();
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
    headers: {
      "Accept": "application/json",
    },
  });

  if (!response.ok) {
    let errorMessage = `Failed to fetch market status`;
    try {
      const errBody = await response.json();
      if (errBody && errBody.detail) {
        errorMessage = errBody.detail;
      }
    } catch {}
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
  const response = await fetch(`${API_BASE_URL}/chat`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Accept": "application/json",
    },
    body: JSON.stringify(request),
  });
  if (!response.ok) {
    let errorMessage = `Chat request failed`;
    try {
      const errBody = await response.json();
      if (errBody && errBody.detail) errorMessage = errBody.detail;
    } catch {}
    throw new Error(errorMessage);
  }
  return response.json();
}

