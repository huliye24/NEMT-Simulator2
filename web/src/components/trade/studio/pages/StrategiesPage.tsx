"use client";

import {
  STRATEGY_BOUNDARIES,
  STRATEGY_LIBRARY_SNAPSHOT,
  STRATEGY_LIFECYCLE_V31,
} from "@/lib/studio/strategy-library";
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
import { StudioIcon } from "../icons";
import type { StudioPageProps } from "../types";

const PUBLISHER_STEPS = [
  { label: "Research Agent", caption: "提出假设，保留研究编号" },
  { label: "MATLAB Experiment", caption: "理论验证与参数分析" },
  { label: "GPU / OOS", caption: "批量验证，但 GPU 不构成证明" },
  { label: "Verified Artifact", caption: "代码、数据与指标可追溯" },
  { label: "Publisher API", caption: "服务身份提交候选版本" },
  { label: "Human Review", caption: "保留 / 拒绝，记录原因" },
  { label: "Paper Approval", caption: "独立风控与审批后才可模拟" },
];

const LIFECYCLE_GATES: ReadonlySet<string> = new Set([
  "submitted",
  "under_review",
  "retained",
  "validated_for_paper",
  "paper_running",
  "retired",
  "archived",
]);

const LIFECYCLE_STEPS = STRATEGY_LIFECYCLE_V31.filter((stage) =>
  LIFECYCLE_GATES.has(stage.id)
).map((stage) => ({
  label: stage.zh,
  caption: stage.label,
  state: "pending" as const,
}));

export default function StrategiesPage({ navigate, route }: StudioPageProps) {
  if (route.id) {
    return <StrategyRecordUnavailable id={route.id} navigate={navigate} />;
  }

  return (
    <EditorialPage className="nsx-strategies">
      <Masthead
        kicker="STRATEGY INTELLIGENCE / 01"
        title="策略研究所"
        accent="From experiments to intelligent allocation."
        lead="AI 自动提出候选，实验提供证据，人负责保留与审批，模拟运行时始终受独立风控约束。这里不是手动导入或手动买卖的入口。"
        issue={{
          label: "PAPER ONLY",
          value: "01",
          note: "NO LIVE CAPITAL",
        }}
        actions={
          <>
            <StatusTag tone="brand">Paper only</StatusTag>
            <StatusTag tone="warn">Publisher API · Not Connected</StatusTag>
          </>
        }
      />

      <MetricTape
        items={[
          {
            label: "Candidates / 候选",
            value: "—",
            note: "AI Publisher 尚未接入",
          },
          {
            label: "Retained / 已保留",
            value: "—",
            note: "保留是独立的人工动作",
          },
          {
            label: "Paper Running / 运行",
            value: "0",
            note: "执行服务未接入，无已知实例",
          },
          {
            label: "Pending Review / 待审",
            value: "—",
            note: "当前没有审核队列",
          },
        ]}
      />

      <Section
        index="01"
        label="AI STRATEGY INBOX"
        title="候选策略"
        description="自动接收 · 等待审核。候选版本必须带有完整研究来源、样本外证据与代码清单；前端不会生成任何候选或实验结论。"
        action={<StatusTag tone="warn">Inbox service not connected</StatusTag>}
        bodyClassName="is-full"
      >
        <div className="nsx-strategy-top">
          <div className="nsx-inbox-panel">
            <div className="nsx-inbox-empty">
              <span className="nsx-inbox-mark">—</span>
              <div className="nsx-inbox-copy">
                <h3>暂无待审核策略</h3>
                <p>
                  MATLAB 与 GPU 验证完成后，由授权 AI Publisher
                  通过服务端接口提交候选策略、实验报告与可核查产物。AI
                  不能批准自己的策略，也不能分配资金或触达实盘。
                </p>
                <div className="nsx-inbox-service">
                  <span className="nsx-tag is-warn">
                    POST /api/v1/strategy-submissions
                  </span>
                  <span className="nsx-tag is-muted">
                    Service identity · Idempotent · Audited
                  </span>
                </div>
                <p className="nsx-empty-meta">
                  {STRATEGY_LIBRARY_SNAPSHOT.reason}
                </p>
              </div>
            </div>

            <div className="nsx-inbox-actions">
              <span className="nsx-count">
                Review actions · enabled when a candidate arrives
              </span>
              <div>
                <button
                  type="button"
                  className="nsx-btn is-small"
                  disabled
                  title="Publisher API 尚未接入，没有可审核的候选"
                >
                  Retain · 保留
                </button>
                <button
                  type="button"
                  className="nsx-btn is-small"
                  disabled
                  title="Publisher API 尚未接入，没有可审核的候选"
                >
                  Reject · 拒绝
                </button>
              </div>
            </div>
          </div>

          <div className="nsx-pipeline-panel">
            <p className="nsx-aside-title">Proposal → evidence → human</p>
            <Pipeline
              steps={PUBLISHER_STEPS}
              ariaLabel="AI 策略发布链路"
              vertical
              className="nsx-research-chain"
            />
            <p className="nsx-note" style={{ marginTop: 12 }}>
              Agent 仅能提交候选；保留、模拟审批与资金配置是彼此独立的人工决策。
            </p>
          </div>
        </div>
      </Section>

      <Section
        index="02"
        label="STRATEGY LIBRARY"
        title="策略库"
        description="只收录经人工保留的版本。每个版本保留研究编号、代码哈希、数据集与审批轨迹。"
        action={<StatusTag tone="warn">Library not connected</StatusTag>}
        bodyClassName="is-full"
      >
        <div className="nsx-library-split">
          <div className="nsx-library-main">
            <EmptyBlock
              mark="—"
              title="尚无已接收的策略版本"
              body="当 AI Publisher 接入并由人工保留候选策略后，版本、研究来源、验证状态与运行资格会在此汇总。"
              meta="Strategy Library API · Not Connected"
              action={
                <EditorialLink onClick={() => navigate("research")}>
                  查看研究工作台
                </EditorialLink>
              }
            />
          </div>

          <aside className="nsx-library-aside">
            <p className="nsx-aside-title">Retain ≠ Approve</p>
            <ul className="nsx-boundary-list">
              {STRATEGY_BOUNDARIES.map((item) => (
                <li key={item.label}>
                  <strong>
                    {item.label}
                    <em>{item.zh}</em>
                  </strong>
                  <p>{item.detail}</p>
                </li>
              ))}
            </ul>
            <p className="nsx-note" style={{ marginTop: 12 }}>
              浏览器只能发起经过授权与审计的操作；任何部署与资金决策必须由服务端风控强制。
            </p>
          </aside>
        </div>

        <div style={{ marginTop: 24 }}>
          <p className="nsx-aside-title">Lifecycle gates</p>
          <Pipeline steps={LIFECYCLE_STEPS} ariaLabel="策略生命周期" />
          <p className="nsx-note" style={{ marginTop: 10 }}>
            REJECTED 是独立分支。保留不等于批准模拟，批准模拟也不等于允许实盘；每次状态变化记录操作者、时间、原因与版本。
          </p>
        </div>
      </Section>

      <Section
        index="03"
        label="VALIDATION RECORDS"
        title="验证记录"
        description="MATLAB、GPU 与样本外实验的可追溯映射。所有指标必须来自可核查的实验产物。"
        action={<StatusTag tone="warn">Validation API not connected</StatusTag>}
        bodyClassName="is-full"
      >
        <div className="nsx-empty-table">
          <div className="nsx-empty-table-head is-validation" aria-hidden="true">
            <span>Strategy</span>
            <span>Research</span>
            <span>MATLAB</span>
            <span>GPU</span>
            <span>OOS</span>
            <span>Status</span>
          </div>
          <EmptyBlock
            mark="—"
            title="尚无验证记录"
            body="验证记录必须由实验服务写入：实验 ID、数据集版本、运行环境、统计指标、交易成本假设与风险指标缺一不可。"
            meta="Validation service · Not Connected"
          />
        </div>
        <p className="nsx-validation-note">
          GPU 测试不是所有策略的强制要求。计算量较小的策略可通过独立 CPU
          实验与充分样本外验证满足阶段要求；GPU 通过也不等于策略有效。
        </p>
      </Section>

      <Section
        index="04"
        label="STRATEGY ALLOCATION"
        title="模拟配置"
        description="为 Meta-Strategy / Adaptive Allocator 预留的配置结构。没有真实配置器时，所有权重保持未接入。"
        action={<StatusTag tone="warn">Allocator not connected</StatusTag>}
        bodyClassName="is-full"
      >
        <div className="nsx-allocation">
          <div className="nsx-allocation-fields">
            <AllocationField label="Market Regime" value="—" quiet />
            <AllocationField label="Eligible Strategies" value="—" quiet />
            <AllocationField label="Target Weights" value="—" quiet />
            <AllocationField label="Actual Weights" value="—" quiet />
            <AllocationField label="Risk Budget" value="—" quiet />
            <AllocationField label="Last Rebalance" value="—" quiet />
            <AllocationField label="Allocation Reason" value="—" quiet />
            <AllocationField label="Allocator Mode" value="Paper only" />
          </div>
          <div className="nsx-allocation-foot">
            <p className="nsx-note">
              Adaptive Allocator 尚未接入。界面不会伪造 AI
              正在自动切换策略、权重或市场状态；本阶段只建立数据模型与展示结构。
            </p>
            <StatusTag tone="warn">Not Connected</StatusTag>
          </div>
        </div>
      </Section>

      <Section
        index="05"
        label="STRATEGY ARCHIVE"
        title="策略存档"
        description="拒绝、淘汰与退役的策略版本。历史引用与审计记录保持完整，不做前端物理删除。"
        bodyClassName="is-full"
      >
        <EmptyBlock
          mark="—"
          title="存档为空"
          body="被拒绝或退役的候选会连同原因、操作者与版本引用一并归档。已有订单、实验或审计记录的历史引用必须保持完整。"
          meta="Archive · No records"
        />
      </Section>

      <PageFootnote
        center="AI discovers and proposes. Humans curate and approve. The runtime executes under independent risk controls."
      />
    </EditorialPage>
  );
}

function AllocationField({
  label,
  value,
  quiet = false,
}: {
  label: string;
  value: string;
  quiet?: boolean;
}) {
  return (
    <div className="nsx-allocation-field">
      <span>{label}</span>
      <strong className={quiet ? "is-quiet" : undefined}>{value}</strong>
    </div>
  );
}

function StrategyRecordUnavailable({
  id,
  navigate,
}: {
  id: string;
  navigate: StudioPageProps["navigate"];
}) {
  return (
    <EditorialPage>
      <div
        className="nsx-eyebrow-row"
        style={{ paddingBottom: 16, borderBottom: "1px solid var(--nsx-line)" }}
      >
        <button
          type="button"
          className="nsx-link"
          onClick={() => navigate("strategies")}
        >
          <StudioIcon name="chevronLeft" size={12} />
          返回策略研究所
        </button>
        <StatusTag tone="muted">ID · {id}</StatusTag>
      </div>

      <Masthead
        compact
        kicker="STRATEGY RECORD / LIBRARY"
        title="策略记录暂不可用"
        accent="The record cannot be verified yet."
        lead="NEMT Cloud Strategy Library API 尚未接入。无法读取该策略的版本、研究来源、验证证据、审批与部署状态。"
        issue={{ label: "RECORD", value: "—", note: "NOT CONNECTED" }}
      />

      <Section
        index="01"
        label="RECORD BOUNDARY"
        title="未获取策略详情"
        description="前端不会用占位版本、虚构回测或默认状态填充策略记录。"
        bodyClassName="is-full"
      >
        <EmptyBlock
          mark="—"
          title="没有可验证的策略版本"
          body="策略详情必须来自服务端记录。保留与部署是不同状态，任何实盘资格都必须经过独立审批与执行服务。"
          action={
            <button
              type="button"
              className="nsx-btn"
              onClick={() => navigate("strategies")}
            >
              返回策略研究所
            </button>
          }
        />
      </Section>

      <PageFootnote center="Strategy records are rendered only from server-verified data." />
    </EditorialPage>
  );
}
