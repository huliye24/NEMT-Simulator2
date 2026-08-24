/**
 * Copyright 2026 NEMT Lab
 *
 * NEMT Alpha Model
 * 借鉴 vnpy.alpha model
 *
 * 功能：
 * - ML 模型训练
 * - 模型推理
 * - 模型管理
 */

// ============================================
// 模型类型
// ============================================

export type ModelType = 'lasso' | 'ridge' | 'random_forest' | 'xgboost' | 'lightgbm' | 'mlp';

export interface ModelConfig {
  type: ModelType;
  hyperparameters: Record<string, unknown>;
}

// ============================================
// 预测结果
// ============================================

export interface PredictionResult {
  /** 预测值 */
  value: number;
  /** 置信度 */
  confidence: number;
  /** 模型名称 */
  modelName: string;
  /** 时间戳 */
  timestamp: number;
}

// ============================================
// BaseModel
// ============================================

export abstract class BaseModel {
  abstract modelType: ModelType;
  abstract modelName: string;

  protected isTrained: boolean = false;
  protected featureNames: string[] = [];

  abstract train(X: number[][], y: number[]): void;
  abstract predict(X: number[]): PredictionResult;

  abstract save(path: string): void;
  abstract load(path: string): void;

  getFeatureNames(): string[] {
    return this.featureNames;
  }

  getIsTrained(): boolean {
    return this.isTrained;
  }
}

// ============================================
// LinearRegression
// ============================================

export class LinearRegression extends BaseModel {
  modelType: ModelType = 'lasso';
  modelName = 'LinearRegression';

  private weights: number[] = [];
  private bias: number = 0;

  train(X: number[][], y: number[]): void {
    const n = X.length;
    const m = X[0].length;

    // 简化的线性回归 (梯度下降)
    const learningRate = 0.01;
    const iterations = 1000;

    this.weights = new Array(m).fill(0);
    this.bias = 0;

    for (let iter = 0; iter < iterations; iter++) {
      const predictions = X.map((x) =>
        x.reduce((sum, xi, i) => sum + xi * this.weights[i], 0) + this.bias
      );

      const errors = predictions.map((pred, i) => pred - y[i]);

      // 更新权重
      for (let j = 0; j < m; j++) {
        const gradient = errors.reduce((sum, err, i) => sum + err * X[i][j], 0) / n;
        this.weights[j] -= learningRate * gradient;
      }

      // 更新偏置
      const biasGradient = errors.reduce((sum, err) => sum + err, 0) / n;
      this.bias -= learningRate * biasGradient;
    }

    this.isTrained = true;
    this.featureNames = X[0].map((_, i) => `feature_${i}`);
  }

  predict(X: number[]): PredictionResult {
    if (!this.isTrained) {
      throw new Error('Model not trained');
    }

    const value = X.reduce((sum, xi, i) => sum + xi * this.weights[i], 0) + this.bias;

    // 计算残差作为置信度
    const residuals = X.map((x, i) => {
      const pred = x.reduce((s, xi, j) => s + xi * this.weights[j], 0) + this.bias;
      return Math.abs(pred - 0); // 简化
    });
    const avgResidual = residuals.reduce((a, b) => a + b, 0) / residuals.length;
    const confidence = Math.max(0, Math.min(1, 1 - avgResidual / 100));

    return {
      value,
      confidence,
      modelName: this.modelName,
      timestamp: Date.now(),
    };
  }

  save(path: string): void {
    const data = { weights: this.weights, bias: this.bias };
    console.log(`[Model] Saving to ${path}:`, data);
  }

  load(path: string): void {
    console.log(`[Model] Loading from ${path}`);
    // 实际应该从文件加载
  }
}

// ============================================
// RidgeRegression
// ============================================

export class RidgeRegression extends BaseModel {
  modelType: ModelType = 'ridge';
  modelName = 'RidgeRegression';

  private weights: number[] = [];
  private bias: number = 0;
  private alpha: number = 1.0;

  train(X: number[][], y: number[]): void {
    this.alpha = (this as any).hyperparameters?.alpha || 1.0;
    const n = X.length;
    const m = X[0].length;

    // 带 L2 正则化的梯度下降
    const learningRate = 0.01;
    const iterations = 1000;

    this.weights = new Array(m).fill(0);
    this.bias = 0;

    for (let iter = 0; iter < iterations; iter++) {
      const predictions = X.map((x) =>
        x.reduce((sum, xi, i) => sum + xi * this.weights[i], 0) + this.bias
      );

      const errors = predictions.map((pred, i) => pred - y[i]);

      for (let j = 0; j < m; j++) {
        const gradient = errors.reduce((sum, err, i) => sum + err * X[i][j], 0) / n;
        const regGradient = this.alpha * this.weights[j];
        this.weights[j] -= learningRate * (gradient + regGradient);
      }

      const biasGradient = errors.reduce((sum, err) => sum + err, 0) / n;
      this.bias -= learningRate * biasGradient;
    }

    this.isTrained = true;
    this.featureNames = X[0].map((_, i) => `feature_${i}`);
  }

  predict(X: number[]): PredictionResult {
    if (!this.isTrained) {
      throw new Error('Model not trained');
    }

    const value = X.reduce((sum, xi, i) => sum + xi * this.weights[i], 0) + this.bias;

    return {
      value,
      confidence: 0.7,
      modelName: this.modelName,
      timestamp: Date.now(),
    };
  }

  save(path: string): void {
    console.log(`[Model] Saving to ${path}`);
  }

  load(path: string): void {
    console.log(`[Model] Loading from ${path}`);
  }
}

// ============================================
// RandomForest (简化版)
// ============================================

export class RandomForest extends BaseModel {
  modelType: ModelType = 'random_forest';
  modelName = 'RandomForest';

  private trees: Array<{ weights: number[]; bias: number }> = [];
  private nTrees: number = 10;

  train(X: number[][], y: number[]): void {
    this.nTrees = (this as any).hyperparameters?.nTrees || 10;
    this.trees = [];

    // 训练多棵简单的决策树 (线性模型模拟)
    for (let i = 0; i < this.nTrees; i++) {
      // 随机采样
      const indices = this.randomIndices(X.length, X.length * 0.8);
      const XSample = indices.map((idx) => X[idx]);
      const ySample = indices.map((idx) => y[idx]);

      // 训练简单的线性模型
      const model = new LinearRegression();
      model.train(XSample, ySample);

      this.trees.push({
        weights: (model as any).weights || [],
        bias: (model as any).bias || 0,
      });
    }

    this.isTrained = true;
    this.featureNames = X[0].map((_, i) => `feature_${i}`);
  }

  predict(X: number[]): PredictionResult {
    if (!this.isTrained) {
      throw new Error('Model not trained');
    }

    // 集成预测
    const predictions = this.trees.map((tree) =>
      X.reduce((sum, xi, i) => sum + xi * tree.weights[i], 0) + tree.bias
    );

    // 取中位数
    predictions.sort((a, b) => a - b);
    const value = predictions[Math.floor(predictions.length / 2)];

    return {
      value,
      confidence: 0.8,
      modelName: this.modelName,
      timestamp: Date.now(),
    };
  }

  save(path: string): void {
    console.log(`[Model] Saving to ${path}`);
  }

  load(path: string): void {
    console.log(`[Model] Loading from ${path}`);
  }

  private randomIndices(n: number, m: number): number[] {
    const indices: number[] = [];
    for (let i = 0; i < m; i++) {
      indices.push(Math.floor(Math.random() * n));
    }
    return indices;
  }
}

// ============================================
// MLP (多层感知机, 简化版)
// ============================================

export class MLP extends BaseModel {
  modelType: ModelType = 'mlp';
  modelName = 'MLP';

  private layers: number[] = [];
  private weights: number[][][] = [];
  private biases: number[][] = [];

  constructor(config?: { layers?: number[] }) {
    super();
    this.layers = config?.layers || [10, 5, 1];
  }

  train(X: number[][], y: number[]): void {
    const inputSize = X[0].length;
    const hiddenSize = this.layers[1] || 10;
    const outputSize = 1;

    // 初始化权重
    this.weights = [
      this.randomMatrix(inputSize, hiddenSize),
      this.randomMatrix(hiddenSize, outputSize),
    ];
    this.biases = [
      new Array(hiddenSize).fill(0),
      new Array(outputSize).fill(0),
    ];

    // 简化的训练过程
    const learningRate = 0.01;
    const iterations = 500;

    for (let iter = 0; iter < iterations; iter++) {
      for (let i = 0; i < X.length; i++) {
        // 前向传播
        const hidden = this.relu(
          X[i].map((x, j) =>
            X[i].reduce((s, xi, k) => s + xi * this.weights[0][k][j], 0) + this.biases[0][j]
          )
        );
        const output = hidden.reduce(
          (s, h, j) => s + h * this.weights[1][j][0],
          0
        ) + this.biases[1][0];

        // 计算误差
        const error = output - y[i];

        // 更新权重 (简化)
        for (let j = 0; j < hiddenSize; j++) {
          for (let k = 0; k < inputSize; k++) {
            this.weights[0][k][j] -= learningRate * error * X[i][k] * this.reluDerivative(hidden[j]);
          }
          this.biases[0][j] -= learningRate * error * this.reluDerivative(hidden[j]);
        }
        for (let k = 0; k < hiddenSize; k++) {
          this.weights[1][k][0] -= learningRate * error * hidden[k];
        }
        this.biases[1][0] -= learningRate * error;
      }
    }

    this.isTrained = true;
    this.featureNames = X[0].map((_, i) => `feature_${i}`);
  }

  predict(X: number[]): PredictionResult {
    if (!this.isTrained) {
      throw new Error('Model not trained');
    }

    // 前向传播
    const hidden = this.relu(
      X.map((_, j) =>
        X.reduce((s, xi, k) => s + xi * this.weights[0][k][j], 0) + this.biases[0][j]
      )
    );
    const value =
      hidden.reduce((s, h, j) => s + h * this.weights[1][j][0], 0) + this.biases[1][0];

    return {
      value,
      confidence: 0.75,
      modelName: this.modelName,
      timestamp: Date.now(),
    };
  }

  save(path: string): void {
    console.log(`[Model] Saving to ${path}`);
  }

  load(path: string): void {
    console.log(`[Model] Loading from ${path}`);
  }

  private randomMatrix(rows: number, cols: number): number[][] {
    const matrix: number[][] = [];
    for (let i = 0; i < rows; i++) {
      matrix.push([]);
      for (let j = 0; j < cols; j++) {
        matrix[i].push((Math.random() - 0.5) * 2);
      }
    }
    return matrix;
  }

  private relu(x: number): number {
    return Math.max(0, x);
  }

  private reluDerivative(x: number): number {
    return x > 0 ? 1 : 0;
  }
}

// ============================================
// 模型工厂
// ============================================

export function createModel(type: ModelType, config?: Record<string, unknown>): BaseModel {
  switch (type) {
    case 'lasso':
      return new LinearRegression();
    case 'ridge':
      return new RidgeRegression();
    case 'random_forest':
      return new RandomForest();
    case 'mlp':
      return new MLP(config?.layers as any);
    default:
      return new LinearRegression();
  }
}

// ============================================
// 模型管理器
// ============================================

export class ModelManager {
  private models: Map<string, BaseModel> = new Map();

  register(name: string, model: BaseModel): void {
    this.models.set(name, model);
    console.log(`[ModelManager] Registered: ${name} (${model.modelType})`);
  }

  get(name: string): BaseModel | undefined {
    return this.models.get(name);
  }

  list(): string[] {
    return Array.from(this.models.keys());
  }

  async train(
    name: string,
    type: ModelType,
    X: number[][],
    y: number[],
    config?: Record<string, unknown>
  ): Promise<void> {
    const model = createModel(type, config);
    model.train(X, y);
    this.register(name, model);
  }
}
