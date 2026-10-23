"use client";

import { useMemo } from "react";
import { EXECUTION_HEALTH } from "@/lib/studio/contracts";
import { ageLabel, fmtQty, fmtTime, fmtUSDT } from "@/lib/trade/format";
import { ORDER_STATUS_LABEL } from "@/lib/trade/order-status";
import type { Order } from "@/lib/trade/types";
import { accountEquity } from "../account/utils";
import { StatusDot } from "../common";
import {
  EditorialLink,
  EditorialPage,
  Masthead,
  MetricTape,
  PageFootnote,
} from "../editorial/Editorial";
import { AbstractPlate } from "../editorial/AbstractPlate";
import { StudioIcon } from "../icons";
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
  const riskLabel = paused ? "新订单已暂停" : "风险边界待验证";
  const riskHint = paused
    ? system?.risk.pause_reason ?? "全局新订单已暂停"
    : "策略执行与独立风控服务尚未接入，不展示虚构风险分数。";

  return (
    <EditorialPage className="nsx-overview">
      <Masthead
        kicker="NEMT / OPERATIONS DESK · 03"
        title="市场不是噪音，"
        accent="而是正在形成的结构。"
        lead="量化运营驾驶舱。策略、资产、风险与系统状态在同一张操作台上汇合；只渲染经过验证的市场与账户数据。"
        issue={{
          label: online ? "LIVE" : "OFFLINE",
          value: "03",
          note: "OCT · 2026",
        }}
        actions={
          <button
            type="button"
            className="nsx-btn is-small"
            onClick={() => navigate("execution")}
          >
            执行边界
            <StudioIcon name="arrowUpRight" size={12} />
          </button>
        }
      />

      <section className="nsx-overview-hero" aria-label="Capital position">
        <div className="nsx-overview-copy">
          <div className="nsx-eyebrow-row">
            <span>01</span>
            CAPITAL POSITION
          </div>
          <p className="nsx-equity-label">TOTAL EQUITY / USDT</p>
          <div className="nsx-equity">
            {balances ? fmtUSDT(equity) : <span>读取中…</span>}
            {balances ? <span>USDT</span> : null}
          </div>
          <p className="nsx-freshness">
            <StatusDot tone={online ? "ok" : "bad"} />
            {balances
              ? `账户快照 · ${ageLabel(balances.fetched_at)}`
              : "正在读取账户快照"}
          </p>

          <div className="nsx-risk-note">
            <span className="nsx-risk-icon">
              <StudioIcon name="shield" size={16} />
            </span>
            <div>
              <p>RISK NOTE</p>
              <strong>{riskLabel}</strong>
              <span>{riskHint}</span>
            </div>
          </div>

          <button
            type="button"
            className="nsx-btn is-ink"
            onClick={() => navigate("strategies")}
          >
            进入策略研究所
            <StudioIcon name="chevronRight" size={13} />
          </button>
        </div>

        <AbstractPlate
          variant="field"
          label="MARKET FIELD"
          caption="抽象结构线稿 · 不表示净值、收益或行情预测"
          className="nsx-overview-art"
        />
      </section>

      <MetricTape
        items={[
          {
            label: "PnL / 收益",
            value: "尚无数据",
            note: "收益历史服务未接入",
            mono: false,
          },
          {
            label: "Active Strategies",
            value: String(EXECUTION_HEALTH.active_runs).padStart(2, "0"),
            note: "策略执行服务未接入",
          },
          {
            label: "AI Inbox",
            value: "—",
            note: "Publisher API 未接入",
          },
          {
            label: "System Link",
            value: online ? "CONNECTED" : "OFFLINE",
            note: online ? "账户与行情通道在线" : "连接恢复后自动同步",
            accent: online,
          },
        ]}
      />

      <div className="nsx-overview-lower">
        <section className="nsx-overview-block" aria-label="Strategy operations">
          <div className="nsx-block-head">
            <div>
              <div className="nsx-eyebrow-row">
                <span>05</span>
                STRATEGY OPERATIONS
              </div>
              <h2>当前策略台</h2>
            </div>
            <EditorialLink onClick={() => navigate("strategies")}>
              策略研究所
            </EditorialLink>
          </div>
          <div className="nsx-strategy-body">
            <span className="nsx-zero">0</span>
            <div>
              <strong>RUNNING</strong>
              <p>
                尚无运行中的策略。AI 候选需经人工保留与独立审批后，才会进入模拟运行。
              </p>
            </div>
            <span className="nsx-tag is-warn">
              <i aria-hidden="true" />
              Not Connected
            </span>
          </div>
        </section>

        <section className="nsx-overview-block" aria-label="Recent activity">
          <div className="nsx-block-head">
            <div>
              <div className="nsx-eyebrow-row">
                <span>06</span>
                RECENT ACTIVITY
              </div>
              <h2>执行记录</h2>
            </div>
            <EditorialLink onClick={() => navigate("execution")}>
              查看执行
            </EditorialLink>
          </div>

          {!orders ? (
            <div className="nsx-activity-empty" aria-hidden="true">
              <span>—</span>
              <div>
                <strong>LOADING SNAPSHOT</strong>
                <p>正在读取服务端订单记录。</p>
              </div>
            </div>
          ) : recentOrders.length === 0 ? (
            <div className="nsx-activity-empty">
              <span>—</span>
              <div>
                <strong>NO RECENT EXECUTIONS</strong>
                <p>
                  {online
                    ? "新的订单和成交事件会显示在这里。"
                    : "当前离线，恢复连接后会自动刷新。"}
                </p>
              </div>
            </div>
          ) : (
            <div className="nsx-activity-list">
              {recentOrders.map((order) => (
                <ActivityRow key={order.id} order={order} />
              ))}
            </div>
          )}
        </section>
      </div>

      <PageFootnote
        center="Only verified market and account data is rendered. Missing services remain explicit."
      />
    </EditorialPage>
  );
}

function ActivityRow({ order }: { order: Order }) {
  const filled = Number(order.filled_qty);
  const price = order.avg_fill_price ?? order.price;
  return (
    <div className="nsx-activity-row">
      <span
        className={`nsx-side ${order.side === "BUY" ? "is-buy" : "is-sell"}`}
      >
        {order.side === "BUY" ? "B" : "S"}
      </span>
      <div>
        <p>
          {order.symbol}
          <em>{order.type === "MARKET" ? "市价" : "限价"}</em>
        </p>
        <small>
          {fmtQty(filled)} / {fmtQty(order.quantity)} BTC
          {price ? ` · ${fmtUSDT(price)} USDT` : ""}
        </small>
      </div>
      <span className="nsx-tag is-muted">
        {ORDER_STATUS_LABEL[order.status]}
      </span>
      <time>{fmtTime(order.updated_at ?? order.created_at)}</time>
    </div>
  );
}
