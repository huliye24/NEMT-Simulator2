/**
 * Copyright 2026 NEMT Lab
 *
 * Stores 统一导出
 */

import { create } from 'zustand';

// Re-export all stores
export {
  useStrategyStore,
  useStrategies,
  useSelectedStrategy,
  useSelectedStrategyId,
  useStrategiesByStatus,
  useRunningStrategies,
  useStrategyMetrics,
  type Strategy,
  type StrategyStatus,
  type StrategyMetrics,
} from './strategyStore';

export {
  useCapsuleStore,
  useCapsules,
  useSelectedCapsule,
  useActiveCapsules,
  useCapsulesByType,
  useCapsuleMetrics,
  useCapsuleHealth,
  type Capsule,
  type CapsuleType,
  type CapsuleStatus,
} from './capsuleStore';

export {
  useBinanceStore,
  useBinanceState,
  useBinancePrices,
  useBinanceKlines,
  useBinanceConnected,
  useSelectedSymbol,
  useSelectedInterval,
  usePriceBySymbol,
  useKlinesBySymbol,
  usePricesBySymbols,
  type MarketData,
  type BinanceState,
  type Interval,
} from './binanceStore';

export {
  useUIStore,
  useTheme,
  useSidebarCollapsed,
  useCommandPaletteOpen,
  useActiveView,
  useIsInitialized,
  useNavigateTo,
  useIsDarkMode,
  type Theme,
  type ViewId,
} from './uiStore';

export {
  useExecutionStore,
  useExecutionState,
  useCurrentPrice,
  useKlines,
  useNEMTState,
  useSignals,
  useLastSignal,
  useExecutionConnected,
  type KlineData,
  type NEMTSignal,
  type NEMTState,
} from './nemtExecutionStore';

export {
  useDualBufferStore,
  useCurrentSession,
  useBacktestProgress,
  useBacktestPeriod,
  useBacktestConfig,
  useLiveKlines,
  useLiveNEMTState,
  useLivePrice,
  useLiveRunning,
  useSessions,
  type BacktestResult,
  type BacktestPeriod,
  type BacktestConfig,
  type Trade,
  type KlineData,
  type NEMTState,
} from './dualBufferStore';

// 仓位管理 Store
export {
  usePositionStore,
  useEquity,
  useRiskTier,
  useAlgoMode,
  useRiskProfile,
  useLastCalculation,
  useOpenOrders,
  usePositionHistory,
  useWinRate,
  useTotalPositionPct,
  type RiskTier,
  type AlgoMode,
  type PositionResult,
  type PositionOrder,
  type PositionHistory,
  type RiskProfile,
  RISK_TIERS_CONFIG,
} from './positionStore';

// Strategy Module Integration
export {
  NEMTStrategyService,
  getStrategyService,
  runBacktestWithStore,
  getSignalFromStore,
  createAndAddStrategy,
  validateResult,
} from '../strategy/integration/storeIntegration';

// 导入需要的 hook
import { useStrategyStore } from './strategyStore';
import { useCapsuleStore } from './capsuleStore';
import { useBinanceStore } from './binanceStore';
import { useUIStore } from './uiStore';

/**
 * 平台总览指标 - 从多个 Store 组合
 */
export const usePlatformOverview = () => {
  const strategyMetrics = useStrategyMetrics();
  const capsuleMetrics = useCapsuleMetrics();
  const capsuleHealth = useCapsuleHealth();

  return {
    totalStrategies: strategyMetrics.totalStrategies,
    runningStrategies: strategyMetrics.runningCount,
    totalTrades: strategyMetrics.totalTrades,
    averageWinRate: strategyMetrics.averageWinRate,
    totalInstances: capsuleMetrics.totalInstances,
    activeCapsules: capsuleMetrics.activeCount,
    capsuleHealthPercent: capsuleHealth.healthPercent,
    isHealthy: capsuleHealth.isHealthy && strategyMetrics.runningCount > 0,
  };
};

/**
 * 当前选中项信息
 */
export const useCurrentSelection = () => {
  const selectedStrategy = useSelectedStrategy();
  const selectedSymbol = useSelectedSymbol();
  const activeView = useActiveView();

  return {
    selectedStrategy,
    selectedSymbol,
    activeView,
    hasSelection: !!(selectedStrategy || selectedSymbol),
  };
};

// 定义缺失的选择器
function useStrategyMetrics() {
  return useStrategyStore(state => {
    const strategies = state.strategies;
    return {
      totalStrategies: strategies.length,
      runningCount: strategies.filter(s => s.status === 'running').length,
      totalTrades: strategies.reduce((sum, s) => sum + (s.metrics?.totalTrades || 0), 0),
      averageWinRate: strategies.length > 0
        ? strategies.reduce((sum, s) => sum + (s.metrics?.winRate || 0), 0) / strategies.length
        : 0,
    };
  });
}

function useCapsuleMetrics() {
  return useCapsuleStore(state => {
    const capsules = state.capsules;
    return {
      totalInstances: capsules.length,
      activeCount: capsules.filter(c => c.status === 'active').length,
    };
  });
}

function useCapsuleHealth() {
  return useCapsuleStore(state => {
    const capsules = state.capsules;
    const total = capsules.length;
    const healthy = capsules.filter(c => c.status === 'active').length;
    return {
      totalInstances: total,
      healthyCount: healthy,
      healthPercent: total > 0 ? (healthy / total) * 100 : 100,
      isHealthy: total === 0 || healthy === total,
    };
  });
}

function useSelectedStrategy() {
  return useStrategyStore(state =>
    state.strategies.find(s => s.id === state.selectedStrategyId)
  );
}

function useSelectedSymbol() {
  return useBinanceStore(state => state.selectedSymbol);
}

function useActiveView() {
  return useUIStore(state => state.activeView);
}
