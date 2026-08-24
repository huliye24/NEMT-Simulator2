/**
 * Copyright 2026 NEMT Lab
 *
 * NEMT 执行 Store - 管理策略执行、信号生成、市场数据
 * 遵循原则：单一职责，只管执行状态
 */

import { create } from 'zustand';

// ============================================
// 类型定义
// ============================================

export interface KlineData {
  time: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface NEMTSignal {
  id: string;
  time: number;
  symbol: string;
  type: 'BUY' | 'SELL' | 'HOLD';
  strength: number;       // 0-1 信号强度
  price: number;          // 信号触发价格
  stopLoss: number;       // 止损价格
  takeProfit: number;     // 止盈价格
  riskReward: number;     // 风险收益比
  confidence: number;     // 置信度 0-100
  reason: string;         // 信号原因
  wavePhase: string;      // 波相位
  entropy: number;        // 熵值
}

export interface NEMTState {
  // 波动率
  psi: number;            // Gross Profit Rate (增长率)
  phi: number;           // Decay Rate (衰减率)
  entropy: number;       // 系统熵

  // 演化状态
  phase: 'stable' | 'critical' | 'critical_up' | 'critical_down' | 'decay';
  waveAmplitude: number;
  waveFrequency: number;

  // 边界条件
  stabilityThreshold: number;
  criticalThreshold: number;
}

export interface ExecutionState {
  // 连接状态
  connected: boolean;
  connecting: boolean;
  error: string | null;

  // 市场数据
  currentSymbol: string;
  currentInterval: string;
  klines: KlineData[];
  currentPrice: number;
  priceChange24h: number;
  priceChangePercent24h: number;
  high24h: number;
  low24h: number;
  volume24h: number;

  // NEMT 状态
  nemtState: NEMTState;

  // 信号
  signals: NEMTSignal[];
  lastSignal: NEMTSignal | null;

  // 执行状态
  isRunning: boolean;
  lastUpdate: number;
}

// ============================================
// Actions 接口
// ============================================

interface ExecutionActions {
  // 连接控制
  connect: (symbol?: string, interval?: string) => Promise<void>;
  disconnect: () => void;

  // 市场数据更新
  updateKlines: (klines: KlineData[]) => void;
  updatePrice: (price: number, change?: number, changePercent?: number) => void;

  // NEMT 状态更新
  updateNEMTState: (state: Partial<NEMTState>) => void;

  // 信号管理
  addSignal: (signal: NEMTSignal) => void;
  clearSignals: () => void;

  // 策略控制
  startExecution: () => void;
  stopExecution: () => void;

  // 符号和周期选择
  setSymbol: (symbol: string) => void;
  setInterval: (interval: string) => void;

  // 错误处理
  setError: (error: string | null) => void;
}

type ExecutionStoreState = ExecutionState & ExecutionActions;

// ============================================
// NEMT 计算引擎
// ============================================

/**
 * 简化的 NEMT 信号计算
 * 基于非线性薛定谔方程的近似解
 */
function calculateNEMTSignal(klines: KlineData[]): Partial<NEMTState> {
  if (klines.length < 20) {
    return {
      psi: 0,
      phi: 0,
      entropy: 0,
      phase: 'stable',
      waveAmplitude: 0,
      waveFrequency: 0,
      stabilityThreshold: 0.3,
      criticalThreshold: 0.7,
    };
  }

  const closes = klines.map(k => k.close);
  const volumes = klines.map(k => k.volume);

  // 计算收益率
  const returns: number[] = [];
  for (let i = 1; i < closes.length; i++) {
    returns.push((closes[i] - closes[i - 1]) / closes[i - 1]);
  }

  // 计算 psi (增长率) - 使用指数加权移动平均
  const alpha = 0.3;
  let psi = returns.reduce((sum, r) => sum + r, 0) / returns.length;
  for (let i = returns.length - 2; i >= 0; i--) {
    psi = alpha * returns[i] + (1 - alpha) * psi;
  }
  psi = psi * 100; // 转换为百分比

  // 计算 phi (衰减率) - 使用波动率
  const mean = returns.reduce((s, r) => s + r, 0) / returns.length;
  const variance = returns.reduce((s, r) => s + (r - mean) ** 2, 0) / returns.length;
  const volatility = Math.sqrt(variance);
  const phi = volatility * Math.sqrt(252) * 100; // 年化波动率

  // 计算熵 - 价格分布的不确定性
  const bins = 10;
  const min = Math.min(...closes);
  const max = Math.max(...closes);
  const range = max - min;
  const binWidth = range / bins;
  const histogram = new Array(bins).fill(0);

  for (const price of closes) {
    const binIndex = Math.min(Math.floor((price - min) / binWidth), bins - 1);
    histogram[binIndex]++;
  }

  let entropy = 0;
  for (const count of histogram) {
    if (count > 0) {
      const p = count / closes.length;
      entropy -= p * Math.log2(p);
    }
  }
  entropy = entropy / Math.log2(bins); // 归一化

  // 确定相位
  let phase: 'stable' | 'critical' | 'critical_up' | 'critical_down' | 'decay' = 'stable';
  const stabilityThreshold = 0.3;
  const criticalThreshold = 0.7;

  if (Math.abs(psi) < stabilityThreshold && entropy < criticalThreshold) {
    phase = 'stable';
  } else if (psi > criticalThreshold && entropy > criticalThreshold) {
    phase = 'critical_up';
  } else if (psi < -criticalThreshold && entropy > criticalThreshold) {
    phase = 'critical_down';
  } else if (entropy > criticalThreshold) {
    phase = 'critical';
  } else {
    phase = 'decay';
  }

  // 计算波幅和频率
  const waveAmplitude = (max - min) / closes[closes.length - 1] * 100;
  const waveFrequency = 2 * Math.PI / (klines.length / 2);

  return {
    psi: Math.round(psi * 1000) / 1000,
    phi: Math.round(phi * 1000) / 1000,
    entropy: Math.round(entropy * 1000) / 1000,
    phase,
    waveAmplitude: Math.round(waveAmplitude * 1000) / 1000,
    waveFrequency: Math.round(waveFrequency * 1000) / 1000,
    stabilityThreshold,
    criticalThreshold,
  };
}

/**
 * 生成交易信号
 */
function generateSignal(
  klines: KlineData[],
  nemtState: Partial<NEMTState>,
  symbol: string
): NEMTSignal | null {
  if (klines.length < 20 || !nemtState.phase || nemtState.psi === undefined || nemtState.entropy === undefined) return null;

  const lastKline = klines[klines.length - 1];
  const prevKline = klines[klines.length - 2];

  const psi = nemtState.psi;
  const entropy = nemtState.entropy;
  const phase = nemtState.phase;
  const price = lastKline.close;

  // 基于相位生成信号
  let signalType: 'BUY' | 'SELL' | 'HOLD' = 'HOLD';
  let strength = 0.5;
  let reason = '';
  let confidence = 50;

  if (phase === 'critical_up') {
    signalType = 'BUY';
    strength = Math.min(1, entropy * psi / 10);
    confidence = Math.round(50 + entropy * 30);
    reason = `突破临界上涨: psi=${psi.toFixed(3)}%, entropy=${entropy.toFixed(3)}`;
  } else if (phase === 'critical_down') {
    signalType = 'SELL';
    strength = Math.min(1, Math.abs(psi) * entropy / 10);
    confidence = Math.round(50 + entropy * 30);
    reason = `突破临界下跌: psi=${psi.toFixed(3)}%, entropy=${entropy.toFixed(3)}`;
  } else if (phase === 'stable' && psi > 0.5) {
    signalType = 'BUY';
    strength = 0.6;
    confidence = 60;
    reason = `稳定上涨: psi=${psi.toFixed(3)}%`;
  } else if (phase === 'stable' && psi < -0.5) {
    signalType = 'SELL';
    strength = 0.6;
    confidence = 60;
    reason = `稳定下跌: psi=${psi.toFixed(3)}%`;
  } else {
    reason = `观望: phase=${phase}, psi=${psi.toFixed(3)}%, entropy=${entropy.toFixed(3)}`;
  }

  // 计算止损止盈
  const atrMultiplier = 2;
  const atr = klines.slice(-14).reduce((sum, k) => {
    return sum + Math.max(
      k.high - k.low,
      Math.abs(k.high - prevKline.close),
      Math.abs(k.low - prevKline.close)
    );
  }, 0) / 14;

  const stopLoss = signalType === 'BUY'
    ? price - atr * atrMultiplier
    : price + atr * atrMultiplier;

  const takeProfit = signalType === 'BUY'
    ? price + atr * atrMultiplier * 2
    : price - atr * atrMultiplier * 2;

  const riskReward = signalType !== 'HOLD'
    ? Math.abs(takeProfit - price) / Math.abs(price - stopLoss)
    : 0;

  return {
    id: `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
    time: Date.now(),
    symbol,
    type: signalType,
    strength: Math.round(strength * 100) / 100,
    price,
    stopLoss: Math.round(stopLoss * 100) / 100,
    takeProfit: Math.round(takeProfit * 100) / 100,
    riskReward: Math.round(riskReward * 100) / 100,
    confidence,
    reason,
    wavePhase: phase,
    entropy,
  };
}

// ============================================
// Store 创建
// ============================================

export const useExecutionStore = create<ExecutionStoreState>()(
  (set, get) => ({
    // 初始状态
    connected: false,
    connecting: false,
    error: null,
    currentSymbol: 'BTCUSDT',
    currentInterval: '1h',
    klines: [],
    currentPrice: 0,
    priceChange24h: 0,
    priceChangePercent24h: 0,
    high24h: 0,
    low24h: 0,
    volume24h: 0,
    nemtState: {
      psi: 0,
      phi: 0,
      entropy: 0,
      phase: 'stable',
      waveAmplitude: 0,
      waveFrequency: 0,
      stabilityThreshold: 0.3,
      criticalThreshold: 0.7,
    },
    signals: [],
    lastSignal: null,
    isRunning: false,
    lastUpdate: 0,

    // 连接控制
    connect: async (symbol = 'BTCUSDT', interval = '1h') => {
      const { binanceService } = await import('../infrastructure/binanceService');

      set({
        connecting: true,
        error: null,
        currentSymbol: symbol,
        currentInterval: interval,
      });

      try {
        // 获取历史K线数据
        const limit = 100;
        const klinesRaw = await binanceService.getKlines(symbol, interval, limit);

        const klines: KlineData[] = klinesRaw.map(k => ({
          time: k.openTime,
          open: parseFloat(k.open),
          high: parseFloat(k.high),
          low: parseFloat(k.low),
          close: parseFloat(k.close),
          volume: parseFloat(k.volume),
        }));

        // 计算 NEMT 状态
        const nemtState = calculateNEMTSignal(klines);

        // 生成初始信号
        const signal = generateSignal(klines, nemtState, symbol);

        set(state => ({
          connected: true,
          connecting: false,
          klines,
          nemtState: { ...state.nemtState, ...nemtState },
          lastSignal: signal,
          signals: signal ? [signal, ...state.signals].slice(0, 50) : state.signals,
          lastUpdate: Date.now(),
        }));

        // 连接 WebSocket 获取实时更新
        await binanceService.connect([symbol], interval);

        // 订阅 K线更新
        binanceService.subscribeKlines(symbol, (kline) => {
          const k: KlineData = {
            time: kline.openTime,
            open: parseFloat(kline.open),
            high: parseFloat(kline.high),
            low: parseFloat(kline.low),
            close: parseFloat(kline.close),
            volume: parseFloat(kline.volume),
          };

          set(state => {
            const newKlines = [...state.klines, k].slice(-200);
            const newNEMTState = calculateNEMTSignal(newKlines);
            const newSignal = generateSignal(newKlines, newNEMTState, state.currentSymbol);

            return {
              klines: newKlines,
              currentPrice: k.close,
              nemtState: { ...state.nemtState, ...newNEMTState },
              lastSignal: newSignal,
              signals: newSignal ? [newSignal, ...state.signals].slice(0, 50) : state.signals,
              lastUpdate: Date.now(),
            };
          });
        });

        // 订阅价格更新
        binanceService.subscribeTicker(symbol, (ticker) => {
          set(state => ({
            currentPrice: parseFloat(ticker.lastPrice),
            priceChange24h: parseFloat(ticker.priceChange),
            priceChangePercent24h: parseFloat(ticker.priceChangePercent),
            high24h: parseFloat(ticker.highPrice),
            low24h: parseFloat(ticker.lowPrice),
            volume24h: parseFloat(ticker.quoteVolume),
          }));
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
      import('../infrastructure/binanceService').then(({ binanceService }) => {
        binanceService.disconnect();
      });
      set({
        connected: false,
        connecting: false,
        error: null,
      });
    },

    // 市场数据更新
    updateKlines: (klines) => {
      const nemtState = calculateNEMTSignal(klines);
      const symbol = get().currentSymbol;
      const signal = generateSignal(klines, nemtState, symbol);

      set(state => ({
        klines,
        nemtState: { ...state.nemtState, ...nemtState },
        lastSignal: signal,
        signals: signal ? [signal, ...state.signals].slice(0, 50) : state.signals,
        lastUpdate: Date.now(),
      }));
    },

    updatePrice: (price, change, changePercent) => {
      set(state => ({
        currentPrice: price,
        priceChange24h: change ?? state.priceChange24h,
        priceChangePercent24h: changePercent ?? state.priceChangePercent24h,
      }));
    },

    // NEMT 状态更新
    updateNEMTState: (newState) => {
      set(state => ({
        nemtState: { ...state.nemtState, ...newState },
      }));
    },

    // 信号管理
    addSignal: (signal) => {
      set(state => ({
        signals: [signal, ...state.signals].slice(0, 50),
        lastSignal: signal,
      }));
    },

    clearSignals: () => {
      set({ signals: [], lastSignal: null });
    },

    // 策略控制
    startExecution: () => {
      set({ isRunning: true });
    },

    stopExecution: () => {
      set({ isRunning: false });
    },

    // 符号和周期选择
    setSymbol: (symbol) => {
      const { connected } = get();
      set({ currentSymbol: symbol });
      if (connected) {
        get().disconnect();
        get().connect(symbol, get().currentInterval);
      }
    },

    setInterval: (interval) => {
      const { connected } = get();
      set({ currentInterval: interval });
      if (connected) {
        get().disconnect();
        get().connect(get().currentSymbol, interval);
      }
    },

    // 错误处理
    setError: (error) => {
      set({ error, connected: false, connecting: false });
    },
  })
);

// ============================================
// 选择器
// ============================================

export const useExecutionState = () => useExecutionStore(state => ({
  connected: state.connected,
  connecting: state.connecting,
  error: state.error,
  isRunning: state.isRunning,
  lastUpdate: state.lastUpdate,
}));

export const useCurrentPrice = () => useExecutionStore(state => state.currentPrice);
export const useKlines = () => useExecutionStore(state => state.klines);
export const useNEMTState = () => useExecutionStore(state => state.nemtState);
export const useSignals = () => useExecutionStore(state => state.signals);
export const useLastSignal = () => useExecutionStore(state => state.lastSignal);
export const useExecutionConnected = () => useExecutionStore(state => state.connected);
