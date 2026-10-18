"use client";

import { PageHeader } from "../common";
import AccountSummary from "../account/AccountSummary";
import MarketPanel from "../market/MarketPanel";
import OrdersPanel from "../orders/OrdersPanel";
import { StudioIcon } from "../icons";
import type { StudioPageProps } from "../types";
import { ageLabel } from "@/lib/trade/format";

interface TradingWorkbenchProps extends StudioPageProps {
  eyebrow: string;
  title: string;
  description: string;
}

export default function TradingWorkbench({
  eyebrow,
  title,
  description,
  session,
  data,
  notify,
  navigate,
}: TradingWorkbenchProps) {
  return (
    <div className="ns-page">
      <PageHeader
        eyebrow={eyebrow}
        title={title}
        description={description}
        actions={
          <>
            <span className="ns-page-sync">
              <span className={`ns-sidebar-status-dot ${data.online ? "is-online" : "is-offline"}`} />
              {data.ticker ? `${ageLabel(data.ticker.fetched_at)}更新` : "等待行情"}
            </span>
            <button
              type="button"
              className="ns-btn ns-btn-outline ns-btn-sm"
              onClick={() => void data.refreshAll()}
              disabled={data.syncing || !data.online}
            >
              <StudioIcon name="refresh" size={14} />
              {data.syncing ? "同步中…" : "刷新数据"}
            </button>
            <button
              type="button"
              className="ns-btn ns-btn-dark ns-btn-sm"
              onClick={() => navigate("execution")}
            >
              全部订单
              <StudioIcon name="chevronRight" size={13} />
            </button>
          </>
        }
      />

      <div className="ns-workspace">
        <MarketPanel data={data} />

        <aside className="ns-rail" aria-label="账户与执行">
          <AccountSummary data={data} navigate={navigate} />
          <ExecutionPolicyCard navigate={navigate} />
        </aside>

        <OrdersPanel
          session={session}
          data={data}
          notify={notify}
          navigate={navigate}
          compact
        />
      </div>
    </div>
  );
}

function ExecutionPolicyCard({
  navigate,
}: {
  navigate: StudioPageProps["navigate"];
}) {
  return (
    <section className="ns-card ns-execution-card" aria-label="执行方式">
      <div className="ns-side-card-head">
        <div>
          <h2 className="ns-card-title">执行方式</h2>
          <p className="ns-card-hint">策略驱动 · 人工入口关闭</p>
        </div>
        <span className="ns-chip ns-chip-brand">
          <StudioIcon name="lock" size={11} />
          人工下单已关闭
        </span>
      </div>

      <dl className="ns-execution-list">
        <div>
          <dt>订单来源</dt>
          <dd>策略执行</dd>
        </div>
        <div>
          <dt>执行校验</dt>
          <dd>服务端风控</dd>
        </div>
        <div>
          <dt>监控与撤单</dt>
          <dd>可用</dd>
        </div>
      </dl>

      <p className="ns-side-note">
        Studio 不提供人工下单。策略执行产生的委托、成交与余额变化会同步展示；未完成订单仍可执行撤销。
      </p>
      <button
        type="button"
        className="ns-btn ns-btn-outline ns-btn-block ns-btn-sm"
        onClick={() => navigate("strategies")}
      >
        查看策略
        <StudioIcon name="chevronRight" size={12} />
      </button>
    </section>
  );
}
