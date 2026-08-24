/**
 * Copyright 2026 NEMT Lab
 *
 * NEMT Strategy Module - Store Integration
 *
 * 将策略模块与现有 NEMT Store 融合
 * 现有: strategyStore, dualBufferStore, binanceStore
 * 新增: strategy module (freqtrade + Lean)
 */

import { useStrategyStore, useDualBufferStore, useBinanceStore } from '../../stores';
import type { Strategy, StrategyMetrics } from '../stores/strategyStore';
import type { BacktestResult, BacktestConfig } from '../stores/dualBufferStore';
import type { KlineData } from '../stores/dualBufferStore';
import type { BinanceState } from '../stores/binanceStore';
// Import directly from source files instead of circular ./index
import type {
  IStrategy,
  NEMTStrategy,
  StrategyConfig,
} from '../interfaces/IStrategy';
import { BacktestEngineCore as BacktestEngine } from '../backtest/engineCore';
import { runBacktest } from '../backtest/engineCore';
import { BinanceAdapter, BinanceDataProvider } from '../exchange/binanceAdapter';
import { NEMTStateCalculator } from '../nemt/nemtCalculator';
import { createNEMTStrategy, createRSIStrategy, createMACDStrategy } from '../templates/strategyTemplates';
import { calculateAllIndicators } from '../indicators/technicalIndicators';
import { createDataFrame, type DataFrame } from '../types/kline';

// ============================================
// 类型适配
// ============================================

export interface StrategyAdapter {
  /** 转换为 Store Strategy */
  toStoreStrategy(): Omit<Strategy, 'id' | 'createdAt' | 'updatedAt'>;
  /** 转换为 IStrategy */
  toIStrategy(): IStrategy;
}

export interface BacktestAdapter {
  /** 转换为 Store BacktestResult */
  toStoreResult(): BacktestResult;
}

// ============================================
// Store 集成服务
// ============================================

export class NEMTStrategyService {
  private exchange: BinanceAdapter;
  private dataProvider: BinanceDataProvider;
  private nemtCalculator: NEMTStateCalculator;

  constructor() {
    this.exchange = new BinanceAdapter({ testnet: true });
    this.dataProvider = new BinanceDataProvider({ testnet: true });
    this.nemtCalculator = new NEMTStateCalculator();
  }

  // -----------------------------------------
  // Store 集成
  // -----------------------------------------

  /**
   * 从 Store 获取策略
   */
  getStrategyFromStore(strategyId: string): IStrategy | null {
    const store = useStrategyStore.getState();
    const strategy = store.strategies.find(s => s.id === strategyId);
    if (!strategy) return null;
    return this.strategyToIStrategy(strategy);
  }

  /**
   * 将策略添加到 Store
   */
  addStrategyToStore(strategy: IStrategy): Strategy {
    const store = useStrategyStore.getState();
    const now = new Date().toISOString();

    const newStrategy: Strategy = {
      id: `strategy_${Date.now()}`,
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
      createdAt: now,
      updatedAt: now,
    };

    store.addStrategy(newStrategy);
    return newStrategy;
  }

  /**
   * 更新策略指标
   */
  updateStrategyMetrics(strategyId: string, result: BacktestResult): void {
    const store = useStrategyStore.getState();
    store.updateStrategy(strategyId, {
      metrics: {
        totalTrades: result.totalTrades,
        winRate: result.winRate,
        totalPnL: result.totalTrades > 0
          ? result.trades.reduce((sum, t) => sum + t.pnl, 0)
          : 0,
        sharpeRatio: result.sharpeRatio,
      },
      updatedAt: new Date().toISOString(),
    });
  }

  // -----------------------------------------
  // 策略转换
  // -----------------------------------------

  /**
   * Store Strategy -> IStrategy
   */
  strategyToIStrategy(strategy: Strategy): IStrategy {
    return createNEMTStrategy(strategy.name, {
      timeframe: '1h',
      maxOpenTrades: 1,
      stoploss: -0.1,
    });
  }

  /**
   * IStrategy -> Store Strategy
   */
  iStrategyToStore(strategy: IStrategy): Omit<Strategy, 'id' | 'createdAt' | 'updatedAt'> {
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

  // -----------------------------------------
  // 回测
  // -----------------------------------------

  /**
   * 运行回测 (使用 Store 数据)
   */
  async runBacktestWithStore(
    strategyId: string,
    symbol: string,
    interval: string
  ): Promise<BacktestResult | null> {
    const dualBufferStore = useDualBufferStore.getState();
    const { startDate, endDate } = dualBufferStore.backtestPeriod;
    const config = dualBufferStore.backtestConfig;

    // 获取策略
    const strategy = this.getStrategyFromStore(strategyId);
    if (!strategy) {
      console.error('[NEMTStrategyService] Strategy not found:', strategyId);
      return null;
    }

    try {
      // 获取 K线数据
      const klines = await this.exchange.getKlines(
        symbol,
        interval,
        1000,
        new Date(startDate).getTime(),
        new Date(endDate).getTime()
      );

      // 创建 DataFrame
      const dataframe = createDataFrame(klines);

      // 计算技术指标
      const indicators = calculateAllIndicators(
        dataframe.high,
        dataframe.low,
        dataframe.close,
        dataframe.volume
      );

      // 计算 NEMT 状态
      const nemtStates = this.nemtCalculator.calculateBatch(dataframe.close);

      // 添加指标到 DataFrame
      const enrichedDataframe = {
        ...dataframe,
        ...indicators,
        psi: nemtStates.map(s => s.psi),
        phi: nemtStates.map(s => s.phi),
        entropy: nemtStates.map(s => s.entropy),
        nemtPhase: nemtStates.map(s => s.phase),
      };

      // 生成信号
      const metadata = { pair: symbol };
      const dfWithEntry = strategy.populateEntryTrend(
        strategy.populateIndicators(enrichedDataframe, metadata),
        metadata
      );
      const dfWithExit = strategy.populateExitTrend(dfWithEntry, metadata);

      // 运行回测
      const result = await runBacktest(
        {
          initialCapital: config.initialCapital,
          commissionRate: 0.001,
          slippage: 0.0005,
          startDate: new Date(startDate).getTime(),
          endDate: new Date(endDate).getTime(),
          pair: symbol,
          timeframe: interval,
        },
        strategy,
        dfWithExit as DataFrame,
        this.dataProvider
      );

      // 更新 Store
      this.updateStrategyMetrics(strategyId, this.toStoreBacktestResult(result));

      return this.toStoreBacktestResult(result);
    } catch (error) {
      console.error('[NEMTStrategyService] Backtest failed:', error);
      return null;
    }
  }

  // -----------------------------------------
  // 结果转换
  // -----------------------------------------

  /**
   * 回测结果 -> Store BacktestResult
   */
  toStoreBacktestResult(result: any): BacktestResult {
    return {
      strategyId: result.config?.pair || 'unknown',
      strategyName: result.config?.pair || 'Unknown',
      startDate: new Date(result.config?.startDate || 0).toISOString(),
      endDate: new Date(result.config?.endDate || 0).toISOString(),
      totalBars: result.trades?.length || 0,
      totalReturn: result.metrics?.totalReturn || 0,
      annualizedReturn: result.metrics?.annualizedReturn || 0,
      sharpeRatio: result.metrics?.sharpeRatio || 0,
      sortinoRatio: result.metrics?.sortinoRatio || 0,
      maxDrawdown: result.metrics?.maxDrawdown || 0,
      maxDrawdownDuration: result.metrics?.maxDrawdownDuration || 0,
      volatility: 0,
      totalTrades: result.metrics?.totalTrades || 0,
      winningTrades: result.metrics?.winningTrades || 0,
      losingTrades: result.metrics?.losingTrades || 0,
      winRate: result.metrics?.winRate || 0,
      avgWin: result.metrics?.avgWin || 0,
      avgLoss: result.metrics?.avgLoss || 0,
      profitFactor: result.metrics?.profitFactor || 0,
      trades: (result.trades || []).map((t: any, i: number) => ({
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
      klines: result.equityCurve || [],
      equityCurve: result.equityCurve || [],
    };
  }

  // -----------------------------------------
  // 实时交易
  // -----------------------------------------

  /**
   * 获取实时信号 (使用 Store 数据)
   */
  getLiveSignal(symbol: string): { signal: 'BUY' | 'SELL' | 'HOLD'; confidence: number } | null {
    const binanceStore = useBinanceStore.getState();
    const klines = binanceStore.getKlines(symbol);

    if (klines.length < 20) return null;

    const closes = klines.map(k => k.close);
    const signal = this.nemtCalculator.getPhaseSignal(
      this.nemtCalculator.calculate(closes)
    );

    return signal;
  }
}

// ============================================
// 单例
// ============================================

let strategyService: NEMTStrategyService | null = null;

export function getStrategyService(): NEMTStrategyService {
  if (!strategyService) {
    strategyService = new NEMTStrategyService();
  }
  return strategyService;
}

// ============================================
// 便捷函数
// ============================================

/**
 * 运行回测
 */
export async function runBacktestWithStore(
  strategyId: string,
  symbol: string = 'BTCUSDT',
  interval: string = '1h'
): Promise<BacktestResult | null> {
  return getStrategyService().runBacktestWithStore(strategyId, symbol, interval);
}

/**
 * 获取实时信号
 */
export function getSignalFromStore(symbol: string): { signal: 'BUY' | 'SELL' | 'HOLD'; confidence: number } | null {
  return getStrategyService().getLiveSignal(symbol);
}

/**
 * 创建策略并添加到 Store
 */
export function createAndAddStrategy(
  type: 'nemt' | 'rsi' | 'macd',
  name: string,
  options?: any
): Strategy {
  const service = getStrategyService();

  let strategy: IStrategy;
  switch (type) {
    case 'rsi':
      strategy = createRSIStrategy(name, options);
      break;
    case 'macd':
      strategy = createMACDStrategy(name, options);
      break;
    case 'nemt':
    default:
      strategy = createNEMTStrategy(name, options);
  }

  return service.addStrategyToStore(strategy);
}

/**
 * 验证回测结果
 */
export function validateResult(result: BacktestResult): { passed: boolean; checks: Array<{ name: string; passed: boolean }> } {
  const checks = [
    { name: '胜率 >= 50%', passed: result.winRate >= 50 },
    { name: '夏普比率 >= 1.5', passed: result.sharpeRatio >= 1.5 },
    { name: '最大回撤 <= 20%', passed: result.maxDrawdown <= 20 },
    { name: '盈亏比 >= 1.2', passed: result.profitFactor >= 1.2 },
    { name: '交易次数 >= 10', passed: result.totalTrades >= 10 },
  ];

  return {
    passed: checks.filter(c => c.passed).length >= 3,
    checks,
  };
}
