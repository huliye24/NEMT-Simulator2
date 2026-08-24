/**
 * Copyright 2026 NEMT Lab
 *
 * NEMT Strategy Module - Integration Guide
 *
 * 本模块整合了:
 * - freqtrade: 回测引擎、策略接口、交易执行
 * - QuantConnect Lean: 事件驱动算法、参数优化
 * - NEMT: 非平衡态市场理论
 *
 * 使用方式:
 * 1. 直接使用策略模块 (独立运行)
 * 2. 通过 Store 集成 (与 NEMT 前端融合)
 */

import {
  // === 核心接口 ===
  IStrategy,
  NEMTStrategy,

  // === 策略模板 ===
  createNEMTStrategy,
  createRSIStrategy,
  createMACDStrategy,

  // === 技术指标 ===
  calculateRSI,
  calculateMACD,
  calculateBollingerBands,
  calculateATR,
  calculateAllIndicators,

  // === 回测引擎 ===
  BacktestEngine,
  runBacktest,
  printBacktestResult,

  // === 算法 (Lean) ===
  QCAlgorithm,
  AlgorithmManager,

  // === 优化器 ===
  optimizeStrategy,
  GridSearchOptimizer,

  // === NEMT 计算器 ===
  NEMTStateCalculator,
  calculateNEMTState,
  getNEMTSignal,

  // === Store 桥接 ===
  strategyStoreToIStrategy,
  iStrategyToStrategyStore,
  backtestResultToStore,
  NEMTStrategyRunner,
  runStrategyBacktest,
  validateBacktestResult,
  createNEMTTradingStrategy,
  createRSITradingStrategy,
  createMACDTradingStrategy,

  // === 交易所适配器 ===
  BinanceAdapter,
  BinanceDataProvider,

  // === 类型 ===
  type DataFrame,
  type KlineData,
} from '../index';

// ============================================
// 示例 1: 快速创建并运行策略
// ============================================

export async function example1_QuickStart() {
  // 创建 NEMT 策略
  const strategy = createNEMTTradingStrategy('My NEMT Strategy', {
    timeframe: '1h',
    nemtConfig: {
      nemtCriticalPsi: 0.5,
      nemtCriticalEntropy: 0.7,
    },
    riskConfig: {
      maxOpenTrades: 3,
      stoploss: -0.05,
    },
  });

  // 创建运行器
  const runner = new NEMTStrategyRunner();

  // 运行回测
  const result = await runner.runBacktest(
    strategy,
    'BTCUSDT',
    '1h',
    Date.now() - 30 * 24 * 60 * 60 * 1000, // 30 天前
    Date.now(),
    10000
  );

  console.log('Backtest Result:', result);
}

// ============================================
// 示例 2: 使用 Store 集成
// ============================================

export async function example2_StoreIntegration() {
  // 通过 Store 运行回测
  const result = await runStrategyBacktest(
    'strategy-1', // 策略 ID
    'BTCUSDT',
    '1h',
    Date.now() - 30 * 24 * 60 * 60 * 1000,
    Date.now()
  );

  if (result) {
    console.log('Backtest completed:', result);

    // 验证结果
    const isValid = validateBacktestResult(result);
    console.log('Validation:', isValid ? 'PASSED' : 'FAILED');
  }
}

// ============================================
// 示例 3: 事件驱动算法 (Lean 风格)
// ============================================

export function example3_EventDrivenAlgorithm() {
  class MyAlgorithm extends QCAlgorithm {
    name = 'MyAlgorithm';
    private symbols = ['BTCUSDT', 'ETHUSDT'];

    Initialize(): void {
      this.SetStartDate(2025, 1, 1);
      this.SetCash(10000);

      for (const symbol of this.symbols) {
        this.AddCrypto(symbol, '1h');
      }

      console.log(`[${this.name}] Initialized with ${this.symbols.join(', ')}`);
    }

    OnData(slice: any): void {
      for (const symbol of this.symbols) {
        const history = this.History(symbol, 20);
        if (history.length < 20) continue;

        const currentPrice = this.CurrentPrice(symbol);
        const oldPrice = history[0].close;
        const momentum = (currentPrice - oldPrice) / oldPrice;

        if (momentum > 0.02) {
          this.SetHoldings(symbol, 0.1);
        } else if (momentum < -0.02) {
          this.Liquidate(symbol);
        }
      }
    }

    OnEndOfDay(symbol?: string): void {
      console.log(`[${this.name}] Portfolio: ${this.account.portfolioValue.toFixed(2)}`);
    }
  }

  // 运行算法
  const algo = new MyAlgorithm();
  const manager = new AlgorithmManager(algo);
  manager.Initialize();
  manager.Start();
}

// ============================================
// 示例 4: 参数优化
// ============================================

export async function example4_ParameterOptimization() {
  const strategy = createRSITradingStrategy('RSI Optimization');

  // 定义参数空间
  const parameterSpaces = [
    { name: 'buyRsiThreshold', min: 20, max: 40, step: 5 },
    { name: 'sellRsiThreshold', min: 60, max: 80, step: 5 },
  ];

  // 定义优化目标
  const target = {
    objective: 'sharpe_ratio' as const,
    constraint: {
      objective: 'max_drawdown' as const,
      operator: '<=' as const,
      value: 20,
    },
  };

  // 回测函数
  const runBacktestFn = async (params: Record<string, number>) => {
    const runner = new NEMTStrategyRunner();
    const strategyWithParams = createRSIStrategy('RSI Strategy', {
      buyRsiThreshold: params.buyRsiThreshold,
      sellRsiThreshold: params.sellRsiThreshold,
    });

    return runner.runBacktest(
      strategyWithParams,
      'BTCUSDT',
      '1h',
      Date.now() - 90 * 24 * 60 * 60 * 1000,
      Date.now(),
      10000
    );
  };

  // 运行优化
  const result = await optimizeStrategy(
    strategy,
    parameterSpaces,
    target,
    runBacktestFn,
    { mode: 'grid', maxRuns: 100 }
  );

  console.log('Best params:', result.bestParams);
  console.log('Best metrics:', result.bestMetrics);
}

// ============================================
// 示例 5: NEMT 状态计算
// ============================================

export function example5_NEMTCalculation() {
  // 模拟价格数据
  const prices = [100, 102, 101, 103, 105, 104, 106, 108, 107, 109, 110, 108, 111, 113, 112, 114];

  // 计算 NEMT 状态
  const state = calculateNEMTState(prices);

  console.log('NEMT State:', {
    psi: state.psi.toFixed(4),
    phi: state.phi.toFixed(4),
    entropy: state.entropy.toFixed(4),
    phase: state.phase,
  });

  // 获取交易信号
  const { signal, confidence } = getNEMTSignal(prices);
  console.log('Signal:', signal, 'Confidence:', (confidence * 100).toFixed(1) + '%');
}

// ============================================
// 示例 6: 使用 Binance 适配器
// ============================================

export async function example6_BinanceAdapter() {
  const exchange = new BinanceAdapter({ testnet: true });

  // 获取 K线数据
  const klines = await exchange.getKlines('BTCUSDT', '1h', 100);
  console.log('Got', klines.length, 'klines');

  // 获取当前价格
  const price = await exchange.getCurrentPrice('BTCUSDT');
  console.log('BTC Price:', price);

  // 获取 24h 统计
  const ticker = await exchange.get24hrTicker('BTCUSDT');
  console.log('24h Change:', ticker.priceChangePercent.toFixed(2) + '%');

  // WebSocket 订阅
  exchange.connectWebSocket((data) => {
    if (data.e === '24hrTicker') {
      console.log('Price update:', data.c);
    }
  });
}

// ============================================
// 导出所有示例
// ============================================

export const examples = {
  quickStart: example1_QuickStart,
  storeIntegration: example2_StoreIntegration,
  eventDrivenAlgorithm: example3_EventDrivenAlgorithm,
  parameterOptimization: example4_ParameterOptimization,
  nemtCalculation: example5_NEMTCalculation,
  binanceAdapter: example6_BinanceAdapter,
};
