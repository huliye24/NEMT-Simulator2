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
 * NEMT核心算法 - TypeScript实现
 * 非平衡市场理论 (Non-Equilibrium Market Theory)
 * 
 * 数学模型：改进的非线性薛定谔方程 (NLS)
 * i∂ψ/∂t + α∂²ψ/∂x² + β|ψ|²ψ = η(x,t)
 */

import { 
  NEMTParams, 
  Complex, 
  ExperimentResult, 
  ResonanceResult,
  NoiseScanResult,
  NonlinearScanResult,
  DEFAULT_PARAMS,
  NOISE_LEVELS,
  BETA_VALUES
} from '../types/nemt';

/**
 * 复数运算工具函数
 */
export const ComplexUtils = {
  // 创建复数
  create: (re: number, im: number = 0): Complex => ({ re, im }),
  
  // 加法
  add: (a: Complex, b: Complex): Complex => ({ re: a.re + b.re, im: a.im + b.im }),
  
  // 减法
  sub: (a: Complex, b: Complex): Complex => ({ re: a.re - b.re, im: a.im - b.im }),
  
  // 乘法
  mul: (a: Complex, b: Complex): Complex => ({
    re: a.re * b.re - a.im * b.im,
    im: a.re * b.im + a.im * b.re
  }),
  
  // 标量乘法
  scale: (a: Complex, s: number): Complex => ({ re: a.re * s, im: a.im * s }),
  
  // 共轭
  conj: (a: Complex): Complex => ({ re: a.re, im: -a.im }),
  
  // 模
  abs: (a: Complex): number => Math.sqrt(a.re * a.re + a.im * a.im),
  
  // 模平方
  abs2: (a: Complex): number => a.re * a.re + a.im * a.im,
  
  // 虚数单位 i
  i: (): Complex => ({ re: 0, im: 1 }),
  
  // 从极坐标创建
  fromPolar: (r: number, theta: number): Complex => ({
    re: r * Math.cos(theta),
    im: r * Math.sin(theta)
  }),
  
  // 转换为极坐标
  toPolar: (a: Complex): { r: number; theta: number } => ({
    r: Math.sqrt(a.re * a.re + a.im * a.im),
    theta: Math.atan2(a.im, a.re)
  })
};

/**
 * FFT实现（Cooley-Tukey算法，2的幂次长度）
 */
export class FFT {
  private n: number;
  private levels: number;
  private cosTable: number[];
  private sinTable: number[];
  
  constructor(n: number) {
    if (n < 2 || (n & (n - 1)) !== 0) {
      throw new Error('FFT length must be a power of 2');
    }
    this.n = n;
    this.levels = Math.log2(n);
    this.cosTable = new Array(n / 2);
    this.sinTable = new Array(n / 2);
    
    for (let i = 0; i < n / 2; i++) {
      const angle = 2 * Math.PI * i / n;
      this.cosTable[i] = Math.cos(angle);
      this.sinTable[i] = Math.sin(angle);
    }
  }
  
  /**
   * 快速傅里叶变换
   * @param input 复数数组
   * @returns 变换后的复数数组
   */
  transform(input: Complex[]): Complex[] {
    const n = this.n;
    const output: Complex[] = input.map(x => ({ ...x }));
    
    // 位反转变位
    for (let i = 0; i < n; i++) {
      const j = this.bitReverse(i);
      if (j > i) {
        [output[i], output[j]] = [output[j], output[i]];
      }
    }
    
    // 蝶形运算
    for (let size = 2; size <= n; size *= 2) {
      const halfSize = size / 2;
      const tableStep = n / size;
      
      for (let i = 0; i < n; i += size) {
        for (let j = 0; j < halfSize; j++) {
          const tableIdx = j * tableStep;
          const even = output[i + j];
          const odd = ComplexUtils.mul(output[i + j + halfSize], {
            re: this.cosTable[tableIdx],
            im: -this.sinTable[tableIdx]
          });
          
          output[i + j] = ComplexUtils.add(even, odd);
          output[i + j + halfSize] = ComplexUtils.sub(even, odd);
        }
      }
    }
    
    return output;
  }
  
  /**
   * 逆FFT
   */
  inverse(input: Complex[]): Complex[] {
    const result = input.map(x => ComplexUtils.conj(x));
    const transformed = this.transform(result);
    return transformed.map(x => ComplexUtils.scale(ComplexUtils.conj(x), 1 / this.n));
  }
  
  private bitReverse(j: number): number {
    let k = 0;
    for (let i = 0; i < this.levels; i++) {
      k = (k << 1) | (j & 1);
      j >>= 1;
    }
    return k;
  }
}

/**
 * NEMT模拟器类
 */
export class NEMTSimulator {
  private params: NEMTParams;
  private psi: Complex[] = [];
  private psiHistory: number[][] = [];
  private N: number = 0;
  
  constructor(params: Partial<NEMTParams> = {}) {
    this.params = { ...DEFAULT_PARAMS, ...params };
  }
  
  /**
   * 设置参数
   */
  setParams(params: Partial<NEMTParams>): void {
    this.params = { ...this.params, ...params };
  }
  
  /**
   * 获取当前参数
   */
  getParams(): NEMTParams {
    return { ...this.params };
  }
  
  /**
   * 初始化市场状态（复振幅ψ）
   * @param priceData 原始价格数据
   * @returns 归一化后的复振幅
   */
  initializeState(priceData: number[]): Complex[] {
    const n = priceData.length;
    
    // 归一化
    const mean = priceData.reduce((a, b) => a + b, 0) / n;
    const variance = priceData.reduce((sum, x) => sum + (x - mean) ** 2, 0) / n;
    const std = Math.sqrt(variance);
    
    // 归一化并转为复数
    this.psi = priceData.map(x => ({
      re: std > 0 ? (x - mean) / std : 0,
      im: 0
    }));
    
    this.N = n;
    return this.psi;
  }
  
  /**
   * 生成高斯噪声
   */
  private generateNoise(size: number): Complex[] {
    const noise: Complex[] = [];
    for (let i = 0; i < size; i++) {
      // Box-Muller变换生成高斯随机数
      const u1 = Math.random();
      const u2 = Math.random();
      const z1 = Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
      const z2 = Math.sqrt(-2 * Math.log(u1)) * Math.sin(2 * Math.PI * u2);
      
      const scale = this.params.noiseLevel * 0.5;
      noise.push({
        re: scale * z1,
        im: scale * z2
      });
    }
    return noise;
  }
  
  /**
   * 计算离散拉普拉斯算子
   */
  private computeLaplacian(psi: Complex[]): Complex[] {
    const laplacian: Complex[] = new Array(this.N);
    const dx2 = this.params.dx * this.params.dx;
    
    // 内部点：中心差分
    for (let i = 1; i < this.N - 1; i++) {
      laplacian[i] = ComplexUtils.scale(
        ComplexUtils.add(
          ComplexUtils.sub(psi[i - 1], ComplexUtils.scale(psi[i], 2)),
          psi[i + 1]
        ),
        1 / dx2
      );
    }
    
    // 边界条件
    laplacian[0] = ComplexUtils.scale(
      ComplexUtils.sub(psi[1], psi[0]),
      1 / dx2
    );
    laplacian[this.N - 1] = ComplexUtils.scale(
      ComplexUtils.sub(psi[this.N - 2], psi[this.N - 1]),
      1 / dx2
    );
    
    return laplacian;
  }
  
  /**
   * 时间演化（核心算法）
   * NLS方程：dψ/dt = i(α∇²ψ + β|ψ|²ψ) + η
   */
  evolve(psi?: Complex[], steps?: number): Complex[] {
    psi = psi || this.psi;
    if (psi.length === 0) {
      throw new Error('State not initialized. Call initializeState first.');
    }
    
    const N = this.N;
    steps = steps || this.params.steps;
    const { alpha, beta, dt } = this.params;
    
    // 记录初始状态
    this.psiHistory = [psi.map(x => ComplexUtils.abs(x))];
    
    // 工作副本
    let state = psi.map(x => ({ ...x }));
    
    for (let t = 0; t < steps; t++) {
      // 1. 计算拉普拉斯算子
      const laplacian = this.computeLaplacian(state);
      
      // 2. 非线性项 |ψ|²ψ
      const nonlinear = state.map(x => {
        const abs2 = ComplexUtils.abs2(x);
        return ComplexUtils.scale(x, beta * abs2);
      });
      
      // 3. dψ/dt = i(α∇²ψ + β|ψ|²ψ)
      const dpsi = state.map((_, i) => {
        const term = ComplexUtils.add(
          ComplexUtils.scale(laplacian[i], alpha),
          nonlinear[i]
        );
        return { re: -term.im, im: term.re }; // i * term
      });
      
      // 4. 添加噪声
      const noise = this.generateNoise(N);
      
      // 5. 更新状态（欧拉法）
      state = state.map((x, i) => 
        ComplexUtils.add(
          ComplexUtils.add(x, ComplexUtils.scale(dpsi[i], dt)),
          ComplexUtils.scale(noise[i], dt)
        )
      );
      
      // 记录振幅演化
      this.psiHistory.push(state.map(x => ComplexUtils.abs(x)));
    }
    
    this.psi = state;
    return this.psi;
  }
  
  /**
   * 频谱分析
   */
  spectralAnalysis(psi?: Complex[]): { freqs: Float64Array; spectrum: Float64Array } {
    psi = psi || this.psi;
    if (psi.length === 0) {
      throw new Error('State not initialized.');
    }
    
    // FFT
    const fft = new FFT(psi.length);
    const spectrum = fft.transform(psi);
    
    // 频率轴
    const N = psi.length;
    const freqs = new Array(Math.floor(N / 2) + 1);
    for (let i = 0; i <= Math.floor(N / 2); i++) {
      freqs[i] = i / (N * this.params.dx);
    }
    
    // 取正半轴的振幅
    const spectrumAmp = new Array(Math.floor(N / 2) + 1);
    for (let i = 0; i <= Math.floor(N / 2); i++) {
      spectrumAmp[i] = ComplexUtils.abs(spectrum[i]);
    }
    
    return {
      freqs: new Float64Array(freqs),
      spectrum: new Float64Array(spectrumAmp)
    };
  }
  
  /**
   * 计算谱宽
   * 谱宽 = sqrt(Σ(f - f_mean)²·S(f) / ΣS(f))
   */
  computeSpectralWidth(freqs: Float64Array, spectrum: Float64Array): number {
    const N = freqs.length;
    
    // 计算总功率
    let totalPower = 0;
    for (let i = 0; i < N; i++) {
      totalPower += spectrum[i] * spectrum[i];
    }
    
    if (totalPower < 1e-10) {
      console.warn('谱功率过低');
      return 0;
    }
    
    // 计算加权均值
    let meanFreq = 0;
    for (let i = 0; i < N; i++) {
      meanFreq += freqs[i] * spectrum[i] * spectrum[i];
    }
    meanFreq /= totalPower;
    
    // 计算方差
    let variance = 0;
    for (let i = 0; i < N; i++) {
      variance += (freqs[i] - meanFreq) ** 2 * spectrum[i] * spectrum[i];
    }
    variance /= totalPower;
    
    return Math.sqrt(variance);
  }
  
  /**
   * 检测共振峰
   */
  detectResonance(freqs: Float64Array, spectrum: Float64Array): ResonanceResult {
    const N = freqs.length;
    const peakIndices: number[] = [];
    const mean = spectrum.reduce((a, b) => a + b, 0) / N;
    
    // 简单峰值检测
    for (let i = 1; i < N - 1; i++) {
      if (spectrum[i] > spectrum[i - 1] && spectrum[i] > spectrum[i + 1]) {
        if (spectrum[i] > mean * 2) {
          peakIndices.push(i);
        }
      }
    }
    
    return {
      peakFrequencies: peakIndices.map(i => freqs[i]),
      peakAmplitudes: peakIndices.map(i => spectrum[i]),
      numPeaks: peakIndices.length
    };
  }
  
  /**
   * 获取演化历史
   */
  getEvolution(): number[][] {
    return this.psiHistory;
  }
  
  /**
   * 运行完整实验
   */
  runExperiment(priceData: number[]): ExperimentResult {
    // 初始化
    const psi = this.initializeState(priceData);
    
    // 演化
    const psiFinal = this.evolve(psi);
    
    // 频谱分析
    const { freqs, spectrum } = this.spectralAnalysis(psiFinal);
    
    // 谱宽
    const spectralWidth = this.computeSpectralWidth(freqs, spectrum);
    
    // 共振检测
    const resonance = this.detectResonance(freqs, spectrum);
    
    // 计算平均频率
    let meanFreq = 0;
    const totalPower = spectrum.reduce((sum, s) => sum + s * s, 0);
    if (totalPower > 0) {
      for (let i = 0; i < freqs.length; i++) {
        meanFreq += freqs[i] * spectrum[i] * spectrum[i];
      }
      meanFreq /= totalPower;
    }
    
    return {
      params: this.getParams(),
      spectralWidth,
      spectrum,
      freqs,
      psi: psiFinal,
      evolution: this.psiHistory,
      resonance,
      meanFrequency: meanFreq
    };
  }
  
  /**
   * 噪声扫描实验
   */
  runNoiseScan(priceData: number[]): NoiseScanResult {
    const results: ExperimentResult[] = [];
    const spectralWidths: number[] = [];
    const meanFrequencies: number[] = [];
    const resonanceCounts: number[] = [];
    
    for (const noiseLevel of NOISE_LEVELS) {
      const sim = new NEMTSimulator({ ...this.params, noiseLevel });
      const result = sim.runExperiment(priceData);
      
      results.push(result);
      spectralWidths.push(result.spectralWidth);
      meanFrequencies.push(result.meanFrequency);
      resonanceCounts.push(result.resonance.numPeaks);
    }
    
    return {
      noiseLevels: [...NOISE_LEVELS],
      spectralWidths,
      meanFrequencies,
      resonanceCounts,
      results
    };
  }
  
  /**
   * 非线性扫描实验
   */
  runNonlinearScan(priceData: number[]): NonlinearScanResult {
    const results: ExperimentResult[] = [];
    const spectralWidths: number[] = [];
    const resonanceCounts: number[] = [];
    const meanFrequencies: number[] = [];
    
    for (const beta of BETA_VALUES) {
      const sim = new NEMTSimulator({ ...this.params, beta });
      const result = sim.runExperiment(priceData);
      
      results.push(result);
      spectralWidths.push(result.spectralWidth);
      resonanceCounts.push(result.resonance.numPeaks);
      meanFrequencies.push(result.meanFrequency);
    }
    
    return {
      betaValues: [...BETA_VALUES],
      spectralWidths,
      resonanceCounts,
      meanFrequencies,
      results
    };
  }
}

/**
 * 生成演示数据
 */
export function generateDemoData(n: number = 128): number[] {
  const data: number[] = [];
  let price = 100;
  
  for (let i = 0; i < n; i++) {
    // 模拟随机游走 + 趋势 + 波动率聚集
    const trend = 0.001 * i;
    const volatility = 1 + 0.5 * Math.sin(i / 20);
    const random = (Math.random() - 0.5) * volatility;
    price = price * (1 + trend + random * 0.02);
    data.push(price);
  }
  
  return data;
}
