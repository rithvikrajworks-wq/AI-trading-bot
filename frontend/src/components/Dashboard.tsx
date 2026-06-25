"use client";

import React, { useEffect, useMemo, useState } from "react";
import StockSearch from "./StockSearch";
import AnalysisCard from "./AnalysisCard";
import TradingViewChart from "./TradingViewChart";
import TopOpportunities from "./TopOpportunities";
import AIChatPanel from "./AIChatPanel";
import WatchlistPanel from "./WatchlistPanel";
import {
  fetchStockAnalysis,
  loginUser,
  StockAnalysisResponse,
  runLowTokenCheck,
  LowTokenCheckResponse,
} from "../utils/api";
import { useLiveTicker } from "../hooks/useLiveTicker";
import {
  normalizeTickerForBackend,
  normalizeTickerForTradingView,
} from "../utils/tickerHelpers";

type DashboardTab = "analyze" | "opportunities" | "watchlist" | "chat";

// Market selector state
type Market = "US" | "INDIA";


export default function Dashboard() {
  const [market, setMarket] = useState<Market>("US");
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [tokenChecked, setTokenChecked] = useState(false);
  const [activeTab, setActiveTab] = useState<DashboardTab>("analyze");

  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [loginError, setLoginError] = useState("");
  const [loginLoading, setLoginLoading] = useState(false);

  const [analysis, setAnalysis] = useState<StockAnalysisResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [selectedTicker, setSelectedTicker] = useState<string | null>(null);
  const marketSelector = (
    <div className="flex items-center gap-2 mb-3">
      <label className="text-sm text-slate-400">Market:</label>
      <select
        value={market}
        onChange={(e) => setMarket(e.target.value as Market)}
        className="rounded bg-slate-800 px-2 py-1 text-sm text-slate-200"
      >
        <option value="US">US</option>
        <option value="INDIA">INDIA</option>
      </select>
    </div>
  );
  const [error, setError] = useState("");

  const [lowTokenLoading, setLowTokenLoading] = useState(false);
  const [lowTokenError, setLowTokenError] = useState("");
  const [lowTokenResult, setLowTokenResult] = useState<LowTokenCheckResponse | null>(null);

  const backendTicker = useMemo(
    () => (selectedTicker ? normalizeTickerForBackend(selectedTicker, market) : undefined),
    [selectedTicker, market]
  );
  const displayTicker = selectedTicker ?? null;
  const tradingViewTicker = useMemo(() => {
    if (selectedTicker) {
      return normalizeTickerForTradingView(selectedTicker);
    }
    if (analysis?.ticker) {
      return normalizeTickerForTradingView(analysis.ticker);
    }
    return "";
  }, [selectedTicker, analysis?.ticker]);
  const chatTicker = backendTicker ?? "";
  const { data: liveData, loading: liveLoading, error: liveError } = useLiveTicker(backendTicker ?? "");

  useEffect(() => {
    const token = localStorage.getItem("access_token");
    setIsAuthenticated(Boolean(token));
    setTokenChecked(true);

    const handleAuthFailed = () => {
      localStorage.removeItem("access_token");
      setIsAuthenticated(false);
      setAnalysis(null);
      setSelectedTicker(null);
    };

    window.addEventListener("auth-failed", handleAuthFailed);
    return () => window.removeEventListener("auth-failed", handleAuthFailed);
  }, []);

  const handleLoginSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoginLoading(true);
    setLoginError("");

    try {
      const token = await loginUser(username, password);
      localStorage.setItem("access_token", token);
      setIsAuthenticated(true);
      setUsername("");
      setPassword("");
    } catch (err: any) {
      setLoginError(err?.message || "Invalid username or password");
    } finally {
      setLoginLoading(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem("access_token");
    setIsAuthenticated(false);
    setAnalysis(null);
    setSelectedTicker(null);
    setLowTokenResult(null);
    setLowTokenError("");
    setError("");
    setActiveTab("analyze");
  };

  const handleSearch = (tickerValue: string) => {
    const cleanTicker = tickerValue.trim().toUpperCase();
    if (!cleanTicker) return;

    setSelectedTicker(cleanTicker);
    setAnalysis(null);
    setError("");
    setLowTokenResult(null);
    setLowTokenError("");
    setLoading(false);
    setActiveTab("analyze");
  };

  const handleNormalAnalysis = async () => {
    if (!selectedTicker) return;

    setLoading(true);
    setError("");

    try {
      const data = await fetchStockAnalysis(selectedTicker, market);
      setAnalysis(data);
    } catch (err: any) {
      console.error(err);
      setError(err?.message || "Failed to fetch analysis");
      setAnalysis(null);
    } finally {
      setLoading(false);
    }
  };

  const handleLowTokenCheck = async () => {
    if (!selectedTicker) return;

    setLowTokenLoading(true);
    setLowTokenError("");

    try {
      const result = await runLowTokenCheck(selectedTicker, market);
      setLowTokenResult(result);
    } catch (err: any) {
      console.error(err);
      setLowTokenError(err?.message || "Low token check failed");
      setLowTokenResult(null);
    } finally {
      setLowTokenLoading(false);
    }
  };

  const tabClass = (tab: DashboardTab) =>
    activeTab === tab
      ? "rounded-lg bg-emerald-600 px-4 py-2 text-sm font-semibold text-white shadow-lg shadow-emerald-950/30"
      : "rounded-lg border border-slate-800 bg-slate-950 px-4 py-2 text-sm font-medium text-slate-400 transition hover:border-slate-700 hover:bg-slate-900 hover:text-slate-100";

  if (!tokenChecked) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-slate-950 text-slate-100">
        <div className="rounded-xl border border-slate-800 bg-slate-900/70 px-6 py-4 shadow-xl">
          <p className="text-sm text-slate-400">Loading trading platform...</p>
        </div>
      </main>
    );
  }

  if (!isAuthenticated) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-slate-950 p-6 text-slate-100">
        <div className="w-full max-w-md rounded-2xl border border-slate-800 bg-slate-900/90 p-8 shadow-2xl">
          <div className="mb-8 text-center">
            <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-emerald-500/10 text-emerald-400">
              AI
            </div>
            <h1 className="text-3xl font-extrabold tracking-tight text-white">
              AI Trading Copilot
            </h1>
            <p className="mt-2 text-sm text-slate-400">
              Sign in to access analysis, scanner, watchlist, and chat.
            </p>
          </div>

          <form onSubmit={handleLoginSubmit} className="space-y-5">
            <div>
              <label htmlFor="username" className="mb-1 block text-sm font-medium text-slate-300">
                Username
              </label>
              <input
                id="username"
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="Username"
                required
                className="block w-full rounded-lg border border-slate-800 bg-slate-950 px-3 py-2.5 text-slate-100 shadow-inner outline-none transition focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/30"
              />
            </div>

            <div>
              <label htmlFor="password" className="mb-1 block text-sm font-medium text-slate-300">
                Password
              </label>
              <input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Password"
                required
                className="block w-full rounded-lg border border-slate-800 bg-slate-950 px-3 py-2.5 text-slate-100 shadow-inner outline-none transition focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/30"
              />
            </div>

            {loginError && (
              <div className="rounded-lg border border-rose-900/60 bg-rose-950/40 px-3 py-2 text-sm text-rose-300">
                {loginError}
              </div>
            )}

            <button
              type="submit"
              disabled={loginLoading}
              className="w-full rounded-lg bg-emerald-600 px-4 py-2.5 text-sm font-semibold text-white shadow-lg shadow-emerald-950/30 transition hover:bg-emerald-500 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {loginLoading ? "Signing in..." : "Sign in"}
            </button>
          </form>
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-slate-950 text-slate-100">
      <div className="mx-auto flex w-full max-w-7xl flex-col gap-6 px-4 py-5 sm:px-6 lg:px-8">
        <header className="flex flex-col gap-4 rounded-2xl border border-slate-800 bg-slate-900/70 p-5 shadow-xl lg:flex-row lg:items-center lg:justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.25em] text-emerald-400">
              AI Trading Platform
            </p>
            <h1 className="mt-1 text-2xl font-bold tracking-tight text-white">
              AI Trading Copilot
            </h1>
            <p className="mt-1 text-sm text-slate-400">
              Analyze stocks, scan opportunities, manage a watchlist, and chat with your AI assistant.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <div className="rounded-lg border border-slate-800 bg-slate-950 px-3 py-2 text-xs text-slate-400">
              Logged in as <span className="font-semibold text-slate-200">Rithvik(admin)</span>
            </div>
            <button
              onClick={handleLogout}
              className="rounded-lg border border-slate-700 px-4 py-2 text-sm font-medium text-slate-300 transition hover:border-rose-500/60 hover:bg-rose-950/30 hover:text-rose-200"
            >
              Logout
            </button>
          </div>
        </header>

        <nav className="flex flex-wrap gap-3 rounded-2xl border border-slate-800 bg-slate-900/70 p-3 shadow-xl">
          <button onClick={() => setActiveTab("analyze")} className={tabClass("analyze")}>
            Analyze
          </button>
          <button onClick={() => setActiveTab("opportunities")} className={tabClass("opportunities")}>
            Opportunities
          </button>
          <button onClick={() => setActiveTab("watchlist")} className={tabClass("watchlist")}>
            Watchlist
          </button>
          <button onClick={() => setActiveTab("chat")} className={tabClass("chat")}>
            Chat
          </button>
        </nav>

        {activeTab === "analyze" && (
          <section className="grid gap-6 xl:grid-cols-[1.45fr_1fr]">
            {marketSelector}
        <div className="flex flex-col gap-6">
              <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-4 shadow-xl">
                <StockSearch onSearch={handleSearch} isLoading={loading} />
                {error && (
                  <div className="mt-3 rounded-lg border border-rose-900/60 bg-rose-950/40 px-3 py-2 text-sm text-rose-300">
                    {error}
                  </div>
                )}
              </div>

              {selectedTicker && !analysis && !loading && (
                <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-4 shadow-xl">
                  <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                    <div>
                      <p className="text-xs uppercase tracking-[0.2em] text-slate-500">Selected ticker</p>
                      <h2 className="text-xl font-bold text-white">{selectedTicker}</h2>
                    </div>

                    {liveLoading ? (
                      <span className="text-sm text-slate-400">Loading live price...</span>
                    ) : liveError ? (
                      <span className="text-sm text-rose-400">{liveError}</span>
                    ) : liveData ? (
                      <div className="text-right">
                        <p className="text-2xl font-bold text-emerald-400">
                          ${liveData.price.toFixed(2)}
                        </p>
                        <p className={liveData.change >= 0 ? "text-sm text-emerald-300" : "text-sm text-rose-300"}>
                          {liveData.change >= 0 ? "▲" : "▼"} {liveData.change.toFixed(2)} (
                          {liveData.change_percent.toFixed(2)}%)
                        </p>
                      </div>
                    ) : (
                      <span className="text-sm text-slate-500">No live data</span>
                    )}
                  </div>

                  <div className="mt-4">
                    <TradingViewChart ticker={tradingViewTicker ?? ""} />
                  </div>

                  <div className="mt-6">
                    <h3 className="mb-3 text-sm uppercase tracking-[0.2em] text-slate-500">
                      Feature Icon Modes
                    </h3>

                    <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                      <button
                        onClick={handleLowTokenCheck}
                        disabled={lowTokenLoading}
                        className="rounded-xl border border-amber-700/50 bg-amber-950/30 p-4 text-left transition hover:border-amber-500 disabled:cursor-not-allowed disabled:opacity-70"
                      >
                        <div className="text-2xl">⚡</div>
                        <p className="mt-2 font-semibold text-amber-200">
                          {lowTokenLoading ? "Checking..." : "Low Token Check"}
                        </p>
                        <p className="mt-1 text-xs text-slate-400">
                          Quick cheap check to decide if full analysis is worth running.
                        </p>
                      </button>

                      <button
                        onClick={handleNormalAnalysis}
                        disabled={loading}
                        className="rounded-xl border border-emerald-700/50 bg-emerald-950/30 p-4 text-left transition hover:border-emerald-500 disabled:cursor-not-allowed disabled:opacity-70"
                      >
                        <div className="text-2xl">🧠</div>
                        <p className="mt-2 font-semibold text-emerald-200">
                          {loading ? "Analyzing..." : "Normal Analysis"}
                        </p>
                        <p className="mt-1 text-xs text-slate-400">
                          Full AI-native stock report using the existing analysis engine.
                        </p>
                      </button>

                      <button
                        className="cursor-not-allowed rounded-xl border border-slate-800 bg-slate-950/60 p-4 text-left opacity-60"
                        disabled
                      >
                        <div className="text-2xl">🧑‍⚖️</div>
                        <p className="mt-2 font-semibold text-slate-300">Trading Committee</p>
                        <p className="mt-1 text-xs text-slate-500">
                          Bull, bear, risk manager, and final decision in one call. Coming soon.
                        </p>
                      </button>

                      <button
                        className="cursor-not-allowed rounded-xl border border-slate-800 bg-slate-950/60 p-4 text-left opacity-60"
                        disabled
                      >
                        <div className="text-2xl">📐</div>
                        <p className="mt-2 font-semibold text-slate-300">Risk/Reward Plan</p>
                        <p className="mt-1 text-xs text-slate-500">
                          Entry, stop loss, targets, invalidation, and risk/reward. Coming soon.
                        </p>
                      </button>

                      <button
                        onClick={() => setActiveTab("chat")}
                        className="rounded-xl border border-sky-700/50 bg-sky-950/30 p-4 text-left transition hover:border-sky-500 sm:col-span-2"
                      >
                        <div className="text-2xl">💬</div>
                        <p className="mt-2 font-semibold text-sky-200">Chat With Stock</p>
                        <p className="mt-1 text-xs text-slate-400">
                          Ask deeper questions about this ticker.
                        </p>
                      </button>
                    </div>

                    {lowTokenError && (
                      <p className="mt-3 rounded-lg border border-rose-900/60 bg-rose-950/40 px-3 py-2 text-sm text-rose-300">
                        {lowTokenError}
                      </p>
                    )}

                    {lowTokenResult && (
                      <div className="mt-4 rounded-2xl border border-slate-800 bg-slate-950/70 p-4 text-sm text-slate-200">
                        <p>
                          <strong>Worth analysis:</strong>{" "}
                          {lowTokenResult.worth_analysis ? "Yes" : "No"}
                        </p>
                        <p>
                          <strong>Setup quality:</strong>{" "}
                          {lowTokenResult.estimated_setup_quality}
                        </p>
                        <p>
                          <strong>Suggested next mode:</strong>{" "}
                          {lowTokenResult.suggested_next_mode}
                        </p>
                        <p>
                          <strong>Reason:</strong> {lowTokenResult.reason}
                        </p>

                        {lowTokenResult.suggested_next_mode === "normal_analysis" && (
                          <p className="mt-3 text-emerald-300">
                            Recommended next: Normal Analysis
                          </p>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              )}

              {loading && (
                <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-8 text-center shadow-xl">
                  <p className="text-sm text-slate-400">Fetching analysis...</p>
                </div>
              )}

              {!selectedTicker && !analysis && !loading && (
                <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-8 text-center shadow-xl">
                  <div className="mx-auto mb-5 flex h-14 w-14 items-center justify-center rounded-2xl bg-emerald-500/10 text-lg font-bold text-emerald-400">
                    AI
                  </div>
                  <h2 className="text-2xl font-bold text-white">Start with a stock ticker</h2>
                  <p className="mx-auto mt-3 max-w-xl text-sm leading-6 text-slate-400">
                    Search for a stock to open its profile first. Then choose Low Token Check,
                    Normal Analysis, Trading Committee, Risk/Reward Plan, or Chat.
                  </p>

                  <div className="mt-6 flex flex-wrap justify-center gap-3">
                    <button
                      onClick={() => handleSearch("AAPL")}
                      className="rounded-lg bg-slate-800 px-4 py-2 text-sm text-slate-200 transition hover:bg-slate-700"
                    >
                      Open AAPL
                    </button>
                    <button
                      onClick={() => handleSearch("MSFT")}
                      className="rounded-lg bg-slate-800 px-4 py-2 text-sm text-slate-200 transition hover:bg-slate-700"
                    >
                      Open MSFT
                    </button>
                    <button
                      onClick={() => handleSearch("NVDA")}
                      className="rounded-lg bg-slate-800 px-4 py-2 text-sm text-slate-200 transition hover:bg-slate-700"
                    >
                      Open NVDA
                    </button>
                  </div>
                </div>
              )}

              {analysis && (
                <>
                  <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-4 shadow-xl">
                    <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                      <div>
                        <p className="text-xs uppercase tracking-[0.2em] text-slate-500">Live ticker</p>
                        <h2 className="text-xl font-bold text-white">{displayTicker ?? "Selected stock"}</h2>
                      </div>

                      {liveLoading ? (
                        <span className="text-sm text-slate-400">Loading live price...</span>
                      ) : liveError ? (
                        <span className="text-sm text-rose-400">{liveError}</span>
                      ) : liveData ? (
                        <div className="text-right">
                          <p className="text-2xl font-bold text-emerald-400">
                            ${liveData.price.toFixed(2)}
                          </p>
                          <p className={liveData.change >= 0 ? "text-sm text-emerald-300" : "text-sm text-rose-300"}>
                            {liveData.change >= 0 ? "▲" : "▼"} {liveData.change.toFixed(2)} (
                            {liveData.change_percent.toFixed(2)}%)
                          </p>
                        </div>
                      ) : (
                        <span className="text-sm text-slate-500">No live data</span>
                      )}
                    </div>
                  </div>

                  <AnalysisCard data={analysis} />

                  <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-4 shadow-xl">
                    <div className="mb-3">
                      <p className="text-xs uppercase tracking-[0.2em] text-slate-500">Chart</p>
                      <h3 className="text-lg font-semibold text-white">{tradingViewTicker} TradingView</h3>
                    </div>
                    <TradingViewChart ticker={tradingViewTicker} />
                  </div>
                </>
              )}
            </div>

            <aside className="flex flex-col gap-6">
              <TopOpportunities />
              <WatchlistPanel onSelect={handleSearch} />
            </aside>
          </section>
        )}

        {activeTab === "opportunities" && (
          <section className="grid gap-6 lg:grid-cols-[1fr_0.8fr]">
            <TopOpportunities />
            <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-6 shadow-xl">
              <p className="text-xs uppercase tracking-[0.2em] text-slate-500">Scanner guide</p>
              <h2 className="mt-2 text-xl font-bold text-white">How to use opportunities</h2>
              <p className="mt-3 text-sm leading-6 text-slate-400">
                Use this section to review ranked AI opportunities. Look at confidence,
                breakout probability, bull/base/bear probabilities, ranking explanation, and risks.
              </p>
            </div>
          </section>
        )}

        {activeTab === "watchlist" && (
          <section className="grid gap-6 lg:grid-cols-[0.8fr_1fr]">
            <WatchlistPanel onSelect={handleSearch} />
            <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-6 shadow-xl">
              <p className="text-xs uppercase tracking-[0.2em] text-slate-500">Watchlist</p>
              <h2 className="mt-2 text-xl font-bold text-white">Track stocks before analyzing</h2>
              <p className="mt-3 text-sm leading-6 text-slate-400">
                Use the watchlist to keep tickers ready. Selecting a stock will send it to the Analyze tab
                and open the stock profile first.
              </p>
              <div className="mt-5 rounded-xl border border-slate-800 bg-slate-950/70 p-4">
                <p className="text-sm font-semibold text-slate-200">Current selected ticker</p>
                <p className="mt-1 text-sm text-slate-400">
                  {displayTicker ? displayTicker : "No ticker selected yet."}
                </p>
              </div>
            </div>
          </section>
        )}

        {activeTab === "chat" && (
          <section className="grid gap-6 lg:grid-cols-[1fr_0.8fr]">
            <AIChatPanel ticker={chatTicker} />
            <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-6 shadow-xl">
              <p className="text-xs uppercase tracking-[0.2em] text-slate-500">AI chat</p>
              <h2 className="mt-2 text-xl font-bold text-white">Ask deeper questions</h2>
              <p className="mt-3 text-sm leading-6 text-slate-400">
                After selecting a ticker, use chat to ask about risk, entry timing, stop loss,
                trend strength, holding period, or bull versus bear cases.
              </p>
              <div className="mt-5 rounded-xl border border-slate-800 bg-slate-950/70 p-4">
                <p className="text-sm font-semibold text-slate-200">Chat context</p>
                <p className="mt-1 text-sm text-slate-400">
                  {displayTicker ? `Currently discussing ${displayTicker}.` : "Select a stock first to give chat a ticker context."}
                </p>
              </div>
            </div>
          </section>
        )}
      </div>
    </main>
  );
}