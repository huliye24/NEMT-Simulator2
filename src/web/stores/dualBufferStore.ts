/**
 * Copyright 2026 NEMT Lab
 *
 * 双缓冲策略检验系统
 *
 * 理念：
 * - 从策略市场选择策略进入双缓冲检验
 * - 历史回测：验证策略在过去时间段的有效性
 * - 实战执行：验证策略在当前时间段的实时表现
 * - 双缓冲对比：确保策略在两个维度都能稳定盈利
 * - 结果写回策略市场，更新策略指标
 *
 * 流程：
 * 1. 策略市场选择策略，点击"回测"
 * 2. 进入双缓冲检验，自动加载策略参数
 * 3. 设置回测区间，运行历史回测
 * 4. 审核回测结果，审核通过后开启实时执行
 * 5. 实时执行结果与回测结果对比
 * 6. 执行完成，结果写回策略市场
 */

import { create } from 'zustand';
import { useStrategyStore, type Strategy } from './strategyStore';

// ============================================
// 类型定义
// ============================================

export type SignalType = 'BUY' | 'SELL' | 'HOLD';

export interface KlineData {
  time: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface Trade {
  id: string;
  entryTime: number;
  exitTime: number;
  type: 'LONG' | 'SHORT';
  entryPrice: number;
  exitPrice: number;
  size: number;
  pnl: number;
  pnlPercent: number;
  stopLoss: number;
  takeProfit: number;
  reason: string;
}

export interface BacktestResult {
  strategyId: string;
  strategyName: string;
  startDate: string;
  endDate: string;
  totalBars: number;

  totalReturn: number;
  annualizedReturn: number;
  sharpeRatio: number;
  sortinoRatio: number;
  maxDrawdown: number;
  maxDrawdownDuration: number;
  volatility: number;

  totalTrades: number;
  winningTrades: number;
  losingTrades: number;
  winRate: number;
  avgWin: number;
  avgLoss: number;
  profitFactor: number;

  trades: Trade[];
  klines: KlineData[];
  equityCurve: { time: number; value: number }[];
}

export interface NEMTState {
  psi: number;
  phi: number;
  entropy: number;
  phase: 'stable' | 'critical' | 'critical_up' | 'critical_down' | 'decay';
  waveAmplitude: number;
  waveFrequency: number;
}

export interface BacktestPeriod {
  startDate: string;
  endDate: string;
}

export interface BacktestConfig {
  initialCapital: number;
  positionSize: number;
  stopLossPercent: number;
  takeProfitPercent: number;
  minConfidence: number;
  minStrength: number;
  entropyThreshold: number;
}

export interface BacktestSession {
  id: string;
  strategyId: string;
  strategyName: string;
  backtestResult: BacktestResult | null;
  liveRunning: boolean;
  liveResult: LiveResult | null;
  createdAt: number;
  updatedAt: number;
}

export interface LiveResult {
  strategyId: string;
  strategyName: string;
  positions: LiveTrade[];
  totalTrades: number;
  winningTrades: number;
  losingTrades: number;
  winRate: number;
  totalPnl: number;
  totalPnlPercent: number;
  equityCurve: { time: number; value: number }[];
  startedAt: number;
  endedAt?: number;
}

export interface LiveTrade {
  id: string;
  entryTime: number;
  entryPrice: number;
  type: 'LONG' | 'SHORT';
  size: number;
  stopLoss: number;
  takeProfit: number;
  currentPrice: number;
  unrealizedPnl: number;
  unrealizedPnlPercent: number;
  status: 'open' | 'closed';
  exitTime?: number;
  exitPrice?: number;
  realizedPnl?: number;
}

// ============================================
// Store 状态
// ============================================

interface DualBufferState {
  // 当前会话
  currentSession: BacktestSession | null;

  // 回测配置
  backtestPeriod: BacktestPeriod;
  backtestConfig: BacktestConfig;

  // 回测状态
  backtesting: boolean;
  backtestProgress: number;

  // 实时执行状态
  liveRunning: boolean;
  liveKlines: KlineData[];
  liveNEMTState: NEMTState;
  currentPrice: number;

  // 历史会话记录
  sessions: BacktestSession[];
}

// ============================================
// Store Actions
// ============================================

interface DualBufferActions {
  // 加载策略到双缓冲
  loadStrategy: (strategy: Strategy) => void;

  // 清空当前会话
  clearSession: () => void;

  // 回测配置
  setBacktestPeriod: (period: BacktestPeriod) => void;
  setBacktestConfig: (config: Partial<BacktestConfig>) => void;

  // 运行回测
  runBacktest: () => Promise<BacktestResult | null>;

  // 审核回测结果
  approveBacktest: (strategyId: string, result: BacktestResult) => void;
  rejectBacktest: (strategyId: string) => void;

  // 实时执行
  startLive: () => Promise<void>;
  stopLive: () => void;

  // 辅助
  setSymbol: (symbol: string) => void;
  setSymbol: (symbol: string) => void;
  setError: (error: string | null) => void;
}

type DualBufferStore = DualBufferState & DualBufferActions;

// ============================================
// 默认配置
// ============================================

const DEFAULT_BACKTEST_CONFIG: BacktestConfig = {
  initialCapital: 10000,
  positionSize: 0.1,
  stopLossPercent: 2,
  takeProfitPercent: 4,
  minConfidence: 50,
  minStrength: 0.3,
  entropyThreshold: 0.5,
};

// ============================================
// NEMT 计算引擎
// ============================================

function calculateNEMTState(klines: KlineData[]): NEMTState {
  if (klines.length < 20) {
    return { psi: 0, phi: 0, entropy: 0, phase: 'stable', waveAmplitude: 0, waveFrequency: 0 };
  }

  const closes = klines.map(k => k.close);
  const returns: number[] = [];
  for (let i = 1; i < closes.length; i++) {
    returns.push((closes[i] - closes[i - 1]) / closes[i - 1]);
  }

  const alpha = 0.3;
  let psi = returns.reduce((sum, r) => sum + r, 0) / returns.length;
  for (let i = returns.length - 2; i >= 0; i--) {
    psi = alpha * returns[i] + (1 - alpha) * psi;
  }
  psi = psi * 100;

  const mean = returns.reduce((s, r) => s + r, 0) / returns.length;
  const variance = returns.reduce((s, r) => s + (r - mean) ** 2, 0) / returns.length;
  const volatility = Math.sqrt(variance);
  const phi = volatility * Math.sqrt(252) * 100;

  const bins = 10;
  const min = Math.min(...closes);
  const max = Math.max(...closes);
  const binWidth = (max - min) / bins;
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
  entropy = entropy / Math.log2(bins);

  let phase: NEMTState['phase'] = 'stable';
  const st = 0.3, ct = 0.7;

  if (Math.abs(psi) < st && entropy < ct) phase = 'stable';
  else if (psi > ct && entropy > ct) phase = 'critical_up';
  else if (psi < -ct && entropy > ct) phase = 'critical_down';
  else if (entropy > ct) phase = 'critical';
  else phase = 'decay';

  const waveAmplitude = (max - min) / closes[closes.length - 1] * 100;
  const waveFrequency = 2 * Math.PI / (klines.length / 2);

  return { psi, phi, entropy, phase, waveAmplitude, waveFrequency };
}

// ============================================
// 回测引擎
// ============================================

async function runBacktestEngine(
  strategyName: string,
  strategyId: string,
  klines: KlineData[],
  config: BacktestConfig,
  onProgress?: (p: number) => void
): Promise<BacktestResult> {
  const { initialCapital, stopLossPercent, takeProfitPercent } = config;

  let capital = initialCapital;
  let peakCapital = initialCapital;
  let maxDrawdown = 0;
  let maxDrawdownDuration = 0;
  let currentDrawdownDuration = 0;

  const trades: Trade[] = [];
  const equityCurve: { time: number; value: number }[] = [];

  let position: {
    type: 'LONG' | 'SHORT';
    entryPrice: number;
    entryTime: number;
    size: number;
    stopLoss: number;
    takeProfit: number;
    reason: string;
  } | null = null;

  for (let i = 20; i < klines.length; i++) {
    const kline = klines[i];
    const historyKlines = klines.slice(0, i);
    const nemt = calculateNEMTState(historyKlines);

    // 更新权益
    if (position) {
      const currentValue = position.type === 'LONG'
        ? position.entryPrice * position.size * (kline.close / position.entryPrice)
        : position.entryPrice * position.size * (2 - kline.close / position.entryPrice);
      capital = initialCapital - (position.entryPrice * position.size - currentValue);
      const drawdown = (peakCapital - capital) / peakCapital;
      if (drawdown > maxDrawdown) {
        maxDrawdown = drawdown;
        maxDrawdownDuration = currentDrawdownDuration;
      }
      if (capital > peakCapital) {
        peakCapital = capital;
        currentDrawdownDuration = 0;
      } else {
        currentDrawdownDuration++;
      }
    }
    equityCurve.push({ time: kline.time, value: capital });

    // 检查持仓
    if (position) {
      const { type, entryPrice, stopLoss, takeProfit } = position;
      const hitStop = type === 'LONG' ? kline.low <= stopLoss : kline.high >= stopLoss;
      const hitTarget = type === 'LONG' ? kline.high >= takeProfit : kline.low <= takeProfit;

      if (hitStop || hitTarget) {
        const exitPrice = hitStop ? stopLoss : takeProfit;
        const pnl = type === 'LONG'
          ? (exitPrice - entryPrice) * position.size
          : (entryPrice - exitPrice) * position.size;
        const pnlPercent = type === 'LONG'
          ? ((exitPrice - entryPrice) / entryPrice) * 100
          : ((entryPrice - exitPrice) / entryPrice) * 100;

        trades.push({
          id: `trade_${i}`,
          entryTime: position.entryTime,
          exitTime: kline.time,
          type: position.type,
          entryPrice: position.entryPrice,
          exitPrice,
          size: position.size,
          pnl,
          pnlPercent,
          stopLoss: position.stopLoss,
          takeProfit: position.takeProfit,
          reason: position.reason,
        });

        capital += pnl;
        position = null;
      }
    }

    // 生成信号
    if (!position) {
      let signalType: SignalType = 'HOLD';
      let reason = '';

      if (nemt.phase === 'critical_up') {
        signalType = 'BUY';
        reason = `临界上涨: psi=${nemt.psi.toFixed(3)}%, S=${nemt.entropy.toFixed(3)}`;
      } else if (nemt.phase === 'critical_down') {
        signalType = 'SELL';
        reason = `临界下跌: psi=${nemt.psi.toFixed(3)}%, S=${nemt.entropy.toFixed(3)}`;
      } else if (nemt.phase === 'stable' && Math.abs(nemt.psi) > 0.5) {
        signalType = nemt.psi > 0 ? 'BUY' : 'SELL';
        reason = `稳定趋势: psi=${nemt.psi.toFixed(3)}%`;
      }

      if (signalType !== 'HOLD') {
        const price = kline.close;
        const size = capital * 0.1 / price;

        position = {
          type: signalType === 'BUY' ? 'LONG' : 'SHORT',
          entryPrice: price,
          entryTime: kline.time,
          size,
          stopLoss: signalType === 'BUY'
            ? price * (1 - stopLossPercent / 100)
            : price * (1 + stopLossPercent / 100),
          takeProfit: signalType === 'BUY'
            ? price * (1 + takeProfitPercent / 100)
            : price * (1 - takeProfitPercent / 100),
          reason,
        };
      }
    }

    if (onProgress) onProgress(Math.round((i / klines.length) * 100));

    if (i % 100 === 0) await new Promise(resolve => setTimeout(resolve, 0));
  }

  // 平仓
  if (position) {
    const lastKline = klines[klines.length - 1];
    const pnl = position.type === 'LONG'
      ? (lastKline.close - position.entryPrice) * position.size
      : (position.entryPrice - lastKline.close) * position.size;

    trades.push({
      id: 'final',
      entryTime: position.entryTime,
      exitTime: lastKline.time,
      type: position.type,
      entryPrice: position.entryPrice,
      exitPrice: lastKline.close,
      size: position.size,
      pnl,
      pnlPercent: position.type === 'LONG'
        ? ((lastKline.close - position.entryPrice) / position.entryPrice) * 100
        : ((position.entryPrice - lastKline.close) / position.entryPrice) * 100,
      stopLoss: position.stopLoss,
      takeProfit: position.takeProfit,
      reason: position.reason,
    });
    capital += pnl;
  }

  // 统计数据
  const winningTrades = trades.filter(t => t.pnl > 0);
  const losingTrades = trades.filter(t => t.pnl <= 0);
  const totalReturn = ((capital - initialCapital) / initialCapital) * 100;
  const years = klines.length / 8760;
  const annualizedReturn = (Math.pow(capital / initialCapital, 1 / years) - 1) * 100;

  const returns = equityCurve.slice(1).map((e, i) =>
    (e.value - equityCurve[i].value) / equityCurve[i].value
  );
  const avgReturn = returns.reduce((s, r) => s + r, 0) / (returns.length || 1);
  const stdReturn = Math.sqrt(
    returns.reduce((s, r) => s + (r - avgReturn) ** 2, 0) / (returns.length || 1)
  );
  const sharpeRatio = stdReturn > 0 ? (avgReturn / stdReturn) * Math.sqrt(8760) : 0;

  const negativeReturns = returns.filter(r => r < 0);
  const stdDownside = Math.sqrt(
    negativeReturns.reduce((s, r) => s + r ** 2, 0) / (negativeReturns.length || 1)
  );
  const sortinoRatio = stdDownside > 0 ? (avgReturn / stdDownside) * Math.sqrt(8760) : 0;
  const volatility = stdReturn * Math.sqrt(8760) * 100;

  return {
    strategyId,
    strategyName,
    startDate: '',
    endDate: '',
    totalBars: klines.length,
    totalReturn,
    annualizedReturn,
    sharpeRatio,
    sortinoRatio,
    maxDrawdown: maxDrawdown * 100,
    maxDrawdownDuration,
    volatility,
    totalTrades: trades.length,
    winningTrades: winningTrades.length,
    losingTrades: losingTrades.length,
    winRate: trades.length > 0 ? (winningTrades.length / trades.length) * 100 : 0,
    avgWin: winningTrades.length > 0
      ? winningTrades.reduce((s, t) => s + t.pnl, 0) / winningTrades.length : 0,
    avgLoss: losingTrades.length > 0
      ? losingTrades.reduce((s, t) => s + t.pnl, 0) / losingTrades.length : 0,
    profitFactor: Math.abs(
      winningTrades.reduce((s, t) => s + t.pnl, 0) /
      (losingTrades.reduce((s, t) => s + t.pnl, 0) || 1)
    ),
    trades,
    klines,
    equityCurve,
  };
}

// ============================================
// Store 实现
// ============================================

export const useDualBufferStore = create<DualBufferStore>()(
  (set, get) => ({
    // 初始状态
    currentSession: null,
    backtestPeriod: {
      startDate: '2025-09-01',
      endDate: '2026-01-31',
    },
    backtestConfig: DEFAULT_BACKTEST_CONFIG,
    backtesting: false,
    backtestProgress: 0,
    liveRunning: false,
    liveKlines: [],
    liveNEMTState: {
      psi: 0, phi: 0, entropy: 0, phase: 'stable',
      waveAmplitude: 0, waveFrequency: 0,
    },
    currentPrice: 0,
    sessions: [],

    // 加载策略
    loadStrategy: (strategy) => {
      const session: BacktestSession = {
        id: `session_${Date.now()}`,
        strategyId: strategy.id,
        strategyName: strategy.name,
        backtestResult: null,
        liveRunning: false,
        liveResult: null,
        createdAt: Date.now(),
        updatedAt: Date.now(),
      };
      set({
        currentSession: session,
        backtestProgress: 0,
        liveRunning: false,
        liveKlines: [],
      });
    },

    clearSession: () => {
      set({ currentSession: null, backtestProgress: 0, liveRunning: false });
    },

    setBacktestPeriod: (period) => set({ backtestPeriod: period }),
    setBacktestConfig: (config) => set(state => ({
      backtestConfig: { ...state.backtestConfig, ...config }
    })),

    // 运行回测
    runBacktest: async () => {
      const { currentSession, backtestPeriod, backtestConfig } = get();

      if (!currentSession) {
        set({ error: '请先选择策略' });
        return null;
      }

      set({ backtesting: true, backtestProgress: 0 });

      try {
        const { binanceService } = await import('../infrastructure/binanceService');

        // 获取历史数据
        const startTime = new Date(backtestPeriod.startDate).getTime();
        const endTime = new Date(backtestPeriod.endDate).getTime();
        const symbol = 'BTCUSDT';
        const interval = '1h';

        const klinesRaw = await binanceService.getKlines(
          symbol, interval, 1000, startTime, endTime
        );

        let klines: KlineData[] = klinesRaw.map(k => ({
          time: k.openTime,
          open: parseFloat(k.open),
          high: parseFloat(k.high),
          low: parseFloat(k.low),
          close: parseFloat(k.close),
          volume: parseFloat(k.volume),
        }));

        // 继续获取更多数据
        while (klines.length > 0 && klines[klines.length - 1].time < endTime - 3600000) {
          const moreRaw = await binanceService.getKlines(
            symbol, interval, 1000, klines[klines.length - 1].time + 1, endTime
          );
          if (moreRaw.length === 0) break;

          const more: KlineData[] = moreRaw.map(k => ({
            time: k.openTime,
            open: parseFloat(k.open),
            high: parseFloat(k.high),
            low: parseFloat(k.low),
            close: parseFloat(k.close),
            volume: parseFloat(k.volume),
          }));

          klines.push(...more);
          await new Promise(r => setTimeout(r, 100));
        }

        if (klines.length === 0) {
          throw new Error('没有获取到历史数据，请检查日期范围');
        }

        // 运行回测
        const result = await runBacktestEngine(
          currentSession.strategyName,
          currentSession.strategyId,
          klines,
          backtestConfig,
          (progress) => set({ backtestProgress: progress })
        );

        result.startDate = backtestPeriod.startDate;
        result.endDate = backtestPeriod.endDate;

        // 更新会话
        set(state => ({
          backtesting: false,
          backtestProgress: 100,
          currentSession: state.currentSession
            ? { ...state.currentSession, backtestResult: result, updatedAt: Date.now() }
            : null,
          sessions: [
            ...state.sessions.filter(s => s.strategyId !== currentSession.strategyId),
            { ...currentSession, backtestResult: result, updatedAt: Date.now() },
          ],
        }));

        return result;
      } catch (error) {
        set({ backtesting: false, error: String(error) });
        return null;
      }
    },

    // 审核通过，写回策略市场
    approveBacktest: (strategyId, result) => {
      useStrategyStore.getState().updateStrategy(strategyId, {
        status: 'running',
        metrics: {
          totalTrades: result.totalTrades,
          winRate: result.winRate / 100,
          totalPnL: result.totalReturn,
          sharpeRatio: result.sharpeRatio,
        },
      });
    },

    rejectBacktest: (strategyId) => {
      useStrategyStore.getState().updateStrategy(strategyId, {
        status: 'archived',
      });
    },

    // 实时执行
    startLive: async () => {
      const { currentSession } = get();
      if (!currentSession) return;

      const { binanceService } = await import('../infrastructure/binanceService');

      set({ liveRunning: true });

      try {
        const symbol = 'BTCUSDT';
        const interval = '1h';

        // 获取最近 K 线
        const klinesRaw = await binanceService.getKlines(symbol, interval, 100);
        const klines: KlineData[] = klinesRaw.map(k => ({
          time: k.openTime,
          open: parseFloat(k.open),
          high: parseFloat(k.high),
          low: parseFloat(k.low),
          close: parseFloat(k.close),
          volume: parseFloat(k.volume),
        }));

        const nemtState = calculateNEMTState(klines);

        set({
          liveKlines: klines,
          liveNEMTState: nemtState,
          currentPrice: klines[klines.length - 1]?.close || 0,
        });

        // 连接 WebSocket
        await binanceService.connect([symbol], interval);

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
            const newKlines = [...state.liveKlines, k].slice(-200);
            const nemt = calculateNEMTState(newKlines);
            return {
              liveKlines: newKlines,
              liveNEMTState: nemt,
              currentPrice: k.close,
            };
          });
        });

        binanceService.subscribeTicker(symbol, (ticker) => {
          set({ currentPrice: parseFloat(ticker.lastPrice) });
        });

      } catch (error) {
        set({ liveRunning: false, error: String(error) });
      }
    },

    stopLive: () => {
      import('../infrastructure/binanceService').then(({ binanceService }) => {
        binanceService.disconnect();
      });
      set({ liveRunning: false });
    },

    setSymbol: () => {},
    setError: () => {},
  })
);

// ============================================
// 选择器
// ============================================

export const useCurrentSession = () => useDualBufferStore(state => state.currentSession);
export const useBacktestProgress = () => useDualBufferStore(state => ({
  backtesting: state.backtesting,
  progress: state.backtestProgress,
}));
export const useBacktestPeriod = () => useDualBufferStore(state => state.backtestPeriod);
export const useBacktestConfig = () => useDualBufferStore(state => state.backtestConfig);
export const useLiveKlines = () => useDualBufferStore(state => state.liveKlines);
export const useLiveNEMTState = () => useDualBufferStore(state => state.liveNEMTState);
export const useLivePrice = () => useDualBufferStore(state => state.currentPrice);
export const useLiveRunning = () => useDualBufferStore(state => state.liveRunning);
export const useSessions = () => useDualBufferStore(state => state.sessions);
