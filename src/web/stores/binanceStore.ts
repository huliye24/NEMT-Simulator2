/**
 * Copyright 2026 NEMT Lab
 *
 * 币安 Store - 独立管理市场数据状态
 * 遵循原则：单一职责，只管市场数据
 */

import { create } from 'zustand';

// ============================================
// 类型定义
// ============================================

export interface MarketData {
  symbol: string;
  price: number;
  change24h: number;
  changePercent24h: number;
  high24h: number;
  low24h: number;
  volume24h: number;
  lastUpdate: number;
}

export interface BinanceState {
  connected: boolean;
  connecting: boolean;
  error: string | null;
  lastUpdate: number | null;
  selectedSymbol: string;
  selectedInterval: string;
  prices: Record<string, MarketData>;
  klines: Record<string, any[]>;
}

export type Interval = '1m' | '3m' | '5m' | '15m' | '30m' | '1h' | '2h' | '4h' | '6h' | '8h' | '12h' | '1d' | '3d' | '1w' | '1M';

// ============================================
// 状态接口
// ============================================

interface BinanceStoreState extends BinanceState {
  // 内部使用
  _priceUpdateCallbacks: Map<string, Array<(data: MarketData) => void>>;
}

// ============================================
// Actions 接口
// ============================================

interface BinanceStoreActions {
  // 连接控制
  connect: (symbols?: string[], interval?: string) => Promise<void>;
  disconnect: () => void;

  // 数据更新
  updatePrice: (symbol: string, data: Partial<MarketData>) => void;
  updateKlines: (symbol: string, klines: any[]) => void;

  // 选择控制
  setSelectedSymbol: (symbol: string) => void;
  setSelectedInterval: (interval: string) => void;

  // 订阅
  subscribeToPrice: (symbol: string, callback: (data: MarketData) => void) => () => void;

  // 错误处理
  setError: (error: string | null) => void;

  // 内部方法
  _triggerPriceUpdate: (symbol: string, data: MarketData) => void;
}

// ============================================
// Store 创建
// ============================================

export const useBinanceStore = create<BinanceStoreState & BinanceStoreActions>()(
  (set, get) => ({
    // 初始状态
    connected: false,
    connecting: false,
    error: null,
    lastUpdate: null,
    selectedSymbol: 'BTCUSDT',
    selectedInterval: '1h',
    prices: {},
    klines: {},
    _priceUpdateCallbacks: new Map(),

    // 连接控制
    connect: async (symbols = ['BTCUSDT', 'ETHUSDT'], interval = '1h') => {
      const { binanceService } = await import('../infrastructure/binanceService');

      set(state => ({
        connecting: true,
        error: null,
        selectedSymbol: symbols[0],
        selectedInterval: interval,
      }));

      try {
        await binanceService.connect(symbols, interval);

        // 订阅价格更新
        symbols.forEach(symbol => {
          binanceService.subscribeTicker(symbol, (ticker) => {
            const price = parseFloat(ticker.lastPrice);
            const change = parseFloat(ticker.priceChange);
            const changePercent = parseFloat(ticker.priceChangePercent);

            get().updatePrice(symbol, {
              symbol,
              price,
              change24h: change,
              changePercent24h: changePercent,
              high24h: parseFloat(ticker.highPrice),
              low24h: parseFloat(ticker.lowPrice),
              volume24h: parseFloat(ticker.quoteVolume),
              lastUpdate: ticker.timestamp,
            });
          });
        });

        set({
          connected: true,
          connecting: false,
        });
      } catch (error) {
        set({
          connected: false,
          connecting: false,
          error: String(error),
        });
      }
    },

    disconnect: () => {
      // 动态导入并断开连接
      import('../infrastructure/binanceService').then(({ binanceService }) => {
        binanceService.disconnect();
      });

      set({
        connected: false,
        connecting: false,
        error: null,
      });
    },

    // 数据更新
    updatePrice: (symbol, data) => {
      const currentPrice = get().prices[symbol] || { symbol };
      const updatedPrice: MarketData = { ...currentPrice, ...data } as MarketData;

      set(state => ({
        prices: {
          ...state.prices,
          [symbol]: updatedPrice,
        },
        lastUpdate: Date.now(),
      }));

      // 触发订阅回调
      get()._triggerPriceUpdate(symbol, updatedPrice);
    },

    updateKlines: (symbol, klines) => {
      set(state => ({
        klines: {
          ...state.klines,
          [symbol]: klines,
        }
      }));
    },

    // 选择控制
    setSelectedSymbol: (symbol) => {
      set({ selectedSymbol: symbol });
    },

    setSelectedInterval: (interval) => {
      set({ selectedInterval: interval });
    },

    // 订阅
    subscribeToPrice: (symbol, callback) => {
      const callbacks = get()._priceUpdateCallbacks;
      const key = `price_${symbol}`;

      const existingCallbacks = callbacks.get(key) || [];
      const updatedCallbacks = [...existingCallbacks, callback];
      callbacks.set(key, updatedCallbacks);

      // 返回取消订阅函数
      return () => {
        const currentCallbacks = callbacks.get(key) || [];
        const filtered = currentCallbacks.filter((cb: (data: MarketData) => void) => cb !== callback);
        callbacks.set(key, filtered);
      };
    },

    // 内部方法
    _triggerPriceUpdate: (symbol, data) => {
      const callbacks = get()._priceUpdateCallbacks;
      const key = `price_${symbol}`;
      const symbolCallbacks = callbacks.get(key) || [];

      symbolCallbacks.forEach((callback: (data: MarketData) => void) => {
        try {
          callback(data);
        } catch (error) {
          console.error(`Error in price callback for ${symbol}:`, error);
        }
      });
    },

    // 错误处理
    setError: (error) => {
      set({ error });
    },
  })
);

// ============================================
// 选择器 (Selectors)
// ============================================

export const useBinanceState = () => useBinanceStore(state => ({
  connected: state.connected,
  connecting: state.connecting,
  error: state.error,
  lastUpdate: state.lastUpdate,
}));

export const useBinancePrices = () => useBinanceStore(state => state.prices);

export const useBinanceKlines = () => useBinanceStore(state => state.klines);

export const useBinanceConnected = () => useBinanceStore(state => state.connected);

export const useSelectedSymbol = () => useBinanceStore(state => state.selectedSymbol);

export const useSelectedInterval = () => useBinanceStore(state => state.selectedInterval);

export const usePriceBySymbol = (symbol: string) => useBinanceStore(state => state.prices[symbol]);

export const useKlinesBySymbol = (symbol: string) => useBinanceStore(state => state.klines[symbol]);

// 便捷的多个价格订阅
export const usePricesBySymbols = (symbols: string[]) => useBinanceStore(state => {
  const prices: Record<string, MarketData> = {};
  symbols.forEach(symbol => {
    if (state.prices[symbol]) {
      prices[symbol] = state.prices[symbol];
    }
  });
  return prices;
});
