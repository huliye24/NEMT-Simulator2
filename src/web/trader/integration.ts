/**
 * Copyright 2026 NEMT Lab
 *
 * Trader + Strategy Module Integration
 * 将 vnpy 架构与 freqtrade/Lean 策略融合
 */

import {
  MainEngine,
  EventEngine,
  DataEngine,
  TradeEngine,
  SignalEngine,
  BaseGateway,
  BinanceGateway,
  BarInfo,
  TickInfo,
} from '../trader';

import {
  IStrategy,
  BacktestEngine,
  runBacktest,
  createDataFrame,
  calculateAllIndicators,
  NEMTStateCalculator,
  BinanceAdapter,
} from '../strategy';

import type { DataFrame } from '../strategy';

// ============================================
// NEMT Strategy Engine
// ============================================

export class NEMTStrategyEngine {
  private mainEngine: MainEngine;
  private eventEngine: EventEngine;
  private strategy: IStrategy;
  private nemtCalculator: NEMTStateCalculator;
  private barCache: Map<string, BarInfo[]> = new Map();
  private symbols: Set<string> = new Set();
  private running: boolean = false;

  constructor(mainEngine: MainEngine, strategy: IStrategy) {
    this.mainEngine = mainEngine;
    this.eventEngine = mainEngine.eventEngine;
    this.strategy = strategy;
    this.nemtCalculator = new NEMTStateCalculator();
  }

  /** 初始化 */
  init(symbols: string[]): void {
    for (const symbol of symbols) {
      this.symbols.add(symbol);

      // 订阅 K 线
      this.eventEngine.register(`bar.${symbol}.BINANCE`, (event) => {
        const bar = event.data as BarInfo;
        this.onBar(bar);
      });
    }

    console.log(`[NEMTStrategyEngine] Initialized for ${symbols.join(', ')}`);
  }

  /** 启动 */
  start(): void {
    if (this.running) return;
    this.running = true;
    console.log('[NEMTStrategyEngine] Started');
  }

  /** 停止 */
  stop(): void {
    this.running = false;
    console.log('[NEMTStrategyEngine] Stopped');
  }

  /** 处理 K 线 */
  private onBar(bar: BarInfo): void {
    if (!this.running) return;

    // 缓存 K 线
    if (!this.barCache.has(bar.vtSymbol)) {
      this.barCache.set(bar.vtSymbol, []);
    }
    const bars = this.barCache.get(bar.vtSymbol)!;
    bars.push(bar);

    // 保留最近 200 根
    if (bars.length > 200) {
      bars.shift();
    }

    // 需要足够的数据
    if (bars.length < this.strategy.config.startupCandleCount) {
      return;
    }

    // 转换为 DataFrame
    const dataframe = this.barsToDataFrame(bars);

    // 计算指标
    const withIndicators = this.strategy.populateIndicators(dataframe, { pair: bar.vtSymbol });

    // 生成入场信号
    const withEntry = this.strategy.populateEntryTrend(withIndicators, { pair: bar.vtSymbol });

    // 生成出场信号
    const withExit = this.strategy.populateExitTrend(withEntry, { pair: bar.vtSymbol });

    // 获取最新信号
    const lastIdx = withExit.close.length - 1;

    if (withExit.enterLong?.[lastIdx] === 1) {
      this.onSignal('long', bar);
    } else if (withExit.enterShort?.[lastIdx] === 1) {
      this.onSignal('short', bar);
    }

    if (withExit.exitLong?.[lastIdx] === 1) {
      this.onExitSignal('long', bar);
    } else if (withExit.exitShort?.[lastIdx] === 1) {
      this.onExitSignal('short', bar);
    }
  }

  /** 信号处理 */
  private onSignal(direction: 'long' | 'short', bar: BarInfo): void {
    console.log(`[NEMTStrategyEngine] Signal: ${direction} @ ${bar.closePrice}`);

    // 发送信号事件
    this.eventEngine.publish('strategy_signal', {
      strategyId: this.strategy.config.id,
      symbol: bar.vtSymbol,
      direction,
      price: bar.closePrice,
      timestamp: bar.timestamp,
    });
  }

  /** 出场信号 */
  private onExitSignal(direction: 'long' | 'short', bar: BarInfo): void {
    console.log(`[NEMTStrategyEngine] Exit Signal: ${direction} @ ${bar.closePrice}`);

    this.eventEngine.publish('strategy_exit_signal', {
      strategyId: this.strategy.config.id,
      symbol: bar.vtSymbol,
      direction,
      price: bar.closePrice,
      timestamp: bar.timestamp,
    });
  }

  /** 转换 K 线为 DataFrame */
  private barsToDataFrame(bars: BarInfo[]): DataFrame {
    return {
      time: bars.map((b) => b.timestamp),
      open: bars.map((b) => b.openPrice),
      high: bars.map((b) => b.highPrice),
      low: bars.map((b) => b.lowPrice),
      close: bars.map((b) => b.closePrice),
      volume: bars.map((b) => b.volume),
    };
  }
}

// ============================================
// NEMT Backtest Trader
// ============================================

export class NEMTBacktestTrader {
  private strategy: IStrategy;
  private exchange: BinanceAdapter;
  private nemtCalculator: NEMTStateCalculator;

  constructor(strategy: IStrategy) {
    this.strategy = strategy;
    this.exchange = new BinanceAdapter({ testnet: true });
    this.nemtCalculator = new NEMTStateCalculator();
  }

  /** 运行回测 */
  async run(
    symbol: string,
    interval: string,
    startTime: number,
    endTime: number,
    initialCapital: number = 10000
  ): Promise<{
    metrics: {
      totalReturn: number;
      sharpeRatio: number;
      maxDrawdown: number;
      winRate: number;
      totalTrades: number;
    };
    trades: Array<{
      entryTime: number;
      exitTime: number;
      direction: string;
      entryPrice: number;
      exitPrice: number;
      pnl: number;
    }>;
  }> {
    // 获取历史数据
    const klines = await this.exchange.getKlines(symbol, interval, 1000, startTime, endTime);

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

    // 丰富 DataFrame
    const enriched = {
      ...dataframe,
      ...indicators,
      psi: nemtStates.map((s) => s.psi),
      phi: nemtStates.map((s) => s.phi),
      entropy: nemtStates.map((s) => s.entropy),
      nemtPhase: nemtStates.map((s) => s.phase),
    };

    // 生成信号
    const withIndicators = this.strategy.populateIndicators(enriched, { pair: symbol });
    const withEntry = this.strategy.populateEntryTrend(withIndicators, { pair: symbol });
    const withExit = this.strategy.populateExitTrend(withEntry, { pair: symbol });

    // 运行回测
    const result = await runBacktest(
      {
        initialCapital,
        commissionRate: 0.001,
        slippage: 0.0005,
        startDate: startTime,
        endDate: endTime,
        pair: symbol,
        timeframe: interval,
      },
      this.strategy,
      withExit as DataFrame,
      {} as any
    );

    return {
      metrics: {
        totalReturn: result.metrics.totalReturn,
        sharpeRatio: result.metrics.sharpeRatio,
        maxDrawdown: result.metrics.maxDrawdown,
        winRate: result.metrics.winRate,
        totalTrades: result.metrics.totalTrades,
      },
      trades: result.trades.map((t) => ({
        entryTime: t.entryTime,
        exitTime: t.exitTime,
        direction: t.direction,
        entryPrice: t.entryPrice,
        exitPrice: t.exitPrice,
        pnl: t.pnl,
      })),
    };
  }
}

// ============================================
// NEMT Live Trader
// ============================================

export class NEMTLiveTrader {
  private mainEngine: MainEngine;
  private gateway: BaseGateway;
  private strategy: IStrategy;
  private nemtCalculator: NEMTStateCalculator;
  private barCache: Map<string, BarInfo[]> = new Map();
  private running: boolean = false;

  constructor(mainEngine: MainEngine, gateway: BaseGateway, strategy: IStrategy) {
    this.mainEngine = mainEngine;
    this.gateway = gateway;
    this.strategy = strategy;
    this.nemtCalculator = new NEMTStateCalculator();
  }

  /** 启动实时交易 */
  async start(symbol: string): Promise<void> {
    if (this.running) return;

    // 订阅 K 线
    this.gateway.subscribe({ symbol, exchange: 'BINANCE' });

    // 注册 K 线事件
    this.mainEngine.eventEngine.register('bar', (event) => {
      const bar = event.data as BarInfo;
      if (bar.vtSymbol !== `${symbol}.BINANCE`) return;

      this.onBar(bar);
    });

    this.running = true;
    console.log(`[NEMTLiveTrader] Started for ${symbol}`);
  }

  /** 停止交易 */
  stop(): void {
    this.running = false;
    console.log('[NEMTLiveTrader] Stopped');
  }

  /** 处理 K 线 */
  private async onBar(bar: BarInfo): Promise<void> {
    if (!this.running) return;

    // 缓存 K 线
    if (!this.barCache.has(bar.vtSymbol)) {
      this.barCache.set(bar.vtSymbol, []);
    }
    const bars = this.barCache.get(bar.vtSymbol)!;
    bars.push(bar);

    if (bars.length > 200) bars.shift();

    if (bars.length < this.strategy.config.startupCandleCount) return;

    // 转换为 DataFrame
    const dataframe: DataFrame = {
      time: bars.map((b) => b.timestamp),
      open: bars.map((b) => b.openPrice),
      high: bars.map((b) => b.highPrice),
      low: bars.map((b) => b.lowPrice),
      close: bars.map((b) => b.closePrice),
      volume: bars.map((b) => b.volume),
    };

    // 计算指标
    const withIndicators = this.strategy.populateIndicators(dataframe, { pair: bar.vtSymbol });
    const withEntry = this.strategy.populateEntryTrend(withIndicators, { pair: bar.vtSymbol });

    // 获取信号
    const lastIdx = withEntry.close.length - 1;

    if (withEntry.enterLong?.[lastIdx] === 1) {
      await this.sendOrder(symbol, 'long', bar.closePrice, 0.01);
    } else if (withEntry.enterShort?.[lastIdx] === 1) {
      await this.sendOrder(symbol, 'short', bar.closePrice, 0.01);
    }
  }

  /** 发送订单 */
  private async sendOrder(
    symbol: string,
    direction: 'long' | 'short',
    price: number,
    volume: number
  ): Promise<void> {
    await this.gateway.sendOrder({
      symbol,
      exchange: 'BINANCE',
      direction,
      type: 'market',
      volume,
      price,
    });
  }
}
