/**
 * Copyright 2026 NEMT Lab
 *
 * NEMT Technical Indicators Library
 * 技术指标库 - 借鉴 freqtrade TA-Lib 实现
 */

import type { DataFrame } from '../types/kline';

// ============================================
// 动量指标
// ============================================

/**
 * RSI (Relative Strength Index)
 * 相对强弱指数
 */
export function calculateRSI(prices: number[], period: number = 14): number[] {
  const rsi: number[] = [];

  if (prices.length < period + 1) {
    return prices.map(() => 50);
  }

  // 计算价格变化
  const changes: number[] = [];
  for (let i = 1; i < prices.length; i++) {
    changes.push(prices[i] - prices[i - 1]);
  }

  // 计算平均增益和平均损失
  let avgGain = 0;
  let avgLoss = 0;

  // 初始平均
  for (let i = 0; i < period; i++) {
    if (changes[i] > 0) avgGain += changes[i];
    else avgLoss -= changes[i];
  }

  avgGain /= period;
  avgLoss /= period;

  // 第一个 RSI
  const rs = avgLoss === 0 ? 100 : avgGain / avgLoss;
  rsi.push(100 - 100 / (1 + rs));

  // 后续 RSI (使用平滑)
  for (let i = period; i < changes.length; i++) {
    const gain = changes[i] > 0 ? changes[i] : 0;
    const loss = changes[i] < 0 ? -changes[i] : 0;

    avgGain = (avgGain * (period - 1) + gain) / period;
    avgLoss = (avgLoss * (period - 1) + loss) / period;

    const rs = avgLoss === 0 ? 100 : avgGain / avgLoss;
    rsi.push(100 - 100 / (1 + rs));
  }

  return rsi;
}

/**
 * MACD (Moving Average Convergence Divergence)
 * 移动平均收敛发散
 */
export function calculateMACD(
  prices: number[],
  fastPeriod: number = 12,
  slowPeriod: number = 26,
  signalPeriod: number = 9
): { macd: number[]; signal: number[]; histogram: number[] } {
  const emaFast = calculateEMA(prices, fastPeriod);
  const emaSlow = calculateEMA(prices, slowPeriod);

  const macdLine: number[] = [];
  for (let i = 0; i < prices.length; i++) {
    macdLine.push(emaFast[i] - emaSlow[i]);
  }

  const signalLine = calculateEMA(macdLine, signalPeriod);

  const histogram: number[] = [];
  for (let i = 0; i < macdLine.length; i++) {
    histogram.push(macdLine[i] - signalLine[i]);
  }

  return { macd: macdLine, signal: signalLine, histogram };
}

/**
 * Stochastic
 * 随机指标
 */
export function calculateStochastic(
  highs: number[],
  lows: number[],
  closes: number[],
  kPeriod: number = 14,
  dPeriod: number = 3
): { k: number[]; d: number[] } {
  const k: number[] = [];

  for (let i = 0; i < closes.length; i++) {
    if (i < kPeriod - 1) {
      k.push(50);
      continue;
    }

    let highestHigh = -Infinity;
    let lowestLow = Infinity;

    for (let j = i - kPeriod + 1; j <= i; j++) {
      highestHigh = Math.max(highestHigh, highs[j]);
      lowestLow = Math.min(lowestLow, lows[j]);
    }

    const range = highestHigh - lowestLow;
    if (range === 0) {
      k.push(50);
    } else {
      k.push(((closes[i] - lowestLow) / range) * 100);
    }
  }

  // %D = SMA(%K, dPeriod)
  const d: number[] = [];
  for (let i = 0; i < k.length; i++) {
    if (i < dPeriod - 1) {
      d.push(50);
    } else {
      const sum = k.slice(i - dPeriod + 1, i + 1).reduce((a, b) => a + b, 0);
      d.push(sum / dPeriod);
    }
  }

  return { k, d };
}

/**
 * ADX (Average Directional Index)
 * 平均方向性指数
 */
export function calculateADX(
  highs: number[],
  lows: number[],
  closes: number[],
  period: number = 14
): { adx: number[]; plusDi: number[]; minusDi: number[] } {
  const tr: number[] = [];
  const plusDM: number[] = [];
  const minusDM: number[] = [];

  // True Range
  for (let i = 0; i < closes.length; i++) {
    if (i === 0) {
      tr.push(highs[0] - lows[0]);
      plusDM.push(0);
      minusDM.push(0);
    } else {
      const hl = highs[i] - lows[i];
      const hc = Math.abs(highs[i] - closes[i - 1]);
      const lc = Math.abs(lows[i] - closes[i - 1]);
      tr.push(Math.max(hl, hc, lc));

      const plus = highs[i] - highs[i - 1];
      const minus = lows[i - 1] - lows[i];
      plusDM.push(plus > minus && plus > 0 ? plus : 0);
      minusDM.push(minus > plus && minus > 0 ? minus : 0);
    }
  }

  // Smooth
  const atr = calculateSmoothedAverage(tr, period);
  const smoothedPlusDM = calculateSmoothedAverage(plusDM, period);
  const smoothedMinusDM = calculateSmoothedAverage(minusDM, period);

  // +DI, -DI
  const plusDi: number[] = [];
  const minusDi: number[] = [];

  for (let i = 0; i < closes.length; i++) {
    if (atr[i] === 0) {
      plusDi.push(0);
      minusDi.push(0);
    } else {
      plusDi.push((smoothedPlusDM[i] / atr[i]) * 100);
      minusDi.push((smoothedMinusDM[i] / atr[i]) * 100);
    }
  }

  // DX
  const dx: number[] = [];
  for (let i = 0; i < closes.length; i++) {
    const diSum = plusDi[i] + minusDi[i];
    if (diSum === 0) {
      dx.push(0);
    } else {
      dx.push((Math.abs(plusDi[i] - minusDi[i]) / diSum) * 100);
    }
  }

  // ADX
  const adx = calculateSmoothedAverage(dx, period);

  return { adx, plusDi, minusDi };
}

// ============================================
// 趋势指标
// ============================================

/**
 * SMA (Simple Moving Average)
 * 简单移动平均
 */
export function calculateSMA(prices: number[], period: number): number[] {
  const sma: number[] = [];

  for (let i = 0; i < prices.length; i++) {
    if (i < period - 1) {
      sma.push(prices[i]);
    } else {
      const sum = prices.slice(i - period + 1, i + 1).reduce((a, b) => a + b, 0);
      sma.push(sum / period);
    }
  }

  return sma;
}

/**
 * EMA (Exponential Moving Average)
 * 指数移动平均
 */
export function calculateEMA(prices: number[], period: number): number[] {
  const k = 2 / (period + 1);
  const ema: number[] = [];

  for (let i = 0; i < prices.length; i++) {
    if (i === 0) {
      ema.push(prices[i]);
    } else if (i < period - 1) {
      const sum = prices.slice(0, i + 1).reduce((a, b) => a + b, 0);
      ema.push(sum / (i + 1));
    } else if (i === period - 1) {
      const sum = prices.slice(0, period).reduce((a, b) => a + b, 0);
      ema.push(sum / period);
    } else {
      ema.push(prices[i] * k + ema[i - 1] * (1 - k));
    }
  }

  return ema;
}

/**
 * Bollinger Bands
 * 布林带
 */
export function calculateBollingerBands(
  prices: number[],
  period: number = 20,
  stdDev: number = 2
): { upper: number[]; middle: number[]; lower: number[] } {
  const sma = calculateSMA(prices, period);
  const upper: number[] = [];
  const lower: number[] = [];

  for (let i = 0; i < prices.length; i++) {
    if (i < period - 1) {
      upper.push(prices[i]);
      lower.push(prices[i]);
    } else {
      const slice = prices.slice(i - period + 1, i + 1);
      const mean = sma[i];
      const variance = slice.reduce((sum, p) => sum + Math.pow(p - mean, 2), 0) / period;
      const std = Math.sqrt(variance);

      upper.push(mean + stdDev * std);
      lower.push(mean - stdDev * std);
    }
  }

  return { upper, middle: sma, lower };
}

// ============================================
// 波动率指标
// ============================================

/**
 * ATR (Average True Range)
 * 平均真实波幅
 */
export function calculateATR(
  highs: number[],
  lows: number[],
  closes: number[],
  period: number = 14
): number[] {
  const tr: number[] = [];

  for (let i = 0; i < closes.length; i++) {
    if (i === 0) {
      tr.push(highs[0] - lows[0]);
    } else {
      const hl = highs[i] - lows[i];
      const hc = Math.abs(highs[i] - closes[i - 1]);
      const lc = Math.abs(lows[i] - closes[i - 1]);
      tr.push(Math.max(hl, hc, lc));
    }
  }

  return calculateSmoothedAverage(tr, period);
}

/**
 * 计算平滑平均 (Wilder's Smoothing)
 */
function calculateSmoothedAverage(values: number[], period: number): number[] {
  const result: number[] = [];

  for (let i = 0; i < values.length; i++) {
    if (i < period - 1) {
      result.push(values[i]);
    } else if (i === period - 1) {
      const sum = values.slice(0, period).reduce((a, b) => a + b, 0);
      result.push(sum / period);
    } else {
      const prev = result[i - 1];
      result.push((prev * (period - 1) + values[i]) / period);
    }
  }

  return result;
}

// ============================================
// 成交量指标
// ============================================

/**
 * OBV (On Balance Volume)
 * 能量潮
 */
export function calculateOBV(closes: number[], volumes: number[]): number[] {
  const obv: number[] = [0];

  for (let i = 1; i < closes.length; i++) {
    if (closes[i] > closes[i - 1]) {
      obv.push(obv[i - 1] + volumes[i]);
    } else if (closes[i] < closes[i - 1]) {
      obv.push(obv[i - 1] - volumes[i]);
    } else {
      obv.push(obv[i - 1]);
    }
  }

  return obv;
}

/**
 * VWAP (Volume Weighted Average Price)
 * 成交量加权平均价
 */
export function calculateVWAP(
  highs: number[],
  lows: number[],
  closes: number[],
  volumes: number[]
): number[] {
  const typicalPrices: number[] = [];
  for (let i = 0; i < closes.length; i++) {
    typicalPrices.push((highs[i] + lows[i] + closes[i]) / 3);
  }

  const vwap: number[] = [];
  let cumVolume = 0;
  let cumTPV = 0;

  for (let i = 0; i < typicalPrices.length; i++) {
    cumVolume += volumes[i];
    cumTPV += typicalPrices[i] * volumes[i];
    vwap.push(cumTPV / cumVolume);
  }

  return vwap;
}

// ============================================
// 振荡器
// ============================================

/**
 * CCI (Commodity Channel Index)
 * 商品通道指数
 */
export function calculateCCI(
  highs: number[],
  lows: number[],
  closes: number[],
  period: number = 20
): number[] {
  const tp: number[] = [];
  for (let i = 0; i < closes.length; i++) {
    tp.push((highs[i] + lows[i] + closes[i]) / 3);
  }

  const sma = calculateSMA(tp, period);
  const cci: number[] = [];

  for (let i = 0; i < tp.length; i++) {
    if (i < period - 1) {
      cci.push(0);
    } else {
      const meanDeviation =
        tp.slice(i - period + 1, i + 1).reduce((sum, p) => sum + Math.abs(p - sma[i]), 0) /
        period;
      cci.push((tp[i] - sma[i]) / (0.015 * meanDeviation));
    }
  }

  return cci;
}

/**
 * MFI (Money Flow Index)
 * 资金流量指数
 */
export function calculateMFI(
  highs: number[],
  lows: number[],
  closes: number[],
  volumes: number[],
  period: number = 14
): number[] {
  const tp: number[] = [];
  const mf: number[] = [];
  const mfSign: number[] = [];

  for (let i = 0; i < closes.length; i++) {
    tp.push((highs[i] + lows[i] + closes[i]) / 3);
    mf.push(tp[i] * volumes[i]);

    if (i === 0) {
      mfSign.push(0);
    } else {
      mfSign.push(tp[i] > tp[i - 1] ? 1 : tp[i] < tp[i - 1] ? -1 : 0);
    }
  }

  const mfi: number[] = [];

  for (let i = 0; i < mf.length; i++) {
    if (i < period) {
      mfi.push(50);
      continue;
    }

    let posMF = 0;
    let negMF = 0;

    for (let j = i - period + 1; j <= i; j++) {
      if (mfSign[j] > 0) posMF += mf[j];
      else if (mfSign[j] < 0) negMF += mf[j];
    }

    if (negMF === 0) {
      mfi.push(100);
    } else {
      const mr = posMF / negMF;
      mfi.push(100 - 100 / (1 + mr));
    }
  }

  return mfi;
}

// ============================================
// 组合指标计算
// ============================================

/**
 * 计算完整指标集
 * 借鉴 freqtrade populate_indicators
 */
export function calculateAllIndicators(
  highs: number[],
  lows: number[],
  closes: number[],
  volumes: number[]
): {
  rsi: number[];
  macd: { macd: number[]; signal: number[]; histogram: number[] };
  stoch: { k: number[]; d: number[] };
  adx: { adx: number[]; plusDi: number[]; minusDi: number[] };
  bollinger: { upper: number[]; middle: number[]; lower: number[] };
  atr: number[];
  cci: number[];
  mfi: number[];
  sma20: number[];
  sma50: number[];
  ema20: number[];
  ema50: number[];
} {
  return {
    rsi: calculateRSI(closes, 14),
    macd: calculateMACD(closes),
    stoch: calculateStochastic(highs, lows, closes),
    adx: calculateADX(highs, lows, closes),
    bollinger: calculateBollingerBands(closes),
    atr: calculateATR(highs, lows, closes),
    cci: calculateCCI(highs, lows, closes),
    mfi: calculateMFI(highs, lows, closes, volumes),
    sma20: calculateSMA(closes, 20),
    sma50: calculateSMA(closes, 50),
    ema20: calculateEMA(closes, 20),
    ema50: calculateEMA(closes, 50),
  };
}
