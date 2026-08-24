/**
 * Copyright 2026 NEMT Lab
 *
 * 演化引擎展示面板
 * 展示系统自我演化能力
 */

import React, { useState, useEffect } from 'react';
import { 
  Sparkles, 
  Eye, 
  GitBranch, 
  Layers, 
  Activity,
  Play, 
  Pause, 
  RotateCcw,
  TrendingUp,
  Clock,
  CheckCircle,
  AlertCircle,
  Loader2
} from 'lucide-react';
import { 
  evolutionEngine, 
  EvolutionState, 
  Observation,
  DiscoveredPattern,
  GenerationRule,
  GeneratedStructure
} from '../evolution/engine';
import { useEvolution } from '../evolution/engine';

const phases = [
  { id: 'observing', name: '观察', icon: Eye, color: '#3b82f6', description: '感知系统行为' },
  { id: 'analyzing', name: '分析', icon: Activity, color: '#8b5cf6', description: '发现行为模式' },
  { id: 'generating', name: '生成', icon: Sparkles, color: '#f59e0b', description: '抽取生成规则' },
  { id: 'adapting', name: '适应', icon: TrendingUp, color: '#10b981', description: '评估优化结构' },
  { id: 'idle', name: '空闲', icon: Clock, color: '#64748b', description: '等待下次迭代' },
];

export function EvolutionPanel() {
  const { state, summary, observe, evolve, start, stop, reset } = useEvolution();
  const [isRunning, setIsRunning] = useState(false);

  const handleToggle = () => {
    if (isRunning) {
      stop();
    } else {
      start(3000);
    }
    setIsRunning(!isRunning);
  };

  // 模拟观察
  const simulateObservation = () => {
    const actions = ['strategy_run', 'backtest_start', 'data_fetch', 'trade_execute', 'risk_check'];
    const action = actions[Math.floor(Math.random() * actions.length)];
    
    observe({
      type: 'action',
      source: 'platform',
      action,
      payload: { 
        timestamp: Date.now(),
        duration: Math.random() * 1000 
      }
    });
  };

  // 手动演化一步
  const handleEvolve = () => {
    simulateObservation();
    const result = evolve({ observations: summary.observations });
    if (result) {
      console.log('[Evolution] Generated structure:', result);
    }
  };

  const getPhaseInfo = () => phases.find(p => p.id === state.phase) || phases[4];

  return (
    <div style={{
      height: '100%',
      display: 'flex',
      flexDirection: 'column',
      background: '#020617',
    }}>
      {/* 控制栏 */}
      <div style={{
        padding: '16px 24px',
        borderBottom: '1px solid #1e293b',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
      }}>
        {/* 演化阶段指示器 */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
        }}>
          {phases.map((phase, i) => {
            const Icon = phase.icon;
            const isActive = state.phase === phase.id;
            const isPast = phases.findIndex(p => p.id === state.phase) > i;

            return (
              <React.Fragment key={phase.id}>
                {i > 0 && (
                  <div style={{
                    width: '32px',
                    height: '2px',
                    background: isPast ? phase.color : '#334155',
                  }} />
                )}
                <div
                  style={{
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    gap: '4px',
                    padding: '8px 12px',
                    background: isActive ? `${phase.color}20` : 'transparent',
                    borderRadius: '8px',
                    transition: 'all 0.3s',
                  }}
                >
                  <Icon 
                    size={18} 
                    style={{ 
                      color: isActive || isPast ? phase.color : '#475569',
                      animation: isActive ? 'pulse 1s infinite' : 'none',
                    }} 
                  />
                  <span style={{
                    fontSize: '11px',
                    color: isActive || isPast ? phase.color : '#475569',
                    fontWeight: isActive ? '600' : '400',
                  }}>
                    {phase.name}
                  </span>
                </div>
              </React.Fragment>
            );
          })}
        </div>

        {/* 控制按钮 */}
        <div style={{ display: 'flex', gap: '8px' }}>
          <button
            onClick={simulateObservation}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              padding: '10px 16px',
              background: '#334155',
              border: '1px solid #475569',
              borderRadius: '8px',
              cursor: 'pointer',
              color: '#e2e8f0',
              fontSize: '13px',
            }}
          >
            <Eye size={14} />
            模拟观察
          </button>
          <button
            onClick={handleEvolve}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              padding: '10px 16px',
              background: '#8b5cf620',
              border: '1px solid #8b5cf6',
              borderRadius: '8px',
              cursor: 'pointer',
              color: '#a78bfa',
              fontSize: '13px',
            }}
          >
            <GitBranch size={14} />
            演化一步
          </button>
          <button
            onClick={handleToggle}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              padding: '10px 20px',
              background: isRunning ? '#ef444420' : '#10b98120',
              border: `1px solid ${isRunning ? '#ef4444' : '#10b981'}`,
              borderRadius: '8px',
              cursor: 'pointer',
              color: isRunning ? '#ef4444' : '#10b981',
              fontSize: '13px',
            }}
          >
            {isRunning ? <Pause size={14} /> : <Play size={14} />}
            {isRunning ? '停止' : '自动演化'}
          </button>
          <button
            onClick={reset}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              padding: '10px 16px',
              background: '#334155',
              border: '1px solid #475569',
              borderRadius: '8px',
              cursor: 'pointer',
              color: '#94a3b8',
              fontSize: '13px',
            }}
          >
            <RotateCcw size={14} />
            重置
          </button>
        </div>
      </div>

      {/* 统计数据 */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(5, 1fr)',
        gap: '16px',
        padding: '20px 24px',
        borderBottom: '1px solid #1e293b',
      }}>
        <StatCard 
          label="观察数" 
          value={state.observations} 
          icon={Eye} 
          color="#3b82f6" 
        />
        <StatCard 
          label="模式数" 
          value={state.patterns} 
          icon={Activity} 
          color="#8b5cf6" 
        />
        <StatCard 
          label="规则数" 
          value={state.rules} 
          icon={GitBranch} 
          color="#f59e0b" 
        />
        <StatCard 
          label="结构数" 
          value={state.structures} 
          icon={Layers} 
          color="#10b981" 
        />
        <StatCard 
          label="适应度" 
          value={(state.fitness * 100).toFixed(1) + '%'} 
          icon={TrendingUp} 
          color="#ec4899" 
        />
      </div>

      {/* 主内容区 */}
      <div style={{
        flex: 1,
        display: 'grid',
        gridTemplateColumns: '1fr 1fr',
        gap: '24px',
        padding: '24px',
        overflow: 'hidden',
      }}>
        {/* 左侧 - 观察与模式 */}
        <div style={{
          display: 'flex',
          flexDirection: 'column',
          gap: '16px',
          overflow: 'hidden',
        }}>
          {/* 观察事件 */}
          <div style={{
            background: '#0f172a',
            borderRadius: '12px',
            border: '1px solid #1e293b',
            padding: '20px',
            flex: 1,
            overflow: 'auto',
          }}>
            <h3 style={{
              fontSize: '14px',
              fontWeight: '600',
              color: '#e2e8f0',
              marginBottom: '16px',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
            }}>
              <Eye size={16} style={{ color: '#3b82f6' }} />
              最近观察
            </h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {summary.observations === 0 ? (
                <EmptyState message="暂无观察记录" />
              ) : (
                summary.patterns.slice(0, 8).map((pattern, i) => (
                  <div
                    key={pattern.id}
                    style={{
                      padding: '10px 12px',
                      background: '#1e293b',
                      borderRadius: '6px',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '12px',
                    }}
                  >
                    <div style={{
                      width: '8px',
                      height: '8px',
                      borderRadius: '50%',
                      background: pattern.confidence > 0.7 ? '#10b981' :
                                 pattern.confidence > 0.5 ? '#f59e0b' : '#64748b',
                    }} />
                    <div style={{ flex: 1 }}>
                      <div style={{ fontSize: '13px', color: '#e2e8f0' }}>
                        {pattern.name}
                      </div>
                      <div style={{ fontSize: '11px', color: '#64748b' }}>
                        置信度: {(pattern.confidence * 100).toFixed(0)}% | 出现: {pattern.occurrences}次
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* 发现模式 */}
          <div style={{
            background: '#0f172a',
            borderRadius: '12px',
            border: '1px solid #1e293b',
            padding: '20px',
            flex: 1,
            overflow: 'auto',
          }}>
            <h3 style={{
              fontSize: '14px',
              fontWeight: '600',
              color: '#e2e8f0',
              marginBottom: '16px',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
            }}>
              <Activity size={16} style={{ color: '#8b5cf6' }} />
              发现模式
            </h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {summary.patterns.length === 0 ? (
                <EmptyState message="暂无发现模式" />
              ) : (
                summary.patterns.slice(0, 6).map((pattern) => (
                  <div
                    key={pattern.id}
                    style={{
                      padding: '12px',
                      background: '#1e293b',
                      borderRadius: '8px',
                    }}
                  >
                    <div style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      marginBottom: '8px',
                    }}>
                      <span style={{ fontSize: '13px', color: '#e2e8f0', fontWeight: '500' }}>
                        {pattern.name}
                      </span>
                      <span style={{
                        fontSize: '11px',
                        padding: '2px 8px',
                        borderRadius: '4px',
                        background: pattern.confidence > 0.7 ? '#10b98120' : '#f59e0b20',
                        color: pattern.confidence > 0.7 ? '#10b981' : '#f59e0b',
                      }}>
                        {(pattern.confidence * 100).toFixed(0)}%
                      </span>
                    </div>
                    <div style={{ fontSize: '12px', color: '#94a3b8' }}>
                      {pattern.description}
                    </div>
                    <div style={{
                      marginTop: '8px',
                      height: '4px',
                      background: '#334155',
                      borderRadius: '2px',
                      overflow: 'hidden',
                    }}>
                      <div style={{
                        width: `${pattern.confidence * 100}%`,
                        height: '100%',
                        background: pattern.confidence > 0.7 ? '#10b981' : '#f59e0b',
                        transition: 'width 0.3s',
                      }} />
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>

        {/* 右侧 - 规则与结构 */}
        <div style={{
          display: 'flex',
          flexDirection: 'column',
          gap: '16px',
          overflow: 'hidden',
        }}>
          {/* 生成规则 */}
          <div style={{
            background: '#0f172a',
            borderRadius: '12px',
            border: '1px solid #1e293b',
            padding: '20px',
            flex: 1,
            overflow: 'auto',
          }}>
            <h3 style={{
              fontSize: '14px',
              fontWeight: '600',
              color: '#e2e8f0',
              marginBottom: '16px',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
            }}>
              <GitBranch size={16} style={{ color: '#f59e0b' }} />
              生成规则
            </h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {summary.rules.length === 0 ? (
                <EmptyState message="暂无生成规则" />
              ) : (
                summary.rules.map((rule) => (
                  <div
                    key={rule.id}
                    style={{
                      padding: '12px',
                      background: '#1e293b',
                      borderRadius: '8px',
                    }}
                  >
                    <div style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      marginBottom: '6px',
                    }}>
                      <span style={{ fontSize: '13px', color: '#e2e8f0', fontWeight: '500' }}>
                        {rule.name}
                      </span>
                      <span style={{
                        fontSize: '11px',
                        padding: '2px 8px',
                        borderRadius: '4px',
                        background: rule.metadata.enabled ? '#10b98120' : '#475569',
                        color: rule.metadata.enabled ? '#10b981' : '#64748b',
                      }}>
                        {rule.metadata.enabled ? '启用' : '禁用'}
                      </span>
                    </div>
                    <div style={{ fontSize: '12px', color: '#94a3b8' }}>
                      优先级: {rule.priority.toFixed(1)} | 版本: v{rule.metadata.version}
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* 生成结构 */}
          <div style={{
            background: '#0f172a',
            borderRadius: '12px',
            border: '1px solid #1e293b',
            padding: '20px',
            flex: 1,
            overflow: 'auto',
          }}>
            <h3 style={{
              fontSize: '14px',
              fontWeight: '600',
              color: '#e2e8f0',
              marginBottom: '16px',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
            }}>
              <Layers size={16} style={{ color: '#10b981' }} />
              生成结构
            </h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {summary.structures.length === 0 ? (
                <EmptyState message="暂无生成结构" />
              ) : (
                summary.structures.slice(0, 5).map((structure) => (
                  <div
                    key={structure.id}
                    style={{
                      padding: '12px',
                      background: '#1e293b',
                      borderRadius: '8px',
                    }}
                  >
                    <div style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      marginBottom: '6px',
                    }}>
                      <span style={{ fontSize: '13px', color: '#e2e8f0', fontWeight: '500' }}>
                        {structure.name}
                      </span>
                      <span style={{
                        fontSize: '11px',
                        padding: '2px 8px',
                        borderRadius: '4px',
                        background: '#10b98120',
                        color: '#10b981',
                      }}>
                        {structure.type}
                      </span>
                    </div>
                    <div style={{
                      display: 'flex',
                      gap: '16px',
                      fontSize: '11px',
                      color: '#64748b',
                    }}>
                      <span>深度: {structure.depth}</span>
                      <span>适应度: {(structure.metadata.fitness * 100).toFixed(1)}%</span>
                      <span>使用: {structure.metadata.usageCount}次</span>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </div>

      {/* CSS 动画 */}
      <style>{`
        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.5; }
        }
      `}</style>
    </div>
  );
}

function StatCard({ label, value, icon: Icon, color }: { 
  label: string; 
  value: number | string; 
  icon: React.ElementType; 
  color: string;
}) {
  return (
    <div style={{
      padding: '16px',
      background: '#0f172a',
      borderRadius: '10px',
      border: '1px solid #1e293b',
    }}>
      <div style={{
        display: 'flex',
        alignItems: 'center',
        gap: '8px',
        marginBottom: '8px',
      }}>
        <Icon size={14} style={{ color }} />
        <span style={{ fontSize: '12px', color: '#64748b' }}>{label}</span>
      </div>
      <div style={{
        fontSize: '24px',
        fontWeight: 'bold',
        color: '#e2e8f0',
        fontFamily: 'monospace',
      }}>
        {value}
      </div>
    </div>
  );
}

function EmptyState({ message }: { message: string }) {
  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '32px',
      color: '#475569',
    }}>
      <AlertCircle size={24} style={{ marginBottom: '8px' }} />
      <span style={{ fontSize: '13px' }}>{message}</span>
    </div>
  );
}
