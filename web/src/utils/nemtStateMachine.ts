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
 * NEMT四相位状态机模块
 * 实现市场四相位的自动识别和转换管理
 */

import {
  MarketPhase,
  NEMTSignals,
  DCISignal,
  VortexConditions,
  ResonanceConditions,
  PhaseStrategy,
  PHASE_STRATEGIES
} from '../types/nemt';

export interface PhaseHistory {
  timestamp: Date;
  phase: MarketPhase;
  durationCandles: number;
  signals?: Record<string, unknown>;
  price?: number;
}

export interface PhaseTransitionEvent {
  timestamp: Date;
  fromPhase: MarketPhase;
  toPhase: MarketPhase;
  transitionType: string;
  confidence: number;
  triggerSignals: Record<string, unknown>;
  price: number;
}

export interface StateMachineConfig {
  dciTrendThreshold: number;
  dciNoiseThreshold: number;
  vortexConditionsRequired: number;
  vortexMaturityLow: number;
  vortexMaturityHigh: number;
  resonanceConfidenceThreshold: number;
  minPhaseDuration: number;
  historyMaxlen: number;
}

export class NEMTStateMachine {
  private config: StateMachineConfig;
  private currentPhase: MarketPhase = MarketPhase.PHASE_A_NOISE;
  private phaseDuration: number = 0;
  private phaseConfidence: number = 0;
  private phaseHistory: PhaseHistory[] = [];
  private transitionHistory: PhaseTransitionEvent[] = [];
  private onPhaseChange?: (event: PhaseTransitionEvent) => void;
  
  private stats = {
    totalTransitions: 0,
    phaseADuration: 0,
    phaseBDuration: 0,
    phaseCDuration: 0,
    phaseDDuration: 0
  };
  
  constructor(config?: Partial<StateMachineConfig>) {
    this.config = {
      dciTrendThreshold: config?.dciTrendThreshold ?? 0.65,
      dciNoiseThreshold: config?.dciNoiseThreshold ?? 0.55,
      vortexConditionsRequired: config?.vortexConditionsRequired ?? 3,
      vortexMaturityLow: config?.vortexMaturityLow ?? 5,
      vortexMaturityHigh: config?.vortexMaturityHigh ?? 15,
      resonanceConfidenceThreshold: config?.resonanceConfidenceThreshold ?? 0.6,
      minPhaseDuration: config?.minPhaseDuration ?? 3,
      historyMaxlen: config?.historyMaxlen ?? 100
    };
  }
  
  /**
   * 设置相位转换回调
   */
  setOnPhaseChange(callback: (event: PhaseTransitionEvent) => void): void {
    this.onPhaseChange = callback;
  }
  
  /**
   * 更新状态机
   */
  update(signals: NEMTSignals, price: number): { phase: MarketPhase; transition: PhaseTransitionEvent | null } {
    const oldPhase = this.currentPhase;
    this.phaseDuration++;
    
    // 更新统计
    this.updateStats(oldPhase);
    
    // 评估相位转换
    const { newPhase, confidence, trigger } = this.evaluatePhaseTransition(signals);
    
    let transition: PhaseTransitionEvent | null = null;
    
    if (newPhase !== oldPhase && this.phaseDuration >= this.config.minPhaseDuration) {
      // 记录历史
      this.phaseHistory.push({
        timestamp: new Date(),
        phase: oldPhase,
        durationCandles: this.phaseDuration,
        signals: this.signalsToDict(signals),
        price
      });
      
      // 限制历史长度
      if (this.phaseHistory.length > this.config.historyMaxlen) {
        this.phaseHistory.shift();
      }
      
      // 创建转换事件
      transition = {
        timestamp: new Date(),
        fromPhase: oldPhase,
        toPhase: newPhase,
        transitionType: `${oldPhase}->${newPhase}`,
        confidence,
        triggerSignals: trigger,
        price
      };
      
      this.transitionHistory.push(transition);
      this.currentPhase = newPhase;
      this.phaseDuration = 0;
      this.phaseConfidence = confidence;
      this.stats.totalTransitions++;
      
      // 触发回调
      if (this.onPhaseChange) {
        this.onPhaseChange(transition);
      }
    } else {
      this.currentPhase = newPhase;
      this.phaseConfidence = Math.max(this.phaseConfidence, confidence);
    }
    
    return { phase: this.currentPhase, transition };
  }
  
  /**
   * 评估相位转换
   */
  private evaluatePhaseTransition(signals: NEMTSignals): {
    newPhase: MarketPhase;
    confidence: number;
    trigger: Record<string, unknown>;
  } {
    const { dci, vortex, resonance } = signals;
    
    // 优先级1: 随机共振触发 -> 相位C
    if (resonance.isResonance && resonance.confidence >= this.config.resonanceConfidenceThreshold) {
      return {
        newPhase: MarketPhase.PHASE_C_RESONANCE,
        confidence: resonance.confidence,
        trigger: {
          type: 'resonance',
          bullish: resonance.bullish,
          confidence: resonance.confidence
        }
      };
    }
    
    // 优先级2: 涡旋形成 -> 相位B
    if (vortex.isVortex) {
      const conditionsMet = [vortex.bbwNarrow, vortex.volumeUniform, vortex.oiHighFlat, vortex.fundingNeutral]
        .filter(Boolean).length;
      
      if (this.config.vortexMaturityLow <= vortex.maturityScore && vortex.maturityScore <= this.config.vortexMaturityHigh) {
        return {
          newPhase: MarketPhase.PHASE_B_VORTEX,
          confidence: 0.8,
          trigger: {
            type: 'mature_vortex',
            maturity: vortex.maturityScore,
            conditions: conditionsMet
          }
        };
      } else if (vortex.maturityScore < this.config.vortexMaturityLow) {
        return {
          newPhase: MarketPhase.PHASE_B_VORTEX,
          confidence: 0.6,
          trigger: {
            type: 'immature_vortex',
            maturity: vortex.maturityScore,
            conditions: conditionsMet
          }
        };
      }
    }
    
    // 优先级3: 高DCI + 无涡旋 -> 相位D
    if (dci.value > this.config.dciTrendThreshold && !vortex.isVortex) {
      return {
        newPhase: MarketPhase.PHASE_D_TREND,
        confidence: 0.7,
        trigger: {
          type: 'trend',
          direction: dci.direction,
          dci: dci.value
        }
      };
    }
    
    // 优先级4: 低DCI -> 相位A
    if (dci.value < this.config.dciNoiseThreshold) {
      const confidence = Math.max(0.5, 1 - (this.config.dciNoiseThreshold - dci.value) / 0.1);
      return {
        newPhase: MarketPhase.PHASE_A_NOISE,
        confidence,
        trigger: { type: 'high_noise', dci: dci.value }
      };
    }
    
    // 过渡期 -> 相位A
    return {
      newPhase: MarketPhase.PHASE_A_NOISE,
      confidence: 0.5,
      trigger: { type: 'transition' }
    };
  }
  
  /**
   * 更新统计数据
   */
  private updateStats(phase: MarketPhase): void {
    const phaseMap: Record<MarketPhase, keyof typeof this.stats> = {
      [MarketPhase.PHASE_A_NOISE]: 'phaseADuration',
      [MarketPhase.PHASE_B_VORTEX]: 'phaseBDuration',
      [MarketPhase.PHASE_C_RESONANCE]: 'phaseCDuration',
      [MarketPhase.PHASE_D_TREND]: 'phaseDDuration'
    };
    
    const key = phaseMap[phase];
    if (key && key in this.stats) {
      (this.stats as Record<string, number>)[key]++;
    }
  }
  
  /**
   * 信号转字典
   */
  private signalsToDict(signals: NEMTSignals): Record<string, unknown> {
    return {
      dciValue: signals.dci.value,
      dciState: signals.dci.noiseState,
      vortexIsForm: signals.vortex.isVortex,
      vortexMaturity: signals.vortex.maturityScore,
      resonanceTriggered: signals.resonance.isResonance,
      resonanceConfidence: signals.resonance.confidence,
      spectralWidth: signals.spectralWidth
    };
  }
  
  // =====================
  // Getters
  // =====================
  
  getPhase(): MarketPhase {
    return this.currentPhase;
  }
  
  getPhaseDuration(): number {
    return this.phaseDuration;
  }
  
  getPhaseConfidence(): number {
    return this.phaseConfidence;
  }
  
  getCurrentStrategy(): PhaseStrategy {
    return PHASE_STRATEGIES[this.currentPhase];
  }
  
  getPhaseDistribution(): Record<string, number> {
    const total = this.stats.phaseADuration + this.stats.phaseBDuration + 
                  this.stats.phaseCDuration + this.stats.phaseDDuration;
    
    if (total === 0) return { A: 0, B: 0, C: 0, D: 0 };
    
    return {
      A: this.stats.phaseADuration / total,
      B: this.stats.phaseBDuration / total,
      C: this.stats.phaseCDuration / total,
      D: this.stats.phaseDDuration / total
    };
  }
  
  getStateSummary(): Record<string, unknown> {
    const strategy = this.getCurrentStrategy();
    
    return {
      currentPhase: this.currentPhase,
      phaseName: strategy.name,
      phaseDuration: this.phaseDuration,
      phaseConfidence: `${(this.phaseConfidence * 100).toFixed(1)}%`,
      totalTransitions: this.stats.totalTransitions,
      phaseDistribution: this.getPhaseDistribution(),
      maxPosition: `${(strategy.maxPosition * 100).toFixed(0)}%`,
      singleRisk: `${(strategy.singleRisk * 100).toFixed(1)}%`,
      leverage: `${strategy.leverageAllowed}x`,
      strategy: strategy.strategyText,
      focus: strategy.focusText,
      avoid: strategy.avoidText
    };
  }
  
  getRecentTransitions(n: number = 5): Record<string, unknown>[] {
    const recent = this.transitionHistory.slice(-n);
    
    return recent.map(t => ({
      timestamp: t.timestamp.toISOString(),
      from: t.fromPhase,
      to: t.toPhase,
      price: t.price,
      confidence: `${(t.confidence * 100).toFixed(1)}%`
    })).reverse();
  }
  
  /**
   * 重置状态机
   */
  reset(): void {
    this.currentPhase = MarketPhase.PHASE_A_NOISE;
    this.phaseDuration = 0;
    this.phaseConfidence = 0;
    this.phaseHistory = [];
    this.transitionHistory = [];
    this.stats = {
      totalTransitions: 0,
      phaseADuration: 0,
      phaseBDuration: 0,
      phaseCDuration: 0,
      phaseDDuration: 0
    };
  }
}

/**
 * 创建演示用状态机
 */
export function createDemoStateMachine(): NEMTStateMachine {
  return new NEMTStateMachine({
    dciTrendThreshold: 0.65,
    dciNoiseThreshold: 0.55,
    vortexConditionsRequired: 3,
    vortexMaturityLow: 5,
    vortexMaturityHigh: 15,
    resonanceConfidenceThreshold: 0.6,
    minPhaseDuration: 3
  });
}
