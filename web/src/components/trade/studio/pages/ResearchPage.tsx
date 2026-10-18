"use client";

import { useState } from "react";
import {
  EditorialLink,
  EditorialPage,
  EmptyBlock,
  Masthead,
  MetricTape,
  PageFootnote,
  Pipeline,
  Section,
  StatusTag,
} from "../editorial/Editorial";
import type { StudioPageProps } from "../types";

const RESEARCH_FILTERS = [
  { id: "all", label: "All" },
  { id: "theory", label: "Theory" },
  { id: "market", label: "Market" },
  { id: "signal", label: "Signal" },
  { id: "risk", label: "Risk" },
] as const;

type ResearchFilter = (typeof RESEARCH_FILTERS)[number]["id"];

const RESEARCH_CHAIN = [
  { label: "Question", caption: "问题必须可证伪" },
  { label: "Hypothesis", caption: "先写预期，再取证据" },
  { label: "MATLAB", caption: "理论验证与参数分析" },
  { label: "Out-of-Sample", caption: "独立样本，单独判定" },
  { label: "Artifact", caption: "代码、数据、指标可追溯" },
  { label: "Publisher", caption: "仅提交候选，不自我批准" },
];

const NOTEBOOK_TEMPLATE = [
  {
    index: "01",
    title: "Question",
    body: "研究问题、适用范围与已知边界。",
  },
  {
    index: "02",
    title: "Hypothesis",
    body: "可证伪的预期；先于实验结果记录。",
  },
  {
    index: "03",
    title: "Method",
    body: "数据集版本、MATLAB / GPU 实验与样本外协议。",
  },
  {
    index: "04",
    title: "Evidence",
    body: "实验 ID、指标、交易成本假设与风险结果。",
  },
  {
    index: "05",
    title: "Verdict",
    body: "保留、拒绝或继续研究；不自动生成策略资格。",
  },
];

export default function ResearchPage({ navigate }: StudioPageProps) {
  const [filter, setFilter] = useState<ResearchFilter>("all");

  return (
    <EditorialPage className="nsx-research">
      <Masthead
        kicker="RESEARCH DIVISION / 02"
        title="研究工作台"
        accent="Where uncertainty becomes evidence."
        lead="研究问题、假设与证据的可追溯工作区。研究不是策略入口：只有经过实验与独立审核的候选，才可能进入策略收件箱。"
        issue={{ label: "RESEARCH", value: "02", note: "NOT CONNECTED" }}
        actions={
          <>
            <StatusTag tone="warn">Research API · Not Connected</StatusTag>
            <EditorialLink onClick={() => navigate("experiments")}>
              查看实验图谱
            </EditorialLink>
          </>
        }
      />

      <MetricTape
        items={[
          { label: "Research items", value: "—", note: "研究记录服务未接入" },
          { label: "Active hypotheses", value: "—", note: "不接受前端补写" },
          { label: "Datasets", value: "—", note: "版本与哈希由实验服务提供" },
          { label: "Reports", value: "—", note: "尚无已验证产物" },
        ]}
      />

      <Section
        index="01"
        label="RESEARCH INDEX"
        title="研究索引"
        description="以研究编号索引假设、方法与证据；任何报告都指向可核查的数据集与实验。"
        action={<StatusTag tone="warn">Index not connected</StatusTag>}
        bodyClassName="is-full"
      >
        <div className="nsx-research-grid">
          <div className="nsx-research-main">
            <div className="nsx-filter-line">
              <div className="nsx-filters" role="group" aria-label="研究类型筛选">
                {RESEARCH_FILTERS.map((item) => (
                  <button
                    key={item.id}
                    type="button"
                    className={`nsx-filter${filter === item.id ? " is-active" : ""}`}
                    onClick={() => setFilter(item.id)}
                    aria-pressed={filter === item.id}
                  >
                    {item.label}
                  </button>
                ))}
              </div>
              <span className="nsx-count">0 visible · API 未接入</span>
            </div>

            <div className="nsx-empty-table">
              <div className="nsx-empty-table-head is-research" aria-hidden="true">
                <span>Research item</span>
                <span>Type</span>
                <span>Market / Dataset</span>
                <span>Version</span>
                <span>Updated</span>
              </div>
              <EmptyBlock
                mark="—"
                title="暂无研究记录"
                body="Research API 接入后，研究假设、数据集版本、实验关联与报告会显示在这里。前端不会展示占位研究、虚构结论或未经验证的收益。"
                meta={`Filter · ${filter}`}
                action={
                  <EditorialLink onClick={() => navigate("experiments")}>
                    打开实验图谱
                  </EditorialLink>
                }
              />
            </div>
          </div>

          <aside className="nsx-research-aside">
            <p className="nsx-aside-title">Observation chain</p>
            <Pipeline
              steps={RESEARCH_CHAIN}
              ariaLabel="研究到策略的链路"
              vertical
              className="nsx-research-chain"
            />
            <p className="nsx-note" style={{ marginTop: 12 }}>
              研究记录不直接部署策略。AI 可以提出候选，但不能批准自己，也不能绕开人工审核与运行时风控。
            </p>
          </aside>
        </div>
      </Section>

      <Section
        index="02"
        label="NOTEBOOK"
        title="研究笔记"
        description="从问题到结论的编辑式记录。以下为空白模板，不代表系统已有研究记录。"
        action={<StatusTag tone="muted">Template · No active record</StatusTag>}
        bodyClassName="is-full"
      >
        <div className="nsx-notebook">
          {NOTEBOOK_TEMPLATE.map((item) => (
            <div className="nsx-notebook-row" key={item.index}>
              <span className="nsx-notebook-index">/{item.index}</span>
              <div className="nsx-notebook-copy">
                <strong>{item.title}</strong>
                <p>{item.body}</p>
              </div>
              <span className="nsx-notebook-empty">待填写</span>
            </div>
          ))}
        </div>
        <p className="nsx-note" style={{ marginTop: 12 }}>
          模板用于约束研究结构。没有服务端记录时，界面保持空白，不生成默认假设或结论。
        </p>
      </Section>

      <Section
        index="03"
        label="EVIDENCE & REPRODUCIBILITY"
        title="证据与可复现性"
        description="研究结论只有在数据集、环境和产物可复现时才成立。"
        bodyClassName="is-full"
      >
        <div className="nsx-grid-3">
          <div className="nsx-panel">
            <div className="nsx-panel-head">
              <div>
                <h3>Dataset manifest</h3>
                <p>版本、来源与校验和</p>
              </div>
              <StatusTag tone="muted">Not connected</StatusTag>
            </div>
            <div className="nsx-panel-body">
              <p className="nsx-note">
                数据集版本不可由前端修改。实验必须引用明确的 Dataset ID
                与哈希，滚动样本外协议单独记录。
              </p>
            </div>
          </div>

          <div className="nsx-panel">
            <div className="nsx-panel-head">
              <div>
                <h3>Experiment evidence</h3>
                <p>MATLAB / GPU / OOS 双向引用</p>
              </div>
              <StatusTag tone="muted">Not connected</StatusTag>
            </div>
            <div className="nsx-panel-body">
              <p className="nsx-note">
                MATLAB 与 GPU 实验保留运行环境、参数与统计结果。GPU
                是计算加速，不是策略有效性的证明。
              </p>
            </div>
          </div>

          <div className="nsx-panel">
            <div className="nsx-panel-head">
              <div>
                <h3>Artifact checksums</h3>
                <p>代码、报告与指标清单</p>
              </div>
              <StatusTag tone="muted">Not connected</StatusTag>
            </div>
            <div className="nsx-panel-body">
              <p className="nsx-note">
                每个候选必须携带 Source Commit、代码哈希与 Artifact
                Manifest。AI 不得编写不存在的收益率、夏普比率或实验结论。
              </p>
            </div>
          </div>
        </div>
      </Section>

      <PageFootnote
        center="Research records require verifiable datasets, environments and checksums. No narrative substitutes for evidence."
      />
    </EditorialPage>
  );
}
