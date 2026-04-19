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
 * NEMT Dashboard - 核心可视化组件
 * 包含：频谱分析图、四相位状态机、信号历史记录
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
  Zap,
  Target,
  Radio,
  ArrowRight,
  Circle,
} from 'lucide-react';
import { Chart as ChartJS, CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend, Filler } from 'chart.js';
import { Line } from 'react-chartjs-2';
import { signalHistory, TradingSignal, getPipelineService } from '../services/nemtPipeline';
import { MarketPhase, PHASE_STRATEGIES, PhaseStrategy } from '../types/nemt';

// 注册 Chart.js 组件
ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend, Filler);

// =====================
// 类型定义
// =====================

export interface OnChainIndicators {
  mvrvScore: number;
  mvrvTrend: 'up' | 'down' | 'stable';
  nupl: number;
  nuplTrend: 'up' | 'down' | 'stable';
  exchangeBalance: 'increasing' | 'decreasing' | 'stable';
  lthSupplyPercent: number;
  sthSupplyPercent: number;
  stablecoinBalance: 'increasing' | 'decreasing' | 'stable';
  whaleFlow: 'inflow' | 'outflow' | 'neutral';
  minerFlow: 'high' | 'medium' | 'low';
  whaleAddressChange: 'increasing' | 'decreasing' | 'stable';
  liquidityScore: number;
  realRate: number;
  halvingPhase: 'accumulation' | 'halving' | 'main_rally' | 'top';
  cycleDay: number;
  btcPrice: number;
  btcChange24h: number;
  onChainScore: number;
  macroScore: number;
  lastUpdated: string;
  notes: string;
}

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

const DEFAULT_INDICATORS: OnChainIndicators = {
  mvrvScore: 0, mvrvTrend: 'stable', nupl: 0, nuplTrend: 'stable',
  exchangeBalance: 'stable', lthSupplyPercent: 0, sthSupplyPercent: 0,
  stablecoinBalance: 'stable', whaleFlow: 'neutral', minerFlow: 'medium',
  whaleAddressChange: 'stable', liquidityScore: 5, realRate: 0,
  halvingPhase: 'accumulation', cycleDay: 0, btcPrice: 0, btcChange24h: 0,
  onChainScore: 5, macroScore: 5, lastUpdated: new Date().toISOString(), notes: '',
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
    <span style={{ display: 'inline-flex', alignItems: 'center', justifyContent: 'center', width: '22px', height: '22px', borderRadius: '4px', background: c.bg, color: c.color }}>
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

const MetricCard: React.FC<MetricCardProps> = ({ label, value, unit, trend, status = 'neutral', description, icon }) => {
  const statusColors = {
    bullish: { bg: '#d1fae5', border: '#10b981', text: '#059669' },
    bearish: { bg: '#fee2e2', border: '#ef4444', text: '#dc2626' },
    neutral: { bg: '#f3f4f6', border: '#6b7280', text: '#6b7280' },
  };
  const colors = statusColors[status];

  return (
    <div style={{ background: 'white', borderRadius: '12px', padding: '16px', border: `2px solid ${colors.border}`, boxShadow: '0 2px 8px rgba(0,0,0,0.06)' }}>
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
      {description && <p style={{ fontSize: '11px', color: '#9ca3af', margin: '8px 0 0', lineHeight: 1.4 }}>{description}</p>}
    </div>
  );
};

// =====================
// 核心可视化组件
// =====================

/**
 * 频谱分析图组件
 */
interface SpectrumAnalyzerProps {
  spectrumData?: number[];
  frequencies?: number[];
  peakFrequencies?: number[];
  title?: string;
}

export const SpectrumAnalyzer: React.FC<SpectrumAnalyzerProps> = ({
  spectrumData = [],
  frequencies = [],
  peakFrequencies = [],
  title = '频谱分析'
}) => {
  // 生成示例数据
  const actualSpectrum = spectrumData.length > 0 ? spectrumData : Array.from({ length: 50 }, (_, i) => Math.exp(-((i - 25) ** 2) / 100) * (1 + 0.3 * Math.sin(i / 5)));
  const actualFreqs = frequencies.length > 0 ? frequencies : Array.from({ length: actualSpectrum.length }, (_, i) => i * 0.02);

  const data = {
    labels: actualFreqs.map(f => f.toFixed(2)),
    datasets: [
      {
        label: '频谱强度',
        data: actualSpectrum,
        borderColor: '#8b5cf6',
        backgroundColor: 'rgba(139, 92, 246, 0.2)',
        fill: true,
        tension: 0.4,
        pointRadius: peakFrequencies.length > 0 ? actualFreqs.map(f => peakFrequencies.includes(f) ? 6 : 0) : 0,
        pointBackgroundColor: '#f59e0b',
        pointBorderColor: '#fff',
        pointBorderWidth: 2,
      }
    ]
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { display: false },
      tooltip: {
        callbacks: {
          label: (ctx: any) => `强度: ${ctx.parsed.y.toFixed(4)}`
        }
      }
    },
    scales: {
      x: { title: { display: true, text: '频率 (Hz)' }, grid: { color: '#f3f4f6' } },
      y: { title: { display: true, text: '振幅' }, beginAtZero: true, grid: { color: '#f3f4f6' } }
    }
  };

  // 频谱统计
  const maxAmplitude = Math.max(...actualSpectrum);
  const spectralWidth = actualSpectrum.filter(v => v > maxAmplitude * 0.5).length * (0.02);
  const peakCount = peakFrequencies.length || actualSpectrum.filter((v, i) => i > 0 && i < actualSpectrum.length - 1 && v > actualSpectrum[i-1] && v > actualSpectrum[i+1] && v > maxAmplitude * 0.5).length;

  return (
    <div style={{ background: 'white', borderRadius: '12px', padding: '20px', boxShadow: '0 2px 8px rgba(0,0,0,0.06)' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
        <h3 style={{ margin: 0, display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Radio size={18} style={{ color: '#8b5cf6' }} />
          {title}
        </h3>
        <div style={{ display: 'flex', gap: '16px', fontSize: '12px' }}>
          <span style={{ color: '#8b5cf6' }}>谱宽: {spectralWidth.toFixed(3)}</span>
          <span style={{ color: '#f59e0b' }}>峰值: {peakCount}</span>
          <span style={{ color: '#10b981' }}>最大: {maxAmplitude.toFixed(4)}</span>
        </div>
      </div>
      <div style={{ height: '200px' }}>
        <Line options={options} data={data} />
      </div>
    </div>
  );
};

/**
 * 四相位状态机组件
 */
interface PhaseStateMachineProps {
  currentPhase: MarketPhase;
  confidence: number;
  dci?: number;
  spectralWidth?: number;
}

export const PhaseStateMachine: React.FC<PhaseStateMachineProps> = ({
  currentPhase,
  confidence = 0.8,
  dci = 0.5,
  spectralWidth = 0.03
}) => {
  const phaseConfig: Record<MarketPhase, { color: string; bgColor: string; name: string; description: string }> = {
    [MarketPhase.PHASE_A_NOISE]: {
      color: '#8c8c8c',
      bgColor: '#f5f5f5',
      name: 'A - 高噪声混乱期',
      description: '市场波动剧烈，无明显趋势方向'
    },
    [MarketPhase.PHASE_B_VORTEX]: {
      color: '#1890ff',
      bgColor: '#e6f4ff',
      name: 'B - 涡旋蓄力期',
      description: '波动收窄，能量积累中'
    },
    [MarketPhase.PHASE_C_RESONANCE]: {
      color: '#faad14',
      bgColor: '#fffbe6',
      name: 'C - 临界爆发前夜',
      description: '随机共振形成，方向选择临近'
    },
    [MarketPhase.PHASE_D_TREND]: {
      color: '#52c41a',
      bgColor: '#f6ffed',
      name: 'D - 趋势运行期',
      description: '方向明确，顺势持仓为主'
    }
  };

  const phases = [
    { key: MarketPhase.PHASE_A_NOISE, label: 'A', position: 0 },
    { key: MarketPhase.PHASE_B_VORTEX, label: 'B', position: 1 },
    { key: MarketPhase.PHASE_C_RESONANCE, label: 'C', position: 2 },
    { key: MarketPhase.PHASE_D_TREND, label: 'D', position: 3 },
  ];

  const currentConfig = phaseConfig[currentPhase];
  const strategy = PHASE_STRATEGIES[currentPhase];

  // 计算进度条位置
  const phaseIndex = phases.findIndex(p => p.key === currentPhase);
  const progressPercent = ((phaseIndex + confidence) / 4) * 100;

  return (
    <div style={{ background: 'white', borderRadius: '12px', padding: '20px', boxShadow: '0 2px 8px rgba(0,0,0,0.06)' }}>
      <h3 style={{ margin: '0 0 20px', display: 'flex', alignItems: 'center', gap: '8px' }}>
        <Target size={18} style={{ color: '#1890ff' }} />
        四相位状态机
      </h3>

      {/* 相位选择器 */}
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px', position: 'relative' }}>
        {/* 连接线 */}
        <div style={{ position: 'absolute', top: '20px', left: '40px', right: '40px', height: '4px', background: '#e5e7eb', borderRadius: '2px' }} />
        {/* 进度线 */}
        <div style={{ position: 'absolute', top: '20px', left: '40px', width: `${progressPercent}%`, height: '4px', background: currentConfig.color, borderRadius: '2px', transition: 'width 0.5s ease' }} />
        
        {phases.map((phase, idx) => {
          const isActive = phase.key === currentPhase;
          const config = phaseConfig[phase.key];
          return (
            <div key={phase.key} style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', zIndex: 1 }}>
              <div style={{
                width: '40px',
                height: '40px',
                borderRadius: '50%',
                background: isActive ? config.color : '#fff',
                border: `3px solid ${config.color}`,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: '16px',
                fontWeight: 700,
                color: isActive ? '#fff' : config.color,
                boxShadow: isActive ? `0 0 12px ${config.color}50` : 'none',
                transition: 'all 0.3s ease'
              }}>
                {phase.label}
              </div>
              <span style={{ marginTop: '8px', fontSize: '11px', color: isActive ? config.color : '#9ca3af', fontWeight: isActive ? 600 : 400 }}>
                {phase.key === MarketPhase.PHASE_A_NOISE ? '噪声' :
                 phase.key === MarketPhase.PHASE_B_VORTEX ? '涡旋' :
                 phase.key === MarketPhase.PHASE_C_RESONANCE ? '共振' : '趋势'}
              </span>
            </div>
          );
        })}
      </div>

      {/* 当前相位详情 */}
      <div style={{
        marginTop: '20px',
        padding: '16px',
        background: currentConfig.bgColor,
        borderRadius: '8px',
        border: `1px solid ${currentConfig.color}30`
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
          <span style={{ fontSize: '18px', fontWeight: 700, color: currentConfig.color }}>
            {currentConfig.name}
          </span>
          <div style={{
            padding: '4px 12px',
            borderRadius: '12px',
            background: currentConfig.color,
            color: '#fff',
            fontSize: '12px',
            fontWeight: 600
          }}>
            {Math.round(confidence * 100)}% 置信度
          </div>
        </div>
        <p style={{ margin: 0, fontSize: '13px', color: '#666' }}>
          {currentConfig.description}
        </p>
      </div>

      {/* 策略信息 */}
      <div style={{ marginTop: '16px', display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '12px' }}>
        <div style={{ padding: '12px', background: '#f9fafb', borderRadius: '8px', textAlign: 'center' }}>
          <div style={{ fontSize: '11px', color: '#6b7280', marginBottom: '4px' }}>仓位上限</div>
          <div style={{ fontSize: '18px', fontWeight: 700, color: '#374151' }}>{Math.round(strategy.maxPosition * 100)}%</div>
        </div>
        <div style={{ padding: '12px', background: '#f9fafb', borderRadius: '8px', textAlign: 'center' }}>
          <div style={{ fontSize: '11px', color: '#6b7280', marginBottom: '4px' }}>最大杠杆</div>
          <div style={{ fontSize: '18px', fontWeight: 700, color: '#374151' }}>≤{strategy.leverageAllowed}x</div>
        </div>
        <div style={{ padding: '12px', background: '#f9fafb', borderRadius: '8px', textAlign: 'center' }}>
          <div style={{ fontSize: '11px', color: '#6b7280', marginBottom: '4px' }}>DCI</div>
          <div style={{ fontSize: '18px', fontWeight: 700, color: dci > 0.6 ? '#52c41a' : dci < 0.4 ? '#f5222d' : '#faad14' }}>{dci.toFixed(2)}</div>
        </div>
      </div>
    </div>
  );
};

/**
 * 信号历史时间线组件
 */
interface SignalTimelineProps {
  signals?: TradingSignal[];
  maxDisplay?: number;
}

export const SignalTimeline: React.FC<SignalTimelineProps> = ({
  signals = [],
  maxDisplay = 10
}) => {
  const displaySignals = signals.slice(0, maxDisplay);

  const getSignalConfig = (type: string, direction: string) => {
    const configs: Record<string, { color: string; bgColor: string; icon: string }> = {
      'vortex_breakout': { color: '#1890ff', bgColor: '#e6f4ff', icon: '⚡' },
      'resonance_trigger': { color: '#faad14', bgColor: '#fffbe6', icon: '🔊' },
      'trend_callback': { color: '#52c41a', bgColor: '#f6ffed', icon: '📈' },
    };
    return configs[type] || { color: '#8c8c8c', bgColor: '#f5f5f5', icon: '📌' };
  };

  const getDirectionLabel = (direction: string) => {
    switch (direction) {
      case 'bullish': return '做多';
      case 'bearish': return '做空';
      default: return '观望';
    }
  };

  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
  };

  return (
    <div style={{ background: 'white', borderRadius: '12px', padding: '20px', boxShadow: '0 2px 8px rgba(0,0,0,0.06)' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <h3 style={{ margin: 0, display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Activity size={18} style={{ color: '#8b5cf6' }} />
          信号历史
        </h3>
        <span style={{ padding: '4px 12px', background: '#f3f4f6', borderRadius: '12px', fontSize: '12px', color: '#6b7280' }}>
          {signals.length} 条记录
        </span>
      </div>

      {displaySignals.length === 0 ? (
        <div style={{ padding: '40px', textAlign: 'center', color: '#9ca3af', background: '#fafafa', borderRadius: '8px' }}>
          <Clock size={32} style={{ marginBottom: '8px', opacity: 0.5 }} />
          <p style={{ margin: 0, fontSize: '14px' }}>暂无信号记录</p>
          <p style={{ margin: '4px 0 0', fontSize: '12px' }}>运行 Pipeline 后将显示信号</p>
        </div>
      ) : (
        <div style={{ position: 'relative' }}>
          {/* 时间线 */}
          <div style={{ position: 'absolute', left: '19px', top: '20px', bottom: '20px', width: '2px', background: '#e5e7eb' }} />
          
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {displaySignals.map((signal, idx) => {
              const config = getSignalConfig(signal.type, signal.direction);
              return (
                <div key={signal.id} style={{ display: 'flex', gap: '16px', position: 'relative' }}>
                  {/* 时间线节点 */}
                  <div style={{
                    width: '40px',
                    height: '40px',
                    borderRadius: '50%',
                    background: config.bgColor,
                    border: `3px solid ${config.color}`,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: '16px',
                    flexShrink: 0,
                    zIndex: 1
                  }}>
                    {config.icon}
                  </div>
                  
                  {/* 信号卡片 */}
                  <div style={{
                    flex: 1,
                    padding: '12px 16px',
                    background: config.bgColor,
                    borderRadius: '8px',
                    border: `1px solid ${config.color}30`
                  }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '8px' }}>
                      <div>
                        <span style={{ fontWeight: 600, color: '#374151', marginRight: '8px' }}>
                          {signal.type.replace('_', ' ').toUpperCase()}
                        </span>
                        <span style={{
                          padding: '2px 8px',
                          borderRadius: '4px',
                          fontSize: '11px',
                          fontWeight: 600,
                          background: signal.direction === 'bullish' ? '#d1fae5' : signal.direction === 'bearish' ? '#fee2e2' : '#f3f4f6',
                          color: signal.direction === 'bullish' ? '#059669' : signal.direction === 'bearish' ? '#dc2626' : '#6b7280'
                        }}>
                          {getDirectionLabel(signal.direction)}
                        </span>
                      </div>
                      <span style={{ fontSize: '12px', color: '#9ca3af' }}>
                        {formatTime(signal.timestamp)}
                      </span>
                    </div>
                    
                    <div style={{ display: 'flex', gap: '16px', fontSize: '12px', color: '#6b7280' }}>
                      <span>价格: <strong>${signal.price.toLocaleString()}</strong></span>
                      <span>置信度: <strong style={{ color: signal.confidence >= 0.7 ? '#52c41a' : signal.confidence >= 0.4 ? '#faad14' : '#f5222d' }}>
                        {(signal.confidence * 100).toFixed(0)}%
                      </strong></span>
                      <span>DCI: <strong>{signal.indicators.dci.toFixed(2)}</strong></span>
                    </div>
                    
                    {signal.reason && (
                      <p style={{ margin: '8px 0 0', fontSize: '12px', color: '#9ca3af' }}>
                        {signal.reason}
                      </p>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
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
  
  // 信号和相位状态
  const [signals, setSignals] = useState<TradingSignal[]>([]);
  const [currentPhase, setCurrentPhase] = useState<MarketPhase>(MarketPhase.PHASE_A_NOISE);
  const [phaseConfidence, setPhaseConfidence] = useState(0.8);

  const pipelineService = getPipelineService();

  // 刷新信号历史
  const refreshSignals = useCallback(() => {
    const history = pipelineService.getSignalHistory();
    setSignals(history);
  }, []);

  // 从币安获取 BTC 价格
  const fetchMarketData = useCallback(async () => {
    setIsLoading(true);
    try {
      const response = await fetch('https://api.binance.com/api/v3/ticker/24hr?symbol=BTCUSDT');
      if (!response.ok) throw new Error('API error');
      const data = await response.json();
      const updated = {
        ...indicators,
        btcPrice: parseFloat(data.lastPrice),
        btcChange24h: parseFloat(data.priceChangePercent),
        lastUpdated: new Date().toISOString(),
      };
      setIndicators(updated);
      saveIndicators(updated);
      setLastApiUpdate(new Date().toLocaleTimeString('zh-CN'));
    } catch (error) {
      console.error('Failed to fetch market data:', error);
    }
    setIsLoading(false);
  }, [indicators]);

  useEffect(() => {
    fetchMarketData();
    refreshSignals();
  }, []);

  const handleSave = useCallback((newIndicators: OnChainIndicators) => {
    setIndicators(newIndicators);
    saveIndicators(newIndicators);
    setShowEditForm(false);
  }, []);

  const getMvrvStatus = (): 'bullish' | 'bearish' | 'neutral' => {
    if (indicators.mvrvScore < 0) return 'bullish';
    if (indicators.mvrvScore > 7) return 'bearish';
    return 'neutral';
  };

  const getNuplStatus = (): 'bullish' | 'bearish' | 'neutral' => {
    if (indicators.nupl < 0.25) return 'bullish';
    if (indicators.nupl > 0.75) return 'bearish';
    return 'neutral';
  };

  const getNuplPhase = (): string => {
    if (indicators.nupl < 0) return '投降';
    if (indicators.nupl < 0.25) return '希望/恐惧';
    if (indicators.nupl < 0.5) return '乐观/焦虑';
    if (indicators.nupl < 0.75) return '信念/否认';
    return '欣快/贪婪';
  };

  const getHalvingPhaseName = (): string => {
    const phases: Record<string, string> = { accumulation: '积累期', halving: '减半期', main_rally: '主升浪', top: '顶部区域' };
    return phases[indicators.halvingPhase] || '未知';
  };

  // 计算综合评分
  const calculateOnChainScore = (): number => {
    let score = 0;
    if (indicators.mvrvScore < 1) score += 2;
    else if (indicators.mvrvScore <= 3) score += 1;
    if (indicators.nupl < 0.25) score += 2;
    else if (indicators.nupl <= 0.5) score += 1;
    if (indicators.exchangeBalance === 'decreasing') score += 2;
    else if (indicators.exchangeBalance === 'stable') score += 1;
    if (indicators.lthSupplyPercent > 65) score += 2;
    else if (indicators.lthSupplyPercent > 55) score += 1;
    if (indicators.stablecoinBalance === 'increasing') score += 2;
    else if (indicators.stablecoinBalance === 'stable') score += 1;
    if (indicators.whaleFlow === 'outflow') score += 2;
    else if (indicators.whaleFlow === 'neutral') score += 1;
    return score;
  };

  const calculatedOnChainScore = calculateOnChainScore();

  return (
    <div style={{ minHeight: '100vh', background: '#f8fafc', padding: '24px' }}>
      {/* 顶部标题栏 */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px', flexWrap: 'wrap', gap: '16px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{ width: '40px', height: '40px', borderRadius: '10px', background: 'linear-gradient(135deg, #8b5cf6 0%, #6d28d9 100%)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'white' }}>
            <Activity size={22} />
          </div>
          <div>
            <h1 style={{ margin: 0, fontSize: '24px', fontWeight: 700, color: '#1f2937' }}>NEMT Dashboard</h1>
            <p style={{ margin: '2px 0 0', fontSize: '13px', color: '#9ca3af' }}>市场分析综合视图</p>
          </div>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <button onClick={refreshSignals} style={{ display: 'flex', alignItems: 'center', gap: '6px', padding: '8px 12px', border: '2px solid #e5e7eb', borderRadius: '8px', background: 'white', cursor: 'pointer', fontSize: '12px', color: '#374151' }}>
            <RefreshCw size={12} /> 刷新信号
          </button>
          <button onClick={() => setShowEditForm(true)} style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '10px 16px', border: '2px solid #e5e7eb', borderRadius: '8px', background: 'white', cursor: 'pointer', fontSize: '13px', color: '#374151' }}>
            <Edit2 size={14} /> 更新数据
          </button>
        </div>
      </div>

      {/* 核心可视化区 */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px', marginBottom: '24px' }}>
        {/* 频谱分析 */}
        <SpectrumAnalyzer
          title="实时频谱分析"
          peakFrequencies={[0.5, 1.0, 1.5]}
        />
        
        {/* 四相位状态机 */}
        <PhaseStateMachine
          currentPhase={currentPhase}
          confidence={phaseConfidence}
          dci={0.68}
          spectralWidth={0.023}
        />
      </div>

      {/* 信号时间线 */}
      <div style={{ marginBottom: '24px' }}>
        <SignalTimeline signals={signals} maxDisplay={8} />
      </div>

      {/* BTC 价格 */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '12px', marginBottom: '24px' }}>
        <MetricCard label="BTC 价格" value={indicators.btcPrice > 0 ? `$${indicators.btcPrice.toLocaleString()}` : '—'} status={indicators.btcChange24h > 0 ? 'bullish' : indicators.btcChange24h < 0 ? 'bearish' : 'neutral'} icon={<DollarSign size={16} />} />
        <MetricCard label="24h 涨跌" value={indicators.btcChange24h > 0 ? `+${indicators.btcChange24h.toFixed(2)}%` : `${indicators.btcChange24h.toFixed(2)}%`} trend={indicators.btcChange24h > 0 ? 'up' : indicators.btcChange24h < 0 ? 'down' : 'stable'} status={indicators.btcChange24h > 0 ? 'bullish' : indicators.btcChange24h < 0 ? 'bearish' : 'neutral'} />
        <MetricCard label="减半周期" value={getHalvingPhaseName()} status="neutral" />
        <MetricCard label="链上评分" value={`${calculatedOnChainScore}/12`} status={calculatedOnChainScore >= 8 ? 'bullish' : calculatedOnChainScore >= 4 ? 'neutral' : 'bearish'} />
      </div>

      {/* MVRV & NUPL */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '12px', marginBottom: '24px' }}>
        <div style={{ background: 'white', borderRadius: '12px', padding: '20px', boxShadow: '0 2px 8px rgba(0,0,0,0.06)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
            <span style={{ fontSize: '14px', fontWeight: 600, color: '#374151' }}>MVRV Z-score</span>
            <TrendIndicator trend={indicators.mvrvTrend} />
          </div>
          <div style={{ fontSize: '36px', fontWeight: 800, color: getMvrvStatus() === 'bullish' ? '#10b981' : getMvrvStatus() === 'bearish' ? '#ef4444' : '#6b7280' }}>
            {indicators.mvrvScore.toFixed(2)}
          </div>
        </div>
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
        </div>
      </div>

      {/* 编辑表单（简化版） */}
      {showEditForm && (
        <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.5)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000, padding: '20px' }}>
          <div style={{ background: 'white', borderRadius: '16px', padding: '24px', width: '100%', maxWidth: '500px', maxHeight: '90vh', overflow: 'auto' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
              <h3 style={{ margin: 0 }}>更新指标</h3>
              <button onClick={() => setShowEditForm(false)} style={{ padding: '4px', border: 'none', background: 'none', cursor: 'pointer' }}><Edit2 size={20} /></button>
            </div>
            <div style={{ display: 'grid', gap: '16px' }}>
              <div>
                <label style={{ display: 'block', fontSize: '12px', fontWeight: 500, marginBottom: '4px' }}>MVRV Z-score</label>
                <input type="number" step="0.1" value={indicators.mvrvScore} onChange={(e) => setIndicators({...indicators, mvrvScore: parseFloat(e.target.value) || 0})} style={{ width: '100%', padding: '10px', border: '2px solid #e5e7eb', borderRadius: '8px' }} />
              </div>
              <div>
                <label style={{ display: 'block', fontSize: '12px', fontWeight: 500, marginBottom: '4px' }}>NUPL (0-1)</label>
                <input type="number" step="0.01" min="0" max="1" value={indicators.nupl} onChange={(e) => setIndicators({...indicators, nupl: Math.min(1, Math.max(0, parseFloat(e.target.value) || 0))})} style={{ width: '100%', padding: '10px', border: '2px solid #e5e7eb', borderRadius: '8px' }} />
              </div>
              <div style={{ display: 'flex', gap: '12px', marginTop: '16px' }}>
                <button onClick={() => setShowEditForm(false)} style={{ flex: 1, padding: '12px', borderRadius: '8px', border: '2px solid #e5e7eb', background: 'white', cursor: 'pointer' }}>取消</button>
                <button onClick={() => handleSave(indicators)} style={{ flex: 1, padding: '12px', borderRadius: '8px', border: 'none', background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)', color: 'white', cursor: 'pointer', fontWeight: 600 }}>保存</button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default OnChainDashboard;
