/**
 * NEMT 执行框架完整服务
 * 整合第七章所有逻辑：预测→信号→验证→加仓→止盈止损
 */

import {
  ExecutionCard,
  ExecutionLog,
  Position,
  Signal,
  MacroScores,
  runPrediction,
  checkSignals,
  SignalConditions,
  verifyVortexBreakout,
  VerificationInput,
  checkAddPositionTiming,
  canAddPosition,
  calculateNewStopLoss,
  checkFeedbackLoop,
  calculateKellyPositionSize,
  getKellyParamsForSignalType,
  getMaxPositionLimit,
  calculateInitialAndAddPosition,
  calculateStopLoss,
  calculateMovingStopLoss,
  checkTakeProfitTrigger,
  createEmptyExecutionCard,
  VerificationResult,
} from './executionFramework';
import { MarketPhase } from '../types/nemt';

// =====================
// 执行框架主类
// =====================

export class ExecutionFramework {
  private card: ExecutionCard;
  private logs: ExecutionLog[] = [];
  private cooldownHours: number = 24;
  
  constructor() {
    this.card = createEmptyExecutionCard();
  }
  
  runFullFramework(
    dci: number,
    vortexMaturity: number,
    marketPhase: MarketPhase,
    spectralWidth: number,
    noiseLevel: number,
    macroScores: MacroScores,
    prices: number[]
  ): ExecutionCard {
    this.clearLogs();
    
    // Step 1: 预测
    this.log('INFO', 'PREDICTION', '开始预测步骤...');
    const prediction = runPrediction(macroScores);
    this.card.prediction = prediction;
    this.log('SUCCESS', 'PREDICTION', prediction.reason);
    
    // Step 2: 信号
    this.log('INFO', 'SIGNAL', '检查入场信号...');
    const signalConditions: SignalConditions = {
      dci,
      vortexMaturity,
      phase: marketPhase,
      spectralWidth,
      priceMomentum: this.calculateMomentum(prices),
      noiseLevel,
      trendMA20Distance: 0.01,
      trendMA50Distance: 0.02,
    };
    
    const signal = checkSignals(signalConditions, prediction.huntingMode);
    this.card.currentSignal = signal;
    
    if (signal.type === 'none') {
      this.log('INFO', 'SIGNAL', signal.reason);
      this.card.signalStatus = 'waiting';
    } else {
      this.log('SUCCESS', 'SIGNAL', `${signal.type} - ${signal.reason}`);
      this.card.signalStatus = 'triggered';
    }
    
    // Step 3: 验证（如果信号触发）
    if (signal.type !== 'none' && prediction.huntingMode === 'on') {
      this.log('INFO', 'VERIFICATION', '验证信号可靠性...');
      const verificationInput = this.buildVerificationInput(prices, signal);
      const verification = this.verifySignal(signal, verificationInput);
      this.card.verification = verification;
      
      if (verification.passed) {
        this.log('SUCCESS', 'VERIFICATION', 
          `验证${verification.confidence === 'full' ? '通过' : '谨慎通过'}，通过项: ${verification.passedCount}/${verification.totalWeight}`);
      } else {
        this.log('WARNING', 'VERIFICATION', '验证失败，放弃本次信号');
      }
    }
    
    // Step 4: 持仓管理
    if (this.card.position) {
      this.log('INFO', 'POSITION', '检查持仓状态...');
      this.updatePosition(prices);
      
      const addTiming = checkAddPositionTiming(this.card.position, {
        price: prices[prices.length - 1],
        maPullbackVolume: 0.6,
        dciPullbackRecovered: true,
        higherTfBreakout: false,
        monthMVRV: 3.5,
      });
      
      if (addTiming) {
        this.card.addPositionTiming = addTiming;
        this.log('INFO', 'ADD_POSITION', `检测到加仓时机: ${addTiming}`);
      }
      
      this.checkStopLossAndTakeProfit(prices);
      
      const feedbackChecks = checkFeedbackLoop(this.card.position, {
        pnlPercent: this.card.position.pnlPercent,
        priceNearATH: false,
        dci,
        macroScore: macroScores.macroScore,
        monthsSinceHalving: macroScores.monthsSinceHalving,
      });
      
      feedbackChecks.forEach(check => {
        this.log('INFO', 'FEEDBACK', `${check.event}: ${check.reassessContent}`);
      });
    }
    
    this.log('SUCCESS', 'COMPLETE', '执行框架运行完成');
    return this.card;
  }
  
  executeEntry(price: number, totalCapital: number, verificationConfidence: 'full' | 'half'): Position | null {
    const signal = this.card.currentSignal;
    if (!signal || signal.type === 'none') {
      this.log('ERROR', 'ENTRY', '无有效信号，无法入场');
      return null;
    }
    
    if (!this.card.verification?.passed) {
      this.log('ERROR', 'ENTRY', '信号未通过验证，无法入场');
      return null;
    }
    
    if (this.card.cooldownUntil) {
      const cooldownEnd = new Date(this.card.cooldownUntil);
      if (new Date() < cooldownEnd) {
        this.log('WARNING', 'ENTRY', '冷静期中，禁止入场');
        return null;
      }
    }
    
    this.log('INFO', 'ENTRY', '开始计算仓位...');
    
    const kellyParams = getKellyParamsForSignalType(signal.type, signal.maturity);
    const kellySize = calculateKellyPositionSize(kellyParams);
    const maxLimit = getMaxPositionLimit(this.card.prediction.directionBias, verificationConfidence === 'full' ? 'optimal' : 'standard');
    const totalSize = Math.min(kellySize, maxLimit);
    const { initial } = calculateInitialAndAddPosition(totalSize, verificationConfidence);
    
    const positionValue = totalCapital * initial;
    const size = positionValue / price;
    const stopLoss = calculateStopLoss(signal.type, price);
    const stopLossPercent = (price - stopLoss) / price;
    
    const position: Position = {
      entryPrice: price,
      currentPrice: price,
      size,
      unrealizedPnL: 0,
      pnlPercent: 0,
      stopLoss,
      positionPhase: 1,
      entryTime: new Date().toISOString(),
    };
    
    this.card.position = position;
    this.card.signalStatus = 'confirmed';
    
    this.log('SUCCESS', 'ENTRY', 
      `入场成功！买入 ${size.toFixed(4)} @ $${price.toFixed(2)}，` +
      `仓位 ${(initial * 100).toFixed(1)}%，止损 ${(stopLossPercent * 100).toFixed(1)}%`);
    
    return position;
  }
  
  executeAddPosition(price: number, addOnSize: number, retestLow: number): boolean {
    const position = this.card.position;
    if (!position) {
      this.log('ERROR', 'ADD_ENTRY', '无持仓，无法加仓');
      return false;
    }
    
    const canAdd = canAddPosition(position, 0.65, 1.5, 2);
    if (!canAdd.canAdd) {
      this.log('WARNING', 'ADD_ENTRY', canAdd.reason);
      return false;
    }
    
    const newStopLoss = calculateNewStopLoss(position, price, retestLow);
    
    const totalSize = position.size + addOnSize;
    const avgPrice = (position.entryPrice * position.size + price * addOnSize) / totalSize;
    
    position.entryPrice = avgPrice;
    position.size = totalSize;
    position.stopLoss = newStopLoss;
    position.positionPhase++;
    
    this.log('SUCCESS', 'ADD_ENTRY', 
      `加仓成功！追加 ${addOnSize.toFixed(4)} @ $${price.toFixed(2)}，` +
      `新均价 $${avgPrice.toFixed(2)}，新止损 $${newStopLoss.toFixed(2)}`);
    
    return true;
  }
  
  executeExit(reason: string): { pnl: number; pnlPercent: number } | null {
    const position = this.card.position;
    if (!position) {
      this.log('ERROR', 'EXIT', '无持仓，无法离场');
      return null;
    }
    
    const pnl = position.unrealizedPnL;
    const pnlPercent = position.pnlPercent;
    
    this.log('SUCCESS', 'EXIT', 
      `离场完成！${reason}，盈亏 $${pnl.toFixed(2)} (${pnlPercent.toFixed(2)}%)`);
    
    const cooldownEnd = new Date();
    cooldownEnd.setHours(cooldownEnd.getHours() + this.cooldownHours);
    this.card.cooldownUntil = cooldownEnd.toISOString();
    
    this.card.exitReason = reason;
    this.card.position = null;
    this.card.takeProfitStatus = { tier1Triggered: false, tier2Triggered: false, tier3Triggered: false, tier4Triggered: false };
    
    return { pnl, pnlPercent };
  }
  
  getCard(): ExecutionCard { return this.card; }
  getLogs(): ExecutionLog[] { return this.logs; }
  
  reset(): void {
    this.card = createEmptyExecutionCard();
    this.clearLogs();
  }
  
  private clearLogs(): void { this.logs = []; }
  
  private log(level: ExecutionLog['level'], step: string, message: string, data?: unknown): void {
    const entry: ExecutionLog = { timestamp: new Date().toISOString(), level, step, message, data };
    this.logs.push(entry);
    console.log(`[${level}] [${step}] ${message}`);
  }
  
  private calculateMomentum(prices: number[]): number {
    if (prices.length < 10) return 0;
    const recent = prices.slice(-5);
    const older = prices.slice(-10, -5);
    if (older.length === 0) return 0;
    const recentAvg = recent.reduce((a, b) => a + b, 0) / recent.length;
    const olderAvg = older.reduce((a, b) => a + b, 0) / older.length;
    return (recentAvg - olderAvg) / olderAvg;
  }
  
  private buildVerificationInput(prices: number[], signal: Signal): VerificationInput {
    const currentPrice = prices[prices.length - 1];
    const entryPrice = signal.price || currentPrice;
    const priceChangePercent = ((currentPrice - entryPrice) / entryPrice) * 100;
    
    return {
      volumeConfirm: true,
      closePriceConfirm: priceChangePercent > 0.5,
      oiConfirm: true,
      timeConfirm: true,
      fundingRateConfirm: true,
      onchainConfirm: false,
      priceChangePercent,
      volumeRatio: 1.8,
    };
  }
  
  private verifySignal(signal: Signal, input: VerificationInput): VerificationResult {
    if (signal.type === 'vortex_breakout') {
      return verifyVortexBreakout(input);
    }
    // 其他信号类型简化为失败
    return { passed: false, confidence: 'failed', items: [], passedCount: 0, totalWeight: 0 };
  }
  
  private updatePosition(prices: number[]): void {
    const position = this.card.position;
    if (!position) return;
    
    const currentPrice = prices[prices.length - 1];
    position.currentPrice = currentPrice;
    position.unrealizedPnL = (currentPrice - position.entryPrice) * position.size;
    position.pnlPercent = ((currentPrice - position.entryPrice) / position.entryPrice) * 100;
    position.stopLoss = calculateMovingStopLoss(position, currentPrice);
  }
  
  private checkStopLossAndTakeProfit(prices: number[]): void {
    const position = this.card.position;
    if (!position) return;
    
    const currentPrice = prices[prices.length - 1];
    
    if (currentPrice <= position.stopLoss) {
      this.log('WARNING', 'STOP_LOSS', `价格触及止损位 $${position.stopLoss.toFixed(2)}`);
      this.executeExit('触发止损');
      return;
    }
    
    const tpStatus = checkTakeProfitTrigger(this.card.takeProfitStatus, {
      mvrvZ: 4.5,
      nupl: 0.65,
      exchangeBalanceTrend: 'down',
      whaleNetflowDays: 2,
      dci: 0.68,
      weeklyCloseBelowMA20: false,
      macroScore: 7,
      monthsSinceHalving: 10,
    });
    
    if (tpStatus.tier1Triggered && !this.card.takeProfitStatus.tier1Triggered) {
      this.log('INFO', 'TAKE_PROFIT', '第一批次止盈触发 (30%)');
    }
    if (tpStatus.tier2Triggered && !this.card.takeProfitStatus.tier2Triggered) {
      this.log('INFO', 'TAKE_PROFIT', '第二批次止盈触发 (30%)');
    }
    if (tpStatus.tier3Triggered && !this.card.takeProfitStatus.tier3Triggered) {
      this.log('INFO', 'TAKE_PROFIT', '第三批次止盈触发 (30%)');
    }
    if (tpStatus.tier4Triggered && !this.card.takeProfitStatus.tier4Triggered) {
      this.log('INFO', 'TAKE_PROFIT', '第四批次止盈触发 (全部)');
    }
    
    this.card.takeProfitStatus = tpStatus;
  }
}

export function createExecutionFramework(): ExecutionFramework {
  return new ExecutionFramework();
}

export function quickMarketAssessment(
  dci: number,
  vortexMaturity: number,
  marketPhase: MarketPhase,
  spectralWidth: number,
  noiseLevel: number,
  macroScore: number,
  onchainScore: number
): { recommendation: 'long' | 'short' | 'watch'; reason: string; positionSize: number } {
  const scores: MacroScores = {
    macroScore,
    onchainScore,
    halvingPhase: 'main_rise',
    monthsSinceHalving: 10,
    rtiScore: 5,
  };
  
  const prediction = runPrediction(scores);
  
  const signalConditions: SignalConditions = {
    dci,
    vortexMaturity,
    phase: marketPhase,
    spectralWidth,
    priceMomentum: 0.02,
    noiseLevel,
    trendMA20Distance: 0.01,
    trendMA50Distance: 0.02,
  };
  
  const signal = checkSignals(signalConditions, prediction.huntingMode);
  
  let recommendation: 'long' | 'short' | 'watch' = 'watch';
  let reason = '无有效信号';
  let positionSize = 0;
  
  if (signal.type !== 'none' && prediction.huntingMode === 'on') {
    if (prediction.directionBias.includes('bullish')) {
      recommendation = 'long';
      reason = signal.reason;
      const params = getKellyParamsForSignalType(signal.type, signal.maturity);
      positionSize = calculateKellyPositionSize(params) * prediction.confidence;
      positionSize = Math.min(positionSize, getMaxPositionLimit(prediction.directionBias, 'optimal'));
    } else if (prediction.directionBias.includes('bearish')) {
      recommendation = 'short';
      reason = signal.reason;
      positionSize = 0.2;
    }
  }
  
  return { recommendation, reason, positionSize: Math.round(positionSize * 100) };
}
