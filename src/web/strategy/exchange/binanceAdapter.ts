/**
 * Copyright 2026 NEMT Lab
 *
 * NEMT Exchange Adapter
 * Binance 交易所适配器
 */

import type { DataFrame, KlineData } from '../types/kline';
import type { DataProvider } from '../interfaces/IStrategy';
import CryptoJS from 'crypto-js';

// ============================================
// 配置类型
// ============================================

export interface ExchangeConfig {
  /** API Key */
  apiKey?: string;
  /** 密钥 */
  secretKey?: string;
  /** 是否测试网 */
  testnet: boolean;
  /** 交易所名称 */
  name: string;
  /** 是否支持做空 */
  canShort: boolean;
  /** 最小交易量 */
  minAmount: number;
  /** 价格精度 */
  pricePrecision: number;
  /** 数量精度 */
  amountPrecision: number;
}

// ============================================
// 订单类型
// ============================================

export interface OrderRequest {
  symbol: string;
  side: 'buy' | 'sell';
  type: 'market' | 'limit';
  amount: number;
  price?: number;
}

export interface OrderResponse {
  id: string;
  symbol: string;
  side: 'buy' | 'sell';
  type: 'market' | 'limit';
  status: 'pending' | 'filled' | 'partially_filled' | 'cancelled';
  amount: number;
  price: number;
  filledAmount: number;
  filledPrice: number;
  commission: number;
  createdAt: number;
  updatedAt: number;
}

// ============================================
// Binance 适配器
// ============================================

export class BinanceAdapter {
  private config: ExchangeConfig;
  private baseUrl: string;

  constructor(config: Partial<ExchangeConfig> = {}) {
    this.config = {
      name: 'binance',
      testnet: true,
      canShort: false,
      minAmount: 0.001,
      pricePrecision: 2,
      amountPrecision: 6,
      ...config,
    };

    this.baseUrl = this.config.testnet
      ? 'https://testnet.binance.vision/api/v3'
      : 'https://api.binance.com/api/v3';
  }

  // -----------------------------------------
  // 行情数据
  // -----------------------------------------

  /**
   * 获取 K 线数据
   */
  async getKlines(
    symbol: string,
    interval: string = '1h',
    limit: number = 100,
    startTime?: number,
    endTime?: number
  ): Promise<KlineData[]> {
    const params = new URLSearchParams({
      symbol: symbol.replace('/', ''),
      interval,
      limit: limit.toString(),
    });

    if (startTime) params.append('startTime', startTime.toString());
    if (endTime) params.append('endTime', endTime.toString());

    const response = await fetch(`${this.baseUrl}/klines?${params}`);
    if (!response.ok) {
      throw new Error(`Failed to fetch klines: ${response.statusText}`);
    }

    const data = await response.json();
    return data.map((k: any[]) => ({
      time: k[0],
      open: parseFloat(k[1]),
      high: parseFloat(k[2]),
      low: parseFloat(k[3]),
      close: parseFloat(k[4]),
      volume: parseFloat(k[5]),
    }));
  }

  /**
   * 获取当前价格
   */
  async getCurrentPrice(symbol: string): Promise<number> {
    const params = new URLSearchParams({ symbol: symbol.replace('/', '') });
    const response = await fetch(`${this.baseUrl}/ticker/price?${params}`);
    if (!response.ok) {
      throw new Error(`Failed to fetch price: ${response.statusText}`);
    }
    const data = await response.json();
    return parseFloat(data.price);
  }

  /**
   * 获取 24h 统计
   */
  async get24hrTicker(symbol: string): Promise<{
    priceChange: number;
    priceChangePercent: number;
    volume: number;
    high: number;
    low: number;
  }> {
    const params = new URLSearchParams({ symbol: symbol.replace('/', '') });
    const response = await fetch(`${this.baseUrl}/ticker/24hr?${params}`);
    if (!response.ok) {
      throw new Error(`Failed to fetch ticker: ${response.statusText}`);
    }
    const data = await response.json();
    return {
      priceChange: parseFloat(data.priceChange),
      priceChangePercent: parseFloat(data.priceChangePercent),
      volume: parseFloat(data.volume),
      high: parseFloat(data.highPrice),
      low: parseFloat(data.lowPrice),
    };
  }

  /**
   * 获取深度数据
   */
  async getOrderBook(
    symbol: string,
    limit: number = 20
  ): Promise<{ bids: [number, number][]; asks: [number, number][] }> {
    const params = new URLSearchParams({
      symbol: symbol.replace('/', ''),
      limit: limit.toString(),
    });
    const response = await fetch(`${this.baseUrl}/depth?${params}`);
    if (!response.ok) {
      throw new Error(`Failed to fetch orderbook: ${response.statusText}`);
    }
    const data = await response.json();
    return {
      bids: data.bids.map((b: [string, string]) => [parseFloat(b[0]), parseFloat(b[1])]),
      asks: data.asks.map((a: [string, string]) => [parseFloat(a[0]), parseFloat(a[1])]),
    };
  }

  // -----------------------------------------
  // 账户操作 (需要认证)
  // -----------------------------------------

  /**
   * 获取账户余额
   */
  async getBalance(): Promise<Record<string, { free: number; locked: number }>> {
    if (!this.config.apiKey || !this.config.secretKey) {
      throw new Error('API key and secret key are required for balance');
    }

    const timestamp = Date.now();
    const params = `timestamp=${timestamp}`;
    const signature = this.generateSignature(params);

    const response = await fetch(`${this.baseUrl}/account?${params}&signature=${signature}`, {
      headers: {
        'X-MBX-APIKEY': this.config.apiKey,
      },
    });

    if (!response.ok) {
      throw new Error(`Failed to fetch balance: ${response.statusText}`);
    }

    const data = await response.json();
    const balances: Record<string, { free: number; locked: number }> = {};

    for (const balance of data.balances) {
      const free = parseFloat(balance.free);
      const locked = parseFloat(balance.locked);
      if (free > 0 || locked > 0) {
        balances[balance.asset] = { free, locked };
      }
    }

    return balances;
  }

  /**
   * 下单
   */
  async placeOrder(order: OrderRequest): Promise<OrderResponse> {
    if (!this.config.apiKey || !this.config.secretKey) {
      throw new Error('API key and secret key are required for trading');
    }

    const timestamp = Date.now();
    const params: Record<string, string> = {
      symbol: order.symbol.replace('/', ''),
      side: order.side.toUpperCase(),
      type: order.type.toUpperCase(),
      quantity: order.amount.toFixed(this.config.amountPrecision),
      timestamp: timestamp.toString(),
    };

    if (order.type === 'limit' && order.price) {
      params.price = order.price.toFixed(this.config.pricePrecision);
      params.timeInForce = 'GTC';
    }

    const queryString = new URLSearchParams(params).toString();
    const signature = this.generateSignature(queryString);

    const response = await fetch(`${this.baseUrl}/order?${queryString}&signature=${signature}`, {
      method: 'POST',
      headers: {
        'X-MBX-APIKEY': this.config.apiKey,
      },
    });

    if (!response.ok) {
      throw new Error(`Failed to place order: ${response.statusText}`);
    }

    const data = await response.json();
    return this.parseOrderResponse(data);
  }

  /**
   * 撤销订单
   */
  async cancelOrder(symbol: string, orderId: string): Promise<boolean> {
    if (!this.config.apiKey || !this.config.secretKey) {
      throw new Error('API key and secret key are required');
    }

    const timestamp = Date.now();
    const params = new URLSearchParams({
      symbol: symbol.replace('/', ''),
      orderId,
      timestamp: timestamp.toString(),
    });
    const queryString = params.toString();
    const signature = this.generateSignature(queryString);

    const response = await fetch(`${this.baseUrl}/order?${queryString}&signature=${signature}`, {
      method: 'DELETE',
      headers: {
        'X-MBX-APIKEY': this.config.apiKey,
      },
    });

    return response.ok;
  }

  /**
   * 获取订单信息
   */
  async getOrder(symbol: string, orderId: string): Promise<OrderResponse> {
    if (!this.config.apiKey || !this.config.secretKey) {
      throw new Error('API key and secret key are required');
    }

    const timestamp = Date.now();
    const params = new URLSearchParams({
      symbol: symbol.replace('/', ''),
      orderId,
      timestamp: timestamp.toString(),
    });
    const queryString = params.toString();
    const signature = this.generateSignature(queryString);

    const response = await fetch(`${this.baseUrl}/order?${queryString}&signature=${signature}`, {
      headers: {
        'X-MBX-APIKEY': this.config.apiKey,
      },
    });

    if (!response.ok) {
      throw new Error(`Failed to get order: ${response.statusText}`);
    }

    const data = await response.json();
    return this.parseOrderResponse(data);
  }

  // -----------------------------------------
  // WebSocket
  // -----------------------------------------

  private ws: WebSocket | null = null;
  private wsSubscriptions: Map<string, (data: any) => void> = new Map();

  /**
   * 连接 WebSocket
   */
  connectWebSocket(onMessage: (data: any) => void): void {
    const wsUrl = this.config.testnet
      ? 'wss://testnet.binance.vision/ws'
      : 'wss://stream.binance.com:9443/ws';

    this.ws = new WebSocket(wsUrl);

    this.ws.onopen = () => {
      console.log('[Binance] WebSocket connected');
    };

    this.ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      onMessage(data);
    };

    this.ws.onerror = (error) => {
      console.error('[Binance] WebSocket error:', error);
    };

    this.ws.onclose = () => {
      console.log('[Binance] WebSocket disconnected');
    };
  }

  /**
   * 订阅 K 线流
   */
  subscribeKlines(symbol: string, interval: string, callback: (kline: KlineData) => void): void {
    const streamName = `${symbol.replace('/', '').toLowerCase()}@kline_${interval}`;
    const message = {
      method: 'SUBSCRIBE',
      params: [streamName],
      id: Date.now(),
    };

    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
      this.wsSubscriptions.set(streamName, (data) => {
        if (data.e === 'kline') {
          const k = data.k;
          callback({
            time: k.t,
            open: parseFloat(k.o),
            high: parseFloat(k.h),
            low: parseFloat(k.l),
            close: parseFloat(k.c),
            volume: parseFloat(k.v),
          });
        }
      });
    }
  }

  /**
   * 断开 WebSocket
   */
  disconnectWebSocket(): void {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  // -----------------------------------------
  // 辅助方法
  // -----------------------------------------

  private generateSignature(queryString: string): string {
    return CryptoJS.HmacSHA256(queryString, this.config.secretKey!).toString();
  }

  private parseOrderResponse(data: any): OrderResponse {
    return {
      id: data.orderId.toString(),
      symbol: data.symbol,
      side: data.side.toLowerCase(),
      type: data.type.toLowerCase(),
      status: data.status.toLowerCase(),
      amount: parseFloat(data.origQty),
      price: parseFloat(data.price),
      filledAmount: parseFloat(data.executedQty),
      filledPrice: parseFloat(data.price),
      commission: parseFloat(data.commission || 0),
      createdAt: data.transactTime,
      updatedAt: data.updateTime,
    };
  }
}

// ============================================
// DataProvider 实现
// ============================================

export class BinanceDataProvider implements DataProvider {
  private adapter: BinanceAdapter;
  private cache: Map<string, KlineData[]> = new Map();

  constructor(config?: Partial<ExchangeConfig>) {
    this.adapter = new BinanceAdapter(config);
  }

  getKlines(pair: string, timeframe: string, limit: number = 100): DataFrame {
    const cacheKey = `${pair}_${timeframe}_${limit}`;
    const cached = this.cache.get(cacheKey);

    if (cached) {
      return this.klinesToDataFrame(cached);
    }

    return { time: [], open: [], high: [], low: [], close: [], volume: [] };
  }

  async getHistoricalKlines(
    pair: string,
    timeframe: string,
    startTime: number,
    endTime: number
  ): Promise<DataFrame> {
    const klines = await this.adapter.getKlines(
      pair,
      timeframe,
      1000,
      startTime,
      endTime
    );

    const cacheKey = `${pair}_${timeframe}_${startTime}_${endTime}`;
    this.cache.set(cacheKey, klines);

    return this.klinesToDataFrame(klines);
  }

  getCurrentPrice(pair: string): number {
    // 简化：实际应缓存最新价格
    return 0;
  }

  getPairData(pair: string): unknown {
    return null;
  }

  private klinesToDataFrame(klines: KlineData[]): DataFrame {
    return {
      time: klines.map((k) => k.time),
      open: klines.map((k) => k.open),
      high: klines.map((k) => k.high),
      low: klines.map((k) => k.low),
      close: klines.map((k) => k.close),
      volume: klines.map((k) => k.volume),
    };
  }
}

// ============================================
// 默认导出
// ============================================

export const defaultExchange = new BinanceAdapter({ testnet: true });
