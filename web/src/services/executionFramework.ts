/**
 * NEMT 执行框架核心服务
 * 实现第七章：预测→信号→验证→加仓 的完整逻辑
 */

import { MarketPhase } from '../types/nemt';

// =====================
// 7.2 预测模块
// =====================

export interface MacroScores {
  macroScore: number;
  onchainScore: number;
  halvingPhase: 'early' | 'main_rise' | 'late' | 'bear_market';
  monthsSinceHalving: number;
  rtiScore: number;
}

export type DirectionBias = 'strongly_bullish' | 'cautiously_bullish' | 'neutral' | 'cautiously_bearish' | 'strongly_bearish' | 'watch';
export type CycleLevel = 'monthly' | 'weekly' | 'daily' | 'none';
export type HuntingMode = 'on' | 'off';

export interface Prediction {
  directionBias: DirectionBias;
  cycleLevel: CycleLevel;
  huntingMode: HuntingMode;
  confidence: number;
  reason: string;
  macroScore: number;
  onchainScore: number;
  halvingPhase: 'early' | 'main_rise' | 'late' | 'bear_market';
  rtiScore: number;
}

function determineDirectionBias(macro: number, onchain: number): DirectionBias {
  if (macro >= 7 && onchain >= 7) return 'strongly_bullish';
  if (macro >= 7 && onchain >= 4 && onchain <= 6) return 'cautiously_bullish';
  if (macro >= 7 && onchain <= 3) return 'watch';
  if (macro >= 4 && macro <= 6 && onchain >= 7) return 'cautiously_bullish';
  if (macro >= 4 && macro <= 6 && onchain >= 4 && onchain <= 6) return 'neutral';
  if (macro >= 4 && macro <= 6 && onchain <= 3) return 'cautiously_bearish';
  if (macro <= 3 && onchain >= 7) return 'watch';
  if (macro <= 3 && onchain >= 4 && onchain <= 6) return 'cautiously_bearish';
  if (macro <= 3 && onchain <= 3) return 'strongly_bearish';
  return 'neutral';
}

function determineCycleLevel(macro: number, onchain: number, halvingPhase: string): CycleLevel {
  if (macro >= 7 && onchain >= 7 && halvingPhase === 'main_rise') return 'monthly';
  if ((macro >= 4 && macro <= 6 && onchain >= 7) || (macro >= 7 && onchain >= 4 && onchain <= 6)) return 'weekly';
  if (macro <= 3 && onchain <= 3) return 'none';
  return 'daily';
}

function determineHuntingMode(direction: DirectionBias, cycle: CycleLevel): HuntingMode {
  if ((direction === 'strongly_bullish' || direction === 'cautiously_bullish' ||
       direction === 'strongly_bearish' || direction === 'cautiously_bearish') &&
      (cycle === 'monthly' || cycle === 'weekly')) {
    return 'on';
  }
  return 'off';
}

export function runPrediction(scores: MacroScores): Prediction {
  let directionBias = determineDirectionBias(scores.macroScore, scores.onchainScore);
  
  if (scores.rtiScore >= 5 && directionBias === 'cautiously_bullish') {
    directionBias = 'strongly_bullish';
  } else if (scores.rtiScore <= -5 && directionBias === 'cautiously_bearish') {
    directionBias = 'strongly_bearish';
  }
  
  const cycleLevel = determineCycleLevel(scores.macroScore, scores.onchainScore, scores.halvingPhase);
  const huntingMode = determineHuntingMode(directionBias, cycleLevel);
  
  let confidence = 0.5;
  if (directionBias === 'strongly_bullish' || directionBias === 'strongly_bearish') confidence = 0.8;
  else if (directionBias === 'cautiously_bullish' || directionBias === 'cautiously_bearish') confidence = 0.6;
  
  const directionText: Record<DirectionBias, string> = {
    strongly_bullish: '强烈看多', cautiously_bullish: '谨慎看多', neutral: '中性',
    cautiously_bearish: '谨慎看空', strongly_bearish: '强烈看空', watch: '观望',
  };
  const cycleText: Record<CycleLevel, string> = {
    monthly: '月线级别趋势', weekly: '周线级别波段', daily: '日线级别交易', none: '不交易',
  };
  
  return {
    directionBias,
    cycleLevel,
    huntingMode,
    confidence,
    reason: huntingMode === 'on' 
      ? `${directionText[directionBias]}，预期${cycleText[cycleLevel]}，狩猎模式开启`
      : '市场环境不支持交易，狩猎模式关闭',
    macroScore: scores.macroScore,
    onchainScore: scores.onchainScore,
    halvingPhase: scores.halvingPhase,
    rtiScore: scores.rtiScore,
  };
}

// =====================
// 7.3 信号模块
// =====================

export type SignalType = 'vortex_breakout' | 'stochastic_resonance' | 'trend_pullback' | 'none';

export interface Signal {
  type: SignalType;
  direction: 'long' | 'short';
  confidence: number;
  maturity: number;
  phase: string;
  price?: number;
  timestamp: string;
  reason: string;
}

export interface SignalConditions {
  dci: number;
  vortexMaturity: number;
  phase: MarketPhase;
  spectralWidth: number;
  priceMomentum: number;
  noiseLevel: number;
  trendMA20Distance: number;
  trendMA50Distance: number;
}

export function checkSignals(cond: SignalConditions, huntingMode: HuntingMode): Signal {
  if (huntingMode === 'off') {
    return { type: 'none', direction: 'long', confidence: 0, maturity: 0, phase: '', timestamp: new Date().toISOString(), reason: '狩猎模式关闭，不产生交易信号' };
  }
  
  // 涡旋突破信号
  if (cond.vortexMaturity >= 5 && cond.vortexMaturity <= 15 && cond.dci >= 0.55 && cond.phase === 'C') {
    return {
      type: 'vortex_breakout',
      direction: 'long',
      confidence: 0.55 + cond.vortexMaturity / 100,
      maturity: cond.vortexMaturity,
      phase: cond.phase,
      timestamp: new Date().toISOString(),
      reason: `涡旋突破信号，成熟度${cond.vortexMaturity}，DCI ${cond.dci.toFixed(2)}`,
    };
  }
  
  // 随机共振触发
  const noiseLevelOk = cond.noiseLevel >= 0.08 && cond.noiseLevel <= 0.15;
  if (noiseLevelOk && cond.phase === 'B' && cond.dci >= 0.5) {
    return {
      type: 'stochastic_resonance',
      direction: 'long',
      confidence: 0.60,
      maturity: cond.vortexMaturity,
      phase: cond.phase,
      timestamp: new Date().toISOString(),
      reason: `随机共振触发，噪声水平 ${cond.noiseLevel.toFixed(3)}，相位B`,
    };
  }
  
  // 趋势回调结束
  const nearMA = Math.abs(cond.trendMA20Distance) < 0.03 || Math.abs(cond.trendMA50Distance) < 0.05;
  if (nearMA && cond.dci >= 0.6 && cond.phase === 'D' && cond.priceMomentum > 0) {
    return {
      type: 'trend_pullback',
      direction: 'long',
      confidence: 0.65,
      maturity: cond.vortexMaturity,
      phase: 'D',
      timestamp: new Date().toISOString(),
      reason: `趋势回调结束信号，价格回踩均线，DCI ${cond.dci.toFixed(2)}`,
    };
  }
  
  return { type: 'none', direction: 'long', confidence: 0, maturity: 0, phase: '', timestamp: new Date().toISOString(), reason: '无有效信号，继续等待' };
}

// =====================
// 7.4 验证模块
// =====================

export interface VerificationItem {
  name: string;
  passed: boolean;
  weight: 'required' | 'high' | 'medium' | 'bonus';
  detail: string;
}

export interface VerificationResult {
  passed: boolean;
  confidence: 'full' | 'half' | 'failed';
  items: VerificationItem[];
  passedCount: number;
  totalWeight: number;
}

export interface VerificationInput {
  volumeConfirm: boolean;
  closePriceConfirm: boolean;
  oiConfirm: boolean;
  timeConfirm: boolean;
  fundingRateConfirm: boolean;
  onchainConfirm: boolean;
  priceChangePercent: number;
  volumeRatio: number;
}

export function verifyVortexBreakout(input: VerificationInput): VerificationResult {
  const items: VerificationItem[] = [
    { name: '成交量确认', passed: input.volumeRatio > 1.5, weight: 'required', detail: input.volumeRatio > 1.5 ? `量比 ${input.volumeRatio.toFixed(2)} > 1.5 ✓` : `量比不足 ✗` },
    { name: '收盘价确认', passed: input.priceChangePercent > 0.5, weight: 'required', detail: input.priceChangePercent > 0.5 ? `突破幅度 OK ✓` : `突破幅度不足 ✗` },
    { name: '持仓量确认', passed: input.oiConfirm, weight: 'high', detail: input.oiConfirm ? 'OI继续增长 ✓' : 'OI未确认 ✗' },
    { name: '时间确认', passed: input.timeConfirm, weight: 'high', detail: input.timeConfirm ? '突破后1小时未回落 ✓' : '时间确认失败 ✗' },
    { name: '资金费率确认', passed: input.fundingRateConfirm, weight: 'medium', detail: input.fundingRateConfirm ? '费率倾斜 ✓' : '费率未确认 ✗' },
    { name: '链上确认', passed: input.onchainConfirm, weight: 'bonus', detail: input.onchainConfirm ? '交易所BTC净流出 ✓' : '链上未确认 ✗' },
  ];
  
  const requiredPassed = items.filter(i => i.weight === 'required' && i.passed).length;
  const highPassed = items.filter(i => i.weight === 'high' && i.passed).length;
  const passedCount = items.filter(i => i.passed).length;
  
  let passed = false;
  let confidence: 'full' | 'half' | 'failed' = 'failed';
  if (requiredPassed >= 2 && highPassed >= 2) { passed = true; confidence = 'full'; }
  else if (requiredPassed >= 2 && highPassed >= 1) { passed = true; confidence = 'half'; }
  
  return { passed, confidence, items, passedCount, totalWeight: items.length };
}

// =====================
// 7.5 加仓模块
// =====================

export type AddPositionTiming = 'breakout_retest' | 'ma_pullback' | 'higher_tf_breakout';

export interface Position {
  entryPrice: number;
  currentPrice: number;
  size: number;
  unrealizedPnL: number;
  pnlPercent: number;
  stopLoss: number;
  positionPhase: number;
  entryTime: string;
}

export function positionPnLPercent(position: Position): number {
  return ((position.currentPrice - position.entryPrice) / position.entryPrice) * 100;
}

export function canAddPosition(position: Position, dci: number, noiseRatio: number, nuplWeeks: number): { canAdd: boolean; reason: string } {
  if (position.pnlPercent < 0) return { canAdd: false, reason: '浮亏状态禁止加仓' };
  if (dci > 0.7) return { canAdd: false, reason: 'DCI高位，趋势可能衰竭' };
  if (noiseRatio > 2.0) return { canAdd: false, reason: '链上信号/噪声比急剧下降' };
  if (nuplWeeks > 4) return { canAdd: false, reason: 'NUPL欣快区超过4周，禁止加仓' };
  return { canAdd: true, reason: '可以加仓' };
}

export function checkAddPositionTiming(position: Position, signal: {
  price: number;
  maPullbackVolume: number;
  dciPullbackRecovered: boolean;
  higherTfBreakout: boolean;
  monthMVRV: number;
}): AddPositionTiming | null {
  if (position.pnlPercent > 0 && signal.maPullbackVolume < 0.7) return 'breakout_retest';
  if (signal.maPullbackVolume > 0 && signal.dciPullbackRecovered) return 'ma_pullback';
  if (signal.higherTfBreakout && signal.monthMVRV < 5) return 'higher_tf_breakout';
  return null;
}

export function calculateNewStopLoss(position: Position, addPositionPrice: number, retestLow: number): number {
  const originalRiskPercent = (position.entryPrice - position.stopLoss) / position.entryPrice;
  const retestStopPercent = (1 - retestLow / addPositionPrice) * 0.98;
  return position.entryPrice * (1 - Math.max(originalRiskPercent, retestStopPercent));
}

// =====================
// 7.6 反馈循环
// =====================

export interface FeedbackCheck {
  event: string;
  shouldReassess: boolean;
  reassessContent: string;
}

export function checkFeedbackLoop(position: Position | null, currentMetrics: {
  pnlPercent: number;
  priceNearATH: boolean;
  dci: number;
  macroScore: number;
  monthsSinceHalving: number;
}): FeedbackCheck[] {
  const checks: FeedbackCheck[] = [];
  if (!position) return checks;
  
  if (currentMetrics.pnlPercent > 20) checks.push({ event: '持仓盈利超过20%', shouldReassess: true, reassessContent: '重新评估预期周期级别' });
  if (currentMetrics.priceNearATH) checks.push({ event: '价格触及历史前高', shouldReassess: true, reassessContent: '重新评估宏观和链上评分' });
  if (currentMetrics.dci < 0.6 && position.pnlPercent > 10) checks.push({ event: 'DCI从高位回落至0.6以下', shouldReassess: true, reassessContent: '趋势可能衰竭' });
  if (currentMetrics.macroScore <= 3) checks.push({ event: '宏观流动性评分降至≤3', shouldReassess: true, reassessContent: '重新运行完整预测步骤' });
  if (currentMetrics.monthsSinceHalving > 18) checks.push({ event: '减半周期进入末端', shouldReassess: true, reassessContent: '重新评估仓位上限' });
  
  return checks;
}

// =====================
// 7.7 仓位计算
// =====================

export interface KellyParams {
  winRate: number;
  rewardRiskRatio: number;
  confidenceCoefficient: number;
}

export function calculateKellyPositionSize(params: KellyParams): number {
  const { winRate, rewardRiskRatio, confidenceCoefficient } = params;
  const kelly = (winRate * rewardRiskRatio - (1 - winRate)) / rewardRiskRatio;
  return Math.max(0, kelly * confidenceCoefficient);
}

export function getKellyParamsForSignalType(signalType: SignalType, maturity: number = 10): KellyParams {
  switch (signalType) {
    case 'vortex_breakout':
      return maturity >= 5 && maturity <= 15
        ? { winRate: 0.55, rewardRiskRatio: 3, confidenceCoefficient: 1.0 }
        : { winRate: 0.45, rewardRiskRatio: 2.5, confidenceCoefficient: 0.7 };
    case 'stochastic_resonance':
      return { winRate: 0.50, rewardRiskRatio: 4, confidenceCoefficient: 1.2 };
    case 'trend_pullback':
      return { winRate: 0.60, rewardRiskRatio: 2, confidenceCoefficient: 0.8 };
    default:
      return { winRate: 0.50, rewardRiskRatio: 2, confidenceCoefficient: 0.5 };
  }
}

export function getMaxPositionLimit(directionBias: DirectionBias, signalQuality: 'optimal' | 'standard' | 'low'): number {
  if (directionBias === 'strongly_bullish' || directionBias === 'strongly_bearish') {
    if (signalQuality === 'optimal') return 0.50;
    if (signalQuality === 'standard') return 0.30;
    return 0.20;
  }
  if (directionBias === 'cautiously_bullish' || directionBias === 'cautiously_bearish') {
    if (signalQuality === 'optimal') return 0.30;
    if (signalQuality === 'standard') return 0.20;
    return 0.10;
  }
  if (directionBias === 'neutral') return signalQuality === 'optimal' ? 0.20 : 0.10;
  return 0.10;
}

export function calculateInitialAndAddPosition(totalSize: number, verificationStrength: 'full' | 'half'): { initial: number; addOn: number } {
  const initialRatio = verificationStrength === 'full' ? 0.7 : 0.5;
  return { initial: totalSize * initialRatio, addOn: totalSize * (1 - initialRatio) };
}

// =====================
// 7.8 止盈止损
// =====================

export function calculateStopLoss(signalType: SignalType, entryPrice: number, signalDayLow?: number, retestLow?: number): number {
  switch (signalType) {
    case 'vortex_breakout': return entryPrice * 0.98;
    case 'stochastic_resonance': return signalDayLow ? signalDayLow * 0.97 : entryPrice * 0.97;
    case 'trend_pullback': return retestLow ? retestLow * 0.98 : entryPrice * 0.97;
    default: return entryPrice * 0.97;
  }
}

export function calculateMovingStopLoss(position: Position, currentPrice: number): number {
  const pnlPercent = positionPnLPercent(position);
  if (pnlPercent < 10) return position.stopLoss;
  if (pnlPercent >= 10 && pnlPercent < 20) return position.entryPrice;
  if (pnlPercent >= 20 && pnlPercent < 50) return Math.max(position.stopLoss, currentPrice * 0.97 * 0.97);
  return Math.max(position.stopLoss, currentPrice * 0.98 * 0.98);
}

export interface TakeProfitStatus {
  tier1Triggered: boolean;
  tier2Triggered: boolean;
  tier3Triggered: boolean;
  tier4Triggered: boolean;
}

export function checkTakeProfitTrigger(currentStatus: TakeProfitStatus, metrics: {
  mvrvZ: number;
  nupl: number;
  exchangeBalanceTrend: 'up' | 'down';
  whaleNetflowDays: number;
  dci: number;
  weeklyCloseBelowMA20: boolean;
  macroScore: number;
  monthsSinceHalving: number;
}): TakeProfitStatus {
  const newStatus = { ...currentStatus };
  if (!newStatus.tier1Triggered && (metrics.mvrvZ > 5 || metrics.nupl > 0.75)) newStatus.tier1Triggered = true;
  if (!newStatus.tier2Triggered && metrics.exchangeBalanceTrend === 'up' && metrics.whaleNetflowDays >= 3) newStatus.tier2Triggered = true;
  if (!newStatus.tier3Triggered && metrics.dci < 0.55 && metrics.weeklyCloseBelowMA20) newStatus.tier3Triggered = true;
  if (!newStatus.tier4Triggered && (metrics.macroScore <= 3 || metrics.monthsSinceHalving > 18)) newStatus.tier4Triggered = true;
  return newStatus;
}

// =====================
// 执行卡片状态
// =====================

export interface ExecutionCard {
  prediction: Prediction;
  currentSignal: Signal | null;
  signalStatus: 'waiting' | 'triggered' | 'confirmed';
  verification: VerificationResult | null;
  position: Position | null;
  takeProfitStatus: TakeProfitStatus;
  addPositionTiming: AddPositionTiming | null;
  exitReason: string | null;
  cooldownUntil: string | null;
}

export interface ExecutionLog {
  timestamp: string;
  level: 'INFO' | 'SUCCESS' | 'WARNING' | 'ERROR';
  step: string;
  message: string;
  data?: unknown;
}

export function createEmptyExecutionCard(): ExecutionCard {
  return {
    prediction: {
      directionBias: 'neutral', cycleLevel: 'none', huntingMode: 'off', confidence: 0,
      reason: '未运行预测', macroScore: 0, onchainScore: 0, halvingPhase: 'bear_market', rtiScore: 0,
    },
    currentSignal: null,
    signalStatus: 'waiting',
    verification: null,
    position: null,
    takeProfitStatus: { tier1Triggered: false, tier2Triggered: false, tier3Triggered: false, tier4Triggered: false },
    addPositionTiming: null,
    exitReason: null,
    cooldownUntil: null,
  };
}
