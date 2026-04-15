/**
 * NEMT Web Simulator - TypeScript类型定义
 * 非平衡市场理论模拟器
 * 
 * 包含:
 * - 基础模型参数 (NEMTParams)
 * - 信号指标类型 (MarketPhase, DCISignal, VortexConditions等)
 * - 链上数据类型 (OnchainMetrics, OnchainHealthScore等)
 * - 执行框架类型 (Prediction, EntrySignal, Position等)
 * - 风控类型 (RiskConfig, PositionSize等)
 */

// =====================
// 基础模型参数
// =====================

export interface NEMTParams {
  alpha: number;        // 扩散系数 (0.01 - 1.0)
  beta: number;         // 非线性强度 (0.1 - 20)
  noiseLevel: number;   // 噪声水平 (0 - 2)
  dt: number;           // 时间步长
  dx: number;           // 空间步长
  steps: number;         // 演化步数
  n: number;            // 空间点数
}

// =====================
// 复数类型
// =====================

export interface Complex {
  re: number;
  im: number;
}

// =====================
// 市场相位
// =====================

export enum MarketPhase {
  PHASE_A_NOISE = "A",      // 高噪声混乱期
  PHASE_B_VORTEX = "B",     // 涡旋蓄力期
  PHASE_C_RESONANCE = "C",   // 临界爆发前夜
  PHASE_D_TREND = "D"         // 趋势运行期
}

// =====================
// 信号指标类型
// =====================

export interface DCISignal {
  value: number;           // DCI值 (0-1)
  noiseState: 'high' | 'medium' | 'low';  // 噪声状态
  direction: 'bullish' | 'bearish' | 'neutral';  // 方向
  trend: 'strengthening' | 'weakening' | 'stable';  // 趋势
}

export interface VortexConditions {
  bbwNarrow: boolean;      // 条件1: 波动率锥收窄
  volumeUniform: boolean;    // 条件2: 成交量均匀分布
  oiHighFlat: boolean;     // 条件3: OI高位走平
  fundingNeutral: boolean;   // 条件4: 资金费率零轴摆动
  isVortex: boolean;       // 是否形成涡旋
  maturityScore: number;    // 涡旋成熟度
}

export interface ResonanceConditions {
  longTermCritical: boolean;  // 条件1: 长周期临界点
  shortTermNoise: boolean;   // 条件2: 短周期噪声适中
  triggerFactor: boolean;   // 条件3: 潜在触发因子
  isResonance: boolean;     // 是否触发随机共振
  bullish: boolean;         // 方向: True=看涨, False=看跌
  confidence: number;       // 置信度 0-1
}

export interface NEMTSignals {
  dci: DCISignal;
  vortex: VortexConditions;
  resonance: ResonanceConditions;
  phase: MarketPhase;
  phaseConfidence: number;
  spectralWidth: number | null;
}

// =====================
// 链上数据类型
// =====================

export interface OnchainMetrics {
  // 估值指标
  mvrvRatio: number | null;
  mvrvZscore: number | null;
  
  // 情绪指标
  nupl: number | null;
  nuplStage: string | null;
  
  // 供需指标
  exchangeBalance: number | null;
  exchangeTrend: 'increasing' | 'decreasing' | 'stable' | null;
  
  // 持有者结构
  lthRatio: number | null;     // 长期持有者占比
  sthRatio: number | null;     // 短期持有者占比
  lthChange: number | null;    // LTH变化率
  
  // 稳定币
  stablecoinMcap: number | null;
  stablecoinChange: number | null;
  
  // 鲸鱼行为
  whaleNetflow: number | null;   // 正=流入, 负=流出
  whaleAddressCount: number | null;
  
  // 矿工
  minerFlow: number | null;
  
  // 时间戳
  timestamp: string | null;
}

export interface OnchainHealthScore {
  totalScore: number;      // 总分 0-10
  mvrvScore: number;       // 0-2
  nuplScore: number;       // 0-2
  exchangeScore: number;    // 0-2
  lthScore: number;        // 0-2
  stablecoinScore: number; // 0-2
  whaleScore: number;      // 0-2
}

export interface CycleIndicators {
  phase: string;           // 周期阶段
  cycleScore: number;      // 综合周期评分 0-1
  halvingPhase: string;    // 减半周期阶段
  daysToHalving: number | null;
}

// =====================
// 执行框架类型
// =====================

export enum Direction {
  BULLISH = "bullish",
  BEARISH = "bearish",
  NEUTRAL = "neutral"
}

export enum CycleLevel {
  INTRADAY = "intraday",  // 日内级别
  SWING = "swing",          // 波段级别 (周线)
  TREND = "trend"            // 趋势级别 (月线)
}

export enum SignalType {
  VORTEX_BREAKOUT = "vortex_breakout",    // 涡旋突破信号
  RESONANCE_TRIGGER = "resonance_trigger",   // 随机共振触发信号
  TREND_CALLBACK = "trend_callback",          // 趋势回调信号
  MACRO_ONCHAIN = "macro_onchain"           // 宏观链上共振信号
}

export enum SignalStatus {
  WAITING = "waiting",      // 等待中
  TRIGGERED = "triggered",   // 已触发
  CONFIRMED = "confirmed",   // 已确认
  FAILED = "failed"         // 失败
}

export interface Prediction {
  direction: Direction;
  cycleLevel: CycleLevel;
  confidence: number;  // 0-1
  reasoning: string;
  huntingMode: boolean;  // 是否开启狩猎模式
}

export interface EntrySignal {
  signalType: SignalType;
  status: SignalStatus;
  triggeredAt: number | null;
  entryPrice: number | null;
  confidence: number;
  conditionsMet: string[];
  conditionsFailed: string[];
}

export interface ValidationResult {
  passed: boolean;
  passedCount: number;
  requiredCount: number;
  checks: Record<string, boolean>;
  recommendation: string;
}

export interface Position {
  entryPrice: number;
  quantity: number;
  stopLoss: number;
  currentPrice: number;
  unrealizedPnl: number;
  unrealizedPnlPct: number;
  openedAt: string;
  phaseAtEntry: MarketPhase;
}

export interface TradePlan {
  prediction: Prediction;
  entrySignals: EntrySignal[];
  plannedPositionSize: number;
  initialPositionSize: number;
  addPositionSize: number;
  stopLoss: number;
  takeProfitTargets: number[];
  riskRewardRatio: number;
}

// =====================
// 风控类型
// =====================

export interface PositionSize {
  maxPosition: number;      // 最大仓位
  singleRisk: number;      // 单笔风险上限
  leverageAllowed: number;  // 允许杠杆
  positionRatio: number;    // 当前建议比例
}

export interface StopLossConfig {
  atrMultiplier: number;     // ATR倍数
  structureBuffer: number; // 结构缓冲
  maxLossPct: number;     // 最大亏损比例
  trailingThreshold: number;  // 移动止损门槛
}

export interface DrawdownLevel {
  level: 'green' | 'yellow' | 'orange' | 'red';
  threshold: number;
  action: string;
  waitingPeriod: number | null;  // 毫秒
}

export interface RiskStats {
  peakBalance: number;
  currentBalance: number;
  drawdown: number;
  drawdownPct: number;
  tradesToday: number;
  lossesToday: number;
  coolingOff: boolean;
  coolingOffUntil: string | null;
}

// =====================
// 实验结果类型
// =====================

export interface ExperimentResult {
  params: NEMTParams;
  spectralWidth: number;
  spectrum: Float64Array;
  freqs: Float64Array;
  psi: Complex[];
  evolution: Float64Array[];  // 时间演化数据
  resonance: ResonanceResult;
  meanFrequency: number;
}

export interface ResonanceResult {
  peakFrequencies: number[];
  peakAmplitudes: number[];
  numPeaks: number;
}

export interface NoiseScanResult {
  noiseLevels: number[];
  spectralWidths: number[];
  meanFrequencies: number[];
  resonanceCounts: number[];
  results: ExperimentResult[];
}

export interface NonlinearScanResult {
  betaValues: number[];
  spectralWidths: number[];
  resonanceCounts: number[];
  meanFrequencies: number[];
  results: ExperimentResult[];
}

// =====================
// 实验类型
// =====================

export type ExperimentType = 'noise' | 'nonlinear' | 'comparison' | 'all';

// =====================
// 可视化数据
// =====================

export interface VisualizationData {
  spectralWidth: number;
  spectrum: Float64Array;
  freqs: Float64Array;
  evolution?: Float64Array[];
  psi?: Complex[];
}

// =====================
// 模拟状态
// =====================

export interface SimulationState {
  isRunning: boolean;
  progress: number;
  currentStep: number;
  result: ExperimentResult | null;
}

// =====================
// 预设参数
// =====================

export interface PresetParams {
  name: string;
  description: string;
  params: NEMTParams;
}

// =====================
// 相位策略
// =====================

export interface PhaseStrategy {
  phase: MarketPhase;
  name: string;
  maxPosition: number;
  singleRisk: number;
  leverageAllowed: number;
  strategyText: string;
  focusText: string;
  avoidText: string;
}

// =====================
// 仪表板数据
// =====================

export interface DashboardData {
  summary: {
    currentPhase: string;
    phaseName: string;
    phaseDuration: number;
    phaseConfidence: string;
    totalTransitions: number;
    phaseDistribution: Record<string, number>;
    maxPosition: string;
    singleRisk: string;
    leverage: string;
    strategy: string;
    focus: string;
    avoid: string;
  };
  signals: {
    dci: DCISignal;
    vortex: VortexConditions;
    resonance: ResonanceConditions;
    spectralWidth: number | null;
  };
  onchain: OnchainHealthScore | null;
  execution: {
    inHuntingMode: boolean;
    hasPosition: boolean;
    pTrend: string;
    stats: {
      totalTrades: number;
      wins: number;
      losses: number;
      winRate: string;
      totalPnl: string;
    };
  };
}

// =====================
// 常量定义
// =====================

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

export const DEFAULT_PARAMS: NEMTParams = {
  alpha: 0.1,
  beta: 1.0,
  noiseLevel: 0.2,
  dt: 0.01,
  dx: 1.0,
  steps: 200,
  n: 128
};

export const NOISE_LEVELS = [0, 0.1, 0.3, 0.5, 0.8, 1.0];
export const BETA_VALUES = [0.5, 1.0, 2.0, 5.0, 10.0];

// =====================
// DCI阈值常量
// =====================

export const DCI_THRESHOLDS = {
  high: 0.70,      // 低噪声阈值
  medium: 0.65,    // 中等阈值
  low: 0.55        // 高噪声阈值
};

// =====================
// 涡旋条件常量
// =====================

export const VORTEX_THRESHOLDS = {
  bbbPercentile: 20,           // 布林带宽度百分位
  oiChangeThreshold: 0.05,      // OI变化阈值
  oiLevelPercentile: 80,       // OI水平百分位
  fundingRateThreshold: 0.0001, // 资金费率阈值
  maturityLow: 5.0,
  maturityHigh: 15.0
};

// =====================
// 随机共振条件常量
// =====================

export const RESONANCE_THRESHOLDS = {
  mvrvCriticalLow: 0.0,
  mvrvCriticalHigh: 5.0,
  dciVolLow: 0.08,
  dciVolHigh: 0.15,
  confidenceThreshold: 0.6
};

// =====================
// 相位策略映射
// =====================

export const PHASE_STRATEGIES: Record<MarketPhase, PhaseStrategy> = {
  [MarketPhase.PHASE_A_NOISE]: {
    phase: MarketPhase.PHASE_A_NOISE,
    name: '高噪声混乱期',
    maxPosition: 0.20,
    singleRisk: 0.01,
    leverageAllowed: 0,
    strategyText: '仅持有长期底仓，不做短线交易',
    focusText: '等待DCI回升、涡旋条件形成',
    avoidText: '在混乱期频繁交易'
  },
  [MarketPhase.PHASE_B_VORTEX]: {
    phase: MarketPhase.PHASE_B_VORTEX,
    name: '涡旋蓄力期',
    maxPosition: 0.50,
    singleRisk: 0.02,
    leverageAllowed: 1,
    strategyText: '识别区间边界，预设突破条件单，不预判方向',
    focusText: '涡旋成熟度、突破时成交量确认',
    avoidText: '预判突破方向、提前入场'
  },
  [MarketPhase.PHASE_C_RESONANCE]: {
    phase: MarketPhase.PHASE_C_RESONANCE,
    name: '临界爆发前夜',
    maxPosition: 0.70,
    singleRisk: 0.03,
    leverageAllowed: 2,
    strategyText: '提高对突破信号的敏感度，敢于追入',
    focusText: '触发事件兑现、突破后量能持续性',
    avoidText: '犹豫不决、等待更低/更高价位'
  },
  [MarketPhase.PHASE_D_TREND]: {
    phase: MarketPhase.PHASE_D_TREND,
    name: '趋势运行期',
    maxPosition: 1.00,
    singleRisk: 0.02,
    leverageAllowed: 1,
    strategyText: '持仓为主，回调至均线加仓',
    focusText: 'DCI是否从高位回落、SNR是否萎缩',
    avoidText: '过早下车、频繁操作'
  }
};

// =====================
// NUPL阶段名称映射
// =====================

export const NUPL_STAGES: Record<string, string> = {
  'capitulation': '投降',
  'hope_fear': '希望/恐惧',
  'optimism_anxiety': '乐观/焦虑',
  'belief_denial': '信念/否认',
  'euphoria_greed': '欣快/贪婪'
};

// =====================
// MVRV Z-score解读
// =====================

export const MVRV_INTERPRETATION = {
  extremelyLow: { threshold: 0, description: '历史底部区域' },
  low: { threshold: 1, description: '低估区域' },
  normal: { threshold: 3, description: '正常区间' },
  high: { threshold: 5, description: '高估区域' },
  extremelyHigh: { threshold: 7, description: '历史顶部区域' }
};
