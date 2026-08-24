/**
 * Copyright 2026 NEMT Lab
 *
 * 策略卡片组件
 */

import React from 'react';
import { Play, Pause, Settings, Cpu, FlaskConical } from 'lucide-react';
import type { Strategy, StrategyStatus } from '../../stores';
import { useDualBufferStore } from '../../stores/dualBufferStore';
import { useUIStore } from '../../stores/uiStore';

interface StrategyCardProps {
  strategy: Strategy;
  onSelect: () => void;
  onToggle: () => void;
}

const statusColors: Record<StrategyStatus, { bg: string; text: string; border: string }> = {
  draft: { bg: '#64748b20', text: '#94a3b8', border: '#475569' },
  testing: { bg: '#f59e0b20', text: '#fbbf24', border: '#f59e0b44' },
  running: { bg: '#10b98120', text: '#34d399', border: '#10b98144' },
  paused: { bg: '#3b82f620', text: '#60a5fa', border: '#3b82f644' },
  archived: { bg: '#47556920', text: '#64748b', border: '#47556944' }
};

const statusLabels: Record<StrategyStatus, string> = {
  draft: '草稿',
  testing: '测试中',
  running: '运行中',
  paused: '已暂停',
  archived: '已归档'
};

export function StrategyCard({ strategy, onSelect, onToggle }: StrategyCardProps) {
  const colors = statusColors[strategy.status];
  const loadStrategy = useDualBufferStore(s => s.loadStrategy);
  const setActiveView = useUIStore(s => s.setActiveView);

  const handleBacktest = (e: React.MouseEvent) => {
    e.stopPropagation();
    // 加载策略到双缓冲
    loadStrategy(strategy);
    // 跳转到双缓冲视图
    setActiveView('dualbuffer');
  };

  return (
    <div
      style={{
        background: '#1e293b',
        borderRadius: '16px',
        padding: '20px',
        border: '1px solid #334155',
        transition: 'all 0.2s',
        cursor: 'pointer'
      }}
      onClick={onSelect}
      onMouseEnter={(e) => {
        e.currentTarget.style.borderColor = '#8b5cf6';
        e.currentTarget.style.transform = 'translateY(-2px)';
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.borderColor = '#334155';
        e.currentTarget.style.transform = 'translateY(0)';
      }}
    >
      {/* 头部区域 */}
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '16px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{
            width: '40px',
            height: '40px',
            borderRadius: '10px',
            background: 'linear-gradient(135deg, #8b5cf6 0%, #6366f1 100%)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}>
            <Cpu size={20} color="#fff" />
          </div>
          <div>
            <h3 style={{ margin: 0, fontSize: '16px', fontWeight: 'bold', color: '#e2e8f0' }}>
              {strategy.name}
            </h3>
            <p style={{ margin: '2px 0 0', fontSize: '12px', color: '#64748b' }}>
              by {strategy.author}
            </p>
          </div>
        </div>

        <div style={{
          padding: '4px 12px',
          borderRadius: '20px',
          background: colors.bg,
          border: `1px solid ${colors.border}`,
          color: colors.text,
          fontSize: '12px',
          fontWeight: '500'
        }}>
          {statusLabels[strategy.status]}
        </div>
      </div>

      {/* 描述 */}
      <p style={{
        fontSize: '13px',
        color: '#94a3b8',
        margin: '0 0 16px',
        lineHeight: 1.5
      }}>
        {strategy.description}
      </p>

      {/* 标签 */}
      <div style={{ display: 'flex', gap: '6px', marginBottom: '16px', flexWrap: 'wrap' }}>
        {strategy.tags.map(tag => (
          <span key={tag} style={{
            padding: '4px 10px',
            borderRadius: '6px',
            background: '#334155',
            fontSize: '11px',
            color: '#94a3b8'
          }}>
            {tag}
          </span>
        ))}
      </div>

      {/* 指标 */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(4, 1fr)',
        gap: '12px',
        padding: '12px',
        background: '#0f172a',
        borderRadius: '8px',
        marginBottom: '16px'
      }}>
        {[
          { label: '交易数', value: strategy.metrics.totalTrades.toLocaleString() },
          { label: '胜率', value: `${(strategy.metrics.winRate * 100).toFixed(1)}%`, color: strategy.metrics.winRate > 0.5 ? '#10b981' : '#ef4444' },
          { label: '盈亏', value: `$${strategy.metrics.totalPnL.toLocaleString()}`, color: strategy.metrics.totalPnL > 0 ? '#10b981' : '#ef4444' },
          { label: '夏普', value: strategy.metrics.sharpeRatio.toFixed(2), color: '#3b82f6' },
        ].map(metric => (
          <div key={metric.label} style={{ textAlign: 'center' }}>
            <div style={{
              fontSize: '14px',
              fontWeight: 'bold',
              color: metric.color || '#e2e8f0',
              fontFamily: 'monospace'
            }}>
              {metric.value}
            </div>
            <div style={{ fontSize: '10px', color: '#64748b' }}>{metric.label}</div>
          </div>
        ))}
      </div>

      {/* 操作按钮 */}
      <div style={{ display: 'flex', gap: '8px' }}>
        <button
          onClick={handleBacktest}
          style={{
            flex: 1,
            padding: '10px',
            borderRadius: '8px',
            border: 'none',
            background: 'linear-gradient(135deg, #8b5cf6, #6366f1)',
            color: '#fff',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '6px',
            fontSize: '13px',
            fontWeight: '500'
          }}
        >
          <FlaskConical size={14} />
          回测
        </button>
        <button
          onClick={(e) => { e.stopPropagation(); onToggle(); }}
          style={{
            flex: 1,
            padding: '10px',
            borderRadius: '8px',
            border: 'none',
            background: strategy.status === 'running' ? '#ef4444' : '#10b981',
            color: '#fff',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '6px',
            fontSize: '13px',
            fontWeight: '500'
          }}
        >
          {strategy.status === 'running' ? (
            <><Pause size={14} /> 暂停</>
          ) : (
            <><Play size={14} /> 运行</>
          )}
        </button>
        <button
          onClick={(e) => e.stopPropagation()}
          style={{
            padding: '10px 16px',
            borderRadius: '8px',
            border: '1px solid #475569',
            background: 'transparent',
            color: '#94a3b8',
            cursor: 'pointer',
            fontSize: '13px'
          }}
        >
          <Settings size={14} />
        </button>
      </div>
    </div>
  );
}
