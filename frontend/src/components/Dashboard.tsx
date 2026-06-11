"use client";

import React, { useState, useEffect } from "react";
import StockSearch from "./StockSearch";
import AnalysisCard from "./AnalysisCard";
import TradingViewChart from "./TradingViewChart";
import TopOpportunities from "./TopOpportunities";
import AIChatPanel from "./AIChatPanel";
import { fetchStockAnalysis, StockAnalysisResponse, loginUser } from "../utils/api";
import { useLiveTicker } from "../hooks/useLiveTicker";
import WatchlistPanel from "./WatchlistPanel";

export default function Dashboard() {
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false);
  const [tokenChecked, setTokenChecked] = useState<boolean>(false);
  
  // Login credentials state
  const [username, setUsername] = useState<string>("");
  const [password, setPassword] = useState<string>("");
  const [loginError, setLoginError] = useState<string>("");
  const [loginLoading, setLoginLoading] = useState<boolean>(false);

  const [analysis, setAnalysis] = useState<StockAnalysisResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string>("");

  useEffect(() => {
    const checkToken = () => {
      const token = localStorage.getItem("access_token");
      setIsAuthenticated(!!token);
      setTokenChecked(true);
    };

    checkToken();

    // Listen to unauthorized responses from api utils
    const handleAuthFailed = () => {
      setIsAuthenticated(false);
    };

    window.addEventListener("auth-failed", handleAuthFailed);
    return () => {
      window.removeEventListener("auth-failed", handleAuthFailed);
    };
  }, []);

  const handleLoginSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoginLoading(true);
    setLoginError("");
    try {
      const token = await loginUser(username, password);
      localStorage.setItem("access_token", token);
      setIsAuthenticated(true);
    } catch (err: any) {
      setLoginError(err.message || "Invalid credentials");
    } finally {
      setLoginLoading(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem("access_token");
    setIsAuthenticated(false);
    setAnalysis(null);
  };

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

  if (!tokenChecked) {
    return (
      <div className="min-h-screen bg-slate-950 text-slate-100 flex items-center justify-center">
        <p className="text-slate-400">Loading platform...</p>
      </div>
    );
  }

  if (!isAuthenticated) {
    return (
      <main className="min-h-screen bg-slate-950 text-slate-100 flex items-center justify-center p-6">
        <div className="w-full max-w-md bg-slate-900 border border-slate-800 p-8 rounded-xl shadow-2xl">
          <div className="text-center mb-8">
            <h1 className="text-3xl font-extrabold text-white tracking-tight">AI Trading Bot</h1>
            <p className="text-slate-400 text-sm mt-2">Sign in to access real-time analysis & scanner</p>
          </div>
          <form onSubmit={handleLoginSubmit} className="space-y-6">
            <div>
              <label htmlFor="username" className="block text-sm font-medium text-slate-300">Username</label>
              <input
                id="username"
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="Rithvik"
                required
                className="mt-1 block w-full rounded-md bg-slate-950 border border-slate-800 text-slate-100 px-3 py-2 shadow-inner focus:outline-none focus:ring-2 focus:ring-emerald-500"
              />
            </div>
            <div>
              <label htmlFor="password" className="block text-sm font-medium text-slate-300">Password</label>
              <input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Password"
                required
                className="mt-1 block w-full rounded-md bg-slate-950 border border-slate-800 text-slate-100 px-3 py-2 shadow-inner focus:outline-none focus:ring-2 focus:ring-emerald-500"
              />
            </div>
            {loginError && <p className="text-rose-500 text-sm">{loginError}</p>}
            <button
              type="submit"
              disabled={loginLoading}
              className="w-full py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-emerald-600 hover:bg-emerald-500 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-emerald-500 disabled:opacity-50"
            >
              {loginLoading ? "Signing In..." : "Sign In"}
            </button>
          </form>
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-slate-950 text-slate-100 p-6 flex flex-col gap-6">
      <header className="flex justify-between items-center max-w-5xl mx-auto w-full border-b border-slate-900 pb-4">
        <h1 className="text-xl font-bold tracking-wider text-slate-100">AI TRADING COPILOT</h1>
        <button
          onClick={handleLogout}
          className="px-3 py-1.5 text-sm font-medium text-slate-300 border border-slate-800 rounded-md hover:bg-slate-900 hover:text-white transition-colors"
        >
          Logout
        </button>
      </header>
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
