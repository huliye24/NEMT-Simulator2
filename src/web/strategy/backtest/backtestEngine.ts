/**
 * Copyright 2026 NEMT Lab
 *
 * NEMT Backtest Engine
 * 借鉴 freqtrade backtesting.py
 *
 * 功能：
 * - 历史数据回测
 * - 订单执行模拟
 * - 绩效计算
 * - 交易记录
 */

import type {
  IStrategy,
  DataProvider,
  Trade,
  Order,
  StrategyMetadata,
} from '../interfaces/IStrategy';
import type { DataFrame, KlineData } from '../types/kline';

// ============================================
// 配置
// ============================================

export interface BacktestConfig {
  /** 初始资金 */
  initialCapital: number;
  /** 手续费率 (如 0.001 表示 0.1%) */
  commissionRate: number;
  /** 滑点 (如 0.0005 表示 0.05%) */
  slippage: number;
  /** 回测开始时间 */
  startDate: number;
  /** 回测结束时间 */
  endDate: number;
  /** 交易对 */
  pair: string;
  /** 时间周期 */
  timeframe: string;
}

// ============================================
// 结果类型
// ============================================

export interface BacktestTrade {
  /** 交易 ID */
  id: string;
  /** 开仓时间 */
  entryTime: number;
  /** 平仓时间 */
  exitTime: number;
  /** 持仓时长 (分钟) */
  duration: number;
  /** 方向 */
  direction: 'long' | 'short';
  /** 入场价格 */
  entryPrice: number;
  /** 出场价格 */
  exitPrice: number;
  /** 数量 */
  amount: number;
  /** 盈亏 */
  pnl: number;
  /** 盈亏 (%) */
  pnlPercent: number;
  /** 手续费 */
  commission: number;
  /** 滑点成本 */
  slippageCost: number;
  /** 出场原因 */
  exitReason: string;
  /** 入场信号标签 */
  entryTag?: string;
}

export interface BacktestMetrics {
  /** 总收益率 (%) */
  totalReturn: number;
  /** 年化收益率 (%) */
  annualizedReturn: number;
  /** 夏普比率 */
  sharpeRatio: number;
  /** 索提诺比率 */
  sortinoRatio: number;
  /** 最大回撤 (%) */
  maxDrawdown: number;
  /** 最大回撤持续时间 */
  maxDrawdownDuration: number;
  /** 总交易次数 */
  totalTrades: number;
  /** 盈利交易次数 */
  winningTrades: number;
  /** 亏损交易次数 */
  losingTrades: number;
  /** 胜率 (%) */
  winRate: number;
  /** 平均盈利 */
  avgWin: number;
  /** 平均亏损 */
  avgLoss: number;
  /** 盈亏比 */
  profitFactor: number;
  /** 盈利因子 */
  totalWin: number;
  /** 亏损总额 */
  totalLoss: number;
  /** 交易天数 */
  tradingDays: number;
}

export interface BacktestResult {
  /** 配置 */
  config: BacktestConfig;
  /** 指标 */
  metrics: BacktestMetrics;
  /** 交易记录 */
  trades: BacktestTrade[];
  /** 权益曲线 */
  equityCurve: { time: number; value: number }[];
  /** 回撤曲线 */
  drawdownCurve: { time: number; value: number }[];
  /** 运行时间 (ms) */
  runtime: number;
}

// ============================================
// 回测引擎
// ============================================

export class BacktestEngine {
  private config: BacktestConfig;
  private strategy: IStrategy;
  private dataProvider: DataProvider;
  private dataframe: DataFrame;
  private trades: BacktestTrade[] = [];
  private equityCurve: { time: number; value: number }[] = [];
  private drawdownCurve: { time: number; value: number }[] = [];

  // 状态
  private capital: number;
  private peakCapital: number;
  private maxDrawdown: number;
  private maxDrawdownDuration: number;
  private currentDrawdownDuration: number;
  private inPosition: boolean;
  private currentTrade: {
    direction: 'long' | 'short';
    entryPrice: number;
    entryTime: number;
    amount: number;
    stoploss: number;
    takeprofit: number;
    entryTag?: string;
  } | null = null;

  constructor(
    config: BacktestConfig,
    strategy: IStrategy,
    dataframe: DataFrame,
    dataProvider: DataProvider
  ) {
    this.config = config;
    this.strategy = strategy;
    this.dataframe = dataframe;
    this.dataProvider = dataProvider;
    this.capital = config.initialCapital;
    this.peakCapital = config.initialCapital;
    this.maxDrawdown = 0;
    this.maxDrawdownDuration = 0;
    this.currentDrawdownDuration = 0;
    this.inPosition = false;
  }

  /**
   * 运行回测
   */
  async run(): Promise<BacktestResult> {
    const startTime = performance.now();

    console.log(`[Backtest] Starting backtest...`);
    console.log(`[Backtest] Period: ${new Date(this.config.startDate)} - ${new Date(this.config.endDate)}`);
    console.log(`[Backtest] Initial Capital: ${this.config.initialCapital}`);

    const startIndex = this.strategy.config.startupCandleCount;
    const df = this.dataframe;

    // 逐 K 线回测
    for (let i = startIndex; i < df.close.length; i++) {
      const kline = this.extractKline(df, i);
      const metadata: StrategyMetadata = { pair: this.config.pair };

      // 计算指标 (如果需要)
      if (i === startIndex) {
        df.indicators = {};
        df.indicators = this.strategy.populateIndicators(df, metadata);
      }

      // 检查入场
      if (!this.inPosition) {
        const entrySignal = this.checkEntry(df, i);
        if (entrySignal) {
          this.executeEntry(kline, entrySignal);
        }
      } else {
        // 检查出场
        const exitSignal = this.checkExit(df, i);
        if (exitSignal) {
          this.executeExit(kline, exitSignal);
        }
      }

      // 更新权益曲线
      this.updateEquityCurve(kline.time);
    }

    // 平仓未结束的交易
    if (this.inPosition && this.currentTrade) {
      const lastKline = this.extractKline(df, df.close.length - 1);
      this.executeExit(lastKline, { reason: 'end_of_backtest' });
    }

    const runtime = performance.now() - startTime;
    console.log(`[Backtest] Completed in ${runtime.toFixed(2)}ms`);
    console.log(`[Backtest] Total Trades: ${this.trades.length}`);

    return {
      config: this.config,
      metrics: this.calculateMetrics(),
      trades: this.trades,
      equityCurve: this.equityCurve,
      drawdownCurve: this.drawdownCurve,
      runtime,
    };
  }

  /**
   * 提取 K 线数据
   */
  private extractKline(df: DataFrame, index: number): KlineData {
    return {
      time: df.time[index],
      open: df.open[index],
      high: df.high[index],
      low: df.low[index],
      close: df.close[index],
      volume: df.volume[index],
    };
  }

  /**
   * 检查入场信号
   */
  private checkEntry(
    df: DataFrame,
    index: number,
    entrySignal: 'enter_long' | 'enter_short' | 0 = 0
  ): { direction: 'long' | 'short'; tag?: string } | null {
    const signal = df.enterLong?.[index] || df.enterShort?.[index] || 0;

    if (signal === 1) {
      if (df.enterLong?.[index] === 1) {
        return { direction: 'long', tag: df.enterTag?.[index] };
      }
      if (df.enterShort?.[index] === 1) {
        return { direction: 'short', tag: df.enterTag?.[index] };
      }
    }

    // 检查 maxOpenTrades
    const openTrades = this.trades.filter((t) => !t.exitTime);
    if (openTrades.length >= this.strategy.config.maxOpenTrades) {
      return null;
    }

    return null;
  }

  /**
   * 检查出场信号
   */
  private checkExit(
    df: DataFrame,
    index: number
  ): { reason: string; exitSignal?: 'exit_long' | 'exit_short' } | null {
    if (!this.currentTrade) return null;

    const { entryPrice, direction, stoploss, takeprofit } = this.currentTrade;
    const kline = this.extractKline(df, index);
    const currentPrice = kline.close;

    // 1. 止损检查
    if (direction === 'long' && currentPrice <= stoploss) {
      return { reason: 'stop_loss' };
    }
    if (direction === 'short' && currentPrice >= stoploss) {
      return { reason: 'stop_loss' };
    }

    // 2. 止盈检查
    if (direction === 'long' && currentPrice >= takeprofit) {
      return { reason: 'roi' };
    }
    if (direction === 'short' && currentPrice <= takeprofit) {
      return { reason: 'roi' };
    }

    // 3. 退出信号
    if (this.strategy.config.useExitSignal) {
      const exitSignal =
        direction === 'long' ? df.exitLong?.[index] : df.exitShort?.[index];
      if (exitSignal === 1) {
        return { reason: 'exit_signal', exitSignal };
      }
    }

    return null;
  }

  /**
   * 执行入场
   */
  private executeEntry(
    kline: KlineData,
    signal: { direction: 'long' | 'short'; tag?: string }
  ): void {
    const { direction } = signal;
    const price = kline.close * (1 + this.config.slippage);

    // 计算仓位
    const positionValue = this.capital * (1 / this.strategy.config.maxOpenTrades);
    const amount = positionValue / price;

    // 计算止损止盈
    const stoplossPercent = Math.abs(this.strategy.config.stoploss);
    const stoploss =
      direction === 'long'
        ? price * (1 - stoplossPercent)
        : price * (1 + stoplossPercent);

    const minimalRoi = this.strategy.config.minimalRoi;
    const maxRoi = Math.max(...Object.values(minimalRoi));
    const takeprofit =
      direction === 'long'
        ? price * (1 + maxRoi)
        : price * (1 - maxRoi);

    this.currentTrade = {
      direction,
      entryPrice: price,
      entryTime: kline.time,
      amount,
      stoploss,
      takeprofit,
      entryTag: signal.tag,
    };

    this.inPosition = true;

    console.log(
      `[Backtest] Entry ${direction.toUpperCase()} @ ${price.toFixed(2)}, amount: ${amount.toFixed(4)}`
    );
  }

  /**
   * 执行出场
   */
  private executeExit(kline: KlineData, exit: { reason: string }): void {
    if (!this.currentTrade) return;

    const { direction, entryPrice, entryTime, amount, entryTag } = this.currentTrade;
    const exitPrice = kline.close * (1 - this.config.slippage);

    // 计算盈亏
    const pnl =
      direction === 'long'
        ? (exitPrice - entryPrice) * amount
        : (entryPrice - exitPrice) * amount;

    const pnlPercent =
      direction === 'long'
        ? (exitPrice - entryPrice) / entryPrice
        : (entryPrice - exitPrice) / entryPrice;

    // 计算手续费
    const entryCommission = entryPrice * amount * this.config.commissionRate;
    const exitCommission = exitPrice * amount * this.config.commissionRate;
    const totalCommission = entryCommission + exitCommission;

    // 计算滑点成本
    const slippageCost =
      kline.close * amount * this.config.slippage * 2;

    // 更新资金
    this.capital += pnl - totalCommission;

    // 记录交易
    const trade: BacktestTrade = {
      id: `trade_${this.trades.length + 1}`,
      entryTime,
      exitTime: kline.time,
      duration: Math.round((kline.time - entryTime) / 60000),
      direction,
      entryPrice,
      exitPrice,
      amount,
      pnl: pnl - totalCommission,
      pnlPercent: pnlPercent * 100,
      commission: totalCommission,
      slippageCost,
      exitReason: exit.reason,
      entryTag,
    };

    this.trades.push(trade);

    console.log(
      `[Backtest] Exit ${direction.toUpperCase()} @ ${exitPrice.toFixed(2)}, PnL: ${pnl.toFixed(2)}, Reason: ${exit.reason}`
    );

    // 重置状态
    this.currentTrade = null;
    this.inPosition = false;
  }

  /**
   * 更新权益曲线
   */
  private updateEquityCurve(time: number): void {
    let currentValue = this.capital;

    if (this.currentTrade) {
      const unrealizedPnL =
        this.currentTrade.direction === 'long'
          ? (this.currentTrade.entryPrice - this.currentTrade.entryPrice) * this.currentTrade.amount
          : (this.currentTrade.entryPrice - this.currentTrade.entryPrice) * this.currentTrade.amount;
      currentValue += 0; // 简化，实际应计算当前市值
    }

    this.equityCurve.push({ time, value: currentValue });

    // 更新峰值
    if (currentValue > this.peakCapital) {
      this.peakCapital = currentValue;
      this.currentDrawdownDuration = 0;
    } else {
      this.currentDrawdownDuration++;
    }

    // 更新最大回撤
    const drawdown = (this.peakCapital - currentValue) / this.peakCapital;
    if (drawdown > this.maxDrawdown) {
      this.maxDrawdown = drawdown;
    }
    if (this.currentDrawdownDuration > this.maxDrawdownDuration) {
      this.maxDrawdownDuration = this.currentDrawdownDuration;
    }

    this.drawdownCurve.push({ time, value: drawdown });
  }

  /**
   * 计算绩效指标
   */
  private calculateMetrics(): BacktestMetrics {
    const trades = this.trades;
    const winningTrades = trades.filter((t) => t.pnl > 0);
    const losingTrades = trades.filter((t) => t.pnl <= 0);

    const totalWin = winningTrades.reduce((sum, t) => sum + t.pnl, 0);
    const totalLoss = Math.abs(losingTrades.reduce((sum, t) => sum + t.pnl, 0));

    const totalReturn =
      ((this.capital - this.config.initialCapital) / this.config.initialCapital) * 100;

    // 年化收益
    const tradingDays = trades.length > 0
      ? Math.max(...trades.map((t) => t.exitTime)) / 86400000
      : 1;
    const years = tradingDays / 365;
    const annualizedReturn = (Math.pow(this.capital / this.config.initialCapital, 1 / years) - 1) * 100;

    // 夏普比率
    const dailyReturns = this.equityCurve.length > 1
      ? this.calculateDailyReturns()
      : [0];
    const avgReturn = dailyReturns.reduce((a, b) => a + b, 0) / dailyReturns.length;
    const stdReturn = this.stdDeviation(dailyReturns);
    const sharpeRatio = stdReturn > 0 ? (avgReturn / stdReturn) * Math.sqrt(252) : 0;

    // 索提诺比率
    const negativeReturns = dailyReturns.filter((r) => r < 0);
    const stdDownside = negativeReturns.length > 0
      ? this.stdDeviation(negativeReturns)
      : 1;
    const sortinoRatio = stdDownside > 0 ? (avgReturn / stdDownside) * Math.sqrt(252) : 0;

    return {
      totalReturn,
      annualizedReturn,
      sharpeRatio,
      sortinoRatio,
      maxDrawdown: this.maxDrawdown * 100,
      maxDrawdownDuration: this.maxDrawdownDuration,
      totalTrades: trades.length,
      winningTrades: winningTrades.length,
      losingTrades: losingTrades.length,
      winRate: trades.length > 0 ? (winningTrades.length / trades.length) * 100 : 0,
      avgWin: winningTrades.length > 0 ? totalWin / winningTrades.length : 0,
      avgLoss: losingTrades.length > 0 ? totalLoss / losingTrades.length : 0,
      profitFactor: totalLoss > 0 ? totalWin / totalLoss : totalWin > 0 ? Infinity : 0,
      totalWin,
      totalLoss,
      tradingDays: Math.round(tradingDays),
    };
  }

  /**
   * 计算日收益率
   */
  private calculateDailyReturns(): number[] {
    const returns: number[] = [];
    for (let i = 1; i < this.equityCurve.length; i++) {
      const dailyReturn =
        (this.equityCurve[i].value - this.equityCurve[i - 1].value) /
        this.equityCurve[i - 1].value;
      returns.push(dailyReturn);
    }
    return returns;
  }

  /**
   * 计算标准差
   */
  private stdDeviation(values: number[]): number {
    if (values.length === 0) return 0;
    const mean = values.reduce((a, b) => a + b, 0) / values.length;
    const squaredDiffs = values.map((v) => Math.pow(v - mean, 2));
    return Math.sqrt(squaredDiffs.reduce((a, b) => a + b, 0) / values.length);
  }
}

// ============================================
// 便捷函数
// ============================================

/**
 * 运行回测
 */
export async function runBacktest(
  config: BacktestConfig,
  strategy: IStrategy,
  dataframe: DataFrame,
  dataProvider: DataProvider
): Promise<BacktestResult> {
  const engine = new BacktestEngine(config, strategy, dataframe, dataProvider);
  return engine.run();
}

/**
 * 打印回测结果
 */
export function printBacktestResult(result: BacktestResult): void {
  const { metrics } = result;

  console.log('\n=== Backtest Results ===');
  console.log(`Total Return:     ${metrics.totalReturn.toFixed(2)}%`);
  console.log(`Annualized:       ${metrics.annualizedReturn.toFixed(2)}%`);
  console.log(`Sharpe Ratio:     ${metrics.sharpeRatio.toFixed(2)}`);
  console.log(`Sortino Ratio:    ${metrics.sortinoRatio.toFixed(2)}`);
  console.log(`Max Drawdown:     ${metrics.maxDrawdown.toFixed(2)}%`);
  console.log(`Total Trades:     ${metrics.totalTrades}`);
  console.log(`Win Rate:         ${metrics.winRate.toFixed(2)}%`);
  console.log(`Profit Factor:    ${metrics.profitFactor.toFixed(2)}`);
  console.log(`Avg Win:          ${metrics.avgWin.toFixed(2)}`);
  console.log(`Avg Loss:         ${metrics.avgLoss.toFixed(2)}`);
  console.log('========================\n');
}
