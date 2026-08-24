/**
 * Copyright 2026 NEMT Lab
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 */

import { withRetry, CircuitBreaker, CircuitState } from './retry';

// ============================================
// 币安 API 类型定义
// ============================================

export interface BinanceKline {
  openTime: number;
  open: string;
  high: string;
  low: string;
  close: string;
  volume: string;
  closeTime: number;
  quoteVolume: string;
  trades: number;
  takerBuyBaseVolume: string;
  takerBuyQuoteVolume: string;
}

export interface BinanceTicker {
  symbol: string;
  priceChange: string;
  priceChangePercent: string;
  lastPrice: string;
  highPrice: string;
  lowPrice: string;
  volume: string;
  quoteVolume: string;
  timestamp: number;
}

export interface BinanceConfig {
  /** REST API 基础 URL */
  restBaseUrl?: string;
  /** WebSocket 基础 URL */
  wsBaseUrl?: string;
  /** 默认交易对 */
  defaultSymbols?: string[];
  /** 默认K线周期 */
  defaultInterval?: string;
  /** 最大重试次数 */
  maxRetries?: number;
  /** 请求超时 (ms) */
  timeout?: number;
}

export interface BinanceConnectionState {
  connected: boolean;
  connecting: boolean;
  error: string | null;
  lastUpdate: number | null;
  symbols: string[];
  interval: string;
}

// ============================================
// 币安 API 服务
// ============================================

const DEFAULT_CONFIG: Required<BinanceConfig> = {
  restBaseUrl: 'https://api.binance.com/api/v3',
  wsBaseUrl: 'wss://stream.binance.com:9443/ws',
  defaultSymbols: ['BTCUSDT', 'ETHUSDT'],
  defaultInterval: '1h',
  maxRetries: 3,
  timeout: 10000,
};

// 断路器实例
const binanceCircuitBreaker = new CircuitBreaker({
  failureThreshold: 5,
  successThreshold: 2,
  halfOpenTimeout: 30000,
  windowTime: 60000,
});

class BinanceService {
  private config: Required<BinanceConfig>;
  private ws: WebSocket | null = null;
  private wsCallbacks: Map<string, Set<(data: any) => void>> = new Map();
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;
  private connectionState: BinanceConnectionState = {
    connected: false,
    connecting: false,
    error: null,
    lastUpdate: null,
    symbols: [],
    interval: '1h',
  };
  private stateListeners: Set<(state: BinanceConnectionState) => void> = new Set();

  constructor(config: BinanceConfig = {}) {
    this.config = { ...DEFAULT_CONFIG, ...config };
  }

  // ============================================
  // 状态管理
  // ============================================

  getConnectionState(): BinanceConnectionState {
    return { ...this.connectionState };
  }

  subscribeToState(listener: (state: BinanceConnectionState) => void): () => void {
    this.stateListeners.add(listener);
    return () => this.stateListeners.delete(listener);
  }

  private updateState(updates: Partial<BinanceConnectionState>): void {
    this.connectionState = { ...this.connectionState, ...updates };
    this.stateListeners.forEach(listener => listener(this.connectionState));
  }

  // ============================================
  // REST API 方法
  // ============================================

  /**
   * 获取 K线数据 (历史)
   */
  async getKlines(
    symbol: string,
    interval: string = '1h',
    limit: number = 100,
    startTime?: number,
    endTime?: number
  ): Promise<BinanceKline[]> {
    const params = new URLSearchParams({
      symbol: symbol.toUpperCase(),
      interval,
      limit: limit.toString(),
    });

    if (startTime) params.append('startTime', startTime.toString());
    if (endTime) params.append('endTime', endTime.toString());

    const result = await withRetry(
      async () => {
        const response = await fetch(
          `${this.config.restBaseUrl}/klines?${params}`,
          { signal: AbortSignal.timeout(this.config.timeout) }
        );

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        return response.json();
      },
      { maxRetries: this.config.maxRetries }
    );

    if (!result.success) {
      throw result.error || new Error('Failed to fetch klines');
    }

    // 转换数据格式
    return (result.data as any[][]).map(k => ({
      openTime: k[0],
      open: k[1],
      high: k[2],
      low: k[3],
      close: k[4],
      volume: k[5],
      closeTime: k[6],
      quoteVolume: k[7],
      trades: k[8],
      takerBuyBaseVolume: k[9],
      takerBuyQuoteVolume: k[10],
    }));
  }

  /**
   * 获取24小时价格变动统计
   */
  async get24hrTicker(symbol: string): Promise<BinanceTicker> {
    const result = await withRetry(
      async () => {
        const response = await fetch(
          `${this.config.restBaseUrl}/ticker/24hr?symbol=${symbol.toUpperCase()}`,
          { signal: AbortSignal.timeout(this.config.timeout) }
        );

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }

        return response.json();
      },
      { maxRetries: this.config.maxRetries }
    );

    if (!result.success) {
      throw result.error || new Error('Failed to fetch ticker');
    }

    const data = result.data as any;
    return {
      symbol: data.symbol,
      priceChange: data.priceChange,
      priceChangePercent: data.priceChangePercent,
      lastPrice: data.lastPrice,
      highPrice: data.highPrice,
      lowPrice: data.lowPrice,
      volume: data.volume,
      quoteVolume: data.quoteVolume,
      timestamp: Date.now(),
    };
  }

  /**
   * 获取多个交易对的24小时统计
   */
  async getAll24hrTickers(): Promise<BinanceTicker[]> {
    const result = await withRetry(
      async () => {
        const response = await fetch(
          `${this.config.restBaseUrl}/ticker/24hr`,
          { signal: AbortSignal.timeout(this.config.timeout) }
        );

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }

        return response.json();
      },
      { maxRetries: this.config.maxRetries }
    );

    if (!result.success) {
      throw result.error || new Error('Failed to fetch tickers');
    }

    return (result.data as any[]).map(data => ({
      symbol: data.symbol,
      priceChange: data.priceChange,
      priceChangePercent: data.priceChangePercent,
      lastPrice: data.lastPrice,
      highPrice: data.highPrice,
      lowPrice: data.lowPrice,
      volume: data.volume,
      quoteVolume: data.quoteVolume,
      timestamp: Date.now(),
    }));
  }

  /**
   * 获取交易对信息
   */
  async getExchangeInfo(): Promise<any> {
    const result = await withRetry(
      async () => {
        const response = await fetch(
          `${this.config.restBaseUrl}/exchangeInfo`,
          { signal: AbortSignal.timeout(this.config.timeout) }
        );

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }

        return response.json();
      },
      { maxRetries: this.config.maxRetries }
    );

    if (!result.success) {
      throw result.error || new Error('Failed to fetch exchange info');
    }

    return result.data;
  }

  /**
   * 获取最近成交
   */
  async getRecentTrades(symbol: string, limit: number = 100): Promise<any[]> {
    const result = await withRetry(
      async () => {
        const response = await fetch(
          `${this.config.restBaseUrl}/trades?symbol=${symbol.toUpperCase()}&limit=${limit}`,
          { signal: AbortSignal.timeout(this.config.timeout) }
        );

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }

        return response.json();
      },
      { maxRetries: this.config.maxRetries }
    );

    if (!result.success) {
      throw result.error || new Error('Failed to fetch trades');
    }

    return result.data;
  }

  // ============================================
  // WebSocket 方法
  // ============================================

  /**
   * 连接 WebSocket 并订阅交易对
   */
  connect(symbols: string[], interval: string = '1h'): Promise<void> {
    return new Promise((resolve, reject) => {
      if (this.ws && this.connectionState.connected) {
        resolve();
        return;
      }

      this.updateState({ connecting: true, error: null });

      // 构建 WebSocket URL
      const streams = symbols.flatMap(s => [
        `${s.toLowerCase()}@ticker`,
        `${s.toLowerCase()}@kline_${interval}`,
      ]);
      const wsUrl = `${this.config.wsBaseUrl}/${streams.join('/')}`;

      try {
        this.ws = new WebSocket(wsUrl);

        this.ws.onopen = () => {
          console.log('[BinanceService] WebSocket connected');
          this.updateState({
            connected: true,
            connecting: false,
            error: null,
            lastUpdate: Date.now(),
            symbols,
            interval,
          });
          this.reconnectAttempts = 0;
          resolve();
        };

        this.ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            this.handleMessage(data);
          } catch (e) {
            console.error('[BinanceService] Parse error:', e);
          }
        };

        this.ws.onerror = (error) => {
          console.error('[BinanceService] WebSocket error:', error);
          this.updateState({
            connected: false,
            connecting: false,
            error: 'Connection error',
          });
          reject(new Error('WebSocket connection failed'));
        };

        this.ws.onclose = () => {
          console.log('[BinanceService] WebSocket closed');
          this.updateState({
            connected: false,
            connecting: false,
          });
          this.attemptReconnect(symbols, interval);
        };
      } catch (error) {
        this.updateState({
          connected: false,
          connecting: false,
          error: String(error),
        });
        reject(error);
      }
    });
  }

  /**
   * 断开 WebSocket 连接
   */
  disconnect(): void {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    this.updateState({
      connected: false,
      connecting: false,
      error: null,
    });
  }

  /**
   * 订阅 K线数据
   */
  subscribeKlines(symbol: string, callback: (kline: BinanceKline) => void): () => void {
    return this.subscribe('kline', callback);
  }

  /**
   * 订阅价格变动
   */
  subscribeTicker(symbol: string, callback: (ticker: BinanceTicker) => void): () => void {
    return this.subscribe('ticker', callback);
  }

  private subscribe(type: string, callback: (data: any) => void): () => void {
    const key = `${type}`;
    if (!this.wsCallbacks.has(key)) {
      this.wsCallbacks.set(key, new Set());
    }
    this.wsCallbacks.get(key)!.add(callback);

    return () => {
      this.wsCallbacks.get(key)?.delete(callback);
    };
  }

  private handleMessage(data: any): void {
    this.updateState({ lastUpdate: Date.now() });

    // K线数据
    if (data.e === 'kline' && data.k) {
      const kline: BinanceKline = {
        openTime: data.k.t,
        open: data.k.o,
        high: data.k.h,
        low: data.k.l,
        close: data.k.c,
        volume: data.k.v,
        closeTime: data.k.T,
        quoteVolume: data.k.q,
        trades: data.k.n,
        takerBuyBaseVolume: data.k.V,
        takerBuyQuoteVolume: data.k.Q,
      };
      this.wsCallbacks.get('kline')?.forEach(cb => cb(kline));
    }

    // Ticker 数据
    if (data.e === '24hrTicker') {
      const ticker: BinanceTicker = {
        symbol: data.s,
        priceChange: data.p,
        priceChangePercent: data.P,
        lastPrice: data.c,
        highPrice: data.h,
        lowPrice: data.l,
        volume: data.v,
        quoteVolume: data.q,
        timestamp: data.E,
      };
      this.wsCallbacks.get('ticker')?.forEach(cb => cb(ticker));
    }
  }

  private attemptReconnect(symbols: string[], interval: string): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('[BinanceService] Max reconnection attempts reached');
      return;
    }

    this.reconnectAttempts++;
    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);

    console.log(`[BinanceService] Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})`);

    setTimeout(() => {
      this.connect(symbols, interval).catch(console.error);
    }, delay);
  }

  // ============================================
  // 工具方法
  // ============================================

  /**
   * 检查服务健康状态
   */
  async healthCheck(): Promise<boolean> {
    try {
      await this.get24hrTicker('BTCUSDT');
      return true;
    } catch {
      return false;
    }
  }

  /**
   * 获取断路器状态
   */
  getCircuitBreakerState(): CircuitState {
    return binanceCircuitBreaker.getState();
  }

  /**
   * 重置断路器
   */
  resetCircuitBreaker(): void {
    binanceCircuitBreaker.reset();
  }
}

// ============================================
// 单例导出
// ============================================

export const binanceService = new BinanceService();

// ============================================
// 便捷函数
// ============================================

export async function fetchKlines(
  symbol: string,
  interval: string = '1h',
  days: number = 30
): Promise<BinanceKline[]> {
  const endTime = Date.now();
  const startTime = endTime - days * 24 * 60 * 60 * 1000;
  const limit = Math.min(days * 24, 1000); // Binance 最大限制

  return binanceService.getKlines(symbol, interval, limit, startTime, endTime);
}

export async function fetchPrice(symbol: string): Promise<number> {
  const ticker = await binanceService.get24hrTicker(symbol);
  return parseFloat(ticker.lastPrice);
}

export async function fetchPrices(symbols: string[]): Promise<Map<string, number>> {
  const tickers = await binanceService.getAll24hrTickers();
  const priceMap = new Map<string, number>();

  tickers
    .filter(t => symbols.includes(t.symbol))
    .forEach(t => priceMap.set(t.symbol, parseFloat(t.lastPrice)));

  return priceMap;
}
