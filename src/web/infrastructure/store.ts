/**
 * Copyright 2026 NEMT Lab
 *
 * Zustand 状态管理 - 带持久化和调试支持
 */

import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';

// 币安服务引用 (延迟加载)
let binanceServiceRef: typeof import('./binanceService') | null = null;

// ============================================
// 策略相关类型
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
// 胶囊相关类型
// ============================================

export type CapsuleType = 'market' | 'signal' | 'risk' | 'execution' | 'brain' | 'monitor';
export type CapsuleStatus = 'active' | 'inactive' | 'error';

export interface Capsule {
  id: string;
  name: string;
  type: CapsuleType;
  status: CapsuleStatus;
  instanceCount: number;
}

// ============================================
// 主题相关类型
// ============================================

export type Theme = 'dark' | 'light' | 'system';

// ============================================
// 视图类型
// ============================================

export type ViewId = 'strategies' | 'containers' | 'capsules' | 'monitor' | 'terminal' | 'market' | 'backtest';

// ============================================
// 市场数据类型
// ============================================

export interface MarketData {
  symbol: string;
  price: number;
  change24h: number;
  changePercent24h: number;
  high24h: number;
  low24h: number;
  volume24h: number;
  lastUpdate: number;
}

export interface BinanceState {
  connected: boolean;
  connecting: boolean;
  error: string | null;
  lastUpdate: number | null;
  selectedSymbol: string;
  selectedInterval: string;
  prices: Record<string, MarketData>;
  klines: Record<string, any[]>;
}

// ============================================
// 平台 Store
// ============================================

interface PlatformState {
  // 策略
  strategies: Strategy[];
  selectedStrategyId: string | null;

  // 胶囊
  capsules: Capsule[];

  // 视图
  activeView: ViewId;

  // 主题
  theme: Theme;

  // UI 状态
  sidebarCollapsed: boolean;
  commandPaletteOpen: boolean;

  // 加载状态
  isLoading: boolean;
  isInitialized: boolean;

  // 币安数据
  binance: BinanceState;
}

// ============================================
// 平台 Actions
// ============================================

interface PlatformActions {
  // 策略操作
  addStrategy: (strategy: Omit<Strategy, 'id' | 'createdAt' | 'updatedAt'>) => void;
  updateStrategy: (id: string, updates: Partial<Strategy>) => void;
  deleteStrategy: (id: string) => void;
  toggleStrategyStatus: (id: string) => void;
  selectStrategy: (id: string | null) => void;

  // 胶囊操作
  updateCapsuleStatus: (id: string, status: CapsuleStatus) => void;
  updateCapsuleInstanceCount: (id: string, count: number) => void;

  // 视图操作
  setActiveView: (view: ViewId) => void;

  // 主题操作
  setTheme: (theme: Theme) => void;

  // UI 操作
  toggleSidebar: () => void;
  toggleCommandPalette: () => void;
  setLoading: (loading: boolean) => void;

  // 初始化
  initialize: () => void;
  reset: () => void;

  // 币安操作
  connectBinance: (symbols?: string[], interval?: string) => Promise<void>;
  disconnectBinance: () => void;
  updateBinancePrice: (symbol: string, data: Partial<MarketData>) => void;
  updateBinanceKlines: (symbol: string, klines: any[]) => void;
  setSelectedSymbol: (symbol: string) => void;
  setSelectedInterval: (interval: string) => void;
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

const defaultCapsules: Capsule[] = [
  { id: 'market', name: 'MarketCapsule', type: 'market', status: 'active', instanceCount: 12 },
  { id: 'signal', name: 'SignalCapsule', type: 'signal', status: 'active', instanceCount: 8 },
  { id: 'risk', name: 'RiskCapsule', type: 'risk', status: 'active', instanceCount: 6 },
  { id: 'execution', name: 'ExecutionCapsule', type: 'execution', status: 'active', instanceCount: 4 },
  { id: 'brain', name: 'BrainCapsule', type: 'brain', status: 'active', instanceCount: 2 },
  { id: 'monitor', name: 'MonitorCapsule', type: 'monitor', status: 'error', instanceCount: 1 },
];

// ============================================
// Store 创建
// ============================================

export const usePlatformStore = create<PlatformState & PlatformActions>()(
  persist(
    (set, get) => ({
      // 初始状态
      strategies: defaultStrategies,
      selectedStrategyId: null,
      capsules: defaultCapsules,
      activeView: 'strategies',
      theme: 'dark',
      sidebarCollapsed: false,
      commandPaletteOpen: false,
      isLoading: false,
      isInitialized: false,

      // 币安数据状态
      binance: {
        connected: false,
        connecting: false,
        error: null,
        lastUpdate: null,
        selectedSymbol: 'BTCUSDT',
        selectedInterval: '1h',
        prices: {},
        klines: {},
      },

      // 策略操作
      addStrategy: (strategy) => {
        const now = new Date().toISOString().split('T')[0];
        const newStrategy: Strategy = {
          ...strategy,
          id: `strategy_${Date.now()}`,
          createdAt: now,
          updatedAt: now
        };
        set(state => ({
          strategies: [newStrategy, ...state.strategies]
        }));
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

      selectStrategy: (id) => {
        set({ selectedStrategyId: id });
      },

      // 胶囊操作
      updateCapsuleStatus: (id, status) => {
        set(state => ({
          capsules: state.capsules.map(c =>
            c.id === id ? { ...c, status } : c
          )
        }));
      },

      updateCapsuleInstanceCount: (id, count) => {
        set(state => ({
          capsules: state.capsules.map(c =>
            c.id === id ? { ...c, instanceCount: count } : c
          )
        }));
      },

      // 视图操作
      setActiveView: (view) => {
        set({ activeView: view });
      },

      // 主题操作
      setTheme: (theme) => {
        set({ theme });
        // 应用主题到 document
        document.documentElement.setAttribute('data-theme', theme);
      },

      // UI 操作
      toggleSidebar: () => {
        set(state => ({ sidebarCollapsed: !state.sidebarCollapsed }));
      },

      toggleCommandPalette: () => {
        set(state => ({ commandPaletteOpen: !state.commandPaletteOpen }));
      },

      setLoading: (loading) => {
        set({ isLoading: loading });
      },

      // 初始化
      initialize: () => {
        set({ isInitialized: true });
      },

      // 重置
      reset: () => {
        set({
          strategies: defaultStrategies,
          capsules: defaultCapsules,
          activeView: 'strategies',
          sidebarCollapsed: false,
          commandPaletteOpen: false,
          isLoading: false,
          binance: {
            connected: false,
            connecting: false,
            error: null,
            lastUpdate: null,
            selectedSymbol: 'BTCUSDT',
            selectedInterval: '1h',
            prices: {},
            klines: {},
          }
        });
      },

      // 币安操作
      connectBinance: async (symbols = ['BTCUSDT', 'ETHUSDT'], interval = '1h') => {
        const { binanceService } = await import('./binanceService');

        set(state => ({
          binance: { ...state.binance, connecting: true, error: null }
        }));

        try {
          await binanceService.connect(symbols, interval);

          // 订阅价格更新
          symbols.forEach(symbol => {
            binanceService.subscribeTicker(symbol, (ticker) => {
              const price = parseFloat(ticker.lastPrice);
              const change = parseFloat(ticker.priceChange);
              const changePercent = parseFloat(ticker.priceChangePercent);

              get().updateBinancePrice(symbol, {
                symbol,
                price,
                change24h: change,
                changePercent24h: changePercent,
                high24h: parseFloat(ticker.highPrice),
                low24h: parseFloat(ticker.lowPrice),
                volume24h: parseFloat(ticker.quoteVolume),
                lastUpdate: ticker.timestamp,
              });
            });
          });

          set(state => ({
            binance: {
              ...state.binance,
              connected: true,
              connecting: false,
              selectedSymbol: symbols[0],
              selectedInterval: interval,
            }
          }));
        } catch (error) {
          set(state => ({
            binance: {
              ...state.binance,
              connected: false,
              connecting: false,
              error: String(error),
            }
          }));
        }
      },

      disconnectBinance: async () => {
        if (!binanceServiceRef) {
          binanceServiceRef = await import('./binanceService');
        }
        binanceServiceRef.binanceService.disconnect();
        set(state => ({
          binance: {
            ...state.binance,
            connected: false,
            connecting: false,
            error: null,
          }
        }));
      },

      updateBinancePrice: (symbol, data) => {
        set(state => ({
          binance: {
            ...state.binance,
            prices: {
              ...state.binance.prices,
              [symbol]: { ...state.binance.prices[symbol], ...data },
            },
            lastUpdate: Date.now(),
          }
        }));
      },

      updateBinanceKlines: (symbol, klines) => {
        set(state => ({
          binance: {
            ...state.binance,
            klines: {
              ...state.binance.klines,
              [symbol]: klines,
            }
          }
        }));
      },

      setSelectedSymbol: (symbol) => {
        set(state => ({
          binance: { ...state.binance, selectedSymbol: symbol }
        }));
      },

      setSelectedInterval: (interval) => {
        set(state => ({
          binance: { ...state.binance, selectedInterval: interval }
        }));
      },
    }),
    {
      name: 'nemt-platform-storage',
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        strategies: state.strategies,
        capsules: state.capsules,
        theme: state.theme,
        sidebarCollapsed: state.sidebarCollapsed,
        activeView: state.activeView
      })
    }
  )
);

// ============================================
// 选择器 (优化性能)
// ============================================

export const useStrategies = () => usePlatformStore(state => state.strategies);
export const useSelectedStrategy = () => usePlatformStore(state =>
  state.strategies.find(s => s.id === state.selectedStrategyId)
);
export const useCapsules = () => usePlatformStore(state => state.capsules);
export const useActiveView = () => usePlatformStore(state => state.activeView);
export const useTheme = () => usePlatformStore(state => state.theme);

// 币安数据选择器
export const useBinanceState = () => usePlatformStore(state => state.binance);
export const useBinancePrices = () => usePlatformStore(state => state.binance.prices);
export const useBinanceConnected = () => usePlatformStore(state => state.binance.connected);

// ============================================
// 状态快照 (用于撤销/重做)
// ============================================

export interface StateSnapshot {
  id: string;
  timestamp: number;
  state: Partial<PlatformState>;
}

class StateHistory {
  private history: StateSnapshot[] = [];
  private currentIndex = -1;
  private maxHistory = 100;

  push(state: Partial<PlatformState>): void {
    // 删除当前位置之后的历史
    this.history = this.history.slice(0, this.currentIndex + 1);

    // 添加新状态
    this.history.push({
      id: `snapshot_${Date.now()}`,
      timestamp: Date.now(),
      state: JSON.parse(JSON.stringify(state))
    });

    // 限制历史长度
    if (this.history.length > this.maxHistory) {
      this.history = this.history.slice(-this.maxHistory);
    }

    this.currentIndex = this.history.length - 1;
  }

  undo(): StateSnapshot | null {
    if (this.currentIndex > 0) {
      this.currentIndex--;
      return this.history[this.currentIndex];
    }
    return null;
  }

  redo(): StateSnapshot | null {
    if (this.currentIndex < this.history.length - 1) {
      this.currentIndex++;
      return this.history[this.currentIndex];
    }
    return null;
  }

  canUndo(): boolean {
    return this.currentIndex > 0;
  }

  canRedo(): boolean {
    return this.currentIndex < this.history.length - 1;
  }

  clear(): void {
    this.history = [];
    this.currentIndex = -1;
  }
}

export const stateHistory = new StateHistory();
