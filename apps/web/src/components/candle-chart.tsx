"use client";

import { ColorType, createChart, CandlestickSeries } from "lightweight-charts";
import { useEffect, useRef } from "react";
import type { Candle } from "@/lib/types";

export function CandleChart({ bars }: { bars: Candle[] }) {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const node = ref.current;
    if (!node || bars.length === 0) {
      return;
    }
    const chart = createChart(node, {
      autoSize: true,
      height: 420,
      layout: {
        background: { type: ColorType.Solid, color: "#0a0a0a" },
        textColor: "#8e8e93",
        fontFamily: "Inter, ui-sans-serif, system-ui, sans-serif",
      },
      grid: {
        vertLines: { color: "rgba(255,255,255,0.04)" },
        horzLines: { color: "rgba(255,255,255,0.04)" },
      },
      rightPriceScale: { borderColor: "rgba(255,255,255,0.08)" },
      timeScale: { borderColor: "rgba(255,255,255,0.08)", rightOffset: 2 },
      crosshair: {
        vertLine: { color: "rgba(245,245,247,0.35)" },
        horzLine: { color: "rgba(245,245,247,0.35)" },
      },
    });
    const series = chart.addSeries(CandlestickSeries, {
      upColor: "#3d9a6a",
      downColor: "#c45c5c",
      borderVisible: false,
      wickUpColor: "#3d9a6a",
      wickDownColor: "#c45c5c",
    });
    series.setData(
      bars.map((bar) => ({
        time: bar.time.slice(0, 10),
        open: bar.open,
        high: bar.high,
        low: bar.low,
        close: bar.close,
      })),
    );
    const fit = () => chart.timeScale().fitContent();
    fit();
    const observer = new ResizeObserver(() => fit());
    observer.observe(node);
    return () => {
      observer.disconnect();
      chart.remove();
    };
  }, [bars]);

  if (bars.length === 0) {
    return <p className="px-6 py-16 text-sm text-muted">No hay precios para esta emisora.</p>;
  }

  return <div ref={ref} className="h-[420px] w-full" />;
}
