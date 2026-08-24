/**
 * Copyright 2026 NEMT Lab
 *
 * NEMT Strategy Store Bridge
 *
 * 将策略模块 (IStrategy, BacktestEngine, Algorithm) 与现有 Store 融合
 * 遵循现有架构：stores → services → components
 */

import { useStrategyStore, useDualBufferStore } from '../stores';
import type { Strategy, StrategyMetrics } from '../stores/strategyStore';
import type { BacktestResult, BacktestConfig, BacktestSession } from '../stores/dualBufferStore';
import type {
  IStrategy,
  StrategyConfig,
  StrategyValidationResult,
} from './interfaces/IStrategy';
import { runBacktest, printBacktestResult } from './backtest/backtestEngine';
import { calculateAllIndicators, createDataFrame } from './indicators/technicalIndicators';
import type { DataFrame, KlineData } from './types/kline';
import { BinanceAdapter, BinanceDataProvider } from './exchange/binanceAdapter';
import type { BinanceAdapter } from './exchange/binanceAdapter';
import { createNEMTStrategy, createRSIStrategy, createMACDStrategy } from './templates/strategyTemplates';
import { NEMTStateCalculator } from './nemt/nemtCalculator';

// ============================================
// 策略 <-> Store 转换器
// ============================================

/**
 * 将 Store Strategy 转换为 IStrategy
 */
export function strategyStoreToIStrategy(strategy: Strategy, config?: Partial<StrategyConfig>): IStrategy {
  const strategyConfig: StrategyConfig = {
    id: strategy.id,
    name: strategy.name,
    author: strategy.author,
    version: strategy.version,
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
    config: strategyConfig,
    populateIndicators: (df) => df,
    populateEntryTrend: (df) => df,
    populateExitTrend: (df) => df,
  };
}

/**
 * 将 IStrategy 转换为 Store Strategy
 */
export function iStrategyToStrategyStore(strategy: IStrategy): Omit<Strategy, 'id' | 'createdAt' | 'updatedAt'> {
  return {
    name: strategy.config.name,
    author: strategy.config.author,
    description: `Strategy v${strategy.config.version}`,
    version: strategy.config.version,
    status: 'draft',
    metrics: {
      totalTrades: 0,
      winRate: 0,
      totalPnL: 0,
      sharpeRatio: 0,
    },
    tags: [],
  };
}

// ============================================
// 回测结果转换
// ============================================

/**
 * 将策略模块 BacktestResult 转换为 Store BacktestResult
 */
export function backtestResultToStore(backtestResult: any): BacktestResult {
  return {
    strategyId: backtestResult.config?.pair || 'unknown',
    strategyName: backtestResult.config?.pair || 'Unknown',
    startDate: new Date(backtestResult.config?.startDate || 0).toISOString(),
    endDate: new Date(backtestResult.config?.endDate || 0).toISOString(),
    totalBars: backtestResult.trades?.length || 0,
    totalReturn: backtestResult.metrics?.totalReturn || 0,
    annualizedReturn: backtestResult.metrics?.annualizedReturn || 0,
    sharpeRatio: backtestResult.metrics?.sharpeRatio || 0,
    sortinoRatio: backtestResult.metrics?.sortinoRatio || 0,
    maxDrawdown: backtestResult.metrics?.maxDrawdown || 0,
    maxDrawdownDuration: backtestResult.metrics?.maxDrawdownDuration || 0,
    volatility: 0,
    totalTrades: backtestResult.metrics?.totalTrades || 0,
    winningTrades: backtestResult.metrics?.winningTrades || 0,
    losingTrades: backtestResult.metrics?.losingTrades || 0,
    winRate: backtestResult.metrics?.winRate || 0,
    avgWin: backtestResult.metrics?.avgWin || 0,
    avgLoss: backtestResult.metrics?.avgLoss || 0,
    profitFactor: backtestResult.metrics?.profitFactor || 0,
    trades: (backtestResult.trades || []).map((t: any, i: number) => ({
      id: t.id || `trade_${i}`,
      entryTime: t.entryTime || 0,
      exitTime: t.exitTime || 0,
      type: t.direction === 'long' ? 'LONG' : 'SHORT',
      entryPrice: t.entryPrice || 0,
      exitPrice: t.exitPrice || 0,
      size: t.amount || 0,
      pnl: t.pnl || 0,
      pnlPercent: t.pnlPercent || 0,
      stopLoss: t.stoploss || 0,
      takeProfit: t.takeprofit || 0,
      reason: t.exitReason || 'unknown',
    })),
    klines: backtestResult.equityCurve || [],
    equityCurve: backtestResult.equityCurve || [],
  };
}

// ============================================
// 策略回测服务
// ============================================

export class NEMTStrategyRunner {
  private exchange: BinanceAdapter;
  private dataProvider: BinanceDataProvider;
  private nemtCalculator: NEMTStateCalculator;

  constructor() {
    this.exchange = new BinanceAdapter({ testnet: true });
    this.dataProvider = new BinanceDataProvider({ testnet: true });
    this.nemtCalculator = new NEMTStateCalculator();
  }

  /**
   * 运行策略回测
   */
  async runBacktest(
    strategy: IStrategy,
    symbol: string,
    interval: string,
    startDate: number,
    endDate: number,
    initialCapital: number = 10000
  ): Promise<BacktestResult> {
    // 1. 获取历史数据
    const klines = await this.exchange.getKlines(symbol, interval, 1000, startDate, endDate);
    const dataframe = createDataFrame(klines);

    // 2. 计算技术指标
    const indicators = calculateAllIndicators(
      dataframe.high,
      dataframe.low,
      dataframe.close,
      dataframe.volume
    );

    // 将指标添加到 DataFrame
    dataframe.indicators = indicators;
    dataframe.rsi = indicators.rsi;
    dataframe.macd = indicators.macd.macd;
    dataframe.macdsignal = indicators.macd.signal;
    dataframe.macdhist = indicators.macd.histogram;

    // 3. 计算 NEMT 状态
    const nemtStates = this.nemtCalculator.calculateBatch(dataframe.close);
    dataframe.psi = nemtStates.map(s => s.psi);
    dataframe.phi = nemtStates.map(s => s.phi);
    dataframe.entropy = nemtStates.map(s => s.entropy);
    dataframe.nemtPhase = nemtStates.map(s => s.phase);

    // 4. 生成信号
    const metadata = { pair: symbol };
    const dfWithIndicators = strategy.populateIndicators(dataframe, metadata);
    const dfWithEntry = strategy.populateEntryTrend(dfWithIndicators, metadata);
    const dfWithExit = strategy.populateExitTrend(dfWithEntry, metadata);

    // 5. 运行回测
    const config = {
      initialCapital,
      commissionRate: 0.001,
      slippage: 0.0005,
      startDate,
      endDate,
      pair: symbol,
      timeframe: interval,
    };

    const result = await runBacktest(config, strategy, dfWithExit, this.dataProvider);

    // 6. 转换并返回
    return backtestResultToStore(result);
  }

  /**
   * 创建 NEMT 策略
   */
  createStrategy(
    name: string,
    type: 'nemt' | 'rsi' | 'macd' = 'nemt',
    options?: any
  ): IStrategy {
    switch (type) {
      case 'rsi':
        return createRSIStrategy(name, options);
      case 'macd':
        return createMACDStrategy(name, options);
      case 'nemt':
      default:
        return createNEMTStrategy(name, options);
    }
  }
}

// ============================================
// Store 集成钩子
// ============================================

/**
 * 使用策略运行器
 */
let strategyRunner: NEMTStrategyRunner | null = null;

export function getStrategyRunner(): NEMTStrategyRunner {
  if (!strategyRunner) {
    strategyRunner = new NEMTStrategyRunner();
  }
  return strategyRunner;
}

/**
 * 运行回测并更新 Store
 */
export async function runStrategyBacktest(
  strategyId: string,
  symbol: string,
  interval: string,
  startDate: number,
  endDate: number
): Promise<BacktestResult | null> {
  const dualBufferStore = useDualBufferStore.getState();
  const strategyStore = useStrategyStore.getState();

  // 获取策略
  const strategy = strategyStore.strategies.find(s => s.id === strategyId);
  if (!strategy) {
    console.error(`[StrategyRunner] Strategy not found: ${strategyId}`);
    return null;
  }

  // 创建 IStrategy
  const iStrategy = strategyStoreToIStrategy(strategy);

  // 获取配置
  const config = dualBufferStore.backtestConfig;

  try {
    // 运行回测
    const runner = getStrategyRunner();
    const result = await runner.runBacktest(
      iStrategy,
      symbol,
      interval,
      startDate,
      endDate,
      config.initialCapital
    );

    // 审核结果
    const isApproved = validateBacktestResult(result);

    if (isApproved) {
      dualBufferStore.approveBacktest(strategyId, result);
    } else {
      dualBufferStore.rejectBacktest(strategyId);
    }

    return result;
  } catch (error) {
    console.error('[StrategyRunner] Backtest failed:', error);
    return null;
  }
}

/**
 * 验证回测结果
 */
export function validateBacktestResult(result: BacktestResult): boolean {
  const checks = [
    { name: '胜率 >= 50%', pass: result.winRate >= 50 },
    { name: '夏普比率 >= 1.5', pass: result.sharpeRatio >= 1.5 },
    { name: '最大回撤 <= 20%', pass: result.maxDrawdown <= 20 },
    { name: '盈亏比 >= 1.2', pass: result.profitFactor >= 1.2 },
    { name: '交易次数 >= 10', pass: result.totalTrades >= 10 },
  ];

  console.log('[StrategyRunner] Validation:');
  for (const check of checks) {
    console.log(`  ${check.pass ? '✓' : '✗'} ${check.name}`);
  }

  // 至少 3 个检查通过
  const passedCount = checks.filter(c => c.pass).length;
  return passedCount >= 3;
}

// ============================================
// 策略创建便捷函数
// ============================================

/**
 * 创建 NEMT 策略
 */
export function createNEMTTradingStrategy(
  name: string,
  options?: {
    timeframe?: string;
    nemtConfig?: any;
    riskConfig?: any;
  }
): IStrategy {
  return createNEMTStrategy(name, {
    timeframe: options?.timeframe || '1h',
    maxOpenTrades: options?.riskConfig?.maxOpenTrades || 3,
    stoploss: options?.riskConfig?.stoploss || -0.05,
    trailingStop: true,
    trailingStopPositive: 0.02,
    ...options,
  });
}

/**
 * 创建 RSI 策略
 */
export function createRSITradingStrategy(
  name: string,
  options?: {
    buyRsiThreshold?: number;
    sellRsiThreshold?: number;
    stoploss?: number;
  }
): IStrategy {
  return createRSIStrategy(name, {
    buyRsiThreshold: options?.buyRsiThreshold || 30,
    sellRsiThreshold: options?.sellRsiThreshold || 70,
    stoploss: options?.stoploss || -0.1,
  });
}

/**
 * 创建 MACD 策略
 */
export function createMACDTradingStrategy(
  name: string,
  options?: {
    fastPeriod?: number;
    slowPeriod?: number;
    stoploss?: number;
  }
): IStrategy {
  return createMACDStrategy(name, {
    fastPeriod: options?.fastPeriod || 12,
    slowPeriod: options?.slowPeriod || 26,
    stoploss: options?.stoploss || -0.1,
  });
}
