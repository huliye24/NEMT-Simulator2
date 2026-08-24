/**
 * Notion 理论中枢同步 - TypeScript 版本
 * 用于前端直接从 Notion 获取 NEMT 理论配置
 */

import { MarketPhase } from '../types';

// ============================================
// 类型定义
// ============================================

export interface PhasePosition {
  phase: MarketPhase;
  name: string;
  maxPosition: number;
  singleRisk: number;
  leverage: number;
  strategy: string;
}

export interface StopLossRule {
  signalType: string;
  atrMultiplier: number;
  description: string;
}

export interface RebalanceRule {
  triggerType: 'reduce' | 'add';
  condition: string;
  action: string;
  targetRatio: number | null;
}

export interface BlackSwanRule {
  scenario: string;
  action: string;
  priority: number;
}

export interface LeverageRules {
  allowedPhases: MarketPhase[];
  maxLeverage: number;
  safetyMargin: number;
  forbiddenConditions: string[];
}

export interface TheoryContent {
  title: string;
  introduction: string;
  phases: PhasePosition[];
  stopLossRules: StopLossRule[];
  rebalanceRules: RebalanceRule[];
  blackSwanRules: BlackSwanRule[];
  leverageRules: LeverageRules;
}

export interface RiskConfig {
  phasePositions: Record<string, number>;
  stopLoss: Record<string, number>;
  rebalance: {
    reduceTriggers: RebalanceRule[];
    addTriggers: RebalanceRule[];
  };
  leverage: LeverageRules;
  blackSwan: BlackSwanRule[];
}

// ============================================
// 默认配置（从 Notion 理论中枢同步）
// ============================================

export const DEFAULT_THEORY_CONFIG: RiskConfig = {
  phasePositions: {
    max_position_phase_a: 0.20,
    single_risk_phase_a: 0.01,
    leverage_phase_a: 0,
    max_position_phase_b: 0.50,
    single_risk_phase_b: 0.02,
    leverage_phase_b: 1,
    max_position_phase_c: 0.70,
    single_risk_phase_c: 0.03,
    leverage_phase_c: 2,
    max_position_phase_d: 1.00,
    single_risk_phase_d: 0.02,
    leverage_phase_d: 1,
  },
  stopLoss: {
    atr_multiplier_vortex_breakout: 1.5,
    atr_multiplier_resonance_trigger: 2.0,
    atr_multiplier_trend_callback: 1.0,
  },
  rebalance: {
    reduceTriggers: [
      {
        triggerType: 'reduce',
        condition: '相位从D降级为B或A',
        action: '总仓位降至50%以下',
        targetRatio: 0.5,
      },
      {
        triggerType: 'reduce',
        condition: '宏观流动性评分下降2分以上',
        action: '总仓位降至60%以下',
        targetRatio: 0.6,
      },
      {
        triggerType: 'reduce',
        condition: '链上健康度评分降至≤3',
        action: '总仓位降至40%以下',
        targetRatio: 0.4,
      },
      {
        triggerType: 'reduce',
        condition: '单日波动超过10%且方向与持仓相反',
        action: '强制减仓20%（防范黑天鹅）',
        targetRatio: null,
      },
    ],
    addTriggers: [
      {
        triggerType: 'add',
        condition: '相位从B升级为C或D',
        action: '总仓位可提升至对应上限',
        targetRatio: null,
      },
      {
        triggerType: 'add',
        condition: '宏观流动性评分上升2分以上且链上健康度≥6',
        action: '加仓至上限',
        targetRatio: null,
      },
      {
        triggerType: 'add',
        condition: '涡旋成熟突破确认',
        action: '按第七章规则执行初始+加仓',
        targetRatio: null,
      },
    ],
  },
  leverage: {
    allowedPhases: [MarketPhase.PHASE_C_RESONANCE, MarketPhase.PHASE_D_TREND],
    maxLeverage: 3,
    safetyMargin: 0.05,
    forbiddenConditions: [
      '相位A（高噪声期）：杠杆会放大双向止损的损耗',
      '宏观流动性评分≤3：紧缩环境下杠杆多头是自杀行为',
      '链上健康度评分≤3：主力可能在派发',
      '单日已亏损超过总资金5%：情绪受损时杠杆会加速毁灭',
      '无明确信号的主观交易：冲动+杠杆=灾难',
    ],
  },
  blackSwan: [
    {
      scenario: '大型交易所暴雷',
      action: '分散至2-3个主流交易所+自托管钱包',
      priority: 1,
    },
    {
      scenario: '稳定币脱锚',
      action: '配置部分稳定币资产，单一资产不超过50%',
      priority: 2,
    },
    {
      scenario: '监管突变',
      action: '设置链上监控警报，提前减仓',
      priority: 3,
    },
    {
      scenario: '比特币核心代码漏洞',
      action: '实时关注社区动态，必要时清仓',
      priority: 4,
    },
  ],
};

// ============================================
// 相位仓位映射表
// ============================================

export const PHASE_POSITION_MAP: Record<MarketPhase, PhasePosition> = {
  [MarketPhase.PHASE_A_NOISE]: {
    phase: MarketPhase.PHASE_A_NOISE,
    name: '高噪声混乱期',
    maxPosition: 0.20,
    singleRisk: 0.01,
    leverage: 0,
    strategy: '持有底仓，不做短线',
  },
  [MarketPhase.PHASE_B_VORTEX]: {
    phase: MarketPhase.PHASE_B_VORTEX,
    name: '涡旋蓄力期',
    maxPosition: 0.50,
    singleRisk: 0.02,
    leverage: 1,
    strategy: '识别边界，预设条件单',
  },
  [MarketPhase.PHASE_C_RESONANCE]: {
    phase: MarketPhase.PHASE_C_RESONANCE,
    name: '临界爆发前夜',
    maxPosition: 0.70,
    singleRisk: 0.03,
    leverage: 2,
    strategy: '提高敏感度，敢于追入',
  },
  [MarketPhase.PHASE_D_TREND]: {
    phase: MarketPhase.PHASE_D_TREND,
    name: '趋势运行期',
    maxPosition: 1.00,
    singleRisk: 0.02,
    leverage: 1,
    strategy: '持仓为主，回调加仓',
  },
};

// ============================================
// 辅助函数
// ============================================

/**
 * 根据相位获取仓位配置
 */
export function getPositionByPhase(phase: MarketPhase): PhasePosition {
  return PHASE_POSITION_MAP[phase];
}

/**
 * 根据信号类型获取 ATR 止损倍数
 */
export function getATRMultiplier(
  signalType: 'vortex_breakout' | 'resonance_trigger' | 'trend_callback'
): number {
  const map: Record<string, number> = {
    vortex_breakout: 1.5,
    resonance_trigger: 2.0,
    trend_callback: 1.0,
  };
  return map[signalType] || 1.5;
}

/**
 * 检查杠杆是否允许
 */
export function checkLeverageAllowed(
  phase: MarketPhase,
  macroScore: number,
  onchainScore: number,
  dailyLossPct: number,
  hasSignal: boolean = true
): { allowed: boolean; reason: string } {
  // 规则1: 只在C和D相位使用
  if (phase === MarketPhase.PHASE_A_NOISE) {
    return {
      allowed: false,
      reason: '相位A（高噪声期）：杠杆会放大双向止损的损耗',
    };
  }

  if (phase === MarketPhase.PHASE_B_VORTEX) {
    return {
      allowed: false,
      reason: '相位B（涡旋蓄力期）：边界未清晰，避免杠杆放大风险',
    };
  }

  // 规则2: 宏观评分检查
  if (macroScore <= 3) {
    return {
      allowed: false,
      reason: `宏观流动性评分≤${macroScore}：紧缩环境下杠杆多头是自杀行为`,
    };
  }

  // 规则3: 链上评分检查
  if (onchainScore <= 3) {
    return {
      allowed: false,
      reason: `链上健康度评分≤${onchainScore}：主力可能在派发`,
    };
  }

  // 规则4: 单日亏损检查
  if (dailyLossPct > 0.05) {
    return {
      allowed: false,
      reason: `单日已亏损超过${(dailyLossPct * 100).toFixed(1)}%：情绪受损时杠杆会加速毁灭`,
    };
  }

  // 规则5: 信号检查
  if (!hasSignal) {
    return {
      allowed: false,
      reason: '无明确信号：冲动+杠杆=灾难',
    };
  }

  return { allowed: true, reason: '允许使用杠杆' };
}

/**
 * 计算杠杆安全边际
 */
export function calculateLeverageMatrix(
  phase: MarketPhase,
  entryPrice: number,
  stopLossPrice: number,
  maintenanceMargin: number = 0.005
): Array<{
  leverage: number;
  liquidationPrice: string;
  safetyMargin: string;
  safe: boolean;
}> {
  const phaseConfig = PHASE_POSITION_MAP[phase];
  const matrix: Array<{
    leverage: number;
    liquidationPrice: string;
    safetyMargin: string;
    safe: boolean;
  }> = [];

  for (let leverage = 1; leverage <= phaseConfig.leverage; leverage++) {
    // 计算强平价格
    const liquidationPrice = entryPrice * (1 - 1 / leverage + maintenanceMargin);

    // 计算安全边际
    const safetyDiff = stopLossPrice - liquidationPrice;
    const safetyPct = safetyDiff / stopLossPrice;
    const isSafe = safetyPct >= DEFAULT_THEORY_CONFIG.leverage.safetyMargin;

    matrix.push({
      leverage,
      liquidationPrice: `$${liquidationPrice.toLocaleString('en-US', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
      })}`,
      safetyMargin: `${(safetyPct * 100).toFixed(1)}%`,
      safe: isSafe,
    });
  }

  return matrix;
}

/**
 * 检查是否需要仓位再平衡
 */
export function checkRebalance(
  currentPhase: MarketPhase,
  previousPhase: MarketPhase | null,
  currentPositionRatio: number,
  macroScoreChange: number,
  onchainScoreChange: number,
  dailyVolatility: number,
  positionDirection: 'long' | 'short' | null,
  priceDirection: 'up' | 'down'
): { shouldRebalance: boolean; action: 'reduce' | 'add' | 'hold'; targetRatio: number | null; reason: string } {
  // 减仓检查
  if (previousPhase === MarketPhase.PHASE_D_TREND &&
      [MarketPhase.PHASE_A_NOISE, MarketPhase.PHASE_B_VORTEX].includes(currentPhase)) {
    return {
      shouldRebalance: true,
      action: 'reduce',
      targetRatio: 0.5,
      reason: '相位从D降级为B或A',
    };
  }

  if (macroScoreChange <= -2) {
    return {
      shouldRebalance: true,
      action: 'reduce',
      targetRatio: 0.6,
      reason: '宏观流动性评分下降2分以上',
    };
  }

  if (onchainScoreChange <= -3) {
    return {
      shouldRebalance: true,
      action: 'reduce',
      targetRatio: 0.4,
      reason: '链上健康度评分降至≤3',
    };
  }

  if (dailyVolatility > 0.10 && positionDirection && priceDirection) {
    const isOpposite = (positionDirection === 'long' && priceDirection === 'down') ||
                       (positionDirection === 'short' && priceDirection === 'up');
    if (isOpposite) {
      return {
        shouldRebalance: true,
        action: 'reduce',
        targetRatio: currentPositionRatio * 0.8,
        reason: '单日波动超过10%且方向与持仓相反',
      };
    }
  }

  // 加仓检查
  if (previousPhase === MarketPhase.PHASE_B_VORTEX &&
      [MarketPhase.PHASE_C_RESONANCE, MarketPhase.PHASE_D_TREND].includes(currentPhase)) {
    const targetRatio = PHASE_POSITION_MAP[currentPhase].maxPosition;
    return {
      shouldRebalance: true,
      action: 'add',
      targetRatio,
      reason: '相位从B升级为C或D',
    };
  }

  if (macroScoreChange >= 2 && onchainScoreChange >= 6) {
    return {
      shouldRebalance: true,
      action: 'add',
      targetRatio: PHASE_POSITION_MAP[currentPhase].maxPosition,
      reason: '宏观流动性评分上升2分以上且链上健康度≥6',
    };
  }

  return {
    shouldRebalance: false,
    action: 'hold',
    targetRatio: null,
    reason: '无再平衡触发条件',
  };
}

/**
 * 格式化理论配置为可读摘要
 */
export function formatTheorySummary(): string {
  const lines: string[] = [
    '═'.repeat(60),
    'NEMT 理论中枢 - 执行框架摘要',
    '═'.repeat(60),
    '',
    '📊 相位-仓位映射表:',
    '─'.repeat(60),
  ];

  Object.entries(PHASE_POSITION_MAP).forEach(([phase, config]) => {
    lines.push(
      `  ${config.name.padEnd(12)} | ` +
      `最大仓位: ${(config.maxPosition * 100).toFixed(0).padStart(3)}% | ` +
      `单笔风险: ${(config.singleRisk * 100).toFixed(1).padStart(4)}% | ` +
      `杠杆: ${config.leverage}x`
    );
  });

  lines.push('');
  lines.push('📉 ATR止损倍数:');
  lines.push('  • 涡旋突破: 1.5x ATR');
  lines.push('  • 随机共振触发: 2.0x ATR');
  lines.push('  • 趋势回调加仓: 1.0x ATR');

  lines.push('');
  lines.push('⚠️  杠杆使用规则:');
  lines.push('  • 允许相位: C, D');
  lines.push('  • 最大杠杆: 3x');
  lines.push('  • 安全边际: 强平价低于止损价 5%');

  lines.push('');
  lines.push('═'.repeat(60));

  return lines.join('\n');
}
