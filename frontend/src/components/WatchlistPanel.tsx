// src/components/WatchlistPanel.tsx
"use client";

import React, { useEffect, useState, useCallback } from "react";
import { Search, Star, X, Plus } from "lucide-react";
import { Card, CardHeader, CardTitle, CardContent } from "./ui/card";

interface WatchlistItem {
  ticker: string;
  pinned: boolean;
}

interface WatchlistPanelProps {
  onSelect: (ticker: string) => void;
}

const STORAGE_KEY = "watchlist";

export default function WatchlistPanel({ onSelect }: WatchlistPanelProps) {
  const [items, setItems] = useState<WatchlistItem[]>([]);
  const [filter, setFilter] = useState("");
  const [newTicker, setNewTicker] = useState("");

  // Load from localStorage on mount
  useEffect(() => {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored) {
      try {
        setItems(JSON.parse(stored));
      } catch {}
    }
  }, []);

  // Persist to localStorage whenever items change
  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(items));
  }, [items]);

  const addTicker = useCallback(() => {
    const cleaned = newTicker.trim().toUpperCase();
    if (!cleaned) return;
    if (items.find((i) => i.ticker === cleaned)) {
      setNewTicker("");
      return;
    }
    setItems((prev) => [...prev, { ticker: cleaned, pinned: false }]);
    setNewTicker("");
  }, [newTicker, items]);

  const removeTicker = useCallback((ticker: string) => {
    setItems((prev) => prev.filter((i) => i.ticker !== ticker));
  }, []);

  const togglePin = useCallback((ticker: string) => {
    setItems((prev) =>
      prev.map((i) => (i.ticker === ticker ? { ...i, pinned: !i.pinned } : i))
    );
  }, []);

  const filtered = items
    .filter((i) => i.ticker.includes(filter.toUpperCase()))
    .sort((a, b) => Number(b.pinned) - Number(a.pinned));

  return (
    <Card className="w-full">
      <CardHeader className="flex flex-row items-center justify-between py-4">
        <CardTitle className="text-lg font-bold flex items-center gap-2">
          <Star className="w-5 h-5 text-emerald-400 fill-emerald-400/20" />
          <span>My Watchlist</span>
        </CardTitle>
        <span className="text-xs text-slate-500 font-semibold uppercase tracking-wider">
          {items.length} Tickers
        </span>
      </CardHeader>
      
      <CardContent className="space-y-4">
        {/* Add Ticker Input */}
        <div className="flex gap-2">
          <div className="relative flex-1">
            <input
              type="text"
              placeholder="Add symbol (e.g. AAPL)..."
              value={newTicker}
              onChange={(e) => setNewTicker(e.target.value)}
              className="w-full rounded-lg border border-slate-800 bg-slate-950/80 px-3 py-2 text-sm text-slate-100 shadow-inner outline-none transition focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/30"
              onKeyDown={(e) => e.key === "Enter" && addTicker()}
            />
          </div>
          <button
            onClick={addTicker}
            className="flex items-center gap-1 rounded-lg bg-emerald-600 px-4 py-2 text-sm font-semibold text-white shadow-lg shadow-emerald-950/30 transition hover:bg-emerald-500 active:scale-95"
          >
            <Plus size={16} />
            <span>Add</span>
          </button>
        </div>

        {/* Filter Input */}
        <div className="relative">
          <span className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-500">
            <Search size={14} />
          </span>
          <input
            type="text"
            placeholder="Filter watchlist..."
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            className="w-full rounded-lg border border-slate-800 bg-slate-950/80 pl-9 pr-3 py-1.5 text-xs text-slate-200 outline-none transition focus:border-slate-700"
          />
        </div>

        {/* Watchlist Tickers List */}
        <ul className="space-y-2 max-h-64 overflow-y-auto pr-1">
          {filtered.map((item) => (
            <li
              key={item.ticker}
              className={`flex items-center justify-between p-2.5 rounded-xl border border-slate-800/40 bg-slate-900/20 hover:bg-slate-800/40 hover:border-slate-700/60 transition-all duration-200 ${
                item.pinned ? "border-emerald-900/30 bg-emerald-950/5" : ""
              }`}
            >
              <span
                className="cursor-pointer text-sm font-semibold text-slate-200 hover:text-emerald-400 transition-colors"
                onClick={() => onSelect(item.ticker)}
              >
                {item.ticker}
              </span>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => togglePin(item.ticker)}
                  className={`p-1 rounded-md hover:bg-slate-800 transition-colors ${
                    item.pinned ? "text-emerald-400" : "text-slate-500 hover:text-slate-300"
                  }`}
                  title={item.pinned ? "Unpin ticker" : "Pin ticker"}
                >
                  <Star className={`w-4 h-4 ${item.pinned ? "fill-emerald-400/20" : ""}`} />
                </button>
                <button
                  onClick={() => removeTicker(item.ticker)}
                  className="p-1 rounded-md text-slate-500 hover:text-rose-400 hover:bg-rose-950/20 transition-colors"
                  title="Remove from watchlist"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            </li>
          ))}
          {filtered.length === 0 && (
            <li className="text-slate-500 text-center py-6 text-xs select-none">
              No tickers in watchlist.
            </li>
          )}
        </ul>
      </CardContent>
    </Card>
  );
}
