// src/components/TopOpportunities.tsx
"use client";

import React, { useEffect, useRef, useState } from "react";
import { Card, CardHeader, CardTitle, CardContent } from "./ui/card";
import { useScannerRefresh } from "../hooks/useScannerRefresh";
import { RankedOpportunityResponse, Market } from "../utils/api";
import { Check, Info, X } from "lucide-react";

function formatPrice(value: number): string {
  return value.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

export default function TopOpportunities() {
  const { data, loading, error, load } = useScannerRefresh();
  const [highlighted, setHighlighted] = useState<string[]>([]);
  const [market, setMarket] = useState<Market>("ALL");
  const prevDataRef = useRef<RankedOpportunityResponse[] | null>(null);

  // Highlight rows where confidence or signal changed
  useEffect(() => {
    if (data && prevDataRef.current) {
      const changed = data
        .filter((newItem) => {
          const oldItem = prevDataRef.current!.find((o) => o.ticker === newItem.ticker);
          return oldItem && (oldItem.confidence !== newItem.confidence || oldItem.signal !== newItem.signal);
        })
        .map((i) => i.ticker);
      if (changed.length > 0) {
        setHighlighted(changed);
        const timeout = setTimeout(() => setHighlighted([]), 800);
        return () => clearTimeout(timeout);
      }
    }
    prevDataRef.current = data;
  }, [data]);

  const handleRunScanner = () => {
    load(market);
  };

  return (
    <Card className="bg-slate-900/80 border-slate-700 glass">
      <CardHeader>
        <CardTitle className="text-slate-300 flex items-center justify-between">
          <span>Top Opportunities</span>
          <div className="flex items-center gap-2">
            <span className="text-xs text-slate-400 font-medium max-w-xs text-right">
              Scanner ranks estimated trades using indicators. Results are not guaranteed.
            </span>
            <select
              value={market}
              onChange={(e) => setMarket(e.target.value as Market)}
              className="px-2 py-1 text-sm bg-slate-800 text-slate-200 rounded"
            >
              <option value="ALL">All Markets</option>
              <option value="US">US Market</option>
              <option value="INDIA">India Market</option>
            </select>
            <button
              onClick={handleRunScanner}
              className="px-3 py-1 text-sm bg-emerald-600 hover:bg-emerald-500 text-white rounded transition"
              disabled={loading}
            >
              {loading ? "Running..." : "Run Scanner"}
            </button>
          </div>
        </CardTitle>
      </CardHeader>
      <CardContent>
        {loading && !data && (
          <div className="text-center py-6 text-slate-300">Loading top opportunities...</div>
        )}
        {error && <div className="text-center py-6 text-rose-500">{error}</div>}
        {data && data.length > 0 ? (
          <div className="space-y-4">
            {data.map((stock, index) => {
              const isBuy = stock.signal === "BUY";
              const isSell = stock.signal === "SELL";
              const isTopRank = index === 0;
              return (
                <div
                  key={stock.ticker}
                  className={`border rounded-xl p-4 transition-all duration-300 space-y-4 ${
                    highlighted.includes(stock.ticker)
                      ? "border-emerald-500/40 bg-emerald-950/10"
                      : isTopRank
                      ? "border-emerald-500/25 bg-slate-950/60 shadow-[0_0_15px_rgba(16,185,129,0.06)]"
                      : "border-slate-800 bg-slate-950/20 hover:border-slate-750 hover:bg-slate-950/45"
                  }`}
                >
                  <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-900 pb-2">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="flex items-center justify-center w-6 h-6 rounded-full bg-slate-900 text-xs font-bold text-emerald-400 border border-slate-800">
                        {index + 1}
                      </span>
                      <span className="font-bold text-base text-slate-100 tracking-wide">{stock.display_ticker ?? stock.ticker.replace(/\.NS$/, "")}</span>
                      <span className="text-xs font-medium px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
                        {stock.market}
                      </span>
                      <span
                        className={`text-xs font-semibold px-2 py-0.5 rounded capitalize ${
                          isBuy
                            ? "bg-emerald-950/30 text-emerald-400 border border-emerald-900/20"
                            : isSell
                            ? "bg-rose-950/30 text-rose-400 border border-rose-900/20"
                            : "bg-amber-950/30 text-amber-400 border border-amber-900/20"
                        }`}
                      >
                        {stock.signal}
                      </span>
                      <span className="text-xs font-medium px-2 py-0.5 rounded capitalize bg-slate-900 text-slate-400 border border-slate-800">
                        {stock.setup_quality} setup
                      </span>
                    </div>
                    <div className="flex items-center gap-4 text-xs">
                      <div>
                        <span className="text-slate-500 mr-1 select-none">Est. profit:</span>
                        <span className="font-bold text-emerald-400">{stock.expected_profit_pct.toFixed(2)}%</span>
                      </div>
                      <div>
                        <span className="text-slate-500 mr-1 select-none">Confidence:</span>
                        <span className="font-bold text-slate-300">{stock.confidence}%</span>
                      </div>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 md:grid-cols-4 gap-2 bg-slate-950/60 p-2.5 rounded-lg border border-slate-900 text-center">
                    <div>
                      <span className="block text-[9px] text-slate-500 uppercase select-none">Entry range</span>
                      <span className="text-xs font-bold text-slate-300">
                        {formatPrice(stock.entry_range_min)} – {formatPrice(stock.entry_range_max)}
                      </span>
                    </div>
                    <div>
                      <span className="block text-[9px] text-slate-500 uppercase select-none">Exit range</span>
                      <span className="text-xs font-bold text-slate-300">
                        {formatPrice(stock.exit_range_min)} – {formatPrice(stock.exit_range_max)}
                      </span>
                    </div>
                    <div>
                      <span className="block text-[9px] text-slate-500 uppercase select-none">Stop loss</span>
                      <span className="text-xs font-bold text-rose-400">{formatPrice(stock.stop_loss)}</span>
                    </div>
                    <div>
                      <span className="block text-[9px] text-slate-500 uppercase select-none">Risk / reward</span>
                      <span className="text-xs font-bold text-slate-300">{stock.risk_reward_ratio.toFixed(2)}</span>
                    </div>
                    <div>
                      <span className="block text-[9px] text-slate-500 uppercase select-none">Breakout</span>
                      <span className="text-xs font-bold text-emerald-400">{stock.breakout_probability}%</span>
                    </div>
                    <div>
                      <span className="block text-[9px] text-slate-500 uppercase select-none">Holding period</span>
                      <span className="text-xs font-bold text-slate-300">{stock.holding_period}</span>
                    </div>
                    {stock.rank_score != null && (
                      <div>
                        <span className="block text-[9px] text-slate-500 uppercase select-none">Rank score</span>
                        <span className="text-xs font-bold text-slate-300">{stock.rank_score.toFixed(2)}</span>
                      </div>
                    )}
                  </div>

                  {stock.reason && (
                    <div className="bg-slate-950/20 p-2 rounded border border-slate-900/60 text-xs">
                      <span className="text-[10px] font-semibold text-slate-400 flex items-center gap-1 select-none">
                        <Info size={12} className="text-sky-500" /> Reason
                      </span>
                      <p className="text-slate-300 leading-relaxed mt-1">{stock.reason}</p>
                    </div>
                  )}

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
                    <div className="space-y-2">
                      <span className="text-[10px] font-semibold text-emerald-500/80 flex items-center gap-1 select-none">
                        <Check size={12} /> Pros
                      </span>
                      {stock.pros.length > 0 ? (
                        <ul className="space-y-1">
                          {stock.pros.map((pro, idx) => (
                            <li
                              key={idx}
                              className="text-slate-300 bg-emerald-950/5 border border-emerald-900/10 p-2 rounded-md"
                            >
                              {pro}
                            </li>
                          ))}
                        </ul>
                      ) : (
                        <p className="text-slate-400">No pros provided.</p>
                      )}
                    </div>
                    <div className="space-y-2">
                      <span className="text-[10px] font-semibold text-rose-500/80 flex items-center gap-1 select-none">
                        <X size={12} /> Cons
                      </span>
                      {stock.cons.length > 0 ? (
                        <ul className="space-y-1">
                          {stock.cons.map((con, idx) => (
                            <li
                              key={idx}
                              className="text-slate-300 bg-rose-950/5 border border-rose-900/10 p-2 rounded-md"
                            >
                              {con}
                            </li>
                          ))}
                        </ul>
                      ) : (
                        <p className="text-slate-400">No cons provided.</p>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          !loading && <p className="text-slate-400 text-center py-6">No opportunities available yet.</p>
        )}
      </CardContent>
    </Card>
  );
}
