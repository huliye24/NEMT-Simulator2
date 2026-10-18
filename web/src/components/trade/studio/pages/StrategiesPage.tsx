"use client";

import { useState } from "react";
import {
  STRATEGY_FILTERS,
  STRATEGY_STAGES,
  type StrategyFilter,
  type StrategySummary,
} from "@/lib/studio/contracts";
import { cn } from "@/lib/trade/format";
import { EmptyState, ModuleState, PageHeader } from "../common";
import { StudioIcon } from "../icons";
import type { StudioPageProps } from "../types";

export default function StrategiesPage({ navigate }: StudioPageProps) {
  const [filter, setFilter] = useState<StrategyFilter>("ALL");
  const strategies: StrategySummary[] = [];

  return (
    <div className="ns-page ns-module-page">
      <PageHeader
        eyebrow="WORKSPACE / STRATEGIES"
        title="策略"
        description="策略研究、验证、审批与部署相互独立。"
        actions={<ModuleState label="Strategy API · Not Connected" />}
      />

      <section className="ns-card ns-module-card" aria-label="Strategy library">
        <div className="ns-module-toolbar">
          <div className="ns-filter-tabs" role="group" aria-label="策略状态筛选">
            {STRATEGY_FILTERS.map((item) => (
              <button
                key={item.id}
                type="button"
                className={cn("ns-filter-tab", filter === item.id && "is-active")}
                onClick={() => setFilter(item.id)}
                aria-pressed={filter === item.id}
              >
                {item.label}
              </button>
            ))}
          </div>
          <span className="ns-module-count">0 strategies</span>
        </div>

        <div className="ns-module-table-wrap">
          <table className="ns-data-table ns-module-table">
            <thead>
              <tr>
                <th>Strategy</th>
                <th>Version</th>
                <th>Market</th>
                <th>Mode</th>
                <th>Status</th>
                <th className="is-numeric">Last Activity</th>
              </tr>
            </thead>
            <tbody>
              {strategies.length === 0 ? (
                <tr className="ns-empty-row">
                  <td colSpan={6}>
                    <EmptyState
                      icon="strategies"
                      title="策略服务未接入"
                      body="云端策略 API 接入后，策略定义、版本、审批状态与部署模式会显示在这里。当前不会伪造运行中的策略。"
                      action={
                        <button type="button" className="ns-btn ns-btn-outline ns-btn-sm" onClick={() => navigate("research")}>
                          查看研究库
                          <StudioIcon name="chevronRight" size={12} />
                        </button>
                      }
                    />
                  </td>
                </tr>
              ) : null}
            </tbody>
          </table>
        </div>

        <div className="ns-lifecycle-band">
          <div className="ns-lifecycle-title">
            <span>Lifecycle</span>
            <p>策略资格与交易执行严格分离</p>
          </div>
          <div className="ns-lifecycle-stages" aria-label="策略生命周期">
            {STRATEGY_STAGES.map((stage, index) => (
              <span className="ns-lifecycle-stage" key={stage.id}>
                <span>{stage.label}</span>
                {index < STRATEGY_STAGES.length - 1 ? (
                  <StudioIcon name="chevronRight" size={11} />
                ) : null}
              </span>
            ))}
          </div>
        </div>
      </section>

      <div className="ns-module-footnote">
        <StudioIcon name="info" size={14} />
        <p>
          回测成功不等于具备实盘资格。LIVE 部署需要独立的风险审批与执行服务。
        </p>
      </div>
    </div>
  );
}
