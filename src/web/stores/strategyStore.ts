/**
 * Copyright 2026 NEMT Lab
 *
 * 策略 Store - 独立管理策略相关状态
 * 遵循原则：单一职责，只管策略
 */

import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';

// ============================================
// 类型定义
// ============================================

export type StrategyStatus = 'draft' | 'testing' | 'running' | 'paused' | 'archived';

export interface StrategyMetrics {
  totalTrades: number;
  winRate: number;
  totalPnL: number;
  sharpeRatio: number;
}

export interface Strategy {
  id: string;
  name: string;
  author: string;
  description: string;
  version: string;
  status: StrategyStatus;
  metrics: StrategyMetrics;
  tags: string[];
  createdAt: string;
  updatedAt: string;
}

// ============================================
// 状态接口
// ============================================

interface StrategyState {
  strategies: Strategy[];
  selectedStrategyId: string | null;
  isLoading: boolean;
}

// ============================================
// Actions 接口
// ============================================

interface StrategyActions {
  // 策略 CRUD
  addStrategy: (strategy: Omit<Strategy, 'id' | 'createdAt' | 'updatedAt'>) => Strategy;
  updateStrategy: (id: string, updates: Partial<Strategy>) => void;
  deleteStrategy: (id: string) => void;
  selectStrategy: (id: string | null) => void;

  // 策略状态控制
  toggleStrategyStatus: (id: string) => void;

  // 数据操作
  setLoading: (loading: boolean) => void;
  reset: () => void;
}

// ============================================
// 默认数据
// ============================================

const defaultStrategies: Strategy[] = [
  {
    id: '1',
    name: 'Vortex Breakout',
    author: 'NEMT Lab',
    description: '基于涡旋理论的突破策略，捕捉市场临界状态的方向选择机会',
    version: '2.1.0',
    status: 'running',
    metrics: { totalTrades: 1234, winRate: 0.62, totalPnL: 15680, sharpeRatio: 2.34 },
    tags: ['涡旋', '突破', '中长期'],
    createdAt: '2026-01-15',
    updatedAt: '2026-04-20'
  },
  {
    id: '2',
    name: 'Resonance Scalper',
    author: 'QuantumTrader',
    description: '利用市场共振频率进行高频套利，适用于波动性高的市场',
    version: '1.5.2',
    status: 'testing',
    metrics: { totalTrades: 892, winRate: 0.54, totalPnL: 3420, sharpeRatio: 1.87 },
    tags: ['共振', '高频', '套利'],
    createdAt: '2026-03-01',
    updatedAt: '2026-04-18'
  },
  {
    id: '3',
    name: 'Trend Follower Pro',
    author: 'AlgoMaster',
    description: '趋势跟踪策略，结合多周期分析确认趋势方向',
    version: '3.0.1',
    status: 'paused',
    metrics: { totalTrades: 3421, winRate: 0.48, totalPnL: -2340, sharpeRatio: 0.92 },
    tags: ['趋势', '多周期', 'CTA'],
    createdAt: '2025-11-20',
    updatedAt: '2026-04-10'
  },
  {
    id: '4',
    name: 'Noise Filter AI',
    author: 'AINexus',
    description: '使用 AI 模型过滤市场噪声，识别真实信号',
    version: '1.0.0-beta',
    status: 'draft',
    metrics: { totalTrades: 0, winRate: 0, totalPnL: 0, sharpeRatio: 0 },
    tags: ['AI', '噪声过滤', '实验性'],
    createdAt: '2026-04-25',
    updatedAt: '2026-04-25'
  }
];

// ============================================
// Store 创建
// ============================================

export const useStrategyStore = create<StrategyState & StrategyActions>()(
  persist(
    (set, get) => ({
      // 初始状态
      strategies: defaultStrategies,
      selectedStrategyId: null,
      isLoading: false,

      // 策略 CRUD
      addStrategy: (strategyData) => {
        const now = new Date().toISOString().split('T')[0];
        const newStrategy: Strategy = {
          ...strategyData,
          id: `strategy_${Date.now()}`,
          createdAt: now,
          updatedAt: now
        };
        set(state => ({
          strategies: [newStrategy, ...state.strategies]
        }));
        return newStrategy;
      },

      updateStrategy: (id, updates) => {
        set(state => ({
          strategies: state.strategies.map(s =>
            s.id === id
              ? { ...s, ...updates, updatedAt: new Date().toISOString().split('T')[0] }
              : s
          )
        }));
      },

      deleteStrategy: (id) => {
        set(state => ({
          strategies: state.strategies.filter(s => s.id !== id),
          selectedStrategyId: state.selectedStrategyId === id ? null : state.selectedStrategyId
        }));
      },

      selectStrategy: (id) => {
        set({ selectedStrategyId: id });
      },

      // 策略状态控制
      toggleStrategyStatus: (id) => {
        set(state => ({
          strategies: state.strategies.map(s => {
            if (s.id !== id) return s;
            const newStatus: StrategyStatus =
              s.status === 'running' ? 'paused' :
              s.status === 'paused' ? 'running' : s.status;
            return { ...s, status: newStatus, updatedAt: new Date().toISOString().split('T')[0] };
          })
        }));
      },

      // 数据操作
      setLoading: (loading) => {
        set({ isLoading: loading });
      },

      reset: () => {
        set({
          strategies: defaultStrategies,
          selectedStrategyId: null,
          isLoading: false
        });
      },
    }),
    {
      name: 'nemt-strategy-storage',
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        strategies: state.strategies,
      })
    }
  )
);

// ============================================
// 选择器 (Selectors)
// ============================================

export const useStrategies = () => useStrategyStore(state => state.strategies);

export const useSelectedStrategy = () => useStrategyStore(state =>
  state.strategies.find(s => s.id === state.selectedStrategyId)
);

export const useSelectedStrategyId = () => useStrategyStore(state => state.selectedStrategyId);

export const useStrategiesByStatus = (status: StrategyStatus) =>
  useStrategyStore(state => state.strategies.filter(s => s.status === status));

export const useRunningStrategies = () =>
  useStrategyStore(state => state.strategies.filter(s => s.status === 'running'));

export const useStrategyMetrics = () => useStrategyStore(state => {
  const strategies = state.strategies;
  return {
    totalStrategies: strategies.length,
    runningCount: strategies.filter(s => s.status === 'running').length,
    totalTrades: strategies.reduce((sum, s) => sum + s.metrics.totalTrades, 0),
    averageWinRate: strategies.length > 0
      ? strategies.reduce((sum, s) => sum + s.metrics.winRate, 0) / strategies.length
      : 0,
  };
});
