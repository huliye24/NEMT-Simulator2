"use client";

import { useState } from "react";
import {
  EXPERIMENT_FILTERS,
  type ExperimentFilter,
  type ExperimentRun,
} from "@/lib/studio/contracts";
import { cn } from "@/lib/trade/format";
import { EmptyState, ModuleState, PageHeader } from "../common";
import { StudioIcon } from "../icons";
import type { StudioPageProps } from "../types";

export default function ExperimentsPage({ navigate }: StudioPageProps) {
  const [filter, setFilter] = useState<ExperimentFilter>("ALL");
  const runs: ExperimentRun[] = [];

  return (
    <div className="ns-page ns-module-page">
      <PageHeader
        eyebrow="WORKSPACE / EXPERIMENTS"
        title="实验"
        description="MATLAB 分析、GPU 计算与可复现实验产物。"
        actions={<ModuleState label="Compute API · Not Connected" />}
      />

      <section className="ns-card ns-module-card" aria-label="Experiment runs">
        <div className="ns-module-toolbar">
          <div className="ns-filter-tabs" role="group" aria-label="实验类型筛选">
            {EXPERIMENT_FILTERS.map((item) => (
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
          <span className="ns-module-count">0 experiment runs</span>
        </div>

        <div className="ns-module-table-wrap">
          <table className="ns-data-table ns-module-table">
            <thead>
              <tr>
                <th>Experiment</th>
                <th>Type</th>
                <th>Status</th>
                <th>Research</th>
                <th>Dataset</th>
                <th className="is-numeric">Created</th>
              </tr>
            </thead>
            <tbody>
              {runs.length === 0 ? (
                <tr className="ns-empty-row">
                  <td colSpan={6}>
                    <EmptyState
                      icon="experiments"
                      title="计算实验服务未接入"
                      body="MATLAB 与 GPU 任务 API 接入后，实验状态、计算资源、数据集版本和产物会显示在这里。"
                      action={
                        <button type="button" className="ns-btn ns-btn-outline ns-btn-sm" onClick={() => navigate("research")}>
                          查看研究
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

        <div className="ns-experiment-kind-band">
          <div className="ns-experiment-kind">
            <span className="ns-experiment-kind-symbol">M</span>
            <div>
              <strong>MATLAB</strong>
              <p>统计分析、回测、参数敏感性与风险模型验证。</p>
            </div>
          </div>
          <div className="ns-experiment-kind-divider" aria-hidden="true" />
          <div className="ns-experiment-kind">
            <span className="ns-experiment-kind-symbol">G</span>
            <div>
              <strong>GPU</strong>
              <p>大规模参数搜索、情景仿真与模型训练。</p>
            </div>
          </div>
          <span className="ns-module-count">按计算需求选择资源</span>
        </div>
      </section>
    </div>
  );
}
