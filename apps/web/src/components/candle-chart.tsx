"use client";

import { ColorType, createChart, CandlestickSeries } from "lightweight-charts";
import { useEffect, useRef } from "react";
import type { Candle } from "@/lib/types";

function cssVar(name: string, fallback: string) {
  if (typeof window === "undefined") return fallback;
  const value = getComputedStyle(document.documentElement).getPropertyValue(name).trim();
  return value || fallback;
}

export function CandleChart({ bars }: { bars: Candle[] }) {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const node = ref.current;
    if (!node || bars.length === 0) {
      return;
    }
    const surface = cssVar("--surface", "#121418");
    const muted = cssVar("--muted", "#9a958c");
    const line = cssVar("--line", "rgba(242,239,232,0.1)");
    const ink = cssVar("--ink", "#f2efe8");
    const up = cssVar("--up", "#3d9a6a");
    const down = cssVar("--down", "#c45c5c");
    const chart = createChart(node, {
      autoSize: true,
      height: Math.min(420, Math.max(280, node.clientWidth * 0.55)),
      layout: {
        background: { type: ColorType.Solid, color: surface },
        textColor: muted,
        fontFamily: "Inter, ui-sans-serif, system-ui, sans-serif",
      },
      grid: {
        vertLines: { color: line },
        horzLines: { color: line },
      },
      rightPriceScale: { borderColor: line },
      timeScale: { borderColor: line, rightOffset: 2 },
      crosshair: {
        vertLine: { color: ink },
        horzLine: { color: ink },
      },
    });
    const series = chart.addSeries(CandlestickSeries, {
      upColor: up,
      downColor: down,
      borderVisible: false,
      wickUpColor: up,
      wickDownColor: down,
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

  return <div ref={ref} className="h-[280px] w-full sm:h-[420px]" />;
}
