/**
 * Copyright 2026 NEMT Lab
 *
 * NEMT Strategy Configuration
 * 借鉴 freqtrade 配置系统
 */

import type { StrategyConfig, Timeframe } from '../interfaces/IStrategy';

// ============================================
// 配置项类型
// ============================================

export interface NEMTConfig {
  // NEMT 特有配置
  nemt: {
    /** 临界熵阈值 */
    criticalEntropy: number;
    /** 临界 ψ 阈值 */
    criticalPsi: number;
    /** 稳定 ψ 阈值 */
    stablePsi: number;
    /** EMA 衰减因子 */
    emaAlpha: number;
    /** 相位确认天数 */
    phaseConfirmDays: number;
  };
}

export interface BacktestConfig {
  // 回测配置
  backtest: {
    /** 初始资金 */
    initialCapital: number;
    /** 手续费率 */
    commissionRate: number;
    /** 滑点 */
    slippage: number;
    /** 开始时间 */
    startDate: string;
    /** 结束时间 */
    endDate: string;
  };
}

export interface ExchangeConfig {
  // 交易所配置
  exchange: {
    /** 交易所名称 */
    name: string;
    /** API Key */
    apiKey?: string;
    /** 密钥 */
    secretKey?: string;
    /** 是否测试网 */
    testnet: boolean;
    /** 交易对 */
    pairs: string[];
    /** 时间周期 */
    timeframe: Timeframe;
  };
}

export interface RiskConfig {
  // 风险配置
  risk: {
    /** 最大同时持仓 */
    maxOpenTrades: number;
    /** 单笔最大仓位 (%) */
    maxPositionSize: number;
    /** 最大总仓位 (%) */
    maxTotalExposure: number;
    /** 止损 (%) */
    stoploss: number;
    /** 追踪止损 (%) */
    trailingStop?: number;
    /** 日亏损限制 (%) */
    dailyLossLimit: number;
    /** 周亏损限制 (%) */
    weeklyLossLimit: number;
    /** 月亏损限制 (%) */
    monthlyLossLimit: number;
  };
}

export interface BotConfig {
  // Bot 配置
  bot: {
    /** Bot 模式 */
    mode: 'dry_run' | 'live' | 'backtest';
    /** 运行时长限制 (秒) */
    maxRuntime?: number;
    /** 心跳间隔 (秒) */
    heartbeatInterval: number;
    /** 日志级别 */
    logLevel: 'debug' | 'info' | 'warning' | 'error';
  };
}

// ============================================
// 完整配置
// ============================================

export interface StrategyRuntimeConfig
  extends StrategyConfig,
    NEMTConfig,
    BacktestConfig,
    ExchangeConfig,
    RiskConfig,
    BotConfig {
  /** 策略 ID */
  strategyId: string;
  /** 策略名称 */
  strategyName: string;
}

// ============================================
// 配置验证
// ============================================

export interface ConfigValidationResult {
  valid: boolean;
  errors: string[];
  warnings: string[];
}

export function validateConfig(config: Partial<StrategyRuntimeConfig>): ConfigValidationResult {
  const errors: string[] = [];
  const warnings: string[] = [];

  // 基础验证
  if (!config.strategyId) {
    errors.push('strategyId is required');
  }

  if (!config.strategyName) {
    errors.push('strategyName is required');
  }

  // 回测验证
  if (config.backtest) {
    if (config.backtest.initialCapital <= 0) {
      errors.push('initialCapital must be positive');
    }
    if (config.backtest.commissionRate < 0 || config.backtest.commissionRate > 1) {
      errors.push('commissionRate must be between 0 and 1');
    }
    if (config.backtest.slippage < 0 || config.backtest.slippage > 1) {
      errors.push('slippage must be between 0 and 1');
    }
  }

  // 风险验证
  if (config.risk) {
    if (config.risk.stoploss >= 0) {
      errors.push('stoploss must be negative');
    }
    if (config.risk.stoploss < -1) {
      warnings.push('stoploss seems too large (> 100%)');
    }
    if (config.risk.maxOpenTrades <= 0) {
      errors.push('maxOpenTrades must be positive');
    }
    if (config.risk.maxPositionSize <= 0 || config.risk.maxPositionSize > 100) {
      errors.push('maxPositionSize must be between 0 and 100');
    }
  }

  // NEMT 验证
  if (config.nemt) {
    if (config.nemt.criticalEntropy < 0 || config.nemt.criticalEntropy > 1) {
      errors.push('criticalEntropy must be between 0 and 1');
    }
    if (config.nemt.criticalPsi < 0 || config.nemt.criticalPsi > 1) {
      errors.push('criticalPsi must be between 0 and 1');
    }
  }

  return {
    valid: errors.length === 0,
    errors,
    warnings,
  };
}

// ============================================
// 默认配置
// ============================================

export const DEFAULT_NEMT_CONFIG: NEMTConfig = {
  nemt: {
    criticalEntropy: 0.7,
    criticalPsi: 0.5,
    stablePsi: 0.3,
    emaAlpha: 0.3,
    phaseConfirmDays: 1,
  },
};

export const DEFAULT_BACKTEST_CONFIG: BacktestConfig = {
  backtest: {
    initialCapital: 10000,
    commissionRate: 0.001,
    slippage: 0.0005,
    startDate: '2025-01-01',
    endDate: '2025-12-31',
  },
};

export const DEFAULT_EXCHANGE_CONFIG: ExchangeConfig = {
  exchange: {
    name: 'binance',
    testnet: true,
    pairs: ['BTCUSDT', 'ETHUSDT'],
    timeframe: '1h',
  },
};

export const DEFAULT_RISK_CONFIG: RiskConfig = {
  risk: {
    maxOpenTrades: 3,
    maxPositionSize: 10,
    maxTotalExposure: 30,
    stoploss: -0.05,
    trailingStop: 0.02,
    dailyLossLimit: 2,
    weeklyLossLimit: 5,
    monthlyLossLimit: 10,
  },
};

export const DEFAULT_BOT_CONFIG: BotConfig = {
  bot: {
    mode: 'dry_run',
    heartbeatInterval: 60,
    logLevel: 'info',
  },
};

// ============================================
// 配置合并
// ============================================

export function mergeConfig(
  base: Partial<StrategyRuntimeConfig>,
  override: Partial<StrategyRuntimeConfig>
): StrategyRuntimeConfig {
  return {
    // 基础配置
    ...base,
    ...override,

    // NEMT 配置
    nemt: {
      ...DEFAULT_NEMT_CONFIG.nemt,
      ...(base.nemt || {}),
      ...(override.nemt || {}),
    },

    // 回测配置
    backtest: {
      ...DEFAULT_BACKTEST_CONFIG.backtest,
      ...(base.backtest || {}),
      ...(override.backtest || {}),
    },

    // 交易所配置
    exchange: {
      ...DEFAULT_EXCHANGE_CONFIG.exchange,
      ...(base.exchange || {}),
      ...(override.exchange || {}),
    },

    // 风险配置
    risk: {
      ...DEFAULT_RISK_CONFIG.risk,
      ...(base.risk || {}),
      ...(override.risk || {}),
    },

    // Bot 配置
    bot: {
      ...DEFAULT_BOT_CONFIG.bot,
      ...(base.bot || {}),
      ...(override.bot || {}),
    },
  };
}

// ============================================
// 配置加载
// ============================================

export function loadConfigFromJSON(json: string): Partial<StrategyRuntimeConfig> {
  try {
    return JSON.parse(json);
  } catch (e) {
    throw new Error(`Failed to parse config JSON: ${e}`);
  }
}

export function saveConfigToJSON(config: Partial<StrategyRuntimeConfig>): string {
  return JSON.stringify(config, null, 2);
}

// ============================================
// 配置预设
// ============================================

export const CONFIG_PRESETS = {
  /** 保守策略 */
  conservative: {
    risk: {
      maxOpenTrades: 1,
      maxPositionSize: 5,
      maxTotalExposure: 10,
      stoploss: -0.03,
      trailingStop: 0.015,
      dailyLossLimit: 1,
      weeklyLossLimit: 3,
      monthlyLossLimit: 5,
    },
  },

  /** 平衡策略 */
  balanced: {
    risk: {
      maxOpenTrades: 3,
      maxPositionSize: 10,
      maxTotalExposure: 30,
      stoploss: -0.05,
      trailingStop: 0.02,
      dailyLossLimit: 2,
      weeklyLossLimit: 5,
      monthlyLossLimit: 10,
    },
  },

  /** 激进策略 */
  aggressive: {
    risk: {
      maxOpenTrades: 5,
      maxPositionSize: 20,
      maxTotalExposure: 50,
      stoploss: -0.10,
      trailingStop: 0.03,
      dailyLossLimit: 3,
      weeklyLossLimit: 8,
      monthlyLossLimit: 15,
    },
  },

  /** 网格策略 */
  grid: {
    backtest: {
      initialCapital: 5000,
    },
    risk: {
      maxOpenTrades: 10,
      maxPositionSize: 10,
      maxTotalExposure: 100,
      stoploss: -0.20,
      dailyLossLimit: 5,
      weeklyLossLimit: 10,
      monthlyLossLimit: 20,
    },
  },
} as const;
