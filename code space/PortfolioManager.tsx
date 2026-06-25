"use client";
/**
 * File path: Tradingbotmk1/frontend/src/components/PortfolioManager.tsx
 *
 * Portfolio Manager UI – dark theme, no AI calls, no auto-refresh.
 * Drop this component anywhere in your dashboard layout.
 */

import { useEffect, useState, useCallback } from "react";
import {
  fetchHoldings,
  fetchSummary,
  createHolding,
  updateHolding,
  deleteHolding,
  Holding,
  HoldingCreate,
  HoldingUpdate,
  HoldingStatus,
  Market,
  PortfolioSummary,
} from "@/utils/portfolioApi";

// ---------------------------------------------------------------------------
// Formatting helpers
// ---------------------------------------------------------------------------

const fmt = (n: number, dec = 2) =>
  n.toLocaleString("en-US", { minimumFractionDigits: dec, maximumFractionDigits: dec });

const pct = (n: number) => `${n >= 0 ? "+" : ""}${fmt(n)}%`;

const plColor = (n: number) =>
  n > 0 ? "text-emerald-400" : n < 0 ? "text-red-400" : "text-slate-400";

// ---------------------------------------------------------------------------
// Empty form state
// ---------------------------------------------------------------------------

const emptyForm = (): HoldingCreate => ({
  ticker: "",
  market: "US",
  quantity: 0,
  average_cost: 0,
  current_price: 0,
  status: "holding",
  notes: "",
});

// ---------------------------------------------------------------------------
// Sub-component: Summary bar
// ---------------------------------------------------------------------------

function SummaryBar({ s }: { s: PortfolioSummary }) {
  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
      {[
        { label: "Invested", value: `$${fmt(s.total_invested)}`, sub: null },
        { label: "Current Value", value: `$${fmt(s.total_current_value)}`, sub: null },
        {
          label: "Total P/L",
          value: `$${fmt(s.total_profit_loss)}`,
          sub: pct(s.total_profit_loss_pct),
          color: plColor(s.total_profit_loss),
        },
        {
          label: "Positions",
          value: `${s.holdings_count + s.watching_count + s.sold_count}`,
          sub: `${s.holdings_count} active`,
          color: "text-slate-300",
        },
      ].map((card) => (
        <div
          key={card.label}
          className="bg-slate-800 border border-slate-700 rounded-xl p-4"
        >
          <p className="text-xs text-slate-500 uppercase tracking-widest mb-1">
            {card.label}
          </p>
          <p className={`text-xl font-semibold ${card.color ?? "text-white"}`}>
            {card.value}
          </p>
          {card.sub && (
            <p className={`text-sm mt-0.5 ${card.color ?? "text-slate-400"}`}>
              {card.sub}
            </p>
          )}
        </div>
      ))}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Sub-component: Add / Edit form
// ---------------------------------------------------------------------------

interface FormProps {
  initial: HoldingCreate | null; // null → add mode
  editTicker: string | null;
  onSave: () => void;
  onCancel: () => void;
}

function HoldingForm({ initial, editTicker, onSave, onCancel }: FormProps) {
  const [form, setForm] = useState<HoldingCreate>(initial ?? emptyForm());
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const set = (field: keyof HoldingCreate, value: string | number) =>
    setForm((f) => ({ ...f, [field]: value }));

  const handleSubmit = async () => {
    setError(null);
    if (!form.ticker.trim()) return setError("Ticker is required.");
    if (form.quantity <= 0) return setError("Quantity must be > 0.");
    if (form.average_cost <= 0) return setError("Average cost must be > 0.");

    setLoading(true);
    try {
      if (editTicker) {
        const patch: HoldingUpdate = {
          market: form.market,
          quantity: form.quantity,
          average_cost: form.average_cost,
          current_price: form.current_price,
          status: form.status,
          notes: form.notes,
        };
        await updateHolding(editTicker, patch);
      } else {
        await createHolding({ ...form, ticker: form.ticker.toUpperCase().trim() });
      }
      onSave();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Request failed");
    } finally {
      setLoading(false);
    }
  };

  const inputCls =
    "w-full bg-slate-900 border border-slate-600 rounded-lg px-3 py-2 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500";
  const labelCls = "block text-xs text-slate-400 mb-1";

  return (
    <div className="bg-slate-800 border border-slate-700 rounded-xl p-5 mb-6">
      <h3 className="text-sm font-semibold text-white mb-4">
        {editTicker ? `Edit ${editTicker}` : "Add Position"}
      </h3>

      <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
        <div>
          <label className={labelCls}>Ticker *</label>
          <input
            className={inputCls}
            placeholder="AAPL"
            value={form.ticker}
            disabled={!!editTicker}
            onChange={(e) => set("ticker", e.target.value)}
          />
        </div>

        <div>
          <label className={labelCls}>Market *</label>
          <select
            className={inputCls}
            value={form.market}
            onChange={(e) => set("market", e.target.value as Market)}
          >
            <option value="US">US</option>
            <option value="INDIA">INDIA</option>
          </select>
        </div>

        <div>
          <label className={labelCls}>Status</label>
          <select
            className={inputCls}
            value={form.status}
            onChange={(e) => set("status", e.target.value as HoldingStatus)}
          >
            <option value="holding">Holding</option>
            <option value="watching">Watching</option>
            <option value="sold">Sold</option>
          </select>
        </div>

        <div>
          <label className={labelCls}>Quantity *</label>
          <input
            type="number"
            className={inputCls}
            placeholder="0"
            value={form.quantity || ""}
            onChange={(e) => set("quantity", parseFloat(e.target.value) || 0)}
          />
        </div>

        <div>
          <label className={labelCls}>Avg Cost *</label>
          <input
            type="number"
            className={inputCls}
            placeholder="0.00"
            value={form.average_cost || ""}
            onChange={(e) => set("average_cost", parseFloat(e.target.value) || 0)}
          />
        </div>

        <div>
          <label className={labelCls}>Current Price</label>
          <input
            type="number"
            className={inputCls}
            placeholder="0.00"
            value={form.current_price || ""}
            onChange={(e) => set("current_price", parseFloat(e.target.value) || 0)}
          />
        </div>

        <div className="col-span-2 md:col-span-3">
          <label className={labelCls}>Notes</label>
          <input
            className={inputCls}
            placeholder="Optional notes…"
            value={form.notes ?? ""}
            onChange={(e) => set("notes", e.target.value)}
          />
        </div>
      </div>

      {error && (
        <p className="text-red-400 text-xs mt-3">{error}</p>
      )}

      <div className="flex gap-3 mt-4">
        <button
          onClick={handleSubmit}
          disabled={loading}
          className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white text-sm rounded-lg transition-colors"
        >
          {loading ? "Saving…" : editTicker ? "Save Changes" : "Add Position"}
        </button>
        <button
          onClick={onCancel}
          className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-slate-300 text-sm rounded-lg transition-colors"
        >
          Cancel
        </button>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Status badge
// ---------------------------------------------------------------------------

const statusBadge: Record<HoldingStatus, string> = {
  holding: "bg-emerald-900 text-emerald-300",
  watching: "bg-amber-900 text-amber-300",
  sold: "bg-slate-700 text-slate-400",
};

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------

export default function PortfolioManager() {
  const [holdings, setHoldings] = useState<Holding[]>([]);
  const [summary, setSummary] = useState<PortfolioSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [showForm, setShowForm] = useState(false);
  const [editTarget, setEditTarget] = useState<Holding | null>(null);

  // -------------------------------------------------------------------------
  // Load data
  // -------------------------------------------------------------------------

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [h, s] = await Promise.all([fetchHoldings(), fetchSummary()]);
      setHoldings(h);
      setSummary(s);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to load portfolio");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  // -------------------------------------------------------------------------
  // Delete
  // -------------------------------------------------------------------------

  const handleDelete = async (ticker: string) => {
    if (!confirm(`Remove ${ticker} from your portfolio?`)) return;
    try {
      await deleteHolding(ticker);
      await load();
    } catch (e: unknown) {
      alert(e instanceof Error ? e.message : "Delete failed");
    }
  };

  // -------------------------------------------------------------------------
  // Render
  // -------------------------------------------------------------------------

  return (
    <div className="bg-slate-900 text-white p-6 rounded-2xl min-h-screen">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-xl font-bold text-white tracking-tight">Portfolio</h2>
          <p className="text-xs text-slate-500 mt-0.5">Your holdings at a glance</p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={load}
            className="px-3 py-2 bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-300 text-sm rounded-lg transition-colors"
          >
            ↻ Refresh
          </button>
          {!showForm && !editTarget && (
            <button
              onClick={() => setShowForm(true)}
              className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white text-sm rounded-lg transition-colors"
            >
              + Add Position
            </button>
          )}
        </div>
      </div>

      {/* Summary */}
      {summary && <SummaryBar s={summary} />}

      {/* Add form */}
      {showForm && !editTarget && (
        <HoldingForm
          initial={null}
          editTicker={null}
          onSave={() => { setShowForm(false); load(); }}
          onCancel={() => setShowForm(false)}
        />
      )}

      {/* Edit form */}
      {editTarget && (
        <HoldingForm
          initial={{
            ticker: editTarget.ticker,
            market: editTarget.market,
            quantity: editTarget.quantity,
            average_cost: editTarget.average_cost,
            current_price: editTarget.current_price,
            status: editTarget.status,
            notes: editTarget.notes ?? "",
          }}
          editTicker={editTarget.ticker}
          onSave={() => { setEditTarget(null); load(); }}
          onCancel={() => setEditTarget(null)}
        />
      )}

      {/* State messages */}
      {loading && (
        <p className="text-slate-500 text-sm text-center py-8">Loading holdings…</p>
      )}
      {error && (
        <p className="text-red-400 text-sm text-center py-8">{error}</p>
      )}

      {/* Holdings table */}
      {!loading && !error && holdings.length === 0 && (
        <div className="text-center py-16 border border-dashed border-slate-700 rounded-xl">
          <p className="text-slate-500 text-sm">No positions yet.</p>
          <p className="text-slate-600 text-xs mt-1">Click "Add Position" to get started.</p>
        </div>
      )}

      {!loading && holdings.length > 0 && (
        <div className="overflow-x-auto">
          <table className="w-full text-sm border-collapse">
            <thead>
              <tr className="text-xs text-slate-500 uppercase tracking-widest border-b border-slate-700">
                {["Ticker", "Market", "Qty", "Avg Cost", "Current", "Invested", "Value", "P/L", "P/L %", "Status", ""].map(
                  (h) => (
                    <th key={h} className="text-left py-3 px-2 font-medium">
                      {h}
                    </th>
                  )
                )}
              </tr>
            </thead>
            <tbody>
              {holdings.map((h) => (
                <tr
                  key={h.ticker}
                  className="border-b border-slate-800 hover:bg-slate-800/50 transition-colors"
                >
                  <td className="py-3 px-2 font-semibold text-white">{h.ticker}</td>
                  <td className="py-3 px-2 text-slate-400">{h.market}</td>
                  <td className="py-3 px-2 text-slate-300">{fmt(h.quantity, 4)}</td>
                  <td className="py-3 px-2 text-slate-300">{fmt(h.average_cost)}</td>
                  <td className="py-3 px-2 text-slate-300">{fmt(h.current_price)}</td>
                  <td className="py-3 px-2 text-slate-400">{fmt(h.invested_amount)}</td>
                  <td className="py-3 px-2 text-slate-300">{fmt(h.current_value)}</td>
                  <td className={`py-3 px-2 font-medium ${plColor(h.profit_loss)}`}>
                    {h.profit_loss >= 0 ? "+" : ""}{fmt(h.profit_loss)}
                  </td>
                  <td className={`py-3 px-2 font-medium ${plColor(h.profit_loss_pct)}`}>
                    {pct(h.profit_loss_pct)}
                  </td>
                  <td className="py-3 px-2">
                    <span
                      className={`text-xs px-2 py-0.5 rounded-full font-medium ${statusBadge[h.status]}`}
                    >
                      {h.status}
                    </span>
                  </td>
                  <td className="py-3 px-2">
                    <div className="flex gap-2">
                      <button
                        onClick={() => { setEditTarget(h); setShowForm(false); }}
                        className="text-xs text-indigo-400 hover:text-indigo-300 transition-colors"
                      >
                        Edit
                      </button>
                      <button
                        onClick={() => handleDelete(h.ticker)}
                        className="text-xs text-red-500 hover:text-red-400 transition-colors"
                      >
                        Delete
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
