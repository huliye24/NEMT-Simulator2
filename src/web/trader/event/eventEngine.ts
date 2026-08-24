/**
 * Copyright 2026 NEMT Lab
 *
 * NEMT Event Engine
 * 借鉴 vnpy event engine
 *
 * 核心概念：
 * - Event: 事件对象
 * - EventEngine: 事件引擎
 * - EventHandler: 事件处理器
 */

import { EventEmitter } from 'events';

// ============================================
// 事件类型
// ============================================

export type EventType =
  // 市场数据
  | 'tick'
  | 'bar'
  | 'orderbook'

  // 交易
  | 'order'
  | 'trade'
  | 'position'
  | 'account'

  // 策略
  | 'signal'
  | 'strategy'

  // 系统
  | 'log'
  | 'error'
  | 'timer'

  // 自定义
  | string;

// ============================================
// 事件对象
// ============================================

export interface Event<T = unknown> {
  /** 事件类型 */
  type: EventType;
  /** 事件数据 */
  data: T;
  /** 事件时间戳 */
  timestamp: number;
}

// ============================================
// 事件处理器
// ============================================

export type EventHandler<T = unknown> = (event: Event<T>) => void | Promise<void>;

// ============================================
// 事件引擎 (借鉴 vnpy EventEngine)
// ============================================

export class EventEngine extends EventEmitter {
  /** 事件处理器映射 */
  private handlers: Map<EventType, Set<EventHandler>> = new Map();

  /** 是否运行中 */
  private active: boolean = false;

  /** 通用处理器 */
  private generalHandlers: Set<EventHandler> = new Set();

  /** 统计 */
  private stats = {
    eventsProcessed: 0,
    eventsByType: new Map<string, number>(),
  };

  constructor() {
    super();
    this.setMaxListeners(100);
  }

  // -----------------------------------------
  // 生命周期
  // -----------------------------------------

  /** 启动事件引擎 */
  start(): void {
    if (this.active) {
      console.warn('[EventEngine] Already started');
      return;
    }

    this.active = true;
    console.log('[EventEngine] Started');
  }

  /** 停止事件引擎 */
  stop(): void {
    if (!this.active) {
      return;
    }

    this.active = false;
    this.removeAllListeners();
    this.handlers.clear();
    this.generalHandlers.clear();

    console.log(`[EventEngine] Stopped. Processed ${this.stats.eventsProcessed} events.`);
  }

  /** 是否运行中 */
  isActive(): boolean {
    return this.active;
  }

  // -----------------------------------------
  // 订阅/取消订阅
  // -----------------------------------------

  /**
   * 注册事件处理器
   */
  register(
    type: EventType,
    handler: EventHandler,
    strategyId?: string
  ): () => void {
    if (!this.handlers.has(type)) {
      this.handlers.set(type, new Set());
    }

    this.handlers.get(type)!.add(handler);

    console.log(`[EventEngine] Registered handler for: ${type}${strategyId ? ` (${strategyId})` : ''}`);

    // 返回取消订阅函数
    return () => this.unregister(type, handler);
  }

  /**
   * 取消注册事件处理器
   */
  unregister(type: EventType, handler: EventHandler): void {
    const handlers = this.handlers.get(type);
    if (handlers) {
      handlers.delete(handler);
      if (handlers.size === 0) {
        this.handlers.delete(type);
      }
    }
  }

  /**
   * 注册通用处理器 (处理所有事件)
   */
  registerGeneralHandler(handler: EventHandler): () => void {
    this.generalHandlers.add(handler);
    return () => this.generalHandlers.delete(handler);
  }

  /**
   * 清除所有处理器
   */
  clear(): void {
    this.handlers.clear();
    this.generalHandlers.clear();
    console.log('[EventEngine] All handlers cleared');
  }

  // -----------------------------------------
  // 事件发布
  // -----------------------------------------

  /**
   * 发布事件
   */
  publish<T = unknown>(type: EventType, data: T): void {
    if (!this.active) {
      return;
    }

    const event: Event<T> = {
      type,
      data,
      timestamp: Date.now(),
    };

    // 统计
    this.stats.eventsProcessed++;
    const count = this.stats.eventsByType.get(type) || 0;
    this.stats.eventsByType.set(type, count + 1);

    // 调用类型特定处理器
    const handlers = this.handlers.get(type);
    if (handlers) {
      for (const handler of handlers) {
        try {
          const result = handler(event);
          if (result instanceof Promise) {
            result.catch((error) => {
              console.error(`[EventEngine] Async handler error:`, error);
            });
          }
        } catch (error) {
          console.error(`[EventEngine] Handler error:`, error);
        }
      }
    }

    // 调用通用处理器
    for (const handler of this.generalHandlers) {
      try {
        const result = handler(event);
        if (result instanceof Promise) {
          result.catch((error) => {
            console.error(`[EventEngine] Async general handler error:`, error);
          });
        }
      } catch (error) {
        console.error(`[EventEngine] General handler error:`, error);
      }
    }
  }

  /**
   * 异步发布事件
   */
  async publishAsync<T = unknown>(type: EventType, data: T): Promise<void> {
    const event: Event<T> = {
      type,
      data,
      timestamp: Date.now(),
    };

    const handlers = this.handlers.get(type);
    if (handlers) {
      await Promise.all(
        Array.from(handlers).map((handler) =>
          Promise.resolve(handler(event)).catch((error) => {
            console.error(`[EventEngine] Handler error:`, error);
          })
        )
      );
    }
  }

  // -----------------------------------------
  // 便捷方法
  // -----------------------------------------

  /**
   * 发布 Tick 事件
   */
  publishTick(tick: TickData): void {
    this.publish('tick', tick);
  }

  /**
   * 发布 Bar 事件
   */
  publishBar(bar: BarData): void {
    this.publish('bar', bar);
  }

  /**
   * 发布订单事件
   */
  publishOrder(order: OrderData): void {
    this.publish('order', order);
  }

  /**
   * 发布成交事件
   */
  publishTrade(trade: TradeData): void {
    this.publish('trade', trade);
  }

  /**
   * 发布持仓事件
   */
  publishPosition(position: PositionData): void {
    this.publish('position', position);
  }

  /**
   * 发布信号事件
   */
  publishSignal(signal: SignalData): void {
    this.publish('signal', signal);
  }

  /**
   * 发布日志
   */
  publishLog(log: LogData): void {
    this.publish('log', log);
  }

  // -----------------------------------------
  // 统计
  // -----------------------------------------

  /**
   * 获取统计信息
   */
  getStats(): {
    eventsProcessed: number;
    eventsByType: Record<string, number>;
    handlerCount: number;
  } {
    let handlerCount = 0;
    for (const handlers of this.handlers.values()) {
      handlerCount += handlers.size;
    }
    handlerCount += this.generalHandlers.size;

    return {
      eventsProcessed: this.stats.eventsProcessed,
      eventsByType: Object.fromEntries(this.stats.eventsByType),
      handlerCount,
    };
  }

  /**
   * 打印统计信息
   */
  printStats(): void {
    const stats = this.getStats();
    console.log('\n=== EventEngine Stats ===');
    console.log(`Total events: ${stats.eventsProcessed}`);
    console.log(`Active handlers: ${stats.handlerCount}`);
    console.log('Events by type:');
    for (const [type, count] of Object.entries(stats.eventsByType).sort((a, b) => b[1] - a[1])) {
      console.log(`  ${type}: ${count}`);
    }
    console.log('========================\n');
  }
}

// ============================================
// 数据类型 (借鉴 vnpy object.py)
// ============================================

export interface TickData {
  /** 股票代码 */
  symbol: string;
  /** 交易所代码 */
  exchange: string;
  /** 完整代码 (symbol.exchange) */
  vtSymbol: string;
  /** 时间戳 */
  timestamp: number;
  /** 名称 */
  name: string;
  /** 最新价 */
  lastPrice: number;
  /** 开盘价 */
  openPrice: number;
  /** 最高价 */
  highPrice: number;
  /** 最低价 */
  lowPrice: number;
  /** 成交量 */
  volume: number;
  /** 成交额 */
  turnover: number;
  /** 买一价 */
  bidPrice1: number;
  /** 买一量 */
  bidVolume1: number;
  /** 卖一价 */
  askPrice1: number;
  /** 卖一量 */
  askVolume1: number;
}

export interface BarData {
  /** 股票代码 */
  symbol: string;
  /** 交易所代码 */
  exchange: string;
  /** 完整代码 */
  vtSymbol: string;
  /** 时间戳 */
  timestamp: number;
  /** 周期 */
  interval: string;
  /** 开盘价 */
  openPrice: number;
  /** 最高价 */
  highPrice: number;
  /** 最低价 */
  lowPrice: number;
  /** 收盘价 */
  closePrice: number;
  /** 成交量 */
  volume: number;
  /** 成交额 */
  turnover: number;
}

export interface OrderData {
  /** 订单编号 */
  orderId: string;
  /** 完整编号 */
  vtOrderId: string;
  /** 股票代码 */
  symbol: string;
  /** 交易所代码 */
  exchange: string;
  /** 完整代码 */
  vtSymbol: string;
  /** 方向 */
  direction: 'long' | 'short';
  /** 开平 */
  offset: 'open' | 'close' | 'closetoday' | 'closeyesterday';
  /** 订单类型 */
  type: 'limit' | 'market' | 'stop';
  /** 价格 */
  price: number;
  /** 数量 */
  volume: number;
  /** 状态 */
  status: 'submitted' | 'partial' | 'filled' | 'cancelled' | 'rejected';
  /** 成交数量 */
  tradedVolume: number;
  /** 时间戳 */
  timestamp: number;
}

export interface TradeData {
  /** 成交编号 */
  tradeId: string;
  /** 完整编号 */
  vtTradeId: string;
  /** 订单编号 */
  orderId: string;
  /** 完整编号 */
  vtOrderId: string;
  /** 股票代码 */
  symbol: string;
  /** 交易所代码 */
  exchange: string;
  /** 完整代码 */
  vtSymbol: string;
  /** 方向 */
  direction: 'long' | 'short';
  /** 开平 */
  offset: 'open' | 'close' | 'closetoday' | 'closeyesterday';
  /** 价格 */
  price: number;
  /** 数量 */
  volume: number;
  /** 时间戳 */
  timestamp: number;
}

export interface PositionData {
  /** 股票代码 */
  symbol: string;
  /** 交易所代码 */
  exchange: string;
  /** 完整代码 */
  vtSymbol: string;
  /** 方向 */
  direction: 'long' | 'short';
  /** 持仓数量 */
  volume: number;
  /** 可用数量 */
  available: number;
  /** 持仓均价 */
  price: number;
  /** 浮动盈亏 */
  pnl: number;
  /** 昨日持仓 */
  ydVolume: number;
}

export interface AccountData {
  /** 账户编号 */
  accountId: string;
  /** 完整编号 */
  vtAccountId: string;
  /** 账户名 */
  name: string;
  /** 账户类型 */
  type: string;
  /** 余额 */
  balance: number;
  /** 可用余额 */
  available: number;
  /** 持仓盈亏 */
  pnl: number;
  /** 冻结金额 */
  frozen: number;
}

export interface SignalData {
  /** 信号 ID */
  signalId: string;
  /** 策略 ID */
  strategyId: string;
  /** 股票代码 */
  symbol: string;
  /** 信号方向 */
  direction: 'long' | 'short' | 'exit';
  /** 信号强度 (0-1) */
  strength: number;
  /** 置信度 (0-1) */
  confidence: number;
  /** 目标价格 */
  targetPrice?: number;
  /** 止损价格 */
  stopLoss?: number;
  /** 止盈价格 */
  takeProfit?: number;
  /** 时间戳 */
  timestamp: number;
}

export interface LogData {
  /** 日志内容 */
  content: string;
  /** 日志级别 */
  level: 'debug' | 'info' | 'warning' | 'error';
  /** 时间戳 */
  timestamp: number;
  /** 来源 */
  source?: string;
}

// ============================================
// 全局事件引擎实例
// ============================================

let globalEventEngine: EventEngine | null = null;

export function getEventEngine(): EventEngine {
  if (!globalEventEngine) {
    globalEventEngine = new EventEngine();
    globalEventEngine.start();
  }
  return globalEventEngine;
}

// ============================================
// 便捷函数
// ============================================

/**
 * 订阅事件
 */
export function on<T = unknown>(
  type: EventType,
  handler: EventHandler<T>,
  engine?: EventEngine
): () => void {
  const ee = engine || getEventEngine();
  return ee.register(type, handler as EventHandler);
}

/**
 * 取消订阅
 */
export function off<T = unknown>(
  type: EventType,
  handler: EventHandler<T>,
  engine?: EventEngine
): void {
  const ee = engine || getEventEngine();
  ee.unregister(type, handler as EventHandler);
}

/**
 * 发布事件
 */
export function emit<T = unknown>(type: EventType, data: T, engine?: EventEngine): void {
  const ee = engine || getEventEngine();
  ee.publish(type, data);
}

/**
 * 一次性订阅
 */
export function once<T = unknown>(
  type: EventType,
  handler: EventHandler<T>,
  engine?: EventEngine
): () => void {
  const ee = engine || getEventEngine();

  const wrappedHandler: EventHandler<T> = (event) => {
    const result = handler(event);
    ee.unregister(type, wrappedHandler);
    return result;
  };

  return ee.register(type, wrappedHandler);
}
