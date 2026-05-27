"use client";

import React, { useState } from "react";
import StockSearch from "./StockSearch";
import AnalysisCard from "./AnalysisCard";
import TradingViewChart from "./TradingViewChart";
import TopOpportunities from "./TopOpportunities";
import AIChatPanel from "./AIChatPanel";
import { fetchStockAnalysis, StockAnalysisResponse } from "../utils/api";
import { useLiveTicker } from "../hooks/useLiveTicker";
import WatchlistPanel from "./WatchlistPanel";

export default function Dashboard() {
  const [analysis, setAnalysis] = useState<StockAnalysisResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string>("");

  const handleSearch = async (ticker: string) => {
    setLoading(true);
    setError("");
    try {
      const data = await fetchStockAnalysis(ticker);
      setAnalysis(data);
    } catch (e: any) {
      console.error(e);
      setError(e.message || "Failed to fetch analysis");
      setAnalysis(null);
    } finally {
      setLoading(false);
    }
  };


  const ticker = analysis?.ticker || "";
  const { data: liveData, loading: liveLoading, error: liveError } = useLiveTicker(ticker);

  return (
    <main className="min-h-screen bg-slate-950 text-slate-100 p-6 flex flex-col gap-6">
      <section className="max-w-2xl mx-auto w-full">
        <StockSearch onSearch={handleSearch} isLoading={loading} />
          <WatchlistPanel onSelect={handleSearch} />
        {error && <p className="mt-2 text-sm text-red-500 text-center">{error}</p>}
      </section>

      {/* Empty state when no ticker selected */}
      {!analysis && !loading && (
        <section className="max-w-3xl mx-auto w-full mt-12 text-center">
          <h2 className="text-2xl font-semibold mb-4">AI Trading Copilot</h2>
          <p className="text-slate-300 mb-4">Select a ticker to start a conversation with the AI assistant.</p>
          <div className="flex flex-wrap justify-center gap-3">
            <button className="px-4 py-2 bg-emerald-600 text-slate-100 rounded-md hover:bg-emerald-500">Is this a good entry?</button>
            <button className="px-4 py-2 bg-emerald-600 text-slate-100 rounded-md hover:bg-emerald-500">What are the risks?</button>
            <button className="px-4 py-2 bg-emerald-600 text-slate-100 rounded-md hover:bg-emerald-500">Bullish vs bearish case</button>
            <button className="px-4 py-2 bg-emerald-600 text-slate-100 rounded-md hover:bg-emerald-500">Explain stop loss</button>
            <button className="px-4 py-2 bg-emerald-600 text-slate-100 rounded-md hover:bg-emerald-500">How strong is this setup?</button>
          </div>
        </section>
      )}

      {analysis && (
        <section className="grid lg:grid-cols-2 gap-6 max-w-5xl mx-auto w-full">
          <div className="flex flex-col gap-4">
            {ticker && (
              <div className="glass p-3 rounded mb-4 flex items-center justify-between">
                <div className="text-lg font-medium text-slate-200">{ticker} Live</div>
                {liveLoading ? (
                  <span className="text-slate-400">Loading...</span>
                ) : liveError ? (
                  <span className="text-rose-400">{liveError}</span>
                ) : liveData ? (
                  <div className="flex items-center gap-2">
                    <span className="text-emerald-400">${liveData.price.toFixed(2)}</span>
                    <span className={liveData.change >= 0 ? "text-emerald-300" : "text-rose-300"}>
                      {liveData.change >= 0 ? "▲" : "▼"} {liveData.change.toFixed(2)} ({liveData.change_percent.toFixed(2)}%)
                    </span>
                  </div>
                ) : null}
              </div>
            )}
            <AnalysisCard data={analysis} />
            <TradingViewChart ticker={analysis.ticker} />
          </div>
          <AIChatPanel ticker={ticker} />
        </section>
      )}

      {/* Top Opportunities section below the main analysis */}
      <section className="max-w-5xl mx-auto w-full mt-8">
        <TopOpportunities />
      </section>
    </main>
  );
}
