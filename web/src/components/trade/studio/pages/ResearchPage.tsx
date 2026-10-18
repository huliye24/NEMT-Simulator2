"use client";

import { useState } from "react";
import {
  RESEARCH_FILTERS,
  type ResearchFilter,
  type ResearchItem,
} from "@/lib/studio/contracts";
import { cn } from "@/lib/trade/format";
import { EmptyState, ModuleState, PageHeader } from "../common";
import { StudioIcon } from "../icons";
import type { StudioPageProps } from "../types";

const RESEARCH_FLOW = [
  { label: "Question", caption: "问题" },
  { label: "Hypothesis", caption: "假设" },
  { label: "Experiment", caption: "实验" },
  { label: "Strategy", caption: "策略" },
];

export default function ResearchPage({ navigate }: StudioPageProps) {
  const [filter, setFilter] = useState<ResearchFilter>("ALL");
  const items: ResearchItem[] = [];

  return (
    <div className="ns-page ns-module-page">
      <PageHeader
        eyebrow="WORKSPACE / RESEARCH"
        title="研究"
        description="研究问题、假设与证据的可追溯版本链。"
        actions={<ModuleState label="Research API · Not Connected" />}
      />

      <section className="ns-card ns-module-card" aria-label="Research library">
        <div className="ns-module-toolbar">
          <div className="ns-filter-tabs" role="group" aria-label="研究类型筛选">
            {RESEARCH_FILTERS.map((item) => (
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
          <span className="ns-module-count">0 research items</span>
        </div>

        <div className="ns-module-table-wrap">
          <table className="ns-data-table ns-module-table">
            <thead>
              <tr>
                <th>Research Item</th>
                <th>Type</th>
                <th>Market / Dataset</th>
                <th>Version</th>
                <th className="is-numeric">Updated</th>
              </tr>
            </thead>
            <tbody>
              {items.length === 0 ? (
                <tr className="ns-empty-row">
                  <td colSpan={5}>
                    <EmptyState
                      icon="research"
                      title="研究工作区未接入"
                      body="Research API 接入后，研究假设、模型、报告、数据集关联与版本历史会显示在这里。"
                      action={
                        <button type="button" className="ns-btn ns-btn-outline ns-btn-sm" onClick={() => navigate("experiments")}>
                          查看实验
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

        <div className="ns-research-flow" aria-label="研究到策略的关联链路">
          <span className="ns-research-flow-label">Link chain</span>
          <div className="ns-research-flow-items">
            {RESEARCH_FLOW.map((step, index) => (
              <span className="ns-research-flow-step" key={step.label}>
                <span>
                  <strong>{step.label}</strong>
                  <em>{step.caption}</em>
                </span>
                {index < RESEARCH_FLOW.length - 1 ? (
                  <StudioIcon name="chevronRight" size={11} />
                ) : null}
              </span>
            ))}
          </div>
        </div>
      </section>
    </div>
  );
}
