"use client";

import { useState } from "react";
import { fmtTime } from "@/lib/trade/format";
import type {
  BacktestSummary,
  StrategyDetail as StrategyDetailModel,
  StrategyLifecycle,
  StrategyParameter,
} from "@/lib/studio/contracts";
import { STRATEGY_LIFECYCLE } from "@/lib/studio/contracts";
import { EmptyState, StatusDot } from "../../common";
import { StudioIcon } from "../../icons";
import type { StudioPageProps } from "../../types";

const DETAIL_TABS = [
  { id: "overview", label: "Overview" },
  { id: "parameters", label: "Parameters" },
  { id: "backtests", label: "Backtests" },
  { id: "experiments", label: "Experiments" },
  { id: "deployment", label: "Deployment" },
  { id: "performance", label: "Performance" },
  { id: "logs", label: "Logs" },
] as const;

type DetailTab = (typeof DETAIL_TABS)[number]["id"];

const LIFECYCLE_META = Object.fromEntries(
  STRATEGY_LIFECYCLE.map((stage) => [stage.id, stage])
) as Record<StrategyLifecycle, (typeof STRATEGY_LIFECYCLE)[number]>;

function LifecycleChip({ stage }: { stage: StrategyLifecycle }) {
  const meta = LIFECYCLE_META[stage];
  return (
    <span className={`ns-lifecycle-chip is-${stage}`}>
      <span className="ns-lifecycle-dot" />
      {meta.zh}
      <em>{meta.label}</em>
    </span>
  );
}

export default function StrategyDetail({
  strategy,
  navigate,
}: {
  strategy: StrategyDetailModel;
  navigate: StudioPageProps["navigate"];
}) {
  const [tab, setTab] = useState<DetailTab>("overview");

  return (
    <div className="ns-page ns-strategy-detail">
      <div className="ns-detail-topline">
        <button
          type="button"
          className="ns-text-link ns-text-link-sm"
          onClick={() => navigate("strategies")}
        >
          <StudioIcon name="chevronLeft" size={13} />
          返回策略库
        </button>
        <span className="ns-chip">Strategy ID · {strategy.id}</span>
      </div>

      <header className="ns-strategy-head">
        <div className="ns-strategy-head-main">
          <div className="ns-strategy-title-row">
            <h1>{strategy.name}</h1>
            <span className="ns-version-chip">v{strategy.version}</span>
            <LifecycleChip stage={strategy.lifecycle} />
          </div>
          <p>
            {strategy.market} · {strategy.mode} · 风险等级 {strategy.risk_grade}
          </p>
        </div>
        <div className="ns-strategy-head-actions">
          <span className="ns-chip ns-chip-warn">
            <StatusDot tone="warn" />
            Execution Not Connected
          </span>
          <button
            type="button"
            className="ns-btn ns-btn-dark ns-btn-sm"
            disabled
            title="实盘部署必须由云端授权、风险审批与独立执行服务完成"
          >
            <StudioIcon name="lock" size={13} />
            部署 / 执行
          </button>
        </div>
      </header>

      <div className="ns-seg-tabs" role="tablist" aria-label="策略详情">
        {DETAIL_TABS.map((item) => (
          <button
            key={item.id}
            type="button"
            role="tab"
            aria-selected={tab === item.id}
            className={`ns-seg-tab${tab === item.id ? " is-active" : ""}`}
            onClick={() => setTab(item.id)}
          >
            {item.label}
          </button>
        ))}
      </div>

      <div className="ns-strategy-detail-body">
        {tab === "overview" ? (
          <OverviewTab strategy={strategy} />
        ) : tab === "parameters" ? (
          <ParametersTab parameters={strategy.parameters} />
        ) : tab === "backtests" ? (
          <BacktestsTab items={strategy.backtests} />
        ) : tab === "experiments" ? (
          <EmptyState
            icon="cpu"
            title={strategy.experiment_ids.length ? "关联实验" : "暂无关联实验"}
            body={
              strategy.experiment_ids.length
                ? strategy.experiment_ids.join(" · ")
                : "研究假设应先通过 MATLAB / GPU 实验验证，再进入策略审批。"
            }
          />
        ) : tab === "deployment" ? (
          <DeploymentTab strategy={strategy} />
        ) : tab === "performance" ? (
          <EmptyState
            icon="activity"
            title="尚无真实绩效数据"
            body="只有接入独立执行服务后的真实、可审计记录才会展示；回测结果不在此冒充实盘绩效。"
          />
        ) : (
          <LogsTab logs={strategy.logs} />
        )}
      </div>
    </div>
  );
}

function OverviewTab({ strategy }: { strategy: StrategyDetailModel }) {
  return (
    <div className="ns-strategy-overview">
      <section className="ns-card ns-detail-card">
        <h2>研究假设</h2>
        <p className="ns-detail-prose">
          {strategy.hypothesis ?? "尚未关联研究假设。"}
        </p>
        <div className="ns-detail-meta">
          <span>Research ID</span>
          <strong>{strategy.research_id ?? "未关联"}</strong>
        </div>
      </section>

      <section className="ns-card ns-detail-card">
        <h2>生命周期</h2>
        <ol className="ns-lifecycle-track">
          {STRATEGY_LIFECYCLE.map((stage, index) => {
            const order = STRATEGY_LIFECYCLE.findIndex((item) => item.id === strategy.lifecycle);
            const done = index < order;
            const current = index === order;
            return (
              <li
                key={stage.id}
                className={`ns-lifecycle-step${done ? " is-done" : ""}${current ? " is-current" : ""}`}
              >
                <span className="ns-lifecycle-step-index">{index + 1}</span>
                <strong>{stage.label}</strong>
                <span>{stage.zh}</span>
              </li>
            );
          })}
        </ol>
        <p className="ns-detail-note">
          每个阶段都是独立门槛。回测成功不等于具备实盘资格；实盘必须经过风险审批与独立执行服务。
        </p>
      </section>

      <section className="ns-card ns-detail-card">
        <h2>状态边界</h2>
        <dl className="ns-detail-list">
          <div>
            <dt>运行模式</dt>
            <dd>{strategy.mode}</dd>
          </div>
          <div>
            <dt>风险评级</dt>
            <dd>{strategy.risk_grade}</dd>
          </div>
          <div>
            <dt>部署状态</dt>
            <dd>{strategy.deployment_state}</dd>
          </div>
          <div>
            <dt>最近活动</dt>
            <dd>{fmtTime(strategy.last_activity_at)}</dd>
          </div>
        </dl>
        <p className="ns-detail-note">
          {strategy.deployment_note ??
            "前端仅展示状态。交易决策、风控和订单执行必须由云端服务完成。"}
        </p>
      </section>
    </div>
  );
}

function ParametersTab({ parameters }: { parameters: StrategyParameter[] }) {
  if (parameters.length === 0) {
    return (
      <EmptyState
        icon="sliders"
        title="暂无参数版本"
        body="参数集需从 NEMT Cloud Strategy API 读取，并保留版本与变更审计。"
      />
    );
  }
  return (
    <section className="ns-card ns-detail-card">
      <div className="ns-table-scroll">
        <table className="ns-data-table">
          <thead>
            <tr>
              <th>参数</th>
              <th>值</th>
              <th>单位</th>
              <th>说明</th>
            </tr>
          </thead>
          <tbody>
            {parameters.map((parameter) => (
              <tr key={parameter.key}>
                <td className="ns-symbol-cell">{parameter.key}</td>
                <td className="ns-number">{parameter.value}</td>
                <td>{parameter.unit ?? "—"}</td>
                <td className="ns-muted-cell">{parameter.description ?? "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function BacktestsTab({ items }: { items: BacktestSummary[] }) {
  if (items.length === 0) {
    return (
      <EmptyState
        icon="fileText"
        title="暂无回测记录"
        body="回测结果由研究/实验服务产生。通过记录不会被前端自动提升为实盘资格。"
      />
    );
  }
  return (
    <section className="ns-card ns-detail-card">
      <div className="ns-table-scroll">
        <table className="ns-data-table">
          <thead>
            <tr>
              <th>回测</th>
              <th>开始</th>
              <th>结束</th>
              <th className="is-numeric">Sharpe</th>
              <th className="is-numeric">最大回撤</th>
              <th>指标状态</th>
            </tr>
          </thead>
          <tbody>
            {items.map((item) => (
              <tr key={item.id}>
                <td className="ns-symbol-cell">{item.label}</td>
                <td>{fmtTime(item.started_at)}</td>
                <td>{fmtTime(item.finished_at)}</td>
                <td className="is-numeric ns-number">{item.sharpe ?? "—"}</td>
                <td className="is-numeric ns-number">{item.max_drawdown ?? "—"}</td>
                <td>{item.metrics_available ? "可用" : "未提供"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function DeploymentTab({ strategy }: { strategy: StrategyDetailModel }) {
  return (
    <div className="ns-strategy-overview">
      <section className="ns-card ns-detail-card">
        <h2>部署门槛</h2>
        <dl className="ns-detail-list">
          <div>
            <dt>当前状态</dt>
            <dd>{strategy.deployment_state}</dd>
          </div>
          <div>
            <dt>风险审批</dt>
            <dd>独立审批（未接入）</dd>
          </div>
          <div>
            <dt>执行服务</dt>
            <dd>Not Connected</dd>
          </div>
          <div>
            <dt>前端下单</dt>
            <dd>不允许</dd>
          </div>
        </dl>
        <p className="ns-detail-note">
          实盘部署必须由明确的授权、风险检查与独立执行服务处理。Studio
          不把一次回测成功当作实盘资格，也不会在浏览器保存交易所密钥。
        </p>
      </section>
    </div>
  );
}

function LogsTab({ logs }: { logs: StrategyDetailModel["logs"] }) {
  if (logs.length === 0) {
    return (
      <EmptyState
        icon="fileText"
        title="暂无策略日志"
        body="策略日志将由云端执行服务提供，并在服务端保留审计记录。"
      />
    );
  }
  return (
    <section className="ns-card ns-detail-card">
      <ul className="ns-log-list">
        {logs.map((log, index) => (
          <li key={`${log.at}-${index}`}>
            <span className={`ns-log-level is-${log.level}`}>{log.level}</span>
            <span className="ns-log-time">{fmtTime(log.at)}</span>
            <span className="ns-log-message">{log.message}</span>
          </li>
        ))}
      </ul>
    </section>
  );
}
