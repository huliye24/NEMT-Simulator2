/**
 * Copyright 2026 NEMT Lab
 *
 * 演化可视化 - 系统自我生成逻辑的可视化
 */

import React, { useState, useEffect, useRef } from 'react';
import { useEvolution } from './engine';
import { EvolutionState, DiscoveredPattern, GeneratedStructure } from './engine';

// ============================================
// 演化状态指示器
// ============================================

export const EvolutionIndicator: React.FC<{
  compact?: boolean;
}> = ({ compact = false }) => {
  const { state } = useEvolution();

  const phaseColors: Record<string, string> = {
    observing: '#3b82f6',
    analyzing: '#8b5cf6',
    generating: '#10b981',
    adapting: '#f59e0b',
    idle: '#64748b'
  };

  const phaseLabels: Record<string, string> = {
    observing: '观察',
    analyzing: '分析',
    generating: '生成',
    adapting: '适应',
    idle: '待机'
  };

  if (compact) {
    return (
      <div style={{
        display: 'flex',
        alignItems: 'center',
        gap: '8px',
        padding: '6px 12px',
        background: '#0f172a',
        borderRadius: '20px',
        border: '1px solid #334155'
      }}>
        <div style={{
          width: '8px',
          height: '8px',
          borderRadius: '50%',
          background: phaseColors[state.phase],
          animation: state.phase !== 'idle' ? 'pulse 1.5s infinite' : 'none'
        }} />
        <span style={{
          fontSize: '11px',
          color: '#94a3b8',
          fontFamily: 'monospace'
        }}>
          {phaseLabels[state.phase]}
        </span>
      </div>
    );
  }

  return (
    <div style={{
      padding: '16px',
      background: '#0f172a',
      borderRadius: '12px',
      border: '1px solid #334155'
    }}>
      <style>{`
        @keyframes pulse {
          0%, 100% { opacity: 1; transform: scale(1); }
          50% { opacity: 0.6; transform: scale(1.2); }
        }
      `}</style>

      <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '12px' }}>
        <div style={{
          width: '12px',
          height: '12px',
          borderRadius: '50%',
          background: phaseColors[state.phase],
          boxShadow: `0 0 12px ${phaseColors[state.phase]}`,
          animation: state.phase !== 'idle' ? 'pulse 1.5s infinite' : 'none'
        }} />
        <span style={{
          fontWeight: 600,
          color: phaseColors[state.phase]
        }}>
          {phaseLabels[state.phase]}
        </span>
        <span style={{
          fontSize: '11px',
          color: '#64748b',
          marginLeft: 'auto'
        }}>
          Level {state.level}
        </span>
      </div>

      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(4, 1fr)',
        gap: '8px',
        fontSize: '11px'
      }}>
        <div style={{ textAlign: 'center' }}>
          <div style={{ color: '#e2e8f0', fontWeight: 600 }}>{state.observations}</div>
          <div style={{ color: '#64748b' }}>观察</div>
        </div>
        <div style={{ textAlign: 'center' }}>
          <div style={{ color: '#e2e8f0', fontWeight: 600 }}>{state.patterns}</div>
          <div style={{ color: '#64748b' }}>模式</div>
        </div>
        <div style={{ textAlign: 'center' }}>
          <div style={{ color: '#e2e8f0', fontWeight: 600 }}>{state.rules}</div>
          <div style={{ color: '#64748b' }}>规则</div>
        </div>
        <div style={{ textAlign: 'center' }}>
          <div style={{ color: '#e2e8f0', fontWeight: 600 }}>{state.structures}</div>
          <div style={{ color: '#64748b' }}>结构</div>
        </div>
      </div>

      {/* 适应度条 */}
      <div style={{
        marginTop: '12px',
        height: '4px',
        background: '#1e293b',
        borderRadius: '2px',
        overflow: 'hidden'
      }}>
        <div style={{
          height: '100%',
          width: `${state.fitness * 100}%`,
          background: 'linear-gradient(90deg, #8b5cf6, #10b981)',
          transition: 'width 0.3s ease'
        }} />
      </div>
      <div style={{
        fontSize: '10px',
        color: '#64748b',
        marginTop: '4px',
        textAlign: 'right'
      }}>
        适应度: {(state.fitness * 100).toFixed(1)}%
      </div>
    </div>
  );
};

// ============================================
// 模式可视化
// ============================================

export const PatternVisualization: React.FC<{
  patterns: DiscoveredPattern[];
}> = ({ patterns }) => {
  if (patterns.length === 0) {
    return (
      <div style={{
        padding: '24px',
        textAlign: 'center',
        color: '#64748b'
      }}>
        暂无发现模式
      </div>
    );
  }

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      gap: '8px',
      maxHeight: '300px',
      overflowY: 'auto'
    }}>
      {patterns.slice(0, 10).map(pattern => (
        <div
          key={pattern.id}
          style={{
            padding: '12px',
            background: '#1e293b',
            borderRadius: '8px',
            border: `1px solid ${pattern.confidence > 0.7 ? '#10b981' : '#334155'}`
          }}
        >
          <div style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            marginBottom: '8px'
          }}>
            <span style={{
              fontSize: '12px',
              fontWeight: 500,
              color: '#e2e8f0'
            }}>
              {pattern.name}
            </span>
            <span style={{
              fontSize: '10px',
              color: '#10b981',
              fontFamily: 'monospace'
            }}>
              {(pattern.confidence * 100).toFixed(0)}%
            </span>
          </div>

          <div style={{
            fontSize: '11px',
            color: '#94a3b8',
            marginBottom: '8px'
          }}>
            {pattern.description}
          </div>

          <div style={{
            height: '2px',
            background: '#334155',
            borderRadius: '1px',
            overflow: 'hidden'
          }}>
            <div style={{
              height: '100%',
              width: `${pattern.confidence * 100}%`,
              background: '#8b5cf6'
            }} />
          </div>

          <div style={{
            display: 'flex',
            justifyContent: 'space-between',
            marginTop: '6px',
            fontSize: '10px',
            color: '#64748b'
          }}>
            <span>出现 {pattern.occurrences} 次</span>
            <span>{pattern.metrics.frequency.toFixed(2)}/s</span>
          </div>
        </div>
      ))}
    </div>
  );
};

// ============================================
// 结构树可视化
// ============================================

export const StructureTree: React.FC<{
  structures: GeneratedStructure[];
  selectedId?: string;
  onSelect?: (id: string) => void;
}> = ({ structures, selectedId, onSelect }) => {
  const renderNode = (structure: GeneratedStructure, depth = 0): React.ReactNode => {
    const isSelected = selectedId === structure.id;
    const fitness = structure.metadata.fitness;

    const fitnessColor = fitness > 0.7
      ? '#10b981'
      : fitness > 0.4
        ? '#f59e0b'
        : '#64748b';

    return (
      <div key={structure.id} style={{ marginLeft: depth * 16 }}>
        <div
          onClick={() => onSelect?.(structure.id)}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            padding: '8px 12px',
            background: isSelected ? '#8b5cf620' : 'transparent',
            borderRadius: '6px',
            cursor: 'pointer',
            border: `1px solid ${isSelected ? '#8b5cf6' : 'transparent'}`,
            transition: 'all 0.15s'
          }}
          onMouseEnter={(e) => {
            if (!isSelected) {
              e.currentTarget.style.background = '#1e293b';
            }
          }}
          onMouseLeave={(e) => {
            if (!isSelected) {
              e.currentTarget.style.background = 'transparent';
            }
          }}
        >
          {/* 深度指示 */}
          <div style={{ display: 'flex', gap: '2px' }}>
            {Array.from({ length: depth + 1 }).map((_, i) => (
              <div
                key={i}
                style={{
                  width: '4px',
                  height: '4px',
                  borderRadius: '50%',
                  background: i === depth ? fitnessColor : '#334155'
                }}
              />
            ))}
          </div>

          {/* 结构图标 */}
          <div style={{
            width: '20px',
            height: '20px',
            borderRadius: '4px',
            background: '#8b5cf620',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: '10px'
          }}>
            {structure.type === 'component' ? '◈' : structure.type === 'layout' ? '▣' : '◆'}
          </div>

          {/* 名称 */}
          <span style={{
            fontSize: '12px',
            color: isSelected ? '#a78bfa' : '#e2e8f0',
            flex: 1
          }}>
            {structure.name}
          </span>

          {/* 适应度 */}
          <span style={{
            fontSize: '10px',
            color: fitnessColor,
            fontFamily: 'monospace'
          }}>
            {(fitness * 100).toFixed(0)}%
          </span>
        </div>

        {/* 递归渲染子结构 */}
        {structures
          .filter(s => s.lineage.includes(structure.id))
          .sort((a, b) => a.metadata.createdAt - b.metadata.createdAt)
          .map(child => renderNode(child, depth + 1))}
      </div>
    );
  };

  // 找到根结构
  const roots = structures.filter(s => s.lineage.length === 0);

  if (roots.length === 0) {
    return (
      <div style={{
        padding: '24px',
        textAlign: 'center',
        color: '#64748b'
      }}>
        暂无生成结构
      </div>
    );
  }

  return (
    <div style={{
      padding: '12px',
      maxHeight: '400px',
      overflowY: 'auto'
    }}>
      {roots
        .sort((a, b) => b.metadata.createdAt - a.metadata.createdAt)
        .map(root => renderNode(root))}
    </div>
  );
};

// ============================================
// 演化面板
// ============================================

export const EvolutionPanel: React.FC = () => {
  const { state, summary, observe, evolve, start, stop, reset } = useEvolution();
  const [selectedTab, setSelectedTab] = useState<'patterns' | 'structures' | 'rules'>('patterns');
  const [isRunning, setIsRunning] = useState(false);

  // 模拟观察
  useEffect(() => {
    const interval = setInterval(() => {
      observe({
        type: 'action',
        source: 'user',
        action: ['click', 'hover', 'type', 'drag'][Math.floor(Math.random() * 4)],
        payload: {
          component: ['StrategyCard', 'CapsuleBar', 'Sidebar'][Math.floor(Math.random() * 3)],
          timestamp: Date.now()
        }
      });
    }, 2000);

    return () => clearInterval(interval);
  }, [observe]);

  const handleToggle = () => {
    if (isRunning) {
      stop();
    } else {
      start(3000);
    }
    setIsRunning(!isRunning);
  };

  return (
    <div style={{
      background: '#0f172a',
      borderRadius: '12px',
      border: '1px solid #334155',
      overflow: 'hidden'
    }}>
      {/* 头部 */}
      <div style={{
        padding: '16px',
        borderBottom: '1px solid #334155',
        display: 'flex',
        alignItems: 'center',
        gap: '12px'
      }}>
        <div style={{
          fontSize: '14px',
          fontWeight: 600,
          color: '#a78bfa'
        }}>
          系统演化引擎
        </div>

        <EvolutionIndicator compact />

        <div style={{ marginLeft: 'auto', display: 'flex', gap: '8px' }}>
          <button
            onClick={handleToggle}
            style={{
              padding: '6px 12px',
              borderRadius: '6px',
              border: 'none',
              background: isRunning ? '#ef4444' : '#10b981',
              color: '#fff',
              fontSize: '11px',
              cursor: 'pointer'
            }}
          >
            {isRunning ? '停止' : '启动'}
          </button>

          <button
            onClick={() => evolve()}
            style={{
              padding: '6px 12px',
              borderRadius: '6px',
              border: '1px solid #475569',
              background: 'transparent',
              color: '#94a3b8',
              fontSize: '11px',
              cursor: 'pointer'
            }}
          >
            演化一步
          </button>

          <button
            onClick={reset}
            style={{
              padding: '6px 12px',
              borderRadius: '6px',
              border: '1px solid #475569',
              background: 'transparent',
              color: '#94a3b8',
              fontSize: '11px',
              cursor: 'pointer'
            }}
          >
            重置
          </button>
        </div>
      </div>

      {/* 标签 */}
      <div style={{
        display: 'flex',
        borderBottom: '1px solid #334155'
      }}>
        {(['patterns', 'structures', 'rules'] as const).map(tab => (
          <button
            key={tab}
            onClick={() => setSelectedTab(tab)}
            style={{
              flex: 1,
              padding: '10px',
              border: 'none',
              background: selectedTab === tab ? '#1e293b' : 'transparent',
              color: selectedTab === tab ? '#a78bfa' : '#64748b',
              fontSize: '12px',
              cursor: 'pointer',
              borderBottom: selectedTab === tab ? '2px solid #8b5cf6' : '2px solid transparent'
            }}
          >
            {tab === 'patterns' ? '模式' : tab === 'structures' ? '结构' : '规则'}
          </button>
        ))}
      </div>

      {/* 内容 */}
      <div style={{ padding: '16px' }}>
        {selectedTab === 'patterns' && (
          <PatternVisualization patterns={summary.patterns} />
        )}

        {selectedTab === 'structures' && (
          <StructureTree structures={summary.structures} />
        )}

        {selectedTab === 'rules' && (
          <div style={{ fontSize: '12px', color: '#94a3b8' }}>
            {summary.rules.length === 0
              ? '暂无规则，请先发现模式'
              : summary.rules.map(rule => (
                <div key={rule.id} style={{
                  padding: '8px',
                  marginBottom: '8px',
                  background: '#1e293b',
                  borderRadius: '6px'
                }}>
                  <div style={{ color: '#e2e8f0', fontWeight: 500 }}>{rule.name}</div>
                  <div style={{ color: '#64748b', fontSize: '11px' }}>
                    优先级: {rule.priority.toFixed(1)} | 版本: v{rule.metadata.version}
                  </div>
                </div>
              ))
            }
          </div>
        )}
      </div>
    </div>
  );
};

// ============================================
// 演化状态可视化 (Canvas)
// ============================================

export const EvolutionCanvas: React.FC<{
  width?: number;
  height?: number;
}> = ({ width = 600, height = 400 }) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const { summary } = useEvolution();
  const [nodes, setNodes] = useState<Array<{x: number; y: number; vx: number; vy: number; structure: GeneratedStructure}>>([]);

  useEffect(() => {
    // 初始化节点
    const newNodes = summary.structures.map((s, i) => {
      const angle = (i / Math.max(summary.structures.length, 1)) * Math.PI * 2;
      return {
        x: width / 2 + Math.cos(angle) * 100,
        y: height / 2 + Math.sin(angle) * 100,
        vx: (Math.random() - 0.5) * 2,
        vy: (Math.random() - 0.5) * 2,
        structure: s
      };
    });
    setNodes(newNodes);
  }, [summary.structures.length, width, height]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animationId: number;

    const animate = () => {
      ctx.fillStyle = '#020617';
      ctx.fillRect(0, 0, width, height);

      // 更新位置
      setNodes(prevNodes => prevNodes.map(node => {
        let { x, y, vx, vy, structure } = node;

        // 边界检查
        if (x < 50 || x > width - 50) vx *= -1;
        if (y < 50 || y > height - 50) vy *= -1;

        // 中心引力
        vx += (width / 2 - x) * 0.001;
        vy += (height / 2 - y) * 0.001;

        // 节点间斥力
        prevNodes.forEach(other => {
          if (other === node) return;
          const dx = x - other.x;
          const dy = y - other.y;
          const dist = Math.sqrt(dx * dx + dy * dy) || 1;
          vx += dx / dist * 0.5;
          vy += dy / dist * 0.5;
        });

        x += vx;
        y += vy;

        return { ...node, x, y, vx, vy };
      }));

      // 绘制连线
      ctx.strokeStyle = '#334155';
      ctx.lineWidth = 1;
      nodes.forEach(node => {
        node.structure.lineage.forEach(parentId => {
          const parent = nodes.find(n => n.structure.id === parentId);
          if (parent) {
            ctx.beginPath();
            ctx.moveTo(parent.x, parent.y);
            ctx.lineTo(node.x, node.y);
            ctx.stroke();
          }
        });
      });

      // 绘制节点
      nodes.forEach(node => {
        const fitness = node.structure.metadata.fitness;
        const color = fitness > 0.7 ? '#10b981' : fitness > 0.4 ? '#f59e0b' : '#8b5cf6';

        // 光晕
        const gradient = ctx.createRadialGradient(
          node.x, node.y, 0,
          node.x, node.y, 20
        );
        gradient.addColorStop(0, color + '44');
        gradient.addColorStop(1, 'transparent');
        ctx.fillStyle = gradient;
        ctx.fillRect(node.x - 20, node.y - 20, 40, 40);

        // 节点
        ctx.beginPath();
        ctx.arc(node.x, node.y, 8, 0, Math.PI * 2);
        ctx.fillStyle = color;
        ctx.fill();

        // 名称
        ctx.fillStyle = '#e2e8f0';
        ctx.font = '10px monospace';
        ctx.textAlign = 'center';
        ctx.fillText(
          node.structure.name.slice(0, 12),
          node.x,
          node.y + 20
        );
      });

      // 中心
      ctx.beginPath();
      ctx.arc(width / 2, height / 2, 4, 0, Math.PI * 2);
      ctx.fillStyle = '#8b5cf6';
      ctx.fill();

      animationId = requestAnimationFrame(animate);
    };

    animate();

    return () => cancelAnimationFrame(animationId);
  }, [nodes, width, height]);

  return (
    <canvas
      ref={canvasRef}
      width={width}
      height={height}
      style={{
        borderRadius: '12px',
        border: '1px solid #334155'
      }}
    />
  );
};
