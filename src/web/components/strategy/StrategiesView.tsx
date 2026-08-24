/**
 * Copyright 2026 NEMT Lab
 *
 * 策略市场视图
 */

import React, { useState } from 'react';
import { Plus, Container, Layers, Shield, Zap, Dna, Box } from 'lucide-react';
import { useStrategies, useStrategyStore } from '../../stores';
import { StrategyCard } from './StrategyCard';
import { CreateStrategyDialog } from './CreateStrategyDialog';
import { EvolutionIndicator, EvolutionPanel } from '../../evolution';
import { GenerationDemoPanel } from '../generationDemo';
import { PerformanceIndicator } from '../../infrastructure/performance';
import { SortableList, DragHandle } from '../../infrastructure/dragSort';
import { eventBus, EventType } from '../../events';

export function StrategiesView() {
  const strategies = useStrategies();
  const { toggleStrategyStatus, selectStrategy, addStrategy } = useStrategyStore();
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);

  const handleCreateStrategy = () => {
    setIsCreateDialogOpen(true);
  };

  return (
    <>
      {/* 工具栏 */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: '24px'
      }}>
        <div>
          <h2 style={{ margin: 0, fontSize: '20px', fontWeight: 'bold' }}>
            策略市场
          </h2>
          <p style={{ margin: '4px 0 0', fontSize: '13px', color: '#64748b' }}>
            发现、部署和管理量化交易策略
          </p>
        </div>

        <button
          onClick={handleCreateStrategy}
          style={{
            padding: '12px 24px',
            borderRadius: '8px',
            border: 'none',
            background: 'linear-gradient(135deg, #8b5cf6 0%, #6366f1 100%)',
            color: '#fff',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            fontSize: '14px',
            fontWeight: '500'
          }}
        >
          <Plus size={16} />
          创建策略
        </button>
      </div>

      {/* 演化引擎状态指示器 */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        gap: '16px',
        marginBottom: '20px',
        padding: '12px 16px',
        background: '#0f172a',
        borderRadius: '8px',
        border: '1px solid #334155'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Dna size={16} style={{ color: '#8b5cf6' }} />
          <span style={{ fontSize: '13px', color: '#94a3b8' }}>演化引擎</span>
        </div>
        <EvolutionIndicator compact />
      </div>

      {/* 策略列表 - 可拖拽排序 */}
      <SortableList
        items={strategies}
        keyExtractor={(s) => s.id}
        onReorder={(newStrategies) => {
          // 观察排序事件
          eventBus.emit(EventType.STRATEGY_UPDATED, {
            strategyId: 'bulk',
            changes: { order: newStrategies.map(s => s.id) }
          });
        }}
        renderItem={(strategy) => (
          <div style={{ marginBottom: '12px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
              <DragHandle label="拖动排序" />
              <span style={{ fontSize: '11px', color: '#64748b' }}>
                拖动调整顺序
              </span>
            </div>
            <StrategyCard
              strategy={strategy}
              onSelect={() => {
                selectStrategy(strategy.id);
                eventBus.emit(EventType.STRATEGY_SELECTED, strategy.id);
              }}
              onToggle={() => {
                toggleStrategyStatus(strategy.id);
                eventBus.emit(EventType.STRATEGY_STATUS_CHANGED, {
                  strategyId: strategy.id,
                  oldStatus: strategy.status,
                  newStatus: strategy.status === 'running' ? 'paused' : 'running'
                });
              }}
            />
          </div>
        )}
        itemHeight={380}
      />

      {/* 平台说明 */}
      <div style={{
        marginTop: '48px',
        padding: '32px',
        background: 'linear-gradient(135deg, #8b5cf620 0%, #3b82f620 100%)',
        borderRadius: '16px',
        border: '1px solid #8b5cf644'
      }}>
        <h3 style={{
          margin: '0 0 16px',
          fontSize: '18px',
          display: 'flex',
          alignItems: 'center',
          gap: '12px'
        }}>
          <Container size={24} style={{ color: '#8b5cf6' }} />
          关于 NEMT Platform
        </h3>
        <p style={{
          color: '#94a3b8',
          lineHeight: 1.8,
          fontSize: '14px'
        }}>
          NEMT Platform 是一个策略容器平台，核心理念源自抖音模式：
          <br /><br />
          <strong style={{ color: '#a78bfa' }}>抖音不生产视频，NEMT 不生产策略。</strong>
          <br /><br />
          我们提供的是策略运行的容器、基础设施和服务：
        </p>
        <div style={{ display: 'flex', gap: '24px', marginTop: '20px' }}>
          {[
            { icon: Box, title: '胶囊架构', desc: 'Market/Signal/Risk/Execution' },
            { icon: Layers, title: '容器编排', desc: '策略隔离与弹性扩展' },
            { icon: Shield, title: '风险管理', desc: '多层风控保障' },
            { icon: Zap, title: '实时执行', desc: '低延迟订单执行' },
            { icon: Dna, title: '自我演化', desc: '系统结构规则递归展开' },
          ].map(item => (
            <div key={item.title} style={{
              padding: '16px',
              background: '#0f172a',
              borderRadius: '8px',
              flex: 1
            }}>
              <item.icon size={24} style={{ color: '#8b5cf6', marginBottom: '8px' }} />
              <div style={{ fontWeight: 'bold', marginBottom: '4px' }}>{item.title}</div>
              <div style={{ fontSize: '12px', color: '#64748b' }}>{item.desc}</div>
            </div>
          ))}
        </div>
      </div>

      {/* 演化引擎面板 */}
      <div style={{ marginTop: '32px' }}>
        <EvolutionPanel />
      </div>

      {/* 生成系统演示 */}
      <GenerationDemoPanel />

      {/* 性能监控 */}
      <PerformanceIndicator />

      {/* 创建策略对话框 */}
      <CreateStrategyDialog
        isOpen={isCreateDialogOpen}
        onClose={() => setIsCreateDialogOpen(false)}
      />
    </>
  );
}
