/**
 * Copyright 2026 NEMT Lab
 *
 * NEMT Main Engine
 * 借鉴 vnpy MainEngine 设计
 *
 * 核心概念：
 * - MainEngine: 主引擎，统一管理 Gateway、Engine、App
 * - BaseEngine: 功能引擎基类
 * - BaseApp: 应用模块基类
 */

import { EventEngine, Event } from '../event/eventEngine';
import { BaseGateway, GatewaySetting, createGateway } from '../gateway/baseGateway';
import { logger, LogLevel } from './logger';

// ============================================
// BaseEngine
// ============================================

export abstract class BaseEngine {
  /** 引擎名称 */
  abstract engineName: string;

  /** 主引擎 */
  protected mainEngine: MainEngine;

  /** 事件引擎 */
  protected eventEngine: EventEngine;

  constructor(mainEngine: MainEngine, eventEngine: EventEngine) {
    this.mainEngine = mainEngine;
    this.eventEngine = eventEngine;
  }

  /** 关闭引擎 */
  close(): void {
    // 子类可覆盖
  }
}

// ============================================
// BaseApp
// ============================================

export abstract class BaseApp {
  /** 应用名称 */
  abstract appName: string;

  /** 应用图标 */
  appIcon: string = '';

  /** 优先级 */
  priority: number = 0;

  /** 是否显示在 UI */
  display: boolean = true;

  /** 主引擎 */
  protected mainEngine: MainEngine;

  /** 事件引擎 */
  protected eventEngine: EventEngine;

  constructor(mainEngine: MainEngine, eventEngine: EventEngine) {
    this.mainEngine = mainEngine;
    this.eventEngine = eventEngine;
  }

  /** 初始化 */
  initEngine(): void {
    this.onInit();
  }

  /** 开始 */
  start(): void {
    this.onStart();
  }

  /** 停止 */
  stop(): void {
    this.onStop();
  }

  /** 关闭 */
  close(): void {
    this.onClose();
  }

  protected onInit(): void {}
  protected onStart(): void {}
  protected onStop(): void {}
  protected onClose(): void {}
}

// ============================================
// MainEngine
// ============================================

export class MainEngine {
  /** 事件引擎 */
  eventEngine: EventEngine;

  /** 网关列表 */
  gateways: Map<string, BaseGateway> = new Map();

  /** 引擎列表 */
  engines: Map<string, BaseEngine> = new Map();

  /** 应用列表 */
  apps: Map<string, BaseApp> = new Map();

  /** 数据引擎 */
  dataEngine: DataEngine;

  /** 交易引擎 */
  tradeEngine: TradeEngine;

  /** 信号引擎 */
  signalEngine: SignalEngine;

  /** 账户信息 */
  accounts: Map<string, AccountInfo> = new Map();

  /** 持仓信息 */
  positions: Map<string, PositionInfo> = new Map();

  constructor(eventEngine?: EventEngine) {
    this.eventEngine = eventEngine || new EventEngine();
    this.eventEngine.start();

    // 初始化内置引擎
    this.dataEngine = new DataEngine(this, this.eventEngine);
    this.tradeEngine = new TradeEngine(this, this.eventEngine);
    this.signalEngine = new SignalEngine(this, this.eventEngine);

    // 注册内置引擎
    this.engines.set('data', this.dataEngine);
    this.engines.set('trade', this.tradeEngine);
    this.engines.set('signal', this.signalEngine);

    console.log('[MainEngine] Initialized');
  }

  // -----------------------------------------
  // Gateway 管理
  // -----------------------------------------

  /**
   * 添加网关
   */
  addGateway(name: string, gateway: BaseGateway): void {
    this.gateways.set(name, gateway);
    console.log(`[MainEngine] Gateway added: ${name}`);
  }

  /**
   * 连接网关
   */
  async connect(name: string, setting: GatewaySetting = {}): Promise<boolean> {
    const gateway = this.gateways.get(name);
    if (!gateway) {
      console.error(`[MainEngine] Gateway not found: ${name}`);
      return false;
    }

    try {
      await gateway.connect(setting);

      // 订阅事件
      this.registerGatewayEvents(gateway);

      return true;
    } catch (error) {
      console.error(`[MainEngine] Failed to connect gateway ${name}:`, error);
      return false;
    }
  }

  /**
   * 断开网关
   */
  async disconnect(name: string): Promise<void> {
    const gateway = this.gateways.get(name);
    if (gateway) {
      await gateway.disconnect();
    }
  }

  /**
   * 获取网关
   */
  getGateway(name: string): BaseGateway | undefined {
    return this.gateways.get(name);
  }

  /**
   * 获取所有网关
   */
  getAllGateways(): Map<string, BaseGateway> {
    return this.gateways;
  }

  /**
   * 注册网关事件
   */
  private registerGatewayEvents(gateway: BaseGateway): void {
    this.eventEngine.register('account', (event) => {
      const account = event.data as AccountInfo;
      this.accounts.set(account.vtAccountId, account);
    });

    this.eventEngine.register('position', (event) => {
      const position = event.data as PositionInfo;
      const key = `${position.vtSymbol}.${position.direction}`;
      this.positions.set(key, position);
    });
  }

  // -----------------------------------------
  // Engine 管理
  // -----------------------------------------

  /**
   * 添加引擎
   */
  addEngine(engine: BaseEngine): void {
    this.engines.set(engine.engineName, engine);
    console.log(`[MainEngine] Engine added: ${engine.engineName}`);
  }

  /**
   * 获取引擎
   */
  getEngine<T extends BaseEngine>(name: string): T | undefined {
    return this.engines.get(name) as T | undefined;
  }

  // -----------------------------------------
  // App 管理
  // -----------------------------------------

  /**
   * 添加应用
   */
  addApp(app: BaseApp): void {
    this.apps.set(app.appName, app);
    app.initEngine();
    console.log(`[MainEngine] App added: ${app.appName}`);
  }

  /**
   * 获取应用
   */
  getApp<T extends BaseApp>(name: string): T | undefined {
    return this.apps.get(name) as T | undefined;
  }

  /**
   * 启动所有应用
   */
  startAll(): void {
    for (const app of this.apps.values()) {
      app.start();
    }
    console.log('[MainEngine] All apps started');
  }

  /**
   * 停止所有应用
   */
  stopAll(): void {
    for (const app of this.apps.values()) {
      app.stop();
    }
    console.log('[MainEngine] All apps stopped');
  }

  // -----------------------------------------
  // 数据查询
  // -----------------------------------------

  /**
   * 获取账户
   */
  getAccount(vtAccountId: string): AccountInfo | undefined {
    return this.accounts.get(vtAccountId);
  }

  /**
   * 获取所有账户
   */
  getAllAccounts(): AccountInfo[] {
    return Array.from(this.accounts.values());
  }

  /**
   * 获取持仓
   */
  getPosition(vtSymbol: string, direction: 'long' | 'short'): PositionInfo | undefined {
    return this.positions.get(`${vtSymbol}.${direction}`);
  }

  /**
   * 获取所有持仓
   */
  getAllPositions(): PositionInfo[] {
    return Array.from(this.positions.values());
  }

  // -----------------------------------------
  // 关闭
  // -----------------------------------------

  /**
   * 关闭主引擎
   */
  close(): void {
    console.log('[MainEngine] Closing...');

    // 停止所有应用
    for (const app of this.apps.values()) {
      app.close();
    }

    // 关闭所有网关
    for (const gateway of this.gateways.values()) {
      gateway.disconnect();
    }

    // 停止事件引擎
    this.eventEngine.stop();

    console.log('[MainEngine] Closed');
  }
}

// ============================================
// 数据引擎
// ============================================

export class DataEngine extends BaseEngine {
  engineName = 'DataEngine';

  /** Tick 缓存 */
  private tickCache: Map<string, TickInfo> = new Map();

  /** Bar 缓存 */
  private barCache: Map<string, BarInfo[]> = new Map();

  /** 历史数据 */
  private historyData: Map<string, BarInfo[]> = new Map();

  constructor(mainEngine: MainEngine, eventEngine: EventEngine) {
    super(mainEngine, eventEngine);

    // 订阅 Tick
    this.eventEngine.register('tick', (event) => {
      const tick = event.data as TickInfo;
      this.tickCache.set(tick.vtSymbol, tick);
    });

    // 订阅 Bar
    this.eventEngine.register('bar', (event) => {
      const bar = event.data as BarInfo;
      this.onBar(bar);
    });
  }

  /**
   * 获取最新 Tick
   */
  getTick(vtSymbol: string): TickInfo | undefined {
    return this.tickCache.get(vtSymbol);
  }

  /**
   * 获取 K 线缓存
   */
  getCachedBars(vtSymbol: string): BarInfo[] {
    return this.barCache.get(vtSymbol) || [];
  }

  /**
   * 获取历史 K 线
   */
  getHistoryBars(vtSymbol: string): BarInfo[] {
    return this.historyData.get(vtSymbol) || [];
  }

  /**
   * 加载历史数据
   */
  async loadHistory(
    gatewayName: string,
    symbol: string,
    exchange: string,
    interval: string,
    start: number,
    end: number
  ): Promise<BarInfo[]> {
    const gateway = this.mainEngine.getGateway(gatewayName);
    if (!gateway) {
      throw new Error(`Gateway not found: ${gatewayName}`);
    }

    const bars = await gateway.queryHistory({
      symbol,
      exchange: exchange as any,
      interval,
      start,
      end,
    });

    const key = `${symbol}.${exchange}.${interval}`;
    this.historyData.set(key, bars);

    return bars;
  }

  /**
   * 处理 K 线
   */
  private onBar(bar: BarInfo): void {
    const key = `${bar.vtSymbol}.${bar.interval}`;

    if (!this.barCache.has(key)) {
      this.barCache.set(key, []);
    }

    const bars = this.barCache.get(key)!;
    bars.push(bar);

    // 保留最近 1000 根
    if (bars.length > 1000) {
      bars.shift();
    }

    // 发布 Bar 事件
    this.eventEngine.publish(`bar.${bar.vtSymbol}.${bar.interval}`, bar);
  }
}

// ============================================
// 交易引擎
// ============================================

export class TradeEngine extends BaseEngine {
  engineName = 'TradeEngine';

  /** 订单映射 */
  private orderMap: Map<string, OrderInfo> = new Map();

  /** 成交映射 */
  private tradeMap: Map<string, TradeInfo> = new Map();

  /** 未完成订单数 */
  private activeOrderCount: number = 0;

  constructor(mainEngine: MainEngine, eventEngine: EventEngine) {
    super(mainEngine, eventEngine);

    // 订阅订单
    this.eventEngine.register('order', (event) => {
      const order = event.data as OrderInfo;
      this.orderMap.set(order.vtOrderId, order);

      if (order.status === 'submitted' || order.status === 'partial') {
        this.activeOrderCount++;
      } else {
        this.activeOrderCount = Math.max(0, this.activeOrderCount - 1);
      }
    });

    // 订阅成交
    this.eventEngine.register('trade', (event) => {
      const trade = event.data as TradeInfo;
      this.tradeMap.set(trade.vtTradeId, trade);
    });
  }

  /**
   * 发送订单
   */
  async sendOrder(
    gatewayName: string,
    symbol: string,
    exchange: string,
    direction: 'long' | 'short',
    volume: number,
    price: number,
    orderType: 'limit' | 'market' = 'limit'
  ): Promise<string | null> {
    const gateway = this.mainEngine.getGateway(gatewayName);
    if (!gateway) {
      logger.error(`Gateway not found: ${gatewayName}`);
      return null;
    }

    const orderId = await gateway.sendOrder({
      symbol,
      exchange: exchange as any,
      direction,
      type: orderType,
      volume,
      price,
    });

    return orderId;
  }

  /**
   * 取消订单
   */
  async cancelOrder(gatewayName: string, orderId: string, symbol: string, exchange: string): Promise<boolean> {
    const gateway = this.mainEngine.getGateway(gatewayName);
    if (!gateway) {
      return false;
    }

    return gateway.cancelOrder({ orderId, symbol, exchange: exchange as any });
  }

  /**
   * 获取订单
   */
  getOrder(vtOrderId: string): OrderInfo | undefined {
    return this.orderMap.get(vtOrderId);
  }

  /**
   * 获取所有订单
   */
  getAllOrders(): OrderInfo[] {
    return Array.from(this.orderMap.values());
  }

  /**
   * 获取活跃订单数
   */
  getActiveOrderCount(): number {
    return this.activeOrderCount;
  }
}

// ============================================
// 信号引擎
// ============================================

export class SignalEngine extends BaseEngine {
  engineName = 'SignalEngine';

  /** 信号映射 */
  private signals: Map<string, SignalInfo[]> = new Map();

  constructor(mainEngine: MainEngine, eventEngine: EventEngine) {
    super(mainEngine, eventEngine);

    // 订阅信号
    this.eventEngine.register('signal', (event) => {
      const signal = event.data as SignalInfo;
      this.onSignal(signal);
    });
  }

  /**
   * 发送信号
   */
  sendSignal(signal: SignalInfo): void {
    this.eventEngine.publish('signal', signal);
  }

  /**
   * 获取信号
   */
  getSignals(vtSymbol: string): SignalInfo[] {
    return this.signals.get(vtSymbol) || [];
  }

  /**
   * 获取最新信号
   */
  getLatestSignal(vtSymbol: string): SignalInfo | undefined {
    const signals = this.signals.get(vtSymbol);
    if (!signals || signals.length === 0) return undefined;
    return signals[signals.length - 1];
  }

  /**
   * 处理信号
   */
  private onSignal(signal: SignalInfo): void {
    const key = signal.vtSymbol;

    if (!this.signals.has(key)) {
      this.signals.set(key, []);
    }

    const signals = this.signals.get(key)!;
    signals.push(signal);

    // 保留最近 100 个
    if (signals.length > 100) {
      signals.shift();
    }
  }
}

// ============================================
// 数据类型
// ============================================

export interface TickInfo {
  symbol: string;
  exchange: string;
  vtSymbol: string;
  timestamp: number;
  name: string;
  lastPrice: number;
  openPrice: number;
  highPrice: number;
  lowPrice: number;
  volume: number;
  turnover: number;
  bidPrice1: number;
  bidVolume1: number;
  askPrice1: number;
  askVolume1: number;
}

export interface BarInfo {
  symbol: string;
  exchange: string;
  vtSymbol: string;
  timestamp: number;
  interval: string;
  openPrice: number;
  highPrice: number;
  lowPrice: number;
  closePrice: number;
  volume: number;
  turnover: number;
}

export interface OrderInfo {
  orderId: string;
  vtOrderId: string;
  symbol: string;
  exchange: string;
  vtSymbol: string;
  direction: 'long' | 'short';
  offset: string;
  type: string;
  price: number;
  volume: number;
  tradedVolume: number;
  status: string;
  timestamp: number;
}

export interface TradeInfo {
  tradeId: string;
  vtTradeId: string;
  orderId: string;
  vtOrderId: string;
  symbol: string;
  exchange: string;
  vtSymbol: string;
  direction: 'long' | 'short';
  offset: string;
  price: number;
  volume: number;
  timestamp: number;
}

export interface AccountInfo {
  accountId: string;
  vtAccountId: string;
  name: string;
  type: string;
  balance: number;
  available: number;
  pnl: number;
  frozen: number;
}

export interface PositionInfo {
  symbol: string;
  exchange: string;
  vtSymbol: string;
  direction: 'long' | 'short';
  volume: number;
  available: number;
  price: number;
  pnl: number;
  ydVolume: number;
}

export interface SignalInfo {
  signalId: string;
  strategyId: string;
  vtSymbol: string;
  direction: 'long' | 'short' | 'exit';
  strength: number;
  confidence: number;
  targetPrice?: number;
  stopLoss?: number;
  takeProfit?: number;
  timestamp: number;
}
