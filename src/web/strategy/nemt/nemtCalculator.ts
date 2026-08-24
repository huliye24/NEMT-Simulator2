/**
 * Copyright 2026 NEMT Lab
 *
 * NEMT State Calculator
 * 计算 NEMT 状态：ψ (增长率), φ (衰减率), 熵, 相位
 */

export interface NEMTState {
  /** ψ 增长率 */
  psi: number;
  /** φ 衰减率 */
  phi: number;
  /** 熵值 */
  entropy: number;
  /** 相位 */
  phase: 'stable' | 'critical' | 'critical_up' | 'critical_down' | 'decay';
  /** 波幅 */
  waveAmplitude: number;
  /** 频率 */
  waveFrequency: number;
}

export interface NEMTConfig {
  /** 临界熵阈值 */
  criticalEntropy: number;
  /** 临界 ψ 阈值 */
  criticalPsi: number;
  /** 稳定 ψ 阈值 */
  stablePsi: number;
  /** EMA 衰减因子 */
  emaAlpha: number;
}

const DEFAULT_CONFIG: NEMTConfig = {
  criticalEntropy: 0.7,
  criticalPsi: 0.5,
  stablePsi: 0.3,
  emaAlpha: 0.3,
};

export class NEMTStateCalculator {
  private config: NEMTConfig;

  constructor(config?: Partial<NEMTConfig>) {
    this.config = { ...DEFAULT_CONFIG, ...config };
  }

  /**
   * 计算单个状态的 NEMT 指标
   */
  calculate(prices: number[]): NEMTState {
    if (prices.length < 2) {
      return {
        psi: 0,
        phi: 0,
        entropy: 0,
        phase: 'stable',
        waveAmplitude: 0,
        waveFrequency: 0,
      };
    }

    // 计算收益率
    const returns = this.calculateReturns(prices);

    // 计算 ψ (增长率) - EMA 动量
    const psi = this.calculatePsi(returns);

    // 计算 φ (衰减率) - 年化波动率
    const phi = this.calculatePhi(returns);

    // 计算熵
    const entropy = this.calculateEntropy(prices);

    // 确定相位
    const phase = this.determinePhase(psi, phi, entropy);

    // 计算波幅和频率
    const waveAmplitude = this.calculateWaveAmplitude(prices);
    const waveFrequency = this.calculateWaveFrequency(prices);

    return { psi, phi, entropy, phase, waveAmplitude, waveFrequency };
  }

  /**
   * 批量计算 NEMT 状态
   */
  calculateBatch(prices: number[]): NEMTState[] {
    const states: NEMTState[] = [];

    for (let i = 0; i < prices.length; i++) {
      const slice = prices.slice(0, i + 1);
      states.push(this.calculate(slice));
    }

    return states;
  }

  /**
   * 计算收益率序列
   */
  private calculateReturns(prices: number[]): number[] {
    const returns: number[] = [];

    for (let i = 1; i < prices.length; i++) {
      const ret = (prices[i] - prices[i - 1]) / prices[i - 1];
      returns.push(ret);
    }

    return returns;
  }

  /**
   * 计算 ψ (增长率) - 指数加权动量
   */
  private calculatePsi(returns: number[]): number {
    if (returns.length === 0) return 0;

    // 使用 EMA 计算加权动量
    let ema = returns[0];
    const alpha = this.config.emaAlpha;

    for (let i = 1; i < returns.length; i++) {
      ema = alpha * returns[i] + (1 - alpha) * ema;
    }

    // 转换为百分比
    return ema * 100;
  }

  /**
   * 计算 φ (衰减率) - 年化波动率
   */
  private calculatePhi(returns: number[]): number {
    if (returns.length < 2) return 0;

    // 计算标准差
    const mean = returns.reduce((a, b) => a + b, 0) / returns.length;
    const squaredDiffs = returns.map(r => Math.pow(r - mean, 2));
    const variance = squaredDiffs.reduce((a, b) => a + b, 0) / returns.length;
    const stdDev = Math.sqrt(variance);

    // 年化 (假设每天 24 小时, 每小时一个数据点)
    const annualizedVol = stdDev * Math.sqrt(24 * 365);

    return annualizedVol * 100;
  }

  /**
   * 计算熵值 (价格分布的不确定性)
   */
  private calculateEntropy(prices: number[]): number {
    if (prices.length < 5) return 0.5; // 默认中等熵

    // 创建价格区间直方图
    const min = Math.min(...prices);
    const max = Math.max(...prices);
    const range = max - min;

    if (range === 0) return 0;

    const binCount = Math.min(10, Math.floor(prices.length / 5));
    const binWidth = range / binCount;
    const bins = new Array(binCount).fill(0);

    // 分配价格到区间
    for (const price of prices) {
      const binIndex = Math.min(
        Math.floor((price - min) / binWidth),
        binCount - 1
      );
      bins[binIndex]++;
    }

    // 计算概率分布
    const total = prices.length;
    const probabilities = bins.map(b => b / total).filter(p => p > 0);

    // 计算香农熵
    const entropy = probabilities.reduce(
      (sum, p) => sum - p * Math.log2(p),
      0
    );

    // 归一化到 [0, 1]
    const maxEntropy = Math.log2(binCount);
    return maxEntropy > 0 ? entropy / maxEntropy : 0;
  }

  /**
   * 确定市场相位
   */
  private determinePhase(psi: number, phi: number, entropy: number): NEMTState['phase'] {
    const { criticalEntropy, criticalPsi, stablePsi } = this.config;

    // 临界状态判断
    if (entropy > criticalEntropy) {
      if (psi > criticalPsi) {
        return 'critical_up';
      } else if (psi < -criticalPsi) {
        return 'critical_down';
      } else {
        return 'critical';
      }
    }

    // 稳定状态判断
    if (entropy < (1 - criticalEntropy) / 2) {
      if (psi > stablePsi) {
        return 'stable';
      } else if (psi < -stablePsi) {
        return 'stable';
      } else {
        return 'decay';
      }
    }

    return 'stable';
  }

  /**
   * 计算波幅
   */
  private calculateWaveAmplitude(prices: number[]): number {
    if (prices.length < 2) return 0;

    const max = Math.max(...prices);
    const min = Math.min(...prices);
    const avg = prices.reduce((a, b) => a + b, 0) / prices.length;

    return avg > 0 ? ((max - min) / avg) * 100 : 0;
  }

  /**
   * 计算频率 (简化版 - 基于零交叉)
   */
  private calculateWaveFrequency(prices: number[]): number {
    if (prices.length < 3) return 0;

    // 计算价格变化方向
    let crosses = 0;
    for (let i = 2; i < prices.length; i++) {
      const prevDiff = prices[i - 1] - prices[i - 2];
      const currDiff = prices[i] - prices[i - 1];

      // 检查方向变化
      if ((prevDiff > 0 && currDiff < 0) || (prevDiff < 0 && currDiff > 0)) {
        crosses++;
      }
    }

    // 归一化频率
    return crosses / (prices.length - 2);
  }

  /**
   * 获取相位信号
   */
  getPhaseSignal(state: NEMTState): { signal: 'BUY' | 'SELL' | 'HOLD'; confidence: number } {
    const { phase, psi, entropy } = state;
    const { criticalPsi } = this.config;

    switch (phase) {
      case 'critical_up':
        // 高熵 + 高 ψ → 强买入信号
        const buyConfidence = Math.min(1, 0.5 + Math.abs(psi) / 100 + entropy / 2);
        return { signal: 'BUY', confidence: buyConfidence };

      case 'critical_down':
        // 高熵 + 低 ψ → 强卖出信号
        const sellConfidence = Math.min(1, 0.5 + Math.abs(psi) / 100 + entropy / 2);
        return { signal: 'SELL', confidence: sellConfidence };

      case 'stable':
        // 低熵 + 中等 ψ → 观望
        if (Math.abs(psi) > this.config.stablePsi) {
          return {
            signal: psi > 0 ? 'BUY' : 'SELL',
            confidence: 0.5,
          };
        }
        return { signal: 'HOLD', confidence: 0.3 };

      case 'decay':
        // 低熵 + 低 ψ → 观望
        return { signal: 'HOLD', confidence: 0.2 };

      default:
        return { signal: 'HOLD', confidence: 0 };
    }
  }
}

// ============================================
// 便捷函数
// ============================================

/**
 * 计算 NEMT 状态
 */
export function calculateNEMTState(
  prices: number[],
  config?: Partial<NEMTConfig>
): NEMTState {
  const calculator = new NEMTStateCalculator(config);
  return calculator.calculate(prices);
}

/**
 * 获取交易信号
 */
export function getNEMTSignal(
  prices: number[],
  config?: Partial<NEMTConfig>
): { signal: 'BUY' | 'SELL' | 'HOLD'; confidence: number; state: NEMTState } {
  const state = calculateNEMTState(prices, config);
  const calculator = new NEMTStateCalculator(config);
  const { signal, confidence } = calculator.getPhaseSignal(state);
  return { signal, confidence, state };
}
