"use client";

import { ageLabel, cn, fmtPct, fmtPrice } from "@/lib/trade/format";
import { PageHeader, SourceTag, StatusDot } from "../common";
import { StudioIcon } from "../icons";
import MarketPanel from "../market/MarketPanel";
import type { StudioPageProps } from "../types";

export default function MarketsPage({ data, navigate }: StudioPageProps) {
  const { ticker, system, online, feedError } = data;
  const positive = Number(ticker?.price_change_percent ?? 0) >= 0;

  return (
    <div className="ns-page">
      <PageHeader
        eyebrow="MARKET / BTC-USDT"
        title="市场行情"
        description="24H 行情快照与多周期 K 线。行情源、更新时间与延迟状态保持可见。"
        actions={
          <button
            type="button"
            className="ns-btn ns-btn-outline ns-btn-sm"
            onClick={() => navigate("execution")}
          >
            <StudioIcon name="orders" size={14} />
            查看订单
          </button>
        }
      />

      <div className="ns-market-workspace">
        <MarketPanel data={data} variant="expanded" />

        <aside className="ns-market-side" aria-label="行情辅助信息">
          <section className="ns-card ns-watchlist" aria-label="自选行情">
            <div className="ns-side-card-head">
              <h2 className="ns-card-title">自选行情</h2>
              <span className="ns-chip">1</span>
            </div>
            <div className="ns-watch-row">
              <span className="ns-watch-asset">
                <span className="ns-asset-token ns-asset-token-btc">₿</span>
                <span>
                  <strong>BTC/USDT</strong>
                  <em>Bitcoin · Spot</em>
                </span>
              </span>
              <span className="ns-watch-values">
                <strong className="ns-number">{fmtPrice(ticker?.last_price)}</strong>
                <span className={cn("ns-number", positive ? "ns-text-up" : "ns-text-down")}>
                  {fmtPct(ticker?.price_change_percent)}
                </span>
              </span>
            </div>
            <p className="ns-side-note">
              当前服务端仅开放 BTC/USDT 现货交易对。
            </p>
          </section>

          <section className="ns-card" aria-label="数据状态">
            <div className="ns-side-card-head">
              <h2 className="ns-card-title">数据状态</h2>
              <StatusDot tone={online && !feedError ? "ok" : online ? "warn" : "bad"} pulse={online && !feedError} />
            </div>
            <dl className="ns-detail-list">
              <div>
                <dt>行情连接</dt>
                <dd>{online ? (feedError ? "异常" : "正常") : "离线"}</dd>
              </div>
              <div>
                <dt>行情源</dt>
                <dd><SourceTag source={ticker?.source} stale={ticker?.stale} /></dd>
              </div>
              <div>
                <dt>最后更新</dt>
                <dd>{ticker ? ageLabel(ticker.fetched_at) : "—"}</dd>
              </div>
              <div>
                <dt>事件时间</dt>
                <dd className="ns-number">
                  {ticker?.event_time
                    ? new Date(ticker.event_time).toLocaleTimeString("zh-CN", { hour12: false })
                    : "—"}
                </dd>
              </div>
              <div>
                <dt>服务端</dt>
                <dd>v{system?.version ?? "—"} · {system?.mode ?? "—"}</dd>
              </div>
              <div>
                <dt>数据通道</dt>
                <dd>REST · 5s / 30s</dd>
              </div>
            </dl>
            <p className="ns-side-note">
              行情与 K 线来自 NEMT Cloud；未闭合 K 线不用于服务端信号计算。
            </p>
          </section>

          <section className="ns-card ns-market-cta" aria-label="执行说明">
            <span className="ns-market-cta-icon">
              <StudioIcon name="shield" size={20} />
            </span>
            <div>
              <h2>执行由策略管理</h2>
              <p>本页仅用于行情监控。人工下单已关闭，策略执行结果可在订单页查看。</p>
            </div>
            <button type="button" className="ns-btn ns-btn-outline ns-btn-sm" onClick={() => navigate("execution")}>
              查看订单
              <StudioIcon name="chevronRight" size={12} />
            </button>
          </section>
        </aside>
      </div>
    </div>
  );
}
