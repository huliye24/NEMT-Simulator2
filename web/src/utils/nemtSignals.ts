/**
 * Copyright 2026 NEMT Lab
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

/**
 * NEMT信号指标模块
 * 实现DCI、SNR、涡旋检测、随机共振检测
 */

import {
  MarketPhase,
  DCISignal,
  VortexConditions,
  ResonanceConditions,
  NEMTSignals,
  DCI_THRESHOLDS,
  VORTEX_THRESHOLDS,
  RESONANCE_THRESHOLDS
} from '../types/nemt';

export class NEMTSignalIndicators {
  private dciHistory: number[] = [];
  private priceHistory: number[] = [];
  
  /**
   * 计算方向一致性指数 (DCI)
   */
  computeDCI(prices: number[], nPeriods: number = 24): DCISignal {
    const n = Math.min(prices.length - 1, nPeriods);
    
    if (n < 2) {
      return {
        value: 0.5,
        noiseState: 'medium',
        direction: 'neutral',
        trend: 'stable'
      };
    }
    
    // 计算涨跌
    let upCount = 0;
    let downCount = 0;
    
    for (let i = prices.length - n; i < prices.length - 1; i++) {
      if (prices[i + 1] > prices[i]) upCount++;
      else if (prices[i + 1] < prices[i]) downCount++;
    }
    
    // DCI计算
    const maxCount = Math.max(upCount, downCount);
    const dciValue = maxCount / n;
    
    // 噪声状态判断
    let noiseState: DCISignal['noiseState'] = 'medium';
    if (dciValue > DCI_THRESHOLDS.high) noiseState = 'low';
    else if (dciValue < DCI_THRESHOLDS.low) noiseState = 'high';
    
    // 方向判断
    let direction: DCISignal['direction'] = 'neutral';
    if (upCount > downCount) direction = 'bullish';
    else if (downCount > upCount) direction = 'bearish';
    
    // 趋势判断
    this.dciHistory.push(dciValue);
    this.priceHistory.push(prices[prices.length - 1]);
    
    let trend: DCISignal['trend'] = 'stable';
    if (this.dciHistory.length >= 3) {
      const recent = this.dciHistory.slice(-3).reduce((a, b) => a + b, 0) / 3;
      const prev = this.dciHistory.length >= 5 
        ? this.dciHistory.slice(-5, -2).reduce((a, b) => a + b, 0) / 3
        : recent;
      
      if (recent > prev * 1.05) trend = 'strengthening';
      else if (recent < prev * 0.95) trend = 'weakening';
    }
    
    return {
      value: dciValue,
      noiseState,
      direction,
      trend
    };
  }
  
  /**
   * 计算DCI波动率
   */
  computeDCIVolatility(window: number = 20): number {
    if (this.dciHistory.length < window) return 0;
    
    const recent = this.dciHistory.slice(-window);
    const mean = recent.reduce((a, b) => a + b, 0) / window;
    const variance = recent.reduce((sum, val) => sum + (val - mean) ** 2, 0) / window;
    
    return Math.sqrt(variance);
  }
  
  /**
   * 检测涡旋结构
   */
  detectVortex(
    prices: number[],
    volumes: number[],
    oiValues: number[],
    fundingRates: number[],
    bbwHistory: number[]
  ): VortexConditions {
    // 条件1: BBW收窄
    let bbwNarrow = false;
    if (bbwHistory.length >= 30) {
      const sortedBBW = [...bbwHistory].sort((a, b) => a - b);
      const bbwPercentile = sortedBBW[Math.floor(bbwHistory.length * VORTEX_THRESHOLDS.bbbPercentile / 100)];
      bbwNarrow = bbwHistory[bbwHistory.length - 1] < bbwPercentile;
    }
    
    // 条件2: 成交量均匀分布
    let volumeUniform = false;
    if (prices.length >= 20) {
      let upVolume = 0;
      let downVolume = 0;
      
      for (let i = 1; i < prices.length; i++) {
        if (prices[i] >= prices[i - 1]) upVolume += volumes[i];
        else downVolume += volumes[i];
      }
      
      const totalVolume = upVolume + downVolume;
      if (totalVolume > 0) {
        const upRatio = upVolume / totalVolume;
        volumeUniform = upRatio >= 0.40 && upRatio <= 0.60;
      }
    }
    
    // 条件3: OI高位走平
    let oiHighFlat = false;
    if (oiValues.length >= 7) {
      const recentOI = oiValues.slice(-7);
      const oiChange = (recentOI[recentOI.length - 1] - recentOI[0]) / recentOI[0];
      const avgOI = recentOI.reduce((a, b) => a + b, 0) / 7;
      
      const oiLevelPercentile = oiValues.length >= 30
        ? [...oiValues.slice(-30)].sort((a, b) => a - b)[Math.floor(30 * VORTEX_THRESHOLDS.oiLevelPercentile / 100)]
        : avgOI;
      
      oiHighFlat = oiValues[oiValues.length - 1] > oiLevelPercentile && Math.abs(oiChange) < VORTEX_THRESHOLDS.oiChangeThreshold;
    }
    
    // 条件4: 资金费率零轴摆动
    let fundingNeutral = false;
    if (fundingRates.length >= 7) {
      const avgFunding = fundingRates.slice(-7).reduce((a, b) => a + Math.abs(b), 0) / 7;
      fundingNeutral = avgFunding < VORTEX_THRESHOLDS.fundingRateThreshold;
    }
    
    // 判断涡旋
    const conditionsMet = [bbwNarrow, volumeUniform, oiHighFlat, fundingNeutral].filter(Boolean).length;
    const isVortex = conditionsMet >= 3;
    
    // 计算成熟度
    let maturityScore = 0;
    if (isVortex) {
      maturityScore = conditionsMet * 2.5;
      if (oiValues.length >= 30) {
        const oiRatio = oiValues[oiValues.length - 1] / (oiValues.slice(-30).reduce((a, b) => a + b, 0) / 30);
        maturityScore *= Math.min(oiRatio, 2.0);
      }
    }
    
    return {
      bbwNarrow,
      volumeUniform,
      oiHighFlat,
      fundingNeutral,
      isVortex,
      maturityScore
    };
  }
  
  /**
   * 检测随机共振
   */
  detectResonance(params: {
    mvrvZscore?: number;
    nupl?: number;
    lthRatio?: number;
    sthRatio?: number;
    daysToHalving?: number;
    liquidityScore?: number;
    dciVolatility?: number;
    hasMacroEvent?: boolean;
    hasOnchainEvent?: boolean;
  }): ResonanceConditions {
    const rs = RESONANCE_THRESHOLDS;
    const {
      mvrvZscore,
      nupl,
      lthRatio,
      sthRatio,
      daysToHalving,
      liquidityScore,
      dciVolatility,
      hasMacroEvent = false,
      hasOnchainEvent = false
    } = params;
    
    // 条件1: 长周期临界点
    let longTermScore = 0;
    let bullishScore = 0;
    let bearishScore = 0;
    
    if (mvrvZscore !== undefined) {
      if (mvrvZscore < rs.mvrvCriticalLow) {
        longTermScore += 2;
        bullishScore++;
      } else if (mvrvZscore > rs.mvrvCriticalHigh) {
        longTermScore += 2;
        bearishScore++;
      }
    }
    
    if (nupl !== undefined) {
      if (nupl < 0) { longTermScore++; bullishScore++; }
      else if (nupl > 0.75) { longTermScore++; bearishScore++; }
    }
    
    if (lthRatio !== undefined && lthRatio > 0.01) {
      longTermScore++;
      bullishScore++;
    }
    
    if (sthRatio !== undefined && sthRatio > 0.01) {
      longTermScore++;
      bearishScore++;
    }
    
    if (daysToHalving !== undefined && daysToHalving >= -180 && daysToHalving <= 180) {
      longTermScore++;
      bullishScore++;
    }
    
    if (liquidityScore !== undefined) {
      if (liquidityScore >= 7) { longTermScore++; bullishScore++; }
      else if (liquidityScore <= 3) { longTermScore++; bearishScore++; }
    }
    
    const longTermCritical = longTermScore >= 4;
    
    // 条件2: 短周期噪声适中
    let shortTermNoise = false;
    if (dciVolatility !== undefined) {
      shortTermNoise = dciVolatility >= rs.dciVolLow && dciVolatility <= rs.dciVolHigh;
    } else if (this.dciHistory.length >= 20) {
      const dciVol = this.computeDCIVolatility(20);
      shortTermNoise = dciVol >= rs.dciVolLow && dciVol <= rs.dciVolHigh;
    }
    
    // 条件3: 潜在触发因子
    const triggerFactor = hasMacroEvent || hasOnchainEvent;
    
    // 综合判断
    const isResonance = longTermCritical && shortTermNoise && triggerFactor;
    const bullish = bullishScore > bearishScore;
    
    const confidence = isResonance
      ? ([longTermCritical, shortTermNoise, triggerFactor].filter(Boolean).length / 3)
      : 0;
    
    return {
      longTermCritical,
      shortTermNoise,
      triggerFactor,
      isResonance,
      bullish,
      confidence
    };
  }
  
  /**
   * 确定市场相位
   */
  determinePhase(
    dci: DCISignal,
    vortex: VortexConditions,
    resonance: ResonanceConditions
  ): { phase: MarketPhase; confidence: number } {
    // 优先级1: 随机共振触发 -> 相位C
    if (resonance.isResonance) {
      return { phase: MarketPhase.PHASE_C_RESONANCE, confidence: resonance.confidence };
    }
    
    // 优先级2: 涡旋形成 -> 相位B
    if (vortex.isVortex) {
      return { phase: MarketPhase.PHASE_B_VORTEX, confidence: vortex.maturityScore / 15 };
    }
    
    // 优先级3: 高DCI -> 相位D
    if (dci.value > DCI_THRESHOLDS.medium) {
      return { phase: MarketPhase.PHASE_D_TREND, confidence: (dci.value - 0.5) * 2 };
    }
    
    // 优先级4: 低DCI -> 相位A
    if (dci.value < DCI_THRESHOLDS.low) {
      return { phase: MarketPhase.PHASE_A_NOISE, confidence: 1 - (DCI_THRESHOLDS.low - dci.value) / 0.1 };
    }
    
    // 过渡期
    return { phase: MarketPhase.PHASE_A_NOISE, confidence: 0.5 };
  }
  
  /**
   * 计算谱宽
   */
  computeSpectralWidth(spectrum: number[], freqs: number[]): { spectralWidth: number; meanFreq: number } {
    let totalPower = 0;
    let weightedSum = 0;
    
    for (let i = 0; i < spectrum.length; i++) {
      const power = spectrum[i] ** 2;
      totalPower += power;
      weightedSum += freqs[i] * power;
    }
    
    if (totalPower < 1e-10) return { spectralWidth: 0, meanFreq: 0 };
    
    const meanFreq = weightedSum / totalPower;
    let variance = 0;
    
    for (let i = 0; i < spectrum.length; i++) {
      variance += (freqs[i] - meanFreq) ** 2 * spectrum[i] ** 2;
    }
    variance /= totalPower;
    
    return { spectralWidth: Math.sqrt(variance), meanFreq };
  }
  
  /**
   * 获取完整信号
   */
  getFullSignals(
    prices: number[],
    volumes: number[],
    oiValues: number[],
    fundingRates: number[],
    bbwHistory: number[],
    spectrum?: number[],
    freqs?: number[],
    onchainParams?: Parameters<typeof this.detectResonance>[0]
  ): NEMTSignals {
    const dci = this.computeDCI(prices);
    const dciVolatility = this.computeDCIVolatility(20);
    const vortex = this.detectVortex(prices, volumes, oiValues, fundingRates, bbwHistory);
    
    const resonance = this.detectResonance({
      ...onchainParams,
      dciVolatility
    });
    
    const { phase, confidence } = this.determinePhase(dci, vortex, resonance);
    
    let spectralWidth: number | null = null;
    if (spectrum && freqs) {
      spectralWidth = this.computeSpectralWidth(spectrum, freqs).spectralWidth;
    }
    
    return {
      dci,
      vortex,
      resonance,
      phase,
      phaseConfidence: confidence,
      spectralWidth
    };
  }
}
