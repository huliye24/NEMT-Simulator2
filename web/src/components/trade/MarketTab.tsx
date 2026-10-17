"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { tradeApi } from "@/lib/trade/api";
import {
  ageLabel,
  cn,
  fmtCompact,
  fmtPrice,
  fmtPct,
} from "@/lib/trade/format";
import type { Klines } from "@/lib/trade/types";
import CandleChart from "./CandleChart";
import type { WorkspaceData } from "./workspace-shared";
import {
  Icon,
  SectionHeader,
  SourceBadge,
  Spinner,
} from "./ui";

const INTERVALS = [
  { key: "1m", label: "1分" },
  { key: "5m", label: "5分" },
  { key: "15m", label: "15分" },
  { key: "1h", label: "1时" },
];

export default function MarketTab({
  data,
  onTrade,
}: {
  data: WorkspaceData;
  onTrade: () => void;
}) {
  const { ticker, online } = data;
  const [interval, setIntervalKey] = useState("5m");
  const [klines, setKlines] = useState<Klines | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const requestRef = useRef(0);

  const load = useCallback(async (nextInterval: string) => {
    const requestId = ++requestRef.current;
    setLoading(true);
    try {
      const next = await tradeApi.getKlines("BTCUSDT", nextInterval, 90);
      if (requestRef.current !== requestId) return;
      setKlines(next);
      setError(null);
    } catch (reason) {
      if (requestRef.current !== requestId) return;
      setError(reason instanceof Error ? reason.message : "K 线加载失败");
    } finally {
      if (requestRef.current === requestId) setLoading(false);
    }
  }, []);

  useEffect(() => {
    let cancelled = false;
    const initial = window.setTimeout(() => {
      if (!cancelled) void load(interval);
    }, 0);
    const timer = window.setInterval(() => {
      if (!document.hidden && navigator.onLine) void load(interval);
    }, 30_000);
    return () => {
      cancelled = true;
      window.clearTimeout(initial);
      window.clearInterval(timer);
    };
  }, [interval, load]);

  const change = Number(ticker?.price_change_percent ?? 0);
  const positive = change >= 0;
  const chartStale = Boolean(klines?.stale) || !online;

  return (
    <div className="space-y-4">
      <section className="trade-card trade-card-accent p-4">
        <div className="flex items-start justify-between gap-3">
          <div>
            <div className="flex items-center gap-2">
              <span className="text-[11px] uppercase tracking-[0.14em] text-slate-500">
                BTC / USDT
              </span>
              <SourceBadge source={ticker?.source} stale={ticker?.stale || !online} />
            </div>
            <div className="flex items-end gap-3 mt-2">
              <p className="trade-number text-[30px] leading-none font-semibold text-slate-50">
                {fmtPrice(ticker?.last_price)}
              </p>
              <span
                className={cn(
                  "trade-number text-[12px] font-semibold pb-0.5",
                  positive ? "trade-up" : "trade-down"
                )}
              >
                {fmtPct(ticker?.price_change_percent)}
              </span>
            </div>
            <p className="text-[10px] text-slate-600 mt-1.5">
              更新时间 {ageLabel(ticker?.fetched_at)} ·{" "}
              {ticker?.source === "demo" ? "本地模拟行情" : "Binance 公共行情"}
            </p>
          </div>
          <button
            type="button"
            onClick={onTrade}
            className="trade-btn trade-btn-outline !min-h-[36px] !px-3 text-[11px] flex-none"
          >
            下单
            <Icon name="chevronRight" size={12} />
          </button>
        </div>

        <div className="mt-4 grid grid-cols-4 gap-2">
          <MarketStat label="24H 高" value={fmtPrice(ticker?.high_price)} />
          <MarketStat label="24H 低" value={fmtPrice(ticker?.low_price)} />
          <MarketStat label="24H 量" value={fmtCompact(ticker?.volume)} />
          <MarketStat label="成交额" value={fmtCompact(ticker?.quote_volume)} />
        </div>
      </section>

      <section className="trade-card p-4">
        <div className="flex items-center justify-between gap-2 mb-4">
          <SectionHeader
            title="价格图表"
            hint={klines ? `${klines.items.length} 根 K 线 · ${klines.source === "demo" ? "SIM" : "BINANCE"}` : "加载中"}
            className="!mb-0"
          />
          <div className="flex items-center gap-1 trade-scroll-x">
            {INTERVALS.map((item) => (
              <button
                key={item.key}
                type="button"
                onClick={() => setIntervalKey(item.key)}
                className={cn(
                  "trade-quick-btn",
                  interval === item.key &&
                    "!border-cyan-300/30 !bg-cyan-400/10 !text-cyan-200"
                )}
              >
                {item.label}
              </button>
            ))}
            <button
              type="button"
              onClick={() => void load(interval)}
              className="trade-quick-btn !px-2"
              aria-label="刷新 K 线"
              disabled={loading}
            >
              {loading ? <Spinner size={12} /> : <Icon name="refresh" size={12} />}
            </button>
          </div>
        </div>

        {chartStale ? (
          <div className="mb-3 flex items-center gap-2 rounded-lg border border-amber-300/20 bg-amber-300/[0.06] px-3 py-2 text-[10px] text-amber-200/75">
            <Icon name="warning" size={12} />
            {!online ? "离线状态：以下为上次缓存视图" : "K 线可能已过期，下单页会再次校验行情"}
          </div>
        ) : null}

        <CandleChart candles={klines?.items ?? []} loading={loading} />

        {error ? (
          <div className="mt-5 flex items-center justify-between rounded-lg border border-rose-400/20 bg-rose-400/[0.06] px-3 py-2 text-[11px] text-rose-200">
            <span>{error}</span>
            <button
              type="button"
              className="font-semibold text-rose-200/80"
              onClick={() => void load(interval)}
            >
              重试
            </button>
          </div>
        ) : null}

        <div className="mt-7 flex items-center justify-between border-t border-white/[0.06] pt-3 text-[10px] text-slate-600">
          <span>未闭合 K 线不用于服务端信号计算</span>
          <span className="trade-number">
            {klines ? `更新 ${ageLabel(klines.fetched_at)}` : "—"}
          </span>
        </div>
      </section>

      <section className="trade-card-flat p-4">
        <div className="flex items-center justify-between">
          <p className="text-[11px] font-semibold text-slate-300">行情说明</p>
          <span className="trade-chip">REST POLL 5s</span>
        </div>
        <div className="mt-3 space-y-2 text-[10px] leading-relaxed text-slate-500">
          <p>
            总览与交易页每 5 秒轮询 NEMT Cloud API；服务端读取 Binance 公共现货行情。
          </p>
          <p>
            K 线图中，未闭合 K 线以当前收盘价绘制；订单确认页始终重新校验行情新鲜度。
          </p>
          {ticker?.source === "demo" ? (
            <p className="text-amber-200/60">
              当前为 DEMO 回退行情：服务端无法访问 Binance 时使用确定性模拟数据，界面上不会伪装成实时行情。
            </p>
          ) : null}
        </div>
        <div className="mt-3 grid grid-cols-2 gap-2 border-t border-white/[0.06] pt-3">
          <div>
            <p className="text-[9px] text-slate-600">事件时间</p>
            <p className="trade-number text-[10px] text-slate-400 mt-0.5">
              {ticker?.event_time
                ? new Date(ticker.event_time).toLocaleString("zh-CN", { hour12: false })
                : "—"}
            </p>
          </div>
          <div className="text-right">
            <p className="text-[9px] text-slate-600">24H 变动额</p>
            <p
              className={cn(
                "trade-number text-[10px] mt-0.5",
                positive ? "trade-up" : "trade-down"
              )}
            >
              {ticker?.price_change ?? "—"} USDT
            </p>
          </div>
        </div>
      </section>
    </div>
  );
}

function MarketStat({ label, value }: { label: string; value: string }) {
  return (
    <div className="min-w-0 rounded-lg bg-black/20 px-2 py-2">
      <p className="text-[9px] text-slate-600">{label}</p>
      <p className="trade-number text-[10px] text-slate-300 mt-0.5 truncate">{value}</p>
    </div>
  );
}
