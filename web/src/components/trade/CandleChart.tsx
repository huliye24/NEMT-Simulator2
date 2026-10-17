"use client";

import { useMemo } from "react";
import { cn, fmtPrice } from "@/lib/trade/format";
import type { Kline } from "@/lib/trade/types";
import { Spinner } from "./ui";

const VIEW_W = 600;
const VIEW_H = 260;
const PRICE_TOP = 10;
const PRICE_BOTTOM = 196;
const VOLUME_TOP = 214;
const VOLUME_BOTTOM = 250;

export default function CandleChart({
  candles,
  loading = false,
  className,
}: {
  candles: Kline[];
  loading?: boolean;
  className?: string;
}) {
  const chart = useMemo(() => {
    const items = candles.slice(-90);
    if (items.length === 0) return null;

    const highs = items.map((item) => Number(item.high));
    const lows = items.map((item) => Number(item.low));
    const rawMax = Math.max(...highs);
    const rawMin = Math.min(...lows);
    const padding = Math.max((rawMax - rawMin) * 0.08, rawMax * 0.0005);
    const max = rawMax + padding;
    const min = rawMin - padding;
    const span = max - min || 1;
    const maxVolume = Math.max(...items.map((item) => Number(item.volume)), 0.0000001);

    const gap = (VIEW_W / items.length) * 0.28;
    const slot = VIEW_W / items.length;
    const bodyWidth = Math.max(slot - gap, 1.2);

    const yFor = (price: number) =>
      PRICE_BOTTOM - ((price - min) / span) * (PRICE_BOTTOM - PRICE_TOP);

    const shapes = items.map((item, index) => {
      const open = Number(item.open);
      const close = Number(item.close);
      const high = Number(item.high);
      const low = Number(item.low);
      const center = slot * index + slot / 2;
      const yOpen = yFor(open);
      const yClose = yFor(close);
      const top = Math.min(yOpen, yClose);
      const height = Math.max(Math.abs(yClose - yOpen), 1.2);
      const up = close >= open;
      const volumeHeight =
        (Number(item.volume) / maxVolume) * (VOLUME_BOTTOM - VOLUME_TOP);
      return {
        x: center,
        top,
        height,
        wickTop: yFor(high),
        wickBottom: yFor(low),
        up,
        volumeTop: VOLUME_BOTTOM - Math.max(volumeHeight, 1),
        close,
      };
    });

    const labels = [0, 0.25, 0.5, 0.75, 1].map((ratio) => ({
      price: max - ratio * span,
      top: (PRICE_TOP + ratio * (PRICE_BOTTOM - PRICE_TOP)) / VIEW_H,
    }));

    const last = items[items.length - 1];
    const lastY = yFor(Number(last.close));
    const lastPrice = Number(last.close);
    const times = [items[0], items[Math.floor(items.length / 2)], last].map(
      (item) => item.open_time_iso
    );

    return {
      shapes,
      labels,
      lastY,
      lastPrice,
      lastLabelTop: lastY / VIEW_H,
      bodyWidth,
      times,
      count: items.length,
    };
  }, [candles]);

  if (!chart) {
    return (
      <div
        className={cn(
          "relative h-[260px] rounded-xl overflow-hidden trade-skeleton",
          className
        )}
      >
        {loading ? (
          <div className="absolute inset-0 flex items-center justify-center">
            <Spinner size={20} className="text-cyan-300/60" />
          </div>
        ) : null}
      </div>
    );
  }

  return (
    <div className={cn("relative", className)}>
      <div className="relative h-[260px] w-full">
        <div className="absolute inset-y-0 left-0 right-[54px]">
          <svg
            width="100%"
            height="100%"
            viewBox={`0 0 ${VIEW_W} ${VIEW_H}`}
            preserveAspectRatio="none"
            className="trade-chart-grid block"
            role="img"
            aria-label="BTCUSDT K 线图"
          >
            {[0, 0.25, 0.5, 0.75, 1].map((ratio) => {
              const y = PRICE_TOP + ratio * (PRICE_BOTTOM - PRICE_TOP);
              return (
                <line
                  key={ratio}
                  x1={0}
                  x2={VIEW_W}
                  y1={y}
                  y2={y}
                  strokeDasharray={ratio === 1 ? "0" : "3 5"}
                />
              );
            })}
            <line
              x1={0}
              x2={VIEW_W}
              y1={VOLUME_BOTTOM}
              y2={VOLUME_BOTTOM}
              stroke="rgba(148,163,184,0.12)"
            />
            {chart.shapes.map((shape, index) => (
              <g key={index}>
                <rect
                  x={shape.x - 0.6}
                  y={shape.wickTop}
                  width={1.2}
                  height={Math.max(shape.wickBottom - shape.wickTop, 1)}
                  fill={shape.up ? "rgba(52,211,153,0.65)" : "rgba(251,113,133,0.65)"}
                />
                <rect
                  x={shape.x - chart.bodyWidth / 2}
                  y={shape.top}
                  width={chart.bodyWidth}
                  height={shape.height}
                  rx={0.6}
                  fill={shape.up ? "#34d399" : "#fb7185"}
                  opacity={0.92}
                />
                <rect
                  x={shape.x - chart.bodyWidth / 2}
                  y={shape.volumeTop}
                  width={chart.bodyWidth}
                  height={Math.max(VOLUME_BOTTOM - shape.volumeTop, 0.8)}
                  rx={0.5}
                  fill={shape.up ? "rgba(52,211,153,0.18)" : "rgba(251,113,133,0.18)"}
                />
              </g>
            ))}
            <line
              x1={0}
              x2={VIEW_W}
              y1={chart.lastY}
              y2={chart.lastY}
              stroke="rgba(16,219,233,0.55)"
              strokeDasharray="5 4"
              strokeWidth={1}
            />
          </svg>
        </div>

        <div className="absolute inset-y-0 right-0 w-[54px] pointer-events-none">
          {chart.labels
            .filter((label) => Math.abs(label.top - chart.lastLabelTop) > 0.07)
            .map((label, index) => (
              <span
                key={index}
                className="absolute left-0 -translate-y-1/2 trade-number text-[9px] text-slate-600 pl-1.5"
                style={{ top: `${label.top * 100}%` }}
              >
                {fmtPrice(label.price)}
              </span>
            ))}
          <span
            className="absolute left-0 -translate-y-1/2 rounded-l-md bg-cyan-400/15 px-1.5 py-0.5 trade-number text-[9px] font-semibold text-cyan-200"
            style={{ top: `${chart.lastLabelTop * 100}%` }}
          >
            {fmtPrice(chart.lastPrice)}
          </span>
        </div>

        <div className="absolute -bottom-5 left-0 right-[54px] flex justify-between text-[9px] text-slate-600">
          {chart.times.map((time, index) => (
            <span key={index}>
              {time
                ? new Date(time).toLocaleTimeString("zh-CN", {
                    hour: "2-digit",
                    minute: "2-digit",
                    hour12: false,
                  })
                : "--:--"}
            </span>
          ))}
        </div>
      </div>
      {loading ? (
        <div className="absolute right-1 top-1 flex items-center gap-1.5 rounded-full border border-white/8 bg-black/50 px-2 py-1 text-[9px] text-slate-400">
          <Spinner size={10} />
          更新
        </div>
      ) : null}
    </div>
  );
}
