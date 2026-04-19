/**
 * NEMT 第十章：市场非平衡视角下的经济因子分析
 * TypeScript 版本
 */

// =====================
// 能量层级定义
// =====================

export enum EnergyLevel {
  FOUNDATION = "foundation",    // 基础能量：央行资产负债表
  MARGINAL = "marginal",       // 边际能量：边际收紧/宽松
  IMPULSE = "impulse"           // 脉冲能量：危机事件
}

export interface EnergyReading {
  level: EnergyLevel;
  value: number;
  direction: 'expanding' | 'contracting' | 'neutral';
  score: number;  // -2 到 +2
  interpretation: string;
}

// =====================
// 全球流动性分析
// =====================

export class GlobalLiquidityAnalyzer {
  private HIGH_ENERGY_THRESHOLD = 0.10;
  private MEDIUM_ENERGY_THRESHOLD = 0.05;
  private LOW_ENERGY_THRESHOLD = 0.0;

  calculateLiquidityEnergy(
    currentBalanceSheet: number,
    balance12MonthsAgo: number
  ): EnergyReading {
    const energy = balance12MonthsAgo > 0
      ? (currentBalanceSheet / balance12MonthsAgo) - 1
      : 0;

    let levelDesc: string;
    let direction: 'expanding' | 'contracting' | 'neutral';
    let score: number;
    let interpretation: string;

    if (energy > this.HIGH_ENERGY_THRESHOLD) {
      levelDesc = "高能注入";
      direction = "expanding";
      score = 2.0;
      interpretation = "2020-2021年级别的史诗级宽松，驱动超级牛市";
    } else if (energy > this.MEDIUM_ENERGY_THRESHOLD) {
      levelDesc = "中能注入";
      direction = "expanding";
      score = 1.0;
      interpretation = "正常宽松周期，支撑趋势上涨";
    } else if (energy > this.LOW_ENERGY_THRESHOLD) {
      levelDesc = "低能/中性";
      direction = "neutral";
      score = 0.0;
      interpretation = "存量博弈，震荡为主";
    } else {
      levelDesc = "能量流出";
      direction = "contracting";
      score = -2.0;
      interpretation = "缩表周期，系统性逆风";
    }

    return {
      level: EnergyLevel.FOUNDATION,
      value: energy * 100,
      direction,
      score,
      interpretation
    };
  }

  getConductionPath(): string[] {
    return [
      "1. 央行扩表/缩表",
      "2. 商业银行准备金变化",
      "3. 资金成本变化",
      "4. 风险偏好变化",
      "5. 资金流向风险资产",
      "6. 财富效应",
      "7. 稳定币发行量变化",
      "8. 交易所弹药变化"
    ];
  }

  getLeadLagRelationships(): { key: string; lag: string; description: string }[] {
    return [
      { key: "balance_to_stablecoin", lag: "3-6个月", description: "央行资产负债表 -> 稳定币总市值" },
      { key: "stablecoin_to_btc", lag: "1-2个月", description: "稳定币市值 -> 比特币价格" }
    ];
  }
}

// =====================
// 实际利率分析
// =====================

export interface RealRateAnalysis {
  currentRate: number;
  levelSignal: 'bullish' | 'bearish' | 'neutral';
  levelInterpretation: string;
  momentumSignal: 'bullish' | 'bearish' | 'neutral';
  momentumInterpretation: string;
  yoyChange?: number;
  macroScoreContribution: number;
  action: string;
}

export class RealRateAnalyzer {
  analyzeRealRate(
    tipsYield: number,
    tipsYield1YAgo?: number
  ): RealRateAnalysis {
    const result: RealRateAnalysis = {
      currentRate: tipsYield,
      levelSignal: 'neutral',
      levelInterpretation: '',
      momentumSignal: 'neutral',
      momentumInterpretation: '',
      macroScoreContribution: 0,
      action: '等待更多信息'
    };

    // 绝对水平分析
    if (tipsYield < 0) {
      result.levelSignal = 'bullish';
      result.levelInterpretation = '实际利率为负，宏观评分额外+1';
      result.macroScoreContribution += 1;
    } else if (tipsYield > 2.0) {
      result.levelSignal = 'bearish';
      result.levelInterpretation = '实际利率高企，持有比特币机会成本大';
      result.macroScoreContribution -= 1;
    } else {
      result.levelInterpretation = '实际利率处于中性区间';
    }

    // 二阶导分析
    if (tipsYield1YAgo !== undefined) {
      const change = tipsYield - tipsYield1YAgo;
      result.yoyChange = change;

      if (change < -0.5) {
        result.momentumSignal = 'bullish';
        result.momentumInterpretation = '实际利率同比下降>0.5%，边际宽松';
        result.macroScoreContribution += 1;
      } else if (change > 0.5) {
        result.momentumSignal = 'bearish';
        result.momentumInterpretation = '实际利率同比上升>0.5%，边际收紧';
        result.macroScoreContribution -= 1;
      } else {
        result.momentumInterpretation = '实际利率变化平稳';
      }
    }

    // 综合行动
    if (result.momentumSignal === 'bullish') {
      result.action = '边际宽松，看涨信号，可适当提高风险敞口';
    } else if (result.momentumSignal === 'bearish') {
      result.action = '边际收紧，降低风险敞口，保护资本';
    } else if (result.levelSignal === 'bullish') {
      result.action = '实际利率为负，额外看涨信号';
    }

    return result;
  }
}

// =====================
// 美元指数分析
// =====================

export interface DXYAnalysis {
  dxyChange: number;
  signal: 'bullish' | 'bearish' | 'neutral';
  interpretation: string;
  macroScoreAdjustment: number;
  action: string;
}

export class DollarIndexAnalyzer {
  private contextIndicators = {
    vixRising: false,
    treasuryYieldRising: false,
    stockMarketRising: true
  };

  setContext(
    vixRising: boolean,
    treasuryYieldRising: boolean,
    stockMarketRising: boolean
  ): void {
    this.contextIndicators = { vixRising, treasuryYieldRising, stockMarketRising };
  }

  analyzeDXYChange(dxyChangePct: number): DXYAnalysis {
    const result: DXYAnalysis = {
      dxyChange: dxyChangePct,
      signal: 'neutral',
      interpretation: '',
      macroScoreAdjustment: 0,
      action: '关注其他指标'
    };

    if (dxyChangePct > 3.0) {
      if (this.contextIndicators.vixRising && this.contextIndicators.treasuryYieldRising) {
        result.signal = 'bearish';
        result.interpretation = 'DXY上涨由避险驱动，比特币看跌';
        result.macroScoreAdjustment = -1;
        result.action = '降低风险暴露，宏观评分-1';
      } else {
        result.interpretation = 'DXY上涨但非避险驱动，以其他指标为准';
      }
    } else if (dxyChangePct > 0) {
      if (this.contextIndicators.vixRising) {
        result.signal = 'bearish';
        result.interpretation = 'DXY上涨由避险驱动（VIX同步上涨）';
        result.action = '谨慎，降低风险敞口';
      } else if (this.contextIndicators.treasuryYieldRising && this.contextIndicators.stockMarketRising) {
        result.signal = 'neutral';
        result.interpretation = 'DXY上涨由增长驱动（美股不跌），中性';
      } else {
        result.interpretation = 'DXY小幅上涨，无明确信号';
      }
    } else if (dxyChangePct < -3.0) {
      result.signal = 'bullish';
      result.interpretation = 'DXY下跌，美元走弱，风险资产受益';
      result.action = '提高风险敞口';
    } else {
      result.interpretation = 'DXY变化平稳，无明确信号';
    }

    return result;
  }
}

// =====================
// 信用利差分析
// =====================

export interface CreditSpreadAnalysis {
  spreadBps: number;
  alertLevel: 'normal' | 'elevated' | 'stress' | 'crisis' | 'extreme_crisis';
  signal: 'neutral' | 'caution' | 'bearish' | 'extreme_bearish';
  interpretation: string;
  action: string;
  spreadChangeBps?: number;
}

export class CreditSpreadAnalyzer {
  private alertLevels = {
    normal: 3.0,
    elevated: 5.0,
    stress: 7.0,
    crisis: 10.0
  };

  analyzeCreditSpread(
    spreadBps: number,
    previousSpread?: number
  ): CreditSpreadAnalysis {
    const result: CreditSpreadAnalysis = {
      spreadBps,
      alertLevel: 'normal',
      signal: 'neutral',
      interpretation: '信用利差正常，系统风险低',
      action: ''
    };

    // 利差水平判断
    if (spreadBps < this.alertLevels.normal) {
      result.alertLevel = 'normal';
      result.signal = 'neutral';
    } else if (spreadBps < this.alertLevels.elevated) {
      result.alertLevel = 'elevated';
      result.signal = 'caution';
      result.interpretation = '信用利差偏高，开始关注';
    } else if (spreadBps < this.alertLevels.stress) {
      result.alertLevel = 'stress';
      result.signal = 'bearish';
      result.interpretation = '信用利差扩大，系统性风险上升';
      result.action = '降低风险敞口，准备防御';
    } else if (spreadBps < this.alertLevels.crisis) {
      result.alertLevel = 'crisis';
      result.signal = 'bearish';
      result.interpretation = '信用利差危机水平，市场承压';
      result.action = '大幅降低仓位，启动黑天鹅预案';
    } else {
      result.alertLevel = 'extreme_crisis';
      result.signal = 'extreme_bearish';
      result.interpretation = '信用利差极端水平，系统性风险爆发';
      result.action = '清仓观望，保护资本';
    }

    // 利差变化
    if (previousSpread !== undefined) {
      const spreadChange = spreadBps - previousSpread;
      result.spreadChangeBps = spreadChange;

      if (spreadChange > 100) {
        result.interpretation += '（利差急剧扩大）';
        result.action = '紧急减仓，流动性可能枯竭';
      }
    }

    return result;
  }

  getHistoricalValidation(): { event: string; description: string }[] {
    return [
      {
        event: '2022全年',
        description: '信用利差持续走阔，提前3-6个月预示比特币深熊'
      },
      {
        event: '2023年3月硅谷银行危机',
        description: '利差短暂飙升后迅速回落，对应比特币V型反转'
      }
    ];
  }
}

// =====================
// 美联储政策分析
// =====================

export enum PolicyCycle {
  TIGHTENING = "tightening",
  PAUSE = "pause",
  EASING = "easing",
  HOLD = "hold"
}

export interface FOMCAnalysis {
  dotPlotShift: number;
  overallTone: 'hawkish' | 'dovish' | 'neutral';
  macroScoreAdjustment: number;
  interpretation: string;
  actions: string[];
}

export interface HalvingResonance {
  resonanceScore: number;
  signal: 'strong_bullish' | 'bullish' | 'neutral' | 'bearish';
  interpretation: string;
  recommendation: string;
}

export class FedPolicyAnalyzer {
  private currentCycle: PolicyCycle = PolicyCycle.EASING;

  analyzeFOMCResult(
    dotPlotShift: number,
    hawkishLanguage: number,
    dovishLanguage: number
  ): FOMCAnalysis {
    const netHawkishness = hawkishLanguage - dovishLanguage;
    const result: FOMCAnalysis = {
      dotPlotShift,
      overallTone: 'neutral',
      macroScoreAdjustment: 0,
      interpretation: 'FOMC结果符合预期，无明显倾向',
      actions: []
    };

    if (dotPlotShift < -25) {
      result.overallTone = 'dovish';
      result.macroScoreAdjustment = 1;
      result.interpretation = '点阵图显示降息预期提前，宏观评分+1';
      result.actions.push('提高风险敞口');
    } else if (dotPlotShift > 25) {
      result.overallTone = 'hawkish';
      result.macroScoreAdjustment = -1;
      result.interpretation = '点阵图显示降息预期推迟，宏观评分-1';
      result.actions.push('降低风险敞口');
    } else if (netHawkishness > 2) {
      result.overallTone = 'hawkish';
      result.macroScoreAdjustment = -1;
      result.interpretation = '鲍威尔强调通胀风险，宏观评分-1';
      result.actions.push('谨慎操作');
    } else if (netHawkishness < -2) {
      result.overallTone = 'dovish';
      result.macroScoreAdjustment = 1;
      result.interpretation = '鲍威尔释放鸽派信号，宏观评分+1';
      result.actions.push('可适度提高风险敞口');
    }

    return result;
  }

  getCyclePhaseInfo(): {
    currentPhase: PolicyCycle;
    description: string;
    liquidityScore: string;
    riskLevel: string;
    recommendedPosition: string;
  } {
    const phaseInfo = {
      [PolicyCycle.TIGHTENING]: {
        description: '紧缩周期，比特币系统性逆风',
        liquidityScore: '3-4',
        riskLevel: 'high',
        recommendedPosition: '20-30%'
      },
      [PolicyCycle.PAUSE]: {
        description: '暂停加息，市场喘息期',
        liquidityScore: '5-6',
        riskLevel: 'medium',
        recommendedPosition: '40-50%'
      },
      [PolicyCycle.EASING]: {
        description: '宽松周期，利好风险资产',
        liquidityScore: '6-8',
        riskLevel: 'low',
        recommendedPosition: '60-100%'
      },
      [PolicyCycle.HOLD]: {
        description: '按兵不动，观察期',
        liquidityScore: '5-6',
        riskLevel: 'medium',
        recommendedPosition: '40-60%'
      }
    };

    const info = phaseInfo[this.currentCycle];
    return {
      currentPhase: this.currentCycle,
      description: info.description,
      liquidityScore: info.liquidityScore,
      riskLevel: info.riskLevel,
      recommendedPosition: info.recommendedPosition
    };
  }

  analyzeHalvingResonance(
    halvingCycle: number,
    fedCycle: PolicyCycle,
    halvingType: 'pre_halving' | 'halving_only' | 'post_halving'
  ): HalvingResonance {
    let resonanceScore = 0;

    // 周期共振评分
    if (fedCycle === PolicyCycle.EASING) {
      resonanceScore += 2;
    } else if (fedCycle === PolicyCycle.PAUSE) {
      resonanceScore += 1;
    } else if (fedCycle === PolicyCycle.TIGHTENING) {
      resonanceScore -= 2;
    }

    // 减半前后
    if (halvingType === 'pre_halving') {
      resonanceScore += 1;
    } else if (halvingType === 'post_halving') {
      resonanceScore += 0.5;
    }

    let signal: 'strong_bullish' | 'bullish' | 'neutral' | 'bearish';
    let interpretation: string;
    let recommendation: string;

    if (resonanceScore >= 3) {
      signal = 'strong_bullish';
      interpretation = '减半 + 美联储宽松 = 最强牛市信号';
      recommendation = '满仓持有，回调加仓';
    } else if (resonanceScore >= 1) {
      signal = 'bullish';
      interpretation = '减半 + 美联储宽松/中性 = 较强牛市';
      recommendation = '保持高仓位，回调买入';
    } else if (resonanceScore <= -1) {
      signal = 'bearish';
      interpretation = '减半 + 美联储紧缩 = 结构性压制';
      recommendation = '降低仓位，等待周期转折';
    } else {
      signal = 'neutral';
      interpretation = '周期共振不明显，以其他信号为准';
      recommendation = '观望等待明确信号';
    }

    return { resonanceScore, signal, interpretation, recommendation };
  }
}

// =====================
// 综合经济分析引擎
// =====================

export interface EconomicAnalysisResult {
  liquidity: {
    energyPct: string;
    direction: string;
    score: number;
    interpretation: string;
  };
  realRate: RealRateAnalysis;
  dxy: DXYAnalysis;
  creditSpread: CreditSpreadAnalysis;
  fomc: FOMCAnalysis;
  halvingResonance: HalvingResonance;
  composite: {
    macroScore: number;
    scoreInterpretation: string;
    recommendedPosition: string;
    keyDrivers: string[];
    riskFactors: string[];
  };
}

export class NEMTEconomicAnalyzer {
  private liquidityAnalyzer = new GlobalLiquidityAnalyzer();
  private realRateAnalyzer = new RealRateAnalyzer();
  private dxyAnalyzer = new DollarIndexAnalyzer();
  private creditSpreadAnalyzer = new CreditSpreadAnalyzer();
  private fedAnalyzer = new FedPolicyAnalyzer();

  runFullAnalysis(params: {
    currentBalanceSheet?: number;
    balance12MonthsAgo?: number;
    tipsYield?: number;
    tipsYield1YAgo?: number;
    dxyChangePct?: number;
    vixRising?: boolean;
    treasuryYieldRising?: boolean;
    stockMarketRising?: boolean;
    creditSpreadBps?: number;
    creditSpreadPrevious?: number;
    dotPlotShift?: number;
    hawkishLanguage?: number;
    dovishLanguage?: number;
    halvingType?: 'pre_halving' | 'halving_only' | 'post_halving';
    fedCycle?: PolicyCycle;
  }): EconomicAnalysisResult {
    const {
      currentBalanceSheet = 0,
      balance12MonthsAgo = 0,
      tipsYield = 0,
      tipsYield1YAgo = 0,
      dxyChangePct = 0,
      vixRising = false,
      treasuryYieldRising = false,
      stockMarketRising = true,
      creditSpreadBps = 3.0,
      creditSpreadPrevious = 3.0,
      dotPlotShift = 0,
      hawkishLanguage = 0,
      dovishLanguage = 0,
      halvingType = 'post_halving',
      fedCycle = PolicyCycle.EASING
    } = params;

    // 1. 流动性分析
    const liquidity = this.liquidityAnalyzer.calculateLiquidityEnergy(
      currentBalanceSheet,
      balance12MonthsAgo
    );

    // 2. 实际利率分析
    const realRate = this.realRateAnalyzer.analyzeRealRate(
      tipsYield,
      tipsYield1YAgo
    );

    // 3. DXY分析
    this.dxyAnalyzer.setContext(vixRising, treasuryYieldRising, stockMarketRising);
    const dxy = this.dxyAnalyzer.analyzeDXYChange(dxyChangePct);

    // 4. 信用利差分析
    const creditSpread = this.creditSpreadAnalyzer.analyzeCreditSpread(
      creditSpreadBps,
      creditSpreadPrevious
    );

    // 5. FOMC分析
    const fomc = this.fedAnalyzer.analyzeFOMCResult(
      dotPlotShift,
      hawkishLanguage,
      dovishLanguage
    );

    // 6. 减半周期共振
    const halvingResonance = this.fedAnalyzer.analyzeHalvingResonance(
      4,
      fedCycle,
      halvingType
    );

    // 7. 综合宏观评分
    let totalScore = 5.0;

    totalScore += liquidity.score * 1.5;
    totalScore += realRate.macroScoreContribution;
    totalScore += dxy.macroScoreAdjustment;

    if (creditSpread.signal === 'bearish' || creditSpread.signal === 'extreme_bearish') {
      totalScore -= 1;
    }
    if (creditSpread.alertLevel === 'stress' || creditSpread.alertLevel === 'crisis') {
      totalScore -= 2;
    }

    totalScore += fomc.macroScoreAdjustment;

    totalScore = Math.max(0, Math.min(10, totalScore));

    let scoreInterpretation: string;
    let recommendedPosition: string;

    if (totalScore >= 8) {
      scoreInterpretation = '极度看涨';
      recommendedPosition = '80-100%';
    } else if (totalScore >= 6) {
      scoreInterpretation = '看涨';
      recommendedPosition = '60-80%';
    } else if (totalScore >= 4) {
      scoreInterpretation = '中性';
      recommendedPosition = '40-60%';
    } else if (totalScore >= 2) {
      scoreInterpretation = '看跌';
      recommendedPosition = '20-40%';
    } else {
      scoreInterpretation = '极度看跌';
      recommendedPosition = '10-20%';
    }

    // 关键驱动因素
    const keyDrivers: string[] = [];
    if (liquidity.score > 0) {
      keyDrivers.push(`流动性${liquidity.direction}（${liquidity.value.toFixed(1)}%）`);
    }
    if (realRate.levelSignal === 'bullish') {
      keyDrivers.push('实际利率为负');
    }
    if (halvingResonance.signal === 'strong_bullish' || halvingResonance.signal === 'bullish') {
      keyDrivers.push('减半周期共振');
    }
    if (fomc.overallTone === 'dovish') {
      keyDrivers.push('FOMC释放鸽派信号');
    }

    // 风险因素
    const riskFactors: string[] = [];
    if (liquidity.score < 0) {
      riskFactors.push(`流动性${liquidity.direction}`);
    }
    if (creditSpread.signal === 'bearish' || creditSpread.signal === 'extreme_bearish') {
      riskFactors.push(`信用利差扩大（${creditSpreadBps}bps）`);
    }
    if (dxy.signal === 'bearish') {
      riskFactors.push('DXY避险上涨');
    }
    if (fomc.overallTone === 'hawkish') {
      riskFactors.push('FOMC释放鹰派信号');
    }

    return {
      liquidity: {
        energyPct: `${liquidity.value.toFixed(1)}%`,
        direction: liquidity.direction,
        score: liquidity.score,
        interpretation: liquidity.interpretation
      },
      realRate,
      dxy,
      creditSpread,
      fomc,
      halvingResonance,
      composite: {
        macroScore: totalScore,
        scoreInterpretation,
        recommendedPosition,
        keyDrivers: keyDrivers.length > 0 ? keyDrivers : ['无明确驱动因素'],
        riskFactors: riskFactors.length > 0 ? riskFactors : ['无明显风险']
      }
    };
  }
}

// =====================
// 辅助函数
// =====================

/**
 * 格式化经济分析结果
 */
export function formatEconomicResult(result: EconomicAnalysisResult): string[] {
  const lines: string[] = [];

  lines.push(`[宏观评分] ${result.composite.macroScore.toFixed(1)}/10`);
  lines.push(`  解读: ${result.composite.scoreInterpretation}`);
  lines.push(`  建议仓位: ${result.composite.recommendedPosition}`);

  lines.push('');
  lines.push(`[流动性] ${result.liquidity.energyPct}`);
  lines.push(`  ${result.liquidity.interpretation}`);

  lines.push('');
  lines.push(`[实际利率] ${result.realRate.currentRate.toFixed(2)}%`);
  if (result.realRate.yoyChange !== undefined) {
    lines.push(`  年变化: ${result.realRate.yoyChange >= 0 ? '+' : ''}${result.realRate.yoyChange.toFixed(2)}%`);
  }
  lines.push(`  ${result.realRate.action}`);

  lines.push('');
  lines.push(`[DXY] ${result.dxy.dxyChange >= 0 ? '+' : ''}${result.dxy.dxyChange.toFixed(1)}%`);
  lines.push(`  ${result.dxy.interpretation}`);

  lines.push('');
  lines.push(`[信用利差] ${result.creditSpread.spreadBps}bps`);
  lines.push(`  ${result.creditSpread.interpretation}`);

  lines.push('');
  lines.push(`[FOMC] ${result.fomc.overallTone}`);
  lines.push(`  ${result.fomc.interpretation}`);

  lines.push('');
  lines.push(`[减半共振] ${result.halvingResonance.resonanceScore}`);
  lines.push(`  ${result.halvingResonance.recommendation}`);

  if (result.composite.keyDrivers.length > 0) {
    lines.push('');
    lines.push('[关键驱动]');
    result.composite.keyDrivers.forEach(d => lines.push(`  + ${d}`));
  }

  if (result.composite.riskFactors.length > 0) {
    lines.push('');
    lines.push('[风险因素]');
    result.composite.riskFactors.forEach(r => lines.push(`  - ${r}`));
  }

  return lines;
}

/**
 * 能量层级名称
 */
export function getEnergyLevelName(level: EnergyLevel): string {
  const names: Record<EnergyLevel, string> = {
    [EnergyLevel.FOUNDATION]: '基础能量',
    [EnergyLevel.MARGINAL]: '边际能量',
    [EnergyLevel.IMPULSE]: '脉冲能量'
  };
  return names[level];
}
