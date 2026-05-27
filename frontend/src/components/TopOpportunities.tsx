"use client";

import React, { useEffect, useRef, useState } from "react";
import { Card, CardHeader, CardTitle, CardContent } from "./ui/card";
import { useScannerRefresh } from "../hooks/useScannerRefresh";
import { StockAnalysisResponse } from "../utils/api";

export default function TopOpportunities() {
  const { data, loading, error, lastUpdated } = useScannerRefresh();
  const [highlighted, setHighlighted] = useState<string[]>([]);
  const prevDataRef = useRef<StockAnalysisResponse[] | null>(null);

  // Highlight rows where confidence or signal changed
  useEffect(() => {
    if (data && prevDataRef.current) {
      const changed = data.filter((newItem) => {
        const oldItem = prevDataRef.current!.find((o) => o.ticker === newItem.ticker);
        return oldItem && (oldItem.confidence !== newItem.confidence || oldItem.signal !== newItem.signal);
      }).map((i) => i.ticker);
      if (changed.length > 0) {
        setHighlighted(changed);
        const timeout = setTimeout(() => setHighlighted([]), 800);
        return () => clearTimeout(timeout);
      }
    }
    prevDataRef.current = data;
  }, [data]);

  if (loading && !data) {
    return (
      <Card className="bg-slate-900/80 border-slate-700 glass">
        <CardHeader>
          <CardTitle className="text-slate-300">Top Opportunities</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="h-4 bg-slate-700 rounded animate-pulse" />
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className="bg-slate-900/80 border-slate-700 glass">
        <CardHeader>
          <CardTitle className="text-slate-300">Top Opportunities</CardTitle>
        </CardHeader>
        <CardContent className="text-center text-red-500">{error}</CardContent>
      </Card>
    );
  }

  return (
    <Card className="bg-slate-900/80 border-slate-700 glass">
      <CardHeader>
        <CardTitle className="text-slate-300">Top Opportunities</CardTitle>
      </CardHeader>
      <CardContent>
        {data && data.length > 0 ? (
          <ul className="space-y-2 text-sm">
            {data.map((stock) => (
              <li
                key={stock.ticker}
                className={`flex justify-between items-center transition-colors duration-300 ${highlighted.includes(stock.ticker) ? "bg-emerald-900/30" : ""}`}
              >
                <span className="font-medium text-slate-100">{stock.ticker}</span>
                <span className={stock.signal === "BUY" ? "text-green-400" : stock.signal === "SELL" ? "text-rose-400" : "text-slate-400"}>
                  {stock.signal}
                </span>
                <span className="text-slate-400">{stock.confidence}%</span>
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-slate-400">No high‑confidence BUY signals found.</p>
        )}
        {lastUpdated && (
          <p className="text-xs text-slate-400 mt-2">
            Last updated {Math.floor((Date.now() - lastUpdated) / 1000)} sec ago
          </p>
        )}
      </CardContent>
    </Card>
  );
}
