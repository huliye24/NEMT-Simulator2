/**
 * NEMT Studio V3.1 — AI-native strategy library contracts.
 *
 * AI discovers and proposes. Humans curate and approve. The runtime executes
 * under independent risk controls. Retention is NOT execution approval.
 *
 * The publisher API does not exist yet, so the Studio renders an explicit
 * "not connected" state. Nothing in this module fabricates strategy metrics,
 * experiment outcomes or AI decisions.
 *
 * Proposed service contract (server-enforced identity + RBAC):
 *   POST /api/v1/strategy-submissions                 (service identity)
 *   GET  /api/v1/strategy-submissions                 (authenticated)
 *   GET  /api/v1/strategy-submissions/{id}            (authenticated)
 *   POST /api/v1/strategy-submissions/{id}/retain     (admin / curator)
 *   POST /api/v1/strategy-submissions/{id}/reject     (admin / curator)
 *   POST /api/v1/strategy-submissions/{id}/archive    (admin / curator)
 *
 * Agents may submit candidates, never approve them, never allocate capital and
 * never touch live deployment state.
 */

import type { ResourceState } from "./contracts";

export const STRATEGY_LIFECYCLE_V31 = [
  {
    id: "submitted",
    label: "Submitted",
    zh: "已提交",
    note: "验证产物进入收件箱，等待人工审核。",
  },
  {
    id: "under_review",
    label: "Under Review",
    zh: "审核中",
    note: "研究来源、样本外证据与风控假设接受核查。",
  },
  {
    id: "retained",
    label: "Retained",
    zh: "已保留",
    note: "保留入库；不代表允许模拟运行或分配资金。",
  },
  {
    id: "rejected",
    label: "Rejected",
    zh: "已拒绝",
    note: "当前候选版本被拒绝，原因进入审计记录。",
  },
  {
    id: "validated_for_paper",
    label: "Validated for Paper",
    zh: "获准模拟",
    note: "独立审批通过后，才允许进入 Paper 验证。",
  },
  {
    id: "paper_running",
    label: "Paper Running",
    zh: "模拟运行",
    note: "运行于独立模拟账户，不连接真实资金。",
  },
  {
    id: "paused",
    label: "Paused",
    zh: "已暂停",
    note: "因风险、退化或人工决定暂停运行。",
  },
  {
    id: "retired",
    label: "Retired",
    zh: "已退役",
    note: "策略停止使用，历史引用保持完整。",
  },
  {
    id: "archived",
    label: "Archived",
    zh: "已归档",
    note: "从活跃库移出，不物理删除历史数据。",
  },
] as const;

export type StrategyLifecycleV31 =
  (typeof STRATEGY_LIFECYCLE_V31)[number]["id"];

export type ValidationState =
  | "PENDING"
  | "VERIFIED"
  | "PARTIAL"
  | "FAILED"
  | "NOT_PROVIDED";

export type AllocationState =
  | "NOT_ELIGIBLE"
  | "ELIGIBLE"
  | "ALLOCATED"
  | "SUSPENDED";

export interface ValidationEvidence {
  research_id: string | null;
  matlab_experiment_ids: string[];
  gpu_experiment_ids: string[];
  dataset_ids: string[];
  oos_verified: boolean;
  validation_state: ValidationState;
  transaction_cost_assumptions: string | null;
  risk_metrics_present: boolean;
}

export interface StrategyArtifact {
  strategy_id: string;
  version: string;
  source_commit: string | null;
  code_hash: string | null;
  hypothesis: string;
  market: string;
  timeframe: string;
  parameters: Record<string, string>;
  evidence: ValidationEvidence;
  recommendation: string | null;
  manifest_hash: string | null;
}

export interface StrategySubmission {
  id: string;
  artifact: StrategyArtifact;
  lifecycle: StrategyLifecycleV31;
  submitted_by: string;
  submitted_at: string;
  reviewed_at: string | null;
  reviewed_by: string | null;
  review_reason: string | null;
  allocation_state: AllocationState;
}

export interface StrategyAllocation {
  id: string;
  strategy_id: string;
  version: string;
  market_regime: string | null;
  target_weight: string | null;
  actual_weight: string | null;
  risk_budget: string | null;
  last_rebalance: string | null;
  reason: string | null;
}

export interface StrategyLibrarySnapshot {
  state: ResourceState;
  submissions: StrategySubmission[];
  allocations: StrategyAllocation[];
  reason: string | null;
  fetched_at: string | null;
}

const NOT_CONNECTED_REASON =
  "Strategy Publisher API 尚未接入。AI 候选、验证证据与配置权重不会被前端伪造。";

export const STRATEGY_LIBRARY_SNAPSHOT: StrategyLibrarySnapshot = {
  state: "not_connected",
  submissions: [],
  allocations: [],
  reason: NOT_CONNECTED_REASON,
  fetched_at: null,
};

/**
 * Future client boundary. The service is intentionally disabled until the
 * server-side publisher exists. Actions must never be reimplemented in the
 * browser: retention, paper approval and allocation are independent,
 * auditable server decisions.
 */
export interface StrategyPublisherService {
  list(): Promise<StrategyLibrarySnapshot>;
  retain(id: string, reason: string): Promise<void>;
  reject(id: string, reason: string): Promise<void>;
  archive(id: string, reason: string): Promise<void>;
}

export const strategyPublisherService: StrategyPublisherService = {
  async list() {
    return STRATEGY_LIBRARY_SNAPSHOT;
  },
  async retain() {
    throw new Error("Strategy Publisher API 尚未接入。");
  },
  async reject() {
    throw new Error("Strategy Publisher API 尚未接入。");
  },
  async archive() {
    throw new Error("Strategy Publisher API 尚未接入。");
  },
};

export const STRATEGY_BOUNDARIES = [
  {
    label: "Retain",
    zh: "保留",
    detail: "保存经过审核的候选版本。保存不会启动策略。",
  },
  {
    label: "Approve for Paper",
    zh: "批准模拟",
    detail: "独立审批后才可进入模拟运行；需要风控与资金边界。",
  },
  {
    label: "Allocate",
    zh: "分配权重",
    detail: "仅在模拟验证后参与目标权重配置，浏览器无权修改。",
  },
  {
    label: "Live",
    zh: "实盘",
    detail: "本阶段完全关闭。不存在自动进入实盘的路径。",
  },
] as const;
