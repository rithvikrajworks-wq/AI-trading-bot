import React from "react";
import { 
  TrendingUp, 
  TrendingDown, 
  Check, 
  AlertTriangle,
  Info,
  DollarSign
} from "lucide-react";
import { StockAnalysisResponse } from "@/utils/api";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "./ui/card";
import { Badge } from "./ui/badge";

interface AnalysisCardProps {
  data: StockAnalysisResponse;
}

export default function AnalysisCard({ data }: AnalysisCardProps) {
  const isBuy = data.signal === "BUY";
  const isSell = data.signal === "SELL";
  const isHold = data.signal === "HOLD";

  // Dynamic colors based on recommendation signal
  let signalBadgeVariant: "success" | "danger" | "warning" = "warning";
  let signalGlowColor = "border-amber-800/40 text-amber-400 bg-amber-950/20";
  let confidenceBarColor = "bg-gradient-to-r from-amber-600 to-amber-400";
  
  if (isBuy) {
    signalBadgeVariant = "success";
    signalGlowColor = "border-emerald-800/40 text-emerald-400 bg-emerald-950/20";
    confidenceBarColor = "bg-gradient-to-r from-emerald-600 to-emerald-400";
  } else if (isSell) {
    signalBadgeVariant = "danger";
    signalGlowColor = "border-rose-800/40 text-rose-400 bg-rose-950/20";
    confidenceBarColor = "bg-gradient-to-r from-rose-600 to-rose-400";
  }

  // RSI sub-status evaluation
  let rsiStatus = "Neutral";
  let rsiStatusColor = "text-slate-400";
  if (data.rsi < 30) {
    rsiStatus = "Oversold";
    rsiStatusColor = "text-emerald-400";
  } else if (data.rsi < 40) {
    rsiStatus = "Undervalued";
    rsiStatusColor = "text-emerald-500/70";
  } else if (data.rsi > 70) {
    rsiStatus = "Overbought";
    rsiStatusColor = "text-rose-400";
  } else if (data.rsi > 60) {
    rsiStatus = "Overvalued";
    rsiStatusColor = "text-rose-500/70";
  }

  let glowClass = "";
  if (isBuy) glowClass = "glow-emerald";
  else if (isSell) glowClass = "glow-rose";
  else if (isHold) glowClass = "glow-amber";

  return (
    <Card className={`w-full h-full flex flex-col ${glowClass}`}>
      <CardHeader className="flex flex-row items-center justify-between gap-4 py-4">
        <div>
          <CardTitle className="text-2xl font-bold flex items-center gap-2">
            <span>{data.ticker}</span>
            <span className="text-base font-normal text-slate-500">Analysis Summary</span>
          </CardTitle>
          <CardDescription>
            Last Close: <span className="font-semibold text-slate-200">{typeof data.price === "number" ? data.price.toLocaleString(undefined, { minimumFractionDigits: 2 }) : "N/A"}</span>
          </CardDescription>
        </div>

        {/* Floating Recommendation Signal Badge */}
        <Badge variant={signalBadgeVariant} glow className="text-sm px-4 py-1.5 font-bold tracking-wider">
          {data.signal}
        </Badge>
      </CardHeader>

      <CardContent className="flex-1 space-y-6">
        {/* Fallback Detection Alert */}
        {((data.summary && data.summary.includes("AI analysis unavailable")) || 
          (data.warnings && data.warnings.some(w => w.includes("AI service failure")))) && (
          <div className="bg-rose-950/30 border border-rose-800/40 text-rose-300 p-3 rounded-lg flex items-center gap-2 text-xs">
            <AlertTriangle size={16} />
            <span>AI analysis unavailable. Showing fallback response.</span>
          </div>
        )}

        {/* Quick Verdict Stats Grid */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 bg-slate-950/20 border border-slate-800/40 rounded-lg p-3">
          <div className="flex flex-col">
            <span className="text-[10px] font-medium text-slate-500 uppercase">Signal</span>
            <span className={`text-base font-bold capitalize ${
              isBuy ? "text-emerald-400" : isSell ? "text-rose-400" : "text-amber-400"
            }`}>{data.signal}</span>
          </div>
          <div className="flex flex-col">
            <span className="text-[10px] font-medium text-slate-500 uppercase">Confidence</span>
            <span className="text-base font-bold text-slate-100">{data.confidence}%</span>
          </div>
          <div className="flex flex-col">
            <span className="text-[10px] font-medium text-slate-500 uppercase">Breakout Prob.</span>
            <span className="text-base font-bold text-emerald-400">{data.breakout_probability ?? "N/A"}%</span>
          </div>
          <div className="flex flex-col">
            <span className="text-[10px] font-medium text-slate-500 uppercase">Risk Level</span>
            <span className="text-base font-bold text-slate-100 capitalize">{data.risk_level ?? "N/A"}</span>
          </div>
        </div>

        {/* Confidence score gauge bar */}
        <div className="bg-slate-950/40 border border-slate-800/40 rounded-lg p-4">
          <div className="flex justify-between items-center mb-1">
            <span className="text-xs font-medium text-slate-400 flex items-center gap-1.5 select-none">
               Recommendation Confidence
            </span>
            <span className="text-sm font-bold text-slate-200">{data.confidence}%</span>
          </div>
          <div className="w-full bg-slate-950/80 h-2.5 rounded-full overflow-hidden border border-slate-800/50 mt-2">
            <div 
              className={`h-full rounded-full transition-all duration-1000 ${confidenceBarColor}`} 
              style={{ width: `${data.confidence}%` }}
            ></div>
          </div>
        </div>

        {/* AI Narrative Section */}
        {data.summary && (
          <div className="space-y-1 bg-slate-950/20 border border-slate-800/40 rounded-lg p-3">
            <h4 className="text-xs font-semibold text-slate-400 flex items-center gap-1"><Info size={13} /> Summary</h4>
            <p className="text-xs text-slate-300 leading-relaxed">{data.summary}</p>
          </div>
        )}

        {data.investment_thesis && (
          <div className="space-y-1 bg-slate-950/20 border border-slate-800/40 rounded-lg p-3">
            <h4 className="text-xs font-semibold text-slate-400 flex items-center gap-1"><DollarSign size={13} /> Investment Thesis</h4>
            <p className="text-xs text-slate-300 leading-relaxed">{data.investment_thesis}</p>
          </div>
        )}

        {/* Technical Indicators Breakdown Grid */}
        <div>
          <h4 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-3 select-none">Technical Indicators</h4>
          <div className="grid grid-cols-3 gap-3">
            {/* RSI */}
            <div className="bg-slate-950/20 border border-slate-800/40 rounded-lg p-3 flex flex-col justify-between">
              <span className="text-[10px] font-medium text-slate-500 uppercase select-none">RSI (14)</span>
              <span className="text-lg font-bold text-slate-100 mt-1">{data.rsi}</span>
              <span className={`text-[10px] font-semibold mt-0.5 ${rsiStatusColor}`}>{rsiStatus}</span>
            </div>

            {/* MACD */}
            <div className="bg-slate-950/20 border border-slate-800/40 rounded-lg p-3 flex flex-col justify-between">
              <span className="text-[10px] font-medium text-slate-500 uppercase select-none">MACD (12, 26, 9)</span>
              <span className={`text-lg font-bold mt-1 flex items-center gap-1 capitalize ${
                data.macd === "bullish" ? "text-emerald-400" : "text-rose-400"
              }`}>
                {data.macd === "bullish" ? <TrendingUp size={16} /> : <TrendingDown size={16} />}
                <span className="text-sm md:text-base font-bold">{data.macd}</span>
              </span>
              <span className="text-[10px] text-slate-500 select-none">Signal crossover</span>
            </div>

            {/* EMA Trend */}
            <div className="bg-slate-950/20 border border-slate-800/40 rounded-lg p-3 flex flex-col justify-between">
              <span className="text-[10px] font-medium text-slate-500 uppercase select-none">EMA Trend (20/50)</span>
              <span className={`text-lg font-bold mt-1 flex items-center gap-1 capitalize ${
                data.ema_trend === "bullish" ? "text-emerald-400" : "text-rose-400"
              }`}>
                {data.ema_trend === "bullish" ? <TrendingUp size={16} /> : <TrendingDown size={16} />}
                <span className="text-sm md:text-base font-bold">{data.ema_trend}</span>
              </span>
              <span className="text-[10px] text-slate-500 select-none">Moving Average</span>
            </div>
          </div>
        </div>

        {/* Target Cases & Strategies */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {data.bull_case && (
            <div className="space-y-1 bg-emerald-950/10 border border-emerald-900/20 rounded-lg p-3">
              <h4 className="text-xs font-semibold text-emerald-400">Bull Case</h4>
              <p className="text-xs text-slate-300 leading-relaxed">{data.bull_case}</p>
            </div>
          )}
          {data.bear_case && (
            <div className="space-y-1 bg-rose-950/10 border border-rose-900/20 rounded-lg p-3">
              <h4 className="text-xs font-semibold text-rose-400">Bear Case</h4>
              <p className="text-xs text-slate-300 leading-relaxed">{data.bear_case}</p>
            </div>
          )}
          {data.entry_strategy && (
            <div className="space-y-1 bg-slate-950/20 border border-slate-800/40 rounded-lg p-3">
              <h4 className="text-xs font-semibold text-slate-400">Entry Strategy</h4>
              <p className="text-xs text-slate-300 leading-relaxed">{data.entry_strategy}</p>
            </div>
          )}
          {data.exit_strategy && (
            <div className="space-y-1 bg-slate-950/20 border border-slate-800/40 rounded-lg p-3">
              <h4 className="text-xs font-semibold text-slate-400">Exit Strategy</h4>
              <p className="text-xs text-slate-300 leading-relaxed">{data.exit_strategy}</p>
            </div>
          )}
        </div>

        {/* Key Levels & Warnings */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          { (data.key_levels && data.key_levels.length > 0) && (
            <div className="space-y-2">
              <h5 className="text-xs font-semibold text-slate-400 select-none">Key Levels</h5>
              <div className="flex flex-wrap gap-1.5">
                {data.key_levels.map((level, idx) => (
                  <span key={idx} className="text-[10px] bg-slate-900 border border-slate-800 px-2 py-0.5 rounded text-slate-300">{level}</span>
                ))}
              </div>
            </div>
          )}
          { !(data.key_levels && data.key_levels.length > 0) && (
            <div className="space-y-2"><h5 className="text-xs font-semibold text-slate-400 select-none">Key Levels</h5><div className="text-xs text-slate-300">No key levels available.</div></div>
          )}
          { (data.warnings && data.warnings.length > 0) && (
            <div className="space-y-2">
              <h5 className="text-xs font-semibold text-rose-500/80 flex items-center gap-1 select-none"><AlertTriangle size={14} /> Catalyst Warnings</h5>
              <div className="flex flex-wrap gap-1.5">
                {data.warnings.map((warning, idx) => (
                  <span key={idx} className="text-[10px] bg-rose-950/10 border border-rose-900/20 px-2 py-0.5 rounded text-rose-300">{warning}</span>
                ))}
              </div>
            </div>
          )}
          { !(data.warnings && data.warnings.length > 0) && (
            <div className="space-y-2"><h5 className="text-xs font-semibold text-rose-500/80 flex items-center gap-1 select-none"><AlertTriangle size={14} /> Catalyst Warnings</h5><div className="text-xs text-slate-300">No warnings available.</div></div>
          )}
        </div>

        {/* Pros & Cons Analysis Split View */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-1">
          {/* Pros */}
          <div className="space-y-2">
            <h5 className="text-xs font-semibold text-emerald-500/80 flex items-center gap-1 select-none">
              <Check size={14} /> Supporting Arguments (Pros)
            </h5>
            {(data.pros && data.pros.length > 0) ? (
              <ul className="space-y-1.5">
                {data.pros.map((pro, idx) => (
                  <li key={idx} className="text-xs text-slate-300 flex items-start gap-2 bg-emerald-950/5 border border-emerald-900/10 p-2 rounded-md">
                    <span className="text-emerald-500 mt-0.5 font-bold">•</span>
                    <span>{pro}</span>
                  </li>
                ))}
              </ul>
            ) : (
              <div className="text-xs text-slate-300">No pros available.</div>
            )}
          </div>

          {/* Cons */}
          <div className="space-y-2">
            <h5 className="text-xs font-semibold text-rose-500/80 flex items-center gap-1 select-none">
              <AlertTriangle size={14} /> Risk Factors (Cons)
            </h5>
            {(data.cons && data.cons.length > 0) ? (
              <ul className="space-y-1.5">
                {data.cons.map((con, idx) => (
                  <li key={idx} className="text-xs text-slate-300 flex items-start gap-2 bg-rose-950/5 border border-rose-900/10 p-2 rounded-md">
                    <span className="text-rose-500 mt-0.5 font-bold">•</span>
                    <span>{con}</span>
                  </li>
                ))}
              </ul>
            ) : (
              <div className="text-xs text-slate-300">No cons available.</div>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
