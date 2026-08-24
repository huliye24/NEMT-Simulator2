/**
 * Copyright 2026 NEMT Lab
 *
 * NEMT Base Gateway
 * 借鉴 vnpy gateway 设计
 */

import { EventEngine, TickData, BarData, OrderData, TradeData, PositionData, AccountData } from '../event/eventEngine';

// ============================================
// 交易所枚举
// ============================================

export type Exchange =
  | 'BINANCE'
  | 'OKX'
  | 'HUOBI'
  | 'BITGET'
  | 'BYBIT'
  | 'GATEIO'
  | 'COINBASE'
  | 'MEXC'
  | 'KUCION'
  | 'NASDAQ'
  | 'NYSE'
  | 'SSE'
  | 'SZSE'
  | 'DCE'
  | 'CZCE'
  | 'CFFEX'
  | 'SHFE';

// ============================================
// 网关配置
// ============================================

export interface GatewaySetting {
  /** API Key */
  apiKey?: string;
  /** 密钥 */
  secretKey?: string;
  /** 密码 */
  password?: string;
  /** 经纪商 */
  broker?: string;
  /** 交易 API Key */
  tradeApiKey?: string;
  /** 交易密钥 */
  tradeSecretKey?: string;
  /** 代理地址 */
  proxyHost?: string;
  /** 代理端口 */
  proxyPort?: number;
  /** 其他设置 */
  [key: string]: unknown;
}

// ============================================
// 连接状态
// ============================================

export type ConnectionStatus = 'disconnected' | 'connecting' | 'connected' | 'authenticated';

// ============================================
// 订阅请求
// ============================================

export interface SubscribeRequest {
  symbol: string;
  exchange: Exchange;
}

// ============================================
// 订单请求
// ============================================

export interface OrderRequest {
  symbol: string;
  exchange: Exchange;
  direction: 'long' | 'short';
  type: 'limit' | 'market' | 'stop';
  volume: number;
  price?: number;
  stopPrice?: number;
  lock?: boolean;
  netting?: boolean;
}

// ============================================
// 撤单请求
// ============================================

export interface CancelRequest {
  orderId: string;
  symbol: string;
  exchange: Exchange;
}

// ============================================
// 查询请求
// ============================================

export interface QueryRequest {
  orderId?: string;
  symbol?: string;
  exchange?: Exchange;
}

// ============================================
// 历史数据请求
// ============================================

export interface HistoryRequest {
  symbol: string;
  exchange: Exchange;
  interval: string;
  start: number;
  end: number;
}

// ============================================
// BaseGateway (借鉴 vnpy)
// ============================================

export abstract class BaseGateway {
  /** 网关名称 */
  abstract gatewayName: string;

  /** 网关类型 */
  gatewayType: 'bitcoin' | 'stock' | 'futures' | 'option' | 'forex' | 'crypto' = 'crypto';

  /** 默认设置 */
  defaultSetting: Record<string, { type: string; default?: unknown }> = {};

  /** 支持的交易所 */
  exchanges: Exchange[] = [];

  /** 事件引擎 */
  protected eventEngine: EventEngine;

  /** 连接状态 */
  protected status: ConnectionStatus = 'disconnected';

  /** 订阅的合约 */
  protected subscribedSymbols: Set<string> = new Set();

  constructor(eventEngine: EventEngine) {
    this.eventEngine = eventEngine;
  }

  // -----------------------------------------
  // 连接
  // -----------------------------------------

  /** 连接 */
  async connect(setting: GatewaySetting): Promise<void> {
    console.log(`[${this.gatewayName}] Connecting...`);
    this.status = 'connecting';
    await this.onConnect(setting);
    this.status = 'connected';
    console.log(`[${this.gatewayName}] Connected`);
  }

  /** 断开连接 */
  async disconnect(): Promise<void> {
    console.log(`[${this.gatewayName}] Disconnecting...`);
    await this.onDisconnect();
    this.status = 'disconnected';
    this.subscribedSymbols.clear();
    console.log(`[${this.gatewayName}] Disconnected`);
  }

  /** 获取状态 */
  getStatus(): ConnectionStatus {
    return this.status;
  }

  // -----------------------------------------
  // 订阅
  // -----------------------------------------

  /** 订阅行情 */
  subscribe(request: SubscribeRequest): void {
    const key = `${request.symbol}.${request.exchange}`;
    if (this.subscribedSymbols.has(key)) {
      return;
    }

    this.subscribedSymbols.add(key);
    this.onSubscribe(request);
  }

  /** 取消订阅 */
  unsubscribe(request: SubscribeRequest): void {
    const key = `${request.symbol}.${request.exchange}`;
    if (!this.subscribedSymbols.has(key)) {
      return;
    }

    this.subscribedSymbols.delete(key);
    this.onUnsubscribe(request);
  }

  // -----------------------------------------
  // 交易
  // -----------------------------------------

  /** 发送订单 */
  async sendOrder(request: OrderRequest): Promise<string | null> {
    return this.onSendOrder(request);
  }

  /** 取消订单 */
  async cancelOrder(request: CancelRequest): Promise<boolean> {
    return this.onCancelOrder(request);
  }

  /** 批量取消订单 */
  async cancelOrders(requests: CancelRequest[]): Promise<void> {
    await Promise.all(requests.map((r) => this.cancelOrder(r)));
  }

  // -----------------------------------------
  // 查询
  // -----------------------------------------

  /** 查询账户 */
  async queryAccount(): Promise<void> {
    return this.onQueryAccount();
  }

  /** 查询持仓 */
  async queryPosition(): Promise<void> {
    return this.onQueryPosition();
  }

  /** 查询历史数据 */
  async queryHistory(request: HistoryRequest): Promise<BarData[]> {
    return this.onQueryHistory(request);
  }

  /** 查询订单 */
  async queryOrder(request: QueryRequest): Promise<void> {
    return this.onQueryOrder(request);
  }

  // -----------------------------------------
  // 事件推送 (借鉴 vnpy)
  // -----------------------------------------

  /**
   * 推送 Tick
   */
  protected onTick(tick: TickData): void {
    tick.vtSymbol = `${tick.symbol}.${tick.exchange}`;
    this.eventEngine.publish('tick', tick);
    this.eventEngine.publish(`tick.${tick.vtSymbol}`, tick);
  }

  /**
   * 推送 Bar
   */
  protected onBar(bar: BarData): void {
    bar.vtSymbol = `${bar.symbol}.${bar.exchange}`;
    this.eventEngine.publish('bar', bar);
  }

  /**
   * 推送订单
   */
  protected onOrder(order: OrderData): void {
    order.vtOrderId = `${this.gatewayName}.${order.orderId}`;
    order.vtSymbol = `${order.symbol}.${order.exchange}`;
    this.eventEngine.publish('order', order);
    this.eventEngine.publish(`order.${order.vtOrderId}`, order);
  }

  /**
   * 推送成交
   */
  protected onTrade(trade: TradeData): void {
    trade.vtTradeId = `${this.gatewayName}.${trade.tradeId}`;
    trade.vtOrderId = `${this.gatewayName}.${trade.orderId}`;
    trade.vtSymbol = `${trade.symbol}.${trade.exchange}`;
    this.eventEngine.publish('trade', trade);
  }

  /**
   * 推送持仓
   */
  protected onPosition(position: PositionData): void {
    position.vtSymbol = `${position.symbol}.${position.exchange}`;
    this.eventEngine.publish('position', position);
    this.eventEngine.publish(`position.${position.vtSymbol}`, position);
  }

  /**
   * 推送账户
   */
  protected onAccount(account: AccountData): void {
    account.vtAccountId = `${this.gatewayName}.${account.accountId}`;
    this.eventEngine.publish('account', account);
    this.eventEngine.publish(`account.${account.vtAccountId}`, account);
  }

  /**
   * 推送日志
   */
  protected onLog(content: string, level: 'debug' | 'info' | 'warning' | 'error' = 'info'): void {
    this.eventEngine.publish('log', {
      content,
      level,
      timestamp: Date.now(),
      source: this.gatewayName,
    });
  }

  // -----------------------------------------
  // 抽象方法 (子类实现)
  // -----------------------------------------

  protected abstract onConnect(setting: GatewaySetting): Promise<void>;
  protected abstract onDisconnect(): Promise<void>;
  protected abstract onSubscribe(request: SubscribeRequest): void;
  protected abstract onUnsubscribe(request: SubscribeRequest): void;
  protected abstract onSendOrder(request: OrderRequest): Promise<string | null>;
  protected abstract onCancelOrder(request: CancelRequest): Promise<boolean>;
  protected abstract onQueryAccount(): Promise<void>;
  protected abstract onQueryPosition(): Promise<void>;
  protected abstract onQueryHistory(request: HistoryRequest): Promise<BarData[]>;
  protected onQueryOrder(_request: QueryRequest): Promise<void> {
    return Promise.resolve();
  }
}

// ============================================
// Binance Gateway
// ============================================

export class BinanceGateway extends BaseGateway {
  gatewayName = 'Binance';
  gatewayType = 'crypto';
  exchanges: Exchange[] = ['BINANCE'];

  defaultSetting = {
    apiKey: { type: 'string' },
    secretKey: { type: 'string' },
    proxyHost: { type: 'string' },
    proxyPort: { type: 'int' },
  };

  private ws: WebSocket | null = null;
  private restUrl = 'https://api.binance.com/api/v3';
  private wsUrl = 'wss://stream.binance.com:9443/ws';

  protected async onConnect(setting: GatewaySetting): Promise<void> {
    // 初始化 REST API
    this.restUrl = setting.testnet ? 'https://testnet.binance.vision/api/v3' : this.restUrl;

    // 连接 WebSocket
    this.connectWebSocket();
  }

  protected async onDisconnect(): Promise<void> {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  protected onSubscribe(request: SubscribeRequest): void {
    const symbol = request.symbol.toLowerCase();
    const stream = `${symbol}@ticker`;

    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({
        method: 'SUBSCRIBE',
        params: [stream],
        id: Date.now(),
      }));
    }
  }

  protected onUnsubscribe(request: SubscribeRequest): void {
    const symbol = request.symbol.toLowerCase();
    const stream = `${symbol}@ticker`;

    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({
        method: 'UNSUBSCRIBE',
        params: [stream],
        id: Date.now(),
      }));
    }
  }

  protected async onSendOrder(request: OrderRequest): Promise<string | null> {
    const symbol = request.symbol.replace('/', '');
    const side = request.direction === 'long' ? 'BUY' : 'SELL';
    const type = request.type.toUpperCase();

    const params: Record<string, string> = {
      symbol,
      side,
      type,
      quantity: request.volume.toString(),
      timestamp: Date.now().toString(),
    };

    if (request.type === 'limit' && request.price) {
      params.price = request.price.toString();
      params.timeInForce = 'GTC';
    }

    // 实际交易需要签名
    this.onLog(`Sending order: ${side} ${request.volume} ${request.symbol} @ ${request.price || 'MARKET'}`);

    return `order_${Date.now()}`;
  }

  protected async onCancelOrder(request: CancelRequest): Promise<boolean> {
    this.onLog(`Cancelling order: ${request.orderId}`);
    return true;
  }

  protected async onQueryAccount(): Promise<void> {
    this.onAccount({
      accountId: 'spot',
      vtAccountId: `${this.gatewayName}.spot`,
      name: 'Spot Account',
      type: 'spot',
      balance: 10000,
      available: 10000,
      pnl: 0,
      frozen: 0,
    });
  }

  protected async onQueryPosition(): Promise<void> {
    // 空实现
  }

  protected async onQueryHistory(request: HistoryRequest): Promise<BarData[]> {
    const symbol = request.symbol.replace('/', '');
    const interval = this.convertInterval(request.interval);

    const url = `${this.restUrl}/klines?symbol=${symbol}&interval=${interval}&startTime=${request.start}&endTime=${request.end}&limit=1000`;

    const response = await fetch(url);
    const data = await response.json();

    return data.map((k: any[]) => ({
      symbol: request.symbol,
      exchange: request.exchange,
      vtSymbol: `${request.symbol}.${request.exchange}`,
      timestamp: k[0],
      interval: request.interval,
      openPrice: parseFloat(k[1]),
      highPrice: parseFloat(k[2]),
      lowPrice: parseFloat(k[3]),
      closePrice: parseFloat(k[4]),
      volume: parseFloat(k[5]),
      turnover: parseFloat(k[7]),
    }));
  }

  private connectWebSocket(): void {
    const streams = Array.from(this.subscribedSymbols)
      .map((s) => `${s.toLowerCase()}@ticker`);

    const wsUrl = streams.length > 0
      ? `wss://stream.binance.com:9443/stream?streams=${streams.join('/')}`
      : this.wsUrl;

    this.ws = new WebSocket(wsUrl);

    this.ws.onopen = () => {
      this.status = 'authenticated';
      this.onLog('WebSocket connected');
    };

    this.ws.onmessage = (event) => {
      const data = JSON.parse(event.data);

      if (data.e === '24hrTicker') {
        this.onTick({
          symbol: data.s.replace(/USDT$/, ''),
          exchange: 'BINANCE',
          vtSymbol: data.s,
          timestamp: data.E,
          name: data.s,
          lastPrice: parseFloat(data.c),
          openPrice: parseFloat(data.o),
          highPrice: parseFloat(data.h),
          lowPrice: parseFloat(data.l),
          volume: parseFloat(data.v),
          turnover: parseFloat(data.q),
          bidPrice1: parseFloat(data.b),
          bidVolume1: parseFloat(data.B),
          askPrice1: parseFloat(data.a),
          askVolume1: parseFloat(data.A),
        });
      }
    };

    this.ws.onerror = (error) => {
      this.onLog(`WebSocket error: ${error}`, 'error');
    };

    this.ws.onclose = () => {
      this.onLog('WebSocket disconnected');
      // 自动重连
      setTimeout(() => this.connectWebSocket(), 5000);
    };
  }

  private convertInterval(interval: string): string {
    const map: Record<string, string> = {
      '1m': '1m', '5m': '5m', '15m': '15m', '30m': '30m',
      '1h': '1h', '4h': '4h', '1d': '1d', '1w': '1w',
    };
    return map[interval] || '1h';
  }
}

// ============================================
// 网关工厂
// ============================================

export const gateways: Record<string, new (ee: EventEngine) => BaseGateway> = {
  Binance: BinanceGateway,
};

export function createGateway(
  name: string,
  eventEngine: EventEngine
): BaseGateway | null {
  const GatewayClass = gateways[name];
  if (!GatewayClass) {
    return null;
  }
  return new GatewayClass(eventEngine);
}
