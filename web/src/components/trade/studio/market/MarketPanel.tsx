"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { tradeApi } from "@/lib/trade/api";
import {
  ageLabel,
  cn,
  fmtCompact,
  fmtPct,
  fmtPrice,
} from "@/lib/trade/format";
import type { Klines } from "@/lib/trade/types";
import type { TradingData } from "../../useTradingData";
import { SourceTag, Skeleton } from "../common";
import { StudioIcon } from "../icons";
import MarketChart from "./MarketChart";

interface MarketPanelProps {
  data: TradingData;
  variant?: "default" | "expanded";
  className?: string;
}

const REFRESH_INTERVAL_MS = 30_000;

export default function MarketPanel({
  data,
  variant = "default",
  className = "",
}: MarketPanelProps) {
  const { ticker, online, feedError } = data;
  const [interval, setIntervalKey] = useState("15m");
  const [klines, setKlines] = useState<Klines | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [reloadKey, setReloadKey] = useState(0);
  const requestRef = useRef(0);

  useEffect(() => {
    const requestId = ++requestRef.current;
    let active = true;

    async function load(background: boolean) {
      if (!active) return;
      if (background) setRefreshing(true);
      else setLoading(true);
      try {
        const next = await tradeApi.getKlines("BTCUSDT", interval, 120);
        if (!active || requestRef.current !== requestId) return;
        setKlines(next);
        setError(null);
      } catch (reason) {
        if (!active || requestRef.current !== requestId) return;
        setError(
          reason instanceof Error ? reason.message : "K 线数据加载失败，请稍后重试"
        );
      } finally {
        if (active && requestRef.current === requestId) {
          setLoading(false);
          setRefreshing(false);
        }
      }
    }

    void load(false);
    const timer = window.setInterval(() => {
      if (!document.hidden && navigator.onLine) void load(true);
    }, REFRESH_INTERVAL_MS);

    return () => {
      active = false;
      window.clearInterval(timer);
    };
  }, [interval, reloadKey]);

  const refresh = useCallback(() => setReloadKey((value) => value + 1), []);

  const change = Number(ticker?.price_change_percent ?? 0);
  const positive = change >= 0;
  const matchingKlines = klines?.interval === interval ? klines : null;
  const candles = matchingKlines?.items ?? [];
  const chartStale = Boolean(matchingKlines?.stale) || Boolean(ticker?.stale) || !online;
  const loadingChart = loading || (!matchingKlines && !error);
  const source = matchingKlines?.source ?? ticker?.source ?? null;

  return (
    <section
      className={`ns-card ns-market-card ns-market-card-${variant} ${className}`.trim()}
      aria-label="BTC/USDT 市场行情"
    >
      <div className="ns-market-head">
        <div className="ns-market-identity">
          <span className="ns-asset-coin" aria-hidden="true">₿</span>
          <div className="ns-market-identity-copy">
            <div className="ns-market-symbol-row">
              <h2 className="ns-market-symbol">
                BTC<span>/USDT</span>
              </h2>
              <span className="ns-market-type">SPOT</span>
            </div>
            <p className="ns-market-subtitle">Bitcoin · US Dollar Tether</p>
          </div>
        </div>

        <div className="ns-market-price-block">
          <div className="ns-market-last">
            {ticker ? (
              <span className="ns-market-last-price">{fmtPrice(ticker.last_price)}</span>
            ) : (
              <Skeleton className="ns-skeleton-price" />
            )}
            <span className={cn("ns-market-change", positive ? "is-up" : "is-down")}>
              {fmtPct(ticker?.price_change_percent)}
            </span>
          </div>
          <div className="ns-market-change-row">
            <span className={cn("ns-market-change-abs", positive ? "is-up" : "is-down")}>
              {positive ? "+" : ""}
              {ticker ? fmtPrice(ticker.price_change) : "—"} USDT
            </span>
            <span className="ns-market-change-window">24H</span>
          </div>
        </div>

        <div className="ns-market-meta">
          <SourceTag source={source} stale={chartStale && source !== "demo"} />
          <span className="ns-market-meta-line">
            <StudioIcon name="clock" size={12} />
            {ticker ? ageLabel(ticker.fetched_at) : "等待行情"}
          </span>
          {!online ? (
            <span className="ns-market-offline">
              <StudioIcon name="warning" size={12} />
              离线
            </span>
          ) : null}
        </div>
      </div>

      <div className="ns-market-stats">
        <MarketStat label="24H 最高" value={fmtPrice(ticker?.high_price)} />
        <MarketStat label="24H 最低" value={fmtPrice(ticker?.low_price)} />
        <MarketStat label="24H 成交量" value={fmtCompact(ticker?.volume)} suffix="BTC" />
        <MarketStat label="24H 成交额" value={fmtCompact(ticker?.quote_volume)} suffix="USDT" />
        <MarketStat
          label="行情状态"
          value={
            !online
              ? "离线"
              : feedError
                ? "异常"
                : ticker?.stale
                  ? "延迟"
                  : ticker
                    ? "正常"
                    : "等待"
          }
          tone={!online || feedError || ticker?.stale ? "warn" : "normal"}
        />
      </div>

      {!ticker && !loading ? (
        <div className="ns-market-unavailable" role="status">
          <StudioIcon name="warning" size={16} />
          <div>
            <p>行情暂不可用</p>
            <span>{feedError ?? "等待 NEMT Cloud 行情服务恢复。"}</span>
          </div>
          <button type="button" className="ns-btn ns-btn-outline ns-btn-sm" onClick={() => void data.refreshAll()}>
            刷新
          </button>
        </div>
      ) : null}

      <MarketChart
        key={interval}
        candles={candles}
        interval={interval}
        source={source}
        stale={chartStale}
        fetchedAt={matchingKlines?.fetched_at ?? null}
        loading={loadingChart}
        refreshing={refreshing}
        error={error}
        onIntervalChange={setIntervalKey}
        onRefresh={refresh}
      />
    </section>
  );
}

function MarketStat({
  label,
  value,
  suffix,
  tone = "normal",
}: {
  label: string;
  value: string;
  suffix?: string;
  tone?: "normal" | "warn";
}) {
  return (
    <div className="ns-market-stat">
      <span className="ns-market-stat-label">{label}</span>
      <span className={cn("ns-market-stat-value", tone === "warn" && "is-warn")}>
        {value}
        {suffix ? <em>{suffix}</em> : null}
      </span>
    </div>
  );
}
