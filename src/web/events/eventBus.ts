/**
 * Copyright 2026 NEMT Lab
 *
 * 事件总线 - Store 间通信的核心机制
 *
 * 设计原则：
 * 1. 发布/订阅模式
 * 2. 类型安全
 * 3. 异步支持
 * 4. 调试友好
 *
 * 注意：使用简单的 TypeScript 实现，避免外部依赖
 */

// ============================================
// 事件类型定义
// ============================================

export enum EventType {
  // 策略事件
  STRATEGY_CREATED = 'strategy:created',
  STRATEGY_UPDATED = 'strategy:updated',
  STRATEGY_DELETED = 'strategy:deleted',
  STRATEGY_SELECTED = 'strategy:selected',
  STRATEGY_STATUS_CHANGED = 'strategy:status_changed',

  // 胶囊事件
  CAPSULE_STATUS_CHANGED = 'capsule:status_changed',
  CAPSULE_INSTANCE_UPDATED = 'capsule:instance_updated',
  CAPSULE_ERROR = 'capsule:error',

  // 市场数据事件
  MARKET_PRICE_UPDATED = 'market:price_updated',
  MARKET_CONNECTION_CHANGED = 'market:connection_changed',
  MARKET_ERROR = 'market:error',

  // UI 事件
  VIEW_CHANGED = 'ui:view_changed',
  THEME_CHANGED = 'ui:theme_changed',
  SIDEBAR_TOGGLED = 'ui:sidebar_toggled',
  COMMAND_PALETTE_TOGGLED = 'ui:command_palette_toggled',

  // 平台事件
  PLATFORM_INITIALIZED = 'platform:initialized',
  PLATFORM_ERROR = 'platform:error',
  PLATFORM_RESET = 'platform:reset',
}

// ============================================
// 事件数据接口
// ============================================

export interface StrategyCreatedPayload {
  strategyId: string;
  strategyName: string;
}

export interface StrategyUpdatedPayload {
  strategyId: string;
  changes: Record<string, unknown>;
}

export interface StrategyStatusChangedPayload {
  strategyId: string;
  oldStatus: string;
  newStatus: string;
}

export interface CapsuleStatusChangedPayload {
  capsuleId: string;
  capsuleName: string;
  oldStatus: string;
  newStatus: string;
}

export interface MarketPriceUpdatedPayload {
  symbol: string;
  price: number;
  change24h: number;
  changePercent24h: number;
}

export interface ViewChangedPayload {
  oldView: string;
  newView: string;
}

export interface ThemeChangedPayload {
  oldTheme: string;
  newTheme: string;
}

// ============================================
// 简单的事件总线实现
// ============================================

type Listener<T = unknown> = (payload: T) => void;

interface EventListeners {
  [event: string]: Listener[];
}

class NEMTEventBus {
  private listeners: EventListeners = {};
  private static instance: NEMTEventBus;

  private constructor() {
    // 私有构造函数
  }

  static getInstance(): NEMTEventBus {
    if (!NEMTEventBus.instance) {
      NEMTEventBus.instance = new NEMTEventBus();
    }
    return NEMTEventBus.instance;
  }

  // ============================================
  // 基础方法
  // ============================================

  /**
   * 订阅事件
   */
  on<T = unknown>(event: string, listener: Listener<T>): () => void {
    if (!this.listeners[event]) {
      this.listeners[event] = [];
    }
    this.listeners[event].push(listener as Listener);

    // 返回取消订阅函数
    return () => {
      this.off(event, listener);
    };
  }

  /**
   * 只订阅一次
   */
  once<T = unknown>(event: string, listener: Listener<T>): void {
    const wrapper: Listener<T> = (payload) => {
      this.off(event, wrapper);
      listener(payload);
    };
    this.on(event, wrapper);
  }

  /**
   * 取消订阅
   */
  off<T = unknown>(event: string, listener: Listener<T>): void {
    if (!this.listeners[event]) return;
    this.listeners[event] = this.listeners[event].filter(l => l !== listener);
  }

  /**
   * 发布事件
   */
  emit<T = unknown>(event: string, payload?: T): void {
    // 调试模式下打印事件
    if (typeof window !== 'undefined' && (window as any).__NEMT_DEBUG__) {
      console.log(`[EventBus] ${event}`, payload);
    }

    if (!this.listeners[event]) return;
    this.listeners[event].forEach(listener => {
      try {
        listener(payload);
      } catch (error) {
        console.error(`[EventBus] Error in listener for ${event}:`, error);
      }
    });
  }

  /**
   * 订阅指定次数后自动取消
   */
  subscribe<T = unknown>(event: string, listener: Listener<T>, count: number): () => void {
    let received = 0;

    const wrapper: Listener<T> = (payload) => {
      received++;
      listener(payload);

      if (received >= count) {
        this.off(event, wrapper);
      }
    };

    return this.on(event, wrapper);
  }

  /**
   * 异步订阅，返回 Promise
   */
  waitFor<T = unknown>(event: string, timeout = 5000): Promise<T> {
    return new Promise((resolve, reject) => {
      const timer = setTimeout(() => {
        this.off(event, wrapper as Listener);
        reject(new Error(`Timeout waiting for event: ${event}`));
      }, timeout);

      const wrapper: Listener<T> = (payload) => {
        clearTimeout(timer);
        this.off(event, wrapper);
        resolve(payload as T);
      };

      this.on(event, wrapper);
    });
  }

  // ============================================
  // 调试和工具方法
  // ============================================

  /**
   * 获取事件监听器数量
   */
  listenerCount(event: string): number {
    return this.listeners[event]?.length || 0;
  }

  /**
   * 获取所有订阅的事件类型
   */
  eventNames(): string[] {
    return Object.keys(this.listeners).filter(e => this.listeners[e].length > 0);
  }

  /**
   * 清除所有监听器
   */
  removeAllListeners(): void {
    this.listeners = {};
  }

  /**
   * 打印所有事件统计
   */
  getStats(): Record<string, number> {
    const stats: Record<string, number> = {};
    this.eventNames().forEach(event => {
      stats[event] = this.listenerCount(event);
    });
    return stats;
  }
}

// ============================================
// 导出单例
// ============================================

export const eventBus = NEMTEventBus.getInstance();
