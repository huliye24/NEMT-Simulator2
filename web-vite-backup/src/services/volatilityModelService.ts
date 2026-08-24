/**
 * NEMT 第十一章：波动性建模
 * 噪声驱动孤子与涡旋-随机共振模型
 * TypeScript 版本
 */

// =====================
// 波动结构类型
// =====================

export enum VolatilityStructure {
  NOISE_DOMINATED = "noise_dominated",
  VORTEX_FORMING = "vortex_forming",
  VORTEX_MATURE = "vortex_mature",
  RESONANCE_TRIGGER = "resonance_trigger",
  SOLITON_TREND = "soliton_trend",
  TREND_EXHAUSTING = "trend_exhausting"
}

// =====================
// 孤子模型
// =====================

export interface SolitonIndicators {
  maxRetracementPct: number;
  retracementVolumeRatio: number;
  oiChangePct: number;
  oiRetracementPct: number;
  dciSustainedDays: number;
  dciMinValue: number;
  isSoliton: boolean;
  confidence: number;
}

export interface SolitonDecaySignal {
  isDecaying: boolean;
  decayStage: 'healthy' | 'warning' | 'critical';
  indicators: string[];
  recommendedAction: string;
}

export class SolitonModel {
  // 孤子结构阈值
  private MAX_RETRACEMENT_SOLITON = 0.08;
  private VOLUME_RATIO_SOLITON = 0.40;
  private OI_RETRACEMENT_SOLITON = 0.05;
  private DCI_MIN_SOLITON = 0.70;
  private DCI_SUSTAINED_DAYS = 7;

  // 衰减警告阈值
  private RETRACEMENT_WARNING = 0.12;
  private RETRACEMENT_CRITICAL = 0.15;
  private VOLUME_RATIO_WARNING = 0.60;
  private OI_RETRACEMENT_WARNING = 0.10;

  analyze(params: {
    priceHigh: number;
    priceLowRetracement: number;
    upVolumeAvg: number;
    downVolumeAvg: number;
    oiStart: number;
    oiCurrent: number;
    oiRetracementLow?: number;
    dciValues?: number[];
  }): SolitonIndicators {
    const {
      priceHigh,
      priceLowRetracement,
      upVolumeAvg,
      downVolumeAvg,
      oiStart,
      oiCurrent,
      oiRetracementLow,
      dciValues
    } = params;

    // 计算最大回调
    const maxRetracement = (priceHigh - priceLowRetracement) / priceHigh;

    // 成交量比
    const volumeRatio = upVolumeAvg > 0 ? downVolumeAvg / upVolumeAvg : 1.0;

    // OI变化
    const oiChange = oiStart > 0 ? (oiCurrent - oiStart) / oiStart : 0;
    let oiRetracement = 0;
    if (oiRetracementLow !== undefined && oiStart > 0) {
      oiRetracement = (oiStart - oiRetracementLow) / oiStart;
    }

    // DCI分析
    let dciMin = 0;
    let dciSustained = 0;
    if (dciValues) {
      dciMin = Math.min(...dciValues);
      dciSustained = dciValues.filter(d => d >= this.DCI_MIN_SOLITON).length;
    }

    // 判断是否为孤子
    const isSoliton = (
      maxRetracement <= this.MAX_RETRACEMENT_SOLITON &&
      volumeRatio <= this.VOLUME_RATIO_SOLITON &&
      oiRetracement <= this.OI_RETRACEMENT_SOLITON &&
      dciMin >= this.DCI_MIN_SOLITON &&
      dciSustained >= this.DCI_SUSTAINED_DAYS
    );

    // 计算置信度
    const confidence = this.calculateConfidence(
      maxRetracement, volumeRatio, oiRetracement, dciMin, dciSustained
    );

    return {
      maxRetracementPct: maxRetracement * 100,
      retracementVolumeRatio: volumeRatio,
      oiChangePct: oiChange * 100,
      oiRetracementPct: oiRetracement * 100,
      dciSustainedDays: dciSustained,
      dciMinValue: dciMin,
      isSoliton,
      confidence
    };
  }

  private calculateConfidence(
    retracement: number,
    volumeRatio: number,
    oiRetracement: number,
    dciMin: number,
    dciSustained: number
  ): number {
    let score = 1.0;

    if (retracement > this.MAX_RETRACEMENT_SOLITON) {
      score -= Math.min(0.3, (retracement - this.MAX_RETRACEMENT_SOLITON) * 5);
    }
    if (volumeRatio > this.VOLUME_RATIO_SOLITON) {
      score -= Math.min(0.2, (volumeRatio - this.VOLUME_RATIO_SOLITON) * 2);
    }
    if (oiRetracement > this.OI_RETRACEMENT_SOLITON) {
      score -= Math.min(0.2, (oiRetracement - this.OI_RETRACEMENT_SOLITON) * 5);
    }
    if (dciMin >= this.DCI_MIN_SOLITON) score += 0.1;
    if (dciSustained >= this.DCI_SUSTAINED_DAYS) score += 0.1;

    return Math.max(0, Math.min(1, score));
  }

  checkDecay(
    solitonIndicators: SolitonIndicators,
    currentRetracement: number,
    currentVolumeRatio: number,
    currentOiRetracement: number,
    dciCurrent: number,
    dciTrend: 'rising' | 'falling' | 'stable'
  ): SolitonDecaySignal {
    const indicators: string[] = [];
    let isDecaying = false;
    let decayStage: 'healthy' | 'warning' | 'critical' = 'healthy';

    // 检查回调深度
    if (currentRetracement > this.RETRACEMENT_CRITICAL) {
      indicators.push(`回调深度${(currentRetracement * 100).toFixed(1)}%超过15%，严重警告`);
      isDecaying = true;
      decayStage = 'critical';
    } else if (currentRetracement > this.RETRACEMENT_WARNING) {
      indicators.push(`回调深度${(currentRetracement * 100).toFixed(1)}%超过12%，开始警告`);
      isDecaying = true;
      decayStage = 'warning';
    }

    // 检查成交量
    if (currentVolumeRatio > this.VOLUME_RATIO_WARNING) {
      indicators.push(`回调成交量比${(currentVolumeRatio * 100).toFixed(1)}%超过60%，抛压增加`);
    }

    // 检查OI回落
    if (currentOiRetracement > this.OI_RETRACEMENT_WARNING) {
      indicators.push(`OI回落${(currentOiRetracement * 100).toFixed(1)}%超过10%，多头平仓`);
    }

    // 检查DCI
    if (dciCurrent < solitonIndicators.dciMinValue * 0.9) {
      indicators.push(`DCI从${solitonIndicators.dciMinValue.toFixed(2)}下降至${dciCurrent.toFixed(2)}，趋势动量减弱`);
      isDecaying = true;
      if (decayStage !== 'critical') decayStage = 'warning';
    }

    if (dciTrend === 'falling') {
      indicators.push('DCI呈下降趋势');
    }

    // 生成建议
    let recommendedAction: string;
    if (decayStage === 'critical') {
      recommendedAction = '立即减仓50%，止损上移至保本价';
    } else if (decayStage === 'warning') {
      recommendedAction = '减仓30%，收紧止损，等待企稳';
    } else {
      recommendedAction = '持仓不动，回调是加仓机会';
    }

    return { isDecaying, decayStage, indicators, recommendedAction };
  }
}

// =====================
// 涡旋-随机共振模型
// =====================

export interface ResonanceParameters {
  barrierProxy: number;
  noiseIntensity: number;
  cycleSignalStrength: number;
  breakthroughProbability: number;
}

export interface ResonancePhase {
  phase: VolatilityStructure;
  name: string;
  mathDescription: string;
  marketDescription: string;
  nemtAction: string;
}

export class VortexResonanceModel {
  private solitonModel = new SolitonModel();

  getPhases(): ResonancePhase[] {
    return [
      {
        phase: VolatilityStructure.VORTEX_FORMING,
        name: '势垒形成',
        mathDescription: 'V(x)的两个势阱深度适中，势垒较高',
        marketDescription: '价格在窄区间内运行，波动率锥收窄，多空对峙',
        nemtAction: '涡旋条件开始满足，成熟度<5，不入场'
      },
      {
        phase: VolatilityStructure.VORTEX_MATURE,
        name: '势垒降低',
        mathDescription: '随着时间推移和OI积累，势垒逐渐降低',
        marketDescription: '区间内波动更加频繁，假突破开始出现',
        nemtAction: '涡旋成熟度5-15，进入最佳交易准备状态'
      },
      {
        phase: VolatilityStructure.RESONANCE_TRIGGER,
        name: '随机共振触发',
        mathDescription: 'σ（噪声强度）与势垒高度匹配，A（宏观信号）被放大',
        marketDescription: '突破K线出现，量能放大，OI跟随',
        nemtAction: '突破确认条件满足，执行入场'
      },
      {
        phase: VolatilityStructure.SOLITON_TREND,
        name: '势垒消失',
        mathDescription: '系统逃逸出双势阱，进入单边运动',
        marketDescription: '孤子结构形成，趋势持续',
        nemtAction: '相位D，持仓为主，回调加仓'
      }
    ];
  }

  /**
   * 估计势垒高度代理变量
   * BBW(20,2) / (ATR(14) / 价格)
   */
  estimateBarrierProxy(bbw: number, atr: number, price: number): number {
    if (price <= 0 || atr <= 0) return 1.0;
    const normalizedAtr = atr / price;
    if (normalizedAtr <= 0) return 1.0;
    return bbw / normalizedAtr;
  }

  /**
   * 估计噪声强度
   * DCI的20日标准差在0.08-0.15之间时最佳
   */
  estimateNoiseIntensity(dciStd20: number): number {
    return Math.max(0.01, Math.min(0.3, dciStd20));
  }

  /**
   * 估计周期信号强度
   */
  estimateCycleSignal(macroScore: number, onchainScore: number): number {
    const macroNormalized = Math.min(10, Math.max(0, macroScore)) / 10;
    const onchainNormalized = Math.min(10, Math.max(0, onchainScore)) / 10;
    return (macroNormalized + onchainNormalized) / 2;
  }

  /**
   * 计算突破概率
   * P(突破) ≈ 1 / (1 + exp((势垒代理 - 0.3) / 0.1)) × 噪声匹配因子
   */
  calculateBreakthroughProbability(
    barrierProxy: number,
    noiseIntensity: number,
    cycleSignal: number
  ): number {
    // 势垒因子
    let barrierFactor = 1 / (1 + Math.exp((barrierProxy - 0.3) / 0.1));

    // 噪声匹配因子
    let noiseFactor: number;
    if (noiseIntensity >= 0.08 && noiseIntensity <= 0.15) {
      noiseFactor = 1.0;
    } else if (noiseIntensity < 0.08) {
      noiseFactor = noiseIntensity / 0.08;
    } else {
      noiseFactor = Math.max(0.3, 1 - (noiseIntensity - 0.15) / 0.15);
    }

    // 周期信号加成
    const signalFactor = 0.5 + 0.5 * cycleSignal;

    return Math.max(0, Math.min(1, barrierFactor * noiseFactor * signalFactor));
  }

  getResonanceParameters(params: {
    bbw: number;
    atr: number;
    price: number;
    dciStd20: number;
    macroScore: number;
    onchainScore: number;
  }): ResonanceParameters {
    const barrierProxy = this.estimateBarrierProxy(params.bbw, params.atr, params.price);
    const noiseIntensity = this.estimateNoiseIntensity(params.dciStd20);
    const cycleSignalStrength = this.estimateCycleSignal(params.macroScore, params.onchainScore);
    const breakthroughProbability = this.calculateBreakthroughProbability(
      barrierProxy, noiseIntensity, cycleSignalStrength
    );

    return {
      barrierProxy,
      noiseIntensity,
      cycleSignalStrength,
      breakthroughProbability
    };
  }

  determinePhase(
    vortexMaturity: number,
    barrierProxy: number,
    noiseIntensity: number,
    hasBreakout: boolean
  ): ResonancePhase {
    const phases = this.getPhases();
    const phaseMap = new Map(phases.map(p => [p.phase, p]));

    if (hasBreakout) {
      return phaseMap.get(VolatilityStructure.SOLITON_TREND)!;
    }

    if (vortexMaturity < 5) {
      return phaseMap.get(VolatilityStructure.VORTEX_FORMING)!;
    } else if (vortexMaturity < 15) {
      if (barrierProxy < 0.3 && noiseIntensity >= 0.08 && noiseIntensity <= 0.15) {
        return phaseMap.get(VolatilityStructure.RESONANCE_TRIGGER)!;
      }
      return phaseMap.get(VolatilityStructure.VORTEX_MATURE)!;
    } else {
      return phaseMap.get(VolatilityStructure.RESONANCE_TRIGGER)!;
    }
  }

  getTradingSignal(params: {
    barrierProxy: number;
    noiseIntensity: number;
    cycleSignal: number;
    vortexMaturity: number;
    currentPhase: VolatilityStructure;
  }): {
    breakthroughProbability: number;
    strength: 'strong' | 'medium' | 'weak';
    signal: string;
    action: string;
    phase: string;
    maturity: number;
    recommendations: string[];
  } {
    const { barrierProxy, noiseIntensity, cycleSignal, vortexMaturity, currentPhase } = params;
    const prob = this.calculateBreakthroughProbability(barrierProxy, noiseIntensity, cycleSignal);

    let strength: 'strong' | 'medium' | 'weak';
    let signal: string;
    let action: string;

    if (prob >= 0.7) {
      strength = 'strong';
      signal = 'bullish';
      action = '突破概率高，准备入场';
    } else if (prob >= 0.4) {
      strength = 'medium';
      signal = 'cautious_bullish';
      action = '概率中等，轻仓试探';
    } else {
      strength = 'weak';
      signal = 'neutral';
      action = '等待信号明确';
    }

    const recommendations: string[] = [];
    if (currentPhase === VolatilityStructure.VORTEX_FORMING) {
      recommendations.push('等待涡旋成熟');
      recommendations.push('不预判突破方向');
    } else if (currentPhase === VolatilityStructure.VORTEX_MATURE) {
      recommendations.push('识别边界，预设条件单');
      recommendations.push('双向挂单，任一方向触发入场');
    } else if (currentPhase === VolatilityStructure.RESONANCE_TRIGGER) {
      recommendations.push('突破确认后立即执行');
      recommendations.push('初始仓位可适当放大');
    } else if (currentPhase === VolatilityStructure.SOLITON_TREND) {
      recommendations.push('持仓为主，回调加仓');
      recommendations.push('使用移动止损保护利润');
    }

    if (vortexMaturity > 12) {
      recommendations.push('注意：成熟度偏高，可能已过最佳入场点');
    }

    return {
      breakthroughProbability: prob,
      strength,
      signal,
      action,
      phase: currentPhase,
      maturity: vortexMaturity,
      recommendations
    };
  }
}

// =====================
// 信号强度评分
// =====================

export interface SignalStrengthScore {
  totalScore: number;
  breakthroughComponent: number;
  solitonComponent: number;
  resonanceFactor: number;
  strengthLabel: string;
  interpretation: string;
}

export interface PositionRecommendation {
  positionPct: number;
  stopLossPct: number;
  positionType: 'full' | 'medium' | 'light' | 'none';
  addOnDip: boolean;
}

export class SignalStrengthScorer {
  private solitonModel = new SolitonModel();
  private resonanceModel = new VortexResonanceModel();

  calculate(params: {
    barrierProxy: number;
    noiseIntensity: number;
    cycleSignal: number;
    currentPhase: VolatilityStructure;
    vortexMaturity: number;
    maxRetracement?: number;
    volumeRatio?: number;
    oiRetracement?: number;
    dciMin?: number;
    dciSustainedDays?: number;
    hasSolitonStructure?: boolean;
  }): SignalStrengthScore {
    const {
      barrierProxy,
      noiseIntensity,
      cycleSignal,
      currentPhase,
      maxRetracement = 0.05,
      volumeRatio = 0.3,
      oiRetracement = 0.03,
      dciMin = 0.5,
      dciSustainedDays = 7,
      hasSolitonStructure = false
    } = params;

    // 突破概率分量
    const pBreakthrough = this.resonanceModel.calculateBreakthroughProbability(
      barrierProxy, noiseIntensity, cycleSignal
    );

    // 孤子结构分量
    const solitonConfidence = this.solitonModel.analyze({
      priceHigh: 1,
      priceLowRetracement: 1 - maxRetracement,
      upVolumeAvg: 1,
      downVolumeAvg: volumeRatio,
      oiStart: 1,
      oiCurrent: 1,
      dciValues: Array(dciSustainedDays).fill(dciMin)
    }).confidence;
    const sSoliton = solitonConfidence;

    // 权重
    const w1 = 0.6;
    const w2 = 0.4;

    // 共振系数
    let resonanceFactor: number;
    if (currentPhase === VolatilityStructure.RESONANCE_TRIGGER) {
      resonanceFactor = 1.2;
    } else if (currentPhase === VolatilityStructure.VORTEX_MATURE) {
      resonanceFactor = 1.0;
    } else if (currentPhase === VolatilityStructure.SOLITON_TREND) {
      resonanceFactor = 0.8;
    } else {
      resonanceFactor = 0.5;
    }

    // 计算总分
    const baseScore = w1 * pBreakthrough + w2 * (hasSolitonStructure ? sSoliton : 0);
    const totalScore = baseScore * resonanceFactor * 100;

    // 强度标签
    let strengthLabel: string;
    let interpretation: string;

    if (totalScore >= 80) {
      strengthLabel = '极强信号';
      interpretation = '多个模型共振，建议重仓';
    } else if (totalScore >= 60) {
      strengthLabel = '强信号';
      interpretation = '突破概率高，可适当加仓';
    } else if (totalScore >= 40) {
      strengthLabel = '中等信号';
      interpretation = '概率中等，建议轻仓';
    } else if (totalScore >= 20) {
      strengthLabel = '弱信号';
      interpretation = '信号不明确，观望为主';
    } else {
      strengthLabel = '无信号';
      interpretation = '放弃本次机会';
    }

    return {
      totalScore,
      breakthroughComponent: pBreakthrough * 100,
      solitonComponent: sSoliton * 100,
      resonanceFactor,
      strengthLabel,
      interpretation
    };
  }

  getPositionRecommendation(score: SignalStrengthScore): PositionRecommendation {
    if (score.totalScore >= 80) {
      return { positionPct: 80, stopLossPct: 5, positionType: 'full', addOnDip: true };
    } else if (score.totalScore >= 60) {
      return { positionPct: 60, stopLossPct: 6, positionType: 'medium', addOnDip: true };
    } else if (score.totalScore >= 40) {
      return { positionPct: 30, stopLossPct: 8, positionType: 'light', addOnDip: false };
    } else {
      return { positionPct: 0, stopLossPct: 10, positionType: 'none', addOnDip: false };
    }
  }
}

// =====================
// 综合波动性分析引擎
// =====================

export interface VolatilityAnalysisResult {
  soliton: {
    isSoliton: boolean;
    confidence: string;
    maxRetracement: string;
    volumeRatio: string;
    dciSustained: string;
  };
  resonance: {
    barrierProxy: string;
    noiseIntensity: string;
    cycleSignal: string;
    breakthroughProbability: string;
  };
  phase: {
    name: string;
    description: string;
    action: string;
  };
  signalStrength: {
    score: string;
    label: string;
    interpretation: string;
    breakthroughComponent: string;
    solitonComponent: string;
  };
  position: PositionRecommendation;
}

export class NEMTVolatilityEngine {
  private solitonModel = new SolitonModel();
  private resonanceModel = new VortexResonanceModel();
  private sssScorer = new SignalStrengthScorer();

  analyze(params: {
    currentPrice: number;
    priceHigh: number;
    priceLowRetracement: number;
    atr: number;
    bbw: number;
    upVolumeAvg: number;
    downVolumeAvg: number;
    oiStart: number;
    oiCurrent: number;
    oiRetracementLow?: number;
    dciValues?: number[];
    dciCurrent?: number;
    vortexMaturity: number;
    macroScore: number;
    onchainScore: number;
    hasBreakout: boolean;
  }): VolatilityAnalysisResult {
    const {
      currentPrice,
      priceHigh,
      priceLowRetracement,
      atr,
      bbw,
      upVolumeAvg,
      downVolumeAvg,
      oiStart,
      oiCurrent,
      oiRetracementLow,
      dciValues,
      dciCurrent = 0.5,
      vortexMaturity,
      macroScore,
      onchainScore,
      hasBreakout
    } = params;

    // 1. 孤子分析
    const soliton = this.solitonModel.analyze({
      priceHigh,
      priceLowRetracement,
      upVolumeAvg,
      downVolumeAvg,
      oiStart,
      oiCurrent,
      oiRetracementLow,
      dciValues
    });

    // 2. 共振参数
    let dciStd20 = 0.1;
    if (dciValues && dciValues.length >= 20) {
      const recentDci = dciValues.slice(-20);
      const mean = recentDci.reduce((a, b) => a + b, 0) / recentDci.length;
      const variance = recentDci.reduce((a, b) => a + (b - mean) ** 2, 0) / recentDci.length;
      dciStd20 = Math.sqrt(variance);
      dciStd20 = Math.max(0.01, Math.min(0.3, dciStd20));
    }

    const resonanceParams = this.resonanceModel.getResonanceParameters({
      bbw,
      atr,
      price: currentPrice,
      dciStd20,
      macroScore,
      onchainScore
    });

    // 3. 确定相位
    const currentPhase = this.resonanceModel.determinePhase(
      vortexMaturity,
      resonanceParams.barrierProxy,
      resonanceParams.noiseIntensity,
      hasBreakout
    );

    // 4. 信号强度评分
    const dciMin = dciValues ? Math.min(...dciValues) : 0.5;
    const dciSustained = dciValues ? dciValues.filter(d => d >= 0.70).length : 0;
    const maxRetracement = (priceHigh - priceLowRetracement) / priceHigh;
    const volumeRatio = upVolumeAvg > 0 ? downVolumeAvg / upVolumeAvg : 1.0;
    const oiRetracement = oiRetracementLow !== undefined && oiStart > 0
      ? (oiStart - oiRetracementLow) / oiStart
      : 0;

    const sss = this.sssScorer.calculate({
      barrierProxy: resonanceParams.barrierProxy,
      noiseIntensity: resonanceParams.noiseIntensity,
      cycleSignal: resonanceParams.cycleSignalStrength,
      currentPhase: currentPhase.phase,
      vortexMaturity,
      maxRetracement,
      volumeRatio,
      oiRetracement,
      dciMin,
      dciSustainedDays: dciSustained,
      hasSolitonStructure: soliton.isSoliton
    });

    // 5. 仓位建议
    const position = this.sssScorer.getPositionRecommendation(sss);

    return {
      soliton: {
        isSoliton: soliton.isSoliton,
        confidence: `${(soliton.confidence * 100).toFixed(0)}%`,
        maxRetracement: `${soliton.maxRetracementPct.toFixed(1)}%`,
        volumeRatio: `${(soliton.retracementVolumeRatio * 100).toFixed(1)}%`,
        dciSustained: `${soliton.dciSustainedDays}天`
      },
      resonance: {
        barrierProxy: resonanceParams.barrierProxy.toFixed(3),
        noiseIntensity: resonanceParams.noiseIntensity.toFixed(3),
        cycleSignal: `${(resonanceParams.cycleSignalStrength * 100).toFixed(0)}%`,
        breakthroughProbability: `${(resonanceParams.breakthroughProbability * 100).toFixed(0)}%`
      },
      phase: {
        name: currentPhase.name,
        description: currentPhase.marketDescription,
        action: currentPhase.nemtAction
      },
      signalStrength: {
        score: `${sss.totalScore.toFixed(0)}/100`,
        label: sss.strengthLabel,
        interpretation: sss.interpretation,
        breakthroughComponent: `${sss.breakthroughComponent.toFixed(0)}`,
        solitonComponent: `${sss.solitonComponent.toFixed(0)}`
      },
      position
    };
  }
}

// =====================
// 辅助函数
// =====================

/**
 * 计算标准差
 */
export function calculateStd(values: number[]): number {
  if (values.length < 2) return 0;
  const mean = values.reduce((a, b) => a + b, 0) / values.length;
  const variance = values.reduce((a, b) => a + (b - mean) ** 2, 0) / values.length;
  return Math.sqrt(variance);
}

/**
 * 格式化波动性分析结果
 */
export function formatVolatilityResult(result: VolatilityAnalysisResult): string[] {
  const lines: string[] = [];

  lines.push(`[信号强度] ${result.signalStrength.score} - ${result.signalStrength.label}`);
  lines.push(`  ${result.signalStrength.interpretation}`);

  lines.push('');
  lines.push(`[当前相位] ${result.phase.name}`);
  lines.push(`  ${result.phase.description}`);
  lines.push(`  行动: ${result.phase.action}`);

  lines.push('');
  lines.push(`[孤子结构] ${result.soliton.isSoliton ? '是' : '否'}`);
  lines.push(`  置信度: ${result.soliton.confidence}`);
  lines.push(`  最大回调: ${result.soliton.maxRetracement}`);
  lines.push(`  成交量比: ${result.soliton.volumeRatio}`);

  lines.push('');
  lines.push(`[共振参数]`);
  lines.push(`  势垒代理: ${result.resonance.barrierProxy}`);
  lines.push(`  噪声强度: ${result.resonance.noiseIntensity}`);
  lines.push(`  周期信号: ${result.resonance.cycleSignal}`);
  lines.push(`  突破概率: ${result.resonance.breakthroughProbability}`);

  lines.push('');
  lines.push(`[仓位建议]`);
  lines.push(`  建议仓位: ${result.position.positionPct}%`);
  lines.push(`  止损设置: ${result.position.stopLossPct}%`);
  lines.push(`  回撤加仓: ${result.position.addOnDip ? '是' : '否'}`);

  return lines;
}
