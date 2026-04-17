/**
 * NEMT 第十二章：趋势概率与执行优化
 * TypeScript 版本
 */

// =====================
// 交易周期类型
// =====================

export enum TradeHorizon {
  LONG_TERM = "long_term",
  MID_TERM = "mid_term",
  SHORT_TERM = "short_term"
}

// =====================
// 概率修正项
// =====================

export interface ProbabilityModifiers {
  // 宏观修正
  realRateDeclining?: boolean;      // 实际利率同比下降>0.5%
  creditSpreadWidening?: boolean;   // 信用利差走阔>20%
  halvingMainWindow?: boolean;      // 减半后6-18个月

  // 链上修正
  btcExchangeWithdrawal?: boolean;   // 交易所BTC余额月降幅>5%
  stablecoinDepositIncrease?: boolean;  // 稳定币交易所余额月增幅>10%
  whaleInflow3days?: boolean;       // 鲸鱼连续3日净流入交易所

  // 相位修正
  resonance3Conditions?: boolean;   // 随机共振三条件全部满足
  soliton4Features?: boolean;      // 孤子五特征满足四项以上
  noiseBurst?: boolean;              // 出现噪声暴
}

// =====================
// 趋势概率模型
// =====================

export interface ProbabilityResult {
  pTrend: number;
  pMacro: number;
  pOnchain: number;
  pPhase: number;
  pSpacetime: number;
  horizon: string;
}

export class TrendProbabilityModel {
  private HORIZON_WEIGHTS: Record<TradeHorizon, Record<string, number>> = {
    [TradeHorizon.LONG_TERM]: {
      p_macro: 0.35,
      p_onchain: 0.35,
      p_phase: 0.15,
      p_spacetime: 0.15
    },
    [TradeHorizon.MID_TERM]: {
      p_macro: 0.25,
      p_onchain: 0.30,
      p_phase: 0.25,
      p_spacetime: 0.20
    },
    [TradeHorizon.SHORT_TERM]: {
      p_macro: 0.15,
      p_onchain: 0.20,
      p_phase: 0.40,
      p_spacetime: 0.25
    }
  };

  private MODIFIER_BONUSES: Record<string, number> = {
    realRateDeclining: 0.10,
    creditSpreadWidening: -0.15,
    halvingMainWindow: 0.10,
    btcExchangeWithdrawal: 0.10,
    stablecoinDepositIncrease: 0.05,
    whaleInflow3days: -0.10,
    resonance3Conditions: 0.15,
    soliton4Features: 0.10,
    noiseBurst: -0.20
  };

  private currentPTrend = 0.5;

  applyModifiers(
    baseProb: number,
    modifiers: ProbabilityModifiers,
    dimension: 'macro' | 'onchain' | 'phase'
  ): number {
    let prob = baseProb;

    if (dimension === 'macro') {
      if (modifiers.realRateDeclining) prob += this.MODIFIER_BONUSES.realRateDeclining;
      if (modifiers.creditSpreadWidening) prob += this.MODIFIER_BONUSES.creditSpreadWidening;
      if (modifiers.halvingMainWindow) prob += this.MODIFIER_BONUSES.halvingMainWindow;
    } else if (dimension === 'onchain') {
      if (modifiers.btcExchangeWithdrawal) prob += this.MODIFIER_BONUSES.btcExchangeWithdrawal;
      if (modifiers.stablecoinDepositIncrease) prob += this.MODIFIER_BONUSES.stablecoinDepositIncrease;
      if (modifiers.whaleInflow3days) prob += this.MODIFIER_BONUSES.whaleInflow3days;
    } else if (dimension === 'phase') {
      if (modifiers.resonance3Conditions) prob += this.MODIFIER_BONUSES.resonance3Conditions;
      if (modifiers.soliton4Features) prob += this.MODIFIER_BONUSES.soliton4Features;
      if (modifiers.noiseBurst) prob += this.MODIFIER_BONUSES.noiseBurst;
    }

    return Math.max(0.05, Math.min(0.95, prob));
  }

  calculatePTrend(
    pMacro: number,
    pOnchain: number,
    pPhase: number,
    pSpacetime: number,
    modifiers: ProbabilityModifiers,
    horizon: TradeHorizon = TradeHorizon.MID_TERM
  ): ProbabilityResult {
    const weights = this.HORIZON_WEIGHTS[horizon];

    // 应用修正项
    const pMacro = this.applyModifiers(pMacro, modifiers, 'macro');
    const pOnchain = this.applyModifiers(pOnchain, modifiers, 'onchain');
    const pPhase = this.applyModifiers(pPhase, modifiers, 'phase');
    const pSpacetime = pSpacetime;

    // 加权几何平均
    let pTrend: number;
    try {
      const logSum = (
        weights.p_macro * Math.log(Math.max(0.01, pMacro)) +
        weights.p_onchain * Math.log(Math.max(0.01, pOnchain)) +
        weights.p_phase * Math.log(Math.max(0.01, pPhase)) +
        weights.p_spacetime * Math.log(Math.max(0.01, pSpacetime))
      );
      pTrend = Math.exp(logSum);
    } catch {
      pTrend = (pMacro + pOnchain + pPhase + pSpacetime) / 4;
    }

    this.currentPTrend = pTrend;

    return {
      pTrend,
      pMacro,
      pOnchain,
      pPhase,
      pSpacetime,
      horizon: horizon.value
    };
  }

  getPositionCoefficient(pTrend: number): number {
    if (pTrend >= 0.80) return 1.0;
    if (pTrend >= 0.70) return 0.8;
    if (pTrend >= 0.60) return 0.6;
    if (pTrend >= 0.50) return 0.4;
    return 0.0;
  }

  calculatePosition(pTrend: number, phaseMaxPosition: number): {
    positionPct: number;
    coefficient: number;
    phaseMax: number;
    action: string;
  } {
    const coefficient = this.getPositionCoefficient(pTrend);
    const positionPct = phaseMaxPosition * coefficient;

    let action: string;
    if (positionPct >= 0.8) {
      action = '重仓持有，趋势明确';
    } else if (positionPct >= 0.5) {
      action = '标准仓位';
    } else if (positionPct >= 0.3) {
      action = '轻仓试探';
    } else {
      action = '观望或清仓';
    }

    return {
      positionPct: positionPct * 100,
      coefficient,
      phaseMax: phaseMaxPosition * 100,
      action
    };
  }
}

// =====================
// 贝叶斯更新模型
// =====================

export interface BayesianUpdateResult {
  pNew: number;
  pOld: number;
  pChange: number;
  evidence: string;
  evidenceDescription: string;
  isConfirming: boolean;
}

export class BayesianUpdateModel {
  private PRESET_EVIDENCES: Record<string, {
    pEGivenH: number;
    pEGivenNotH: number;
    description: string;
  }> = {
    breakout_confirmed: {
      pEGivenH: 0.85,
      pEGivenNotH: 0.30,
      description: '突破确认（量价配合）'
    },
    dci_sustained_above_0_7: {
      pEGivenH: 0.80,
      pEGivenNotH: 0.25,
      description: 'DCI持续高于0.7超过5天'
    },
    oi_following: {
      pEGivenH: 0.75,
      pEGivenNotH: 0.35,
      description: 'OI跟随价格上涨'
    },
    whale_accumulation: {
      pEGivenH: 0.70,
      pEGivenNotH: 0.40,
      description: '鲸鱼累积信号'
    },
    macro_score_improving: {
      pEGivenH: 0.70,
      pEGivenNotH: 0.45,
      description: '宏观评分持续改善'
    },
    fake_breakout: {
      pEGivenH: 0.15,
      pEGivenNotH: 0.70,
      description: '假突破后回落'
    },
    dci_divergence: {
      pEGivenH: 0.20,
      pEGivenNotH: 0.65,
      description: 'DCI与价格背离'
    },
    oi_drop: {
      pEGivenH: 0.25,
      pEGivenNotH: 0.60,
      description: 'OI下跌伴随价格上涨'
    },
    volume_decline: {
      pEGivenH: 0.30,
      pEGivenNotH: 0.55,
      description: '上涨时成交量萎缩'
    },
    noise_burst: {
      pEGivenH: 0.10,
      pEGivenNotH: 0.80,
      description: '噪声暴出现'
    },
    consolidation: {
      pEGivenH: 0.60,
      pEGivenNotH: 0.50,
      description: '盘整（正常调整）'
    }
  };

  bayesianUpdate(
    pOld: number,
    evidenceKey: string,
    customLikelihood?: [number, number]
  ): BayesianUpdateResult {
    let pEGivenH: number;
    let pEGivenNotH: number;
    let description = '';

    if (customLikelihood) {
      pEGivenH = customLikelihood[0];
      pEGivenNotH = customLikelihood[1];
    } else if (this.PRESET_EVIDENCES[evidenceKey]) {
      const ev = this.PRESET_EVIDENCES[evidenceKey];
      pEGivenH = ev.pEGivenH;
      pEGivenNotH = ev.pEGivenNotH;
      description = ev.description;
    } else {
      return {
        pNew: pOld,
        pOld,
        pChange: 0,
        evidence: evidenceKey,
        evidenceDescription: '未知证据类型',
        isConfirming: false
      };
    }

    const numerator = pEGivenH * pOld;
    const denominator = pEGivenH * pOld + pEGivenNotH * (1 - pOld);

    const pNew = denominator > 0 ? numerator / denominator : pOld;

    return {
      pNew,
      pOld,
      pChange: pNew - pOld,
      evidence: evidenceKey,
      evidenceDescription: description,
      isConfirming: pNew > pOld
    };
  }

  simplifiedUpdate(
    pOld: number,
    signal: 'bullish' | 'bearish' | 'neutral'
  ): number {
    if (signal === 'bullish') {
      return Math.max(0.05, Math.min(0.95, pOld + 0.10));
    } else if (signal === 'bearish') {
      return Math.max(0.05, Math.min(0.95, pOld - 0.15));
    }
    return pOld;
  }

  shouldExit(pTrend: number): boolean {
    return pTrend < 0.50;
  }
}

// =====================
// 执行优化模型
// =====================

export interface ExecutionPlan {
  orderType: 'twap' | 'vwap' | 'market';
  numSplits: number;
  splitIntervalMinutes: number;
  avoidFundingTimes: string[];
  liquidityCheckPassed: boolean;
}

export interface StopLossPlan {
  atrDistance: number;
  atrMultiplier: number;
  structureDistance: number;
  finalStopLoss: number;
  stopLossPct: number;
}

export class ExecutionOptimizer {
  private ATR_MULTIPLIERS: Array<[number, number, number]> = [
    [0.80, 1.0, 1.5],
    [0.60, 0.80, 2.0],
    [0.40, 0.60, 2.5],
    [0.20, 0.40, 3.0]
  ];

  private FUNDING_SETTLEMENT_TIMES = ['UTC 00:00', 'UTC 08:00', 'UTC 16:00'];

  createEntryPlan(
    positionSizeUsd: number,
    currentPrice: number,
    orderType: 'twap' | 'vwap' | 'market' = 'twap'
  ): ExecutionPlan {
    let numSplits: number;
    if (positionSizeUsd <= 10000) {
      numSplits = 1;
    } else if (positionSizeUsd <= 50000) {
      numSplits = 3;
    } else if (positionSizeUsd <= 100000) {
      numSplits = 5;
    } else if (positionSizeUsd <= 500000) {
      numSplits = 8;
    } else {
      numSplits = 10;
    }

    const splitIntervalMinutes = numSplits <= 5 ? 3 : 5;

    return {
      orderType,
      numSplits,
      splitIntervalMinutes,
      avoidFundingTimes: this.FUNDING_SETTLEMENT_TIMES,
      liquidityCheckPassed: true  // 实际应检查订单簿
    };
  }

  calculateStopLoss(params: {
    atr: number;
    currentPrice: number;
    pTrend: number;
    entryPrice: number;
    isLong?: boolean;
    vortexMid?: number;
    recentLow?: number;
    lthCostBasis?: number;
  }): StopLossPlan {
    const {
      atr,
      currentPrice,
      pTrend,
      entryPrice,
      isLong = true,
      vortexMid,
      recentLow,
      lthCostBasis
    } = params;

    // ATR倍数K
    let atrMultiplier = 2.0;
    for (const [low, high, k] of this.ATR_MULTIPLIERS) {
      if (low <= pTrend && pTrend < high) {
        atrMultiplier = k;
        break;
      }
    }

    const atrDistance = atr * atrMultiplier;

    // 结构止损位
    let structureDistance = Infinity;

    if (isLong) {
      const candidates: Array<[string, number]> = [];
      if (vortexMid) candidates.push(['涡旋区间中轴', vortexMid]);
      if (recentLow) candidates.push(['近期低点', recentLow]);
      if (lthCostBasis) candidates.push(['LTH成本基础', lthCostBasis]);

      if (candidates.length > 0) {
        const minCandidate = candidates.reduce((min, curr) =>
          Math.abs(curr[1] - entryPrice) < Math.abs(min[1] - entryPrice) ? curr : min
        );
        structureDistance = entryPrice - minCandidate[1];
      }
    } else {
      const candidates: Array<[string, number]> = [];
      if (vortexMid) candidates.push(['涡旋区间中轴', vortexMid]);
      if (recentLow) candidates.push(['近期高点', recentLow]);

      if (candidates.length > 0) {
        const maxCandidate = candidates.reduce((max, curr) =>
          Math.abs(curr[1] - entryPrice) > Math.abs(max[1] - entryPrice) ? curr : max
        );
        structureDistance = maxCandidate[1] - entryPrice;
      }
    }

    // 取较小值
    const finalDistance = Math.min(atrDistance, structureDistance === Infinity ? atrDistance : structureDistance);

    const finalStopLoss = isLong
      ? entryPrice - finalDistance
      : entryPrice + finalDistance;

    const stopLossPct = (finalDistance / entryPrice) * 100;

    return {
      atrDistance,
      atrMultiplier,
      structureDistance: structureDistance === Infinity ? 0 : structureDistance,
      finalStopLoss,
      stopLossPct
    };
  }
}

// =====================
// 综合概率执行引擎
// =====================

export interface ProbabilityExecutionResult {
  probability: {
    pTrend: string;
    pMacro: string;
    pOnchain: string;
    pPhase: string;
    pSpacetime: string;
    horizon: string;
  };
  position: {
    recommendedPct: string;
    coefficient: number;
    action: string;
  };
  execution: {
    orderType: string;
    numSplits: number;
    splitInterval: string;
    avoidTimes: string[];
    liquidityCheck: string;
  };
  stopLoss: {
    atrDistance: string;
    atrMultiplier: number;
    stopPrice: string;
    stopLossPct: string;
  };
  decision: {
    shouldEnter: boolean;
    shouldExit: boolean;
    confidence: '高' | '中' | '低';
  };
}

export class NEMTProbabilityEngine {
  private probabilityModel = new TrendProbabilityModel();
  private bayesianModel = new BayesianUpdateModel();
  private executionOptimizer = new ExecutionOptimizer();

  analyzeAndPlan(params: {
    pMacro?: number;
    pOnchain?: number;
    pPhase?: number;
    pSpacetime?: number;
    modifiers?: ProbabilityModifiers;
    horizon?: TradeHorizon;
    phaseMaxPosition?: number;
    positionSizeUsd?: number;
    atr?: number;
    currentPrice?: number;
    vortexMid?: number;
    recentLow?: number;
    lthCostBasis?: number;
  }): ProbabilityExecutionResult {
    const {
      pMacro = 0.5,
      pOnchain = 0.5,
      pPhase = 0.5,
      pSpacetime = 0.5,
      modifiers = {},
      horizon = TradeHorizon.MID_TERM,
      phaseMaxPosition = 0.7,
      positionSizeUsd = 10000,
      atr = 2000,
      currentPrice = 60000,
      vortexMid,
      recentLow,
      lthCostBasis
    } = params;

    // 1. 计算趋势概率
    const probResult = this.probabilityModel.calculatePTrend(
      pMacro, pOnchain, pPhase, pSpacetime, modifiers, horizon
    );

    // 2. 计算仓位
    const positionResult = this.probabilityModel.calculatePosition(
      probResult.pTrend, phaseMaxPosition
    );

    // 3. 创建执行计划
    const executionPlan = this.executionOptimizer.createEntryPlan(
      positionSizeUsd, currentPrice
    );

    // 4. 计算止损
    const stopLossPlan = this.executionOptimizer.calculateStopLoss({
      atr,
      currentPrice,
      pTrend: probResult.pTrend,
      entryPrice: currentPrice,
      vortexMid,
      recentLow,
      lthCostBasis
    });

    // 5. 综合决策
    const shouldEnter = probResult.pTrend >= 0.50;
    const shouldExit = this.bayesianModel.shouldExit(probResult.pTrend);

    let confidence: '高' | '中' | '低';
    if (probResult.pTrend >= 0.7) confidence = '高';
    else if (probResult.pTrend >= 0.5) confidence = '中';
    else confidence = '低';

    return {
      probability: {
        pTrend: `${(probResult.pTrend * 100).toFixed(1)}%`,
        pMacro: `${(probResult.pMacro * 100).toFixed(1)}%`,
        pOnchain: `${(probResult.pOnchain * 100).toFixed(1)}%`,
        pPhase: `${(probResult.pPhase * 100).toFixed(1)}%`,
        pSpacetime: `${(probResult.pSpacetime * 100).toFixed(1)}%`,
        horizon: probResult.horizon
      },
      position: {
        recommendedPct: `${positionResult.positionPct.toFixed(0)}%`,
        coefficient: positionResult.coefficient,
        action: positionResult.action
      },
      execution: {
        orderType: executionPlan.orderType,
        numSplits: executionPlan.numSplits,
        splitInterval: `${executionPlan.splitIntervalMinutes}分钟`,
        avoidTimes: executionPlan.avoidFundingTimes,
        liquidityCheck: executionPlan.liquidityCheckPassed ? '通过' : '失败'
      },
      stopLoss: {
        atrDistance: `$${stopLossPlan.atrDistance.toFixed(0)}`,
        atrMultiplier: stopLossPlan.atrMultiplier,
        stopPrice: `$${stopLossPlan.finalStopLoss.toFixed(0)}`,
        stopLossPct: `${stopLossPlan.stopLossPct.toFixed(1)}%`
      },
      decision: {
        shouldEnter,
        shouldExit,
        confidence
      }
    };
  }

  // 贝叶斯更新
  updateProbability(
    pOld: number,
    evidenceKey: string,
    customLikelihood?: [number, number]
  ): BayesianUpdateResult {
    return this.bayesianModel.bayesianUpdate(pOld, evidenceKey, customLikelihood);
  }

  // 简化更新
  simplifiedUpdate(pOld: number, signal: 'bullish' | 'bearish' | 'neutral'): number {
    return this.bayesianModel.simplifiedUpdate(pOld, signal);
  }
}

// =====================
// 辅助函数
// =====================

/**
 * 获取交易周期名称
 */
export function getHorizonName(horizon: TradeHorizon): string {
  const names: Record<TradeHorizon, string> = {
    [TradeHorizon.LONG_TERM]: '长线持仓>3个月',
    [TradeHorizon.MID_TERM]: '中线持仓2-8周',
    [TradeHorizon.SHORT_TERM]: '短线持仓1-5天'
  };
  return names[horizon];
}

/**
 * 获取周期权重
 */
export function getHorizonWeights(horizon: TradeHorizon): Record<string, number> {
  const weights: Record<TradeHorizon, Record<string, number>> = {
    [TradeHorizon.LONG_TERM]: { macro: 0.35, onchain: 0.35, phase: 0.15, spacetime: 0.15 },
    [TradeHorizon.MID_TERM]: { macro: 0.25, onchain: 0.30, phase: 0.25, spacetime: 0.20 },
    [TradeHorizon.SHORT_TERM]: { macro: 0.15, onchain: 0.20, phase: 0.40, spacetime: 0.25 }
  };
  return weights[horizon];
}

/**
 * 格式化概率执行结果
 */
export function formatProbabilityResult(result: ProbabilityExecutionResult): string[] {
  const lines: string[] = [];

  lines.push(`[趋势概率] ${result.probability.pTrend}`);
  lines.push(`  宏观: ${result.probability.pMacro}`);
  lines.push(`  链上: ${result.probability.pOnchain}`);
  lines.push(`  相位: ${result.probability.pPhase}`);
  lines.push(`  时空: ${result.probability.pSpacetime}`);
  lines.push(`  周期: ${result.probability.horizon}`);

  lines.push('');
  lines.push(`[仓位建议] ${result.position.recommendedPct}`);
  lines.push(`  ${result.position.action}`);

  lines.push('');
  lines.push(`[执行计划]`);
  lines.push(`  订单类型: ${result.execution.orderType}`);
  lines.push(`  分批数量: ${result.execution.numSplits}`);
  lines.push(`  间隔: ${result.execution.splitInterval}`);
  lines.push(`  避开: ${result.execution.avoidTimes.join(', ')}`);

  lines.push('');
  lines.push(`[止损计划]`);
  lines.push(`  止损位: ${result.stopLoss.stopPrice}`);
  lines.push(`  ATR倍数: ${result.stopLoss.atrMultiplier}`);
  lines.push(`  止损%: ${result.stopLoss.stopLossPct}`);

  lines.push('');
  lines.push(`[决策]`);
  lines.push(`  入场: ${result.decision.shouldEnter ? '是' : '否'}`);
  lines.push(`  离场: ${result.decision.shouldExit ? '是' : '否'}`);
  lines.push(`  信心: ${result.decision.confidence}`);

  return lines;
}
