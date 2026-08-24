/**
 * Copyright 2026 NEMT Lab
 *
 * NEMT Alpha Dataset
 * 借鉴 vnpy.alpha dataset
 *
 * 功能：
 * - 因子特征工程
 * - Alpha 158 因子
 * - 数据批处理
 */

import { BarData } from '../../event/eventEngine';

// ============================================
// 数据类型
// ============================================

export interface FactorData {
  /** 因子名称 */
  name: string;
  /** 因子值 */
  value: number;
  /** 时间戳 */
  timestamp: number;
}

export interface FeatureRow {
  /** 时间戳 */
  timestamp: number;
  /** 特征 */
  features: Record<string, number>;
  /** 标签 */
  label?: number;
}

export interface DatasetConfig {
  /** 特征列表 */
  features: string[];
  /** 标签列 */
  label?: string;
  /** 回看窗口 */
  lookback: number;
  /** 预测窗口 */
  horizon: number;
}

// ============================================
// 因子计算器基类
// ============================================

export abstract class BaseFactor {
  abstract name: string;

  calculate(data: BarData[]): number[] {
    const result: number[] = [];
    for (let i = 0; i < data.length; i++) {
      result.push(this._calculate(data.slice(0, i + 1)));
    }
    return result;
  }

  protected abstract _calculate(data: BarData[]): number;
}

// ============================================
// Alpha 158 因子 (源于微软 Qlib)
// ============================================

export class Alpha158 {
  /**
   * 计算 Alpha 158 因子集
   * 源自微软 Qlib 项目
   */
  static calculate(data: BarData[]): Record<string, number[]> {
    if (data.length < 100) {
      return {};
    }

    const closes = data.map((d) => d.closePrice);
    const highs = data.map((d) => d.highPrice);
    const lows = data.map((d) => d.lowPrice);
    const volumes = data.map((d) => d.volume);

    return {
      // 收盘价相关
      close: closes,
      close_pct_change_1: this.pctChange(closes, 1),
      close_pct_change_5: this.pctChange(closes, 5),
      close_pct_change_10: this.pctChange(closes, 10),
      close_pct_change_20: this.pctChange(closes, 20),

      // 成交量相关
      volume: volumes,
      volume_pct_change_1: this.pctChange(volumes, 1),
      volume_pct_change_5: this.pctChange(volumes, 5),

      // 均价相关
      vwap: this.vwap(closes, volumes, 20),

      // 波动率
      volatility_5: this.volatility(closes, 5),
      volatility_10: this.volatility(closes, 10),
      volatility_20: this.volatility(closes, 20),

      // RSI
      rsi_6: this.rsi(closes, 6),
      rsi_12: this.rsi(closes, 12),
      rsi_24: this.rsi(closes, 24),

      // MACD
      macd: this.macd(closes, 12, 26, 9).macd,
      macd_signal: this.macd(closes, 12, 26, 9).signal,
      macd_hist: this.macd(closes, 12, 26, 9).histogram,

      // 布林带
      bb_upper: this.bollingerBands(closes, 20).upper,
      bb_middle: this.bollingerBands(closes, 20).middle,
      bb_lower: this.bollingerBands(closes, 20).lower,

      // ATR
      atr_14: this.atr(highs, lows, closes, 14),

      // KDJ
      kdj_k: this.kdj(highs, lows, closes, 9, 3, 3).k,
      kdj_d: this.kdj(highs, lows, closes, 9, 3, 3).d,
      kdj_j: this.kdj(highs, lows, closes, 9, 3, 3).j,

      // 动量
      momentum_5: this.momentum(closes, 5),
      momentum_10: this.momentum(closes, 10),
      momentum_20: this.momentum(closes, 20),
    };
  }

  // 百分比变化
  static pctChange(data: number[], period: number): number[] {
    const result: number[] = [];
    for (let i = 0; i < data.length; i++) {
      if (i < period) {
        result.push(0);
      } else {
        result.push((data[i] - data[i - period]) / data[i - period]);
      }
    }
    return result;
  }

  // VWAP
  static vwap(closes: number[], volumes: number[], period: number): number[] {
    const result: number[] = [];
    for (let i = 0; i < closes.length; i++) {
      if (i < period - 1) {
        result.push(closes[i]);
        continue;
      }
      let sum = 0;
      let volSum = 0;
      for (let j = i - period + 1; j <= i; j++) {
        sum += closes[j] * volumes[j];
        volSum += volumes[j];
      }
      result.push(volSum > 0 ? sum / volSum : closes[i]);
    }
    return result;
  }

  // 波动率
  static volatility(data: number[], period: number): number[] {
    const result: number[] = [];
    for (let i = 0; i < data.length; i++) {
      if (i < period) {
        result.push(0);
        continue;
      }
      const slice = data.slice(i - period, i);
      const returns: number[] = [];
      for (let j = 1; j < slice.length; j++) {
        returns.push((slice[j] - slice[j - 1]) / slice[j - 1]);
      }
      const mean = returns.reduce((a, b) => a + b, 0) / returns.length;
      const variance = returns.reduce((a, b) => a + (b - mean) ** 2, 0) / returns.length;
      result.push(Math.sqrt(variance) * Math.sqrt(252));
    }
    return result;
  }

  // RSI
  static rsi(data: number[], period: number): number[] {
    const result: number[] = [];
    const gains: number[] = [];
    const losses: number[] = [];

    for (let i = 1; i < data.length; i++) {
      const change = data[i] - data[i - 1];
      gains.push(change > 0 ? change : 0);
      losses.push(change < 0 ? -change : 0);

      if (i < period) {
        result.push(50);
        continue;
      }

      const avgGain = gains.slice(-period).reduce((a, b) => a + b, 0) / period;
      const avgLoss = losses.slice(-period).reduce((a, b) => a + b, 0) / period;

      if (avgLoss === 0) {
        result.push(100);
      } else {
        const rs = avgGain / avgLoss;
        result.push(100 - 100 / (1 + rs));
      }
    }

    return result;
  }

  // MACD
  static macd(
    data: number[],
    fast: number,
    slow: number,
    signal: number
  ): { macd: number[]; signal: number[]; histogram: number[] } {
    const emaFast = this.ema(data, fast);
    const emaSlow = this.ema(data, slow);
    const macdLine: number[] = [];

    for (let i = 0; i < data.length; i++) {
      macdLine.push(emaFast[i] - emaSlow[i]);
    }

    const signalLine = this.ema(macdLine, signal);
    const histogram: number[] = [];

    for (let i = 0; i < macdLine.length; i++) {
      histogram.push(macdLine[i] - signalLine[i]);
    }

    return { macd: macdLine, signal: signalLine, histogram };
  }

  // EMA
  static ema(data: number[], period: number): number[] {
    const k = 2 / (period + 1);
    const result: number[] = [];

    for (let i = 0; i < data.length; i++) {
      if (i === 0) {
        result.push(data[i]);
      } else if (i < period) {
        const sum = data.slice(0, i + 1).reduce((a, b) => a + b, 0);
        result.push(sum / (i + 1));
      } else if (i === period) {
        const sum = data.slice(0, period).reduce((a, b) => a + b, 0);
        result.push(sum / period);
      } else {
        result.push(data[i] * k + result[i - 1] * (1 - k));
      }
    }

    return result;
  }

  // 布林带
  static bollingerBands(
    data: number[],
    period: number,
    std: number = 2
  ): { upper: number[]; middle: number[]; lower: number[] } {
    const sma = this.sma(data, period);
    const upper: number[] = [];
    const lower: number[] = [];

    for (let i = 0; i < data.length; i++) {
      if (i < period - 1) {
        upper.push(data[i]);
        lower.push(data[i]);
      } else {
        const slice = data.slice(i - period + 1, i + 1);
        const mean = sma[i];
        const variance = slice.reduce((a, b) => a + (b - mean) ** 2, 0) / period;
        const stdDev = Math.sqrt(variance);
        upper.push(mean + std * stdDev);
        lower.push(mean - std * stdDev);
      }
    }

    return { upper, middle: sma, lower };
  }

  // SMA
  static sma(data: number[], period: number): number[] {
    const result: number[] = [];
    for (let i = 0; i < data.length; i++) {
      if (i < period - 1) {
        result.push(data[i]);
      } else {
        const sum = data.slice(i - period + 1, i + 1).reduce((a, b) => a + b, 0);
        result.push(sum / period);
      }
    }
    return result;
  }

  // ATR
  static atr(highs: number[], lows: number[], closes: number[], period: number): number[] {
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
    return this.sma(tr, period);
  }

  // KDJ
  static kdj(
    highs: number[],
    lows: number[],
    closes: number[],
    period: number,
    kPeriod: number,
    dPeriod: number
  ): { k: number[]; d: number[]; j: number[] } {
    const k: number[] = [];
    const d: number[] = [];
    const j: number[] = [];

    for (let i = 0; i < closes.length; i++) {
      if (i < period - 1) {
        k.push(50);
        d.push(50);
        j.push(50);
        continue;
      }

      let highestHigh = -Infinity;
      let lowestLow = Infinity;

      for (let j = i - period + 1; j <= i; j++) {
        highestHigh = Math.max(highestHigh, highs[j]);
        lowestLow = Math.min(lowestLow, lows[j]);
      }

      const range = highestHigh - lowestLow;
      const rsv = range === 0 ? 50 : ((closes[i] - lowestLow) / range) * 100;

      const prevK = k.length > 0 ? k[k.length - 1] : 50;
      const prevD = d.length > 0 ? d[d.length - 1] : 50;

      k.push((2 / 3) * prevK + (1 / 3) * rsv);
      d.push((2 / 3) * prevD + (1 / 3) * k[k.length - 1]);
      j.push(3 * k[k.length - 1] - 2 * d[d.length - 1]);
    }

    return { k, d, j };
  }

  // 动量
  static momentum(data: number[], period: number): number[] {
    return this.pctChange(data, period);
  }
}

// ============================================
// 数据集
// ============================================

export class Dataset {
  private config: DatasetConfig;
  private data: Map<number, FeatureRow> = new Map();

  constructor(config: DatasetConfig) {
    this.config = config;
  }

  /**
   * 添加数据
   */
  addData(timestamp: number, features: Record<string, number>, label?: number): void {
    this.data.set(timestamp, { timestamp, features, label });
  }

  /**
   * 获取特征
   */
  getFeatures(timestamp: number): Record<string, number> | undefined {
    return this.data.get(timestamp)?.features;
  }

  /**
   * 获取标签
   */
  getLabel(timestamp: number): number | undefined {
    return this.data.get(timestamp)?.label;
  }

  /**
   * 获取批次
   */
  getBatch(start: number, end: number): FeatureRow[] {
    const rows: FeatureRow[] = [];
    for (const [timestamp, row] of this.data) {
      if (timestamp >= start && timestamp <= end) {
        rows.push(row);
      }
    }
    return rows.sort((a, b) => a.timestamp - b.timestamp);
  }

  /**
   * 转置为训练数据
   */
  toTrainingData(): { X: number[][]; y: number[]; timestamps: number[] } {
    const sortedData = Array.from(this.data.values()).sort((a, b) => a.timestamp - b.timestamp);
    const X: number[][] = [];
    const y: number[] = [];
    const timestamps: number[] = [];

    for (const row of sortedData) {
      const featureValues = this.config.features.map((f) => row.features[f] || 0);
      X.push(featureValues);
      if (row.label !== undefined) {
        y.push(row.label);
      }
      timestamps.push(row.timestamp);
    }

    return { X, y, timestamps };
  }
}

// ============================================
// 特征表达式计算
// ============================================

export class FeatureExpression {
  /**
   * 解析并计算特征表达式
   */
  static evaluate(expression: string, data: BarData[]): number[] {
    // 简化实现，实际应该解析表达式语法树
    const closes = data.map((d) => d.closePrice);
    const volumes = data.map((d) => d.volume);

    if (expression === 'close') return closes;
    if (expression === 'volume') return volumes;
    if (expression.startsWith('return_')) {
      const period = parseInt(expression.split('_')[1]);
      return Alpha158.pctChange(closes, period);
    }
    if (expression === 'rsi') return Alpha158.rsi(closes, 14);
    if (expression === 'macd') return Alpha158.macd(closes, 12, 26, 9).macd;

    return closes;
  }
}
