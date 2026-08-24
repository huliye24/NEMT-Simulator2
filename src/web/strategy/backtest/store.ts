/**
 * Copyright 2026 NEMT Lab
 *
 * Backtest Store
 * Zustand 状态管理
 */

import { create } from 'zustand';
import { subscribeWithSelector } from 'zustand/middleware';
import type {
  BacktestConfig,
  BacktestResult,
  BacktestProgress,
  BacktestStatus,
  DataSourceConfig,
  Trade,
} from './types';

interface StrategyConfig {
  id: string;
  name: string;
  strategy: 'ma_cross' | 'rsi' | 'bollinger' | 'macd' | 'combo' | 'turtle';
  canShort: boolean;
  stoploss: number;
  trailingStop: boolean;
  minimalRoi: Record<string, number>;
  useExitSignal: boolean;
  maxOpenTrades: number;
  startupCandleCount: number;
}

interface BacktestState {
  // 配置
  config: BacktestConfig;
  strategyConfig: StrategyConfig;
  dataSource: DataSourceConfig;

  // 状态
  status: BacktestStatus;
  progress: number;
  currentBar: number;
  totalBars: number;

  // 结果
  result: BacktestResult | null;
  trades: Trade[];
  selectedTrade: Trade | null;

  // 错误
  error: string | null;

  // 快捷设置
  presets: Record<string, Partial<BacktestConfig & StrategyConfig>>;

  // Actions
  setConfig: (config: Partial<BacktestConfig>) => void;
  setStrategyConfig: (config: Partial<StrategyConfig>) => void;
  setDataSource: (source: Partial<DataSourceConfig>) => void;
  setStatus: (status: BacktestStatus) => void;
  setProgress: (progress: number, currentBar: number, totalBars: number) => void;
  setResult: (result: BacktestResult) => void;
  setSelectedTrade: (trade: Trade | null) => void;
  setError: (error: string | null) => void;
  loadPreset: (presetName: string) => void;
  reset: () => void;
}

const defaultConfig: BacktestConfig = {
  initialCapital: 10000,
  commissionRate: 0.001,
  slippage: 0.0005,
  startDate: Date.now() - 90 * 24 * 60 * 60 * 1000,
  endDate: Date.now(),
  pair: 'BTCUSDT',
  timeframe: '1h',
  strategy: 'ma_cross',
  feeTier: ' Binance',
  marginRatio: 1,
  hedging: false,
  dryRun: true,
};

const defaultStrategyConfig: StrategyConfig = {
  id: 'default',
  name: 'Default Strategy',
  strategy: 'ma_cross',
  canShort: false,
  stoploss: -0.1,
  trailingStop: false,
  minimalRoi: { '0': 0.05 },
  useExitSignal: true,
  maxOpenTrades: 1,
  startupCandleCount: 50,
};

const defaultState: Pick<
  BacktestState,
  'status' | 'progress' | 'currentBar' | 'totalBars' | 'result' | 'trades' | 'selectedTrade' | 'error'
> = {
  status: 'idle',
  progress: 0,
  currentBar: 0,
  totalBars: 0,
  result: null,
  trades: [],
  selectedTrade: null,
  error: null,
};

export const useBacktestStore = create<BacktestState>()(
  subscribeWithSelector((set, get) => ({
    // 初始状态
    config: defaultConfig,
    strategyConfig: defaultStrategyConfig,
    dataSource: {
      type: 'binance',
      symbol: 'BTCUSDT',
      timeframe: '1h',
    },

    ...defaultState,

    // 预设配置
    presets: {
      conservative: {
        initialCapital: 10000,
        commissionRate: 0.001,
        slippage: 0.001,
        maxOpenTrades: 1,
        stoploss: -0.05,
        minimalRoi: { '0': 0.03 },
      },
      aggressive: {
        initialCapital: 50000,
        commissionRate: 0.0005,
        slippage: 0.0002,
        maxOpenTrades: 3,
        stoploss: -0.15,
        minimalRoi: { '0': 0.1, '60': 0.05 },
      },
      highFrequency: {
        initialCapital: 5000,
        commissionRate: 0.0002,
        slippage: 0.0001,
        maxOpenTrades: 5,
        stoploss: -0.02,
        minimalRoi: { '0': 0.01, '15': 0.005, '60': 0.02 },
      },
    },

    // Actions
    setConfig: (config) =>
      set((state) => ({ config: { ...state.config, ...config } })),

    setStrategyConfig: (config) =>
      set((state) => ({ strategyConfig: { ...state.strategyConfig, ...config } })),

    setDataSource: (source) =>
      set((state) => ({ dataSource: { ...state.dataSource, ...source } })),

    setStatus: (status) => set({ status }),

    setProgress: (progress, currentBar, totalBars) =>
      set({ progress, currentBar, totalBars }),

    setResult: (result) =>
      set({
        result,
        trades: result.trades,
        progress: 100,
        status: 'completed',
      }),

    setSelectedTrade: (trade) => set({ selectedTrade: trade }),

    setError: (error) => set({ error, status: 'error' }),

    loadPreset: (presetName) => {
      const preset = get().presets[presetName];
      if (preset) {
        set((state) => ({
          config: { ...state.config, ...preset },
          strategyConfig: {
            ...state.strategyConfig,
            maxOpenTrades: preset.maxOpenTrades ?? state.strategyConfig.maxOpenTrades,
            stoploss: preset.stoploss ?? state.strategyConfig.stoploss,
            minimalRoi: preset.minimalRoi ?? state.strategyConfig.minimalRoi,
          },
        }));
      }
    },

    reset: () =>
      set({
        ...defaultState,
        config: { ...defaultConfig, strategy: 'ma_cross' },
        strategyConfig: defaultStrategyConfig,
        dataSource: {
          type: 'binance',
          symbol: 'BTCUSDT',
          timeframe: '1h',
        },
      }),
  }))
);

// 导出进度对象（用于组件直接使用）
export const useBacktestProgress = (): BacktestProgress => {
  const { status, progress, currentBar, totalBars, result } = useBacktestStore();
  return {
    status,
    progress,
    currentBar,
    totalBars,
    currentEquity: result?.equityCurve[result.equityCurve.length - 1]?.value ?? 0,
    openTrades: result?.trades.filter((t) => !t.exitTime).length ?? 0,
    completedTrades: result?.trades.filter((t) => !!t.exitTime).length ?? 0,
  };
};
