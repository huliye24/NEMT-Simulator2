/**
 * Copyright 2026 NEMT Lab
 *
 * NEMT Strategy Optimizer
 * 借鉴 QuantConnect Lean Optimizer
 *
 * 功能：
 * - 参数网格搜索
 * - 穷举搜索
 * - 遗传算法优化
 * - 并行优化
 */

import type { BacktestConfig, BacktestResult } from '../backtest/backtestEngine';
import type { IStrategy } from '../interfaces/IStrategy';

// ============================================
// 优化目标
// ============================================

export type OptimizationObjective =
  | 'sharpe_ratio'
  | 'sortino_ratio'
  | 'total_return'
  | 'profit_factor'
  | 'win_rate'
  | 'max_drawdown'
  | 'calmar_ratio';

export type OptimizationMode = 'maximize' | 'minimize';

// ============================================
// 参数空间
// ============================================

export interface ParameterSpace {
  name: string;
  min: number;
  max: number;
  step: number;
}

export interface OptimizationTarget {
  objective: OptimizationObjective;
  targetValue?: number;
  constraint?: {
    objective: OptimizationObjective;
    operator: '>' | '<' | '>=' | '<=';
    value: number;
  };
}

// ============================================
// 优化结果
// ============================================

export interface OptimizationResult {
  /** 最佳参数组合 */
  bestParams: Record<string, number>;
  /** 最佳指标 */
  bestMetrics: BacktestMetrics;
  /** 最佳回测结果 */
  bestResult: BacktestResult;
  /** 所有结果 */
  allResults: Array<{
    params: Record<string, number>;
    metrics: BacktestMetrics;
    result: BacktestResult;
  }>;
  /** 总运行次数 */
  totalRuns: number;
  /** 运行时间 */
  runtime: number;
}

export interface BacktestMetrics {
  totalReturn: number;
  sharpeRatio: number;
  sortinoRatio: number;
  maxDrawdown: number;
  winRate: number;
  profitFactor: number;
  calmarRatio: number;
}

// ============================================
// 优化器基类
// ============================================

export abstract class BaseOptimizer {
  protected strategy: IStrategy;
  protected parameterSpaces: ParameterSpace[];
  protected target: OptimizationTarget;
  protected maxRuns: number;
  protected onProgress?: (progress: number, current: number, total: number) => void;

  constructor(
    strategy: IStrategy,
    parameterSpaces: ParameterSpace[],
    target: OptimizationTarget,
    maxRuns: number = 1000
  ) {
    this.strategy = strategy;
    this.parameterSpaces = parameterSpaces;
    this.target = target;
    this.maxRuns = maxRuns;
  }

  /** 设置进度回调 */
  setProgressCallback(callback: (progress: number, current: number, total: number) => void): void {
    this.onProgress = callback;
  }

  /** 抽象优化方法 */
  abstract optimize(
    runBacktest: (params: Record<string, number>) => Promise<BacktestResult>
  ): Promise<OptimizationResult>;

  /** 计算参数组合数 */
  protected calculateTotalRuns(): number {
    let total = 1;
    for (const space of this.parameterSpaces) {
      const steps = Math.floor((space.max - space.min) / space.step) + 1;
      total *= steps;
    }
    return Math.min(total, this.maxRuns);
  }

  /** 获取目标指标值 */
  protected getObjectiveValue(metrics: BacktestMetrics): number {
    switch (this.target.objective) {
      case 'sharpe_ratio':
        return metrics.sharpeRatio;
      case 'sortino_ratio':
        return metrics.sortinoRatio;
      case 'total_return':
        return metrics.totalReturn;
      case 'profit_factor':
        return metrics.profitFactor;
      case 'win_rate':
        return metrics.winRate;
      case 'max_drawdown':
        return metrics.maxDrawdown;
      case 'calmar_ratio':
        return metrics.calmarRatio;
      default:
        return 0;
    }
  }

  /** 检查约束 */
  protected checkConstraints(metrics: BacktestMetrics): boolean {
    if (!this.target.constraint) return true;

    const value = this.getObjectiveValue({
      ...metrics,
      [this.target.constraint.objective]: this.getConstraintValue(this.target.constraint, metrics),
    });

    const { operator, value: threshold } = this.target.constraint;

    switch (operator) {
      case '>':
        return value > threshold;
      case '<':
        return value < threshold;
      case '>=':
        return value >= threshold;
      case '<=':
        return value <= threshold;
      default:
        return true;
    }
  }

  private getConstraintValue(
    constraint: { objective: OptimizationObjective; value: number },
    metrics: BacktestMetrics
  ): number {
    switch (constraint.objective) {
      case 'sharpe_ratio':
        return metrics.sharpeRatio;
      case 'sortino_ratio':
        return metrics.sortinoRatio;
      case 'total_return':
        return metrics.totalReturn;
      case 'profit_factor':
        return metrics.profitFactor;
      case 'win_rate':
        return metrics.winRate;
      case 'max_drawdown':
        return metrics.maxDrawdown;
      case 'calmar_ratio':
        return metrics.calmarRatio;
      default:
        return 0;
    }
  }

  /** 比较结果 */
  protected isBetter(current: number, best: number): boolean {
    if (this.target.objective === 'max_drawdown') {
      // 对于回撤，越小越好
      return this.target.target?.mode === 'minimize'
        ? current < best
        : current < best;
    }

    return current > best;
  }
}

// ============================================
// 网格搜索优化器
// ============================================

export class GridSearchOptimizer extends BaseOptimizer {
  async optimize(
    runBacktest: (params: Record<string, number>) => Promise<BacktestResult>
  ): Promise<OptimizationResult> {
    const startTime = performance.now();
    const allResults: OptimizationResult['allResults'] = [];
    let bestParams: Record<string, number> = {};
    let bestMetrics: BacktestMetrics = {
      totalReturn: 0,
      sharpeRatio: 0,
      sortinoRatio: 0,
      maxDrawdown: 100,
      winRate: 0,
      profitFactor: 0,
      calmarRatio: 0,
    };
    let bestResult: BacktestResult | null = null;
    let bestScore = this.target.objective === 'max_drawdown' ? Infinity : -Infinity;

    // 生成所有参数组合
    const generateCombinations = (
      spaces: ParameterSpace[],
      index: number = 0,
      current: Record<string, number> = {}
    ): Record<string, number>[] => {
      if (index === spaces.length) {
        return [current];
      }

      const space = spaces[index];
      const combinations: Record<string, number>[] = [];

      for (let value = space.min; value <= space.max; value += space.step) {
        const newCurrent = { ...current, [space.name]: value };
        combinations.push(...generateCombinations(spaces, index + 1, newCurrent));
      }

      return combinations;
    };

    let allCombinations = generateCombinations(this.parameterSpaces);
    const total = Math.min(allCombinations.length, this.maxRuns);

    console.log(`[GridSearch] Total combinations: ${allCombinations.length}`);

    // 限制运行次数
    if (allCombinations.length > this.maxRuns) {
      allCombinations = allCombinations.slice(0, this.maxRuns);
    }

    // 运行优化
    let currentRun = 0;
    for (const params of allCombinations) {
      currentRun++;

      const result = await runBacktest(params);

      if (!result) continue;

      const metrics = this.extractMetrics(result);

      // 检查约束
      if (!this.checkConstraints(metrics)) {
        if (this.onProgress) {
          this.onProgress(currentRun / total, currentRun, total);
        }
        continue;
      }

      const score = this.getObjectiveValue(metrics);
      const isBetter = this.isBetter(score, bestScore);

      allResults.push({ params, metrics, result });

      if (isBetter) {
        bestScore = score;
        bestParams = params;
        bestMetrics = metrics;
        bestResult = result;

        console.log(`[GridSearch] New best: ${JSON.stringify(params)} - Score: ${score.toFixed(4)}`);
      }

      if (this.onProgress) {
        this.onProgress(currentRun / total, currentRun, total);
      }

      // 检查是否达到最大运行次数
      if (currentRun >= this.maxRuns) break;
    }

    const runtime = performance.now() - startTime;

    return {
      bestParams,
      bestMetrics,
      bestResult: bestResult!,
      allResults,
      totalRuns: currentRun,
      runtime,
    };
  }

  private extractMetrics(result: BacktestResult): BacktestMetrics {
    const { metrics } = result;
    return {
      totalReturn: metrics.totalReturn,
      sharpeRatio: metrics.sharpeRatio,
      sortinoRatio: metrics.sortinoRatio,
      maxDrawdown: metrics.maxDrawdown,
      winRate: metrics.winRate,
      profitFactor: metrics.profitFactor,
      calmarRatio:
        metrics.maxDrawdown !== 0 ? metrics.annualizedReturn / metrics.maxDrawdown : 0,
    };
  }
}

// ============================================
// 随机搜索优化器
// ============================================

export class RandomSearchOptimizer extends BaseOptimizer {
  private iterations: number;

  constructor(
    strategy: IStrategy,
    parameterSpaces: ParameterSpace[],
    target: OptimizationTarget,
    iterations: number = 100
  ) {
    super(strategy, parameterSpaces, target, iterations);
    this.iterations = iterations;
  }

  async optimize(
    runBacktest: (params: Record<string, number>) => Promise<BacktestResult>
  ): Promise<OptimizationResult> {
    const startTime = performance.now();
    const allResults: OptimizationResult['allResults'] = [];
    let bestParams: Record<string, number> = {};
    let bestMetrics: BacktestMetrics = {
      totalReturn: 0,
      sharpeRatio: 0,
      sortinoRatio: 0,
      maxDrawdown: 100,
      winRate: 0,
      profitFactor: 0,
      calmarRatio: 0,
    };
    let bestResult: BacktestResult | null = null;
    let bestScore = this.target.objective === 'max_drawdown' ? Infinity : -Infinity;

    console.log(`[RandomSearch] Running ${this.iterations} iterations`);

    for (let i = 0; i < this.iterations; i++) {
      // 随机生成参数
      const params: Record<string, number> = {};
      for (const space of this.parameterSpaces) {
        params[space.name] = space.min + Math.random() * (space.max - space.min);
        // 四舍五入到步长的整数倍
        params[space.name] = Math.round(params[space.name] / space.step) * space.step;
        // 确保在范围内
        params[space.name] = Math.max(space.min, Math.min(space.max, params[space.name]));
      }

      const result = await runBacktest(params);

      if (!result) continue;

      const metrics = this.extractMetrics(result);

      if (!this.checkConstraints(metrics)) {
        if (this.onProgress) {
          this.onProgress((i + 1) / this.iterations, i + 1, this.iterations);
        }
        continue;
      }

      const score = this.getObjectiveValue(metrics);
      const isBetter = this.isBetter(score, bestScore);

      allResults.push({ params, metrics, result });

      if (isBetter) {
        bestScore = score;
        bestParams = params;
        bestMetrics = metrics;
        bestResult = result;

        console.log(
          `[RandomSearch] New best: ${JSON.stringify(params)} - Score: ${score.toFixed(4)}`
        );
      }

      if (this.onProgress) {
        this.onProgress((i + 1) / this.iterations, i + 1, this.iterations);
      }
    }

    const runtime = performance.now() - startTime;

    return {
      bestParams,
      bestMetrics,
      bestResult: bestResult!,
      allResults,
      totalRuns: this.iterations,
      runtime,
    };
  }

  private extractMetrics(result: BacktestResult): BacktestMetrics {
    const { metrics } = result;
    return {
      totalReturn: metrics.totalReturn,
      sharpeRatio: metrics.sharpeRatio,
      sortinoRatio: metrics.sortinoRatio,
      maxDrawdown: metrics.maxDrawdown,
      winRate: metrics.winRate,
      profitFactor: metrics.profitFactor,
      calmarRatio:
        metrics.maxDrawdown !== 0 ? metrics.annualizedReturn / metrics.maxDrawdown : 0,
    };
  }
}

// ============================================
// 优化报告
// ============================================

export function printOptimizationReport(result: OptimizationResult): void {
  console.log('\n=== Optimization Report ===');
  console.log(`Total Runs:    ${result.totalRuns}`);
  console.log(`Runtime:      ${(result.runtime / 1000).toFixed(2)}s`);
  console.log(`Runs/sec:      ${(result.totalRuns / (result.runtime / 1000)).toFixed(2)}`);
  console.log('\nBest Parameters:');
  for (const [key, value] of Object.entries(result.bestParams)) {
    console.log(`  ${key}: ${value}`);
  }
  console.log('\nBest Metrics:');
  console.log(`  Total Return:    ${result.bestMetrics.totalReturn.toFixed(2)}%`);
  console.log(`  Sharpe Ratio:    ${result.bestMetrics.sharpeRatio.toFixed(4)}`);
  console.log(`  Sortino Ratio:  ${result.bestMetrics.sortinoRatio.toFixed(4)}`);
  console.log(`  Max Drawdown:   ${result.bestMetrics.maxDrawdown.toFixed(2)}%`);
  console.log(`  Win Rate:      ${result.bestMetrics.winRate.toFixed(2)}%`);
  console.log(`  Profit Factor:  ${result.bestMetrics.profitFactor.toFixed(4)}`);
  console.log(`  Calmar Ratio:   ${result.bestMetrics.calmarRatio.toFixed(4)}`);
  console.log('===========================\n');
}

// ============================================
// 便捷函数
// ============================================

export async function optimizeStrategy(
  strategy: IStrategy,
  parameterSpaces: ParameterSpace[],
  target: OptimizationTarget,
  runBacktest: (params: Record<string, number>) => Promise<BacktestResult>,
  options: {
    mode?: 'grid' | 'random';
    maxRuns?: number;
    onProgress?: (progress: number, current: number, total: number) => void;
  } = {}
): Promise<OptimizationResult> {
  const { mode = 'grid', maxRuns = 1000, onProgress } = options;

  const optimizer =
    mode === 'random'
      ? new RandomSearchOptimizer(strategy, parameterSpaces, target, maxRuns)
      : new GridSearchOptimizer(strategy, parameterSpaces, target, maxRuns);

  if (onProgress) {
    optimizer.setProgressCallback(onProgress);
  }

  return optimizer.optimize(runBacktest);
}
