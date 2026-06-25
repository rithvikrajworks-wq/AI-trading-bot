// src/utils/tickerHelpers.ts
/**
 * Utility functions for normalizing ticker symbols based on market.
 * Backend (yfinance) expects Indian tickers to have the ".NS" suffix, while
 * TradingView works with the plain symbol.
 */

/**
 * Normalizes ticker for backend API calls.
 */
export function normalizeTickerForBackend(ticker: string, market: "US" | "INDIA"): string {
  let clean = ticker.trim().toUpperCase();
  if (market === "INDIA") {
    if (!clean.endsWith('.NS')) {
      clean = `${clean}.NS`;
    }
  } else {
    if (clean.endsWith('.NS')) {
      clean = clean.replace(/\.NS$/i, '');
    }
  }
  return clean;
}

/**
 * Normalizes ticker for TradingView chart.
 */
export function normalizeTickerForTradingView(ticker: string): string {
  return ticker.trim().toUpperCase().replace(/\.NS$/i, '');
}
