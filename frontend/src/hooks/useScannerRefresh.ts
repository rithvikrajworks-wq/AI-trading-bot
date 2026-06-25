// src/hooks/useScannerRefresh.ts
"use client";

import { useState, useCallback } from "react";
import { getTopOpportunities, Market, RankedOpportunityResponse } from "../utils/api";

/**
 * Hook that provides a manual loader for top opportunities.
 * No automatic fetching or polling.
 */
export function useScannerRefresh() {
  const [data, setData] = useState<RankedOpportunityResponse[] | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<number | null>(null);

  const load = useCallback(async (market: Market = "ALL") => {
    setLoading(true);
    setError(null);
    try {
      const result = await getTopOpportunities(market);
      setData(result);
      setLastUpdated(Date.now());
    } catch (e: any) {
      setError(e.message || "Failed to load top opportunities");
    } finally {
      setLoading(false);
    }
  }, []);

  return { data, loading, error, lastUpdated, load };
}



