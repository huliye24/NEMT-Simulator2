"use client";

import { cn, fmtQty, fmtUSDT, ageLabel } from "@/lib/trade/format";
import type { TradingData } from "../../useTradingData";
import { CardHeader, Skeleton, StatusDot } from "../common";
import { StudioIcon } from "../icons";
import type { StudioSection } from "../types";

interface AccountSummaryProps {
  data: TradingData;
  navigate: (section: StudioSection) => void;
  className?: string;
}

export function findAsset(data: TradingData, asset: string) {
  const item = data.balances?.balances.find((entry) => entry.asset === asset);
  return {
    asset,
    free: Number(item?.free ?? 0),
    locked: Number(item?.locked ?? 0),
    total: Number(item?.total ?? 0),
    raw: item ?? null,
  };
}

export function accountEquity(data: TradingData): number {
  const usdt = findAsset(data, "USDT");
  const btc = findAsset(data, "BTC");
  const btcPrice = Number(data.ticker?.last_price ?? 0);
  return usdt.total + btc.total * btcPrice;
}

export default function AccountSummary({ data, navigate, className = "" }: AccountSummaryProps) {
  const { balances } = data;
  const usdt = findAsset(data, "USDT");
  const btc = findAsset(data, "BTC");
  const lastPrice = Number(data.ticker?.last_price ?? 0);
  const total = accountEquity(data);
  const loaded = Boolean(balances);

  return (
    <section className={`ns-card ns-account-card ${className}`.trim()} aria-label="账户概览">
      <CardHeader
        title="账户概览"
        hint={
          balances?.source === "demo"
            ? "DEMO 模拟账本 · USDT 估值"
            : "现货账户 · USDT 估值"
        }
        action={
          <button type="button" className="ns-text-link ns-text-link-sm" onClick={() => navigate("portfolio")}>
            资产明细
            <StudioIcon name="chevronRight" size={12} />
          </button>
        }
      />

      <div className="ns-account-equity">
        <p className="ns-account-equity-label">总资产估值</p>
        {loaded ? (
          <p className="ns-account-equity-value">
            {fmtUSDT(total)}
            <span>USDT</span>
          </p>
        ) : (
          <Skeleton className="ns-skeleton-equity" />
        )}
        <p className="ns-account-equity-note">
          现货账户 · 不包含合约未实现盈亏
        </p>
      </div>

      <div className="ns-account-balances">
        <div className="ns-account-balance">
          <span className="ns-account-asset">
            <span className="ns-asset-token ns-asset-token-usdt">U</span>
            可用 USDT
          </span>
          <span className="ns-account-value">
            {loaded ? fmtUSDT(usdt.free) : <Skeleton className="ns-skeleton-value" />}
          </span>
        </div>
        <div className="ns-account-balance">
          <span className="ns-account-asset">
            <span className="ns-asset-token ns-asset-token-btc">₿</span>
            可用 BTC
          </span>
          <span className="ns-account-value">
            {loaded ? fmtQty(btc.free) : <Skeleton className="ns-skeleton-value" />}
          </span>
          <span className="ns-account-value-sub">
            ≈ {fmtUSDT(btc.free * lastPrice)} USDT
          </span>
        </div>
      </div>

      <div className="ns-account-foot">
        <span className="ns-account-foot-state">
          <StatusDot
            tone={!balances ? "muted" : balances.connected ? "ok" : balances.account_status === "NOT_CONFIGURED" ? "warn" : "bad"}
          />
          <span>
            {!balances
              ? "正在获取账户快照"
              : balances.connected
                ? balances.stale
                  ? "账户数据延迟"
                  : "账户已同步"
                : balances.account_status === "NOT_CONFIGURED"
                  ? "账户未配置"
                  : "账户连接异常"}
          </span>
        </span>
        <span className={cn("ns-account-foot-age", balances?.stale && "is-warn")}>
          {balances?.fetched_at ? `${ageLabel(balances.fetched_at)}更新` : "—"}
        </span>
      </div>

      {loaded && lastPrice <= 0 ? (
        <p className="ns-account-valuation-note">
          行情等待中，BTC 资产暂按 0 USDT 估值。
        </p>
      ) : null}
    </section>
  );
}
