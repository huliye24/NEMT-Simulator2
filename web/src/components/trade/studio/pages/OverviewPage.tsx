"use client";

import { useMemo } from "react";
import { ageLabel, cn, fmtQty, fmtTime, fmtUSDT } from "@/lib/trade/format";
import { ORDER_STATUS_LABEL } from "@/lib/trade/order-status";
import type { Order } from "@/lib/trade/types";
import { accountEquity } from "../account/utils";
import { Skeleton, StatusDot } from "../common";
import { StudioIcon } from "../icons";
import type { StudioPageProps } from "../types";
import styles from "./OverviewPage.module.css";

export default function OverviewPage({ data, navigate }: StudioPageProps) {
  const { balances, orders, system, online } = data;
  const equity = accountEquity(data);
  const recentOrders = useMemo(
    () => [...(orders?.orders ?? [])].sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()).slice(0, 4),
    [orders]
  );
  const paused = Boolean(system?.risk.pause_new_orders);
  const riskLabel = paused ? "新订单已暂停" : "风险边界待验证";
  const riskHint = paused ? system?.risk.pause_reason ?? "全局新订单已暂停" : "执行风控服务尚未接入，不展示虚构风险分数。";

  return (
    <div className={cn("ns-page ns-overview", styles.page)}>
      <header className={styles.masthead}>
        <div>
          <p className={styles.kicker}>NEMT / OPERATIONS DESK · 03</p>
          <h1>市场不是噪音，<br /><em>而是正在形成的结构。</em></h1>
          <p className={styles.lead}>量化运营驾驶舱 · 策略、资产、风险与系统状态</p>
        </div>
        <div className={styles.issueMark} aria-hidden="true"><span>LIVE</span><strong>03</strong><small>OCT · 2026</small></div>
      </header>

      <section className={styles.hero} aria-label="Portfolio briefing">
        <div className={styles.heroCopy}>
          <div className={styles.sectionLabel}><span>01</span> CAPITAL POSITION</div>
          <p className={styles.overline}>TOTAL EQUITY / USDT</p>
          <div className={styles.equity}>
            {balances ? fmtUSDT(equity) : <Skeleton className="ns-skeleton-kpi" />}
            {balances ? <span>USDT</span> : null}
          </div>
          <p className={styles.freshness}><StatusDot tone={online ? "ok" : "bad"} />{balances ? `账户快照 · ${ageLabel(balances.fetched_at)}` : "正在读取账户快照"}</p>
          <div className={styles.riskNote}>
            <span className={styles.riskIcon}><StudioIcon name="shield" size={18} /></span>
            <div><p>RISK NOTE</p><strong>{riskLabel}</strong><span>{riskHint}</span></div>
          </div>
          <button type="button" className={styles.primaryAction} onClick={() => navigate("strategies")}>进入策略工作区 <StudioIcon name="chevronRight" size={15} /></button>
        </div>
        <MarketSketch paused={paused} />
      </section>

      <section className={styles.tape} aria-label="Operational metrics">
        <Metric index="02" label="PnL / 收益" value="尚无数据" note="收益历史服务未接入" />
        <Metric index="03" label="Active Strategies" value="00" note="等待策略执行服务" mono />
        <Metric index="04" label="System Link" value={online ? "CONNECTED" : "OFFLINE"} note={online ? "账户与行情通道在线" : "连接恢复后自动同步"} accent={online} mono />
      </section>

      <div className={styles.lowerGrid}>
        <section className={styles.editorialPanel} aria-label="Strategy operations">
          <div className={styles.panelHead}><div><p className={styles.sectionLabel}><span>05</span> STRATEGY OPERATIONS</p><h2>当前策略台</h2></div><button type="button" onClick={() => navigate("strategies")}>策略中心 ↗</button></div>
          <div className={styles.strategyBody}>
            <span className={styles.zero}>0</span>
            <div><strong>RUNNING</strong><p>尚无运行中的策略。接入执行服务后，实例、信号和状态会在此汇合。</p></div>
            <div className={styles.signalDoodle} aria-hidden="true"><i /><i /><i /><i /><i /></div>
          </div>
        </section>

        <section className={styles.activityPanel} aria-label="Recent activity">
          <div className={styles.panelHead}><div><p className={styles.sectionLabel}><span>06</span> RECENT ACTIVITY</p><h2>执行记录</h2></div><button type="button" onClick={() => navigate("execution")}>查看全部 ↗</button></div>
          {!orders ? (
            <div className={styles.loading} aria-hidden="true"><Skeleton className="ns-skeleton-row" /><Skeleton className="ns-skeleton-row" /></div>
          ) : recentOrders.length === 0 ? (
            <div className={styles.emptyActivity}><span>—</span><div><strong>NO RECENT EXECUTIONS</strong><p>{online ? "新的订单和成交事件会显示在这里。" : "当前离线，恢复连接后会自动刷新。"}</p></div></div>
          ) : (
            <div className={styles.activityList}>{recentOrders.map((order) => <ActivityRow key={order.id} order={order} />)}</div>
          )}
        </section>
      </div>

      <footer className={styles.pageNote}><span>NEMT STUDIO</span><p>Only verified market and account data is rendered. Missing services remain explicit.</p><span>NON-EQUILIBRIUM / 2026</span></footer>
    </div>
  );
}

function MarketSketch({ paused }: { paused: boolean }) {
  return (
    <div className={styles.sketch} aria-label="Abstract market structure illustration">
      <div className={styles.sketchMeta}><span>MARKET FIELD</span><span>ψ / Δt</span></div>
      <svg viewBox="0 0 620 420" role="img" aria-label="抽象行情结构线稿">
        <defs><pattern id="overview-grid" width="31" height="31" patternUnits="userSpaceOnUse"><path d="M31 0H0V31" fill="none" stroke="currentColor" strokeOpacity=".09" /></pattern></defs>
        <rect width="620" height="420" fill="url(#overview-grid)" />
        <path className={styles.orbit} d="M45 302C124 231 164 342 229 258S343 125 411 192s94 26 164-87" />
        <path className={styles.orbitFaint} d="M41 333C124 278 174 368 257 294s107-162 166-100 84 54 151-9" />
        <path className={styles.axis} d="M45 56V354H579" />
        <circle className={styles.sun} cx="411" cy="192" r="15" /><circle className={styles.ring} cx="411" cy="192" r="47" /><circle className={styles.ring} cx="411" cy="192" r="79" />
        <path className={styles.arrow} d="M509 139l48-37m-10 1 10-1-3 10" />
        <g className={styles.candles}><path d="M111 245v54m-9-34h18v22h-18zM151 219v58m-9-42h18v25h-18zM191 227v67m-9-48h18v31h-18zM231 181v89m-9-62h18v41h-18z" /></g>
        <text x="48" y="45">STRUCTURE / NOT NOISE</text><text x="441" y="205">CRITICAL POINT</text><text x="48" y="383">t₀</text><text x="555" y="383">tₙ</text>
      </svg>
      <div className={styles.sketchCaption}><span className={paused ? styles.badDot : styles.cyanDot} />{paused ? "ORDER FLOW PAUSED" : "OBSERVATION MODE · LIVE DATA"}</div>
    </div>
  );
}

function Metric({ index, label, value, note, mono, accent }: { index: string; label: string; value: string; note: string; mono?: boolean; accent?: boolean }) {
  return <article className={styles.metric}><span className={styles.metricIndex}>{index}</span><p>{label}</p><strong className={cn(mono && styles.mono, accent && styles.accent)}>{value}</strong><small>{note}</small></article>;
}

function ActivityRow({ order }: { order: Order }) {
  const filled = Number(order.filled_qty);
  const price = order.avg_fill_price ?? order.price;
  return (
    <div className={styles.activityRow}>
      <span className={cn(styles.side, order.side === "BUY" ? styles.buy : styles.sell)}>{order.side === "BUY" ? "B" : "S"}</span>
      <div><p>{order.symbol}<em>{order.type === "MARKET" ? "市价" : "限价"}</em></p><small>{fmtQty(filled)} / {fmtQty(order.quantity)} BTC{price ? ` · ${fmtUSDT(price)} USDT` : ""}</small></div>
      <span className={styles.orderStatus}>{ORDER_STATUS_LABEL[order.status]}</span><time>{fmtTime(order.updated_at ?? order.created_at)}</time>
    </div>
  );
}
