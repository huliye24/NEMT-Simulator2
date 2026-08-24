/**
 * Copyright 2026 NEMT Lab
 *
 * NEMT Strategy Templates
 * 借鉴 freqtrade 策略模板
 */

import type {
  IStrategy,
  StrategyConfig,
  DataFrame,
  StrategyMetadata,
  NEMTStrategy,
  NEMTStrategyConfig,
  NEMTState,
  Trade,
} from '../interfaces/IStrategy';

// ============================================
// 模板 1: 基础策略模板
// ============================================

export function createBasicStrategy(
  name: string,
  config: Partial<StrategyConfig>,
  indicatorsFn: (df: DataFrame) => DataFrame,
  entryFn: (df: DataFrame) => DataFrame,
  exitFn: (df: DataFrame) => DataFrame
): IStrategy {
  const fullConfig: StrategyConfig = {
    id: `strategy_${Date.now()}`,
    name,
    author: 'NEMT Lab',
    version: '1.0.0',
    timeframe: '1h',
    canShort: false,
    maxOpenTrades: 1,
    stoploss: -0.1,
    trailingStop: false,
    minimalRoi: { '0': 0.02 },
    processOnlyNewCandles: true,
    startupCandleCount: 20,
    useExitSignal: true,
    exitProfitOnly: false,
    ignoreRoiIfEntrySignal: false,
    positionAdjustmentEnable: false,
    ...config,
  };

  return {
    INTERFACE_VERSION: 3,
    config: fullConfig,

    populateIndicators: indicatorsFn,
    populateEntryTrend: entryFn,
    populateExitTrend: exitFn,
  };
}

// ============================================
// 模板 2: NEMT 策略模板
// ============================================

export function createNEMTStrategy(
  name: string,
  config: Partial<StrategyConfig & { nemtConfig: NEMTStrategyConfig }>,
  customIndicatorsFn?: (df: DataFrame) => DataFrame,
  customEntryFn?: (df: DataFrame, nemtState: NEMTState) => DataFrame,
  customExitFn?: (df: DataFrame, nemtState: NEMTState) => DataFrame
): NEMTStrategy {
  const defaultNemtConfig: NEMTStrategyConfig = {
    nemtCriticalEntropy: 0.7,
    nemtCriticalPsi: 0.5,
    nemtStablePsi: 0.3,
    nemtEmaAlpha: 0.3,
    validNemtPhases: ['critical_up', 'critical_down'],
    nemtExitOnPhaseChange: true,
  };

  const fullConfig: StrategyConfig = {
    id: `nemt_strategy_${Date.now()}`,
    name,
    author: 'NEMT Lab',
    version: '1.0.0',
    timeframe: '1h',
    canShort: true,
    maxOpenTrades: 3,
    stoploss: -0.05,
    trailingStop: true,
    trailingStopPositive: 0.02,
    trailingStopPositiveOffset: 0.01,
    minimalRoi: { '30': 0.01, '0': 0.03 },
    processOnlyNewCandles: true,
    startupCandleCount: 50,
    useExitSignal: true,
    exitProfitOnly: true,
    ignoreRoiIfEntrySignal: false,
    positionAdjustmentEnable: false,
    ...config,
  };

  const nemtConfig = { ...defaultNemtConfig, ...config.nemtConfig };

  return {
    INTERFACE_VERSION: 3,
    config: fullConfig,
    nemtConfig,

    populateIndicators: customIndicatorsFn || ((df) => df),

    populateEntryTrend: customEntryFn
      ? customEntryFn
      : (df: DataFrame, metadata: StrategyMetadata) => {
          // 默认 NEMT 入场逻辑
          const result = { ...df };
          result.enterLong = df.enterLong || 0;
          result.enterShort = df.enterShort || 0;

          // 检查 NEMT 入场条件
          if (df.nemtPhase === 'critical_up' && df.psi > nemtConfig.nemtCriticalPsi) {
            result.enterLong = 1;
          }
          if (df.nemtPhase === 'critical_down' && df.psi < -nemtConfig.nemtCriticalPsi) {
            result.enterShort = 1;
          }

          return result;
        },

    populateExitTrend: customExitFn
      ? customExitFn
      : (df: DataFrame, metadata: StrategyMetadata) => {
          // 默认 NEMT 出场逻辑
          const result = { ...df };
          result.exitLong = df.exitLong || 0;
          result.exitShort = df.exitShort || 0;

          // NEMT 出场条件
          if (nemtConfig.nemtExitOnPhaseChange) {
            if (df.nemtPhase === 'decay' || df.nemtPhase === 'stable') {
              result.exitLong = 1;
              result.exitShort = 1;
            }
          }

          return result;
        },

    getNEMTState(dataframe: DataFrame): NEMTState {
      return {
        psi: dataframe.psi || 0,
        phi: dataframe.phi || 0,
        entropy: dataframe.entropy || 0,
        phase: dataframe.nemtPhase || 'stable',
        waveAmplitude: dataframe.waveAmplitude || 0,
        waveFrequency: dataframe.waveFrequency || 0,
      };
    },

    checkNEMTEntryCondition(nemtState: NEMTState): boolean {
      const { phase, psi, entropy } = nemtState;

      if (entropy < nemtConfig.nemtCriticalEntropy) {
        return false;
      }

      if (nemtConfig.validNemtPhases.includes(phase)) {
        if (phase === 'critical_up' && psi > nemtConfig.nemtCriticalPsi) {
          return true;
        }
        if (phase === 'critical_down' && psi < -nemtConfig.nemtCriticalPsi) {
          return true;
        }
      }

      return false;
    },

    checkNEMTExitCondition(nemtState: NEMTState, trade: Trade): boolean {
      const { phase } = nemtState;

      if (!nemtConfig.nemtExitOnPhaseChange) {
        return false;
      }

      // 相位转换为 stable 或 decay 时出场
      if (phase === 'stable' || phase === 'decay') {
        return true;
      }

      return false;
    },
  };
}

// ============================================
// 模板 3: RSI 策略模板
// ============================================

export function createRSIStrategy(
  name: string,
  options: {
    timeframe?: string;
    buyRsiThreshold?: number;
    sellRsiThreshold?: number;
    stoploss?: number;
  } = {}
): IStrategy {
  const { buyRsiThreshold = 30, sellRsiThreshold = 70, stoploss = -0.1 } = options;

  const config: StrategyConfig = {
    id: `rsi_strategy_${Date.now()}`,
    name,
    author: 'NEMT Lab',
    version: '1.0.0',
    timeframe: '1h',
    canShort: false,
    maxOpenTrades: 1,
    stoploss,
    trailingStop: false,
    minimalRoi: { '60': 0.01, '30': 0.02, '0': 0.04 },
    processOnlyNewCandles: true,
    startupCandleCount: 50,
    useExitSignal: true,
    exitProfitOnly: false,
    ignoreRoiIfEntrySignal: false,
    positionAdjustmentEnable: false,
  };

  return {
    INTERFACE_VERSION: 3,
    config,

    populateIndicators: (df: DataFrame) => {
      // RSI 计算 (简化版)
      const period = 14;
      const changes = [];
      for (let i = 1; i < df.close.length; i++) {
        changes.push(df.close[i] - df.close[i - 1]);
      }

      let gains = 0;
      let losses = 0;
      for (const change of changes.slice(-period)) {
        if (change > 0) gains += change;
        else losses -= change;
      }

      const avgGain = gains / period;
      const avgLoss = losses / period;
      const rs = avgLoss === 0 ? 100 : avgGain / avgLoss;
      const rsi = 100 - 100 / (1 + rs);

      return {
        ...df,
        rsi,
      };
    },

    populateEntryTrend: (df: DataFrame, metadata: StrategyMetadata) => {
      return {
        ...df,
        enterLong: df.rsi < buyRsiThreshold ? 1 : 0,
        enterShort: 0,
      };
    },

    populateExitTrend: (df: DataFrame, metadata: StrategyMetadata) => {
      return {
        ...df,
        exitLong: df.rsi > sellRsiThreshold ? 1 : 0,
        exitShort: 0,
      };
    },
  };
}

// ============================================
// 模板 4: MACD 策略模板
// ============================================

export function createMACDStrategy(
  name: string,
  options: {
    fastPeriod?: number;
    slowPeriod?: number;
    signalPeriod?: number;
    stoploss?: number;
  } = {}
): IStrategy {
  const { fastPeriod = 12, slowPeriod = 26, signalPeriod = 9, stoploss = -0.1 } = options;

  const config: StrategyConfig = {
    id: `macd_strategy_${Date.now()}`,
    name,
    author: 'NEMT Lab',
    version: '1.0.0',
    timeframe: '1h',
    canShort: false,
    maxOpenTrades: 1,
    stoploss,
    trailingStop: false,
    minimalRoi: { '0': 0.02 },
    processOnlyNewCandles: true,
    startupCandleCount: 50,
    useExitSignal: true,
    exitProfitOnly: false,
    ignoreRoiIfEntrySignal: false,
    positionAdjustmentEnable: false,
  };

  return {
    INTERFACE_VERSION: 3,
    config,

    populateIndicators: (df: DataFrame) => {
      // 简化 MACD 计算
      const emaFast = calculateEMA(df.close, fastPeriod);
      const emaSlow = calculateEMA(df.close, slowPeriod);
      const macdLine = emaFast.map((v, i) => v - emaSlow[i]);
      const signalLine = calculateEMA(macdLine, signalPeriod);
      const histogram = macdLine.map((v, i) => v - signalLine[i]);

      return {
        ...df,
        macd: macdLine,
        macdsignal: signalLine,
        macdhist: histogram,
      };
    },

    populateEntryTrend: (df: DataFrame, metadata: StrategyMetadata) => {
      const lastIdx = df.close.length - 1;
      const hist = df.macdhist[lastIdx];
      const prevHist = df.macdhist[lastIdx - 1];

      return {
        ...df,
        enterLong: hist > 0 && prevHist <= 0 ? 1 : 0,
        enterShort: hist < 0 && prevHist >= 0 ? 1 : 0,
      };
    },

    populateExitTrend: (df: DataFrame, metadata: StrategyMetadata) => {
      const lastIdx = df.close.length - 1;
      const hist = df.macdhist[lastIdx];
      const prevHist = df.macdhist[lastIdx - 1];

      return {
        ...df,
        exitLong: hist < 0 && prevHist >= 0 ? 1 : 0,
        exitShort: hist > 0 && prevHist <= 0 ? 1 : 0,
      };
    },
  };
}

// ============================================
// 工具函数
// ============================================

function calculateEMA(prices: number[], period: number): number[] {
  const k = 2 / (period + 1);
  const ema: number[] = [];

  for (let i = 0; i < prices.length; i++) {
    if (i === 0) {
      ema.push(prices[i]);
    } else if (i < period) {
      // 简单平均作为初始值
      const sum = prices.slice(0, i + 1).reduce((a, b) => a + b, 0);
      ema.push(sum / (i + 1));
    } else {
      ema.push(prices[i] * k + ema[i - 1] * (1 - k));
    }
  }

  return ema;
}
