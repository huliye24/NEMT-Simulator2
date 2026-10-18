"use client";

import { useId, useMemo, useState } from "react";
import { ApiError, tradeApi } from "@/lib/trade/api";
import {
  cn,
  fmtPrice,
  fmtQty,
  fmtTime,
} from "@/lib/trade/format";
import { isOpenOrder } from "@/lib/trade/order-status";
import type {
  Fill,
  Order,
  OrderStatus,
  Session,
} from "@/lib/trade/types";
import type { TradingData } from "../../useTradingData";
import type { StudioNotify, StudioSection } from "../types";
import { EmptyState, Skeleton, Spinner } from "../common";
import { StudioIcon } from "../icons";

type OrdersTab = "open" | "history" | "trades";

interface OrdersPanelProps {
  session: Session;
  data: TradingData;
  notify: StudioNotify;
  navigate: (section: StudioSection) => void;
  compact?: boolean;
  className?: string;
}

interface FillRow {
  fill: Fill;
  order: Order;
}

const STATUS_LABELS: Record<OrderStatus, string> = {
  NEW: "未成交",
  PARTIALLY_FILLED: "部分成交",
  FILLED: "已成交",
  CANCELED: "已撤销",
  EXPIRED: "已过期",
  REJECTED: "已拒绝",
  PENDING_RECONCILIATION: "待对账",
};

function statusClass(status: OrderStatus): string {
  switch (status) {
    case "FILLED":
      return "is-filled";
    case "PARTIALLY_FILLED":
    case "PENDING_RECONCILIATION":
      return "is-partial";
    case "REJECTED":
      return "is-rejected";
    case "NEW":
      return "is-new";
    default:
      return "is-muted";
  }
}

function canCancel(order: Order): boolean {
  return order.status === "NEW" || order.status === "PARTIALLY_FILLED";
}

function orderPrice(order: Order): string {
  if (order.avg_fill_price != null) return fmtPrice(order.avg_fill_price);
  if (order.price != null) return fmtPrice(order.price);
  return "市价";
}

export default function OrdersPanel({
  session,
  data,
  notify,
  navigate,
  compact = false,
  className = "",
}: OrdersPanelProps) {
  const id = useId();
  const { orders, online, coreError } = data;
  const [tab, setTab] = useState<OrdersTab>("open");
  const [refreshing, setRefreshing] = useState(false);
  const [cancelConfirmId, setCancelConfirmId] = useState<string | null>(null);
  const [cancelingId, setCancelingId] = useState<string | null>(null);

  const allOrders = useMemo(() => orders?.orders ?? [], [orders]);
  const openOrders = useMemo(
    () => allOrders.filter((order) => isOpenOrder(order.status)),
    [allOrders]
  );
  const historyOrders = useMemo(
    () => allOrders.filter((order) => !isOpenOrder(order.status)),
    [allOrders]
  );
  const fills = useMemo<FillRow[]>(
    () =>
      allOrders
        .flatMap((order) => order.fills.map((fill) => ({ fill, order })))
        .sort(
          (a, b) =>
            new Date(b.fill.filled_at).getTime() - new Date(a.fill.filled_at).getTime()
        ),
    [allOrders]
  );

  async function refresh() {
    if (refreshing) return;
    setRefreshing(true);
    try {
      await data.refreshOrders();
    } finally {
      setRefreshing(false);
    }
  }

  async function cancelOrder(order: Order) {
    if (cancelingId) return;
    setCancelingId(order.id);
    try {
      const canceled = await tradeApi.cancelOrder(session.csrf_token, order.id);
      setCancelConfirmId(null);
      notify("success", `订单已撤销 · ${STATUS_LABELS[canceled.status]}`);
      await data.refreshAll();
    } catch (error) {
      notify(
        "error",
        error instanceof ApiError ? error.message : "撤单失败，请刷新后核对订单状态"
      );
      await data.refreshAll();
    } finally {
      setCancelingId(null);
    }
  }

  if (!orders && !coreError) {
    return (
      <section className={cn("ns-card ns-orders-card", className)} aria-label="订单与成交">
        <OrdersHead
          id={id}
          tab={tab}
          setTab={setTab}
          counts={{ open: 0, history: 0, trades: 0 }}
          refreshing={refreshing}
          onRefresh={() => void refresh()}
          compact={compact}
          onViewAll={() => navigate("execution")}
        />
        <div className="ns-orders-loading">
          <Skeleton className="ns-skeleton-row" />
          <Skeleton className="ns-skeleton-row" />
          <Skeleton className="ns-skeleton-row" />
        </div>
      </section>
    );
  }

  const visibleOrders = tab === "open" ? openOrders : historyOrders;
  const maxRows = compact ? 5 : visibleOrders.length;
  const visibleFills = compact ? fills.slice(0, 5) : fills;
  const loading = !orders && !coreError;

  return (
    <section
      className={cn("ns-card ns-orders-card", compact && "is-compact", className)}
      aria-label="订单与成交"
    >
      <OrdersHead
        id={id}
        tab={tab}
        setTab={setTab}
        counts={{
          open: orders?.open_count ?? openOrders.length,
          history: historyOrders.length,
          trades: fills.length,
        }}
        refreshing={refreshing}
        onRefresh={() => void refresh()}
        compact={compact}
        onViewAll={() => navigate("execution")}
      />

      <div
        className="ns-orders-panel"
        id={`${id}-panel`}
        role="tabpanel"
        aria-labelledby={`${id}-tab-${tab}`}
      >
        {loading ? (
          <OrdersLoading />
        ) : !orders && coreError ? (
          <EmptyState
            compact={compact}
            icon="warning"
            title="订单数据暂不可用"
            body={coreError}
            action={
              <button type="button" className="ns-btn ns-btn-outline ns-btn-sm" onClick={() => void refresh()}>
                重新获取
              </button>
            }
          />
        ) : tab === "trades" ? (
          fills.length === 0 ? (
            <EmptyState
              compact={compact}
              icon="activity"
              title="暂无成交记录"
              body="订单成交后，逐笔成交明细会显示在这里。"
            />
          ) : (
            <>
              <div className="ns-table-scroll">
                <table className="ns-data-table ns-trades-table">
                  <thead>
                    <tr>
                      <th>成交时间</th>
                      <th>交易对</th>
                      <th>方向</th>
                      <th className="is-numeric">成交价格</th>
                      <th className="is-numeric">成交数量</th>
                      <th className="is-numeric">手续费</th>
                    </tr>
                  </thead>
                  <tbody>
                    {visibleFills.map(({ fill, order }) => (
                      <tr key={`${order.id}-${fill.id}`}>
                        <td className="ns-time-cell">{fmtTime(fill.filled_at)}</td>
                        <td className="ns-symbol-cell">{order.symbol}</td>
                        <td>
                          <span className={cn("ns-side-text", order.side === "BUY" ? "is-buy" : "is-sell")}>
                            {order.side === "BUY" ? "买入" : "卖出"}
                          </span>
                        </td>
                        <td className="is-numeric ns-number">{fmtPrice(fill.price)}</td>
                        <td className="is-numeric ns-number">{fmtQty(fill.quantity)} BTC</td>
                        <td className="is-numeric ns-number ns-muted-cell">
                          {fmtQty(fill.commission)} {fill.commission_asset ?? ""}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <div className="ns-order-mobile-list">
                {visibleFills.map(({ fill, order }) => (
                  <article className="ns-mobile-order" key={`${order.id}-${fill.id}-mobile`}>
                    <div className="ns-mobile-order-row">
                      <span className={cn("ns-side-text", order.side === "BUY" ? "is-buy" : "is-sell")}>
                        {order.side === "BUY" ? "买入" : "卖出"} {order.symbol}
                      </span>
                      <span className="ns-number ns-mobile-order-price">{fmtPrice(fill.price)}</span>
                    </div>
                    <div className="ns-mobile-order-meta">
                      <span>{fmtTime(fill.filled_at)}</span>
                      <span className="ns-number">{fmtQty(fill.quantity)} BTC</span>
                      <span>费 {fmtQty(fill.commission)} {fill.commission_asset ?? ""}</span>
                    </div>
                  </article>
                ))}
              </div>
            </>
          )
        ) : visibleOrders.length === 0 ? (
          <EmptyState
            compact={compact}
            icon={tab === "open" ? "orders" : "fileText"}
            title={tab === "open" ? "没有未完成订单" : "暂无订单历史"}
            body={
              tab === "open"
                ? "策略执行产生的未完成委托会显示在这里，可对未成交部分执行撤销。"
                : "已成交、已撤销的订单位置会保存在这里。"
            }
            action={
              tab === "open" ? (
                <button type="button" className="ns-btn ns-btn-outline ns-btn-sm" onClick={() => void refresh()}>
                  <StudioIcon name="refresh" size={12} />
                  刷新订单
                </button>
              ) : undefined
            }
          />
        ) : (
          <>
            <div className="ns-table-scroll">
              <table className="ns-data-table">
                <thead>
                  <tr>
                    <th>时间</th>
                    <th>交易对</th>
                    <th>方向</th>
                    <th>类型</th>
                    <th className="is-numeric">委托价格</th>
                    <th className="is-numeric">数量</th>
                    <th className="is-numeric">已成交</th>
                    <th>状态</th>
                    <th className="is-actions">操作</th>
                  </tr>
                </thead>
                <tbody>
                  {visibleOrders.slice(0, maxRows).map((order) => {
                    const cancelable = tab === "open" && canCancel(order) && online;
                    const confirming = cancelConfirmId === order.id;
                    const canceling = cancelingId === order.id;
                    return (
                      <tr key={order.id}>
                        <td className="ns-time-cell">{fmtTime(order.created_at)}</td>
                        <td className="ns-symbol-cell">
                          {order.symbol}
                          {order.mode !== "DEMO" ? (
                            <span className="ns-table-mode">{order.mode}</span>
                          ) : null}
                        </td>
                        <td>
                          <span className={cn("ns-side-text", order.side === "BUY" ? "is-buy" : "is-sell")}>
                            {order.side === "BUY" ? "买入" : "卖出"}
                          </span>
                        </td>
                        <td className="ns-muted-cell">{order.type === "MARKET" ? "市价" : "限价"}</td>
                        <td className="is-numeric ns-number">{orderPrice(order)}</td>
                        <td className="is-numeric ns-number">{fmtQty(order.quantity)} BTC</td>
                        <td className="is-numeric ns-number">{fmtQty(order.filled_qty)} BTC</td>
                        <td>
                          <span className={cn("ns-status-chip", statusClass(order.status))}>
                            {STATUS_LABELS[order.status]}
                          </span>
                        </td>
                        <td className="is-actions">
                          {cancelable ? (
                            confirming ? (
                              <span className="ns-cancel-confirm">
                                <button
                                  type="button"
                                  className="ns-link-danger"
                                  onClick={() => void cancelOrder(order)}
                                  disabled={canceling}
                                >
                                  {canceling ? <Spinner size={11} /> : "确认撤单"}
                                </button>
                                <button
                                  type="button"
                                  className="ns-link-muted"
                                  onClick={() => setCancelConfirmId(null)}
                                  disabled={canceling}
                                >
                                  取消
                                </button>
                              </span>
                            ) : (
                              <button
                                type="button"
                                className="ns-table-action"
                                onClick={() => setCancelConfirmId(order.id)}
                              >
                                撤单
                              </button>
                            )
                          ) : (
                            <span className="ns-action-placeholder">—</span>
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>

            <div className="ns-order-mobile-list">
              {visibleOrders.slice(0, maxRows).map((order) => {
                const cancelable = tab === "open" && canCancel(order) && online;
                const confirming = cancelConfirmId === order.id;
                const canceling = cancelingId === order.id;
                return (
                  <article className="ns-mobile-order" key={`${order.id}-mobile`}>
                    <div className="ns-mobile-order-row">
                      <span className="ns-mobile-order-name">
                        <span className={cn("ns-side-badge", order.side === "BUY" ? "is-buy" : "is-sell")}>
                          {order.side === "BUY" ? "买" : "卖"}
                        </span>
                        {order.symbol}
                        <em>{order.type === "MARKET" ? "市价" : "限价"}</em>
                      </span>
                      <span className={cn("ns-status-chip", statusClass(order.status))}>
                        {STATUS_LABELS[order.status]}
                      </span>
                    </div>
                    <div className="ns-mobile-order-main">
                      <span className="ns-number">{orderPrice(order)} <em>USDT</em></span>
                      <span className="ns-number">{fmtQty(order.quantity)} <em>BTC</em></span>
                    </div>
                    <div className="ns-mobile-order-meta">
                      <span>{fmtTime(order.created_at)}</span>
                      <span>已成交 {fmtQty(order.filled_qty)} BTC</span>
                      {cancelable ? (
                        confirming ? (
                          <span className="ns-cancel-confirm">
                            <button
                              type="button"
                              className="ns-link-danger"
                              onClick={() => void cancelOrder(order)}
                              disabled={canceling}
                            >
                              {canceling ? <Spinner size={11} /> : "确认撤单"}
                            </button>
                            <button
                              type="button"
                              className="ns-link-muted"
                              onClick={() => setCancelConfirmId(null)}
                              disabled={canceling}
                            >
                              取消
                            </button>
                          </span>
                        ) : (
                          <button
                            type="button"
                            className="ns-mobile-order-cancel"
                            onClick={() => setCancelConfirmId(order.id)}
                          >
                            撤单
                          </button>
                        )
                      ) : null}
                    </div>
                  </article>
                );
              })}
            </div>
          </>
        )}
      </div>

      {compact && tab !== "trades" && visibleOrders.length > maxRows ? (
        <button type="button" className="ns-orders-more" onClick={() => navigate("execution")}>
          查看全部 {visibleOrders.length} 笔订单
          <StudioIcon name="chevronRight" size={12} />
        </button>
      ) : null}
      {!online ? (
        <p className="ns-orders-offline-note">
          <StudioIcon name="warning" size={12} />
          离线状态下无法撤单，网络恢复后自动同步。
        </p>
      ) : null}
    </section>
  );
}

function OrdersHead({
  id,
  tab,
  setTab,
  counts,
  refreshing,
  onRefresh,
  compact,
  onViewAll,
}: {
  id: string;
  tab: OrdersTab;
  setTab: (tab: OrdersTab) => void;
  counts: { open: number; history: number; trades: number };
  refreshing: boolean;
  onRefresh: () => void;
  compact: boolean;
  onViewAll: () => void;
}) {
  const tabs: { key: OrdersTab; label: string; count: number }[] = [
    { key: "open", label: "当前委托", count: counts.open },
    { key: "history", label: "订单历史", count: counts.history },
    { key: "trades", label: "成交记录", count: counts.trades },
  ];

  return (
    <div className="ns-orders-head">
      <div className="ns-orders-tabs" role="tablist" aria-label="订单分类">
        {tabs.map((item) => (
          <button
            key={item.key}
            type="button"
            id={`${id}-tab-${item.key}`}
            role="tab"
            aria-selected={tab === item.key}
            aria-controls={`${id}-panel`}
            className={cn("ns-orders-tab", tab === item.key && "is-active")}
            onClick={() => setTab(item.key)}
          >
            {item.label}
            <span className="ns-orders-count">{item.count}</span>
          </button>
        ))}
      </div>
      <div className="ns-orders-actions">
        <button
          type="button"
          className="ns-icon-btn ns-icon-btn-sm"
          onClick={onRefresh}
          disabled={refreshing}
          aria-label="刷新订单"
          title="刷新订单"
        >
          {refreshing ? <Spinner size={13} /> : <StudioIcon name="refresh" size={14} />}
        </button>
        {compact ? (
          <button type="button" className="ns-text-link ns-text-link-sm" onClick={onViewAll}>
            全部订单
            <StudioIcon name="chevronRight" size={12} />
          </button>
        ) : null}
      </div>
    </div>
  );
}

function OrdersLoading() {
  return (
    <div className="ns-orders-loading" aria-live="polite">
      <span className="ns-sr-only">正在加载订单</span>
      <Skeleton className="ns-skeleton-row" />
      <Skeleton className="ns-skeleton-row" />
      <Skeleton className="ns-skeleton-row" />
    </div>
  );
}
