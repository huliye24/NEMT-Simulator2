/**
 * Copyright 2026 NEMT Lab
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

/**
 * Notion 看板集成 - TypeScript 类型定义
 * 支持: 交易日志、策略流水线、研究任务、信号预警
 */

// =====================
// Notion 配置
// =====================

export interface NotionConfig {
  apiKey: string;
  databaseId: string;
  enabled: boolean;
  syncInterval: number; // 同步间隔 (毫秒)
}

export const DEFAULT_NOTION_CONFIG: NotionConfig = {
  apiKey: '',
  databaseId: '',
  enabled: false,
  syncInterval: 30000 // 30秒
};

// =====================
// 看板任务类型
// =====================

export type NotionTaskType = 'trade_log' | 'strategy_pipeline' | 'research_task' | 'signal_alert';

// 看板状态 (对应 Notion 的 Column)
export type NotionBoardStatus = 
  | 'backlog'      // 待办/待处理
  | 'in_progress'  // 进行中
  | 'review'       // 审核/确认
  | 'completed'    // 已完成
  | 'archived';    // 归档

// 优先级
export type NotionPriority = 'low' | 'medium' | 'high' | 'urgent';

// 任务标签
export type NotionTag = 
  | 'analysis'           // 分析
  | 'backtest'           // 回测
  | 'live_trading'       // 实盘
  | 'research'           // 研究
  | 'development'        // 开发
  | 'review'             // 审核
  | 'vortex'             // 涡旋信号
  | 'resonance'          // 共振信号
  | 'trend'              // 趋势
  | 'risk_alert';        // 风控预警

// =====================
// 基础 Notion 任务
// =====================

export interface NotionTask {
  id: string;
  title: string;
  status: NotionBoardStatus;
  priority: NotionPriority;
  tags: NotionTag[];
  createdAt: string;
  updatedAt: string;
  createdBy: string;
  description?: string;
  taskType: NotionTaskType;
  
  // Notion 特定属性
  notionPageId?: string;
  notionUrl?: string;
}

// =====================
// 交易日志任务
// =====================

export interface TradeLogTask extends NotionTask {
  taskType: 'trade_log';
  
  // 交易相关字段
  symbol?: string;                    // 交易对 (如 BTCUSDT)
  direction?: 'long' | 'short';      // 方向
  entryPrice?: number;               // 入场价格
  exitPrice?: number;                // 出场价格
  positionSize?: number;             // 仓位大小
  pnl?: number;                      // 盈亏
  pnlPercent?: number;               // 盈亏百分比
  tradePhase?: string;               // 交易相位 (A/B/C/D)
  signalType?: string;               // 信号类型
  entryReason?: string;              // 入场原因
  exitReason?: string;               // 出场原因
  stopLoss?: number;                 // 止损价格
  takeProfit?: number;               // 止盈价格
  leverage?: number;                 // 杠杆倍数
  openedAt?: string;                 // 开仓时间
  closedAt?: string;                 // 平仓时间
  
  // NEMT 信号关联
  spectralWidth?: number;           // 谱宽
  dciValue?: number;                 // DCI 值
  vortexMaturity?: number;          // 涡旋成熟度
  resonanceConfidence?: number;      // 共振置信度
}

// =====================
// 策略流水线任务
// =====================

export type StrategyPipelineStage = 
  | 'idea'           // 想法
  | 'research'       // 研究
  | 'backtest'       // 回测
  | 'optimization'   // 优化
  | 'paper_trading'  // 模拟交易
  | 'live_ready'     // 待实盘
  | 'live'           // 实盘中
  | 'archived';      // 归档

export interface StrategyPipelineTask extends NotionTask {
  taskType: 'strategy_pipeline';
  
  // 策略相关字段
  strategyName?: string;             // 策略名称
  stage: StrategyPipelineStage;
  previousStage?: StrategyPipelineStage;
  
  // 回测结果
  backtestPeriod?: string;           // 回测周期
  backtestResult?: {
    totalReturn?: number;
    sharpeRatio?: number;
    maxDrawdown?: number;
    winRate?: number;
    totalTrades?: number;
  };
  
  // 策略参数
  parameters?: Record<string, number | string>;
  
  // 风险评估
  riskLevel?: 'low' | 'medium' | 'high';
  estimatedCapacity?: number;        // 策略容量
  
  // 备注
  notes?: string;
}

// =====================
// 研究任务
// =====================

export interface ResearchTask extends NotionTask {
  taskType: 'research_task';
  
  // 研究相关字段
  researchTopic?: string;            // 研究主题
  researchType?: 'market' | 'technical' | 'fundamental' | 'onchain' | 'other';
  
  // 研究结果
  findings?: string;                  // 主要发现
  conclusion?: string;               // 结论
  dataSources?: string[];            // 数据来源
  
  // 进度
  progress?: number;                  // 0-100
  deadline?: string;                 // 截止日期
  
  // 相关性
  relatedStrategies?: string[];      // 相关策略
  relatedSignals?: string[];         // 相关信号
}

// =====================
// 信号预警任务
// =====================

export interface SignalAlertTask extends NotionTask {
  taskType: 'signal_alert';
  
  // 信号相关字段
  signalName?: string;               // 信号名称
  signalCategory?: 'vortex' | 'resonance' | 'trend' | 'macro' | 'risk';
  
  // 信号详情
  signalStrength?: number;           // 信号强度 0-100
  signalValue?: number;               // 信号具体值
  threshold?: number;                 // 触发阈值
  
  // 市场上下文
  symbol?: string;
  marketPhase?: string;              // 市场相位
  priceLevel?: number;               // 价格水平
  
  // 预警状态
  acknowledged?: boolean;            // 是否已确认
  actionTaken?: string;              // 采取的行动
  resolved?: boolean;                // 是否已解决
  
  // 时间
  triggeredAt?: string;
  acknowledgedAt?: string;
  resolvedAt?: string;
}

// =====================
// 联合类型
// =====================

export type AnyNotionTask = TradeLogTask | StrategyPipelineTask | ResearchTask | SignalAlertTask;

// =====================
// 看板列配置
// =====================

export interface NotionBoardColumn {
  id: NotionBoardStatus;
  title: string;
  color: string;
  tasks: AnyNotionTask[];
}

// =====================
// 同步状态
// =====================

export type SyncStatus = 'idle' | 'syncing' | 'success' | 'error';

export interface NotionSyncState {
  status: SyncStatus;
  lastSyncTime: string | null;
  error: string | null;
  pendingChanges: number;
}

// =====================
// API 请求/响应类型
// =====================

export interface CreateTaskRequest {
  title: string;
  status: NotionBoardStatus;
  priority: NotionPriority;
  tags: NotionTag[];
  description?: string;
  taskType: NotionTaskType;
  // 类型特定字段
  [key: string]: unknown;
}

export interface UpdateTaskRequest {
  taskId: string;
  updates: Partial<{
    title: string;
    status: NotionBoardStatus;
    priority: NotionPriority;
    tags: NotionTag[];
    description: string;
    // 类型特定字段
    [key: string]: unknown;
  }>;
}

export interface NotionQueryResponse {
  object: string;
  results: NotionPage[];
  has_more: boolean;
  next_cursor: string | null;
}

export interface NotionPage {
  id: string;
  properties: Record<string, NotionProperty>;
  created_time: string;
  last_edited_time: string;
  url: string;
}

export interface NotionProperty {
  id: string;
  type: string;
  // 根据类型动态内容
  title?: Array<{ plain_text: string }>;
  rich_text?: Array<{ plain_text: string }>;
  select?: { name: string };
  multi_select?: Array<{ name: string }>;
  checkbox?: boolean;
  number?: number;
  date?: { start: string; end?: string };
  url?: string;
  email?: string;
  phone_number?: string;
  people?: Array<{ id: string }>;
  relation?: Array<{ id: string }>;
  rollup?: unknown;
  formula?: unknown;
  created_time?: string;
  last_edited_time?: string;
}

// =====================
// Notion API 配置
// =====================

export const NOTION_API_BASE = 'https://api.notion.com/v1';
export const NOTION_API_VERSION = '2022-06-28';

// =====================
// 看板状态配置
// =====================

export const BOARD_STATUS_CONFIG: Record<NotionBoardStatus, { label: string; color: string }> = {
  backlog: { label: '待办', color: '#6b7280' },
  in_progress: { label: '进行中', color: '#3b82f6' },
  review: { label: '审核', color: '#f59e0b' },
  completed: { label: '已完成', color: '#10b981' },
  archived: { label: '归档', color: '#9ca3af' }
};

// =====================
// 优先级配置
// =====================

export const PRIORITY_CONFIG: Record<NotionPriority, { label: string; color: string }> = {
  low: { label: '低', color: '#6b7280' },
  medium: { label: '中', color: '#3b82f6' },
  high: { label: '高', color: '#f59e0b' },
  urgent: { label: '紧急', color: '#ef4444' }
};

// =====================
// 标签配置
// =====================

export const TAG_CONFIG: Record<NotionTag, { label: string; color: string }> = {
  analysis: { label: '分析', color: '#8b5cf6' },
  backtest: { label: '回测', color: '#06b6d4' },
  live_trading: { label: '实盘', color: '#10b981' },
  research: { label: '研究', color: '#f59e0b' },
  development: { label: '开发', color: '#3b82f6' },
  review: { label: '审核', color: '#ec4899' },
  vortex: { label: '涡旋', color: '#14b8a6' },
  resonance: { label: '共振', color: '#f97316' },
  trend: { label: '趋势', color: '#22c55e' },
  risk_alert: { label: '风控', color: '#ef4444' }
};
