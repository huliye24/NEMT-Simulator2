"use client";

import { useState } from "react";
import { ApiError, tradeApi } from "@/lib/trade/api";
import {
  cn,
  fmtPrice,
  fmtQty,
  fmtTime,
  fmtUSDT,
} from "@/lib/trade/format";
import {
  ORDER_STATUS_LABEL,
  isOpenOrder,
  orderStatusChip,
} from "@/lib/trade/order-status";
import type { Order, Session } from "@/lib/trade/types";
import {
  canCancelOrder,
  type ToastKind,
  type WorkspaceData,
} from "./workspace-shared";
import {
  EmptyState,
  Icon,
  Spinner,
  StatusDot,
} from "./ui";

type Filter = "open" | "all";

export default function OrdersTab({
  session,
  data,
  notify,
  refreshAll,
}: {
  session: Session;
  data: WorkspaceData;
  notify: (kind: ToastKind, message: string) => void;
  refreshAll: () => Promise<void>;
}) {
  const { orders, online } = data;
  const [filter, setFilter] = useState<Filter>("open");
  const [cancelingId, setCancelingId] = useState<string | null>(null);
  const [confirmId, setConfirmId] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);

  const allOrders = orders?.orders ?? [];
  const openOrders = allOrders.filter((order) => isOpenOrder(order.status));
  const visible = filter === "open" ? openOrders : allOrders;

  async function handleRefresh() {
    setRefreshing(true);
    try {
      await refreshAll();
    } finally {
      setRefreshing(false);
    }
  }

  async function handleCancel(order: Order) {
    if (cancelingId) return;
    setCancelingId(order.id);
    try {
      const canceled = await tradeApi.cancelOrder(session.csrf_token, order.id);
      setConfirmId(null);
      notify(
        "success",
        `订单已撤销 · ${ORDER_STATUS_LABEL[canceled.status]}（已成交仓位保持不变）`
      );
      await refreshAll();
    } catch (error) {
      const message =
        error instanceof ApiError ? error.message : "撤单失败，请刷新后核对";
      notify("error", message);
      await refreshAll();
    } finally {
      setCancelingId(null);
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex items-start justify-between gap-3">
        <div>
          <h1 className="text-[17px] font-semibold text-slate-100">订单</h1>
          <p className="text-[10px] font-bold uppercase tracking-[0.16em] text-slate-500 mt-0.5">Cloud orders</p>
        </div>
        <button
          type="button"
          onClick={() => void handleRefresh()}
          disabled={refreshing}
          className="trade-btn trade-btn-outline !min-h-[36px] !px-3 text-[11px]"
        >
          {refreshing ? <Spinner size={12} /> : <Icon name="refresh" size={12} />}
          刷新
        </button>
      </div>

      {!online ? (
        <div className="flex items-center gap-2 rounded-xl border border-amber-300/20 bg-amber-300/[0.06] px-3.5 py-2.5 text-[10px] text-amber-200/70">
          <Icon name="wifiOff" size={12} />
          离线状态，无法撤单或刷新；恢复网络后自动同步。
        </div>
      ) : null}

      <div className="trade-seg">
        <button
          type="button"
          onClick={() => setFilter("open")}
          className={cn("trade-seg-btn", filter === "open" && "trade-seg-btn-active")}
        >
          未完成 {orders ? `(${orders.open_count})` : ""}
        </button>
        <button
          type="button"
          onClick={() => setFilter("all")}
          className={cn("trade-seg-btn", filter === "all" && "trade-seg-btn-active")}
        >
          全部 {orders ? `(${orders.count})` : ""}
        </button>
      </div>

      {filter === "open" && !orders ? (
        <OrdersSkeleton />
      ) : visible.length === 0 ? (
        <div className="trade-card">
          <EmptyState
            icon="orders"
            title={filter === "open" ? "没有未完成订单" : "还没有订单记录"}
            body={
              filter === "open"
                ? "限价挂单会出现在这里，可随时撤销。"
                : "在交易页完成预览与二次确认后，订单会持久化在这里。"
            }
          />
        </div>
      ) : (
        <div className="space-y-3">
          {visible.map((order) => (
            <OrderCard
              key={order.id}
              order={order}
              canCancel={canCancelOrder(order) && online}
              canceling={cancelingId === order.id}
              confirming={confirmId === order.id}
              onStartCancel={() => setConfirmId(order.id)}
              onDismissCancel={() => setConfirmId(null)}
              onConfirmCancel={() => void handleCancel(order)}
            />
          ))}
        </div>
      )}

    </div>
  );
}

function OrderCard({
  order,
  canCancel,
  canceling,
  confirming,
  onStartCancel,
  onDismissCancel,
  onConfirmCancel,
}: {
  order: Order;
  canCancel: boolean;
  canceling: boolean;
  confirming: boolean;
  onStartCancel: () => void;
  onDismissCancel: () => void;
  onConfirmCancel: () => void;
}) {
  const buy = order.side === "BUY";
  const filled = Number(order.filled_qty);
  const total = Number(order.quantity);
  const progress = total > 0 ? Math.min(100, (filled / total) * 100) : 0;
  const priceLabel =
    order.avg_fill_price != null
      ? `${fmtPrice(order.avg_fill_price)} USDT`
      : order.price != null
        ? `${fmtPrice(order.price)} USDT`
        : "市价";
  const unfilled = Math.max(0, total - filled);
  const riskReasons = order.risk?.reasons ?? [];

  return (
    <article className="trade-card p-3.5">
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-2.5 min-w-0">
          <span
            className={cn(
              "w-8 h-8 rounded-lg flex items-center justify-center text-[11px] font-bold flex-none",
              buy ? "bg-emerald-400/10 text-emerald-300" : "bg-rose-400/10 text-rose-300"
            )}
          >
            {buy ? "买" : "卖"}
          </span>
          <div className="min-w-0">
            <div className="flex items-center gap-1.5">
              <span className="text-[12px] font-semibold text-slate-200">
                {order.symbol}
              </span>
              <span className="trade-chip !min-h-[18px] !text-[8px]">
                {order.type === "MARKET" ? "市价" : "限价"}
              </span>
              {order.mode !== "DEMO" ? (
                <span className="trade-chip trade-chip-cyan !min-h-[18px] !text-[8px]">
                  {order.mode}
                </span>
              ) : null}
            </div>
            <p className="text-[9px] text-slate-600 mt-0.5">
              {fmtTime(order.created_at)}
            </p>
          </div>
        </div>
        <span className={cn("trade-chip", orderStatusChip(order.status))}>
          {ORDER_STATUS_LABEL[order.status]}
        </span>
      </div>

      <div className="mt-3 grid grid-cols-2 gap-2">
        <OrderStat
          label={order.avg_fill_price != null ? "成交均价" : "委托价格"}
          value={priceLabel}
        />
        <OrderStat
          label="数量 / 已成交"
          value={`${fmtQty(order.filled_qty)} / ${fmtQty(order.quantity)} BTC`}
        />
      </div>
      <div className="mt-2 flex items-center justify-between gap-3 text-[9px] text-slate-500">
        <span>
          手续费{" "}
          <span className="trade-number text-slate-400">
            {fmtQty(order.fee)} {order.fee_asset ?? ""}
          </span>
        </span>
        <span className="trade-number">
          {unfilled > 0 ? `未成交 ${fmtQty(unfilled)} BTC` : "全部成交"}
        </span>
      </div>

      {order.status === "PARTIALLY_FILLED" || (progress > 0 && progress < 100) ? (
        <div className="mt-3">
          <div className="h-1.5 rounded-full bg-white/[0.06] overflow-hidden">
            <div
              className="h-full rounded-full bg-gradient-to-r from-cyan-400 to-emerald-400"
              style={{ width: `${progress}%` }}
            />
          </div>
          <p className="text-right text-[9px] text-slate-600 mt-1">
            已成交 {progress.toFixed(1)}%
          </p>
        </div>
      ) : null}

      {order.error_message ? (
        <div className="mt-3 rounded-lg border border-rose-400/20 bg-rose-400/[0.05] px-3 py-2">
          <p className="text-[9px] font-semibold text-rose-200/80">
            {order.error_code ?? "error"}
          </p>
          <p className="text-[10px] leading-relaxed text-rose-200/55 mt-0.5">
            {order.error_message}
          </p>
        </div>
      ) : null}

      <div className="mt-3 flex items-center justify-between gap-2 border-t border-white/[0.05] pt-2.5">
        <details className="min-w-0 flex-1">
          <summary className="cursor-pointer list-none text-[10px] text-slate-500 hover:text-slate-300">
            详情
          </summary>
          <div className="mt-2 space-y-1.5 text-[9px] leading-relaxed text-slate-500">
            <p className="trade-number break-all">
              clientOrderId: {order.client_order_id}
            </p>
            {order.exchange_order_id ? (
              <p className="trade-number break-all">
                exchangeOrderId: {order.exchange_order_id}
              </p>
            ) : null}
            <p>更新时间：{fmtTime(order.updated_at)}</p>
            {order.price != null ? (
              <p className="trade-number">冻结：{fmtUSDT(order.reserved_amount)} {order.reserved_asset ?? ""}</p>
            ) : null}
            {riskReasons.length > 0 ? (
              <ul className="pl-3.5 list-disc text-rose-200/60">
                {riskReasons.map((reason) => (
                  <li key={reason}>{reason}</li>
                ))}
              </ul>
            ) : null}
            {order.fills.length > 0 ? (
              <div className="pt-1">
                <p className="font-semibold text-slate-400">成交明细</p>
                {order.fills.map((fill) => (
                  <p key={fill.id} className="trade-number">
                    {fmtTime(fill.filled_at)} · {fmtQty(fill.quantity)} @{" "}
                    {fmtPrice(fill.price)} · fee {fmtQty(fill.commission)}{" "}
                    {fill.commission_asset}
                  </p>
                ))}
              </div>
            ) : null}
          </div>
        </details>

        {canCancel ? (
          confirming ? (
            <div className="flex items-center gap-1.5">
              <button
                type="button"
                onClick={onDismissCancel}
                disabled={canceling}
                className="trade-quick-btn !min-h-[30px]"
              >
                返回
              </button>
              <button
                type="button"
                onClick={onConfirmCancel}
                disabled={canceling}
                className="trade-quick-btn !min-h-[30px] !border-rose-400/30 !text-rose-300"
              >
                {canceling ? <Spinner size={10} /> : "确认撤销"}
              </button>
            </div>
          ) : (
            <button
              type="button"
              onClick={onStartCancel}
              className="trade-quick-btn !min-h-[30px] !px-2.5"
            >
              撤单
            </button>
          )
        ) : order.status === "PENDING_RECONCILIATION" ? (
          <span className="flex items-center gap-1.5 text-[9px] text-amber-300/60">
            <StatusDot tone="warn" />
            待对账，暂不可撤
          </span>
        ) : null}
      </div>
    </article>
  );
}

function OrderStat({
  label,
  value,
  align = "left",
}: {
  label: string;
  value: string;
  align?: "left" | "right";
}) {
  return (
    <div className={cn("min-w-0 rounded-lg bg-black/20 px-2.5 py-2", align === "right" && "text-right")}>
      <p className="text-[8px] text-slate-600 truncate">{label}</p>
      <p className="trade-number text-[10px] text-slate-300 mt-0.5 truncate">{value}</p>
    </div>
  );
}

function OrdersSkeleton() {
  return (
    <div className="space-y-3" aria-hidden="true">
      {[0, 1].map((item) => (
        <div key={item} className="trade-skeleton h-[150px] !rounded-[18px]" />
      ))}
    </div>
  );
}
