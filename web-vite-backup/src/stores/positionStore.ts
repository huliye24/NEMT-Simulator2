/**
 * Copyright 2026 NEMT Lab
 *
 * 仓位管理 Store - 管理仓位计算、风险配置、历史记录
 */

import { create } from 'zustand';

// ============================================
// 类型定义
// ============================================

export type RiskTier = 'micro' | 'small' | 'medium' | 'large';
export type AlgoMode = 'simple' | 'hybrid';

export interface PositionResult {
  position_value: number;
  position_pct: number;
  contracts: number;
  risk_amount: number;
  risk_tier: RiskTier;
  algo_mode: AlgoMode;
  methods?: {
    atr?: number;
    kelly?: number;
    confidence?: number;
    weights?: Record<string, number>;
  };
}

export interface PositionOrder {
  order_id: string;
  symbol: string;
  side: 'long' | 'short';
  position_value: number;
  position_pct: number;
  entry_price: number;
  current_price: number;
  unrealized_pnl: number;
  unrealized_pnl_pct: number;
  stop_loss: number;
  take_profit: number;
  risk_amount: number;
  confidence: number;
  timestamp: number;
  status: 'pending' | 'active' | 'closed';
}

export interface PositionHistory {
  history_id: string;
  symbol: string;
  side: 'long' | 'short';
  position_pct: number;
  entry_price: number;
  exit_price: number;
  pnl: number;
  pnl_pct: number;
  risk_amount: number;
  exit_reason: 'stop_loss' | 'take_profit' | 'manual';
  exit_time: number;
  holding_period: number;
  algo_mode: AlgoMode;
  risk_tier: RiskTier;
}

export interface RiskProfile {
  tier: RiskTier;
  tier_label: string;
  risk_per_trade_pct: number;
  max_position_pct: number;
  risk_amount: number;
  max_position: number;
  max_daily_loss: number;
}

// ============================================
// 风险等级配置
// ============================================

export const RISK_TIERS_CONFIG: Record<RiskTier, {
  max_equity: number;
  risk_per_trade: number;
  max_position_pct: number;
  max_daily_loss: number;
  max_drawdown: number;
  label: string;
  color: string;
}> = {
  micro: {
    max_equity: 10000,
    risk_per_trade: 0.05,
    max_position_pct: 0.25,
    max_daily_loss: 0.10,
    max_drawdown: 0.20,
    label: '微型',
    color: '#ef4444',
  },
  small: {
    max_equity: 100000,
    risk_per_trade: 0.03,
    max_position_pct: 0.20,
    max_daily_loss: 0.08,
    max_drawdown: 0.15,
    label: '小型',
    color: '#f97316',
  },
  medium: {
    max_equity: 1000000,
    risk_per_trade: 0.02,
    max_position_pct: 0.15,
    max_daily_loss: 0.05,
    max_drawdown: 0.10,
    label: '中型',
    color: '#22c55e',
  },
  large: {
    max_equity: Infinity,
    risk_per_trade: 0.01,
    max_position_pct: 0.10,
    max_daily_loss: 0.03,
    max_drawdown: 0.05,
    label: '大型',
    color: '#3b82f6',
  },
};

// ============================================
// Store 接口
// ============================================

interface PositionState {
  // 账户状态
  equity: number;
  initial_equity: number;
  available_margin: number;
  
  // 持仓
  open_orders: PositionOrder[];
  
  // 历史
  history: PositionHistory[];
  
  // 风险配置
  risk_tier: RiskTier;
  algo_mode: AlgoMode;
  risk_profile: RiskProfile | null;
  
  // 计算结果
  last_calculation: PositionResult | null;
  
  // 统计
  win_count: number;
  loss_count: number;
  daily_loss: number;
  max_drawdown: number;
  
  // UI 状态
  risk_slider_value: number;  // 0-100, 0=保守, 100=激进
  
  // 是否已连接
  connected: boolean;
}

interface PositionActions {
  // 初始化
  initialize: (equity: number) => void;
  
  // 仓位计算
  calculatePosition: (params: {
    symbol: string;
    side: 'long' | 'short';
    entry_price: number;
    stop_loss_pct?: number;
    signal_confidence?: number;
    atr?: number;
    historical_win_rate?: number;
    reward_ratio?: number;
  }) => PositionResult;
  
  // 订单管理
  createOrder: (order: Omit<PositionOrder, 'order_id' | 'unrealized_pnl' | 'unrealized_pnl_pct' | 'status'>) => PositionOrder;
  closeOrder: (order_id: string, exit_price: number, reason?: 'stop_loss' | 'take_profit' | 'manual') => void;
  
  // 配置更新
  setAlgoMode: (mode: AlgoMode) => void;
  setRiskSlider: (value: number) => void;
  
  // 权益更新
  updateEquity: (new_equity: number) => void;
  
  // 重置
  resetDailyLoss: () => void;
  resetAll: () => void;
}

type PositionStoreState = PositionState & PositionActions;

// ============================================
// 辅助函数
// ============================================

function getRiskTier(equity: number): RiskTier {
  if (equity < 10000) return 'micro';
  if (equity < 100000) return 'small';
  if (equity < 1000000) return 'medium';
  return 'large';
}

function generateOrderId(): string {
  return `POS_${Date.now()}_${Math.random().toString(36).substring(2, 8)}`;
}

// ============================================
// Store 实现
// ============================================

let orderCounter = 0;

export const usePositionStore = create<PositionStoreState>((set, get) => ({
  // 初始状态
  equity: 10000,
  initial_equity: 10000,
  available_margin: 10000,
  open_orders: [],
  history: [],
  risk_tier: 'micro',
  algo_mode: 'simple',
  risk_profile: null,
  last_calculation: null,
  win_count: 0,
  loss_count: 0,
  daily_loss: 0,
  max_drawdown: 0,
  risk_slider_value: 50,
  connected: false,

  // 初始化
  initialize: (equity: number) => {
    const tier = getRiskTier(equity);
    const config = RISK_TIERS_CONFIG[tier];
    
    set({
      equity,
      initial_equity: equity,
      available_margin: equity,
      risk_tier: tier,
      risk_profile: {
        tier,
        tier_label: config.label,
        risk_per_trade_pct: config.risk_per_trade * 100,
        max_position_pct: config.max_position_pct * 100,
        risk_amount: equity * config.risk_per_trade,
        max_position: equity * config.max_position_pct,
        max_daily_loss: equity * config.max_daily_loss,
      },
      connected: true,
    });
  },

  // 仓位计算
  calculatePosition: (params) => {
    const state = get();
    const { equity, algo_mode, risk_tier } = state;
    const config = RISK_TIERS_CONFIG[risk_tier];
    
    const {
      symbol,
      side,
      entry_price,
      stop_loss_pct = 0.02,
      signal_confidence = 1.0,
      atr = 0,
      historical_win_rate = 0.55,
      reward_ratio = 1.5,
    } = params;
    
    let result: PositionResult;
    
    if (algo_mode === 'hybrid') {
      // ATR + 凯利 + 信心度 复合算法
      const risk_amount = equity * config.risk_per_trade;
      
      // ATR 仓位
      const atr_multiplier = 2.0;
      const stop_distance_pct = atr > 0 ? (atr / entry_price) * atr_multiplier : stop_loss_pct;
      const atr_position = stop_distance_pct > 0 ? risk_amount / stop_distance_pct : risk_amount;
      
      // 凯利仓位 (半凯利)
      const kelly_fraction = Math.max(0, Math.min(0.25, ((reward_ratio * historical_win_rate - (1 - historical_win_rate)) / reward_ratio) * 0.5));
      const kelly_position = equity * kelly_fraction;
      
      // 信心度仓位
      const confidence_position = equity * config.risk_per_trade * 3 * signal_confidence;
      
      // 加权平均
      const final_value = atr_position * 0.4 + kelly_position * 0.3 + confidence_position * 0.3;
      
      result = {
        position_value: Math.min(final_value, equity * config.max_position_pct),
        position_pct: Math.min(final_value / equity, config.max_position_pct),
        contracts: final_value / entry_price,
        risk_amount,
        risk_tier,
        algo_mode,
        methods: {
          atr: atr_position,
          kelly: kelly_position,
          confidence: confidence_position,
          weights: { atr: 0.4, kelly: 0.3, confidence: 0.3 },
        },
      };
    } else {
      // 简单动态百分比算法
      const risk_amount = equity * config.risk_per_trade;
      const position_value = stop_loss_pct > 0 ? risk_amount / stop_loss_pct : risk_amount;
      const adjusted_position = position_value * signal_confidence;
      const final_value = Math.min(adjusted_position, equity * config.max_position_pct);
      
      result = {
        position_value: final_value,
        position_pct: final_value / equity,
        contracts: final_value / entry_price,
        risk_amount,
        risk_tier,
        algo_mode,
      };
    }
    
    set({ last_calculation: result });
    return result;
  },

  // 创建订单
  createOrder: (order_data) => {
    const state = get();
    orderCounter++;
    
    const order: PositionOrder = {
      ...order_data,
      order_id: `POS_${String(orderCounter).padStart(6, '0')}_${order_data.symbol}_${Date.now()}`,
      unrealized_pnl: 0,
      unrealized_pnl_pct: 0,
      status: 'active',
    };
    
    set({
      open_orders: [...state.open_orders, order],
      equity: state.equity - order_data.position_value,
      available_margin: state.equity - order_data.position_value,
    });
    
    return order;
  },

  // 关闭订单
  closeOrder: (order_id, exit_price, reason = 'manual') => {
    const state = get();
    const order = state.open_orders.find(o => o.order_id === order_id);
    
    if (!order) return;
    
    // 计算盈亏
    const pnl = order.side === 'long'
      ? (exit_price - order.entry_price) * order.position_value / order.entry_price
      : (order.entry_price - exit_price) * order.position_value / order.entry_price;
    
    const pnl_pct = pnl / order.position_value;
    
    // 创建历史记录
    const historyEntry: PositionHistory = {
      history_id: `HIST_${order_id}`,
      symbol: order.symbol,
      side: order.side,
      position_pct: order.position_pct,
      entry_price: order.entry_price,
      exit_price,
      pnl,
      pnl_pct,
      risk_amount: order.risk_amount,
      exit_reason: reason,
      exit_time: Date.now(),
      holding_period: (Date.now() - order.timestamp) / 1000,
      algo_mode: state.algo_mode,
      risk_tier: state.risk_tier,
    };
    
    // 更新状态
    set({
      open_orders: state.open_orders.filter(o => o.order_id !== order_id),
      history: [historyEntry, ...state.history].slice(0, 50),
      equity: state.equity + order.position_value + pnl,
      win_count: pnl > 0 ? state.win_count + 1 : state.win_count,
      loss_count: pnl <= 0 ? state.loss_count + 1 : state.loss_count,
      daily_loss: pnl < 0 ? state.daily_loss + Math.abs(pnl) : state.daily_loss,
    });
  },

  // 设置算法模式
  setAlgoMode: (mode) => {
    set({ algo_mode: mode });
  },

  // 设置风险滑块
  setRiskSlider: (value) => {
    set({ risk_slider_value: value });
  },

  // 更新权益
  updateEquity: (new_equity) => {
    const state = get();
    const old_tier = state.risk_tier;
    const new_tier = getRiskTier(new_equity);
    const config = RISK_TIERS_CONFIG[new_tier];
    
    set({
      equity: new_equity,
      risk_tier: new_tier,
      risk_profile: {
        tier: new_tier,
        tier_label: config.label,
        risk_per_trade_pct: config.risk_per_trade * 100,
        max_position_pct: config.max_position_pct * 100,
        risk_amount: new_equity * config.risk_per_trade,
        max_position: new_equity * config.max_position_pct,
        max_daily_loss: new_equity * config.max_daily_loss,
      },
    });
  },

  // 重置日亏损
  resetDailyLoss: () => {
    set({ daily_loss: 0 });
  },

  // 重置所有
  resetAll: () => {
    const state = get();
    set({
      equity: state.initial_equity,
      available_margin: state.initial_equity,
      open_orders: [],
      history: [],
      win_count: 0,
      loss_count: 0,
      daily_loss: 0,
      max_drawdown: 0,
      last_calculation: null,
    });
  },
}));

// ============================================
// 选择器
// ============================================

export const useEquity = () => usePositionStore(state => state.equity);
export const useRiskTier = () => usePositionStore(state => state.risk_tier);
export const useAlgoMode = () => usePositionStore(state => state.algo_mode);
export const useRiskProfile = () => usePositionStore(state => state.risk_profile);
export const useLastCalculation = () => usePositionStore(state => state.last_calculation);
export const useOpenOrders = () => usePositionStore(state => state.open_orders);
export const usePositionHistory = () => usePositionStore(state => state.history);
export const useWinRate = () => usePositionStore(state => {
  const total = state.win_count + state.loss_count;
  return total > 0 ? state.win_count / total : 0;
});
export const useTotalPositionPct = () => usePositionStore(state => {
  const total_value = state.open_orders.reduce((sum, o) => sum + o.position_value, 0);
  return state.equity > 0 ? total_value / state.equity : 0;
});
