"use client";

import { useMemo } from "react";
import {
  ageLabel,
  cn,
  fmtQty,
  fmtTime,
  fmtUSDT,
} from "@/lib/trade/format";
import { ORDER_STATUS_LABEL } from "@/lib/trade/order-status";
import type { Order } from "@/lib/trade/types";
import { accountEquity } from "../account/utils";
import { EmptyState, PageHeader, Skeleton, StatusDot } from "../common";
import { StudioIcon, type StudioIconName } from "../icons";
import type { StudioPageProps } from "../types";

export default function OverviewPage({ data, navigate }: StudioPageProps) {
  const { balances, orders, system, online } = data;
  const equity = accountEquity(data);
  const recentOrders = useMemo(
    () =>
      [...(orders?.orders ?? [])]
        .sort(
          (a, b) =>
            new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
        )
        .slice(0, 4),
    [orders]
  );

  const paused = Boolean(system?.risk.pause_new_orders);
  const riskValue = paused ? "Paused" : "Unverified";
  const riskHint = paused
    ? system?.risk.pause_reason ?? "全局新订单已暂停"
    : "执行风控服务未接入";
  const riskTone = paused ? "bad" : "warn";

  return (
    <div className="ns-page ns-overview">
      <PageHeader
        eyebrow="WORKSPACE / OVERVIEW"
        title="总览"
        description="Quantitative Operations Dashboard"
        actions={
          <button
            type="button"
            className="ns-btn ns-btn-dark ns-btn-sm"
            onClick={() => navigate("strategies")}
          >
            <StudioIcon name="strategies" size={14} />
            打开策略
          </button>
        }
      />

      <div className="ns-overview-kpis">
        <KpiCard
          icon="assets"
          label="Total Equity"
          value={balances ? `${fmtUSDT(equity)}` : <Skeleton className="ns-skeleton-kpi" />}
          suffix={balances ? "USDT" : undefined}
          hint={balances ? "USDT 估值 · 现货账户" : "正在获取账户快照"}
          tone="neutral"
        />
        <KpiCard
          icon="activity"
          label="PnL"
          value="—"
          hint="收益记录服务未接入"
          tone="neutral"
          muted
        />
        <KpiCard
          icon="strategies"
          label="Strategies"
          value="0"
          suffix="Running"
          hint="策略服务未接入"
          tone="neutral"
        />
        <KpiCard
          icon="shield"
          label="Risk Status"
          value={riskValue}
          hint={riskHint}
          tone={riskTone}
          status
        />
      </div>

      <div className="ns-overview-main">
        <section className="ns-card ns-equity-panel" aria-label="Portfolio equity">
          <div className="ns-overview-panel-head">
            <div>
              <p className="ns-overview-eyebrow">PORTFOLIO</p>
              <h2 className="ns-card-title">净值曲线</h2>
              <p className="ns-card-hint">
                {balances
                  ? `当前净值 ${fmtUSDT(equity)} USDT · ${ageLabel(balances.fetched_at)}`
                  : "等待账户快照"}
              </p>
            </div>
            <button type="button" className="ns-text-link ns-text-link-sm" onClick={() => navigate("portfolio")}>
              投资组合
              <StudioIcon name="chevronRight" size={12} />
            </button>
          </div>
          <div className="ns-equity-empty">
            <EmptyState
              compact
              icon="markets"
              title="暂无净值历史"
              body="净值记录 API 尚未接入。当前不生成模拟收益曲线。"
            />
          </div>
        </section>

        <section className="ns-card ns-strategy-overview" aria-label="Strategy operations">
          <div className="ns-overview-panel-head">
            <div>
              <p className="ns-overview-eyebrow">STRATEGY OPERATIONS</p>
              <h2 className="ns-card-title">策略运行</h2>
              <p className="ns-card-hint">
                <span className="ns-inline-status">
                  <StatusDot tone="muted" />
                  策略服务未接入
                </span>
              </p>
            </div>
            <button type="button" className="ns-text-link ns-text-link-sm" onClick={() => navigate("strategies")}>
              策略中心
              <StudioIcon name="chevronRight" size={12} />
            </button>
          </div>
          <div className="ns-strategy-empty">
            <div className="ns-strategy-empty-count">
              <span>0</span>
              <p>Running strategies</p>
            </div>
            <EmptyState
              compact
              icon="strategies"
              title="尚无运行中的策略"
              body="接入策略服务后，当前运行实例和最近信号会显示在这里。"
            />
          </div>
        </section>
      </div>

      <section className="ns-card ns-overview-activity" aria-label="Recent activity">
        <div className="ns-overview-panel-head">
          <div>
            <p className="ns-overview-eyebrow">RECENT ACTIVITY</p>
            <h2 className="ns-card-title">最近活动</h2>
            <p className="ns-card-hint">执行结果与订单状态更新</p>
          </div>
          <button type="button" className="ns-text-link ns-text-link-sm" onClick={() => navigate("execution")}>
            查看执行
            <StudioIcon name="chevronRight" size={12} />
          </button>
        </div>

        {!orders ? (
          <div className="ns-overview-activity-loading" aria-hidden="true">
            <Skeleton className="ns-skeleton-row" />
            <Skeleton className="ns-skeleton-row" />
          </div>
        ) : recentOrders.length === 0 ? (
          <EmptyState
            compact
            icon="activity"
            title="暂无最近活动"
            body={
              online
                ? "策略执行产生的订单与成交事件会显示在这里。"
                : "当前离线，恢复连接后会自动刷新。"
            }
          />
        ) : (
          <div className="ns-activity-list">
            {recentOrders.map((order) => (
              <ActivityRow key={order.id} order={order} />
            ))}
          </div>
        )}
      </section>
    </div>
  );
}

function KpiCard({
  icon,
  label,
  value,
  suffix,
  hint,
  tone,
  status = false,
  muted = false,
}: {
  icon: StudioIconName;
  label: string;
  value: React.ReactNode;
  suffix?: string;
  hint: string;
  tone: "neutral" | "up" | "down" | "warn" | "bad";
  status?: boolean;
  muted?: boolean;
}) {
  return (
    <section className="ns-kpi-card">
      <div className="ns-kpi-card-head">
        <span className="ns-kpi-label">{label}</span>
        <span className="ns-kpi-icon"><StudioIcon name={icon} size={15} /></span>
      </div>
      <div className={cn("ns-kpi-value", muted && "is-muted", tone !== "neutral" && `is-${tone}`)}>
        {status ? (
          <StatusDot tone={tone === "bad" ? "bad" : tone === "warn" ? "warn" : "ok"} />
        ) : null}
        <span>{value}</span>
        {suffix ? <em>{suffix}</em> : null}
      </div>
      <p className={cn("ns-kpi-hint", status && "is-status")}>{hint}</p>
    </section>
  );
}

function ActivityRow({ order }: { order: Order }) {
  const filled = Number(order.filled_qty);
  const price = order.avg_fill_price ?? order.price;
  return (
    <div className="ns-activity-row">
      <span className={cn("ns-activity-side", order.side === "BUY" ? "is-buy" : "is-sell")}>
        {order.side === "BUY" ? "买" : "卖"}
      </span>
      <div className="ns-activity-copy">
        <p>
          {order.symbol}
          <span>{order.type === "MARKET" ? "市价" : "限价"}</span>
          <span className={cn("ns-status-chip", statusClass(order.status))}>
            {ORDER_STATUS_LABEL[order.status]}
          </span>
        </p>
        <span>
          {fmtQty(filled)} / {fmtQty(order.quantity)} BTC
          {price ? ` · ${fmtUSDT(price)} USDT` : ""}
        </span>
      </div>
      <span className="ns-activity-time">{fmtTime(order.updated_at ?? order.created_at)}</span>
    </div>
  );
}

function statusClass(status: Order["status"]): string {
  if (status === "FILLED") return "is-filled";
  if (status === "PARTIALLY_FILLED" || status === "PENDING_RECONCILIATION") return "is-partial";
  if (status === "REJECTED") return "is-rejected";
  if (status === "NEW") return "is-new";
  return "is-muted";
}
