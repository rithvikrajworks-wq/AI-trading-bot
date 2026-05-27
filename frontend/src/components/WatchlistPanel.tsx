// src/components/WatchlistPanel.tsx
"use client";

import React, { useEffect, useState, useCallback } from "react";
import { Search, Star, X } from "lucide-react"; // assuming lucide-react is installed

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
    <div className="glass p-4 max-w-md mx-auto mb-6">
      <h2 className="text-xl font-semibold text-slate-200 mb-3 flex items-center">
        <Star className="w-5 h-5 mr-2 text-emerald-400" /> Watchlist
      </h2>
      <div className="flex gap-2 mb-3">
        <input
          type="text"
          placeholder="Add ticker"
          value={newTicker}
          onChange={(e) => setNewTicker(e.target.value)}
          className="flex-1 px-2 py-1 bg-slate-800 text-slate-100 rounded"
          onKeyDown={(e) => e.key === "Enter" && addTicker()}
        />
        <button
          onClick={addTicker}
          className="px-3 py-1 bg-emerald-600 text-slate-100 rounded hover:bg-emerald-500 transition"
        >
          Add
        </button>
      </div>
      <input
        type="text"
        placeholder="Search…"
        value={filter}
        onChange={(e) => setFilter(e.target.value)}
        className="w-full px-2 py-1 mb-3 bg-slate-800 text-slate-100 rounded"
      />
      <ul className="space-y-1 max-h-60 overflow-y-auto">
        {filtered.map((item) => (
          <li
            key={item.ticker}
            className="flex items-center justify-between p-1 rounded hover:bg-slate-700 transition"
          >
            <span
              className="cursor-pointer text-slate-100"
              onClick={() => onSelect(item.ticker)}
            >
              {item.ticker}
            </span>
            <div className="flex items-center gap-2">
              <button
                onClick={() => togglePin(item.ticker)}
                className={`w-4 h-4 ${item.pinned ? "text-emerald-400" : "text-slate-400"}`}
              >
                <Star className="w-4 h-4" />
              </button>
              <button
                onClick={() => removeTicker(item.ticker)}
                className="text-rose-400 hover:text-rose-300 transition"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          </li>
        ))}
        {filtered.length === 0 && (
          <li className="text-slate-500 text-center py-2">No tickers found.</li>
        )}
      </ul>
    </div>
  );
}
