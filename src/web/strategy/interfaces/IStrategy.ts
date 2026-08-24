/**
 * Copyright 2026 NEMT Lab
 *
 * NEMT IStrategy Interface
 * 借鉴 freqtrade IStrategy 接口模式
 *
 * 核心概念：
 * - populate_indicators: 计算技术指标
 * - populate_entry_trend: 定义入场信号
 * - populate_exit_trend: 定义出场信号
 */

import type { DataFrame, KlineData } from '../types/kline';
import type { NEMTState } from '../types/nemt';

// ============================================
// 策略接口版本
// ============================================

export const INTERFACE_VERSION = 3;

// ============================================
// 策略类型
// ============================================

export type Timeframe = '1m' | '5m' | '15m' | '30m' | '1h' | '4h' | '1d' | '1w';
export type SignalDirection = 'long' | 'short' | 'both';
export type OrderType = 'market' | 'limit';
export type ExitReason = 'roi' | 'stop_loss' | 'trailing_stop' | 'exit_signal' | 'force_exit';

// ============================================
// 策略配置
// ============================================

export interface StrategyConfig {
  /** 策略 ID */
  id: string;
  /** 策略名称 */
  name: string;
  /** 策略作者 */
  author: string;
  /** 版本 */
  version: string;
  /** 时间周期 */
  timeframe: Timeframe;
  /** 是否支持做空 */
  canShort: boolean;
  /** 最大同时持仓数 */
  maxOpenTrades: number;
  /** 止损 (负数，如 -0.1 表示 10% 止损) */
  stoploss: number;
  /** 追踪止损 */
  trailingStop: boolean;
  trailingStopPositive?: number;
  trailingStopPositiveOffset?: number;
  /** 最小 ROI 表 */
  minimalRoi: Record<string, number>;
  /** 订单类型 */
  orderTypes?: Record<string, OrderType>;
  /** 持仓时间 */
  orderTimeInForce?: Record<string, string>;
  /** 是否仅处理新 K线 */
  processOnlyNewCandles: boolean;
  /** 启动所需 K线数 */
  startupCandleCount: number;
  /** 是否使用退出信号 */
  useExitSignal: boolean;
  /** 仅在盈利时退出 */
  exitProfitOnly: boolean;
  /** 忽略 ROI 如果有入场信号 */
  ignoreRoiIfEntrySignal: boolean;
  /** 仓位调整 */
  positionAdjustmentEnable: boolean;
}

// ============================================
// 数据类型
// ============================================

export interface StrategyMetadata {
  /** 交易对 */
  pair: string;
  /** 附加数据 */
  [key: string]: unknown;
}

// ============================================
// 信号类型
// ============================================

export interface EntrySignal {
  /** 信号类型: 'enter_long' | 'enter_short' | 0 */
  signal: 'enter_long' | 'enter_short' | 0;
  /** 信号标签 (可选) */
  tag?: string;
}

export interface ExitSignal {
  /** 信号类型: 'exit_long' | 'exit_short' | 0 */
  signal: 'exit_long' | 'exit_short' | 0;
  /** 退出原因 */
  reason?: ExitReason;
}

// ============================================
// 策略接口定义
// ============================================

export interface IStrategy {
  /** 接口版本 */
  readonly INTERFACE_VERSION: number;

  /** 策略配置 */
  readonly config: StrategyConfig;

  /** 数据提供者 */
  dp?: DataProvider;

  // -----------------------------------------
  // 核心方法
  // -----------------------------------------

  /**
   * 计算技术指标
   * @param dataframe K线数据
   * @param metadata 元数据
   * @returns 带指标的数据框
   */
  populateIndicators(dataframe: DataFrame, metadata: StrategyMetadata): DataFrame;

  /**
   * 定义入场信号
   * @param dataframe K线数据 (含指标)
   * @param metadata 元数据
   * @returns 带入场信号的数据框
   */
  populateEntryTrend(dataframe: DataFrame, metadata: StrategyMetadata): DataFrame;

  /**
   * 定义出场信号
   * @param dataframe K线数据 (含指标)
   * @param metadata 元数据
   * @returns 带出场信号的数据框
   */
  populateExitTrend(dataframe: DataFrame, metadata: StrategyMetadata): DataFrame;

  // -----------------------------------------
  // 可选方法
  // -----------------------------------------

  /**
   * 获取信息对
   * 返回额外的 (pair, timeframe) 组合
   */
  informativePairs?(): Array<{ pair: string; timeframe: Timeframe }>;

  /**
   * Bot 启动时调用
   */
  botStart?(): void;

  /**
   * Bot 循环开始时调用
   */
  botLoopStart?(currentTime: Date): void;

  /**
   * 自定义止损
   * @returns 新的止损距离 (相对于当前价格的比率)
   */
  customStoploss?(
    pair: string,
    trade: Trade,
    currentTime: Date,
    currentRate: number,
    currentProfit: number,
    afterFill: boolean
  ): number;

  /**
   * 自定义 ROI
   */
  customRoi?(
    pair: string,
    trade: Trade,
    currentTime: Date,
    tradeDuration: number
  ): number | null;

  /**
   * 确认入场
   * @returns true 确认下单，false 取消
   */
  confirmTradeEntry?(
    pair: string,
    orderType: OrderType,
    amount: number,
    rate: number,
    currentTime: Date,
    entryTag?: string,
    side?: SignalDirection
  ): boolean;

  /**
   * 确认出场
   * @returns true 确认下单，false 取消
   */
  confirmTradeExit?(
    pair: string,
    trade: Trade,
    orderType: OrderType,
    amount: number,
    rate: number,
    exitReason: ExitReason,
    currentTime: Date
  ): boolean;

  /**
   * 订单成交时调用
   */
  orderFilled?(pair: string, trade: Trade, order: Order, currentTime: Date): void;
}

// ============================================
// 数据提供者接口
// ============================================

export interface DataProvider {
  /** 获取当前 K线数据 */
  getKlines(pair: string, timeframe: Timeframe, limit?: number): DataFrame;

  /** 获取历史 K线数据 */
  getHistoricalKlines(
    pair: string,
    timeframe: Timeframe,
    startTime: number,
    endTime: number
  ): DataFrame;

  /** 获取当前价格 */
  getCurrentPrice(pair: string): number;

  /** 获取指定交易对的数据 */
  getPairData(pair: string): unknown;
}

// ============================================
// 交易相关类型
// ============================================

export interface Trade {
  /** 交易 ID */
  id: string;
  /** 交易对 */
  pair: string;
  /** 交易方向 */
  direction: 'long' | 'short';
  /** 开仓价格 */
  openRate: number;
  /** 当前价格 */
  currentRate: number;
  /** 开仓时间 */
  openDate: Date;
  /** 持仓数量 */
  amount: number;
  /** 当前盈亏 */
  currentProfit: number;
  /** 当前盈亏 (%) */
  currentProfitPercent: number;
  /** 止损价格 */
  stopLoss?: number;
  /** 止盈价格 */
  takeProfit?: number;
  /** 交易标签 */
  entryTag?: string;
}

export interface Order {
  /** 订单 ID */
  id: string;
  /** 订单状态 */
  status: 'pending' | 'filled' | 'cancelled' | 'expired';
  /** 订单类型 */
  side: 'buy' | 'sell';
  /** 订单类型 */
  type: OrderType;
  /** 价格 */
  price: number;
  /** 数量 */
  amount: number;
  /** 成交价格 */
  filledRate?: number;
  /** 成交数量 */
  filledAmount?: number;
  /** 创建时间 */
  createdAt: Date;
  /** 更新时间 */
  updatedAt: Date;
}

// ============================================
// NEMT 策略扩展接口
// ============================================

export interface NEMTStrategyConfig {
  /** NEMT 临界熵阈值 */
  nemtCriticalEntropy: number;
  /** NEMT 临界 ψ 阈值 */
  nemtCriticalPsi: number;
  /** NEMT 稳定 ψ 阈值 */
  nemtStablePsi: number;
  /** NEMT EMA 衰减因子 */
  nemtEmaAlpha: number;
  /** 有效 NEMT 相位列表 */
  validNemtPhases: Array<'stable' | 'critical' | 'critical_up' | 'critical_down' | 'decay'>;
  /** 是否启用 NEMT 出场 */
  nemtExitOnPhaseChange: boolean;
}

export interface NEMTStrategy extends IStrategy {
  /** NEMT 配置 */
  nemtConfig: NEMTStrategyConfig;

  /**
   * 获取 NEMT 状态
   * @param dataframe K线数据
   * @returns NEMT 状态
   */
  getNEMTState(dataframe: DataFrame): NEMTState;

  /**
   * 检查 NEMT 入场条件
   * @param nemtState NEMT 状态
   * @returns 是否满足入场条件
   */
  checkNEMTEntryCondition(nemtState: NEMTState): boolean;

  /**
   * 检查 NEMT 出场条件
   * @param nemtState NEMT 状态
   * @param trade 当前交易
   * @returns 是否满足出场条件
   */
  checkNEMTExitCondition(nemtState: NEMTState, trade: Trade): boolean;
}

// ============================================
// 策略验证结果
// ============================================

export interface StrategyValidationResult {
  /** 是否有效 */
  valid: boolean;
  /** 错误列表 */
  errors: string[];
  /** 警告列表 */
  warnings: string[];
}
