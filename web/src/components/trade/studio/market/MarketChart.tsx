"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { ageLabel, cn, fmtCompact, fmtPrice } from "@/lib/trade/format";
import type { Kline } from "@/lib/trade/types";
import { Spinner } from "../common";
import { StudioIcon } from "../icons";

const INTERVALS = [
  { key: "1m", label: "1m" },
  { key: "5m", label: "5m" },
  { key: "15m", label: "15m" },
  { key: "1h", label: "1H" },
  { key: "4h", label: "4H" },
  { key: "1d", label: "1D" },
];

interface MarketChartProps {
  candles: Kline[];
  interval: string;
  source: "binance" | "demo" | null;
  stale: boolean;
  fetchedAt: string | null;
  loading: boolean;
  refreshing: boolean;
  error: string | null;
  onIntervalChange: (interval: string) => void;
  onRefresh: () => void;
}

interface Size {
  width: number;
  height: number;
}

function useElementSize(ref: React.RefObject<HTMLDivElement | null>): Size {
  const [size, setSize] = useState<Size>({ width: 0, height: 0 });

  useEffect(() => {
    const element = ref.current;
    if (!element) return;

    const measure = () => {
      setSize((current) => {
        const width = Math.round(element.clientWidth);
        const height = Math.round(element.clientHeight);
        if (current.width === width && current.height === height) return current;
        return { width, height };
      });
    };

    measure();
    const observer = new ResizeObserver(measure);
    observer.observe(element);
    return () => observer.disconnect();
  }, [ref]);

  return size;
}

function axisTime(iso: string, interval: string): string {
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return "—";
  if (interval === "1h" || interval === "4h" || interval === "1d") {
    return date.toLocaleDateString("zh-CN", {
      month: "2-digit",
      day: "2-digit",
    });
  }
  return date.toLocaleTimeString("zh-CN", {
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  });
}

function intervalLabel(interval: string): string {
  return INTERVALS.find((item) => item.key === interval)?.label ?? interval;
}

export default function MarketChart({
  candles,
  interval,
  source,
  stale,
  fetchedAt,
  loading,
  refreshing,
  error,
  onIntervalChange,
  onRefresh,
}: MarketChartProps) {
  const canvasRef = useRef<HTMLDivElement>(null);
  const size = useElementSize(canvasRef);
  const [hoverIndex, setHoverIndex] = useState<number | null>(null);

  const chart = useMemo(() => {
    const items = candles.slice(-120);
    if (items.length === 0 || size.width < 40 || size.height < 80) return null;

    const width = size.width;
    const height = size.height;
    const plotLeft = 8;
    const plotRight = Math.max(plotLeft + 100, width - 62);
    const plotWidth = plotRight - plotLeft;
    const axisBottom = height - 23;
    const volumeHeight = Math.max(34, height * 0.16);
    const volumeTop = axisBottom - volumeHeight;
    const priceTop = 14;
    const priceBottom = volumeTop - 16;

    const high = Math.max(...items.map((item) => Number(item.high)));
    const low = Math.min(...items.map((item) => Number(item.low)));
    const rawSpan = high - low;
    const padding = Math.max(rawSpan * 0.08, high * 0.00035);
    const max = high + padding;
    const min = low - padding;
    const span = max - min || 1;
    const maxVolume = Math.max(...items.map((item) => Number(item.volume)), 0.0000001);
    const slot = plotWidth / items.length;
    const bodyWidth = Math.min(11, Math.max(1.2, slot * 0.62));

    const yFor = (price: number) =>
      priceBottom - ((price - min) / span) * (priceBottom - priceTop);

    const rendered = items.map((item, index) => {
      const open = Number(item.open);
      const close = Number(item.close);
      const candleHigh = Number(item.high);
      const candleLow = Number(item.low);
      const center = plotLeft + slot * index + slot / 2;
      const yOpen = yFor(open);
      const yClose = yFor(close);
      const volume = Number(item.volume);
      const barHeight = Math.max(1, (volume / maxVolume) * (volumeHeight - 4));
      return {
        center,
        up: close >= open,
        bodyTop: Math.min(yOpen, yClose),
        bodyHeight: Math.max(Math.abs(yClose - yOpen), 1),
        wickTop: yFor(candleHigh),
        wickBottom: yFor(candleLow),
        volumeY: axisBottom - barHeight,
        barHeight,
      };
    });

    const grid = [0, 0.25, 0.5, 0.75, 1].map((ratio) => ({
      y: priceTop + ratio * (priceBottom - priceTop),
      value: max - ratio * span,
    }));

    const timeIndexes = Array.from(
      new Set([0, Math.floor((items.length - 1) * 0.25), Math.floor((items.length - 1) * 0.5), Math.floor((items.length - 1) * 0.75), items.length - 1])
    );
    const times = timeIndexes.map((index) => ({
      index,
      x: plotLeft + slot * index + slot / 2,
      label: axisTime(items[index].open_time_iso, interval),
    }));

    const last = items[items.length - 1];
    const lastY = yFor(Number(last.close));
    const lastPrice = Number(last.close);

    return {
      items,
      rendered,
      grid,
      times,
      plotLeft,
      plotRight,
      plotWidth,
      priceTop,
      priceBottom,
      volumeTop,
      axisBottom,
      slot,
      bodyWidth,
      maxVolume,
      lastY,
      lastPrice,
      width,
      height,
    };
  }, [candles, interval, size]);

  const selected =
    chart && chart.items.length > 0
      ? hoverIndex !== null
        ? chart.items[Math.min(hoverIndex, chart.items.length - 1)]
        : chart.items[chart.items.length - 1]
      : null;

  const selectedUp = selected ? Number(selected.close) >= Number(selected.open) : true;

  const handlePointerMove = useCallback(
    (event: React.PointerEvent<SVGSVGElement>) => {
      if (!chart) return;
      const rect = event.currentTarget.getBoundingClientRect();
      const x = event.clientX - rect.left;
      if (x < chart.plotLeft || x > chart.plotRight) {
        setHoverIndex(null);
        return;
      }
      const next = Math.max(
        0,
        Math.min(chart.items.length - 1, Math.floor((x - chart.plotLeft) / chart.slot))
      );
      setHoverIndex(next);
    },
    [chart]
  );

  const hoveredShape =
    chart && hoverIndex !== null
      ? chart.rendered[Math.min(hoverIndex, chart.rendered.length - 1)]
      : null;
  const hoveredClose = chart && hoverIndex !== null
    ? Number(chart.items[Math.min(hoverIndex, chart.items.length - 1)].close)
    : null;

  const empty = !loading && !error && candles.length === 0;

  return (
    <div className="ns-chart">
      <div className="ns-chart-toolbar">
        <div className="ns-chart-ohlc" aria-live="polite">
          <span className="ns-chart-ohlc-pair">
            BTC/USDT <span>{intervalLabel(interval)}</span>
          </span>
          {selected ? (
            <span className="ns-chart-ohlc-values">
              <span>O <b>{fmtPrice(selected.open)}</b></span>
              <span>H <b className="ns-text-up">{fmtPrice(selected.high)}</b></span>
              <span>L <b className="ns-text-down">{fmtPrice(selected.low)}</b></span>
              <span>C <b className={selectedUp ? "ns-text-up" : "ns-text-down"}>{fmtPrice(selected.close)}</b></span>
              <span className="ns-chart-ohlc-volume">VOL <b>{fmtCompact(selected.volume)}</b></span>
            </span>
          ) : (
            <span className="ns-chart-ohlc-placeholder">等待 K 线数据</span>
          )}
        </div>

        <div className="ns-chart-actions">
          <div className="ns-intervals" role="group" aria-label="K 线周期">
            {INTERVALS.map((item) => (
              <button
                type="button"
                key={item.key}
                className={cn("ns-interval", interval === item.key && "is-active")}
                onClick={() => onIntervalChange(item.key)}
                aria-pressed={interval === item.key}
              >
                {item.label}
              </button>
            ))}
          </div>
          <button
            type="button"
            className="ns-icon-btn ns-chart-refresh"
            onClick={onRefresh}
            disabled={loading || refreshing}
            aria-label="刷新 K 线"
            title="刷新 K 线"
          >
            {loading || refreshing ? <Spinner size={14} /> : <StudioIcon name="refresh" size={15} />}
          </button>
        </div>
      </div>

      <div className="ns-chart-canvas" ref={canvasRef}>
        {chart ? (
          <svg
            width={chart.width}
            height={chart.height}
            viewBox={`0 0 ${chart.width} ${chart.height}`}
            className="ns-chart-svg"
            role="img"
            aria-label={`BTCUSDT ${interval} K 线图，最新价格 ${fmtPrice(chart.lastPrice)} USDT`}
            onPointerMove={handlePointerMove}
            onPointerLeave={() => setHoverIndex(null)}
          >
            {chart.grid.map((line, index) => (
              <g key={`grid-${index}`}>
                <line
                  x1={chart.plotLeft}
                  x2={chart.plotRight}
                  y1={line.y}
                  y2={line.y}
                  className="ns-chart-gridline"
                />
                <text
                  x={chart.plotRight + 8}
                  y={line.y + 3.5}
                  className="ns-chart-axis-label"
                >
                  {fmtPrice(line.value)}
                </text>
              </g>
            ))}

            <line
              x1={chart.plotLeft}
              x2={chart.plotRight}
              y1={chart.volumeTop - 8}
              y2={chart.volumeTop - 8}
              className="ns-chart-divider"
            />

            {chart.rendered.map((shape, index) => (
              <g key={index} className={shape.up ? "ns-candle-up" : "ns-candle-down"}>
                <line
                  x1={shape.center}
                  x2={shape.center}
                  y1={shape.wickTop}
                  y2={shape.wickBottom}
                  className="ns-candle-wick"
                />
                <rect
                  x={shape.center - chart.bodyWidth / 2}
                  y={shape.bodyTop}
                  width={chart.bodyWidth}
                  height={shape.bodyHeight}
                  rx={0.6}
                  className="ns-candle-body"
                />
                <rect
                  x={shape.center - chart.bodyWidth / 2}
                  y={shape.volumeY}
                  width={chart.bodyWidth}
                  height={shape.barHeight}
                  rx={0.5}
                  className="ns-volume-bar"
                />
              </g>
            ))}

            <line
              x1={chart.plotLeft}
              x2={chart.plotRight}
              y1={chart.lastY}
              y2={chart.lastY}
              className="ns-chart-lastline"
            />
            <g>
              <rect
                x={chart.plotRight + 4}
                y={chart.lastY - 9}
                width={56}
                height={18}
                rx={4}
                className="ns-chart-price-tag"
              />
              <text
                x={chart.plotRight + 32}
                y={chart.lastY + 3.5}
                textAnchor="middle"
                className="ns-chart-price-label"
              >
                {fmtPrice(chart.lastPrice)}
              </text>
            </g>

            {hoveredShape && hoveredClose !== null ? (
              <g className="ns-chart-crosshair">
                <line
                  x1={hoveredShape.center}
                  x2={hoveredShape.center}
                  y1={chart.priceTop}
                  y2={chart.axisBottom}
                />
                <line
                  x1={chart.plotLeft}
                  x2={chart.plotRight}
                  y1={chart.rendered[hoverIndex ?? 0] ? chart.rendered[hoverIndex ?? 0].bodyTop : chart.lastY}
                  y2={chart.rendered[hoverIndex ?? 0] ? chart.rendered[hoverIndex ?? 0].bodyTop : chart.lastY}
                />
                <circle
                  cx={hoveredShape.center}
                  cy={chart.rendered[hoverIndex ?? 0]?.bodyTop ?? chart.lastY}
                  r={3}
                />
                <rect
                  x={chart.plotRight + 4}
                  y={(chart.rendered[hoverIndex ?? 0]?.bodyTop ?? chart.lastY) - 9}
                  width={56}
                  height={18}
                  rx={4}
                  className="ns-chart-hover-tag"
                />
                <text
                  x={chart.plotRight + 32}
                  y={(chart.rendered[hoverIndex ?? 0]?.bodyTop ?? chart.lastY) + 3.5}
                  textAnchor="middle"
                  className="ns-chart-hover-label"
                >
                  {fmtPrice(hoveredClose)}
                </text>
              </g>
            ) : null}

            {chart.times.map((time, index) => (
              <text
                key={`time-${index}`}
                x={Math.min(Math.max(time.x, chart.plotLeft + 14), chart.plotRight - 14)}
                y={chart.height - 6}
                textAnchor={index === 0 ? "start" : index === chart.times.length - 1 ? "end" : "middle"}
                className="ns-chart-axis-label"
              >
                {time.label}
              </text>
            ))}
          </svg>
        ) : null}

        {!chart && loading ? (
          <div className="ns-chart-state" aria-live="polite">
            <Spinner size={22} />
            <p>正在加载 K 线数据…</p>
            <span className="ns-chart-state-hint">BTC/USDT · {intervalLabel(interval)}</span>
          </div>
        ) : null}

        {!chart && error ? (
          <div className="ns-chart-state ns-chart-state-error" role="alert">
            <span className="ns-chart-state-icon">
              <StudioIcon name="warning" size={20} />
            </span>
            <p>{error}</p>
            <button type="button" className="ns-btn ns-btn-outline ns-btn-sm" onClick={onRefresh}>
              重新加载
            </button>
          </div>
        ) : null}

        {!chart && empty ? (
          <div className="ns-chart-state">
            <span className="ns-chart-state-icon">
              <StudioIcon name="markets" size={20} />
            </span>
            <p>暂无 K 线数据</p>
            <button type="button" className="ns-btn ns-btn-outline ns-btn-sm" onClick={onRefresh}>
              刷新
            </button>
          </div>
        ) : null}

        {refreshing && chart ? (
          <span className="ns-chart-updating">
            <Spinner size={11} />
            更新中
          </span>
        ) : null}

        {stale ? (
          <span className="ns-chart-stale">
            <StudioIcon name="warning" size={12} />
            数据可能延迟
          </span>
        ) : null}
      </div>

      <div className="ns-chart-foot">
        <span>
          {candles.length > 0 ? `${candles.length} 根 K 线 · ${source === "demo" ? "模拟行情" : "Binance 公共行情"}` : "K 线数据"}
          {stale ? " · 已过期" : ""}
        </span>
        <span className="ns-chart-foot-right">
          {error && chart ? (
            <>
              <span className="ns-chart-foot-error">更新失败</span>
              <button type="button" onClick={onRefresh} className="ns-text-link">
                重试
              </button>
            </>
          ) : (
            <>
              <StudioIcon name="clock" size={12} />
              更新于 {fetchedAt ? ageLabel(fetchedAt) : "—"}
            </>
          )}
        </span>
      </div>
    </div>
  );
}
