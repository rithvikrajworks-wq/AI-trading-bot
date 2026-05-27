import React, { useState } from "react";
import { Search } from "lucide-react";
import { Input } from "./ui/input";
import { Button } from "./ui/button";

interface StockSearchProps {
  onSearch: (ticker: string) => void;
  isLoading: boolean;
}

export default function StockSearch({ onSearch, isLoading }: StockSearchProps) {
  const [ticker, setTicker] = useState("");
  const [error, setError] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const cleanTicker = ticker.trim().toUpperCase();

    if (!cleanTicker) {
      setError("Please enter a stock ticker symbol");
      return;
    }

    if (cleanTicker.length > 10) {
      setError("Ticker symbol cannot exceed 10 characters");
      return;
    }

    setError("");
    onSearch(cleanTicker);
  };

  const handleQuickClick = (symbol: string) => {
    setTicker(symbol);
    setError("");
    onSearch(symbol);
  };

  const quickTickers = ["NVDA", "AAPL", "MSFT", "TSLA", "AMD", "META"];

  return (
    <div className="w-full">
      <form onSubmit={handleSubmit} className="flex gap-2">
        <div className="relative flex-1">
          <span className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-500">
            <Search size={18} />
          </span>
          <Input
            type="text"
            placeholder="Search stock ticker (e.g. AAPL, NVDA, TSLA)..."
            value={ticker}
            onChange={(e) => {
              setTicker(e.target.value);
              if (error) setError("");
            }}
            error={!!error}
            className="pl-10 h-11"
            disabled={isLoading}
            maxLength={12}
          />
        </div>
        <Button type="submit" disabled={isLoading} className="h-11 px-6">
          {isLoading ? "Analyzing..." : "Analyze"}
        </Button>
      </form>

      {error && <p className="text-xs text-red-500 mt-1.5 ml-1">{error}</p>}

      {/* Quick Search Tickers list */}
      <div className="flex flex-wrap items-center gap-2 mt-3">
        <span className="text-xs text-slate-500 mr-1 select-none">Quick select:</span>
        {quickTickers.map((symbol) => (
          <button
            key={symbol}
            type="button"
            onClick={() => handleQuickClick(symbol)}
            disabled={isLoading}
            className="px-2.5 py-1 text-xs text-slate-400 bg-slate-900/60 border border-slate-800 rounded-md hover:bg-slate-800/60 hover:text-slate-200 transition-all active:scale-95 disabled:opacity-50"
          >
            {symbol}
          </button>
        ))}
      </div>
    </div>
  );
}
