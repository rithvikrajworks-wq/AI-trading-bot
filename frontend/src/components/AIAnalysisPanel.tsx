// frontend/src/components/AIAnalysisPanel.tsx

import React, { useState } from 'react';
import { fetchAIAnalysis, AIAnalysisResponse } from '@/utils/api';

/**
 * A premium‑styled panel that lets the user request an AI‑driven analysis for any ticker.
 * Uses glassmorphism, subtle gradients and smooth micro‑animations to match the app’s visual language.
 */
export default function AIAnalysisPanel() {
  const [ticker, setTicker] = useState('');
  const [analysis, setAnalysis] = useState<AIAnalysisResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleAnalyze = async () => {
    if (!ticker.trim()) return;
    setLoading(true);
    setError(null);
    setAnalysis(null);
    try {
      const result = await fetchAIAnalysis(ticker);
      setAnalysis(result);
    } catch (e: any) {
      setError(e.message || 'Unexpected error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="p-6 bg-white bg-opacity-20 backdrop-blur-lg rounded-xl shadow-lg border border-gray-200/30 transition-all hover:shadow-2xl">
      <h2 className="text-2xl font-semibold mb-4 text-gray-800">AI Stock Analyzer</h2>
      <div className="flex gap-2 mb-4">
        <input
          type="text"
          placeholder="Enter ticker (e.g., AAPL)"
          value={ticker}
          onChange={(e) => setTicker(e.target.value)}
          className="flex-1 px-4 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500 transition"
        />
        <button
          onClick={handleAnalyze}
          disabled={loading}
          className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 disabled:opacity-50 transition"
        >
          {loading ? 'Analyzing…' : 'Analyze'}
        </button>
      </div>
      {error && <p className="text-red-600">{error}</p>}
      {analysis && (
        <article className="mt-4 p-4 bg-white bg-opacity-30 rounded-md backdrop-blur-sm">
          <h3 className="text-xl font-medium mb-2">{analysis.ticker}</h3>
          <p className="text-gray-800 mb-1">{analysis.analysis}</p>
          <p className="text-gray-600">Confidence: <span className="font-semibold">{analysis.confidence}%</span></p>
        </article>
      )}
    </section>
  );
}
