/**
 * Copyright 2026 NEMT Lab
 *
 * NEMT Kline Data Types
 * K线数据类型定义
 */

/**
 * K线数据
 */
export interface KlineData {
  /** 时间戳 (ms) */
  time: number;
  /** 开盘价 */
  open: number;
  /** 最高价 */
  high: number;
  /** 最低价 */
  low: number;
  /** 收盘价 */
  close: number;
  /** 成交量 */
  volume: number;
}

/**
 * DataFrame - 用于策略计算的扁平数据结构
 * 借鉴 freqtrade pandas DataFrame
 */
export interface DataFrame {
  /** 时间戳数组 */
  time: number[];
  /** 开盘价数组 */
  open: number[];
  /** 最高价数组 */
  high: number[];
  /** 最低价数组 */
  low: number[];
  /** 收盘价数组 */
  close: number[];
  /** 成交量数组 */
  volume: number[];

  // 信号列 (可选)
  /** 入场做多信号 */
  enterLong?: number[];
  /** 入场做空信号 */
  enterShort?: number[];
  /** 出场做多信号 */
  exitLong?: number[];
  /** 出场做空信号 */
  exitShort?: number[];
  /** 入场标签 */
  enterTag?: string[];
  /** 出场标签 */
  exitTag?: string[];

  // 技术指标 (可选)
  indicators?: Record<string, number[]>;

  // NEMT 指标 (可选)
  /** NEMT ψ 值 */
  psi?: number[];
  /** NEMT φ 值 */
  phi?: number[];
  /** NEMT 熵值 */
  entropy?: number[];
  /** NEMT 相位 */
  nemtPhase?: Array<'stable' | 'critical' | 'critical_up' | 'critical_down' | 'decay'>;
  /** NEMT 波幅 */
  waveAmplitude?: number[];
  /** NEMT 频率 */
  waveFrequency?: number[];
}

/**
 * OHLCV 辅助函数
 */
export function createDataFrame(klines: KlineData[]): DataFrame {
  return {
    time: klines.map((k) => k.time),
    open: klines.map((k) => k.open),
    high: klines.map((k) => k.high),
    low: klines.map((k) => k.low),
    close: klines.map((k) => k.close),
    volume: klines.map((k) => k.volume),
  };
}

export function dataFrameToKlines(df: DataFrame): KlineData[] {
  const klines: KlineData[] = [];
  for (let i = 0; i < df.close.length; i++) {
    klines.push({
      time: df.time[i],
      open: df.open[i],
      high: df.high[i],
      low: df.low[i],
      close: df.close[i],
      volume: df.volume[i],
    });
  }
  return klines;
}
