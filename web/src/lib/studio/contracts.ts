/**
 * NEMT Studio cloud contracts.
 *
 * Current scope: strategy registry + execution health. NEMT Cloud does not yet
 * expose these services, so the Studio shows explicit "Not Connected" states
 * rather than fabricating runs or performance.
 *
 * Research and Experiments are deferred to a later product phase (removed from
 * the current navigation and routes on 2026-10-18). Their implementation and
 * API contract are preserved under deliverables/deferred/research-experiments.
 *
 * Future endpoints (authenticated, server-side risk enforced):
 *   GET  /api/v1/strategies                      -> StrategyListResponse
 *   GET  /api/v1/strategies/{id}                 -> StrategyDetail
 *   GET  /api/v1/execution/health                -> ExecutionHealth
 *
 * Execution decisions, risk validation and exchange adapters must stay in the
 * cloud service. The browser only monitors and issues authorised admin actions.
 */

export type ResourceState = "not_connected" | "loading" | "ready" | "error";

export const STRATEGY_LIFECYCLE = [
  { id: "draft", label: "Draft", zh: "草稿" },
  { id: "backtested", label: "Backtested", zh: "已回测" },
  { id: "validated", label: "Validated", zh: "已验证" },
  { id: "paper", label: "Paper", zh: "模拟盘" },
  { id: "risk_approval", label: "Risk Approval", zh: "风控审批" },
  { id: "live", label: "Live", zh: "实盘" },
  { id: "paused", label: "Paused / Stopped", zh: "暂停 / 停止" },
] as const;

export type StrategyLifecycle = (typeof STRATEGY_LIFECYCLE)[number]["id"];

export type StrategyRunMode = "BACKTEST" | "PAPER" | "LIVE";

export type StrategyDeploymentState =
  | "NOT_DEPLOYED"
  | "PENDING_APPROVAL"
  | "APPROVED"
  | "DEPLOYED"
  | "PAUSED"
  | "STOPPED";

export type RiskGrade = "UNRATED" | "LOW" | "MEDIUM" | "HIGH";

export interface StrategySummary {
  id: string;
  name: string;
  version: string;
  lifecycle: StrategyLifecycle;
  mode: StrategyRunMode;
  market: string;
  risk_grade: RiskGrade;
  deployment_state: StrategyDeploymentState;
  last_activity_at: string | null;
  research_id: string | null;
  hypothesis: string | null;
}

export interface StrategyParameter {
  key: string;
  value: string;
  unit: string | null;
  description: string | null;
}

export interface BacktestSummary {
  id: string;
  label: string;
  started_at: string;
  finished_at: string | null;
  sharpe: number | null;
  max_drawdown: number | null;
  metrics_available: boolean;
}

export interface StrategyDetail extends StrategySummary {
  parameters: StrategyParameter[];
  backtests: BacktestSummary[];
  /** References reserved for the deferred Experiments phase. */
  experiment_ids: string[];
  performance_note: string | null;
  performance_available: boolean;
  deployment_note: string | null;
  logs: { at: string; level: "info" | "warning" | "error"; message: string }[];
}

export interface StrategyListSnapshot {
  state: ResourceState;
  items: StrategySummary[];
  reason: string | null;
  fetched_at: string | null;
}

export interface ExecutionHealth {
  state: ResourceState;
  service_connected: boolean;
  active_runs: number;
  risk_validation: "unknown" | "connected" | "blocked";
  reason: string | null;
}

const STRATEGY_REASON =
  "NEMT Cloud Strategy API 尚未接入。策略、回测与部署数据不会被前端伪造。";

export const STRATEGY_SNAPSHOT: StrategyListSnapshot = {
  state: "not_connected",
  items: [],
  reason: STRATEGY_REASON,
  fetched_at: null,
};

export const EXECUTION_HEALTH: ExecutionHealth = {
  state: "not_connected",
  service_connected: false,
  active_runs: 0,
  risk_validation: "unknown",
  reason: "策略执行服务尚未接入；当前没有自动执行实例。",
};

/**
 * Future client boundary. These functions are deliberately not called until
 * the corresponding cloud endpoints exist; the UI uses the explicit snapshot
 * above so that "Not Connected" can never be confused with an empty result.
 */
export interface StrategyService {
  list(): Promise<StrategyListSnapshot>;
  get(id: string): Promise<StrategyDetail | null>;
  executionHealth(): Promise<ExecutionHealth>;
}

export const strategyService: StrategyService = {
  async list() {
    return STRATEGY_SNAPSHOT;
  },
  async get() {
    return null;
  },
  async executionHealth() {
    return EXECUTION_HEALTH;
  },
};
