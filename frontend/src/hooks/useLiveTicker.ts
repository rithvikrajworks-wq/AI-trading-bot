// src/hooks/useLiveTicker.ts
"use client";

import { useEffect, useRef, useState } from "react";
import { fetchLivePrice, LivePriceResponse } from "../utils/api";

/**
 * Hook that polls the live‑price endpoint for a given ticker.
 * Default polling interval is 8 seconds (WebSocket‑ready – can be swapped later).
 */
export function useLiveTicker(
  ticker: string | null,
  pollIntervalMs: number = 8000
): {
  data: LivePriceResponse | null;
  loading: boolean;
  error: string | null;
} {
  const [data, setData] = useState<LivePriceResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const prevTickerRef = useRef<string | null>(null);

  useEffect(() => {
    if (!ticker) {
      setData(null);
      setError(null);
      setLoading(false);
      return;
    }
    let cancelled = false;
    const load = async () => {
      setLoading(true);
      setError(null);
      try {
        const result = await fetchLivePrice(ticker);
        if (!cancelled) setData(result);
      } catch (e: any) {
        if (!cancelled) setError(e.message ?? "Failed to fetch live price");
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    load();
    const interval = setInterval(load, pollIntervalMs);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [ticker, pollIntervalMs]);

  // Reset when ticker changes completely
  useEffect(() => {
    if (prevTickerRef.current !== ticker) {
      setData(null);
    }
    prevTickerRef.current = ticker;
  }, [ticker]);

  return { data, loading, error };
}
