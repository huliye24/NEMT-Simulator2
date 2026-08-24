/**
 * Copyright 2026 NEMT Lab
 *
 * NEMT Alpha Strategy
 * 基于 ML 信号预测的量化交易策略
 */

import { BaseModel, PredictionResult } from '../model/model';

// ============================================
// 策略信号
// ============================================

export interface AlphaSignal {
  /** 信号方向: 1=做多, -1=做空, 0=观望 */
  direction: number;
  /** 置信度 */
  confidence: number;
  /** 预测值 */
  prediction: number;
  /** 模型名称 */
  modelName: string;
  /** 时间戳 */
  timestamp: number;
}

// ============================================
// Alpha Strategy
// ============================================

export class AlphaStrategy {
  private model: BaseModel;
  private symbol: string;
  private threshold: number;

  constructor(model: BaseModel, symbol: string, threshold: number = 0.01) {
    this.model = model;
    this.symbol = symbol;
    this.threshold = threshold;
  }

  /**
   * 生成信号
   */
  generateSignal(features: number[]): AlphaSignal {
    const prediction = this.model.predict(features);

    let direction = 0;
    let confidence = prediction.confidence;

    if (prediction.value > this.threshold) {
      direction = 1; // 做多
      confidence = Math.min(1, confidence + 0.1);
    } else if (prediction.value < -this.threshold) {
      direction = -1; // 做空
      confidence = Math.min(1, confidence + 0.1);
    }

    return {
      direction,
      confidence,
      prediction: prediction.value,
      modelName: this.model.modelName,
      timestamp: Date.now(),
    };
  }

  /**
   * 批量生成信号
   */
  generateSignals(featureMatrix: number[][]): AlphaSignal[] {
    return featureMatrix.map((features) => this.generateSignal(features));
  }
}

// ============================================
// 多因子策略
// ============================================

export class MultiFactorStrategy {
  private strategies: AlphaStrategy[];
  private weights: number[];

  constructor(strategies: AlphaStrategy[], weights?: number[]) {
    this.strategies = strategies;
    this.weights = weights || strategies.map(() => 1 / strategies.length);

    if (this.weights.length !== this.strategies.length) {
      throw new Error('Weights length must match strategies length');
    }
  }

  /**
   * 生成综合信号
   */
  generateSignal(featureMatrix: number[][]): {
    direction: number;
    confidence: number;
    predictions: { model: string; value: number; weight: number }[];
  } {
    let weightedDirection = 0;
    let totalConfidence = 0;

    const predictions: { model: string; value: number; weight: number }[] = [];

    for (let i = 0; i < this.strategies.length; i++) {
      const signal = this.strategies[i].generateSignal(featureMatrix[i]);
      weightedDirection += signal.direction * this.weights[i];
      totalConfidence += signal.confidence * this.weights[i];

      predictions.push({
        model: signal.modelName,
        value: signal.prediction,
        weight: this.weights[i],
      });
    }

    const direction = weightedDirection > 0.5 ? 1 : weightedDirection < -0.5 ? -1 : 0;
    const confidence = totalConfidence / this.strategies.length;

    return { direction, confidence, predictions };
  }
}
