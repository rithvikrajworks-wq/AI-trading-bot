// src/components/TradingViewChart.tsx
import React, { useEffect, useState } from "react";

interface TradingViewChartProps {
  ticker: string;
  width?: string; // e.g. "100%"
  height?: string; // e.g. "400px"
}

/**
 * Simple TradingView embed using an iframe. The widget URL is the public lightweight
 * chart that does not require any API keys. If the ticker is empty a placeholder is shown.
 */
export default function TradingViewChart({ ticker, width = "100%", height = "400px" }: TradingViewChartProps) {
  const [embedUrl, setEmbedUrl] = useState<string>("");

  useEffect(() => {
    if (!ticker) {
      setEmbedUrl("");
      return;
    }
    // Construct a public TradingView widget URL. The format works for most exchanges.
    // Example: https://s.tradingview.com/embed-widget/advanced-chart/?locale=en#%7B"symbol":"NASDAQ%3ANVDA","interval":"D","timezone":"Etc%2FUTC","theme":"dark","style":"1","toolbar_bg":"#212121","enable_publishing":false,"allow_symbol_change":true,"hide_top_toolbar":false,"save_image":false,"study":[]%7D
    const symbol = `NASDAQ%3A${encodeURIComponent(ticker)}`;
    const params = encodeURIComponent(
      JSON.stringify({
        symbol,
        interval: "D",
        timezone: "Etc/UTC",
        theme: "dark",
        style: "1",
        toolbar_bg: "#212121",
        enable_publishing: false,
        allow_symbol_change: true,
        hide_top_toolbar: false,
        save_image: false,
        studies: []
      })
    );
    const url = `https://s.tradingview.com/embed-widget/advanced-chart/?locale=en#${params}`;
    setEmbedUrl(url);
  }, [ticker]);

  if (!embedUrl) {
    return (
      <div className="flex items-center justify-center h-48 text-slate-500">Enter a ticker to view chart</div>
    );
  }

  return (
    <div className="w-full" style={{ width, height }}>
      <iframe
        src={embedUrl}
        width="100%"
        height="100%"
        frameBorder="0"
        allowTransparency="true"
        scrolling="no"
        className="rounded-lg bg-slate-900"
      ></iframe>
    </div>
  );
}
