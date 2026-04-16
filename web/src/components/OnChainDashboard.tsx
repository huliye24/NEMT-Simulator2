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
 * NEMT 链上指标 Dashboard
 * 用于监控 MVRV、NUPL、流动性评分等核心指标
 * 支持从币安 API 自动获取 BTC 实时数据
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  TrendingUp,
  TrendingDown,
  Minus,
  Activity,
  BarChart3,
  PieChart,
  DollarSign,
  Clock,
  AlertTriangle,
  CheckCircle,
  Info,
  Edit2,
  Save,
  RefreshCw,
  ArrowUpRight,
  ArrowDownRight,
  Loader2,
} from 'lucide-react';

// =====================
// 类型定义
// =====================

export interface OnChainIndicators {
  // 市场全景指标
  mvrvScore: number;
  mvrvTrend: 'up' | 'down' | 'stable';
  nupl: number;
  nuplTrend: 'up' | 'down' | 'stable';

  // 供需结构
  exchangeBalance: 'increasing' | 'decreasing' | 'stable';
  lthSupplyPercent: number;
  sthSupplyPercent: number;
  stablecoinBalance: 'increasing' | 'decreasing' | 'stable';

  // 鲸鱼行为
  whaleFlow: 'inflow' | 'outflow' | 'neutral';
  minerFlow: 'high' | 'medium' | 'low';
  whaleAddressChange: 'increasing' | 'decreasing' | 'stable';

  // 宏观指标
  liquidityScore: number;
  realRate: number;
  halvingPhase: 'accumulation' | 'halving' | 'main_rally' | 'top';
  cycleDay: number;

  // BTC 价格
  btcPrice: number;
  btcChange24h: number;

  // 评分
  onChainScore: number;
  macroScore: number;

  // 时间戳
  lastUpdated: string;
  notes: string;
}

export const DEFAULT_INDICATORS: OnChainIndicators = {
  mvrvScore: 0,
  mvrvTrend: 'stable',
  nupl: 0,
  nuplTrend: 'stable',
  exchangeBalance: 'stable',
  lthSupplyPercent: 0,
  sthSupplyPercent: 0,
  stablecoinBalance: 'stable',
  whaleFlow: 'neutral',
  minerFlow: 'medium',
  whaleAddressChange: 'stable',
  liquidityScore: 5,
  realRate: 0,
  halvingPhase: 'accumulation',
  cycleDay: 0,
  btcPrice: 0,
  btcChange24h: 0,
  onChainScore: 5,
  macroScore: 5,
  lastUpdated: new Date().toISOString(),
  notes: '',
};

// =====================
// API 获取函数
// =====================

interface BinanceTicker {
  symbol: string;
  price: number;
  priceChange: number;
  priceChangePercent: number;
  high: number;
  low: number;
  volume: number;
  quoteVolume: number;
}

// 从币安获取 BTC 价格
const fetchBinancePrice = async (): Promise<BinanceTicker | null> => {
  try {
    const response = await fetch('https://api.binance.com/api/v3/ticker/24hr?symbol=BTCUSDT');
    if (!response.ok) throw new Error('API error');
    const data = await response.json();
    return {
      symbol: data.symbol,
      price: parseFloat(data.lastPrice),
      priceChange: parseFloat(data.priceChange),
      priceChangePercent: parseFloat(data.priceChangePercent),
      high: parseFloat(data.highPrice),
      low: parseFloat(data.lowPrice),
      volume: parseFloat(data.volume),
      quoteVolume: parseFloat(data.quoteVolume),
    };
  } catch (error) {
    console.error('Failed to fetch Binance price:', error);
    return null;
  }
};

// =====================
// 工具函数
// =====================

const loadIndicators = (): OnChainIndicators => {
  try {
    const saved = localStorage.getItem('nemt_indicators');
    return saved ? JSON.parse(saved) : DEFAULT_INDICATORS;
  } catch {
    return DEFAULT_INDICATORS;
  }
};

const saveIndicators = (indicators: OnChainIndicators) => {
  localStorage.setItem('nemt_indicators', JSON.stringify(indicators));
};

// =====================
// 评分计算
// =====================

const calculateOnChainScore = (indicators: OnChainIndicators): number => {
  let score = 0;

  // MVRV Z-score (+2/1/0)
  if (indicators.mvrvScore < 1) score += 2;
  else if (indicators.mvrvScore <= 3) score += 1;

  // NUPL (+2/1/0)
  if (indicators.nupl < 0.25) score += 2;
  else if (indicators.nupl <= 0.5) score += 1;

  // 交易所余额 (+2/1/0)
  if (indicators.exchangeBalance === 'decreasing') score += 2;
  else if (indicators.exchangeBalance === 'stable') score += 1;

  // LTH供应占比变化 (+2/1/0)
  if (indicators.lthSupplyPercent > 65) score += 2;
  else if (indicators.lthSupplyPercent > 55) score += 1;

  // 稳定币余额 (+2/1/0)
  if (indicators.stablecoinBalance === 'increasing') score += 2;
  else if (indicators.stablecoinBalance === 'stable') score += 1;

  // 鲸鱼流量 (+2/1/0)
  if (indicators.whaleFlow === 'outflow') score += 2;
  else if (indicators.whaleFlow === 'neutral') score += 1;

  return score;
};

const calculateMacroScore = (indicators: OnChainIndicators): number => {
  let score = 5;

  // 流动性评分
  if (indicators.liquidityScore >= 7) score = 9;
  else if (indicators.liquidityScore >= 6) score = 8;
  else if (indicators.liquidityScore >= 5) score = 6;
  else if (indicators.liquidityScore >= 4) score = 5;
  else if (indicators.liquidityScore >= 3) score = 3;
  else score = 2;

  return score;
};

// =====================
// 子组件
// =====================

/** 趋势指示器 */
const TrendIndicator: React.FC<{ trend: 'up' | 'down' | 'stable' }> = ({ trend }) => {
  const config = {
    up: { icon: <ArrowUpRight size={14} />, color: '#10b981', bg: '#d1fae5' },
    down: { icon: <ArrowDownRight size={14} />, color: '#ef4444', bg: '#fee2e2' },
    stable: { icon: <Minus size={14} />, color: '#6b7280', bg: '#f3f4f6' },
  };
  const c = config[trend];
  return (
    <span style={{
      display: 'inline-flex',
      alignItems: 'center',
      justifyContent: 'center',
      width: '22px',
      height: '22px',
      borderRadius: '4px',
      background: c.bg,
      color: c.color,
    }}>
      {c.icon}
    </span>
  );
};

/** 指标卡片 */
interface MetricCardProps {
  label: string;
  value: string | number;
  unit?: string;
  trend?: 'up' | 'down' | 'stable';
  status?: 'bullish' | 'bearish' | 'neutral';
  description?: string;
  icon?: React.ReactNode;
}

const MetricCard: React.FC<MetricCardProps> = ({
  label,
  value,
  unit,
  trend,
  status = 'neutral',
  description,
  icon,
}) => {
  const statusColors = {
    bullish: { bg: '#d1fae5', border: '#10b981', text: '#059669' },
    bearish: { bg: '#fee2e2', border: '#ef4444', text: '#dc2626' },
    neutral: { bg: '#f3f4f6', border: '#6b7280', text: '#6b7280' },
  };
  const colors = statusColors[status];

  return (
    <div style={{
      background: 'white',
      borderRadius: '12px',
      padding: '16px',
      border: `2px solid ${colors.border}`,
      boxShadow: '0 2px 8px rgba(0,0,0,0.06)',
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '8px' }}>
        <span style={{ fontSize: '12px', color: '#6b7280', fontWeight: 500 }}>{label}</span>
        {icon && <span style={{ color: colors.text }}>{icon}</span>}
      </div>
      <div style={{ display: 'flex', alignItems: 'baseline', gap: '4px' }}>
        <span style={{ fontSize: '24px', fontWeight: 700, color: colors.text }}>
          {typeof value === 'number' ? value.toLocaleString() : value}
        </span>
        {unit && <span style={{ fontSize: '14px', color: '#6b7280' }}>{unit}</span>}
        {trend && <TrendIndicator trend={trend} />}
      </div>
      {description && (
        <p style={{ fontSize: '11px', color: '#9ca3af', margin: '8px 0 0', lineHeight: 1.4 }}>
          {description}
        </p>
      )}
    </div>
  );
};

/** 评分仪表 */
interface ScoreGaugeProps {
  label: string;
  score: number;
  maxScore?: number;
  thresholds?: { green: number; yellow: number };
}

const ScoreGauge: React.FC<ScoreGaugeProps> = ({
  label,
  score,
  maxScore = 10,
  thresholds = { green: 7, yellow: 4 },
}) => {
  const percentage = (score / maxScore) * 100;
  const color = score >= thresholds.green ? '#10b981' : score >= thresholds.yellow ? '#f59e0b' : '#ef4444';
  const bgColor = score >= thresholds.green ? '#d1fae5' : score >= thresholds.yellow ? '#fef3c7' : '#fee2e2';

  return (
    <div style={{
      background: 'white',
      borderRadius: '12px',
      padding: '20px',
      textAlign: 'center',
      boxShadow: '0 2px 8px rgba(0,0,0,0.06)',
    }}>
      <div style={{ fontSize: '12px', color: '#6b7280', marginBottom: '12px', fontWeight: 500 }}>
        {label}
      </div>
      <div style={{ position: 'relative', width: '120px', height: '120px', margin: '0 auto' }}>
        <svg viewBox="0 0 120 120" style={{ transform: 'rotate(-90deg)' }}>
          <circle
            cx="60"
            cy="60"
            r="50"
            fill="none"
            stroke="#e5e7eb"
            strokeWidth="10"
          />
          <circle
            cx="60"
            cy="60"
            r="50"
            fill="none"
            stroke={color}
            strokeWidth="10"
            strokeLinecap="round"
            strokeDasharray={`${(percentage / 100) * 314} 314`}
            style={{ transition: 'stroke-dasharray 0.5s ease' }}
          />
        </svg>
        <div style={{
          position: 'absolute',
          top: '50%',
          left: '50%',
          transform: 'translate(-50%, -50%)',
          textAlign: 'center',
        }}>
          <span style={{ fontSize: '32px', fontWeight: 800, color }}>{score}</span>
          <span style={{ fontSize: '14px', color: '#9ca3af' }}>/{maxScore}</span>
        </div>
      </div>
      <div style={{
        marginTop: '12px',
        padding: '4px 12px',
        borderRadius: '20px',
        background: bgColor,
        color: color,
        fontSize: '12px',
        fontWeight: 600,
        display: 'inline-block',
      }}>
        {score >= thresholds.green ? '健康' : score >= thresholds.yellow ? '一般' : '需关注'}
      </div>
    </div>
  );
};

/** 状态指示器 */
interface StatusIndicatorProps {
  label: string;
  value: string;
  options: { value: string; color: string; bgColor: string; icon?: React.ReactNode }[];
}

const StatusIndicator: React.FC<StatusIndicatorProps> = ({ label, value, options }) => {
  const current = options.find(o => o.value === value) || options[0];
  return (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      padding: '12px 16px',
      background: current.bgColor,
      borderRadius: '8px',
    }}>
      <span style={{ fontSize: '13px', color: '#374151', fontWeight: 500 }}>{label}</span>
      <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
        {current.icon}
        <span style={{ fontSize: '13px', color: current.color, fontWeight: 600 }}>
          {current.value}
        </span>
      </div>
    </div>
  );
};

/** 编辑表单 */
interface EditFormProps {
  indicators: OnChainIndicators;
  onSave: (indicators: OnChainIndicators) => void;
  onCancel: () => void;
}

const EditForm: React.FC<EditFormProps> = ({ indicators, onSave, onCancel }) => {
  const [form, setForm] = useState(indicators);

  const handleSave = () => {
    const updated = {
      ...form,
      onChainScore: calculateOnChainScore(form),
      macroScore: calculateMacroScore(form),
      lastUpdated: new Date().toISOString(),
    };
    onSave(updated);
  };

  const updateField = (field: keyof OnChainIndicators, value: any) => {
    setForm(prev => ({ ...prev, [field]: value }));
  };

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      background: 'rgba(0,0,0,0.5)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 1000,
      padding: '20px',
    }}>
      <div style={{
        background: 'white',
        borderRadius: '16px',
        padding: '24px',
        width: '100%',
        maxWidth: '600px',
        maxHeight: '90vh',
        overflow: 'auto',
        boxShadow: '0 20px 60px rgba(0,0,0,0.2)',
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
          <h3 style={{ margin: 0, fontSize: '18px', fontWeight: 600 }}>更新指标数据</h3>
          <button onClick={onCancel} style={{ padding: '4px', border: 'none', background: 'none', cursor: 'pointer', color: '#6b7280' }}>
            <Edit2 size={20} />
          </button>
        </div>

        <div style={{ display: 'grid', gap: '20px' }}>
          {/* BTC 价格 */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
            <div>
              <label style={{ display: 'block', fontSize: '12px', fontWeight: 500, marginBottom: '4px', color: '#374151' }}>
                BTC 价格 (USD)
              </label>
              <input
                type="number"
                value={form.btcPrice}
                onChange={(e) => updateField('btcPrice', parseFloat(e.target.value) || 0)}
                style={{ width: '100%', padding: '10px', border: '2px solid #e5e7eb', borderRadius: '8px', fontSize: '14px' }}
              />
            </div>
            <div>
              <label style={{ display: 'block', fontSize: '12px', fontWeight: 500, marginBottom: '4px', color: '#374151' }}>
                24h 涨跌幅 (%)
              </label>
              <input
                type="number"
                step="0.01"
                value={form.btcChange24h}
                onChange={(e) => updateField('btcChange24h', parseFloat(e.target.value) || 0)}
                style={{ width: '100%', padding: '10px', border: '2px solid #e5e7eb', borderRadius: '8px', fontSize: '14px' }}
              />
            </div>
          </div>

          {/* MVRV & NUPL */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
            <div>
              <label style={{ display: 'block', fontSize: '12px', fontWeight: 500, marginBottom: '4px', color: '#374151' }}>
                MVRV Z-score
              </label>
              <input
                type="number"
                step="0.1"
                value={form.mvrvScore}
                onChange={(e) => updateField('mvrvScore', parseFloat(e.target.value) || 0)}
                style={{ width: '100%', padding: '10px', border: '2px solid #e5e7eb', borderRadius: '8px', fontSize: '14px' }}
              />
            </div>
            <div>
              <label style={{ display: 'block', fontSize: '12px', fontWeight: 500, marginBottom: '4px', color: '#374151' }}>
                NUPL (0-1)
              </label>
              <input
                type="number"
                step="0.01"
                min="0"
                max="1"
                value={form.nupl}
                onChange={(e) => updateField('nupl', Math.min(1, Math.max(0, parseFloat(e.target.value) || 0)))}
                style={{ width: '100%', padding: '10px', border: '2px solid #e5e7eb', borderRadius: '8px', fontSize: '14px' }}
              />
            </div>
          </div>

          {/* 供应分布 */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
            <div>
              <label style={{ display: 'block', fontSize: '12px', fontWeight: 500, marginBottom: '4px', color: '#374151' }}>
                LTH 供应占比 (%)
              </label>
              <input
                type="number"
                step="0.1"
                value={form.lthSupplyPercent}
                onChange={(e) => updateField('lthSupplyPercent', parseFloat(e.target.value) || 0)}
                style={{ width: '100%', padding: '10px', border: '2px solid #e5e7eb', borderRadius: '8px', fontSize: '14px' }}
              />
            </div>
            <div>
              <label style={{ display: 'block', fontSize: '12px', fontWeight: 500, marginBottom: '4px', color: '#374151' }}>
                STH 供应占比 (%)
              </label>
              <input
                type="number"
                step="0.1"
                value={form.sthSupplyPercent}
                onChange={(e) => updateField('sthSupplyPercent', parseFloat(e.target.value) || 0)}
                style={{ width: '100%', padding: '10px', border: '2px solid #e5e7eb', borderRadius: '8px', fontSize: '14px' }}
              />
            </div>
          </div>

          {/* 流动性评分 */}
          <div>
            <label style={{ display: 'block', fontSize: '12px', fontWeight: 500, marginBottom: '4px', color: '#374151' }}>
              流动性评分 (0-10)
            </label>
            <input
              type="range"
              min="0"
              max="10"
              step="0.5"
              value={form.liquidityScore}
              onChange={(e) => updateField('liquidityScore', parseFloat(e.target.value))}
              style={{ width: '100%' }}
            />
            <div style={{ textAlign: 'center', fontSize: '14px', fontWeight: 600, color: form.liquidityScore >= 7 ? '#10b981' : form.liquidityScore >= 4 ? '#f59e0b' : '#ef4444' }}>
              {form.liquidityScore.toFixed(1)}
            </div>
          </div>

          {/* 实际利率 */}
          <div>
            <label style={{ display: 'block', fontSize: '12px', fontWeight: 500, marginBottom: '4px', color: '#374151' }}>
              10年期实际利率 (%)
            </label>
            <input
              type="number"
              step="0.01"
              value={form.realRate}
              onChange={(e) => updateField('realRate', parseFloat(e.target.value) || 0)}
              style={{ width: '100%', padding: '10px', border: '2px solid #e5e7eb', borderRadius: '8px', fontSize: '14px' }}
            />
          </div>

          {/* 选择性指标 */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
            <div>
              <label style={{ display: 'block', fontSize: '12px', fontWeight: 500, marginBottom: '4px', color: '#374151' }}>
                交易所余额趋势
              </label>
              <select
                value={form.exchangeBalance}
                onChange={(e) => updateField('exchangeBalance', e.target.value)}
                style={{ width: '100%', padding: '10px', border: '2px solid #e5e7eb', borderRadius: '8px', fontSize: '14px' }}
              >
                <option value="decreasing">下降</option>
                <option value="stable">稳定</option>
                <option value="increasing">上升</option>
              </select>
            </div>
            <div>
              <label style={{ display: 'block', fontSize: '12px', fontWeight: 500, marginBottom: '4px', color: '#374151' }}>
                稳定币余额趋势
              </label>
              <select
                value={form.stablecoinBalance}
                onChange={(e) => updateField('stablecoinBalance', e.target.value)}
                style={{ width: '100%', padding: '10px', border: '2px solid #e5e7eb', borderRadius: '8px', fontSize: '14px' }}
              >
                <option value="increasing">上升</option>
                <option value="stable">稳定</option>
                <option value="decreasing">下降</option>
              </select>
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
            <div>
              <label style={{ display: 'block', fontSize: '12px', fontWeight: 500, marginBottom: '4px', color: '#374151' }}>
                鲸鱼流量
              </label>
              <select
                value={form.whaleFlow}
                onChange={(e) => updateField('whaleFlow', e.target.value)}
                style={{ width: '100%', padding: '10px', border: '2px solid #e5e7eb', borderRadius: '8px', fontSize: '14px' }}
              >
                <option value="outflow">净流出</option>
                <option value="neutral">中性</option>
                <option value="inflow">净流入</option>
              </select>
            </div>
            <div>
              <label style={{ display: 'block', fontSize: '12px', fontWeight: 500, marginBottom: '4px', color: '#374151' }}>
                减半周期阶段
              </label>
              <select
                value={form.halvingPhase}
                onChange={(e) => updateField('halvingPhase', e.target.value)}
                style={{ width: '100%', padding: '10px', border: '2px solid #e5e7eb', borderRadius: '8px', fontSize: '14px' }}
              >
                <option value="accumulation">积累期</option>
                <option value="halving">减半期</option>
                <option value="main_rally">主升浪</option>
                <option value="top">顶部区域</option>
              </select>
            </div>
          </div>

          {/* 备注 */}
          <div>
            <label style={{ display: 'block', fontSize: '12px', fontWeight: 500, marginBottom: '4px', color: '#374151' }}>
              备注
            </label>
            <textarea
              value={form.notes}
              onChange={(e) => updateField('notes', e.target.value)}
              placeholder="添加分析备注..."
              rows={3}
              style={{ width: '100%', padding: '10px', border: '2px solid #e5e7eb', borderRadius: '8px', fontSize: '14px', resize: 'vertical' }}
            />
          </div>
        </div>

        {/* 按钮 */}
        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px', marginTop: '24px' }}>
          <button
            onClick={onCancel}
            style={{
              padding: '12px 24px',
              borderRadius: '8px',
              border: '2px solid #e5e7eb',
              background: 'white',
              cursor: 'pointer',
              fontSize: '14px',
              fontWeight: 500,
              color: '#6b7280',
            }}
          >
            取消
          </button>
          <button
            onClick={handleSave}
            style={{
              padding: '12px 24px',
              borderRadius: '8px',
              border: 'none',
              background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
              color: 'white',
              cursor: 'pointer',
              fontSize: '14px',
              fontWeight: 600,
              boxShadow: '0 4px 12px rgba(16, 185, 129, 0.3)',
            }}
          >
            <Save size={14} style={{ marginRight: '6px', verticalAlign: 'middle' }} />
            保存数据
          </button>
        </div>
      </div>
    </div>
  );
};

// =====================
// 主组件
// =====================

export const OnChainDashboard: React.FC = () => {
  const [indicators, setIndicators] = useState<OnChainIndicators>(() => loadIndicators());
  const [showEditForm, setShowEditForm] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [lastApiUpdate, setLastApiUpdate] = useState<string | null>(null);

  // 从币安获取 BTC 数据
  const fetchMarketData = useCallback(async () => {
    setIsLoading(true);
    try {
      const ticker = await fetchBinancePrice();
      if (ticker) {
        const updated = {
          ...indicators,
          btcPrice: ticker.price,
          btcChange24h: ticker.priceChangePercent,
          lastUpdated: new Date().toISOString(),
        };
        setIndicators(updated);
        saveIndicators(updated);
        setLastApiUpdate(new Date().toLocaleTimeString('zh-CN'));
      }
    } catch (error) {
      console.error('Failed to fetch market data:', error);
    }
    setIsLoading(false);
  }, [indicators]);

  // 组件加载时获取一次数据
  useEffect(() => {
    fetchMarketData();
  }, []);

  // 保存数据（仅手动更新）
  const handleSave = useCallback((newIndicators: OnChainIndicators) => {
    setIndicators(newIndicators);
    saveIndicators(newIndicators);
    setShowEditForm(false);
  }, []);

  // 计算当前评分
  const calculatedOnChainScore = calculateOnChainScore(indicators);
  const calculatedMacroScore = calculateMacroScore(indicators);

  // 获取 MVRV 状态
  const getMvrvStatus = (): 'bullish' | 'bearish' | 'neutral' => {
    if (indicators.mvrvScore < 0) return 'bullish';
    if (indicators.mvrvScore > 7) return 'bearish';
    if (indicators.mvrvScore > 5) return 'neutral';
    return 'neutral';
  };

  // 获取 NUPL 状态
  const getNuplStatus = (): 'bullish' | 'bearish' | 'neutral' => {
    if (indicators.nupl < 0.25) return 'bullish';
    if (indicators.nupl > 0.75) return 'bearish';
    if (indicators.nupl > 0.5) return 'neutral';
    return 'neutral';
  };

  // 获取 NUPL 阶段名称
  const getNuplPhase = (): string => {
    if (indicators.nupl < 0) return '投降';
    if (indicators.nupl < 0.25) return '希望/恐惧';
    if (indicators.nupl < 0.5) return '乐观/焦虑';
    if (indicators.nupl < 0.75) return '信念/否认';
    return '欣快/贪婪';
  };

  // 获取减半阶段名称
  const getHalvingPhaseName = (): string => {
    const phases: Record<string, string> = {
      accumulation: '积累期',
      halving: '减半期',
      main_rally: '主升浪',
      top: '顶部区域',
    };
    return phases[indicators.halvingPhase] || '未知';
  };

  return (
    <div style={{ minHeight: '100vh', background: '#f8fafc', padding: '24px' }}>
      {/* 顶部标题栏 */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: '24px',
        flexWrap: 'wrap',
        gap: '16px',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{
            width: '40px',
            height: '40px',
            borderRadius: '10px',
            background: 'linear-gradient(135deg, #8b5cf6 0%, #6d28d9 100%)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: 'white',
          }}>
            <Activity size={22} />
          </div>
          <div>
            <h1 style={{ margin: 0, fontSize: '24px', fontWeight: 700, color: '#1f2937' }}>
              NEMT 链上指标
            </h1>
            <p style={{ margin: '2px 0 0', fontSize: '13px', color: '#9ca3af' }}>
              宏观-链上二维决策矩阵
            </p>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{ fontSize: '12px', color: '#6b7280' }}>
            <Clock size={12} style={{ verticalAlign: 'middle', marginRight: '4px' }} />
            {lastApiUpdate ? `BTC 更新于 ${lastApiUpdate}` : 'BTC 价格'}
          </div>
          <button
            onClick={fetchMarketData}
            disabled={isLoading}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              padding: '8px 12px',
              border: '2px solid #e5e7eb',
              borderRadius: '8px',
              background: isLoading ? '#f3f4f6' : 'white',
              cursor: isLoading ? 'not-allowed' : 'pointer',
              fontSize: '12px',
              fontWeight: 500,
              color: '#374151',
            }}
          >
            <RefreshCw size={12} className={isLoading ? 'animate-spin' : ''} />
            {isLoading ? '刷新中...' : '刷新'}
          </button>
          <button
            onClick={() => setShowEditForm(true)}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              padding: '10px 16px',
              border: '2px solid #e5e7eb',
              borderRadius: '8px',
              background: 'white',
              cursor: 'pointer',
              fontSize: '13px',
              fontWeight: 500,
              color: '#374151',
            }}
          >
            <Edit2 size={14} />
            更新数据
          </button>
        </div>
      </div>

      {/* 核心评分 */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
        gap: '16px',
        marginBottom: '24px',
      }}>
        <ScoreGauge label="链上健康度" score={calculatedOnChainScore} thresholds={{ green: 8, yellow: 5 }} />
        <ScoreGauge label="宏观流动性" score={calculatedMacroScore} thresholds={{ green: 7, yellow: 4 }} />
        
        {/* 综合评分 */}
        <div style={{
          background: 'white',
          borderRadius: '12px',
          padding: '20px',
          textAlign: 'center',
          boxShadow: '0 2px 8px rgba(0,0,0,0.06)',
          border: `2px solid ${calculatedOnChainScore + calculatedMacroScore >= 14 ? '#10b981' : calculatedOnChainScore + calculatedMacroScore >= 8 ? '#f59e0b' : '#ef4444'}`,
        }}>
          <div style={{ fontSize: '12px', color: '#6b7280', marginBottom: '12px', fontWeight: 500 }}>
            综合评分
          </div>
          <div style={{ fontSize: '48px', fontWeight: 800, color: calculatedOnChainScore + calculatedMacroScore >= 14 ? '#10b981' : calculatedOnChainScore + calculatedMacroScore >= 8 ? '#f59e0b' : '#ef4444' }}>
            {calculatedOnChainScore + calculatedMacroScore}
          </div>
          <div style={{ fontSize: '14px', color: '#9ca3af', marginTop: '8px' }}>
            /20
          </div>
          <div style={{
            marginTop: '12px',
            padding: '4px 12px',
            borderRadius: '20px',
            background: calculatedOnChainScore + calculatedMacroScore >= 14 ? '#d1fae5' : calculatedOnChainScore + calculatedMacroScore >= 8 ? '#fef3c7' : '#fee2e2',
            color: calculatedOnChainScore + calculatedMacroScore >= 14 ? '#059669' : calculatedOnChainScore + calculatedMacroScore >= 8 ? '#d97706' : '#dc2626',
            fontSize: '12px',
            fontWeight: 600,
          }}>
            {calculatedOnChainScore + calculatedMacroScore >= 14 ? '积极做多' : calculatedOnChainScore + calculatedMacroScore >= 8 ? '中性观望' : '降低风险'}
          </div>
        </div>
      </div>

      {/* BTC 价格 & 市场全景 */}
      <div style={{ marginBottom: '24px' }}>
        <h3 style={{ fontSize: '14px', fontWeight: 600, color: '#374151', marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <DollarSign size={16} />
          市场概况
        </h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '12px' }}>
          <MetricCard
            label="BTC 价格"
            value={indicators.btcPrice > 0 ? `$${indicators.btcPrice.toLocaleString()}` : '—'}
            status={indicators.btcChange24h > 0 ? 'bullish' : indicators.btcChange24h < 0 ? 'bearish' : 'neutral'}
            icon={<DollarSign size={16} />}
          />
          <MetricCard
            label="24h 涨跌"
            value={indicators.btcChange24h > 0 ? `+${indicators.btcChange24h.toFixed(2)}%` : `${indicators.btcChange24h.toFixed(2)}%`}
            trend={indicators.btcChange24h > 0 ? 'up' : indicators.btcChange24h < 0 ? 'down' : 'stable'}
            status={indicators.btcChange24h > 0 ? 'bullish' : indicators.btcChange24h < 0 ? 'bearish' : 'neutral'}
            icon={indicators.btcChange24h > 0 ? <TrendingUp size={16} /> : <TrendingDown size={16} />}
          />
          <MetricCard
            label="减半周期"
            value={getHalvingPhaseName()}
            status="neutral"
          />
          <MetricCard
            label="实际利率"
            value={`${indicators.realRate.toFixed(2)}%`}
            status={indicators.realRate < 0 ? 'bullish' : indicators.realRate > 1 ? 'bearish' : 'neutral'}
          />
        </div>
      </div>

      {/* MVRV & NUPL */}
      <div style={{ marginBottom: '24px' }}>
        <h3 style={{ fontSize: '14px', fontWeight: 600, color: '#374151', marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <BarChart3 size={16} />
          市场全景指标
        </h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '12px' }}>
          {/* MVRV */}
          <div style={{ background: 'white', borderRadius: '12px', padding: '20px', boxShadow: '0 2px 8px rgba(0,0,0,0.06)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <span style={{ fontSize: '14px', fontWeight: 600, color: '#374151' }}>MVRV Z-score</span>
              <TrendIndicator trend={indicators.mvrvTrend} />
            </div>
            <div style={{ fontSize: '36px', fontWeight: 800, color: getMvrvStatus() === 'bullish' ? '#10b981' : getMvrvStatus() === 'bearish' ? '#ef4444' : '#6b7280' }}>
              {indicators.mvrvScore.toFixed(2)}
            </div>
            <div style={{ marginTop: '12px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', color: '#6b7280', marginBottom: '4px' }}>
                <span>底部区</span>
                <span>顶部区</span>
              </div>
              <div style={{ height: '8px', background: '#e5e7eb', borderRadius: '4px', position: 'relative' }}>
                <div style={{
                  position: 'absolute',
                  left: '50%',
                  top: '-4px',
                  width: '4px',
                  height: '16px',
                  background: '#374151',
                  borderRadius: '2px',
                  transform: `translateX(${Math.min(Math.max(indicators.mvrvScore / 10, 0), 1) * 100 - 50}%)`,
                }} />
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '10px', color: '#9ca3af', marginTop: '4px' }}>
                <span>&lt;0 底部</span>
                <span>&gt;7 顶部</span>
              </div>
            </div>
          </div>

          {/* NUPL */}
          <div style={{ background: 'white', borderRadius: '12px', padding: '20px', boxShadow: '0 2px 8px rgba(0,0,0,0.06)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <span style={{ fontSize: '14px', fontWeight: 600, color: '#374151' }}>NUPL</span>
              <TrendIndicator trend={indicators.nuplTrend} />
            </div>
            <div style={{ fontSize: '36px', fontWeight: 800, color: getNuplStatus() === 'bullish' ? '#10b981' : getNuplStatus() === 'bearish' ? '#ef4444' : '#6b7280' }}>
              {indicators.nupl.toFixed(2)}
            </div>
            <div style={{ marginTop: '8px', fontSize: '13px', fontWeight: 600, color: getNuplStatus() === 'bullish' ? '#10b981' : getNuplStatus() === 'bearish' ? '#ef4444' : '#6b7280' }}>
              {getNuplPhase()}
            </div>
            <div style={{ marginTop: '12px', display: 'flex', flexWrap: 'wrap', gap: '4px' }}>
              {[
                { label: '投降', max: 0, color: '#ef4444' },
                { label: '希望', max: 0.25, color: '#f59e0b' },
                { label: '乐观', max: 0.5, color: '#eab308' },
                { label: '信念', max: 0.75, color: '#22c55e' },
                { label: '贪婪', max: 1, color: '#dc2626' },
              ].map(phase => (
                <div
                  key={phase.label}
                  style={{
                    padding: '2px 8px',
                    borderRadius: '4px',
                    background: indicators.nupl <= phase.max ? phase.color + '30' : '#f3f4f6',
                    color: indicators.nupl <= phase.max ? phase.color : '#9ca3af',
                    fontSize: '10px',
                    fontWeight: indicators.nupl <= phase.max ? 600 : 400,
                  }}
                >
                  {phase.label}
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* 供需结构 */}
      <div style={{ marginBottom: '24px' }}>
        <h3 style={{ fontSize: '14px', fontWeight: 600, color: '#374151', marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <PieChart size={16} />
          供需结构
        </h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '12px' }}>
          <StatusIndicator
            label="交易所余额"
            value={indicators.exchangeBalance}
            options={[
              { value: '下降', color: '#10b981', bgColor: '#d1fae5' },
              { value: '稳定', color: '#6b7280', bgColor: '#f3f4f6' },
              { value: '上升', color: '#ef4444', bgColor: '#fee2e2' },
            ]}
          />
          <StatusIndicator
            label="稳定币余额"
            value={indicators.stablecoinBalance}
            options={[
              { value: '上升（弹药充足）', color: '#10b981', bgColor: '#d1fae5' },
              { value: '稳定', color: '#6b7280', bgColor: '#f3f4f6' },
              { value: '下降', color: '#ef4444', bgColor: '#fee2e2' },
            ]}
          />
        </div>
        <div style={{ marginTop: '12px', display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '12px' }}>
          <MetricCard
            label="LTH 供应占比"
            value={`${indicators.lthSupplyPercent.toFixed(1)}%`}
            status={indicators.lthSupplyPercent > 65 ? 'bullish' : indicators.lthSupplyPercent < 50 ? 'bearish' : 'neutral'}
            description="长期持有者持有比例"
            icon={<Activity size={16} />}
          />
          <MetricCard
            label="STH 供应占比"
            value={`${indicators.sthSupplyPercent.toFixed(1)}%`}
            status={indicators.sthSupplyPercent > 40 ? 'bearish' : 'neutral'}
            description="短期持有者持有比例"
          />
        </div>
      </div>

      {/* 鲸鱼行为 */}
      <div style={{ marginBottom: '24px' }}>
        <h3 style={{ fontSize: '14px', fontWeight: 600, color: '#374151', marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Activity size={16} />
          鲸鱼行为
        </h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '12px' }}>
          <StatusIndicator
            label="鲸鱼交易所流量"
            value={indicators.whaleFlow}
            options={[
              { value: '净流出（积累）', color: '#10b981', bgColor: '#d1fae5' },
              { value: '中性', color: '#6b7280', bgColor: '#f3f4f6' },
              { value: '净流入（派发）', color: '#ef4444', bgColor: '#fee2e2' },
            ]}
          />
          <StatusIndicator
            label="矿工流出量"
            value={indicators.minerFlow}
            options={[
              { value: '低位（供给压力小）', color: '#10b981', bgColor: '#d1fae5' },
              { value: '中等', color: '#f59e0b', bgColor: '#fef3c7' },
              { value: '高位（矿工投降风险）', color: '#ef4444', bgColor: '#fee2e2' },
            ]}
          />
        </div>
      </div>

      {/* 备注 */}
      {indicators.notes && (
        <div style={{
          background: 'white',
          borderRadius: '12px',
          padding: '16px',
          boxShadow: '0 2px 8px rgba(0,0,0,0.06)',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
            <Info size={14} color="#6b7280" />
            <span style={{ fontSize: '12px', fontWeight: 600, color: '#6b7280' }}>分析备注</span>
          </div>
          <p style={{ fontSize: '14px', color: '#374151', margin: 0, lineHeight: 1.6 }}>
            {indicators.notes}
          </p>
        </div>
      )}

      {/* NEMT 决策规则提示 */}
      <div style={{
        marginTop: '24px',
        background: 'linear-gradient(135deg, #fef3c7 0%, #fde68a 100%)',
        borderRadius: '12px',
        padding: '20px',
        border: '1px solid #f59e0b',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
          <AlertTriangle size={18} color="#d97706" />
          <span style={{ fontSize: '14px', fontWeight: 600, color: '#92400e' }}>NEMT 决策规则</span>
        </div>
        <div style={{ display: 'grid', gap: '8px', fontSize: '13px', color: '#78350f' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <CheckCircle size={14} color="#10b981" />
            链上评分≥8 + 宏观评分≥7：满仓操作
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <CheckCircle size={14} color="#10b981" />
            链上评分6-8 + 宏观评分6-7：标准仓位
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <AlertTriangle size={14} color="#f59e0b" />
            综合评分4-8：中性仓位，等待方向
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <AlertTriangle size={14} color="#ef4444" />
            综合评分≤4：降低仓位或空仓
          </div>
        </div>
      </div>

      {/* 编辑表单 */}
      {showEditForm && (
        <EditForm
          indicators={indicators}
          onSave={handleSave}
          onCancel={() => setShowEditForm(false)}
        />
      )}
    </div>
  );
};

export default OnChainDashboard;
