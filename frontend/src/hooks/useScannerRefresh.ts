// src/hooks/useScannerRefresh.ts
"use client";

import { useEffect, useState } from "react";
import { fetchTopOpportunities, StockAnalysisResponse } from "../utils/api";

/**
 * Hook that fetches top opportunities on an interval.
 * Returns the data, loading flag, any error and the timestamp of the last successful fetch.
 */
export function useScannerRefresh(
  refreshIntervalMs: number = 45000
): {
  data: StockAnalysisResponse[] | null;
  loading: boolean;
  error: string | null;
  lastUpdated: number | null; // epoch ms of last successful fetch
} {
  const [data, setData] = useState<StockAnalysisResponse[] | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<number | null>(null);

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await fetchTopOpportunities();
      setData(result);
      setLastUpdated(Date.now());
    } catch (e: any) {
      setError(e.message || "Failed to load top opportunities");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
    const interval = setInterval(load, refreshIntervalMs);
    return () => clearInterval(interval);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return { data, loading, error, lastUpdated };
}
