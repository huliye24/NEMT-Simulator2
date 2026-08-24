/**
 * NEMT 执行框架核心类型定义
 * 对应第七章：预测→信号→验证→加仓
 */

// =====================
// 方向假设
// =====================
export type DirectionBias = 'strongly_bullish' | 'cautiously_bullish' | 'neutral' | 'cautiously_bearish' | 'strongly_bearish' | 'watch';

export type CycleLevel = 'monthly' | 'weekly' | 'daily' | 'none';

export type HuntingMode = 'on' | 'off';

// =====================
// 预测结果
// =====================
export interface Prediction {
  directionBias: DirectionBias;
  cycleLevel: CycleLevel;
  huntingMode: HuntingMode;
  confidence: number; // 0-1
  reason: string;
  macroScore: number;    // 宏观流动性评分 (0-10)
  onchainScore: number;  // 链上健康度评分 (0-10)
  halvingPhase: 'early' | 'main_rise' | 'late' | 'bear_market';
  rtiScore: number;       // 角色倾向指数 (-10 to +10)
}

// =====================
// 信号类型
// =====================
export type SignalType = 'vortex_breakout' | 'stochastic_resonance' | 'trend_pullback' | 'none';

export interface Signal {
  type: SignalType;
  direction: 'long' | 'short';
  confidence: number;      // 0-1
  maturity?: number;       // 涡旋成熟度 (0-20)
  phase?: string;          // A/B/C/D
  price?: number;
  timestamp: string;
  reason: string;
}

// =====================
// 验证清单
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

// =====================
// 仓位管理
// =====================
export interface PositionSize {
  initialPercent: number;  // 初始仓位百分比
  maxPercent: number;      // 最大仓位百分比
  addOnPercent: number;    // 加仓百分比
  stopLossPercent: number;  // 止损百分比
}

export interface KellyParams {
  winRate: number;
  rewardRiskRatio: number;
  confidenceCoefficient: number;
}

export type AddPositionTiming = 'breakout_retest' | 'ma_pullback' | 'higher_tf_breakout';

// =====================
// 止盈止损
// =====================
export type TakeProfitTier = 1 | 2 | 3 | 4;

export interface TakeProfitCondition {
  tier: TakeProfitTier;
  trigger: string;
  percent: number;
  indicator: string;
  value: number;
}

export interface StopLossRule {
  type: 'fixed' | 'breakeven' | 'trailing';
  level: number;      // 百分比
  triggerCondition: string;
}

// =====================
// 持仓状态
// =====================
export interface Position {
  entryPrice: number;
  currentPrice: number;
  size: number;           // 仓位大小
  unrealizedPnL: number;   // 浮盈/浮亏
  pnlPercent: number;      // 浮盈/浮亏百分比
  stopLoss: number;        // 当前止损位
  positionPhase: number;   // 第几次加仓后
  entryTime: string;
  signals: Signal[];       // 触发入场的信号列表
}

export interface TakeProfitStatus {
  tier1Triggered: boolean;
  tier2Triggered: boolean;
  tier3Triggered: boolean;
  tier4Triggered: boolean;
}

// =====================
// 执行卡片状态
// =====================
export interface ExecutionCard {
  // 预测
  prediction: Prediction;
  
  // 信号
  currentSignal: Signal | null;
  signalStatus: 'waiting' | 'triggered' | 'confirmed';
  
  // 验证
  verification: VerificationResult | null;
  
  // 持仓
  position: Position | null;
  takeProfitStatus: TakeProfitStatus;
  
  // 加仓
  addPositionTiming: AddPositionTiming | null;
  
  // 离场
  exitReason: string | null;
  cooldownUntil: string | null;  // 冷静期
}

// =====================
// Pipeline 日志
// =====================
export interface ExecutionLog {
  timestamp: string;
  step: string;
  level: 'INFO' | 'SUCCESS' | 'WARNING' | 'ERROR';
  message: string;
  data?: any;
}
