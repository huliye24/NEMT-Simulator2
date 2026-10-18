/**
 * Frontend contracts for NEMT Studio's strategy-first modules.
 *
 * These endpoints are reserved for the NEMT Cloud backend. The current UI
 * renders NOT_CONNECTED / empty states and never fabricates strategy,
 * research, experiment, execution-run, or performance data.
 */

export type ModuleConnectionState =
  | "CONNECTED"
  | "NOT_CONNECTED"
  | "NOT_CONFIGURED"
  | "NOT_AVAILABLE"
  | "LOADING"
  | "ERROR";

export const STUDIO_API_PATHS = {
  strategies: "/api/v1/studio/strategies",
  strategy: (strategyId: string) =>
    `/api/v1/studio/strategies/${encodeURIComponent(strategyId)}`,
  research: "/api/v1/studio/research",
  researchItem: (researchId: string) =>
    `/api/v1/studio/research/${encodeURIComponent(researchId)}`,
  experiments: "/api/v1/studio/experiments",
  experiment: (experimentId: string) =>
    `/api/v1/studio/experiments/${encodeURIComponent(experimentId)}`,
  executionRuns: "/api/v1/studio/execution/runs",
  executionEvents: "/api/v1/studio/execution/events",
  portfolioHistory: "/api/v1/studio/portfolio/history",
} as const;

export type StrategyStage =
  | "DRAFT"
  | "BACKTESTED"
  | "VALIDATED"
  | "PAPER_TRADING"
  | "RISK_APPROVAL"
  | "LIVE"
  | "PAUSED"
  | "STOPPED";

export const STRATEGY_STAGES: {
  id: StrategyStage;
  label: string;
  shortLabel: string;
}[] = [
  { id: "DRAFT", label: "Draft", shortLabel: "草稿" },
  { id: "BACKTESTED", label: "Backtested", shortLabel: "已回测" },
  { id: "VALIDATED", label: "Validated", shortLabel: "已验证" },
  { id: "PAPER_TRADING", label: "Paper Trading", shortLabel: "模拟" },
  { id: "RISK_APPROVAL", label: "Risk Approval", shortLabel: "风控审批" },
  { id: "LIVE", label: "Live", shortLabel: "实盘" },
  { id: "PAUSED", label: "Paused", shortLabel: "暂停" },
  { id: "STOPPED", label: "Stopped", shortLabel: "停止" },
];

export type StrategyFilter = "ALL" | "DRAFT" | "TESTING" | "PAPER" | "LIVE" | "PAUSED";

export const STRATEGY_FILTERS: { id: StrategyFilter; label: string }[] = [
  { id: "ALL", label: "全部" },
  { id: "DRAFT", label: "草稿" },
  { id: "TESTING", label: "测试中" },
  { id: "PAPER", label: "模拟盘" },
  { id: "LIVE", label: "实盘" },
  { id: "PAUSED", label: "已暂停" },
];

export type StrategyDetailSection =
  | "overview"
  | "parameters"
  | "backtests"
  | "experiments"
  | "deployment"
  | "performance"
  | "logs";

export const STRATEGY_DETAIL_SECTIONS: {
  id: StrategyDetailSection;
  label: string;
}[] = [
  { id: "overview", label: "Overview" },
  { id: "parameters", label: "Parameters" },
  { id: "backtests", label: "Backtests" },
  { id: "experiments", label: "Experiments" },
  { id: "deployment", label: "Deployment" },
  { id: "performance", label: "Performance" },
  { id: "logs", label: "Logs" },
];

export type RiskRating = "LOW" | "MEDIUM" | "HIGH" | "UNRATED";

export interface StrategySummary {
  id: string;
  name: string;
  version: string;
  stage: StrategyStage;
  market: string;
  researchHypothesisId: string | null;
  riskRating: RiskRating;
  deploymentStatus: "NONE" | "PAPER" | "LIVE" | "PAUSED";
  lastActivityAt: string | null;
}

export interface StrategyDetail extends StrategySummary {
  parameters: Record<string, string | number | boolean>;
  linkedExperimentIds: string[];
  backtestSummary: {
    period: string;
    netReturn: number;
    maxDrawdown: number;
    sharpe: number;
  } | null;
  approvedBy: string | null;
  approvedAt: string | null;
}

export type ResearchCategory = "HYPOTHESIS" | "MODEL" | "REPORT";
export type ResearchFilter = "ALL" | ResearchCategory;

export const RESEARCH_FILTERS: { id: ResearchFilter; label: string }[] = [
  { id: "ALL", label: "全部" },
  { id: "HYPOTHESIS", label: "假设" },
  { id: "MODEL", label: "模型" },
  { id: "REPORT", label: "报告" },
];

export interface ResearchItem {
  id: string;
  title: string;
  category: ResearchCategory;
  market: string | null;
  datasets: string[];
  version: string;
  linkedExperimentIds: string[];
  linkedStrategyIds: string[];
  updatedAt: string;
}

export type ExperimentFilter = "ALL" | "MATLAB" | "GPU";
export type ExperimentKind = "MATLAB" | "GPU";
export type ExperimentStatus =
  | "QUEUED"
  | "RUNNING"
  | "SUCCEEDED"
  | "FAILED"
  | "CANCELLED";

export const EXPERIMENT_FILTERS: { id: ExperimentFilter; label: string }[] = [
  { id: "ALL", label: "全部" },
  { id: "MATLAB", label: "MATLAB" },
  { id: "GPU", label: "GPU" },
];

export interface ExperimentRun {
  id: string;
  name: string;
  kind: ExperimentKind;
  status: ExperimentStatus;
  durationSeconds: number | null;
  createdAt: string;
  researchId: string | null;
  dataset: string | null;
  artifactCount: number;
}

export type ExecutionRunStatus = "RUNNING" | "PAUSED" | "STOPPED" | "ERROR";

export interface ExecutionRun {
  id: string;
  strategyId: string;
  strategyName: string;
  status: ExecutionRunStatus;
  startedAt: string;
  lastHeartbeatAt: string | null;
}

export type ExecutionEventSeverity = "INFO" | "WARNING" | "ERROR";

export interface ExecutionEvent {
  id: string;
  type: string;
  severity: ExecutionEventSeverity;
  message: string;
  createdAt: string;
  orderId: string | null;
}

export interface PortfolioMetrics {
  realizedPnl: string | null;
  unrealizedPnl: string | null;
  maxDrawdown: string | null;
  exposure: string | null;
  equityHistory: { timestamp: string; equity: string }[];
}

export type ExecutionTab = "runs" | "orders" | "fills" | "events" | "risk";

export const EXECUTION_TABS: { id: ExecutionTab; label: string }[] = [
  { id: "runs", label: "运行实例" },
  { id: "orders", label: "订单" },
  { id: "fills", label: "成交" },
  { id: "events", label: "事件" },
  { id: "risk", label: "风控" },
];
