"use client";

import ExecutionSummary from "../execution/ExecutionSummary";
import OrdersPanel from "../orders/OrdersPanel";
import { PageHeader } from "../common";
import { StudioIcon } from "../icons";
import type { StudioPageProps } from "../types";

export default function ExecutionPage({
  session,
  data,
  notify,
  navigate,
}: StudioPageProps) {
  return (
    <div className="ns-page">
      <PageHeader
        eyebrow="OPERATIONS / EXECUTION"
        title="执行"
        description="监控策略执行、服务端风控与订单状态。Studio 不提供绕过策略和风控的人工下单入口。"
        actions={
          <button
            type="button"
            className="ns-btn ns-btn-outline ns-btn-sm"
            onClick={() => void data.refreshAll()}
            disabled={data.syncing || !data.online}
          >
            <StudioIcon name="refresh" size={14} />
            {data.syncing ? "同步中…" : "刷新执行状态"}
          </button>
        }
      />

      <ExecutionSummary data={data} />
      <OrdersPanel
        session={session}
        data={data}
        notify={notify}
        navigate={navigate}
      />
    </div>
  );
}
