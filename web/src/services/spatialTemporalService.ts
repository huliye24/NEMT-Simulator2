/**
 * NEMT 第九章：时间-空间决策
 * 多周期信号叠加与市场间套利
 * TypeScript 版本
 */

// =====================
// 周期层级定义
// =====================

export enum CycleLevel {
  MACRO = "macro",           // 宏观层：月线级别
  STRATEGIC = "strategic",   // 战略层：周线级别
  TACTICAL = "tactical",     // 战术层：日线级别
  EXECUTION = "execution",   // 执行层：4小时级别
  MICRO = "micro",           // 微观层：15分钟级别
}

export interface CycleSignal {
  level: CycleLevel;
  direction: 'bullish' | 'bearish' | 'neutral';
  confidence: number;  // 0-1
  weight: number;  // 决策权重
  reason: string;
  timestamp: Date;
}

export interface CycleResonanceResult {
  resonanceScore: number;  // 0-10
  dominantDirection: 'bullish' | 'bearish' | 'neutral';
  conflictCount: number;
  conflictDetails: string[];
  recommendation: string;
}

// =====================
// 多周期决策框架
// =====================

export const CYCLE_WEIGHTS: Record<CycleLevel, number> = {
  [CycleLevel.MACRO]: 0.30,
  [CycleLevel.STRATEGIC]: 0.25,
  [CycleLevel.TACTICAL]: 0.25,
  [CycleLevel.EXECUTION]: 0.15,
  [CycleLevel.MICRO]: 0.05,
};

export const CYCLE_OBSERVATION: Record<CycleLevel, string> = {
  [CycleLevel.MACRO]: "每月第一周",
  [CycleLevel.STRATEGIC]: "每周",
  [CycleLevel.TACTICAL]: "每日收盘",
  [CycleLevel.EXECUTION]: "每4小时",
  [CycleLevel.MICRO]: "实时",
};

export class MultiCycleFramework {
  private signals: Map<CycleLevel, CycleSignal> = new Map();

  addSignal(signal: CycleSignal): void {
    this.signals.set(signal.level, signal);
  }

  calculateResonance(): CycleResonanceResult {
    if (this.signals.size === 0) {
      return {
        resonanceScore: 0,
        dominantDirection: 'neutral',
        conflictCount: 0,
        conflictDetails: ['无信号'],
        recommendation: '等待信号'
      };
    }

    const directionScores = {
      bullish: 0,
      bearish: 0,
      neutral: 0
    };

    const conflicts: string[] = [];
    const levels = Object.values(CycleLevel);
    let previousDirection: string | null = null;

    for (const level of levels) {
      const sig = this.signals.get(level);
      if (sig) {
        const weight = CYCLE_WEIGHTS[level];

        if (sig.direction === 'bullish') {
          directionScores.bullish += weight * sig.confidence;
        } else if (sig.direction === 'bearish') {
          directionScores.bearish += weight * sig.confidence;
        } else {
          directionScores.neutral += weight * sig.confidence;
        }

        if (previousDirection && previousDirection !== sig.direction) {
          conflicts.push(`${level}与上一级信号冲突: ${previousDirection} vs ${sig.direction}`);
        }

        previousDirection = sig.direction;
      }
    }

    const total = directionScores.bullish + directionScores.bearish + directionScores.neutral;
    const dominant = Object.entries(directionScores).reduce((a, b) =>
      a[1] > b[1] ? a : b
    )[0] as 'bullish' | 'bearish' | 'neutral';
    const dominantScore = directionScores[dominant] / total;

    const resonanceScore = dominantScore * 10;

    let recommendation: string;
    if (resonanceScore >= 8) {
      recommendation = `强烈${dominant}信号，执行${dominant === 'bullish' ? '做多' : dominant === 'bearish' ? '做空' : '观望'}策略`;
    } else if (resonanceScore >= 6) {
      recommendation = `${dominant}信号，可适度建仓`;
    } else if (resonanceScore >= 4) {
      recommendation = '信号分歧，保持观望，等待共振明确';
    } else {
      recommendation = '信号混乱，放弃本次机会';
    }

    return {
      resonanceScore,
      dominantDirection: dominant,
      conflictCount: conflicts.length,
      conflictDetails: conflicts,
      recommendation
    };
  }

  getDecisionSummary(): {
    signals: Record<string, { direction: string; confidence: string; reason: string }>;
    resonanceScore: number;
    dominantDirection: string;
    conflictCount: number;
    recommendation: string;
  } {
    const resonance = this.calculateResonance();

    const signalsObj: Record<string, { direction: string; confidence: string; reason: string }> = {};
    this.signals.forEach((sig, level) => {
      signalsObj[level] = {
        direction: sig.direction,
        confidence: `${(sig.confidence * 100).toFixed(0)}%`,
        reason: sig.reason
      };
    });

    return {
      signals: signalsObj,
      resonanceScore: resonance.resonanceScore,
      dominantDirection: resonance.dominantDirection,
      conflictCount: resonance.conflictCount,
      recommendation: resonance.recommendation
    };
  }
}

// =====================
// 跨交易所价差指标
// =====================

export interface PremiumIndex {
  name: string;
  currentValue: number;
  threshold: number;
  signal: 'bullish' | 'bearish' | 'neutral';
  durationHours: number;
  interpretation: string;
}

export class CrossExchangeFramework {
  /**
   * Coinbase溢价指数
   */
  checkCoinbasePremium(
    coinbasePrice: number,
    binancePrice: number,
    durationHours: number = 4
  ): PremiumIndex {
    const premiumPct = ((coinbasePrice - binancePrice) / binancePrice) * 100;

    let signal: 'bullish' | 'bearish' | 'neutral' = 'neutral';
    let interpretation: string;

    if (premiumPct > 0.3 && durationHours >= 4) {
      signal = 'bullish';
      interpretation = '机构买盘强劲，趋势看涨';
    } else if (premiumPct < -0.3 && durationHours >= 4) {
      signal = 'bearish';
      interpretation = '机构卖压或避险，趋势看跌';
    } else {
      signal = 'neutral';
      interpretation = '正常状态，无额外信息';
    }

    return {
      name: 'Coinbase溢价指数',
      currentValue: premiumPct,
      threshold: 0.3,
      signal,
      durationHours,
      interpretation
    };
  }

  /**
   * 韩国泡菜溢价
   */
  checkKimchiPremium(koreanPrice: number, globalPrice: number): PremiumIndex {
    const premiumPct = ((koreanPrice - globalPrice) / globalPrice) * 100;

    let signal: 'bullish' | 'bearish' | 'neutral' = 'neutral';
    let interpretation: string;

    if (premiumPct > 10) {
      signal = 'bearish';
      interpretation = '强烈顶部预警，应考虑减仓';
    } else if (premiumPct > 5) {
      signal = 'bearish';
      interpretation = '散户FOMO，短期顶部信号';
    } else if (premiumPct < 0) {
      signal = 'bullish';
      interpretation = '韩国散户恐慌，往往是阶段性底部';
    } else {
      interpretation = '正常状态';
    }

    return {
      name: '泡菜溢价',
      currentValue: premiumPct,
      threshold: 5.0,
      signal,
      durationHours: 0,
      interpretation
    };
  }

  /**
   * 稳定币脱锚指数
   */
  checkStablecoinDepeg(
    stablecoinPrices: Record<string, number>
  ): PremiumIndex {
    let maxDiscount = 0;
    let maxPremium = 0;

    Object.values(stablecoinPrices).forEach(price => {
      if (price < 1) {
        maxDiscount = Math.max(maxDiscount, (1 - price) * 100);
      } else {
        maxPremium = Math.max(maxPremium, (price - 1) * 100);
      }
    });

    let signal: 'bullish' | 'bearish' | 'neutral' = 'neutral';
    let interpretation: string;

    if (maxDiscount > 0.5) {
      signal = 'bearish';
      interpretation = '市场在抛售稳定币换取法币，是恐慌信号';
    } else if (maxPremium > 0.5) {
      signal = 'bullish';
      interpretation = '资金在涌入加密市场，看涨';
    } else {
      interpretation = '稳定币锚定正常';
    }

    return {
      name: '稳定币脱锚指数',
      currentValue: maxDiscount > 0 ? -maxDiscount : maxPremium,
      threshold: 0.5,
      signal,
      durationHours: 0,
      interpretation
    };
  }

  /**
   * 获取所有套利信号
   */
  getArbitrageSignals(
    coinbasePrice: number,
    binancePrice: number,
    koreanPrice: number,
    globalPrice: number,
    stablecoinPrices: Record<string, number>
  ): {
    coinbasePremium: { value: string; signal: string; interpretation: string };
    kimchiPremium: { value: string; signal: string; interpretation: string };
    stablecoinDepeg: { value: string; signal: string; interpretation: string };
    compositeSignal: 'bullish' | 'bearish' | 'neutral';
    recommendations: string[];
  } {
    const coinbase = this.checkCoinbasePremium(coinbasePrice, binancePrice);
    const kimchi = this.checkKimchiPremium(koreanPrice, globalPrice);
    const stablecoin = this.checkStablecoinDepeg(stablecoinPrices);

    const signals = [coinbase.signal, kimchi.signal, stablecoin.signal];
    const bullishCount = signals.filter(s => s === 'bullish').length;
    const bearishCount = signals.filter(s => s === 'bearish').length;

    let composite: 'bullish' | 'bearish' | 'neutral' = 'neutral';
    if (bullishCount >= 2) composite = 'bullish';
    else if (bearishCount >= 2) composite = 'bearish';

    const recommendations: string[] = [];

    if (coinbase.signal === 'bearish') {
      recommendations.push('趋势向上但Coinbase持续折价，上涨根基不稳，降低仓位、收紧止损');
    }

    if (kimchi.currentValue > 10) {
      recommendations.push('泡菜溢价>10% + NUPL>0.75，分批卖出锁定利润');
    } else if (kimchi.currentValue < 0) {
      recommendations.push('泡菜溢价转负，可能是阶段性底部关注');
    }

    if (stablecoin.signal === 'bearish') {
      recommendations.push('稳定币折价>0.5%，是恐慌信号，短期看跌');
    } else if (stablecoin.signal === 'bullish') {
      recommendations.push('稳定币溢价>0.5%，资金涌入，看涨');
    }

    return {
      coinbasePremium: {
        value: `${coinbase.currentValue.toFixed(2)}%`,
        signal: coinbase.signal,
        interpretation: coinbase.interpretation
      },
      kimchiPremium: {
        value: `${kimchi.currentValue.toFixed(2)}%`,
        signal: kimchi.signal,
        interpretation: kimchi.interpretation
      },
      stablecoinDepeg: {
        value: `${stablecoin.currentValue.toFixed(2)}%`,
        signal: stablecoin.signal,
        interpretation: stablecoin.interpretation
      },
      compositeSignal: composite,
      recommendations: recommendations.length > 0 ? recommendations : ['无特殊套利建议']
    };
  }
}

// =====================
// 期现结构与资金费率
// =====================

export interface BasisSignals {
  basis: { value: string; type: string; signal: string; interpretation: string };
  basisChange: { value: string; signal: string; interpretation: string };
}

export interface FundingRateData {
  rate: string;
  annualized: string;
  interpretation: string;
}

export interface EntryOptimization {
  currentRate: string;
  positionSizeReduction: string;
  warning: string | null;
  bestEntryTimes: Record<string, string>;
  avoidTimes: string[];
}

export class FuturesSpotFramework {
  /**
   * 基差信号
   */
  checkBasisSignal(
    futuresPrice: number,
    spotPrice: number,
    previousBasisPct?: number
  ): BasisSignals {
    const basisPct = ((futuresPrice - spotPrice) / spotPrice) * 100;
    const basisType = basisPct > 0 ? 'contango' : 'backwardation';

    const basisChange = previousBasisPct !== undefined
      ? basisPct - previousBasisPct
      : 0;

    let signal: string;
    let interpretation: string;

    if (basisPct > 5) {
      signal = 'very_bullish';
      interpretation = '正基差扩大，市场极度乐观，警惕顶部';
    } else if (basisPct > 2) {
      signal = 'bullish';
      interpretation = '正常牛市基差结构';
    } else if (basisPct < -2) {
      signal = 'bearish';
      interpretation = '负基差，市场恐慌或牛市末期';
    } else {
      signal = 'neutral';
      interpretation = '基差收窄，观望';
    }

    let changeSignal: string;
    let changeInterpretation: string;

    if (basisChange < -3) {
      changeSignal = 'bearish';
      changeInterpretation = '基差急剧收窄，可能转势';
    } else if (basisChange > 3) {
      changeSignal = 'bullish';
      changeInterpretation = '基差快速扩大，看涨情绪升温';
    } else {
      changeSignal = 'neutral';
      changeInterpretation = '基差变化平稳';
    }

    return {
      basis: {
        value: `${basisPct.toFixed(2)}%`,
        type: basisType,
        signal,
        interpretation
      },
      basisChange: {
        value: `${basisChange >= 0 ? '+' : ''}${basisChange.toFixed(2)}%`,
        signal: changeSignal,
        interpretation: changeInterpretation
      }
    };
  }

  /**
   * 资金费率分析
   */
  checkFundingRate(fundingRate: number, periodHours: number = 8): FundingRateData {
    const ratePct = fundingRate * 100;
    const rateAnnualized = ratePct * (365 * 24 / periodHours);

    let interpretation: string;

    if (ratePct > 0.05) {
      interpretation = '多头拥挤，极端贪婪，警惕顶部';
    } else if (ratePct > 0.01) {
      interpretation = '多头略占优势，正常';
    } else if (ratePct < -0.05) {
      interpretation = '空头拥挤，极端恐慌，可能是底部';
    } else if (ratePct < -0.01) {
      interpretation = '空头略占优势';
    } else {
      interpretation = '多空平衡';
    }

    return {
      rate: `${ratePct.toFixed(3)}%`,
      annualized: `${rateAnnualized.toFixed(1)}%`,
      interpretation
    };
  }

  /**
   * 入场时机优化
   */
  getEntryOptimization(fundingRate: number): EntryOptimization {
    const ratePct = Math.abs(fundingRate) * 100;

    let positionSizeReduction: number;
    let warning: string | null = null;

    if (ratePct > 0.05) {
      positionSizeReduction = 0.5;
      warning = '资金费率极端，减少仓位50%';
    } else if (ratePct > 0.02) {
      positionSizeReduction = 0.8;
      warning = '资金费率偏高，减少仓位20%';
    } else {
      positionSizeReduction = 1.0;
    }

    return {
      currentRate: `${ratePct.toFixed(3)}%`,
      positionSizeReduction: `${(positionSizeReduction * 100).toFixed(0)}%`,
      warning,
      bestEntryTimes: {
        morning: 'UTC 00:00 结算后4小时内',
        afternoon: 'UTC 08:00 结算后4小时内',
        evening: 'UTC 16:00 结算后4小时内',
      },
      avoidTimes: ['结算前1小时', '极端波动时段']
    };
  }
}

// =====================
// 综合决策引擎
// =====================

export interface SpatialTemporalResult {
  cycleAnalysis: {
    resonanceScore: number;
    dominantDirection: string;
    conflicts: number;
    recommendation: string;
  };
  arbitrageSignals: {
    coinbasePremium: { value: string; signal: string; interpretation: string };
    kimchiPremium: { value: string; signal: string; interpretation: string };
    stablecoinDepeg: { value: string; signal: string; interpretation: string };
    compositeSignal: 'bullish' | 'bearish' | 'neutral';
    recommendations: string[];
  };
  basisSignals: BasisSignals;
  fundingRate: FundingRateData;
  finalSignal: 'bullish' | 'bearish' | 'neutral';
  positionAdjustments: string[];
  entryOptimization: EntryOptimization;
  actionPlan: {
    action: string;
    recommendedPosition: string;
    adjustments: string[];
    riskLevel: 'low' | 'medium' | 'high';
  };
}

export class NEMTSpatialTemporalEngine {
  private cycleFramework = new MultiCycleFramework();
  private crossExchange = new CrossExchangeFramework();
  private futuresSpot = new FuturesSpotFramework();

  /**
   * 运行完整分析
   */
  runFullAnalysis(params: {
    macroDirection?: 'bullish' | 'bearish' | 'neutral';
    strategicDirection?: 'bullish' | 'bearish' | 'neutral';
    tacticalDirection?: 'bullish' | 'bearish' | 'neutral';
    executionDirection?: 'bullish' | 'bearish' | 'neutral';
    coinbasePremium?: number;
    kimchiPremium?: number;
    stablecoinDiscount?: number;
    basisPct?: number;
    fundingRate?: number;
    nupl?: number;
    phase?: string;
  }): SpatialTemporalResult {
    const {
      macroDirection = 'neutral',
      strategicDirection = 'neutral',
      tacticalDirection = 'neutral',
      executionDirection = 'neutral',
      coinbasePremium = 0,
      kimchiPremium = 0,
      stablecoinDiscount = 0,
      basisPct = 0,
      fundingRate = 0,
      nupl = 0.5,
      phase = 'A'
    } = params;

    // 1. 多周期共振
    if (macroDirection !== 'neutral') {
      this.cycleFramework.addSignal({
        level: CycleLevel.MACRO,
        direction: macroDirection,
        confidence: 0.8,
        weight: 0.30,
        reason: '宏观流动性评分',
        timestamp: new Date()
      });
    }

    if (strategicDirection !== 'neutral') {
      this.cycleFramework.addSignal({
        level: CycleLevel.STRATEGIC,
        direction: strategicDirection,
        confidence: 0.7,
        weight: 0.25,
        reason: '战略周期判断',
        timestamp: new Date()
      });
    }

    if (tacticalDirection !== 'neutral') {
      this.cycleFramework.addSignal({
        level: CycleLevel.TACTICAL,
        direction: tacticalDirection,
        confidence: 0.6,
        weight: 0.25,
        reason: '战术相位判断',
        timestamp: new Date()
      });
    }

    if (executionDirection !== 'neutral') {
      this.cycleFramework.addSignal({
        level: CycleLevel.EXECUTION,
        direction: executionDirection,
        confidence: 0.5,
        weight: 0.15,
        reason: '执行层信号',
        timestamp: new Date()
      });
    }

    const resonance = this.cycleFramework.calculateResonance();

    // 2. 跨交易所信号
    const arbitrageSignals = this.crossExchange.getArbitrageSignals(
      1 + coinbasePremium / 100,
      1,
      1 + kimchiPremium / 100,
      1,
      { binance: 1 - stablecoinDiscount / 100 }
    );

    // 3. 期现结构
    const basisSignals = this.futuresSpot.checkBasisSignal(
      1 + basisPct / 100,
      1
    );
    const fundingData = this.futuresSpot.checkFundingRate(fundingRate);
    const entryOptimization = this.futuresSpot.getEntryOptimization(fundingRate);

    // 4. 综合决策
    const signals = [
      resonance.dominantDirection,
      arbitrageSignals.compositeSignal,
      basisSignals.basis.signal.replace('very_', '')
    ];

    const bullishCount = signals.filter(s => s === 'bullish').length;
    const bearishCount = signals.filter(s => s === 'bearish').length;

    let finalSignal: 'bullish' | 'bearish' | 'neutral' = 'neutral';
    if (bullishCount >= 2) finalSignal = 'bullish';
    else if (bearishCount >= 2) finalSignal = 'bearish';

    // 5. 仓位调整
    const positionAdjustments: string[] = [];

    if (arbitrageSignals.coinbasePremium.signal === 'bearish') {
      positionAdjustments.push('Coinbase折价：降低仓位20%');
    }

    if (kimchiPremium > 10 && nupl > 0.75) {
      positionAdjustments.push('泡菜溢价+NUPL过高：分批卖出');
    }

    if (stablecoinDiscount > 0.5) {
      positionAdjustments.push('稳定币脱锚：观望或减仓');
    }

    if (Math.abs(fundingRate) * 100 > 0.05) {
      positionAdjustments.push(`极端资金费率：${entryOptimization.warning}`);
    }

    return {
      cycleAnalysis: {
        resonanceScore: resonance.resonanceScore,
        dominantDirection: resonance.dominantDirection,
        conflicts: resonance.conflictCount,
        recommendation: resonance.recommendation
      },
      arbitrageSignals,
      basisSignals,
      fundingRate: fundingData,
      finalSignal,
      positionAdjustments,
      entryOptimization,
      actionPlan: this.generateActionPlan(finalSignal, positionAdjustments, phase)
    };
  }

  private generateActionPlan(
    signal: 'bullish' | 'bearish' | 'neutral',
    adjustments: string[],
    phase: string
  ): {
    action: string;
    recommendedPosition: string;
    adjustments: string[];
    riskLevel: 'low' | 'medium' | 'high';
  } {
    let action: string;
    let position: string;

    if (signal === 'bullish' && ['B', 'C', 'D'].includes(phase)) {
      if (phase === 'B') {
        action = '识别边界，预设突破条件单';
        position = '50%';
      } else if (phase === 'C') {
        action = '提高敏感度，敢于追入';
        position = '70%';
      } else {
        action = '持仓为主，回调加仓';
        position = '100%';
      }
    } else if (signal === 'bearish') {
      action = '观望或轻仓，避免逆势';
      position = '20%';
    } else {
      action = '等待信号明确';
      position = '持有底仓';
    }

    let riskLevel: 'low' | 'medium' | 'high' = 'low';
    if (adjustments.length > 2) riskLevel = 'high';
    else if (adjustments.length > 0) riskLevel = 'medium';

    return {
      action,
      recommendedPosition: position,
      adjustments,
      riskLevel
    };
  }
}

// =====================
// 辅助函数
// =====================

/**
 * 获取周期层级名称
 */
export function getCycleLevelName(level: CycleLevel): string {
  const names: Record<CycleLevel, string> = {
    [CycleLevel.MACRO]: '宏观层',
    [CycleLevel.STRATEGIC]: '战略层',
    [CycleLevel.TACTICAL]: '战术层',
    [CycleLevel.EXECUTION]: '执行层',
    [CycleLevel.MICRO]: '微观层'
  };
  return names[level];
}

/**
 * 格式化分析结果
 */
export function formatSpatialTemporalResult(result: SpatialTemporalResult): string[] {
  const lines: string[] = [];

  lines.push(`📊 多周期共振: ${result.cycleAnalysis.resonanceScore.toFixed(1)}/10`);
  lines.push(`   主导方向: ${result.cycleAnalysis.dominantDirection}`);
  lines.push(`   冲突数量: ${result.cycleAnalysis.conflicts}`);
  lines.push(`   建议: ${result.cycleAnalysis.recommendation}`);

  lines.push('');
  lines.push(`🌐 Coinbase溢价: ${result.arbitrageSignals.coinbasePremium.value}`);
  lines.push(`   泡菜溢价: ${result.arbitrageSignals.kimchiPremium.value}`);
  lines.push(`   稳定币: ${result.arbitrageSignals.stablecoinDepeg.value}`);
  lines.push(`   综合信号: ${result.arbitrageSignals.compositeSignal}`);

  lines.push('');
  lines.push(`📈 基差: ${result.basisSignals.basis.value} (${result.basisSignals.basis.type})`);
  lines.push(`   资金费率: ${result.fundingRate.rate}`);

  lines.push('');
  lines.push(`🎯 最终信号: ${result.finalSignal.toUpperCase()}`);
  lines.push(`   行动计划: ${result.actionPlan.action}`);
  lines.push(`   建议仓位: ${result.actionPlan.recommendedPosition}`);

  if (result.positionAdjustments.length > 0) {
    lines.push('');
    lines.push('⚠️ 仓位调整:');
    result.positionAdjustments.forEach(adj => {
      lines.push(`   • ${adj}`);
    });
  }

  return lines;
}
