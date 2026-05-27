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

  return (
    <Card className="w-full h-full flex flex-col">
      <CardHeader className="flex flex-row items-center justify-between gap-4 py-4">
        <div>
          <CardTitle className="text-2xl font-bold flex items-center gap-2">
            <span>{data.ticker}</span>
            <span className="text-base font-normal text-slate-500">Analysis Summary</span>
          </CardTitle>
          <CardDescription>
            Last Close: <span className="font-semibold text-slate-200">${data.price.toLocaleString(undefined, { minimumFractionDigits: 2 })}</span>
          </CardDescription>
        </div>

        {/* Floating Recommendation Signal Badge */}
        <Badge variant={signalBadgeVariant} glow className="text-sm px-4 py-1.5 font-bold tracking-wider">
          {data.signal}
        </Badge>
      </CardHeader>

      <CardContent className="flex-1 space-y-6">
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

        {/* Pros & Cons Analysis Split View */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-1">
          {/* Pros */}
          <div className="space-y-2">
            <h5 className="text-xs font-semibold text-emerald-500/80 flex items-center gap-1 select-none">
              <Check size={14} /> Supporting Arguments (Pros)
            </h5>
            <ul className="space-y-1.5">
              {data.pros.map((pro, idx) => (
                <li key={idx} className="text-xs text-slate-300 flex items-start gap-2 bg-emerald-950/5 border border-emerald-900/10 p-2 rounded-md">
                  <span className="text-emerald-500 mt-0.5 font-bold">•</span>
                  <span>{pro}</span>
                </li>
              ))}
            </ul>
          </div>

          {/* Cons */}
          <div className="space-y-2">
            <h5 className="text-xs font-semibold text-rose-500/80 flex items-center gap-1 select-none">
              <AlertTriangle size={14} /> Risk Factors (Cons)
            </h5>
            <ul className="space-y-1.5">
              {data.cons.map((con, idx) => (
                <li key={idx} className="text-xs text-slate-300 flex items-start gap-2 bg-rose-950/5 border border-rose-900/10 p-2 rounded-md">
                  <span className="text-rose-500 mt-0.5 font-bold">•</span>
                  <span>{con}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
