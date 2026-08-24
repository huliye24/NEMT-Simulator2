/**
 * Copyright 2026 NEMT Lab
 *
 * NEMT Backtest Types
 * 回测系统类型定义
 */

// ============================================
// K线数据
// ============================================

export interface KlineData {
  time: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface DataFrame {
  time: number[];
  open: number[];
  high: number[];
  low: number[];
  close: number[];
  volume: number[];
  indicators?: Record<string, number[]>;
  enterLong?: number[];
  enterShort?: number[];
  exitLong?: number[];
  exitShort?: number[];
  enterTag?: string[];
}

// ============================================
// 策略接口
// ============================================

export type Timeframe = '1m' | '5m' | '15m' | '30m' | '1h' | '4h' | '1d' | '1w';
export type SignalDirection = 'long' | 'short' | 'both';
export type OrderType = 'market' | 'limit';
export type ExitReason = 'roi' | 'stop_loss' | 'trailing_stop' | 'exit_signal' | 'force_exit' | 'end_of_backtest';

export interface StrategyConfig {
  id: string;
  name: string;
  author: string;
  version: string;
  timeframe: Timeframe;
  canShort: boolean;
  maxOpenTrades: number;
  stoploss: number;
  trailingStop: boolean;
  trailingStopPositive?: number;
  trailingStopPositiveOffset?: number;
  minimalRoi: Record<string, number>;
  orderTypes?: Record<string, OrderType>;
  useExitSignal: boolean;
  startupCandleCount: number;
}

export interface StrategyMetadata {
  pair: string;
}

export interface DataProvider {
  getData(pair: string, timeframe: string, start?: number, end?: number): Promise<DataFrame>;
}

// ============================================
// 订单和交易
// ============================================

export interface Order {
  id: string;
  symbol: string;
  type: OrderType;
  side: 'buy' | 'sell';
  price: number;
  quantity: number;
  filled: number;
  status: 'pending' | 'filled' | 'partial' | 'cancelled' | 'rejected';
  timestamp: number;
}

export interface Trade {
  id: string;
  entryTime: number;
  exitTime: number;
  duration: number;
  direction: 'long' | 'short';
  entryPrice: number;
  exitPrice: number;
  amount: number;
  pnl: number;
  pnlPercent: number;
  commission: number;
  slippageCost: number;
  exitReason: ExitReason;
  entryTag?: string;
}

// ============================================
// 回测配置
// ============================================

export interface BacktestConfig {
  initialCapital: number;
  commissionRate: number;
  slippage: number;
  startDate: number;
  endDate: number;
  pair: string;
  timeframe: Timeframe;
  strategy: 'ma_cross' | 'rsi' | 'bollinger' | 'macd' | 'combo' | 'turtle';
  feeTier?: string;
  marginRatio?: number;
  hedging?: boolean;
  dryRun?: boolean;
}

// ============================================
// 回测指标
// ============================================

export interface BacktestMetrics {
  totalReturn: number;
  annualizedReturn: number;
  sharpeRatio: number;
  sortinoRatio: number;
  maxDrawdown: number;
  maxDrawdownDuration: number;
  maxDrawdownPeak?: number;
  totalTrades: number;
  winningTrades: number;
  losingTrades: number;
  winRate: number;
  avgWin: number;
  avgLoss: number;
  profitFactor: number;
  totalWin: number;
  totalLoss: number;
  tradingDays: number;
  expectancy: number;
  calmarRatio?: number;
  volatility?: number;
  bestTrade: number;
  worstTrade: number;
  avgTradeDuration: number;
}

export interface EquityPoint {
  time: number;
  value: number;
  drawdown: number;
}

export interface BacktestResult {
  config: BacktestConfig;
  metrics: BacktestMetrics;
  trades: Trade[];
  equityCurve: EquityPoint[];
  drawdownCurve: { time: number; value: number }[];
  runtime: number;
  timestamp: number;
}

// ============================================
// 回测状态
// ============================================

export type BacktestStatus = 'idle' | 'loading' | 'running' | 'completed' | 'error';

export interface BacktestProgress {
  status: BacktestStatus;
  progress: number;
  currentBar: number;
  totalBars: number;
  currentEquity: number;
  openTrades: number;
  completedTrades: number;
  error?: string;
}

// ============================================
// 数据源
// ============================================

export type DataSourceType = 'binance' | 'csv' | 'memory';

export interface DataSourceConfig {
  type: DataSourceType;
  symbol?: string;
  timeframe?: Timeframe;
  startDate?: number;
  endDate?: number;
  csvPath?: string;
}

// ============================================
// 信号
// ============================================

export type SignalType = 'buy' | 'sell' | 'hold' | 'close';

export interface TradingSignal {
  type: SignalType;
  strength: number;
  price: number;
  reason: string;
  timestamp: number;
  metadata?: Record<string, unknown>;
}
