"use client";

import {
  EditorialLink,
  EditorialPage,
  EmptyBlock,
  Masthead,
  MetricTape,
  PageFootnote,
  Section,
  StatusTag,
} from "../editorial/Editorial";
import { StudioIcon } from "../icons";
import type { StudioPageProps } from "../types";

const VALIDATION_LADDER = [
  {
    label: "In-sample",
    zh: "样本内",
    detail: "参数拟合与机制检查。通过不代表具备样本外能力。",
  },
  {
    label: "Out-of-sample",
    zh: "样本外",
    detail: "独立数据与滚动窗口验证。必须与样本内证据分开呈现。",
  },
  {
    label: "Paper",
    zh: "模拟运行",
    detail: "独立模拟账户持续观察适应性、退化与风险；不是实盘承诺。",
  },
];

export default function ExperimentsPage({ navigate }: StudioPageProps) {
  return (
    <EditorialPage className="nsx-experiments">
      <Masthead
        kicker="COMPUTE DIVISION / 03"
        title="实验图谱"
        accent="Compute is evidence infrastructure."
        lead="MATLAB 理论验证、GPU 批量评估与独立样本外验证的实验工作区。先把证据做扎实，再让 AI 提交候选。"
        issue={{ label: "COMPUTE", value: "03", note: "NOT CONNECTED" }}
        actions={
          <>
            <StatusTag tone="warn">Compute API · Not Connected</StatusTag>
            <EditorialLink onClick={() => navigate("research")}>
              返回研究工作台
            </EditorialLink>
          </>
        }
      />

      <MetricTape
        items={[
          { label: "Experiment runs", value: "—", note: "计算服务未接入" },
          { label: "MATLAB", value: "—", note: "无已知运行" },
          { label: "GPU", value: "—", note: "无已知运行" },
          { label: "Validated", value: "—", note: "尚无完成样本外验证的产物" },
        ]}
      />

      <Section
        index="01"
        label="EXPERIMENT MAP"
        title="计算图谱"
        description="两条计算通路服务不同的验证阶段。任务由受控实验服务调度，前端点击不会在生产主机执行任意代码。"
        action={<StatusTag tone="warn">Scheduler not connected</StatusTag>}
        bodyClassName="is-full"
      >
        <div className="nsx-experiment-grid">
          <article className="nsx-compute-lane">
            <div className="nsx-compute-lane-head">
              <span className="nsx-compute-symbol" aria-hidden="true">
                M
              </span>
              <StatusTag tone="warn">Offline</StatusTag>
            </div>
            <h3>MATLAB Laboratory</h3>
            <p>
              理论假设、统计检验、参数敏感性与风险模型验证。适用于计算量可控、需要精细核查的研究阶段。
            </p>
            <dl className="nsx-compute-facts">
              <div>
                <dt>Queue</dt>
                <dd>—</dd>
              </div>
              <div>
                <dt>Environment</dt>
                <dd>未连接</dd>
              </div>
              <div>
                <dt>Artifacts</dt>
                <dd>—</dd>
              </div>
              <div>
                <dt>Last run</dt>
                <dd>—</dd>
              </div>
            </dl>
          </article>

          <article className="nsx-compute-lane">
            <div className="nsx-compute-lane-head">
              <span className="nsx-compute-symbol" aria-hidden="true">
                G
              </span>
              <StatusTag tone="warn">Offline</StatusTag>
            </div>
            <h3>GPU Validation</h3>
            <p>
              大规模参数搜索、情景仿真与模型评估。GPU 提升计算吞吐，但不替代独立样本外验证与 Paper
              观察。
            </p>
            <dl className="nsx-compute-facts">
              <div>
                <dt>Queue</dt>
                <dd>—</dd>
              </div>
              <div>
                <dt>Environment</dt>
                <dd>未连接</dd>
              </div>
              <div>
                <dt>Artifacts</dt>
                <dd>—</dd>
              </div>
              <div>
                <dt>Last run</dt>
                <dd>—</dd>
              </div>
            </dl>
          </article>
        </div>

        <div className="nsx-compute-note">
          <StudioIcon name="warning" size={15} />
          <p>
            GPU 实验通过不是策略有效的证明。真实性能仍需独立样本外数据和持续的 Paper
            Trading 观察；实验元数据与策略版本必须双向可查。
          </p>
        </div>
      </Section>

      <Section
        index="02"
        label="VALIDATION LADDER"
        title="验证阶梯"
        description="每个阶段单独判定，不因上一阶段通过而自动晋级。"
        bodyClassName="is-full"
      >
        <div className="nsx-grid-3">
          {VALIDATION_LADDER.map((step, index) => (
            <div className="nsx-panel" key={step.label}>
              <div className="nsx-panel-head">
                <div>
                  <h3>
                    <span
                      style={{
                        color: "var(--nsx-cyan)",
                        fontFamily: "var(--nsx-mono)",
                        fontSize: 9,
                        marginRight: 8,
                      }}
                    >
                      {String(index + 1).padStart(2, "0")}
                    </span>
                    {step.zh}
                  </h3>
                  <p>{step.label}</p>
                </div>
                <StatusTag tone="muted">Not connected</StatusTag>
              </div>
              <div className="nsx-panel-body">
                <p className="nsx-note">{step.detail}</p>
              </div>
            </div>
          ))}
        </div>
        <p className="nsx-validation-note">
          GPU 测试不是所有策略的强制要求。计算量较小的策略可以通过独立 CPU
          实验和充分样本外验证满足阶段要求；任何新提交的策略代码仍视为不可信代码。
        </p>
      </Section>

      <Section
        index="03"
        label="EXPERIMENT RUNS"
        title="实验运行"
        description="运行记录、数据集与产物映射。MATLAB 与 GPU 结果必须真实可追踪。"
        action={<StatusTag tone="warn">Run index not connected</StatusTag>}
        bodyClassName="is-full"
      >
        <div className="nsx-empty-table">
          <div className="nsx-empty-table-head is-experiments" aria-hidden="true">
            <span>Experiment</span>
            <span>Type</span>
            <span>Status</span>
            <span>Research</span>
            <span>Dataset</span>
            <span>Created</span>
          </div>
          <EmptyBlock
            mark="—"
            title="暂无实验运行"
            body="实验 ID、运行环境、数据集版本、统计指标与产物存储地址会在此汇总。没有真实记录时，界面保持空白。"
            meta="Compute API · Not Connected"
            action={
              <EditorialLink onClick={() => navigate("strategies")}>
                返回策略研究所
              </EditorialLink>
            }
          />
        </div>
      </Section>

      <PageFootnote
        center="GPU accelerates evaluation. Independent out-of-sample evidence and paper observation decide whether a strategy is credible."
      />
    </EditorialPage>
  );
}
