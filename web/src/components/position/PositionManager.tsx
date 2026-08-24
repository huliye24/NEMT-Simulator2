/**
 * Copyright 2026 NEMT Lab
 *
 * 仓位管理面板组件
 * 
 * 功能：
 * - 实时仓位显示
 * - 风险等级仪表盘
 * - 仓位计算器
 * - 历史仓位记录
 */

import React, { useState, useEffect } from 'react';
import {
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  Shield,
  DollarSign,
  Percent,
  Activity,
  Clock,
  Settings,
  Calculator,
  ChevronRight,
  ChevronDown,
  X,
  type LucideIcon,
} from 'lucide-react';
import {
  usePositionStore,
  useEquity,
  useRiskTier,
  useAlgoMode,
  useRiskProfile,
  useLastCalculation,
  useOpenOrders,
  usePositionHistory,
  useWinRate,
  useTotalPositionPct,
  RISK_TIERS_CONFIG,
  type AlgoMode,
} from '../../stores';

// ============================================
// 子组件
// ============================================

/** 数值卡片组件 */
function StatCard({
  label,
  value,
  subValue,
  icon: Icon,
  trend,
  color = '#8b5cf6',
}: {
  label: string;
  value: React.ReactNode;
  subValue?: string;
  icon: LucideIcon;
  trend?: 'up' | 'down' | 'neutral';
  color?: string;
}) {
  const TrendIcon = trend === 'up' ? TrendingUp : trend === 'down' ? TrendingDown : Activity;
  
  return (
    <div style={{
      background: 'linear-gradient(135deg, #1e293b 0%, #0f172a 100%)',
      border: '1px solid #334155',
      borderRadius: '12px',
      padding: '16px',
      display: 'flex',
      flexDirection: 'column',
      gap: '8px',
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <span style={{ fontSize: '12px', color: '#64748b', textTransform: 'uppercase' }}>{label}</span>
        <Icon size={16} style={{ color }} />
      </div>
      <div style={{ fontSize: '24px', fontWeight: 700, color: '#f1f5f9' }}>
        {value}
      </div>
      {subValue && (
        <div style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '12px' }}>
          {trend && <TrendIcon size={12} style={{ color: trend === 'up' ? '#22c55e' : trend === 'down' ? '#ef4444' : '#64748b' }} />}
          <span style={{ color: trend === 'up' ? '#22c55e' : trend === 'down' ? '#ef4444' : '#64748b' }}>{subValue}</span>
        </div>
      )}
    </div>
  );
}

/** 风险等级指示器 */
function RiskTierBadge({ tier }: { tier: string }) {
  const config = RISK_TIERS_CONFIG[tier as keyof typeof RISK_TIERS_CONFIG];
  if (!config) return null;
  
  return (
    <div style={{
      display: 'inline-flex',
      alignItems: 'center',
      gap: '6px',
      padding: '4px 12px',
      borderRadius: '20px',
      background: `${config.color}20`,
      border: `1px solid ${config.color}`,
    }}>
      <Shield size={14} style={{ color: config.color }} />
      <span style={{ fontSize: '13px', fontWeight: 600, color: config.color }}>{config.label}</span>
    </div>
  );
}

/** 仓位滑块 */
function RiskSlider({
  value,
  onChange,
}: {
  value: number;
  onChange: (value: number) => void;
}) {
  const getLabel = (v: number) => {
    if (v < 25) return { text: '极度保守', color: '#3b82f6' };
    if (v < 50) return { text: '保守', color: '#22c55e' };
    if (v < 75) return { text: '激进', color: '#f97316' };
    return { text: '极度激进', color: '#ef4444' };
  };
  
  const label = getLabel(value);
  
  return (
    <div style={{ padding: '16px', background: '#1e293b', borderRadius: '12px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '12px' }}>
        <span style={{ fontSize: '13px', color: '#94a3b8' }}>风险偏好</span>
        <span style={{ fontSize: '13px', fontWeight: 600, color: label.color }}>{label.text}</span>
      </div>
      <input
        type="range"
        min="0"
        max="100"
        value={value}
        onChange={(e) => onChange(parseInt(e.target.value))}
        style={{
          width: '100%',
          height: '8px',
          borderRadius: '4px',
          background: `linear-gradient(to right, #3b82f6 0%, #22c55e 25%, #f97316 75%, #ef4444 100%)`,
          appearance: 'none',
          cursor: 'pointer',
        }}
      />
      <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '8px', fontSize: '11px', color: '#64748b' }}>
        <span>保守</span>
        <span>激进</span>
      </div>
    </div>
  );
}

/** 算法切换 */
function AlgoModeToggle({
  mode,
  onChange,
}: {
  mode: AlgoMode;
  onChange: (mode: AlgoMode) => void;
}) {
  return (
    <div style={{
      display: 'flex',
      background: '#0f172a',
      borderRadius: '8px',
      padding: '4px',
      border: '1px solid #334155',
    }}>
      <button
        onClick={() => onChange('simple')}
        style={{
          flex: 1,
          padding: '8px 16px',
          border: 'none',
          borderRadius: '6px',
          background: mode === 'simple' ? '#8b5cf6' : 'transparent',
          color: mode === 'simple' ? '#fff' : '#64748b',
          cursor: 'pointer',
          fontSize: '13px',
          fontWeight: 500,
          transition: 'all 0.2s',
        }}
      >
        简单模式
      </button>
      <button
        onClick={() => onChange('hybrid')}
        style={{
          flex: 1,
          padding: '8px 16px',
          border: 'none',
          borderRadius: '6px',
          background: mode === 'hybrid' ? '#8b5cf6' : 'transparent',
          color: mode === 'hybrid' ? '#fff' : '#64748b',
          cursor: 'pointer',
          fontSize: '13px',
          fontWeight: 500,
          transition: 'all 0.2s',
        }}
      >
        复合算法
      </button>
    </div>
  );
}

/** 仓位计算结果 */
function PositionCalculator({
  onCalculate,
}: {
  onCalculate: () => void;
}) {
  const [symbol, setSymbol] = useState('BTC');
  const [side, setSide] = useState<'long' | 'short'>('long');
  const [entryPrice, setEntryPrice] = useState('50000');
  const [stopLoss, setStopLoss] = useState('2');
  const [confidence, setConfidence] = useState('100');
  
  const result = useLastCalculation();
  
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
      {/* 输入表单 */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
        <div>
          <label style={{ fontSize: '12px', color: '#64748b', marginBottom: '4px', display: 'block' }}>交易品种</label>
          <select
            value={symbol}
            onChange={(e) => setSymbol(e.target.value)}
            style={{
              width: '100%',
              padding: '10px 12px',
              background: '#0f172a',
              border: '1px solid #334155',
              borderRadius: '8px',
              color: '#f1f5f9',
              fontSize: '14px',
            }}
          >
            <option value="BTC">BTC</option>
            <option value="ETH">ETH</option>
            <option value="SOL">SOL</option>
          </select>
        </div>
        
        <div>
          <label style={{ fontSize: '12px', color: '#64748b', marginBottom: '4px', display: 'block' }}>方向</label>
          <div style={{ display: 'flex', gap: '8px' }}>
            <button
              onClick={() => setSide('long')}
              style={{
                flex: 1,
                padding: '10px',
                border: 'none',
                borderRadius: '8px',
                background: side === 'long' ? '#22c55e' : '#1e293b',
                color: '#fff',
                cursor: 'pointer',
                fontWeight: 600,
              }}
            >
              做多
            </button>
            <button
              onClick={() => setSide('short')}
              style={{
                flex: 1,
                padding: '10px',
                border: 'none',
                borderRadius: '8px',
                background: side === 'short' ? '#ef4444' : '#1e293b',
                color: '#fff',
                cursor: 'pointer',
                fontWeight: 600,
              }}
            >
              做空
            </button>
          </div>
        </div>
        
        <div>
          <label style={{ fontSize: '12px', color: '#64748b', marginBottom: '4px', display: 'block' }}>入场价格</label>
          <input
            type="number"
            value={entryPrice}
            onChange={(e) => setEntryPrice(e.target.value)}
            style={{
              width: '100%',
              padding: '10px 12px',
              background: '#0f172a',
              border: '1px solid #334155',
              borderRadius: '8px',
              color: '#f1f5f9',
              fontSize: '14px',
            }}
          />
        </div>
        
        <div>
          <label style={{ fontSize: '12px', color: '#64748b', marginBottom: '4px', display: 'block' }}>止损百分比 (%)</label>
          <input
            type="number"
            value={stopLoss}
            onChange={(e) => setStopLoss(e.target.value)}
            style={{
              width: '100%',
              padding: '10px 12px',
              background: '#0f172a',
              border: '1px solid #334155',
              borderRadius: '8px',
              color: '#f1f5f9',
              fontSize: '14px',
            }}
          />
        </div>
        
        <div style={{ gridColumn: '1 / -1' }}>
          <label style={{ fontSize: '12px', color: '#64748b', marginBottom: '4px', display: 'block' }}>
            信心度 {confidence}%
          </label>
          <input
            type="range"
            min="0"
            max="100"
            value={confidence}
            onChange={(e) => setConfidence(e.target.value)}
            style={{
              width: '100%',
              height: '6px',
              borderRadius: '3px',
              background: `linear-gradient(to right, #8b5cf6 0%, #8b5cf6 ${confidence}%, #334155 ${confidence}%, #334155 100%)`,
              appearance: 'none',
            }}
          />
        </div>
      </div>
      
      <button
        onClick={onCalculate}
        style={{
          padding: '12px',
          background: 'linear-gradient(135deg, #8b5cf6 0%, #6366f1 100%)',
          border: 'none',
          borderRadius: '8px',
          color: '#fff',
          fontSize: '14px',
          fontWeight: 600,
          cursor: 'pointer',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          gap: '8px',
        }}
      >
        <Calculator size={16} />
        计算仓位
      </button>
      
      {/* 计算结果 */}
      {result && (
        <div style={{
          padding: '16px',
          background: '#0f172a',
          borderRadius: '12px',
          border: '1px solid #8b5cf640',
        }}>
          <div style={{ fontSize: '12px', color: '#64748b', marginBottom: '12px', textTransform: 'uppercase' }}>
            计算结果
          </div>
          
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
            <div>
              <div style={{ fontSize: '11px', color: '#64748b' }}>建议仓位</div>
              <div style={{ fontSize: '20px', fontWeight: 700, color: '#f1f5f9' }}>
                ${result.position_value.toLocaleString(undefined, { maximumFractionDigits: 2 })}
              </div>
            </div>
            <div>
              <div style={{ fontSize: '11px', color: '#64748b' }}>仓位比例</div>
              <div style={{ fontSize: '20px', fontWeight: 700, color: '#8b5cf6' }}>
                {(result.position_pct * 100).toFixed(1)}%
              </div>
            </div>
            <div>
              <div style={{ fontSize: '11px', color: '#64748b' }}>风险金额</div>
              <div style={{ fontSize: '16px', fontWeight: 600, color: '#ef4444' }}>
                ${result.risk_amount.toLocaleString(undefined, { maximumFractionDigits: 2 })}
              </div>
            </div>
            <div>
              <div style={{ fontSize: '11px', color: '#64748b' }}>风险等级</div>
              <RiskTierBadge tier={result.risk_tier} />
            </div>
          </div>
          
          {/* 复合算法明细 */}
          {result.methods && (
            <div style={{ marginTop: '16px', paddingTop: '16px', borderTop: '1px solid #334155' }}>
              <div style={{ fontSize: '11px', color: '#64748b', marginBottom: '8px' }}>算法贡献</div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                {Object.entries(result.methods)
                  .filter(([key, val]) => ['atr', 'kelly', 'confidence'].includes(key) && typeof val === 'number')
                  .map(([key, value]) => (
                    <div key={key} style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px' }}>
                      <span style={{ color: '#94a3b8', textTransform: 'uppercase' }}>{key}</span>
                      <span style={{ color: '#f1f5f9' }}>
                        ${(value as number).toLocaleString(undefined, { maximumFractionDigits: 2 })}
                      </span>
                    </div>
                  ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

/** 历史记录表格 */
function HistoryTable({ history }: { history: ReturnType<typeof usePositionHistory> }) {
  const [expanded, setExpanded] = useState(false);
  
  if (history.length === 0) {
    return (
      <div style={{
        padding: '32px',
        textAlign: 'center',
        color: '#64748b',
        background: '#1e293b',
        borderRadius: '12px',
      }}>
        <Clock size={32} style={{ margin: '0 auto 12px', opacity: 0.5 }} />
        <div>暂无历史记录</div>
      </div>
    );
  }
  
  const displayHistory = expanded ? history : history.slice(0, 5);
  
  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
        <span style={{ fontSize: '13px', color: '#94a3b8' }}>最近 {history.length} 笔交易</span>
        {history.length > 5 && (
          <button
            onClick={() => setExpanded(!expanded)}
            style={{
              background: 'none',
              border: 'none',
              color: '#8b5cf6',
              cursor: 'pointer',
              fontSize: '12px',
              display: 'flex',
              alignItems: 'center',
              gap: '4px',
            }}
          >
            {expanded ? '收起' : '查看全部'}
            {expanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
          </button>
        )}
      </div>
      
      <div style={{ overflowX: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ borderBottom: '1px solid #334155' }}>
              {['时间', '品种', '方向', '仓位', '入场', '出场', '盈亏', '原因'].map((header, i) => (
                <th key={i} style={{
                  padding: '8px 12px',
                  textAlign: i >= 4 ? 'right' : 'left',
                  fontSize: '11px',
                  color: '#64748b',
                  textTransform: 'uppercase',
                  fontWeight: 500,
                }}>
                  {header}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {displayHistory.map((record) => (
              <tr key={record.history_id} style={{ borderBottom: '1px solid #1e293b' }}>
                <td style={{ padding: '10px 12px', fontSize: '12px', color: '#94a3b8' }}>
                  {new Date(record.exit_time).toLocaleString('zh-CN', {
                    month: '2-digit',
                    day: '2-digit',
                    hour: '2-digit',
                    minute: '2-digit',
                  })}
                </td>
                <td style={{ padding: '10px 12px', fontSize: '12px', color: '#f1f5f9', fontWeight: 500 }}>
                  {record.symbol}
                </td>
                <td style={{ padding: '10px 12px' }}>
                  <span style={{
                    padding: '2px 8px',
                    borderRadius: '4px',
                    fontSize: '11px',
                    fontWeight: 600,
                    background: record.side === 'long' ? '#22c55e20' : '#ef444420',
                    color: record.side === 'long' ? '#22c55e' : '#ef4444',
                  }}>
                    {record.side === 'long' ? '多' : '空'}
                  </span>
                </td>
                <td style={{ padding: '10px 12px', fontSize: '12px', color: '#94a3b8', textAlign: 'right' }}>
                  {(record.position_pct * 100).toFixed(1)}%
                </td>
                <td style={{ padding: '10px 12px', fontSize: '12px', color: '#94a3b8', textAlign: 'right' }}>
                  ${record.entry_price.toLocaleString()}
                </td>
                <td style={{ padding: '10px 12px', fontSize: '12px', color: '#94a3b8', textAlign: 'right' }}>
                  ${record.exit_price.toLocaleString()}
                </td>
                <td style={{
                  padding: '10px 12px',
                  fontSize: '12px',
                  fontWeight: 600,
                  textAlign: 'right',
                  color: record.pnl >= 0 ? '#22c55e' : '#ef4444',
                }}>
                  {record.pnl >= 0 ? '+' : ''}{record.pnl_pct.toFixed(2)}%
                </td>
                <td style={{ padding: '10px 12px', fontSize: '11px', color: '#64748b' }}>
                  {record.exit_reason === 'stop_loss' ? '止损' :
                   record.exit_reason === 'take_profit' ? '止盈' : '手动'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

/** 当前持仓列表 */
function OpenOrders({ orders }: { orders: ReturnType<typeof useOpenOrders> }) {
  const closeOrder = usePositionStore(state => state.closeOrder);
  
  if (orders.length === 0) {
    return (
      <div style={{
        padding: '24px',
        textAlign: 'center',
        color: '#64748b',
        background: '#1e293b',
        borderRadius: '12px',
      }}>
        <Shield size={24} style={{ margin: '0 auto 8px', opacity: 0.5 }} />
        <div>暂无持仓</div>
      </div>
    );
  }
  
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
      {orders.map((order) => (
        <div
          key={order.order_id}
          style={{
            padding: '12px 16px',
            background: '#1e293b',
            borderRadius: '8px',
            border: '1px solid #334155',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <span style={{
              padding: '4px 8px',
              borderRadius: '4px',
              fontSize: '11px',
              fontWeight: 600,
              background: order.side === 'long' ? '#22c55e20' : '#ef444420',
              color: order.side === 'long' ? '#22c55e' : '#ef4444',
            }}>
              {order.side === 'long' ? '多' : '空'} {order.symbol}
            </span>
            <div>
              <div style={{ fontSize: '13px', fontWeight: 600, color: '#f1f5f9' }}>
                ${order.position_value.toLocaleString()}
              </div>
              <div style={{ fontSize: '11px', color: '#64748b' }}>
                {(order.position_pct * 100).toFixed(1)}% @ ${order.entry_price.toLocaleString()}
              </div>
            </div>
          </div>
          
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
            <div style={{ textAlign: 'right' }}>
              <div style={{
                fontSize: '13px',
                fontWeight: 600,
                color: order.unrealized_pnl >= 0 ? '#22c55e' : '#ef4444',
              }}>
                {order.unrealized_pnl >= 0 ? '+' : ''}{order.unrealized_pnl_pct.toFixed(2)}%
              </div>
              <div style={{ fontSize: '11px', color: '#64748b' }}>
                ${order.unrealized_pnl.toLocaleString(undefined, { maximumFractionDigits: 2 })}
              </div>
            </div>
            <button
              onClick={() => closeOrder(order.order_id, order.current_price, 'manual')}
              style={{
                padding: '6px 12px',
                background: '#334155',
                border: 'none',
                borderRadius: '6px',
                color: '#94a3b8',
                cursor: 'pointer',
                fontSize: '12px',
              }}
            >
              平仓
            </button>
          </div>
        </div>
      ))}
    </div>
  );
}

// ============================================
// 主组件
// ============================================

export function PositionManager() {
  const equity = useEquity();
  const riskTier = useRiskTier();
  const algoMode = useAlgoMode();
  const riskProfile = useRiskProfile();
  const lastCalculation = useLastCalculation();
  const openOrders = useOpenOrders();
  const history = usePositionHistory();
  const winRate = useWinRate();
  const totalPositionPct = useTotalPositionPct();
  
  const {
    initialize,
    calculatePosition,
    setAlgoMode,
    setRiskSlider,
    risk_slider_value,
  } = usePositionStore();
  
  // 初始化
  useEffect(() => {
    initialize(10000);
  }, []);
  
  // 计算涨跌
  const equityChange = equity - 10000;
  const equityChangePct = (equityChange / 10000) * 100;
  
  // 处理计算
  const handleCalculate = () => {
    calculatePosition({
      symbol: 'BTC',
      side: 'long',
      entry_price: 50000,
      stop_loss_pct: 0.02,
      signal_confidence: 0.8,
    });
  };
  
  return (
    <div style={{ padding: '24px', maxWidth: '1200px', margin: '0 auto' }}>
      {/* 标题 */}
      <div style={{ marginBottom: '24px' }}>
        <h1 style={{ fontSize: '24px', fontWeight: 700, color: '#f1f5f9', marginBottom: '8px' }}>
          仓位管理
        </h1>
        <p style={{ fontSize: '14px', color: '#64748b' }}>
          智能仓位计算，动态风险控制
        </p>
      </div>
      
      {/* 顶部统计卡片 */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '16px', marginBottom: '24px' }}>
        <StatCard
          label="账户权益"
          value={`$${equity.toLocaleString(undefined, { maximumFractionDigits: 2 })}`}
          subValue={`${equityChange >= 0 ? '+' : ''}$${equityChange.toFixed(2)} (${equityChangePct.toFixed(2)}%)`}
          icon={DollarSign}
          trend={equityChange >= 0 ? 'up' : 'down'}
          color="#8b5cf6"
        />
        <StatCard
          label="总持仓"
          value={`${(totalPositionPct * 100).toFixed(1)}%`}
          subValue={`$${(equity * totalPositionPct).toLocaleString()}`}
          icon={Percent}
          color="#f97316"
        />
        <StatCard
          label="风险等级"
          value={<RiskTierBadge tier={riskTier} />}
          icon={Shield}
          color={RISK_TIERS_CONFIG[riskTier].color}
        />
        <StatCard
          label="胜率"
          value={`${(winRate * 100).toFixed(1)}%`}
          subValue={`${history.filter(h => h.pnl > 0).length} 胜 ${history.filter(h => h.pnl <= 0).length} 负`}
          icon={Activity}
          color={winRate >= 0.5 ? '#22c55e' : '#ef4444'}
        />
      </div>
      
      {/* 风险配置卡片 */}
      {riskProfile && (
        <div style={{
          padding: '16px',
          background: `${RISK_TIERS_CONFIG[riskTier].color}10`,
          border: `1px solid ${RISK_TIERS_CONFIG[riskTier].color}40`,
          borderRadius: '12px',
          marginBottom: '24px',
          display: 'flex',
          justifyContent: 'space-around',
        }}>
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: '11px', color: '#64748b' }}>每笔风险</div>
            <div style={{ fontSize: '18px', fontWeight: 700, color: '#f1f5f9' }}>
              {riskProfile.risk_per_trade_pct.toFixed(1)}%
            </div>
          </div>
          <div style={{ width: '1px', background: '#334155' }} />
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: '11px', color: '#64748b' }}>最大仓位</div>
            <div style={{ fontSize: '18px', fontWeight: 700, color: '#f1f5f9' }}>
              {riskProfile.max_position_pct.toFixed(1)}%
            </div>
          </div>
          <div style={{ width: '1px', background: '#334155' }} />
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: '11px', color: '#64748b' }}>日亏损限额</div>
            <div style={{ fontSize: '18px', fontWeight: 700, color: '#f1f5f9' }}>
              ${riskProfile.max_daily_loss.toLocaleString()}
            </div>
          </div>
          <div style={{ width: '1px', background: '#334155' }} />
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: '11px', color: '#64748b' }}>风险金额</div>
            <div style={{ fontSize: '18px', fontWeight: 700, color: '#ef4444' }}>
              ${riskProfile.risk_amount.toLocaleString()}
            </div>
          </div>
        </div>
      )}
      
      {/* 主要内容区 */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px' }}>
        {/* 左侧：计算器 */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          {/* 算法切换 */}
          <div style={{ background: '#1e293b', borderRadius: '12px', padding: '16px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <div style={{ fontSize: '14px', fontWeight: 600, color: '#f1f5f9' }}>
                算法模式
              </div>
              <Settings size={16} style={{ color: '#64748b' }} />
            </div>
            <AlgoModeToggle mode={algoMode} onChange={setAlgoMode} />
            <div style={{ fontSize: '11px', color: '#64748b', marginTop: '8px' }}>
              {algoMode === 'simple' 
                ? '简单动态百分比：根据资金规模自动调整风险'
                : '复合算法：ATR + 凯利公式 + 信心度 加权'}
            </div>
          </div>
          
          {/* 风险滑块 */}
          <RiskSlider value={risk_slider_value} onChange={setRiskSlider} />
          
          {/* 仓位计算器 */}
          <div style={{ background: '#1e293b', borderRadius: '12px', padding: '16px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <div style={{ fontSize: '14px', fontWeight: 600, color: '#f1f5f9' }}>
                仓位计算器
              </div>
              <Calculator size={16} style={{ color: '#8b5cf6' }} />
            </div>
            <PositionCalculator onCalculate={handleCalculate} />
          </div>
        </div>
        
        {/* 右侧：持仓和历史 */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          {/* 当前持仓 */}
          <div style={{ background: '#1e293b', borderRadius: '12px', padding: '16px' }}>
            <div style={{ fontSize: '14px', fontWeight: 600, color: '#f1f5f9', marginBottom: '16px' }}>
              当前持仓 ({openOrders.length})
            </div>
            <OpenOrders orders={openOrders} />
          </div>
          
          {/* 历史记录 */}
          <div style={{ background: '#1e293b', borderRadius: '12px', padding: '16px' }}>
            <div style={{ fontSize: '14px', fontWeight: 600, color: '#f1f5f9', marginBottom: '16px' }}>
              历史记录
            </div>
            <HistoryTable history={history} />
          </div>
        </div>
      </div>
    </div>
  );
}

export default PositionManager;
