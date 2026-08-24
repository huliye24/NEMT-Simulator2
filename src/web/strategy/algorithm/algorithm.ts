/**
 * Copyright 2026 NEMT Lab
 *
 * NEMT Event-Driven Algorithm
 * 借鉴 QuantConnect Lean 的事件驱动架构
 *
 * 核心概念：
 * - Initialize: 初始化
 * - OnData: 每个时间步事件
 * - OnOrderEvent: 订单事件
 * - OnEndOfDay: 每日收盘事件
 */

import type { DataFrame, KlineData } from '../types/kline';
import type { Trade, Order } from '../interfaces/IStrategy';

// ============================================
// 算法事件类型
// ============================================

export type AlgorithmEvent =
  | 'on_data'
  | 'on_order_event'
  | 'on_end_of_day'
  | 'on_end_of_hour'
  | 'on_securities_changed'
  | 'on_assignment_order'
  | 'on_margin_call'
  | 'on_brokerage_connection'
  | 'onWarmUpComplete';

// ============================================
// Slice 数据结构
// ============================================

export interface Slice {
  /** 时间戳 */
  timestamp: number;
  /** K线数据 */
  klines: Map<string, KlineData>;
  /** 当前价格 */
  prices: Map<string, number>;
  /** 是否是新 K线 */
  isNewBar: boolean;
}

// ============================================
// 订单事件
// ============================================

export interface OrderEvent {
  /** 订单 ID */
  orderId: string;
  /** 交易对 */
  symbol: string;
  /** 方向 */
  direction: 'buy' | 'sell';
  /** 数量 */
  quantity: number;
  /** 价格 */
  price: number;
  /** 订单状态 */
  status: 'submitted' | 'partiallyFilled' | 'filled' | 'canceled' | 'rejected';
  /** 成交数量 */
  fillQuantity: number;
  /** 成交价格 */
  fillPrice: number;
  /** 消息 */
  message: string;
}

// ============================================
// 持仓信息
// ============================================

export interface Position {
  /** 交易对 */
  symbol: string;
  /** 数量 */
  quantity: number;
  /** 平均价格 */
  averagePrice: number;
  /** 当前价格 */
  currentPrice: number;
  /** 盈亏 */
  unrealizedPnL: number;
  /** 盈亏 (%) */
  unrealizedPnLPercent: number;
  /** 总成本 */
  totalCost: number;
  /** 方向 */
  direction: 'long' | 'short';
}

// ============================================
// 账户信息
// ============================================

export interface Account {
  /** 总资金 */
  totalCash: number;
  /** 可用资金 */
  availableCash: number;
  /** 已用保证金 */
  usedMargin: number;
  /** 总持仓价值 */
  portfolioValue: number;
  /** 持仓列表 */
  positions: Position[];
}

// ============================================
// 证券信息
// ============================================

export interface Security {
  /** 交易对 */
  symbol: string;
  /** 类型 */
  type: 'equity' | 'forex' | 'crypto' | 'future';
  /** 实时价格 */
  price: number;
  /** 开盘价 */
  open: number;
  /** 最高价 */
  high: number;
  /** 最低价 */
  low: number;
  /** 成交量 */
  volume: number;
  /** 是否已授权交易 */
  isTradable: boolean;
}

// ============================================
// 算法接口
// ============================================

export interface IAlgorithm {
  /** 初始化方法 (必须实现) */
  Initialize(): void;

  // -----------------------------------------
  // 事件处理
  // -----------------------------------------

  /** 每个时间步事件 */
  OnData(slice: Slice): void;

  /** 订单事件 */
  OnOrderEvent(event: OrderEvent): void;

  /** 每日收盘事件 */
  OnEndOfDay(symbol?: string): void;

  /** 每小时收盘事件 */
  OnEndOfHour(symbol?: string): void;

  // -----------------------------------------
  // 可选事件
  // -----------------------------------------

  /** 证券变化事件 (添加/移除) */
  OnSecuritiesChanged?(changes: { added: Security[]; removed: Security[] }): void;

  /** 预热完成事件 */
  OnWarmUpComplete?(): void;

  /** 追加保证金事件 */
  OnMarginCall?(requests: MarginCallRequest[]): void;
}

// ============================================
// 保证金请求
// ============================================

export interface MarginCallRequest {
  /** 订单方向 */
  direction: 'buy' | 'sell';
  /** 交易对 */
  symbol: string;
  /** 数量 */
  quantity: number;
}

// ============================================
// 算法基类
// ============================================

export abstract class QCAlgorithm implements IAlgorithm {
  /** 算法名称 */
  name: string = 'Algorithm';

  /** 账户信息 */
  account: Account;

  /** 证券列表 */
  securities: Map<string, Security>;

  /** 持仓列表 */
  portfolio: Map<string, Position>;

  /** K线数据缓存 */
  klineCache: Map<string, KlineData[]>;

  /** 算法状态 */
  isInitialized: boolean = false;
  isRunning: boolean = false;

  // -----------------------------------------
  // 必须实现的方法
  // -----------------------------------------

  abstract Initialize(): void;
  abstract OnData(slice: Slice): void;

  // -----------------------------------------
  // 可选事件
  // -----------------------------------------

  OnOrderEvent(event: OrderEvent): void {}
  OnEndOfDay(symbol?: string): void {}
  OnEndOfHour(symbol?: string): void {}
  OnSecuritiesChanged?(changes: { added: Security[]; removed: Security[] }): void {}
  OnWarmUpComplete?(): void {}
  OnMarginCall?(requests: MarginCallRequest[]): void {}

  // -----------------------------------------
  // 构造函数
  // -----------------------------------------

  constructor() {
    this.account = {
      totalCash: 0,
      availableCash: 0,
      usedMargin: 0,
      portfolioValue: 0,
      positions: [],
    };
    this.securities = new Map();
    this.portfolio = new Map();
    this.klineCache = new Map();
  }

  // -----------------------------------------
  // 初始化方法
  // -----------------------------------------

  /** 设置开始日期 */
  SetStartDate(year: number, month: number, day: number): Date {
    return new Date(year, month - 1, day);
  }

  /** 设置结束日期 */
  SetEndDate(year: number, month: number, day: number): Date {
    return new Date(year, month - 1, day);
  }

  /** 设置初始资金 */
  SetCash(amount: number): void {
    this.account.totalCash = amount;
    this.account.availableCash = amount;
  }

  /** 设置保证金模型 */
  SetBrokerageModel(model: string): void {
    console.log(`[Algorithm] Brokerage model: ${model}`);
  }

  // -----------------------------------------
  // 订阅证券
  // -----------------------------------------

  /** 添加交易对 */
  AddCrypto(symbol: string, resolution: string = '1h'): Security {
    const security: Security = {
      symbol,
      type: 'crypto',
      price: 0,
      open: 0,
      high: 0,
      low: 0,
      volume: 0,
      isTradable: true,
    };

    this.securities.set(symbol, security);
    this.klineCache.set(symbol, []);

    return security;
  }

  /** 添加多个交易对 */
  AddCryptoBulk(symbols: string[], resolution: string = '1h'): void {
    for (const symbol of symbols) {
      this.AddCrypto(symbol, resolution);
    }
  }

  /** 移除交易对 */
  RemoveSecurity(symbol: string): void {
    this.securities.delete(symbol);
    this.klineCache.delete(symbol);
    this.portfolio.delete(symbol);
  }

  // -----------------------------------------
  // 交易执行
  // -----------------------------------------

  /** 市价单 */
  MarketOrder(symbol: string, quantity: number): string {
    const orderId = `order_${Date.now()}`;
    console.log(`[Algorithm] Market Order: ${quantity} ${symbol}`);
    return orderId;
  }

  /** 限价单 */
  LimitOrder(symbol: string, quantity: number, limitPrice: number): string {
    const orderId = `order_${Date.now()}`;
    console.log(`[Algorithm] Limit Order: ${quantity} ${symbol} @ ${limitPrice}`);
    return orderId;
  }

  /** 止损单 */
  StopMarketOrder(symbol: string, quantity: number, stopPrice: number): string {
    const orderId = `order_${Date.now()}`;
    console.log(`[Algorithm] Stop Market Order: ${quantity} ${symbol} @ ${stopPrice}`);
    return orderId;
  }

  /** 设置持仓比例 */
  SetHoldings(symbol: string, percentage: number): void {
    const targetValue = this.account.portfolioValue * percentage;
    const currentPrice = this.securities.get(symbol)?.price || 0;

    if (currentPrice === 0) return;

    const quantity = targetValue / currentPrice;
    this.MarketOrder(symbol, quantity);
  }

  /** 清仓 */
  Liquidate(symbol?: string): void {
    if (symbol) {
      const position = this.portfolio.get(symbol);
      if (position) {
        this.MarketOrder(symbol, -position.quantity);
      }
    } else {
      // 清仓所有
      for (const [sym, pos] of this.portfolio) {
        this.MarketOrder(sym, -pos.quantity);
      }
    }
  }

  // -----------------------------------------
  // 数据获取
  // -----------------------------------------

  /** 获取当前价格 */
  CurrentPrice(symbol: string): number {
    return this.securities.get(symbol)?.price || 0;
  }

  /** 获取历史数据 */
  History(
    symbol: string,
    barCount: number
  ): KlineData[] {
    return this.klineCache.get(symbol) || [];
  }

  /** 获取 K线数据 */
  GetKlines(symbol: string): KlineData[] {
    return this.klineCache.get(symbol) || [];
  }

  // -----------------------------------------
  // 内部方法
  // -----------------------------------------

  /** 处理新的 K线数据 */
  _processNewBar(symbol: string, kline: KlineData): void {
    const cache = this.klineCache.get(symbol);
    if (cache) {
      cache.push(kline);
      // 保留最近 1000 条
      if (cache.length > 1000) {
        cache.shift();
      }
    }

    // 更新证券价格
    const security = this.securities.get(symbol);
    if (security) {
      security.price = kline.close;
      security.open = kline.open;
      security.high = kline.high;
      security.low = kline.low;
      security.volume = kline.volume;
    }
  }

  /** 更新账户信息 */
  _updateAccount(): void {
    let totalValue = this.account.totalCash;
    const positions: Position[] = [];

    for (const [symbol, position] of this.portfolio) {
      const price = this.CurrentPrice(symbol);
      position.currentPrice = price;
      position.unrealizedPnL = (price - position.averagePrice) * position.quantity;
      position.unrealizedPnLPercent =
        position.averagePrice > 0
          ? ((price - position.averagePrice) / position.averagePrice) * 100
          : 0;
      positions.push(position);
      totalValue += position.quantity * price;
    }

    this.account.portfolioValue = totalValue;
    this.account.positions = positions;
    this.account.availableCash = this.account.totalCash - this.account.usedMargin;
  }
}

// ============================================
// 算法管理器
// ============================================

export class AlgorithmManager {
  private algorithm: IAlgorithm;
  private isRunning: boolean = false;
  private timeStep: number = 60000; // 1 分钟

  constructor(algorithm: IAlgorithm) {
    this.algorithm = algorithm;
  }

  /** 初始化算法 */
  Initialize(): void {
    // 确保实现了 Initialize
    if (typeof (this.algorithm as any).Initialize !== 'function') {
      throw new Error('Algorithm must implement Initialize()');
    }

    (this.algorithm as QCAlgorithm).Initialize();
    (this.algorithm as QCAlgorithm).isInitialized = true;
    console.log(`[AlgorithmManager] Algorithm initialized: ${this.algorithm.name}`);
  }

  /** 开始运行 */
  Start(): void {
    if (!(this.algorithm as QCAlgorithm).isInitialized) {
      this.Initialize();
    }
    this.isRunning = true;
    console.log('[AlgorithmManager] Algorithm started');
  }

  /** 停止运行 */
  Stop(): void {
    this.isRunning = false;
    console.log('[AlgorithmManager] Algorithm stopped');
  }

  /** 处理新的 K线数据 */
  OnNewBar(symbol: string, kline: KlineData): void {
    if (!this.isRunning) return;

    // 更新缓存
    (this.algorithm as QCAlgorithm)._processNewBar(symbol, kline);

    // 创建 Slice
    const slice: Slice = {
      timestamp: kline.time,
      klines: new Map([[symbol, kline]]),
      prices: new Map([[symbol, kline.close]]),
      isNewBar: true,
    };

    // 更新账户
    (this.algorithm as QCAlgorithm)._updateAccount();

    // 调用 OnData
    this.algorithm.OnData(slice);

    // 检查是否收盘
    const date = new Date(kline.time);
    if (date.getMinutes() === 0) {
      this.algorithm.OnEndOfHour(symbol);
    }
    if (date.getHours() === 0) {
      this.algorithm.OnEndOfDay(symbol);
    }
  }
}

// ============================================
// 示例算法
// ============================================

export class MomentumAlgorithm extends QCAlgorithm {
  name = 'MomentumAlgorithm';
  private symbols: string[] = [];

  Initialize(): void {
    this.SetStartDate(2025, 1, 1);
    this.SetEndDate(2025, 12, 31);
    this.SetCash(10000);
    this.SetBrokerageModel('Binance');

    // 订阅交易对
    this.symbols = ['BTCUSDT', 'ETHUSDT'];
    this.AddCryptoBulk(this.symbols, '1h');

    console.log(`[${this.name}] Initialized with ${this.symbols.join(', ')}`);
  }

  OnData(slice: Slice): void {
    for (const symbol of this.symbols) {
      const history = this.History(symbol, 20);
      if (history.length < 20) continue;

      // 计算简单动量
      const currentPrice = this.CurrentPrice(symbol);
      const oldPrice = history[0].close;
      const momentum = (currentPrice - oldPrice) / oldPrice;

      // 动量策略
      if (momentum > 0.02) {
        this.SetHoldings(symbol, 0.1);
      } else if (momentum < -0.02) {
        this.Liquidate(symbol);
      }
    }
  }

  OnEndOfDay(symbol?: string): void {
    console.log(`[${this.name}] End of day: ${new Date().toISOString()}`);
    this._updateAccount();
    console.log(`[${this.name}] Portfolio value: ${this.account.portfolioValue.toFixed(2)}`);
  }
}
