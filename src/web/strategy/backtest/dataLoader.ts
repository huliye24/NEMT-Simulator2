/**
 * Copyright 2026 NEMT Lab
 *
 * Backtest Data Loader
 * 数据加载器 - 支持 Binance / CSV / 内存数据
 */

import type { DataFrame, KlineData } from './types';

// ============================================
// Binance 数据加载器
// ============================================

export interface BinanceKline {
  openTime: number;
  open: string;
  high: string;
  low: string;
  close: string;
  volume: string;
  closeTime: number;
}

const BINANCE_BASE = 'https://api.binance.com';

/** 从 Binance 加载 K 线数据 */
export async function loadFromBinance(
  symbol: string,
  interval: string,
  startTime?: number,
  endTime?: number,
  limit: number = 500
): Promise<DataFrame> {
  const params = new URLSearchParams({
    symbol: symbol.toUpperCase(),
    interval,
    limit: String(limit),
  });
  if (startTime) params.set('startTime', String(startTime));
  if (endTime) params.set('endTime', String(endTime));

  const url = `${BINANCE_BASE}/api/v3/klines?${params.toString()}`;
  const response = await fetch(url);

  if (!response.ok) {
    throw new Error(`Binance API error: ${response.status}`);
  }

  const data: BinanceKline[] = await response.json();

  return klinesToDataFrame(data);
}

/** 分段加载大量数据 */
export async function loadBinanceRange(
  symbol: string,
  interval: string,
  startTime: number,
  endTime: number,
  onProgress?: (loaded: number, total: number) => void
): Promise<DataFrame> {
  const intervals: Record<string, number> = {
    '1m': 60000,
    '5m': 300000,
    '15m': 900000,
    '30m': 1800000,
    '1h': 3600000,
    '4h': 14400000,
    '1d': 86400000,
    '1w': 604800000,
  };

  const intervalMs = intervals[interval] || 3600000;
  const maxBars = 1000;
  const batchMs = intervalMs * maxBars;

  const allData: BinanceKline[] = [];
  let current = startTime;

  while (current < endTime) {
    const batchEnd = Math.min(current + batchMs, endTime);
    const data = await loadFromBinance(symbol, interval, current, batchEnd, maxBars);

    // 合并到 allData
    const klines: BinanceKline[] = (data as any)._raw || [];
    allData.push(...klines);

    if (data.time.length > 0) {
      current = data.time[data.time.length - 1] + intervalMs;
    } else {
      current = batchEnd;
    }

    if (onProgress) {
      onProgress(current - startTime, endTime - startTime);
    }
  }

  return klinesToDataFrame(allData);
}

/** K线转 DataFrame */
function klinesToDataFrame(klines: BinanceKline[]): DataFrame {
  const df: DataFrame = {
    time: [],
    open: [],
    high: [],
    low: [],
    close: [],
    volume: [],
  };

  for (const k of klines) {
    df.time.push(k.openTime);
    df.open.push(parseFloat(k.open));
    df.high.push(parseFloat(k.high));
    df.low.push(parseFloat(k.low));
    df.close.push(parseFloat(k.close));
    df.volume.push(parseFloat(k.volume));
  }

  return df;
}

// ============================================
// CSV 加载器
// ============================================

/** 从 CSV 加载数据 */
export async function loadFromCSV(csvText: string): Promise<DataFrame> {
  const lines = csvText.trim().split('\n');
  if (lines.length < 2) throw new Error('CSV empty or no header');

  const header = lines[0].toLowerCase().split(',').map((h) => h.trim());

  // 尝试多种列名映射
  const timeIdx = header.findIndex((h) =>
    ['time', 'timestamp', 'date', 'datetime', 't'].includes(h)
  );
  const openIdx = header.findIndex((h) =>
    ['open', 'o'].includes(h)
  );
  const highIdx = header.findIndex((h) =>
    ['high', 'h'].includes(h)
  );
  const lowIdx = header.findIndex((h) =>
    ['low', 'l'].includes(h)
  );
  const closeIdx = header.findIndex((h) =>
    ['close', 'c'].includes(h)
  );
  const volumeIdx = header.findIndex((h) =>
    ['volume', 'vol', 'v', 'q'].includes(h)
  );

  if (closeIdx === -1) throw new Error('CSV must have close column');

  const df: DataFrame = {
    time: [],
    open: [],
    high: [],
    low: [],
    close: [],
    volume: [],
  };

  for (let i = 1; i < lines.length; i++) {
    const cols = lines[i].split(',').map((c) => c.trim());
    const time = timeIdx >= 0 ? parseTime(cols[timeIdx]) : i * 60000;
    const open = openIdx >= 0 ? parseFloat(cols[openIdx]) : parseFloat(cols[closeIdx]);
    const high = highIdx >= 0 ? parseFloat(cols[highIdx]) : parseFloat(cols[closeIdx]);
    const low = lowIdx >= 0 ? parseFloat(cols[lowIdx]) : parseFloat(cols[closeIdx]);
    const close = parseFloat(cols[closeIdx]);
    const volume = volumeIdx >= 0 ? parseFloat(cols[volumeIdx]) : 0;

    df.time.push(time);
    df.open.push(open);
    df.high.push(high);
    df.low.push(low);
    df.close.push(close);
    df.volume.push(volume);
  }

  return df;
}

/** 解析时间字符串 */
function parseTime(value: string): number {
  if (!value) return 0;
  const num = Number(value);
  if (!isNaN(num)) return num;

  const date = new Date(value);
  if (!isNaN(date.getTime())) return date.getTime();

  return 0;
}

/** 解析 CSV 文件 */
export async function parseCSVFile(file: File): Promise<DataFrame> {
  const text = await file.text();
  return loadFromCSV(text);
}

// ============================================
// 内存数据生成
// ============================================

/** 生成模拟数据 */
export function generateMockData(
  bars: number = 500,
  interval: number = 3600000,
  startPrice: number = 50000,
  volatility: number = 0.02,
  trend: number = 0.0001
): DataFrame {
  const df: DataFrame = {
    time: [],
    open: [],
    high: [],
    low: [],
    close: [],
    volume: [],
  };

  let price = startPrice;
  let time = Date.now() - bars * interval;

  for (let i = 0; i < bars; i++) {
    const change = (Math.random() - 0.5) * 2 * volatility + trend;
    const open = price;
    price = price * (1 + change);
    const close = price;
    const high = Math.max(open, close) * (1 + Math.random() * volatility * 0.5);
    const low = Math.min(open, close) * (1 - Math.random() * volatility * 0.5);
    const volume = 100 + Math.random() * 500;

    df.time.push(time);
    df.open.push(open);
    df.high.push(high);
    df.low.push(low);
    df.close.push(close);
    df.volume.push(volume);

    time += interval;
  }

  return df;
}

/** 生成带趋势的数据 */
export function generateTrendingData(
  bars: number = 500,
  interval: number = 3600000,
  startPrice: number = 50000,
  phases: number = 4
): DataFrame {
  const df: DataFrame = {
    time: [],
    open: [],
    high: [],
    low: [],
    close: [],
    volume: [],
  };

  let price = startPrice;
  let time = Date.now() - bars * interval;
  const barsPerPhase = Math.floor(bars / phases);

  for (let i = 0; i < bars; i++) {
    const phaseIndex = Math.floor(i / barsPerPhase);
    const phaseProgress = (i % barsPerPhase) / barsPerPhase;

    let trend: number;
    let volatility: number;

    switch (phaseIndex % phases) {
      case 0:
        // 上涨
        trend = 0.001;
        volatility = 0.015;
        break;
      case 1:
        // 盘整
        trend = 0;
        volatility = 0.01;
        break;
      case 2:
        // 下跌
        trend = -0.0008;
        volatility = 0.018;
        break;
      default:
        // 反弹
        trend = 0.0005;
        volatility = 0.012;
    }

    // 相位内趋势变化
    const phaseTrend = Math.sin(phaseProgress * Math.PI * 2) * 0.0003;
    const change = (Math.random() - 0.5) * 2 * volatility + trend + phaseTrend;

    const open = price;
    price = price * (1 + change);
    const close = price;
    const high = Math.max(open, close) * (1 + Math.random() * volatility * 0.5);
    const low = Math.min(open, close) * (1 - Math.random() * volatility * 0.5);
    const volume = 100 + Math.random() * 500 + (Math.abs(change) > volatility ? 200 : 0);

    df.time.push(time);
    df.open.push(open);
    df.high.push(high);
    df.low.push(low);
    df.close.push(close);
    df.volume.push(volume);

    time += interval;
  }

  return df;
}

// ============================================
// 数据缓存
// ============================================

const dataCache = new Map<string, DataFrame>();

export function cacheData(key: string, df: DataFrame): void {
  dataCache.set(key, df);
}

export function getCachedData(key: string): DataFrame | undefined {
  return dataCache.get(key);
}

export function clearDataCache(): void {
  dataCache.clear();
}

// ============================================
// 数据验证
// ============================================

export interface DataValidationResult {
  valid: boolean;
  errors: string[];
  warnings: string[];
  stats: {
    bars: number;
    startTime: number;
    endTime: number;
    avgVolume: number;
    priceRange: { min: number; max: number };
  };
}

export function validateData(df: DataFrame): DataValidationResult {
  const errors: string[] = [];
  const warnings: string[] = [];
  const result: DataValidationResult = {
    valid: false,
    errors,
    warnings,
    stats: {
      bars: df.close.length,
      startTime: df.time[0] || 0,
      endTime: df.time[df.time.length - 1] || 0,
      avgVolume: 0,
      priceRange: { min: 0, max: 0 },
    },
  };

  // 基本检查
  if (df.close.length === 0) {
    errors.push('No data');
    return result;
  }

  if (df.close.length < 50) {
    warnings.push(`Only ${df.close.length} bars, recommend at least 100`);
  }

  // 数据完整性
  const hasOHLCV = df.open.length === df.close.length &&
                   df.high.length === df.close.length &&
                   df.low.length === df.close.length &&
                   df.volume.length === df.close.length;

  if (!hasOHLCV) {
    errors.push('OHLCV columns have different lengths');
    return result;
  }

  // 价格合理性
  const prices = df.close.filter((p) => !isNaN(p) && p > 0);
  if (prices.length === 0) {
    errors.push('No valid prices');
    return result;
  }

  const min = Math.min(...prices);
  const max = Math.max(...prices);
  result.stats.priceRange = { min, max };

  if (max / min > 100) {
    warnings.push('Extreme price range detected, check for data errors');
  }

  // 时间顺序
  for (let i = 1; i < df.time.length; i++) {
    if (df.time[i] <= df.time[i - 1]) {
      errors.push(`Time not increasing at index ${i}`);
      break;
    }
  }

  // 统计
  result.stats.avgVolume = df.volume.reduce((a, b) => a + b, 0) / df.volume.length;
  result.valid = errors.length === 0;

  return result;
}
