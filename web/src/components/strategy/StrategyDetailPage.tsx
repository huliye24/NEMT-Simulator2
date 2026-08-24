/**
 * Copyright 2026 NEMT Lab
 *
 * 策略详情页组件
 */

import React from 'react';
import { ArrowLeft, Play, Pause, Settings, Cpu, FlaskConical } from 'lucide-react';
import type { StrategyStatus } from '../../stores';
import { useStrategyStore } from '../../stores';
import { useDualBufferStore } from '../../stores/dualBufferStore';
import { useUIStore } from '../../stores/uiStore';
import { DocReader } from './DocReader';

interface StrategyDetailPageProps {
  strategyId: string;
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

export function StrategyDetailPage({ strategyId }: StrategyDetailPageProps) {
  const strategy = useStrategyStore(state => 
    state.strategies.find(s => s.id === strategyId)
  );
  const toggleStrategyStatus = useStrategyStore(state => state.toggleStrategyStatus);
  const closeStrategyDetail = useUIStore(state => state.closeStrategyDetail);
  const setActiveView = useUIStore(state => state.setActiveView);
  const loadStrategy = useDualBufferStore(state => state.loadStrategy);

  if (!strategy) {
    return (
      <div style={{
        position: 'fixed',
        inset: 0,
        background: '#020617',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 1000
      }}>
        <div style={{ color: '#94a3b8', fontSize: '16px' }}>策略不存在</div>
      </div>
    );
  }

  const colors = statusColors[strategy.status];

  const handleBacktest = () => {
    loadStrategy(strategy);
    closeStrategyDetail();
    setActiveView('dualbuffer');
  };

  const handleToggle = () => {
    toggleStrategyStatus(strategy.id);
  };

  return (
    <div style={{
      position: 'fixed',
      inset: 0,
      background: '#020617',
      overflow: 'auto',
      zIndex: 1000
    }}>
      {/* 顶部导航栏 */}
      <div style={{
        position: 'sticky',
        top: 0,
        background: '#0f172a',
        borderBottom: '1px solid #334155',
        padding: '16px 24px',
        display: 'flex',
        alignItems: 'center',
        gap: '16px',
        zIndex: 10
      }}>
        <button
          onClick={closeStrategyDetail}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            padding: '8px 16px',
            borderRadius: '8px',
            border: '1px solid #334155',
            background: 'transparent',
            color: '#94a3b8',
            cursor: 'pointer',
            fontSize: '14px'
          }}
        >
          <ArrowLeft size={16} />
          返回
        </button>
        <h1 style={{ margin: 0, fontSize: '18px', fontWeight: 'bold', color: '#e2e8f0' }}>
          策略详情
        </h1>
      </div>

      {/* 内容区域 */}
      <div style={{ maxWidth: '900px', margin: '0 auto', padding: '32px 24px' }}>
        {/* 策略头部 */}
        <div style={{
          background: '#1e293b',
          borderRadius: '16px',
          padding: '24px',
          border: '1px solid #334155',
          marginBottom: '24px'
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '20px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
              <div style={{
                width: '56px',
                height: '56px',
                borderRadius: '12px',
                background: 'linear-gradient(135deg, #8b5cf6 0%, #6366f1 100%)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}>
                <Cpu size={28} color="#fff" />
              </div>
              <div>
                <h2 style={{ margin: 0, fontSize: '24px', fontWeight: 'bold', color: '#e2e8f0' }}>
                  {strategy.name}
                </h2>
                <p style={{ margin: '4px 0 0', fontSize: '14px', color: '#64748b' }}>
                  by {strategy.author} · v{strategy.version}
                </p>
              </div>
            </div>

            <div style={{
              padding: '6px 16px',
              borderRadius: '20px',
              background: colors.bg,
              border: `1px solid ${colors.border}`,
              color: colors.text,
              fontSize: '13px',
              fontWeight: '500'
            }}>
              {statusLabels[strategy.status]}
            </div>
          </div>

          <p style={{
            fontSize: '15px',
            color: '#94a3b8',
            margin: 0,
            lineHeight: 1.6
          }}>
            {strategy.description}
          </p>

          {/* 标签 */}
          <div style={{ display: 'flex', gap: '8px', marginTop: '16px', flexWrap: 'wrap' }}>
            {strategy.tags.map(tag => (
              <span key={tag} style={{
                padding: '6px 12px',
                borderRadius: '8px',
                background: '#334155',
                fontSize: '13px',
                color: '#94a3b8'
              }}>
                {tag}
              </span>
            ))}
          </div>
        </div>

        {/* 指标卡片 */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(4, 1fr)',
          gap: '16px',
          marginBottom: '24px'
        }}>
          {[
            { label: '交易数', value: strategy.metrics.totalTrades.toLocaleString(), color: '#e2e8f0' },
            { label: '胜率', value: `${(strategy.metrics.winRate * 100).toFixed(1)}%`, color: strategy.metrics.winRate > 0.5 ? '#10b981' : '#ef4444' },
            { label: '盈亏', value: `$${strategy.metrics.totalPnL.toLocaleString()}`, color: strategy.metrics.totalPnL > 0 ? '#10b981' : '#ef4444' },
            { label: '夏普比率', value: strategy.metrics.sharpeRatio.toFixed(2), color: '#3b82f6' },
          ].map(metric => (
            <div key={metric.label} style={{
              background: '#1e293b',
              borderRadius: '12px',
              padding: '20px',
              border: '1px solid #334155',
              textAlign: 'center'
            }}>
              <div style={{
                fontSize: '24px',
                fontWeight: 'bold',
                color: metric.color,
                fontFamily: 'monospace'
              }}>
                {metric.value}
              </div>
              <div style={{ fontSize: '12px', color: '#64748b', marginTop: '4px' }}>{metric.label}</div>
            </div>
          ))}
        </div>

        {/* README 内容 - Notion 风格阅读器 */}
        <div style={{
          background: '#1e293b',
          borderRadius: '16px',
          border: '1px solid #334155',
          marginBottom: '24px',
          overflow: 'hidden'
        }}>
          <div style={{ height: '600px' }}>
            <DocReader
              content={strategy.readme}
              title={strategy.name}
            />
          </div>
        </div>

        {/* 底部操作按钮 */}
        <div style={{
          display: 'flex',
          gap: '12px',
          justifyContent: 'center'
        }}>
          <button
            onClick={handleBacktest}
            style={{
              flex: 1,
              maxWidth: '200px',
              padding: '14px 24px',
              borderRadius: '10px',
              border: 'none',
              background: 'linear-gradient(135deg, #8b5cf6, #6366f1)',
              color: '#fff',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '8px',
              fontSize: '14px',
              fontWeight: '600'
            }}
          >
            <FlaskConical size={16} />
            回测
          </button>
          <button
            onClick={handleToggle}
            style={{
              flex: 1,
              maxWidth: '200px',
              padding: '14px 24px',
              borderRadius: '10px',
              border: 'none',
              background: strategy.status === 'running' ? '#ef4444' : '#10b981',
              color: '#fff',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '8px',
              fontSize: '14px',
              fontWeight: '600'
            }}
          >
            {strategy.status === 'running' ? (
              <><Pause size={16} /> 暂停</>
            ) : (
              <><Play size={16} /> 运行</>
            )}
          </button>
          <button
            style={{
              flex: 1,
              maxWidth: '200px',
              padding: '14px 24px',
              borderRadius: '10px',
              border: '1px solid #475569',
              background: 'transparent',
              color: '#94a3b8',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '8px',
              fontSize: '14px',
              fontWeight: '600'
            }}
          >
            <Settings size={16} />
            设置
          </button>
        </div>
      </div>
    </div>
  );
}
