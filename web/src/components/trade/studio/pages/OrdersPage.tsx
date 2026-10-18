"use client";

import { useMemo } from "react";
import { isOpenOrder } from "@/lib/trade/order-status";
import { PageHeader, StatusDot } from "../common";
import { StudioIcon } from "../icons";
import OrdersPanel from "../orders/OrdersPanel";
import type { StudioPageProps } from "../types";

export default function OrdersPage({ session, data, notify, navigate }: StudioPageProps) {
  const allOrders = useMemo(() => data.orders?.orders ?? [], [data.orders]);
  const openOrders = useMemo(
    () => allOrders.filter((order) => isOpenOrder(order.status)),
    [allOrders]
  );
  const closedOrders = Math.max(0, allOrders.length - openOrders.length);
  const fillCount = useMemo(
    () => allOrders.reduce((total, order) => total + order.fills.length, 0),
    [allOrders]
  );

  return (
    <div className="ns-page">
      <PageHeader
        eyebrow="ACCOUNT / ORDERS"
        title="订单"
        description="查看策略执行产生的当前委托、历史订单与逐笔成交。撤单只作用于未成交部分，不会改变已成交仓位。"
      />

      <div className="ns-kpi-grid">
        <KpiCard
          icon="orders"
          label="当前委托"
          value={String(data.orders?.open_count ?? openOrders.length)}
          hint="未完成订单"
          tone={openOrders.length > 0 ? "brand" : "neutral"}
        />
        <KpiCard
          icon="fileText"
          label="历史订单"
          value={String(closedOrders)}
          hint="已完成或已撤销"
        />
        <KpiCard
          icon="activity"
          label="逐笔成交"
          value={String(fillCount)}
          hint="当前记录内成交明细"
        />
        <KpiCard
          icon="database"
          label="订单数据"
          value={data.orders ? "已同步" : data.coreError ? "异常" : "加载中"}
          hint={data.orders ? "最多展示最近 100 笔" : "等待 NEMT Cloud"}
          tone={data.orders ? "up" : data.coreError ? "down" : "neutral"}
          status
        />
      </div>

      <OrdersPanel
        session={session}
        data={data}
        notify={notify}
        navigate={navigate}
      />
    </div>
  );
}

function KpiCard({
  icon,
  label,
  value,
  hint,
  tone = "neutral",
  status = false,
}: {
  icon: "orders" | "fileText" | "activity" | "database";
  label: string;
  value: string;
  hint: string;
  tone?: "neutral" | "brand" | "up" | "down";
  status?: boolean;
}) {
  return (
    <div className="ns-card ns-kpi">
      <span className={`ns-kpi-icon is-${tone}`}>
        <StudioIcon name={icon} size={17} />
      </span>
      <div className="ns-kpi-copy">
        <span className="ns-kpi-label">{label}</span>
        <span className="ns-kpi-value">
          {status ? (
            <StatusDot
              tone={tone === "up" ? "ok" : tone === "down" ? "bad" : "warn"}
            />
          ) : null}
          {value}
        </span>
        <span className="ns-kpi-hint">{hint}</span>
      </div>
    </div>
  );
}
