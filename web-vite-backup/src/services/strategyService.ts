/**
 * Strategy Service
 * 前端策略管理服务 - 调用云端策略层API
 */

import { StrategyStatus, StrategyType } from '../types/nemt';

// =====================
// 配置
// =====================

const API_CONFIG = {
  baseUrl: 'http://localhost:8080',
  timeout: 60000, // 60秒超时（回测可能较慢）
};

// =====================
// 类型定义
// =====================

// 策略
export interface Strategy {
  id: string;
  name: string;
  strategy_type: StrategyType | string;
  version: string;
  description: string;
  status: StrategyStatus | string;
  capital_weight: number;
  metrics: StrategyMetrics;
  performance: number[];
  created_at: string;
  last_trade_at: string | null;
  last_update_at: string;
  params: Record<string, any>;
}

// 策略指标
export interface StrategyMetrics {
  sharpe_ratio: number;
  max_drawdown: number;
  win_rate: number;
  profit_factor: number;
  total_trades: number;
  avg_holding_hours: number;
  total_pnl: number;
  recent_sharpe: number;
  recent_return: number;
}

// 策略评分
export interface StrategyScore {
  strategy_id: string;
  total_score: number;
  profitability_score: number;
  consistency_score: number;
  risk_adjusted_score: number;
  adaptability_score: number;
  reasoning: string;
}

// 淘汰事件
export interface EvictionEvent {
  strategy_id: string;
  strategy_name: string;
  action: 'dormant' | 'dead' | 'activate' | 'keep';
  score_before: number;
  score_after: number;
  reason: string;
  timestamp: string;
}

// 回测配置
export interface BacktestConfig {
  strategy_id: string;
  symbol?: string;
  start_date?: string;
  end_date?: string;
  initial_capital?: number;
  slippage_bps?: number;
  commission_bps?: number;
}

// 回测结果
export interface BacktestResult {
  strategy_id: string;
  initial_capital: number;
  final_equity: number;
  total_pnl: number;
  return_pct: number;
  sharpe_ratio: number;
  max_drawdown: number;
  win_rate: number;
  profit_factor: number;
  total_trades: number;
  trades: Trade[];
  equity_curve: EquityPoint[];
}

// 交易记录
export interface Trade {
  entry_time: string;
  entry_price: number;
  exit_time: string;
  exit_price: number;
  pnl_pct: number;
  pnl_value: number;
}

// 权益曲线点
export interface EquityPoint {
  index: number;
  price: number;
  equity: number;
  position: number;
  timestamp: string | number;
}

// 策略模板
export interface StrategyTemplate {
  id: string;
  name: string;
  type: string;
  params: Record<string, any>;
}

// 策略统计
export interface StrategyStats {
  total: number;
  alive: number;
  testing: number;
  dormant: number;
  dead: number;
  avg_score: number;
}

// API响应
interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
  timestamp?: string;
}

// =====================
// HTTP 客户端
// =====================

class ApiClient {
  private baseUrl: string;
  private timeout: number;

  constructor(baseUrl: string, timeout: number = 60000) {
    this.baseUrl = baseUrl;
    this.timeout = timeout;
  }

  async post<T>(endpoint: string, body: any): Promise<ApiResponse<T>> {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), this.timeout);

      const response = await fetch(`${this.baseUrl}${endpoint}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(body),
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      if (error instanceof Error) {
        if (error.name === 'AbortError') {
          throw new Error(`请求超时 (${this.timeout}ms)`);
        }
        throw error;
      }
      throw new Error('Unknown error');
    }
  }

  async get<T>(endpoint: string): Promise<ApiResponse<T>> {
    try {
      const response = await fetch(`${this.baseUrl}${endpoint}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      if (error instanceof Error) {
        throw error;
      }
      throw new Error('Unknown error');
    }
  }
}

// =====================
// 策略服务
// =====================

class StrategyService {
  private apiClient: ApiClient;

  constructor() {
    this.apiClient = new ApiClient(API_CONFIG.baseUrl, API_CONFIG.timeout);
  }

  /**
   * 设置API地址
   */
  setBaseUrl(url: string): void {
    this.apiClient = new ApiClient(url, API_CONFIG.timeout);
  }

  /**
   * 获取策略模板列表
   */
  async getTemplates(): Promise<StrategyTemplate[]> {
    const response = await this.apiClient.get<{ templates: StrategyTemplate[]; count: number }>('/api/strategy/templates');
    if (response.success && response.data) {
      return response.data.templates;
    }
    throw new Error(response.error || '获取模板失败');
  }

  /**
   * 获取策略列表
   */
  async listStrategies(status?: StrategyStatus): Promise<Strategy[]> {
    const endpoint = status ? `/api/strategy/list?status=${status}` : '/api/strategy/list';
    const response = await this.apiClient.get<{ strategies: Strategy[]; count: number }>(endpoint);
    if (response.success && response.data) {
      return response.data.strategies;
    }
    throw new Error(response.error || '获取策略列表失败');
  }

  /**
   * 获取策略详情
   */
  async getStrategy(strategyId: string): Promise<{ strategy: Strategy; score: StrategyScore | null }> {
    const response = await this.apiClient.post<{ strategy: Strategy; score: StrategyScore | null }>('/api/strategy/get', {
      strategy_id: strategyId,
    });
    if (response.success && response.data) {
      return response.data;
    }
    throw new Error(response.error || '获取策略失败');
  }

  /**
   * 创建策略
   */
  async createStrategy(template: string, name?: string, params?: Record<string, any>): Promise<Strategy> {
    const response = await this.apiClient.post<Strategy>('/api/strategy/create', {
      template,
      name,
      params,
    });
    if (response.success && response.data) {
      return response.data;
    }
    throw new Error(response.error || '创建策略失败');
  }

  /**
   * 更新策略
   */
  async updateStrategy(strategyId: string, updates: Partial<Strategy>): Promise<Strategy> {
    const response = await this.apiClient.post<Strategy>('/api/strategy/update', {
      strategy_id: strategyId,
      updates,
    });
    if (response.success && response.data) {
      return response.data;
    }
    throw new Error(response.error || '更新策略失败');
  }

  /**
   * 删除策略
   */
  async deleteStrategy(strategyId: string): Promise<boolean> {
    const response = await this.apiClient.post<null>('/api/strategy/delete', {
      strategy_id: strategyId,
    });
    if (response.success) {
      return true;
    }
    throw new Error(response.error || '删除策略失败');
  }

  /**
   * 运行回测
   */
  async runBacktest(strategyId: string, prices: number[], config?: Partial<BacktestConfig>): Promise<BacktestResult> {
    const response = await this.apiClient.post<BacktestResult>('/api/strategy/backtest', {
      strategy_id: strategyId,
      prices,
      config: config || {},
    });
    if (response.success && response.data) {
      return response.data;
    }
    throw new Error(response.error || '回测失败');
  }

  /**
   * 批量回测
   */
  async batchBacktest(strategyIds: string[], prices: number[], config?: Partial<BacktestConfig>): Promise<Record<string, BacktestResult>> {
    const response = await this.apiClient.post<{ results: Record<string, BacktestResult>; count: number }>('/api/strategy/batch_backtest', {
      strategy_ids: strategyIds,
      prices,
      config: config || {},
    });
    if (response.success && response.data) {
      return response.data.results;
    }
    throw new Error(response.error || '批量回测失败');
  }

  /**
   * 获取策略评分
   */
  async getScore(strategyId: string): Promise<StrategyScore> {
    const response = await this.apiClient.post<StrategyScore>('/api/strategy/score', {
      strategy_id: strategyId,
    });
    if (response.success && response.data) {
      return response.data;
    }
    throw new Error(response.error || '获取评分失败');
  }

  /**
   * 获取所有评分
   */
  async getAllScores(): Promise<StrategyScore[]> {
    const response = await this.apiClient.get<{ scores: StrategyScore[]; count: number }>('/api/strategy/scores');
    if (response.success && response.data) {
      return response.data.scores;
    }
    throw new Error(response.error || '获取评分失败');
  }

  /**
   * 触发淘汰评估
   */
  async evict(strategyId?: string): Promise<EvictionEvent[]> {
    const response = await this.apiClient.post<{ events: EvictionEvent[]; count: number }>('/api/strategy/evict', {
      strategy_id: strategyId,
    });
    if (response.success && response.data) {
      return response.data.events;
    }
    throw new Error(response.error || '淘汰评估失败');
  }

  /**
   * 获取淘汰事件
   */
  async getEvictionEvents(limit: number = 10): Promise<EvictionEvent[]> {
    const response = await this.apiClient.get<{ events: EvictionEvent[]; count: number }>(`/api/strategy/events?limit=${limit}`);
    if (response.success && response.data) {
      return response.data.events;
    }
    throw new Error(response.error || '获取事件失败');
  }

  /**
   * 重新分配权重
   */
  async rebalance(mode: 'equal' | 'score' = 'equal'): Promise<Record<string, number>> {
    const response = await this.apiClient.post<{ weights: Record<string, number>; mode: string }>('/api/strategy/rebalance', {
      mode,
    });
    if (response.success && response.data) {
      return response.data.weights;
    }
    throw new Error(response.error || '权重分配失败');
  }

  /**
   * 获取策略统计
   */
  async getStats(): Promise<StrategyStats> {
    const response = await this.apiClient.get<StrategyStats>('/api/strategy/stats');
    if (response.success && response.data) {
      return response.data;
    }
    throw new Error(response.error || '获取统计失败');
  }

  /**
   * 批量创建策略
   */
  async batchCreate(strategies: Array<{ template: string; name?: string; params?: Record<string, any> }>): Promise<Strategy[]> {
    const response = await this.apiClient.post<{ strategies: Strategy[]; count: number }>('/api/strategy/batch_create', {
      strategies,
    });
    if (response.success && response.data) {
      return response.data.strategies;
    }
    throw new Error(response.error || '批量创建失败');
  }

  /**
   * 检查服务状态
   */
  async checkStatus(): Promise<{ available: boolean; message: string }> {
    try {
      const response = await this.apiClient.get<any>('/api/pipeline/status');
      if (response.success) {
        return {
          available: true,
          message: '策略服务正常',
        };
      }
      return {
        available: false,
        message: response.error || '未知错误',
      };
    } catch (error) {
      return {
        available: false,
        message: error instanceof Error ? error.message : '连接失败',
      };
    }
  }
}

// =====================
// 单例
// =====================

let strategyService: StrategyService | null = null;

export function getStrategyService(): StrategyService {
  if (!strategyService) {
    strategyService = new StrategyService();
  }
  return strategyService;
}

// 导出类供直接使用
export { StrategyService };

// 导出类型
export type {
  Strategy,
  StrategyMetrics,
  StrategyScore,
  EvictionEvent,
  BacktestConfig,
  BacktestResult,
  Trade,
  EquityPoint,
  StrategyTemplate,
  StrategyStats,
};
