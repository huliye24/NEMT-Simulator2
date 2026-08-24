/**
 * Copyright 2026 NEMT Lab
 *
 * Backtest Engine
 * 可运行的回测引擎
 *
 * 功能：
 * - 历史数据回测
 * - 订单执行模拟
 * - 绩效计算
 * - 支持多种入场/出场策略
 */

import type {
  BacktestConfig,
  BacktestResult,
  BacktestMetrics,
  Trade,
  DataFrame,
  EquityPoint,
  BacktestProgressCallback,
} from './types';

// ============================================
// 内置策略信号生成器
// ============================================

export type SignalGenerator = (df: DataFrame, index: number, trade?: Trade | null) => {
  signal: 'entry_long' | 'entry_short' | 'exit' | 'hold';
  strength: number;
  reason: string;
};

/** 均线金叉/死叉策略信号 */
export function maCrossSignal(df: DataFrame, index: number): {
  signal: 'entry_long' | 'entry_short' | 'exit' | 'hold';
  strength: number;
  reason: string;
} {
  const fast = 7;
  const slow = 25;

  if (index < slow) return { signal: 'hold', strength: 0, reason: '预热期' };

  const close = df.close;
  const smaFast = average(close.slice(index - fast + 1, index + 1));
  const smaSlow = average(close.slice(index - slow + 1, index + 1));
  const prevFast = average(close.slice(index - fast, index));
  const prevSlow = average(close.slice(index - slow, index));

  if (prevFast <= prevSlow && smaFast > smaSlow) {
    return { signal: 'entry_long', strength: 1, reason: `MA(${fast})上穿MA(${slow})` };
  }
  if (prevFast >= prevSlow && smaFast < smaSlow) {
    return { signal: 'entry_short', strength: 1, reason: `MA(${fast})下穿MA(${slow})` };
  }

  return { signal: 'hold', strength: 0, reason: '' };
}

/** RSI 超买超卖策略信号 */
export function rsiSignal(df: DataFrame, index: number): {
  signal: 'entry_long' | 'entry_short' | 'exit' | 'hold';
  strength: number;
  reason: string;
} {
  const period = 14;
  if (index < period) return { signal: 'hold', strength: 0, reason: '预热期' };

  const close = df.close;
  const rsi = calculateRSI(close, period)[index];
  if (rsi === undefined) return { signal: 'hold', strength: 0, reason: '无RSI数据' };

  if (rsi < 30) {
    return { signal: 'entry_long', strength: 1, reason: `RSI超卖(${rsi.toFixed(1)})` };
  }
  if (rsi > 70) {
    return { signal: 'entry_short', strength: 1, reason: `RSI超买(${rsi.toFixed(1)})` };
  }

  return { signal: 'hold', strength: 0, reason: '' };
}

/** 布林带策略信号 */
export function bollingerSignal(df: DataFrame, index: number): {
  signal: 'entry_long' | 'entry_short' | 'exit' | 'hold';
  strength: number;
  reason: string;
} {
  const period = 20;
  const stdDev = 2;
  if (index < period) return { signal: 'hold', strength: 0, reason: '预热期' };

  const close = df.close.slice(0, index + 1);
  const bb = calculateBollingerBands(close, period, stdDev);
  const upper = bb.upper[bb.upper.length - 1];
  const lower = bb.lower[bb.lower.length - 1];
  const middle = bb.middle[bb.middle.length - 1];
  const price = close[close.length - 1];

  const position = upper !== lower ? (price - lower) / (upper - lower) : 0.5;

  if (position < 0.1) {
    return { signal: 'entry_long', strength: 1 - position, reason: '触及布林下轨' };
  }
  if (position > 0.9) {
    return { signal: 'entry_short', strength: position, reason: '触及布林上轨' };
  }

  return { signal: 'hold', strength: 0, reason: '' };
}

/** MACD 策略信号 */
export function macdSignal(df: DataFrame, index: number): {
  signal: 'entry_long' | 'entry_short' | 'exit' | 'hold';
  strength: number;
  reason: string;
} {
  const period = 14;
  if (index < 35) return { signal: 'hold', strength: 0, reason: '预热期' };

  const close = df.close.slice(0, index + 1);
  const macd = calculateMACD(close, 12, 26);
  const hist = macd.histogram[macd.histogram.length - 1];
  const prevHist = macd.histogram[macd.histogram.length - 2] ?? 0;

  if (prevHist <= 0 && hist > 0) {
    return { signal: 'entry_long', strength: Math.min(1, hist * 10 + 0.5), reason: 'MACD金叉' };
  }
  if (prevHist >= 0 && hist < 0) {
    return { signal: 'entry_short', strength: Math.min(1, -hist * 10 + 0.5), reason: 'MACD死叉' };
  }

  return { signal: 'hold', strength: 0, reason: '' };
}

/** 组合策略 - 多指标确认 */
export function comboSignal(df: DataFrame, index: number): {
  signal: 'entry_long' | 'entry_short' | 'exit' | 'hold';
  strength: number;
  reason: string;
} {
  const ma = maCrossSignal(df, index);
  const rsi = rsiSignal(df, index);
  const bb = bollingerSignal(df, index);

  // Long: MA金叉 + RSI不超买 + 布林带支撑
  if (ma.signal === 'entry_long' && rsi.momentum !== 'overbought') {
    const strength = 0.4 + (rsi.strength > 0 ? 0.3 : 0) + (bb.signal === 'entry_long' ? 0.3 : 0);
    if (strength >= 0.7) {
      return { signal: 'entry_long', strength, reason: `${ma.reason} + ${rsi.reason}` };
    }
  }

  // Short: MA死叉 + RSI不超卖 + 布林带压力
  if (ma.signal === 'entry_short' && rsi.momentum !== 'oversold') {
    const strength = 0.4 + (rsi.strength > 0 ? 0.3 : 0) + (bb.signal === 'entry_short' ? 0.3 : 0);
    if (strength >= 0.7) {
      return { signal: 'entry_short', strength, reason: `${ma.reason} + ${rsi.reason}` };
    }
  }

  return { signal: 'hold', strength: 0, reason: '' };
}

// ============================================
// 海龟交易法策略
// ============================================

export interface TurtleConfig {
  entryPeriod: number;  // 入场周期 (默认20)
  exitPeriod: number;   // 出场周期 (默认10)
  atrPeriod: number;    // ATR周期 (默认20)
  maxUnits: number;     // 最大仓位单位 (默认4)
}

export const DEFAULT_TURTLE_CONFIG: TurtleConfig = {
  entryPeriod: 20,
  exitPeriod: 10,
  atrPeriod: 20,
  maxUnits: 4,
};

/** 计算 True Range */
function calculateTrueRange(high: number, low: number, prevClose: number): number {
  const hl = high - low;
  const hc = Math.abs(high - prevClose);
  const lc = Math.abs(low - prevClose);
  return Math.max(hl, hc, lc);
}

/** 计算 ATR 序列 */
export function calculateATRSeries(highs: number[], lows: number[], closes: number[], period: number): number[] {
  const tr: number[] = [0];
  for (let i = 1; i < highs.length; i++) {
    tr.push(calculateTrueRange(highs[i], lows[i], closes[i - 1]));
  }
  // 简单移动平均
  const atr: number[] = [];
  for (let i = 0; i < tr.length; i++) {
    if (i < period - 1) {
      atr.push(NaN);
    } else {
      const sum = tr.slice(i - period + 1, i + 1).reduce((a, b) => a + b, 0);
      atr.push(sum / period);
    }
  }
  return atr;
}

/** 计算 N 日最高价 */
function rollingMax(arr: number[], period: number, index: number): number {
  if (index < period) return NaN;
  return Math.max(...arr.slice(index - period, index));
}

/** 计算 N 日最低价 */
function rollingMin(arr: number[], period: number, index: number): number {
  if (index < period) return NaN;
  return Math.min(...arr.slice(index - period, index));
}

/** 海龟交易法信号生成器 */
export function turtleSignal(
  df: DataFrame,
  index: number,
  state?: TurtlePositionState | null
): {
  signal: 'entry_long' | 'entry_short' | 'exit' | 'hold';
  action?: 'entry' | 'add' | 'exit' | 'stop';
  strength: number;
  reason: string;
} {
  const config = DEFAULT_TURTLE_CONFIG;
  const { entryPeriod, exitPeriod, atrPeriod, maxUnits } = config;

  // 预热期
  if (index < atrPeriod) {
    return { signal: 'hold', strength: 0, reason: '预热期' };
  }

  const high = df.high;
  const low = df.low;
  const close = df.close;

  // 计算 ATR
  const atr = calculateTrueRange(high[index], low[index], close[index - 1]);
  const atrAvg = calculateATRSeries(high, low, close, atrPeriod)[index];
  if (isNaN(atrAvg) || atrAvg <= 0) {
    return { signal: 'hold', strength: 0, reason: '无ATR数据' };
  }

  // 计算入场和出场高低点 (shift 1)
  const entryHigh = rollingMax(high, entryPeriod, index - 1);
  const exitLow = rollingMin(low, exitPeriod, index - 1);

  if (isNaN(entryHigh) || isNaN(exitLow)) {
    return { signal: 'hold', strength: 0, reason: '无高低点数据' };
  }

  // 无持仓状态
  if (!state || state.units === 0) {
    // 入场条件：突破 20 日最高价
    if (high[index] > entryHigh) {
      return {
        signal: 'entry_long',
        action: 'entry',
        strength: 1,
        reason: `突破${entryPeriod}日高点 ${entryHigh.toFixed(2)}`,
      };
    }
    return { signal: 'hold', strength: 0, reason: '' };
  }

  // 有持仓状态
  if (state.direction === 'long') {
    // 止损：跌破 2N
    const stopLoss = state.entryPrice - 2 * atrAvg;
    if (low[index] <= stopLoss) {
      return {
        signal: 'exit',
        action: 'stop',
        strength: 1,
        reason: `止损 ${stopLoss.toFixed(2)}`,
      };
    }

    // 加仓条件：价格 > 入场价 + 0.5N 且未满仓
    if (state.units < maxUnits) {
      const addPrice = state.entryPrice + 0.5 * atrAvg;
      if (close[index] >= addPrice) {
        return {
          signal: 'hold',
          action: 'add',
          strength: 0.8,
          reason: `加仓点 ${addPrice.toFixed(2)}`,
        };
      }
    }

    // 出场条件：跌破 M 日最低价
    if (low[index] < exitLow) {
      return {
        signal: 'exit',
        action: 'exit',
        strength: 1,
        reason: `跌破${exitPeriod}日低点 ${exitLow.toFixed(2)}`,
      };
    }
  }

  return { signal: 'hold', strength: 0, reason: '' };
}

export interface TurtlePositionState {
  direction: 'long' | 'short';
  entryPrice: number;
  units: number;
}

// ============================================
// 技术指标
// ============================================

function average(arr: number[]): number {
  return arr.reduce((a, b) => a + b, 0) / arr.length;
}

export function calculateSMA(prices: number[], period: number): number[] {
  const result: number[] = [];
  for (let i = 0; i < prices.length; i++) {
    if (i < period - 1) {
      result.push(NaN);
    } else {
      result.push(average(prices.slice(i - period + 1, i + 1)));
    }
  }
  return result;
}

export function calculateEMA(prices: number[], period: number): number[] {
  const result: number[] = [];
  const multiplier = 2 / (period + 1);
  let ema = average(prices.slice(0, period));
  for (let i = 0; i < prices.length; i++) {
    if (i < period - 1) {
      result.push(NaN);
    } else if (i === period - 1) {
      result.push(ema);
    } else {
      ema = (prices[i] - ema) * multiplier + ema;
      result.push(ema);
    }
  }
  return result;
}

export function calculateRSI(prices: number[], period: number): number[] {
  const result: number[] = [];
  const gains: number[] = [];
  const losses: number[] = [];

  for (let i = 1; i < prices.length; i++) {
    const change = prices[i] - prices[i - 1];
    gains.push(change > 0 ? change : 0);
    losses.push(change < 0 ? -change : 0);
  }

  for (let i = 0; i < prices.length; i++) {
    if (i === 0) {
      result.push(NaN);
    } else if (i < period) {
      result.push(NaN);
    } else {
      const avgGain = average(gains.slice(i - period, i));
      const avgLoss = average(losses.slice(i - period, i));
      if (avgLoss === 0) {
        result.push(100);
      } else {
        const rs = avgGain / avgLoss;
        result.push(100 - 100 / (1 + rs));
      }
    }
  }
  return result;
}

export function calculateMACD(prices: number[], fast: number, slow: number): {
  macd: number[];
  signal: number[];
  histogram: number[];
} {
  const emaFast = calculateEMA(prices, fast);
  const emaSlow = calculateEMA(prices, slow);
  const macd: number[] = [];
  const histogram: number[] = [];

  for (let i = 0; i < prices.length; i++) {
    macd.push(emaFast[i] - emaSlow[i]);
    histogram.push(0);
  }

  const signal = calculateEMA(macd.filter((v) => !isNaN(v)), 9);
  const offset = macd.length - signal.length;

  for (let i = 0; i < macd.length; i++) {
    if (i >= offset) {
      histogram[i] = macd[i] - signal[i - offset];
    }
  }

  return { macd, signal, histogram };
}

export function calculateBollingerBands(
  prices: number[],
  period: number,
  stdDev: number
): { upper: number[]; middle: number[]; lower: number[] } {
  const sma = calculateSMA(prices, period);
  const upper: number[] = [];
  const lower: number[] = [];

  for (let i = 0; i < prices.length; i++) {
    if (i < period - 1) {
      upper.push(NaN);
      lower.push(NaN);
    } else {
      const slice = prices.slice(i - period + 1, i + 1);
      const mean = sma[i];
      const variance = slice.reduce((sum, p) => sum + Math.pow(p - mean, 2), 0) / period;
      const std = Math.sqrt(variance);
      upper.push(mean + stdDev * std);
      lower.push(mean - stdDev * std);
    }
  }

  return { upper, middle: sma, lower };
}

export function calculateATR(
  highs: number[],
  lows: number[],
  closes: number[],
  period: number
): number[] {
  const tr: number[] = [0];
  for (let i = 1; i < highs.length; i++) {
    const hl = highs[i] - lows[i];
    const hc = Math.abs(highs[i] - closes[i - 1]);
    const lc = Math.abs(lows[i] - closes[i - 1]);
    tr.push(Math.max(hl, hc, lc));
  }
  return calculateSMA(tr, period);
}

// ============================================
// 回测引擎
// ============================================

export interface EngineConfig {
  initialCapital: number;
  commissionRate: number;
  slippage: number;
  stoploss: number;
  minimalRoi: Record<string, number>;
  trailingStop: boolean;
  useExitSignal: boolean;
  maxOpenTrades: number;
  canShort: boolean;
  startupCandleCount: number;
}

export const DEFAULT_ENGINE_CONFIG: EngineConfig = {
  initialCapital: 10000,
  commissionRate: 0.001,
  slippage: 0.0005,
  stoploss: -0.1,
  minimalRoi: { '0': 0.05 },
  trailingStop: false,
  useExitSignal: true,
  maxOpenTrades: 1,
  canShort: false,
  startupCandleCount: 50,
};

export interface EngineState {
  capital: number;
  peakCapital: number;
  maxDrawdown: number;
  maxDrawdownDuration: number;
  currentDrawdownDuration: number;
  inPosition: boolean;
  currentTrade: {
    id: string;
    direction: 'long' | 'short';
    entryPrice: number;
    entryTime: number;
    amount: number;
    stoploss: number;
    takeprofit: number;
    entryTag?: string;
  } | null;
  trades: Trade[];
  equityCurve: EquityPoint[];
}

export class BacktestEngineCore {
  private config: EngineConfig;
  private df: DataFrame;
  private state: EngineState;
  private signalGenerator: SignalGenerator;
  private onProgress?: BacktestProgressCallback;

  constructor(
    df: DataFrame,
    config: Partial<EngineConfig> = {},
    signalGenerator: SignalGenerator = maCrossSignal,
    onProgress?: BacktestProgressCallback
  ) {
    this.df = df;
    this.config = { ...DEFAULT_ENGINE_CONFIG, ...config };
    this.signalGenerator = signalGenerator;
    this.onProgress = onProgress;

    this.state = {
      capital: this.config.initialCapital,
      peakCapital: this.config.initialCapital,
      maxDrawdown: 0,
      maxDrawdownDuration: 0,
      currentDrawdownDuration: 0,
      inPosition: false,
      currentTrade: null,
      trades: [],
      equityCurve: [],
    };
  }

  /** 运行回测 */
  run(): BacktestResult {
    const startTime = performance.now();
    const { config, df } = this;
    const startIndex = config.startupCandleCount;
    const totalBars = df.close.length - startIndex;

    // 预计算指标
    this.precomputeIndicators();

    // 逐K线回测
    for (let i = startIndex; i < df.close.length; i++) {
      const kline = this.extractKline(df, i);

      // 检查入场
      if (!this.state.inPosition) {
        const sig = this.signalGenerator(df, i, null);
        if ((sig.signal === 'entry_long') || (sig.signal === 'entry_short' && config.canShort)) {
          this.executeEntry(kline, sig.signal as 'entry_long' | 'entry_short', sig.reason);
        }
      } else {
        // 检查出场
        const exitReason = this.checkExit(df, i);
        if (exitReason) {
          this.executeExit(kline, exitReason);
        }
      }

      // 更新权益曲线
      this.updateEquity(kline.time, kline.close);

      // 进度回调
      if (this.onProgress && i % 50 === 0) {
        this.onProgress({
          progress: ((i - startIndex) / totalBars) * 100,
          currentBar: i - startIndex,
          totalBars,
          equity: this.state.capital,
          openTrades: this.state.inPosition ? 1 : 0,
        });
      }
    }

    // 平仓未结束交易
    if (this.state.inPosition && this.state.currentTrade) {
      const lastKline = this.extractKline(df, df.close.length - 1);
      this.executeExit(lastKline, 'force_exit');
    }

    const runtime = performance.now() - startTime;

    return this.buildResult(runtime);
  }

  /** 预计算指标 */
  private precomputeIndicators(): void {
    // 指标已内嵌在信号生成器中，按需计算
    // 如需预计算，可扩展此处
  }

  private extractKline(df: DataFrame, index: number) {
    return {
      time: df.time[index],
      open: df.open[index],
      high: df.high[index],
      low: df.low[index],
      close: df.close[index],
      volume: df.volume[index],
    };
  }

  /** 执行入场 */
  private executeEntry(
    kline: { time: number; close: number },
    direction: 'entry_long' | 'entry_short',
    reason: string
  ): void {
    const { config, state } = this;
    const price = kline.close * (1 + config.slippage);
    const positionValue = state.capital / config.maxOpenTrades;
    const amount = positionValue / price;

    const stoplossPct = Math.abs(config.stoploss);
    const stoploss = direction === 'entry_long'
      ? price * (1 - stoplossPct)
      : price * (1 + stoplossPct);

    const maxRoiPct = Math.max(...Object.values(config.minimalRoi));
    const takeprofit = direction === 'entry_long'
      ? price * (1 + maxRoiPct)
      : price * (1 - maxRoiPct);

    state.inPosition = true;
    state.currentTrade = {
      id: `trade_${state.trades.length + 1}`,
      direction: direction === 'entry_long' ? 'long' : 'short',
      entryPrice: price,
      entryTime: kline.time,
      amount,
      stoploss,
      takeprofit,
      entryTag: reason,
    };
  }

  /** 检查出场 */
  private checkExit(df: DataFrame, index: number): string | null {
    const { state, config } = this;
    if (!state.currentTrade) return null;

    const { entryPrice, direction, stoploss } = state.currentTrade;
    const kline = this.extractKline(df, index);
    const currentPrice = kline.close;
    const entryTime = state.currentTrade.entryTime;
    const duration = (kline.time - entryTime) / 60000;

    // 1. 止损
    if (direction === 'long' && currentPrice <= stoploss) return 'stop_loss';
    if (direction === 'short' && currentPrice >= stoploss) return 'stop_loss';

    // 2. ROI 止盈
    const roiKey = Object.keys(config.minimalRoi)
      .map(Number)
      .filter((t) => duration >= t)
      .sort((a, b) => b - a)[0];
    if (roiKey !== undefined) {
      const roiPct = config.minimalRoi[roiKey];
      const takeprofit = direction === 'long'
        ? entryPrice * (1 + roiPct)
        : entryPrice * (1 - roiPct);
      if (direction === 'long' && currentPrice >= takeprofit) return 'roi';
      if (direction === 'short' && currentPrice <= takeprofit) return 'roi';
    }

    // 3. 追踪止损
    if (config.trailingStop) {
      const trailingDist = 0.005;
      const highSinceEntry = Math.max(...df.high.slice(
        df.time.indexOf(entryTime),
        index + 1
      ));
      const lowSinceEntry = Math.min(...df.low.slice(
        df.time.indexOf(entryTime),
        index + 1
      ));
      if (direction === 'long') {
        const trailingSL = highSinceEntry * (1 - trailingDist);
        if (currentPrice <= trailingSL) return 'trailing_stop';
      } else {
        const trailingSL = lowSinceEntry * (1 + trailingDist);
        if (currentPrice >= trailingSL) return 'trailing_stop';
      }
    }

    // 4. 退出信号
    if (config.useExitSignal) {
      const sig = this.signalGenerator(df, index, state.trades[state.trades.length - 1] ?? null);
      const oppositeDirection = direction === 'long' ? 'entry_short' : 'entry_long';
      if (sig.signal === oppositeDirection) return 'exit_signal';
    }

    return null;
  }

  /** 执行出场 */
  private executeExit(
    kline: { time: number; close: number },
    reason: string
  ): void {
    const { state, config } = this;
    if (!state.currentTrade) return;

    const trade = state.currentTrade;
    const exitPrice = kline.close * (1 - config.slippage);
    const duration = (kline.time - trade.entryTime) / 60000;

    const pnl = trade.direction === 'long'
      ? (exitPrice - trade.entryPrice) * trade.amount
      : (trade.entryPrice - exitPrice) * trade.amount;

    const pnlPercent = trade.direction === 'long'
      ? (exitPrice - trade.entryPrice) / trade.entryPrice
      : (trade.entryPrice - exitPrice) / trade.entryPrice;

    const entryCommission = trade.entryPrice * trade.amount * config.commissionRate;
    const exitCommission = exitPrice * trade.amount * config.commissionRate;
    const totalCommission = entryCommission + exitCommission;
    const slippageCost = kline.close * trade.amount * config.slippage * 2;
    const netPnl = pnl - totalCommission;

    state.capital += netPnl;

    const completedTrade: Trade = {
      id: trade.id,
      entryTime: trade.entryTime,
      exitTime: kline.time,
      duration: Math.round(duration),
      direction: trade.direction,
      entryPrice: trade.entryPrice,
      exitPrice,
      amount: trade.amount,
      pnl: netPnl,
      pnlPercent: pnlPercent * 100,
      commission: totalCommission,
      slippageCost,
      exitReason: reason as Trade['exitReason'],
      entryTag: trade.entryTag,
    };

    state.trades.push(completedTrade);
    state.inPosition = false;
    state.currentTrade = null;
  }

  /** 更新权益曲线 */
  private updateEquity(time: number, close: number): void {
    const { state } = this;
    let currentValue = state.capital;

    if (state.currentTrade) {
      const unrealized = state.currentTrade.direction === 'long'
        ? (close - state.currentTrade.entryPrice) * state.currentTrade.amount
        : (state.currentTrade.entryPrice - close) * state.currentTrade.amount;
      currentValue += unrealized;
    }

    const drawdown = state.peakCapital > 0
      ? (state.peakCapital - currentValue) / state.peakCapital
      : 0;

    if (currentValue > state.peakCapital) {
      state.peakCapital = currentValue;
      state.currentDrawdownDuration = 0;
    } else {
      state.currentDrawdownDuration++;
    }

    if (drawdown > state.maxDrawdown) state.maxDrawdown = drawdown;
    if (state.currentDrawdownDuration > state.maxDrawdownDuration) {
      state.maxDrawdownDuration = state.currentDrawdownDuration;
    }

    state.equityCurve.push({ time, value: currentValue, drawdown });
  }

  /** 构建结果 */
  private buildResult(runtime: number): BacktestResult {
    const { state, config } = this;
    const trades = state.trades;
    const winningTrades = trades.filter((t) => t.pnl > 0);
    const losingTrades = trades.filter((t) => t.pnl <= 0);

    const totalWin = winningTrades.reduce((s, t) => s + t.pnl, 0);
    const totalLoss = Math.abs(losingTrades.reduce((s, t) => s + t.pnl, 0));

    const totalReturn = state.capital > 0
      ? ((state.capital - config.initialCapital) / config.initialCapital) * 100
      : 0;

    const tradingDays = trades.length > 0
      ? Math.max(...trades.map((t) => t.exitTime)) / 86400000
      : 1;
    const years = tradingDays / 365;
    const annualizedReturn = years > 0
      ? (Math.pow(state.capital / config.initialCapital, 1 / years) - 1) * 100
      : 0;

    const dailyReturns = this.calcDailyReturns();
    const avgReturn = dailyReturns.length > 0
      ? dailyReturns.reduce((a, b) => a + b, 0) / dailyReturns.length
      : 0;
    const stdReturn = this.stdDev(dailyReturns);
    const sharpeRatio = stdReturn > 0 ? (avgReturn / stdReturn) * Math.sqrt(252) : 0;

    const negativeReturns = dailyReturns.filter((r) => r < 0);
    const stdDownside = negativeReturns.length > 0 ? this.stdDev(negativeReturns) : 1;
    const sortinoRatio = stdDownside > 0 ? (avgReturn / stdDownside) * Math.sqrt(252) : 0;

    const calmarRatio = state.maxDrawdown > 0 ? annualizedReturn / (state.maxDrawdown * 100) : 0;
    const expectancy = trades.length > 0
      ? trades.reduce((s, t) => s + t.pnl, 0) / trades.length
      : 0;
    const volatility = stdReturn * Math.sqrt(252) * 100;

    const metrics: BacktestMetrics = {
      totalReturn,
      annualizedReturn,
      sharpeRatio,
      sortinoRatio,
      maxDrawdown: state.maxDrawdown * 100,
      maxDrawdownDuration: state.maxDrawdownDuration,
      maxDrawdownPeak: state.peakCapital,
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
      expectancy,
      calmarRatio: isFinite(calmarRatio) ? calmarRatio : 0,
      volatility,
      bestTrade: trades.length > 0 ? Math.max(...trades.map((t) => t.pnl)) : 0,
      worstTrade: trades.length > 0 ? Math.min(...trades.map((t) => t.pnl)) : 0,
      avgTradeDuration: trades.length > 0
        ? trades.reduce((s, t) => s + t.duration, 0) / trades.length
        : 0,
    };

    return {
      config: {
        initialCapital: config.initialCapital,
        commissionRate: config.commissionRate,
        slippage: config.slippage,
        startDate: this.df.time[config.startupCandleCount],
        endDate: this.df.time[this.df.time.length - 1],
        pair: 'BTCUSDT',
        timeframe: '1h',
      },
      metrics,
      trades,
      equityCurve: state.equityCurve,
      drawdownCurve: state.equityCurve.map((e) => ({ time: e.time, value: e.drawdown * 100 })),
      runtime,
      timestamp: Date.now(),
    };
  }

  private calcDailyReturns(): number[] {
    const returns: number[] = [];
    for (let i = 1; i < this.state.equityCurve.length; i++) {
      const prev = this.state.equityCurve[i - 1].value;
      const curr = this.state.equityCurve[i].value;
      if (prev > 0) returns.push((curr - prev) / prev);
    }
    return returns;
  }

  private stdDev(values: number[]): number {
    if (values.length === 0) return 0;
    const mean = values.reduce((a, b) => a + b, 0) / values.length;
    const squaredDiffs = values.map((v) => Math.pow(v - mean, 2));
    return Math.sqrt(squaredDiffs.reduce((a, b) => a + b, 0) / values.length);
  }
}

// ============================================
// 便捷 API
// ============================================

export type StrategyName = 'ma_cross' | 'rsi' | 'bollinger' | 'macd' | 'combo' | 'turtle';

const SIGNAL_MAP: Record<StrategyName, SignalGenerator> = {
  ma_cross: maCrossSignal,
  rsi: rsiSignal,
  bollinger: bollingerSignal,
  macd: macdSignal,
  combo: comboSignal,
  turtle: () => ({ signal: 'hold', strength: 0, reason: 'Use turtle engine' }),
};

export interface QuickBacktestOptions {
  df: DataFrame;
  strategy?: StrategyName;
  initialCapital?: number;
  commissionRate?: number;
  stoploss?: number;
  canShort?: boolean;
  onProgress?: BacktestProgressCallback;
}

export function runBacktest(options: QuickBacktestOptions): BacktestResult {
  const strategy = SIGNAL_MAP[options.strategy ?? 'ma_cross'];
  const config: Partial<EngineConfig> = {
    initialCapital: options.initialCapital,
    commissionRate: options.commissionRate,
    stoploss: options.stoploss,
    canShort: options.canShort,
  };
  const engine = new BacktestEngineCore(options.df, config, strategy, options.onProgress);
  return engine.run();
}

// ============================================
// 海龟交易法专用引擎
// ============================================

export class TurtleBacktestEngine {
  private df: DataFrame;
  private config: TurtleConfig & {
    initialCapital: number;
    commissionRate: number;
    slippage: number;
  };

  constructor(df: DataFrame, turtleConfig: Partial<TurtleConfig> = {}, capital: number = 10000) {
    this.df = df;
    this.config = {
      ...DEFAULT_TURTLE_CONFIG,
      ...turtleConfig,
      initialCapital: capital,
      commissionRate: 0.001,
      slippage: 0.0005,
    };
  }

  run(): BacktestResult {
    const startTime = performance.now();
    const { config, df } = this;
    const { entryPeriod, exitPeriod, atrPeriod, maxUnits, initialCapital, commissionRate, slippage } = config;

    const state = {
      capital: initialCapital,
      peakCapital: initialCapital,
      maxDrawdown: 0,
      maxDrawdownDuration: 0,
      currentDrawdownDuration: 0,
      trades: [] as Trade[],
      equityCurve: [] as EquityPoint[],
      // 海龟持仓状态
      position: 0,
      entryPrice: 0,
      entryTime: 0,
      units: 0,
      stopLoss: 0,
    };

    // 预计算 ATR
    const atrValues = calculateATRSeries(df.high, df.low, df.close, atrPeriod);

    const startIndex = atrPeriod;

    for (let i = startIndex; i < df.close.length; i++) {
      const high = df.high[i];
      const low = df.low[i];
      const close = df.close[i];
      const time = df.time[i];
      const atr = atrValues[i];

      if (isNaN(atr) || atr <= 0) continue;

      // 计算入场和出场高低点 (shift 1)
      const entryHigh = rollingMax(df.high, entryPeriod, i - 1);
      const exitLow = rollingMin(df.low, exitPeriod, i - 1);

      if (isNaN(entryHigh) || isNaN(exitLow)) continue;

      // 无持仓：检查入场
      if (state.position === 0) {
        if (high > entryHigh) {
          // 入场：突破 20 日最高价
          const unitSize = state.capital * 0.01 / atr;
          state.position = unitSize;
          state.entryPrice = entryHigh;
          state.entryTime = time;
          state.stopLoss = state.entryPrice - 2 * atr;
          state.units = 1;
          state.capital = state.capital - state.position * state.entryPrice * (1 + slippage);
        }
      } else {
        // 有持仓：检查加仓、止损、出场

        // 止损
        if (low <= state.stopLoss) {
          this.closeTrade(state, time, state.stopLoss, 'stop_loss', commissionRate, slippage);
        }
        // 加仓
        else if (state.units < maxUnits) {
          const addPrice = state.entryPrice + 0.5 * atr;
          if (close >= addPrice) {
            const addSize = state.capital * 0.01 / atr;
            const cost = addSize * close * (1 + slippage);
            if (cost <= state.capital) {
              state.position += addSize;
              state.entryPrice = (state.entryPrice * state.units + close) / (state.units + 1);
              state.stopLoss = state.entryPrice - 2 * atr;
              state.capital -= cost;
              state.units++;
            }
          }
        }
        // 出场
        else if (low < exitLow) {
          this.closeTrade(state, time, close, 'exit_signal', commissionRate, slippage);
        }
      }

      // 更新权益曲线
      this.updateEquity(state, time, close);
    }

    // 强制平仓
    if (state.position > 0) {
      const lastClose = df.close[df.close.length - 1];
      const lastTime = df.time[df.time.length - 1];
      this.closeTrade(state, lastTime, lastClose, 'force_exit', commissionRate, slippage);
    }

    const runtime = performance.now() - startTime;
    return this.buildResult(state, runtime);
  }

  private closeTrade(
    state: ReturnType<typeof this['run']> extends infer R ? { capital: number; peakCapital: number; maxDrawdown: number; maxDrawdownDuration: number; currentDrawdownDuration: number; trades: Trade[]; equityCurve: EquityPoint[] } : never,
    exitTime: number,
    exitPrice: number,
    reason: string,
    commissionRate: number,
    slippage: number
  ): void {
    const direction = 'long';
    const exitPx = exitPrice * (1 - slippage);
    const pnl = (exitPx - state.entryPrice) * state.position;
    const commission = (state.entryPrice * state.position + exitPx * state.position) * commissionRate;
    const netPnl = pnl - commission;

    state.capital += state.position * exitPx - commission;

    const trade: Trade = {
      id: `turtle_${state.trades.length + 1}`,
      entryTime: state.entryTime,
      exitTime,
      duration: Math.round((exitTime - state.entryTime) / 60000),
      direction,
      entryPrice: state.entryPrice,
      exitPrice: exitPx,
      amount: state.position,
      pnl: netPnl,
      pnlPercent: ((exitPx - state.entryPrice) / state.entryPrice) * 100,
      commission,
      slippageCost: exitPrice * state.position * slippage,
      exitReason: reason as Trade['exitReason'],
      entryTag: `海龟${state.units}单位`,
    };

    state.trades.push(trade);
    state.position = 0;
    state.units = 0;
  }

  private updateEquity(
    state: { capital: number; peakCapital: number; maxDrawdown: number; maxDrawdownDuration: number; currentDrawdownDuration: number; position: number; entryPrice: number; equityCurve: EquityPoint[] },
    time: number,
    close: number
  ): void {
    let currentValue = state.capital;
    if (state.position > 0) {
      currentValue += (close - state.entryPrice) * state.position;
    }

    const drawdown = state.peakCapital > 0 ? (state.peakCapital - currentValue) / state.peakCapital : 0;

    if (currentValue > state.peakCapital) {
      state.peakCapital = currentValue;
      state.currentDrawdownDuration = 0;
    } else {
      state.currentDrawdownDuration++;
    }

    if (drawdown > state.maxDrawdown) state.maxDrawdown = drawdown;
    if (state.currentDrawdownDuration > state.maxDrawdownDuration) {
      state.maxDrawdownDuration = state.currentDrawdownDuration;
    }

    state.equityCurve.push({ time, value: currentValue, drawdown });
  }

  private buildResult(state: { capital: number; peakCapital: number; maxDrawdown: number; maxDrawdownDuration: number; currentDrawdownDuration: number; trades: Trade[]; equityCurve: EquityPoint[] }, runtime: number): BacktestResult {
    const trades = state.trades;
    const winningTrades = trades.filter((t) => t.pnl > 0);
    const losingTrades = trades.filter((t) => t.pnl <= 0);

    const totalWin = winningTrades.reduce((s, t) => s + t.pnl, 0);
    const totalLoss = Math.abs(losingTrades.reduce((s, t) => s + t.pnl, 0));

    const totalReturn = ((state.capital - this.config.initialCapital) / this.config.initialCapital) * 100;

    const tradingDays = trades.length > 0 ? Math.max(...trades.map((t) => t.exitTime)) / 86400000 : 1;
    const years = tradingDays / 365;
    const annualizedReturn = years > 0 ? (Math.pow(state.capital / this.config.initialCapital, 1 / years) - 1) * 100 : 0;

    const dailyReturns: number[] = [];
    for (let i = 1; i < state.equityCurve.length; i++) {
      const prev = state.equityCurve[i - 1].value;
      const curr = state.equityCurve[i].value;
      if (prev > 0) dailyReturns.push((curr - prev) / prev);
    }

    const avgReturn = dailyReturns.length > 0 ? dailyReturns.reduce((a, b) => a + b, 0) / dailyReturns.length : 0;
    const stdReturn = this.stdDev(dailyReturns);
    const sharpeRatio = stdReturn > 0 ? (avgReturn / stdReturn) * Math.sqrt(252) : 0;

    const negativeReturns = dailyReturns.filter((r) => r < 0);
    const stdDownside = negativeReturns.length > 0 ? this.stdDev(negativeReturns) : 1;
    const sortinoRatio = stdDownside > 0 ? (avgReturn / stdDownside) * Math.sqrt(252) : 0;

    const metrics: BacktestMetrics = {
      totalReturn,
      annualizedReturn,
      sharpeRatio,
      sortinoRatio,
      maxDrawdown: state.maxDrawdown * 100,
      maxDrawdownDuration: state.maxDrawdownDuration,
      maxDrawdownPeak: state.peakCapital,
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
      expectancy: trades.length > 0 ? trades.reduce((s, t) => s + t.pnl, 0) / trades.length : 0,
      calmarRatio: state.maxDrawdown > 0 ? annualizedReturn / (state.maxDrawdown * 100) : 0,
      volatility: stdReturn * Math.sqrt(252) * 100,
      bestTrade: trades.length > 0 ? Math.max(...trades.map((t) => t.pnl)) : 0,
      worstTrade: trades.length > 0 ? Math.min(...trades.map((t) => t.pnl)) : 0,
      avgTradeDuration: trades.length > 0 ? trades.reduce((s, t) => s + t.duration, 0) / trades.length : 0,
    };

    return {
      config: {
        initialCapital: this.config.initialCapital,
        commissionRate: this.config.commissionRate,
        slippage: this.config.slippage,
        startDate: this.df.time[this.config.atrPeriod],
        endDate: this.df.time[this.df.time.length - 1],
        pair: 'BTCUSDT',
        timeframe: '1h',
      },
      metrics,
      trades,
      equityCurve: state.equityCurve,
      drawdownCurve: state.equityCurve.map((e) => ({ time: e.time, value: e.drawdown * 100 })),
      runtime,
      timestamp: Date.now(),
    };
  }

  private stdDev(values: number[]): number {
    if (values.length === 0) return 0;
    const mean = values.reduce((a, b) => a + b, 0) / values.length;
    const squaredDiffs = values.map((v) => Math.pow(v - mean, 2));
    return Math.sqrt(squaredDiffs.reduce((a, b) => a + b, 0) / values.length);
  }
}

export function runTurtleBacktest(
  df: DataFrame,
  options: {
    initialCapital?: number;
    entryPeriod?: number;
    exitPeriod?: number;
    atrPeriod?: number;
    maxUnits?: number;
  } = {}
): BacktestResult {
  const engine = new TurtleBacktestEngine(df, {
    entryPeriod: options.entryPeriod ?? 20,
    exitPeriod: options.exitPeriod ?? 10,
    atrPeriod: options.atrPeriod ?? 20,
    maxUnits: options.maxUnits ?? 4,
  }, options.initialCapital ?? 10000);
  return engine.run();
}
