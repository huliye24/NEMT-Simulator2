/**
 * NEMT Web Simulator - TypeScript类型定义
 * 非平衡市场理论模拟器
 */

// NEMT模型参数
export interface NEMTParams {
  alpha: number;        // 扩散系数 (0.01 - 1.0)
  beta: number;         // 非线性强度 (0.1 - 20)
  noiseLevel: number;  // 噪声水平 (0 - 2)
  dt: number;          // 时间步长
  dx: number;          // 空间步长
  steps: number;       // 演化步数
  n: number;            // 空间点数
}

// 复数类型（JavaScript中没有原生复数）
export interface Complex {
  re: number;
  im: number;
}

// 实验结果
export interface ExperimentResult {
  params: NEMTParams;
  spectralWidth: number;
  spectrum: Float64Array;
  freqs: Float64Array;
  psi: Complex[];
  evolution: number[][];  // 时间演化数据
  resonance: ResonanceResult;
  meanFrequency: number;
}

// 共振分析结果
export interface ResonanceResult {
  peakFrequencies: number[];
  peakAmplitudes: number[];
  numPeaks: number;
}

// 噪声扫描实验结果
export interface NoiseScanResult {
  noiseLevels: number[];
  spectralWidths: number[];
  meanFrequencies: number[];
  resonanceCounts: number[];
  results: ExperimentResult[];
}

// 非线性扫描实验结果
export interface NonlinearScanResult {
  betaValues: number[];
  spectralWidths: number[];
  resonanceCounts: number[];
  meanFrequencies: number[];
  results: ExperimentResult[];
}

// 实验类型
export type ExperimentType = 'noise' | 'nonlinear' | 'comparison' | 'all';

// 可视化数据
export interface VisualizationData {
  spectralWidth: number;
  spectrum: Float64Array;
  freqs: Float64Array;
  evolution?: number[][];
  psi?: Complex[];
}

// 模拟状态
export interface SimulationState {
  isRunning: boolean;
  progress: number;
  currentStep: number;
  result: ExperimentResult | null;
}

// 预设参数
export interface PresetParams {
  name: string;
  description: string;
  params: NEMTParams;
}

export const PRESET_PARAMS: PresetParams[] = [
  {
    name: '默认参数',
    description: '适用于一般市场模拟',
    params: { alpha: 0.1, beta: 1.0, noiseLevel: 0.2, dt: 0.01, dx: 1.0, steps: 200, n: 128 }
  },
  {
    name: '高波动市场',
    description: '模拟高波动性市场',
    params: { alpha: 0.05, beta: 5.0, noiseLevel: 0.8, dt: 0.01, dx: 1.0, steps: 300, n: 128 }
  },
  {
    name: '稳定市场',
    description: '模拟低波动稳定市场',
    params: { alpha: 0.2, beta: 0.5, noiseLevel: 0.1, dt: 0.01, dx: 1.0, steps: 200, n: 128 }
  },
  {
    name: '极端事件',
    description: '模拟黑天鹅事件',
    params: { alpha: 0.01, beta: 10.0, noiseLevel: 1.5, dt: 0.005, dx: 1.0, steps: 500, n: 256 }
  }
];

// 默认参数
export const DEFAULT_PARAMS: NEMTParams = {
  alpha: 0.1,
  beta: 1.0,
  noiseLevel: 0.2,
  dt: 0.01,
  dx: 1.0,
  steps: 200,
  n: 128
};

// 噪声扫描参数
export const NOISE_LEVELS = [0, 0.1, 0.3, 0.5, 0.8, 1.0];

// 非线性扫描参数
export const BETA_VALUES = [0.5, 1.0, 2.0, 5.0, 10.0];
