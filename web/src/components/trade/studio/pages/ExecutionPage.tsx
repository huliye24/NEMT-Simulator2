"use client";

import { useMemo } from "react";
import { ageLabel, cn, fmtPrice, fmtQty, fmtTime, fmtUSDT } from "@/lib/trade/format";
import type { Order, OrderStatus } from "@/lib/trade/types";
import { EXECUTION_HEALTH } from "@/lib/studio/contracts";
import { accountEquity, findAsset } from "../account/AccountSummary";
import { EmptyState, StatusDot } from "../common";
import {
  EditorialPage,
  Masthead,
  StatusTag,
} from "../editorial/Editorial";
import { StudioIcon } from "../icons";
import OrdersPanel from "../orders/OrdersPanel";
import type { ExecutionTab, StudioPageProps } from "../types";

const EXECUTION_TABS: { id: ExecutionTab; label: string; labelEn: string }[] = [
  { id: "runs", label: "运行实例", labelEn: "Active Runs" },
  { id: "orders", label: "订单", labelEn: "Orders" },
  { id: "fills", label: "成交", labelEn: "Fills" },
  { id: "events", label: "事件", labelEn: "Events" },
  { id: "risk", label: "风险", labelEn: "Risk" },
];

const STATUS_LABELS: Record<OrderStatus, string> = {
  NEW: "未成交",
  PARTIALLY_FILLED: "部分成交",
  FILLED: "已成交",
  CANCELED: "已撤销",
  EXPIRED: "已过期",
  REJECTED: "已拒绝",
  PENDING_RECONCILIATION: "待对账",
};

function statusTone(status: OrderStatus): string {
  if (status === "FILLED") return "is-filled";
  if (status === "REJECTED") return "is-rejected";
  if (status === "NEW" || status === "PARTIALLY_FILLED") return "is-new";
  return "is-muted";
}

interface ExecutionEvent {
  id: string;
  at: string;
  title: string;
  detail: string;
  tone: "neutral" | "up" | "down" | "warn";
}

export default function ExecutionPage({
  session,
  data,
  notify,
  navigate,
  route,
}: StudioPageProps) {
  const activeTab: ExecutionTab = route.tab ?? "runs";
  const { orders, system, balances, ticker } = data;
  const fills = useMemo(
    () => (orders?.orders ?? []).flatMap((order) => order.fills),
    [orders]
  );
  const paused = Boolean(system?.risk.pause_new_orders);
  const orderGuard = !system
    ? { value: "Unknown", tone: "muted" as const, hint: "等待服务端状态" }
    : !system.trading_enabled
      ? { value: "Disabled", tone: "muted" as const, hint: "服务端未开放订单写入" }
      : paused
        ? { value: "Paused", tone: "warn" as const, hint: system?.risk.pause_reason ?? "新订单已暂停" }
        : { value: "DEMO Active", tone: "ok" as const, hint: "服务端限额与行情新鲜度校验生效" };

  const events = useMemo(() => buildExecutionEvents(data.orders?.orders ?? [], system), [data.orders, system]);

  const counts: Record<ExecutionTab, number> = {
    runs: EXECUTION_HEALTH.active_runs,
    orders: orders?.count ?? 0,
    fills: fills.length,
    events: events.length,
    risk: 0,
  };

  return (
    <EditorialPage className="nsx-execution">
      <Masthead
        compact
        kicker="EXECUTION DESK / 04"
        title="执行台"
        accent="Automation under independent risk control."
        lead="执行服务、策略实例与风控状态彼此独立。Studio 不提供人工下单面板；订单与成交只来自服务端已有记录。"
        issue={{ label: "EXECUTION", value: "04", note: session.mode }}
        actions={
          <>
            <StatusTag tone={session.mode === "LIVE" ? "bad" : "brand"}>
              {session.mode}
            </StatusTag>
            <button
              type="button"
              className="nsx-btn is-small"
              onClick={() => void data.refreshAll()}
              disabled={data.syncing || !data.online}
            >
              <StudioIcon name="refresh" size={12} />
              {data.syncing ? "同步中…" : "刷新"}
            </button>
          </>
        }
      />

      <div className="nsx-exec-strip" aria-label="执行状态">
        <ExecutionStatusItem
          label="Execution Service"
          value="Not Connected"
          hint="策略执行服务尚未接入"
          tone="warn"
        />
        <ExecutionStatusItem
          label="Active Runs"
          value={String(EXECUTION_HEALTH.active_runs)}
          hint="当前没有自动执行实例"
          tone="muted"
        />
        <ExecutionStatusItem
          label="Strategy Risk Control"
          value="Unknown"
          hint="策略级风险校验未接入，不标记为安全"
          tone="warn"
        />
        <ExecutionStatusItem
          label="Server Order Guard"
          value={orderGuard.value}
          hint={orderGuard.hint}
          tone={orderGuard.tone}
        />
      </div>

      <p className="nsx-note" style={{ paddingTop: 10 }}>
        人工买卖表单已从主工作台移除。下方订单与成交仅来自服务端已有 DEMO
        记录；策略执行仍需要独立的云端服务与授权。
      </p>

      <div className="ns-exec-tabs" role="tablist" aria-label="执行模块">
        {EXECUTION_TABS.map((tab) => (
          <button
            key={tab.id}
            type="button"
            role="tab"
            aria-selected={activeTab === tab.id}
            className={cn("ns-exec-tab", activeTab === tab.id && "is-active")}
            onClick={() => navigate("execution", { tab: tab.id })}
          >
            <span>{tab.label}</span>
            <em>{tab.labelEn}</em>
            {counts[tab.id] > 0 ? <b>{counts[tab.id]}</b> : null}
          </button>
        ))}
      </div>

      <div className="ns-exec-content">
        {activeTab === "runs" ? (
          <RunsTab data={data} navigate={navigate} />
        ) : activeTab === "orders" ? (
          <OrdersPanel
            session={session}
            data={data}
            notify={notify}
            navigate={navigate}
            defaultTab="open"
            visibleTabs={["open", "history"]}
          />
        ) : activeTab === "fills" ? (
          <OrdersPanel
            session={session}
            data={data}
            notify={notify}
            navigate={navigate}
            defaultTab="trades"
            visibleTabs={["trades"]}
            hideTabs
            className="ns-embedded-orders"
          />
        ) : activeTab === "events" ? (
          <EventsTab events={events} />
        ) : (
          <RiskTab data={data} orderGuard={orderGuard} paused={paused} />
        )}
      </div>
    </EditorialPage>
  );
}

function ExecutionStatusItem({
  label,
  value,
  hint,
  tone,
}: {
  label: string;
  value: string;
  hint: string;
  tone: "ok" | "warn" | "muted" | "bad";
}) {
  return (
    <div className="nsx-exec-item">
      <span>
        <StatusDot tone={tone} />
        {label}
      </span>
      <strong
        className={
          tone === "ok" ? "is-ok" : tone === "warn" || tone === "bad" ? "is-warn" : undefined
        }
      >
        {value}
      </strong>
      <p>{hint}</p>
    </div>
  );
}

function RunsTab({
  data,
  navigate,
}: {
  data: StudioPageProps["data"];
  navigate: StudioPageProps["navigate"];
}) {
  const recentOrders = (data.orders?.orders ?? []).slice(0, 5);
  return (
    <div className="ns-exec-runs">
      <section className="ns-card">
        <EmptyState
          icon="execution"
          title="没有运行中的执行实例"
          body="策略运行、暂停和信号由 NEMT Cloud 执行服务管理。当前执行服务未接入，因此不会展示虚构实例。"
          action={
            <button
              type="button"
              className="ns-btn ns-btn-outline ns-btn-sm"
              onClick={() => navigate("strategies")}
            >
              查看策略
            </button>
          }
        />
      </section>

      <section className="ns-card ns-exec-history" aria-label="执行历史">
        <div className="ns-exec-card-head">
          <div>
            <h2>Execution History</h2>
            <p>服务端 DEMO 订单记录的最近活动</p>
          </div>
          <button
            type="button"
            className="ns-text-link ns-text-link-sm"
            onClick={() => navigate("execution", { tab: "orders" })}
          >
            全部订单
            <StudioIcon name="chevronRight" size={12} />
          </button>
        </div>
        {recentOrders.length === 0 ? (
          <EmptyState
            compact
            icon="orders"
            title="No execution records"
            body="当前没有订单或成交记录。人工下单不在 Studio 工作台提供。"
          />
        ) : (
          <ul className="ns-exec-history-list">
            {recentOrders.map((order) => (
              <li key={order.id}>
                <button
                  type="button"
                  className="ns-exec-history-row"
                  onClick={() => navigate("execution", { tab: "orders" })}
                >
                  <span className={cn("ns-exec-side", order.side === "BUY" ? "is-buy" : "is-sell")}>
                    {order.side === "BUY" ? "买" : "卖"}
                  </span>
                  <span className="ns-exec-history-main">
                    <strong>
                      {order.symbol}
                      <span className="ns-exec-history-type">
                        {order.type === "MARKET" ? "市价" : "限价"}
                      </span>
                    </strong>
                    <em>{fmtTime(order.updated_at || order.created_at)}</em>
                  </span>
                  <span className="ns-exec-history-num">
                    <strong className="ns-number">{fmtQty(order.filled_qty || order.quantity)} BTC</strong>
                    <em className="ns-number">{fmtPrice(order.avg_fill_price ?? order.price)} USDT</em>
                  </span>
                  <span className={cn("ns-status-chip", statusTone(order.status))}>
                    {STATUS_LABELS[order.status]}
                  </span>
                </button>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}

function EventsTab({ events }: { events: ExecutionEvent[] }) {
  return (
    <section className="ns-card ns-exec-events" aria-label="执行事件">
      <div className="ns-exec-card-head">
        <div>
          <h2>Execution Events</h2>
          <p>来自真实订单、成交记录与系统状态的只读事件流</p>
        </div>
        <span className="ns-chip">Live-derived</span>
      </div>
      {events.length === 0 ? (
        <EmptyState
          icon="activity"
          title="暂无执行事件"
          body="订单提交、成交、撤单与系统风控事件会按服务端时间显示在这里。"
        />
      ) : (
        <ol className="ns-exec-event-list">
          {events.map((event) => (
            <li key={event.id}>
              <span className={cn("ns-exec-event-dot", `is-${event.tone}`)} />
              <div className="ns-exec-event-copy">
                <strong>{event.title}</strong>
                <p>{event.detail}</p>
              </div>
              <time>{fmtTime(event.at)}</time>
            </li>
          ))}
        </ol>
      )}
    </section>
  );
}

function RiskTab({
  data,
  orderGuard,
  paused,
}: {
  data: StudioPageProps["data"];
  orderGuard: { value: string; tone: "ok" | "warn" | "muted"; hint: string };
  paused: boolean;
}) {
  const btc = findAsset(data, "BTC");
  const price = Number(data.ticker?.last_price ?? 0);
  const exposure = btc.total * price;
  const equity = accountEquity(data);
  const limits = data.system?.limits;

  return (
    <div className="ns-exec-risk-grid">
      <section className="ns-card ns-risk-card">
        <div className="ns-exec-card-head">
          <div>
            <h2>Strategy Risk Validation</h2>
            <p>策略信号到执行之间的独立风控层</p>
          </div>
          <span className="ns-chip ns-chip-warn">Unknown / Not Connected</span>
        </div>
        <EmptyState
          compact
          icon="shield"
          title="策略风控尚未接入"
          body="未部署策略不等于风险为零。策略级敞口、回撤暂停和订单防护必须由独立执行服务强制。"
        />
      </section>

      <section className="ns-card ns-risk-card">
        <div className="ns-exec-card-head">
          <div>
            <h2>Server Order Guard</h2>
            <p>现有服务端订单限额与风控校验</p>
          </div>
          <span
            className={cn(
              "ns-chip",
              orderGuard.tone === "ok"
                ? "ns-chip-brand"
                : orderGuard.tone === "warn"
                  ? "ns-chip-warn"
                  : ""
            )}
          >
            <StatusDot tone={orderGuard.tone} />
            {orderGuard.value}
          </span>
        </div>
        {limits ? (
          <dl className="ns-risk-limits">
            <div>
              <dt>单笔名义金额</dt>
              <dd>{limits.min_order_notional} – {limits.max_order_notional} USDT</dd>
            </div>
            <div>
              <dt>单日累计上限</dt>
              <dd>{limits.max_daily_notional} USDT</dd>
            </div>
            <div>
              <dt>最大持仓估值</dt>
              <dd>{limits.max_position_notional} USDT</dd>
            </div>
            <div>
              <dt>未完成订单上限</dt>
              <dd>{limits.max_open_orders} 笔</dd>
            </div>
            <div>
              <dt>下单频率</dt>
              <dd>{limits.max_orders_per_minute} 笔 / 分钟</dd>
            </div>
            <div>
              <dt>行情过期阈值</dt>
              <dd>{limits.market_stale_seconds} 秒</dd>
            </div>
          </dl>
        ) : (
          <EmptyState compact icon="shield" title="限额暂不可用" body="等待服务端状态同步。" />
        )}
        <p className="ns-risk-note">
          {paused
            ? data.system?.risk.pause_reason ?? "服务端已暂停新订单。"
            : "所有硬性限额由服务端强制执行；浏览器不能绕过或覆盖。"}
        </p>
      </section>

      <section className="ns-card ns-risk-card ns-risk-exposure">
        <div className="ns-exec-card-head">
          <div>
            <h2>Known Exposure</h2>
            <p>仅基于当前 DEMO 现货账户与订单快照</p>
          </div>
        </div>
        <div className="ns-risk-exposure-grid">
          <div>
            <span>BTC 现货敞口</span>
            <strong className="ns-number">
              {data.balances ? `${fmtUSDT(exposure)} USDT` : "—"}
            </strong>
            <em>{btc.total > 0 ? `${fmtQty(btc.total)} BTC` : "无 BTC 持仓"}</em>
          </div>
          <div>
            <span>总资产估值</span>
            <strong className="ns-number">
              {data.balances ? `${fmtUSDT(equity)} USDT` : "—"}
            </strong>
            <em>{data.balances?.source === "demo" ? "DEMO 模拟账本" : "账户快照"}</em>
          </div>
          <div>
            <span>未完成订单</span>
            <strong className="ns-number">{data.orders?.open_count ?? 0}</strong>
            <em>当前委托数</em>
          </div>
          <div>
            <span>行情新鲜度</span>
            <strong className="ns-number">
              {data.ticker ? ageLabel(data.ticker.fetched_at) : "—"}
            </strong>
            <em>{data.ticker?.stale ? "已超过阈值" : "用于估值与风控校验"}</em>
          </div>
        </div>
        <p className="ns-risk-note">
          此面板不推断策略未来敞口，也不提供“安全”结论；无数据时保持未知状态。
        </p>
      </section>
    </div>
  );
}

function buildExecutionEvents(
  orders: Order[],
  system: StudioPageProps["data"]["system"]
): ExecutionEvent[] {
  const events: ExecutionEvent[] = [];

  for (const order of orders) {
    events.push({
      id: `${order.id}-created`,
      at: order.created_at,
      title: "委托创建",
      detail: `${order.side === "BUY" ? "买入" : "卖出"} ${fmtQty(order.quantity)} ${order.symbol} · ${
        order.type === "MARKET" ? "市价" : `限价 ${fmtPrice(order.price)}`
      }`,
      tone: "neutral",
    });

    for (const fill of order.fills) {
      events.push({
        id: `${order.id}-${fill.id}`,
        at: fill.filled_at,
        title: "成交",
        detail: `${order.side === "BUY" ? "买入" : "卖出"} ${fmtQty(fill.quantity)} BTC @ ${fmtPrice(
          fill.price
        )} USDT · 费 ${fmtQty(fill.commission)} ${fill.commission_asset ?? ""}`,
        tone: order.side === "BUY" ? "up" : "down",
      });
    }

    if (order.status !== "NEW" && order.status !== "PARTIALLY_FILLED") {
      events.push({
        id: `${order.id}-status`,
        at: order.updated_at,
        title: STATUS_LABELS[order.status],
        detail:
          order.error_message ??
          `${order.symbol} · 已成交 ${fmtQty(order.filled_qty)} / ${fmtQty(order.quantity)} BTC`,
        tone:
          order.status === "REJECTED" || order.status === "EXPIRED"
            ? "warn"
            : "neutral",
      });
    }
  }

  if (system?.risk.pause_new_orders) {
    events.push({
      id: "risk-pause",
      at: system.risk.pause_updated_at ?? system.server_time,
      title: "风控暂停新订单",
      detail:
        system.risk.pause_reason ??
        `管理员 ${system.risk.pause_updated_by ?? "system"} 暂停全部新订单`,
      tone: "warn",
    });
  }

  return events
    .sort((a, b) => new Date(b.at).getTime() - new Date(a.at).getTime())
    .slice(0, 40);
}
