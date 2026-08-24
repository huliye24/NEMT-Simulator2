/**
 * Copyright 2026 NEMT Lab
 *
 * 生成系统展示面板
 * 展示约束引擎、数据生成器、组件生成器、工作流引擎
 */

import React, { useState, useEffect } from 'react';
import { Shield, Database, Layout, Workflow, CheckCircle, AlertCircle, Info, Play, Pause, RotateCcw } from 'lucide-react';
import { constraintEngine, ConstraintViolation, createPlatformConstraints, Constraint } from '../generation/constraints';
import { ConstraintContext, Operation } from '../generation/constraints';
import { useConstraints } from '../generation/constraints';

const modules = [
  {
    id: 'constraints',
    name: '约束引擎',
    description: '软件生成的宪法 - 定义可能性的边界',
    icon: Shield,
    color: '#8b5cf6',
  },
  {
    id: 'data',
    name: '数据生成器',
    description: '基于约束的测试数据自动生成',
    icon: Database,
    color: '#3b82f6',
  },
  {
    id: 'component',
    name: '组件生成器',
    description: 'UI 组件的声明式生成',
    icon: Layout,
    color: '#10b981',
  },
  {
    id: 'workflow',
    name: '工作流引擎',
    description: '复杂业务流程的编排执行',
    icon: Workflow,
    color: '#f59e0b',
  },
];

export function GenerationPanel() {
  const [activeModule, setActiveModule] = useState('constraints');
  const [violations, setViolations] = useState<ConstraintViolation[]>([]);
  const [isValid, setIsValid] = useState(true);
  const [isRunning, setIsRunning] = useState(false);
  const [history, setHistory] = useState<ConstraintViolation[]>([]);

  // 模拟验证
  const runValidation = () => {
    const context: ConstraintContext = {
      state: { strategies: [] },
      entities: new Map([['strategies', [
        { name: '趋势跟随', status: 'running' },
        { name: '均值回归', status: 'testing' },
      ]]]),
      history: [],
      variables: {}
    };

    const result = constraintEngine.validate(context);
    setViolations(result.violations);
    setIsValid(result.valid);
    setHistory([...history, ...result.violations].slice(-50));
  };

  useEffect(() => {
    if (isRunning) {
      const interval = setInterval(runValidation, 3000);
      return () => clearInterval(interval);
    }
  }, [isRunning, history]);

  return (
    <div style={{
      height: '100%',
      display: 'flex',
      flexDirection: 'column',
      background: '#020617',
    }}>
      {/* 模块选择器 */}
      <div style={{
        padding: '16px 24px',
        borderBottom: '1px solid #1e293b',
        display: 'flex',
        gap: '12px',
      }}>
        {modules.map((module) => {
          const Icon = module.icon;
          const isActive = activeModule === module.id;

          return (
            <button
              key={module.id}
              onClick={() => setActiveModule(module.id)}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '10px',
                padding: '12px 20px',
                background: isActive ? `${module.color}20` : 'transparent',
                border: `1px solid ${isActive ? module.color : '#334155'}`,
                borderRadius: '10px',
                cursor: 'pointer',
                color: isActive ? module.color : '#94a3b8',
                transition: 'all 0.2s',
              }}
              onMouseEnter={(e) => {
                if (!isActive) {
                  e.currentTarget.style.borderColor = '#64748b';
                  e.currentTarget.style.color = '#e2e8f0';
                }
              }}
              onMouseLeave={(e) => {
                if (!isActive) {
                  e.currentTarget.style.borderColor = '#334155';
                  e.currentTarget.style.color = '#94a3b8';
                }
              }}
            >
              <Icon size={18} />
              <span style={{ fontWeight: isActive ? '600' : '400' }}>{module.name}</span>
            </button>
          );
        })}

        {/* 控制按钮 */}
        <div style={{ marginLeft: 'auto', display: 'flex', gap: '8px' }}>
          <button
            onClick={() => setIsRunning(!isRunning)}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              padding: '10px 16px',
              background: isRunning ? '#ef444420' : '#10b98120',
              border: `1px solid ${isRunning ? '#ef4444' : '#10b981'}`,
              borderRadius: '8px',
              cursor: 'pointer',
              color: isRunning ? '#ef4444' : '#10b981',
              fontSize: '13px',
            }}
          >
            {isRunning ? <Pause size={14} /> : <Play size={14} />}
            {isRunning ? '停止' : '自动验证'}
          </button>
          <button
            onClick={runValidation}
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
            <RotateCcw size={14} />
            验证
          </button>
        </div>
      </div>

      {/* 内容区域 */}
      <div style={{
        flex: 1,
        display: 'grid',
        gridTemplateColumns: '1fr 400px',
        gap: '24px',
        padding: '24px',
        overflow: 'hidden',
      }}>
        {/* 左侧 - 模块详情 */}
        <div style={{
          background: '#0f172a',
          borderRadius: '12px',
          border: '1px solid #1e293b',
          padding: '24px',
          overflow: 'auto',
        }}>
          <h2 style={{
            fontSize: '18px',
            fontWeight: '600',
            color: '#e2e8f0',
            marginBottom: '8px',
          }}>
            {modules.find(m => m.id === activeModule)?.name}
          </h2>
          <p style={{
            fontSize: '14px',
            color: '#94a3b8',
            marginBottom: '24px',
          }}>
            {modules.find(m => m.id === activeModule)?.description}
          </p>

          {/* 约束引擎详情 */}
          {activeModule === 'constraints' && <ConstraintsDetail />}
          {activeModule === 'data' && <DataGeneratorDetail />}
          {activeModule === 'component' && <ComponentGeneratorDetail />}
          {activeModule === 'workflow' && <WorkflowDetail />}
        </div>

        {/* 右侧 - 状态面板 */}
        <div style={{
          display: 'flex',
          flexDirection: 'column',
          gap: '16px',
          overflow: 'auto',
        }}>
          {/* 状态摘要 */}
          <div style={{
            background: '#0f172a',
            borderRadius: '12px',
            border: '1px solid #1e293b',
            padding: '20px',
          }}>
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '12px',
              marginBottom: '16px',
            }}>
              {isValid ? (
                <CheckCircle size={24} style={{ color: '#10b981' }} />
              ) : (
                <AlertCircle size={24} style={{ color: '#ef4444' }} />
              )}
              <span style={{
                fontSize: '16px',
                fontWeight: '600',
                color: isValid ? '#10b981' : '#ef4444',
              }}>
                {isValid ? '验证通过' : '发现违规'}
              </span>
            </div>

            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(3, 1fr)',
              gap: '12px',
            }}>
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: '20px', fontWeight: 'bold', color: '#ef4444' }}>
                  {violations.filter(v => v.severity === 'error').length}
                </div>
                <div style={{ fontSize: '11px', color: '#64748b' }}>错误</div>
              </div>
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: '20px', fontWeight: 'bold', color: '#f59e0b' }}>
                  {violations.filter(v => v.severity === 'warning').length}
                </div>
                <div style={{ fontSize: '11px', color: '#64748b' }}>警告</div>
              </div>
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: '20px', fontWeight: 'bold', color: '#3b82f6' }}>
                  {violations.filter(v => v.severity === 'info').length}
                </div>
                <div style={{ fontSize: '11px', color: '#64748b' }}>信息</div>
              </div>
            </div>
          </div>

          {/* 违规列表 */}
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
            }}>
              违规记录 ({violations.length})
            </h3>

            {violations.length === 0 ? (
              <div style={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
                padding: '40px',
                color: '#475569',
              }}>
                <CheckCircle size={32} style={{ marginBottom: '12px' }} />
                <span>暂无违规</span>
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {violations.slice(0, 10).map((v, i) => (
                  <div
                    key={i}
                    style={{
                      padding: '12px',
                      background: v.severity === 'error' ? '#ef444410' :
                                 v.severity === 'warning' ? '#f59e0b10' : '#3b82f610',
                      borderRadius: '8px',
                      borderLeft: `3px solid ${v.severity === 'error' ? '#ef4444' :
                                                 v.severity === 'warning' ? '#f59e0b' : '#3b82f6'}`,
                    }}
                  >
                    <div style={{ fontSize: '13px', color: '#e2e8f0', marginBottom: '4px' }}>
                      {v.constraintName}
                    </div>
                    <div style={{ fontSize: '12px', color: '#94a3b8' }}>
                      {v.message}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

function ConstraintsDetail() {
  const constraints = constraintEngine.getConstraints();
  const categories = [...new Set(constraints.map(c => c.metadata.category))];

  return (
    <div>
      <h3 style={{ fontSize: '16px', fontWeight: '600', color: '#e2e8f0', marginBottom: '16px' }}>
        已注册约束 ({constraints.length})
      </h3>

      {categories.map(category => {
        const categoryConstraints = constraints.filter(c => c.metadata.category === category);
        return (
          <div key={category} style={{ marginBottom: '20px' }}>
            <div style={{
              fontSize: '12px',
              color: '#8b5cf6',
              fontWeight: '600',
              marginBottom: '8px',
              textTransform: 'uppercase',
              letterSpacing: '1px',
            }}>
              {category}
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
              {categoryConstraints.map(c => (
                <div
                  key={c.id}
                  style={{
                    padding: '10px 14px',
                    background: '#1e293b',
                    borderRadius: '6px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                  }}
                >
                  <span style={{ fontSize: '13px', color: '#e2e8f0' }}>{c.name}</span>
                  <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px',
                  }}>
                    <span style={{
                      fontSize: '11px',
                      padding: '2px 8px',
                      borderRadius: '4px',
                      background: c.metadata.enabled ? '#10b98120' : '#475569',
                      color: c.metadata.enabled ? '#10b981' : '#64748b',
                    }}>
                      {c.metadata.enabled ? '启用' : '禁用'}
                    </span>
                    <span style={{
                      fontSize: '11px',
                      padding: '2px 8px',
                      borderRadius: '4px',
                      background: c.severity === 'error' ? '#ef444420' :
                                 c.severity === 'warning' ? '#f59e0b20' : '#3b82f620',
                      color: c.severity === 'error' ? '#ef4444' :
                             c.severity === 'warning' ? '#f59e0b' : '#3b82f6',
                    }}>
                      {c.severity}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        );
      })}
    </div>
  );
}

function DataGeneratorDetail() {
  const fields = [
    { name: 'string', desc: '随机字符串', example: '"xK9#mN2"' },
    { name: 'number', desc: '随机数字', example: '42' },
    { name: 'boolean', desc: '随机布尔值', example: 'true' },
    { name: 'date', desc: '随机日期', example: '2026-05-04' },
    { name: 'email', desc: '随机邮箱', example: 'user@example.com' },
    { name: 'uuid', desc: 'UUID', example: '550e8400-e29b...' },
  ];

  return (
    <div>
      <h3 style={{ fontSize: '16px', fontWeight: '600', color: '#e2e8f0', marginBottom: '16px' }}>
        支持的数据类型
      </h3>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '12px' }}>
        {fields.map(field => (
          <div
            key={field.name}
            style={{
              padding: '14px',
              background: '#1e293b',
              borderRadius: '8px',
            }}
          >
            <div style={{ fontSize: '13px', fontWeight: '600', color: '#3b82f6', marginBottom: '4px' }}>
              {field.name}
            </div>
            <div style={{ fontSize: '12px', color: '#94a3b8', marginBottom: '6px' }}>
              {field.desc}
            </div>
            <code style={{ fontSize: '11px', color: '#10b981' }}>
              {field.example}
            </code>
          </div>
        ))}
      </div>
    </div>
  );
}

function ComponentGeneratorDetail() {
  const components = [
    { type: 'Button', props: 'size, variant, disabled', icon: '⬜' },
    { type: 'Input', props: 'type, placeholder, value', icon: '📝' },
    { type: 'Card', props: 'title, children, footer', icon: '🗃️' },
    { type: 'Table', props: 'columns, data, onSort', icon: '📊' },
    { type: 'Modal', props: 'open, onClose, children', icon: '📦' },
    { type: 'Chart', props: 'type, data, options', icon: '📈' },
  ];

  return (
    <div>
      <h3 style={{ fontSize: '16px', fontWeight: '600', color: '#e2e8f0', marginBottom: '16px' }}>
        可生成组件
      </h3>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
        {components.map(comp => (
          <div
            key={comp.type}
            style={{
              padding: '14px',
              background: '#1e293b',
              borderRadius: '8px',
              display: 'flex',
              alignItems: 'center',
              gap: '14px',
            }}
          >
            <span style={{ fontSize: '20px' }}>{comp.icon}</span>
            <div>
              <div style={{ fontSize: '13px', fontWeight: '600', color: '#10b981' }}>
                {comp.type}
              </div>
              <div style={{ fontSize: '11px', color: '#64748b' }}>
                {comp.props}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function WorkflowDetail() {
  const steps = [
    { id: 1, name: '输入验证', status: 'done' },
    { id: 2, name: '数据预处理', status: 'done' },
    { id: 3, name: '核心处理', status: 'running' },
    { id: 4, name: '结果校验', status: 'pending' },
    { id: 5, name: '输出格式化', status: 'pending' },
  ];

  return (
    <div>
      <h3 style={{ fontSize: '16px', fontWeight: '600', color: '#e2e8f0', marginBottom: '16px' }}>
        工作流示例
      </h3>
      <div style={{
        padding: '20px',
        background: '#1e293b',
        borderRadius: '10px',
      }}>
        {steps.map((step, i) => (
          <div key={step.id} style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
            <div style={{
              width: '28px',
              height: '28px',
              borderRadius: '50%',
              background: step.status === 'done' ? '#10b981' :
                         step.status === 'running' ? '#8b5cf6' : '#334155',
              color: '#fff',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: '12px',
              fontWeight: 'bold',
            }}>
              {step.status === 'done' ? '✓' : step.id}
            </div>
            <span style={{
              fontSize: '14px',
              color: step.status === 'pending' ? '#64748b' : '#e2e8f0',
              fontWeight: step.status === 'running' ? '600' : '400',
            }}>
              {step.name}
            </span>
            {i < steps.length - 1 && (
              <div style={{
                width: '2px',
                height: '24px',
                background: step.status === 'done' ? '#10b981' : '#334155',
                marginLeft: '13px',
              }} />
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
