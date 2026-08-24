/**
 * Copyright 2026 NEMT Lab
 *
 * 生成系统演示面板
 */

import React, { useState } from 'react';
import { ConstraintEngine, constraintEngine } from '../generation/constraints';
import { DataGenerator, StrategySchema, validateData } from '../generation/dataGenerator';
import { ComponentGenerator, componentGenerator } from '../generation/componentGenerator';
import { WorkflowEngine, workflowEngine } from '../generation/workflowEngine';
import {
  CandlestickChart,
  LineChart,
  GaugeChart,
  Sparkline,
  generateMockCandleData,
  generateMockLineData
} from './charts';
import { ConnectionIndicator, SyncProvider, useSync } from './sync';

// ============================================
// 演示面板
// ============================================

export const GenerationDemoPanel: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'constraints' | 'data' | 'components' | 'workflows' | 'charts'>('constraints');

  return (
    <div style={{
      marginTop: '32px',
      background: '#0f172a',
      borderRadius: '12px',
      border: '1px solid #334155',
      overflow: 'hidden'
    }}>
      {/* 头部 */}
      <div style={{
        padding: '16px 20px',
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
          生成系统演示
        </div>
        <span style={{
          fontSize: '11px',
          color: '#64748b',
          background: '#1e293b',
          padding: '2px 8px',
          borderRadius: '4px'
        }}>
          约束驱动 · 自动生成 · 自我演化
        </span>
      </div>

      {/* 标签 */}
      <div style={{
        display: 'flex',
        borderBottom: '1px solid #334155',
        overflowX: 'auto'
      }}>
        {[
          { id: 'constraints', label: '约束引擎', icon: '⚖️' },
          { id: 'data', label: '数据生成', icon: '📊' },
          { id: 'components', label: '组件生成', icon: '🧩' },
          { id: 'workflows', label: '工作流', icon: '🔄' },
          { id: 'charts', label: '可视化', icon: '📈' }
        ].map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id as any)}
            style={{
              padding: '12px 20px',
              border: 'none',
              background: activeTab === tab.id ? '#1e293b' : 'transparent',
              color: activeTab === tab.id ? '#a78bfa' : '#64748b',
              fontSize: '13px',
              cursor: 'pointer',
              borderBottom: activeTab === tab.id ? '2px solid #8b5cf6' : '2px solid transparent',
              whiteSpace: 'nowrap'
            }}
          >
            <span style={{ marginRight: '6px' }}>{tab.icon}</span>
            {tab.label}
          </button>
        ))}
      </div>

      {/* 内容 */}
      <div style={{ padding: '20px' }}>
        {activeTab === 'constraints' && <ConstraintsDemo />}
        {activeTab === 'data' && <DataGenerationDemo />}
        {activeTab === 'components' && <ComponentDemo />}
        {activeTab === 'workflows' && <WorkflowDemo />}
        {activeTab === 'charts' && <ChartsDemo />}
      </div>
    </div>
  );
};

// ============================================
// 约束引擎演示
// ============================================

const ConstraintsDemo: React.FC = () => {
  const constraints = constraintEngine.getConstraints();

  return (
    <div>
      <div style={{ marginBottom: '16px' }}>
        <h4 style={{ margin: '0 0 8px', color: '#e2e8f0' }}>平台约束</h4>
        <p style={{ margin: 0, fontSize: '12px', color: '#64748b' }}>
          定义了系统的业务规则和数据约束，确保生成的代码符合规范
        </p>
      </div>

      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))',
        gap: '12px'
      }}>
        {constraints.slice(0, 6).map(constraint => (
          <div
            key={constraint.id}
            style={{
              padding: '12px',
              background: '#1e293b',
              borderRadius: '8px',
              border: `1px solid ${
                constraint.severity === 'error' ? '#ef444433' :
                constraint.severity === 'warning' ? '#f59e0b33' : '#3b82f633'
              }`
            }}
          >
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              marginBottom: '8px'
            }}>
              <span style={{
                fontSize: '10px',
                padding: '2px 6px',
                borderRadius: '4px',
                background: constraint.type === 'invariant' ? '#10b98120' :
                           constraint.type === 'precondition' ? '#3b82f620' :
                           constraint.type === 'postcondition' ? '#8b5cf620' :
                           '#f59e0b20',
                color: constraint.type === 'invariant' ? '#10b981' :
                       constraint.type === 'precondition' ? '#3b82f6' :
                       constraint.type === 'postcondition' ? '#8b5cf6' : '#f59e0b'
              }}>
                {constraint.type}
              </span>
              <span style={{
                fontSize: '10px',
                padding: '2px 6px',
                borderRadius: '4px',
                background: constraint.severity === 'error' ? '#ef444420' :
                           constraint.severity === 'warning' ? '#f59e0b20' : '#64748b20',
                color: constraint.severity === 'error' ? '#ef4444' :
                       constraint.severity === 'warning' ? '#f59e0b' : '#64748b'
              }}>
                {constraint.severity}
              </span>
            </div>
            <div style={{ fontSize: '13px', color: '#e2e8f0', fontWeight: 500 }}>
              {constraint.name}
            </div>
            <div style={{ fontSize: '11px', color: '#64748b', marginTop: '4px' }}>
              {constraint.description}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

// ============================================
// 数据生成演示
// ============================================

const DataGenerationDemo: React.FC = () => {
  const generator = new DataGenerator(42);
  const [generated, setGenerated] = useState<any>(null);

  const generate = () => {
    const data = generator.generate({
      name: 'strategy',
      type: 'object',
      properties: StrategySchema.fields
    });
    setGenerated(data);
  };

  return (
    <div>
      <div style={{ marginBottom: '16px' }}>
        <h4 style={{ margin: '0 0 8px', color: '#e2e8f0' }}>数据生成器</h4>
        <p style={{ margin: 0, fontSize: '12px', color: '#64748b' }}>
          基于约束生成符合 Schema 的测试数据
        </p>
      </div>

      <div style={{ display: 'flex', gap: '12px', marginBottom: '16px' }}>
        <button
          onClick={generate}
          style={{
            padding: '10px 20px',
            borderRadius: '8px',
            border: 'none',
            background: 'linear-gradient(135deg, #8b5cf6 0%, #6366f1 100%)',
            color: '#fff',
            cursor: 'pointer',
            fontSize: '13px'
          }}
        >
          生成策略数据
        </button>

        <button
          onClick={() => setGenerated(null)}
          style={{
            padding: '10px 20px',
            borderRadius: '8px',
            border: '1px solid #475569',
            background: 'transparent',
            color: '#94a3b8',
            cursor: 'pointer',
            fontSize: '13px'
          }}
        >
          清空
        </button>
      </div>

      {generated && (
        <div style={{
          background: '#1e293b',
          borderRadius: '8px',
          padding: '16px',
          fontFamily: 'monospace',
          fontSize: '12px'
        }}>
          <pre style={{
            margin: 0,
            color: '#a78bfa',
            whiteSpace: 'pre-wrap',
            wordBreak: 'break-all'
          }}>
            {JSON.stringify(generated, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
};

// ============================================
// 组件生成演示
// ============================================

const ComponentDemo: React.FC = () => {
  const [formData, setFormData] = useState<Record<string, any>>({});

  const fields = [
    { name: 'name', label: '策略名称', type: 'input' as const, required: true },
    { name: 'author', label: '作者', type: 'input' as const },
    { name: 'status', label: '状态', type: 'select' as const, options: [
      { label: '草稿', value: 'draft' },
      { label: '运行中', value: 'running' },
      { label: '已暂停', value: 'paused' }
    ]},
    { name: 'riskLevel', label: '风险等级', type: 'slider' as const, min: 1, max: 10 },
    { name: 'enabled', label: '启用', type: 'switch' as const }
  ];

  return (
    <div>
      <div style={{ marginBottom: '16px' }}>
        <h4 style={{ margin: '0 0 8px', color: '#e2e8f0' }}>表单生成器</h4>
        <p style={{ margin: 0, fontSize: '12px', color: '#64748b' }}>
          从配置自动生成表单组件
        </p>
      </div>

      <div style={{
        background: '#1e293b',
        borderRadius: '8px',
        padding: '20px',
        maxWidth: '500px'
      }}>
        {fields.map(field => (
          <div key={field.name} style={{ marginBottom: '16px' }}>
            <label style={{
              display: 'block',
              marginBottom: '6px',
              fontSize: '13px',
              color: '#94a3b8'
            }}>
              {field.label}
              {field.required && <span style={{ color: '#ef4444' }}> *</span>}
            </label>

            {field.type === 'input' && (
              <input
                type="text"
                value={formData[field.name] || ''}
                onChange={e => setFormData(prev => ({ ...prev, [field.name]: e.target.value }))}
                style={{
                  width: '100%',
                  padding: '10px 12px',
                  borderRadius: '8px',
                  border: '1px solid #334155',
                  background: '#0f172a',
                  color: '#e2e8f0',
                  fontSize: '14px'
                }}
              />
            )}

            {field.type === 'select' && (
              <select
                value={formData[field.name] || ''}
                onChange={e => setFormData(prev => ({ ...prev, [field.name]: e.target.value }))}
                style={{
                  width: '100%',
                  padding: '10px 12px',
                  borderRadius: '8px',
                  border: '1px solid #334155',
                  background: '#0f172a',
                  color: '#e2e8f0',
                  fontSize: '14px'
                }}
              >
                <option value="">请选择</option>
                {field.options?.map(opt => (
                  <option key={opt.value} value={opt.value}>{opt.label}</option>
                ))}
              </select>
            )}

            {field.type === 'slider' && (
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                <input
                  type="range"
                  min={field.min}
                  max={field.max}
                  value={formData[field.name] || field.min}
                  onChange={e => setFormData(prev => ({ ...prev, [field.name]: parseInt(e.target.value) }))}
                  style={{ flex: 1 }}
                />
                <span style={{ color: '#e2e8f0', fontFamily: 'monospace', minWidth: '30px' }}>
                  {formData[field.name] || field.min}
                </span>
              </div>
            )}

            {field.type === 'switch' && (
              <div
                onClick={() => setFormData(prev => ({ ...prev, [field.name]: !prev[field.name] }))}
                style={{
                  width: '44px',
                  height: '24px',
                  borderRadius: '12px',
                  background: formData[field.name] ? '#10b981' : '#334155',
                  position: 'relative',
                  cursor: 'pointer',
                  transition: 'background 0.2s'
                }}
              >
                <div style={{
                  width: '20px',
                  height: '20px',
                  borderRadius: '50%',
                  background: '#fff',
                  position: 'absolute',
                  top: '2px',
                  left: formData[field.name] ? '22px' : '2px',
                  transition: 'left 0.2s'
                }} />
              </div>
            )}
          </div>
        ))}

        <div style={{ marginTop: '20px', padding: '12px', background: '#0f172a', borderRadius: '8px' }}>
          <div style={{ fontSize: '11px', color: '#64748b', marginBottom: '4px' }}>表单数据</div>
          <pre style={{ margin: 0, fontSize: '11px', color: '#a78bfa' }}>
            {JSON.stringify(formData, null, 2)}
          </pre>
        </div>
      </div>
    </div>
  );
};

// ============================================
// 工作流演示
// ============================================

const WorkflowDemo: React.FC = () => {
  const workflows = [
    workflowEngine.getWorkflow('wf_simple')?.name || '简单流程',
    workflowEngine.getWorkflow('wf_approval')?.name || '审批流程',
    workflowEngine.getWorkflow('wf_pipeline')?.name || '数据管道',
    workflowEngine.getWorkflow('wf_state-machine')?.name || '状态机'
  ];

  return (
    <div>
      <div style={{ marginBottom: '16px' }}>
        <h4 style={{ margin: '0 0 8px', color: '#e2e8f0' }}>工作流引擎</h4>
        <p style={{ margin: 0, fontSize: '12px', color: '#64748b' }}>
          约束驱动的业务流程编排
        </p>
      </div>

      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))',
        gap: '12px'
      }}>
        {workflows.map((name, i) => (
          <div
            key={i}
            style={{
              padding: '16px',
              background: '#1e293b',
              borderRadius: '8px',
              border: '1px solid #334155'
            }}
          >
            <div style={{
              width: '40px',
              height: '40px',
              borderRadius: '8px',
              background: '#8b5cf620',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              marginBottom: '12px',
              fontSize: '20px'
            }}>
              {['▶', '✓', '⟳', '⬡'][i]}
            </div>
            <div style={{ fontSize: '14px', color: '#e2e8f0', fontWeight: 500 }}>
              {name}
            </div>
            <div style={{ fontSize: '11px', color: '#64748b', marginTop: '4px' }}>
              {['start → process → end', 'submit → approve → process/notify', 'data → clean → analyze → report', 'draft → review → published'][i]}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

// ============================================
// 图表演示
// ============================================

const ChartsDemo: React.FC = () => {
  const [candleData] = useState(() => generateMockCandleData(100));
  const [lineData] = useState(() => generateMockLineData(50));

  return (
    <div>
      <div style={{ marginBottom: '16px' }}>
        <h4 style={{ margin: '0 0 8px', color: '#e2e8f0' }}>Canvas 图表</h4>
        <p style={{ margin: 0, fontSize: '12px', color: '#64748b' }}>
          高性能 Canvas 渲染，支持缩放和交互
        </p>
      </div>

      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))',
        gap: '20px'
      }}>
        {/* K线图 */}
        <div style={{
          background: '#1e293b',
          borderRadius: '12px',
          padding: '16px'
        }}>
          <div style={{ fontSize: '13px', color: '#94a3b8', marginBottom: '12px' }}>
            K线图表
          </div>
          <div style={{ height: '250px' }}>
            <CandlestickChart data={candleData} />
          </div>
        </div>

        {/* 仪表盘 */}
        <div style={{
          background: '#1e293b',
          borderRadius: '12px',
          padding: '16px'
        }}>
          <div style={{ fontSize: '13px', color: '#94a3b8', marginBottom: '12px' }}>
            性能指标
          </div>
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(3, 1fr)',
            gap: '16px'
          }}>
            <div style={{ textAlign: 'center' }}>
              <GaugeChart value={72} label="胜率" unit="%" size={100} />
            </div>
            <div style={{ textAlign: 'center' }}>
              <GaugeChart value={2.34} label="夏普比率" unit="" size={100} />
            </div>
            <div style={{ textAlign: 'center' }}>
              <GaugeChart value={85} label="利用率" unit="%" size={100} />
            </div>
          </div>
        </div>

        {/* 折线图 */}
        <div style={{
          background: '#1e293b',
          borderRadius: '12px',
          padding: '16px'
        }}>
          <div style={{ fontSize: '13px', color: '#94a3b8', marginBottom: '12px' }}>
            收益率曲线
          </div>
          <div style={{ height: '150px' }}>
            <LineChart data={lineData} />
          </div>
        </div>

        {/* 迷你图 */}
        <div style={{
          background: '#1e293b',
          borderRadius: '12px',
          padding: '16px'
        }}>
          <div style={{ fontSize: '13px', color: '#94a3b8', marginBottom: '12px' }}>
            实时数据
          </div>
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(4, 1fr)',
            gap: '12px',
            alignItems: 'end'
          }}>
            {Array.from({ length: 4 }).map((_, i) => (
              <div key={i} style={{ textAlign: 'center' }}>
                <Sparkline
                  data={Array.from({ length: 20 }).map(() => Math.random() * 100)}
                  color={['#10b981', '#8b5cf6', '#f59e0b', '#3b82f6'][i]}
                />
                <div style={{ fontSize: '10px', color: '#64748b', marginTop: '4px' }}>
                  {['BTC', 'ETH', 'SOL', 'DOGE'][i]}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

// ============================================
// 同步状态演示
// ============================================

const SyncDemo: React.FC = () => {
  return (
    <SyncProvider>
      <SyncDemoContent />
    </SyncProvider>
  );
};

const SyncDemoContent: React.FC = () => {
  const [state] = useState('disconnected');

  return (
    <div style={{
      marginTop: '16px',
      display: 'flex',
      alignItems: 'center',
      gap: '12px'
    }}>
      <ConnectionIndicator state={state as any} />
      <span style={{ fontSize: '11px', color: '#64748b' }}>
        实时同步已配置 (模拟)
      </span>
    </div>
  );
};

export { SyncDemo };
