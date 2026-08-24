/**
 * Copyright 2026 NEMT Lab
 *
 * Create Strategy Dialog
 * AI-powered strategy creation with DeepSeek
 */

import React, { useState, useEffect } from 'react';
import { X, Sparkles, Settings, Loader2, AlertCircle, CheckCircle, ArrowRight, RotateCcw, Zap } from 'lucide-react';
import {
  generateStrategyFromDescription,
  generateMultipleStrategiesFromDescription,
  type GeneratedStrategy,
  type StrategyGenerationRequest,
} from '../../ai/strategy/strategyGenerator';
import { useStrategyStore } from '../../stores';
import { eventBus, EventType } from '../../events';

interface CreateStrategyDialogProps {
  isOpen: boolean;
  onClose: () => void;
}

// -----------------------------------------
// 策略类型选项
// -----------------------------------------

const STRATEGY_TYPES = [
  { value: 'any', label: '任意类型', desc: 'AI 自动选择最佳类型' },
  { value: 'trend_following', label: '趋势跟踪', desc: '顺势交易，追涨杀跌' },
  { value: 'mean_reversion', label: '均值回归', desc: '高卖低买，回归均值' },
  { value: 'breakout', label: '突破策略', desc: '突破关键位置入场' },
  { value: 'arbitrage', label: '套利策略', desc: '捕捉价差机会' },
  { value: 'ai_driven', label: 'AI 驱动', desc: 'AI 分析驱动的策略' },
] as const;

const RISK_LEVELS = [
  { value: 'low', label: '低风险', color: '#10b981', desc: '严格止损，小仓位' },
  { value: 'medium', label: '中等风险', color: '#f59e0b', desc: '平衡收益与风险' },
  { value: 'high', label: '高风险', color: '#ef4444', desc: '宽松止损，大仓位' },
] as const;

const TIMEFRAMES = [
  { value: '1m', label: '1分钟' },
  { value: '5m', label: '5分钟' },
  { value: '15m', label: '15分钟' },
  { value: '1h', label: '1小时' },
  { value: '4h', label: '4小时' },
  { value: '1d', label: '日线' },
];

// -----------------------------------------
// 主组件
// -----------------------------------------

export function CreateStrategyDialog({ isOpen, onClose }: CreateStrategyDialogProps) {
  const [mode, setMode] = useState<'select' | 'manual' | 'ai'>('select');
  const [isGenerating, setIsGenerating] = useState(false);
  const [generatedStrategies, setGeneratedStrategies] = useState<GeneratedStrategy[]>([]);
  const [selectedIndex, setSelectedIndex] = useState(0);
  const [error, setError] = useState<string | null>(null);

  // Manual form state
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    author: 'User',
    version: '1.0.0',
    strategyType: 'any',
    riskLevel: 'medium' as 'low' | 'medium' | 'high',
    timeframe: '1h',
    tags: [] as string[],
    stopLoss: 0.05,
    takeProfit: 0.10,
  });

  // AI form state
  const [aiFormData, setAiFormData] = useState({
    description: '',
    symbol: 'BTCUSDT',
    strategyType: 'any' as StrategyGenerationRequest['strategyType'],
    riskTolerance: 'medium' as 'low' | 'medium' | 'high',
    timeframe: '1h',
    generateCount: 1,
  });

  const addStrategy = useStrategyStore(state => state.addStrategy);

  // Reset state when dialog opens
  useEffect(() => {
    if (isOpen) {
      setMode('select');
      setIsGenerating(false);
      setGeneratedStrategies([]);
      setError(null);
      setSelectedIndex(0);
    }
  }, [isOpen]);

  if (!isOpen) return null;

  // -----------------------------------------
  // 模式选择
  // -----------------------------------------

  const renderModeSelect = () => (
    <div style={{ padding: '8px' }}>
      <h3 style={{
        margin: '0 0 20px',
        fontSize: '18px',
        fontWeight: 'bold',
        color: '#e2e8f0',
        textAlign: 'center'
      }}>
        选择创建方式
      </h3>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
        {/* AI 创建 */}
        <button
          onClick={() => setMode('ai')}
          style={{
            padding: '20px',
            borderRadius: '12px',
            border: '2px solid #8b5cf6',
            background: 'linear-gradient(135deg, #8b5cf620, #6366f120)',
            cursor: 'pointer',
            textAlign: 'left',
            transition: 'all 0.2s'
          }}
          onMouseEnter={e => {
            e.currentTarget.style.background = 'linear-gradient(135deg, #8b5cf630, #6366f130)';
            e.currentTarget.style.transform = 'translateY(-2px)';
          }}
          onMouseLeave={e => {
            e.currentTarget.style.background = 'linear-gradient(135deg, #8b5cf620, #6366f120)';
            e.currentTarget.style.transform = 'translateY(0)';
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '8px' }}>
            <div style={{
              width: '48px',
              height: '48px',
              borderRadius: '12px',
              background: 'linear-gradient(135deg, #8b5cf6, #6366f1)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}>
              <Sparkles size={24} color="#fff" />
            </div>
            <div>
              <div style={{ fontSize: '16px', fontWeight: 'bold', color: '#e2e8f0' }}>
                AI 智能创建
              </div>
              <div style={{ fontSize: '13px', color: '#94a3b8' }}>
                使用 DeepSeek 生成策略
              </div>
            </div>
          </div>
          <p style={{ margin: '0', fontSize: '13px', color: '#94a3b8', lineHeight: 1.5 }}>
            描述你的交易想法，AI 将为你生成完整的策略配置，包括指标参数、入场出场规则和风险管理设置。
          </p>
        </button>

        {/* 手动创建 */}
        <button
          onClick={() => setMode('manual')}
          style={{
            padding: '20px',
            borderRadius: '12px',
            border: '2px solid #334155',
            background: 'transparent',
            cursor: 'pointer',
            textAlign: 'left',
            transition: 'all 0.2s'
          }}
          onMouseEnter={e => {
            e.currentTarget.style.borderColor = '#475569';
            e.currentTarget.style.transform = 'translateY(-2px)';
          }}
          onMouseLeave={e => {
            e.currentTarget.style.borderColor = '#334155';
            e.currentTarget.style.transform = 'translateY(0)';
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '8px' }}>
            <div style={{
              width: '48px',
              height: '48px',
              borderRadius: '12px',
              background: '#334155',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}>
              <Settings size={24} color="#94a3b8" />
            </div>
            <div>
              <div style={{ fontSize: '16px', fontWeight: 'bold', color: '#e2e8f0' }}>
                手动创建
              </div>
              <div style={{ fontSize: '13px', color: '#94a3b8' }}>
                自定义所有参数
              </div>
            </div>
          </div>
          <p style={{ margin: '0', fontSize: '13px', color: '#94a3b8', lineHeight: 1.5 }}>
            手动配置策略的每一个参数，适合有明确策略需求的资深用户。
          </p>
        </button>
      </div>
    </div>
  );

  // -----------------------------------------
  // AI 创建模式
  // -----------------------------------------

  const handleAIGenerate = async () => {
    if (!aiFormData.description.trim()) {
      setError('请输入策略描述');
      return;
    }

    setIsGenerating(true);
    setError(null);

    try {
      let strategies: GeneratedStrategy[];

      if (aiFormData.generateCount > 1) {
        strategies = await generateMultipleStrategiesFromDescription(
          aiFormData.description,
          aiFormData.generateCount,
          {
            symbol: aiFormData.symbol,
            strategyType: aiFormData.strategyType,
            riskTolerance: aiFormData.riskTolerance,
            preferredTimeframe: aiFormData.timeframe,
          }
        );
      } else {
        const strategy = await generateStrategyFromDescription(aiFormData.description, {
          symbol: aiFormData.symbol,
          strategyType: aiFormData.strategyType,
          riskTolerance: aiFormData.riskTolerance,
          preferredTimeframe: aiFormData.timeframe,
        });
        strategies = [strategy];
      }

      setGeneratedStrategies(strategies);
      setSelectedIndex(0);
    } catch (err) {
      setError(err instanceof Error ? err.message : '生成失败，请重试');
    } finally {
      setIsGenerating(false);
    }
  };

  const handleAICreate = () => {
    const strategy = generatedStrategies[selectedIndex];
    if (!strategy) return;

    const newStrategy = addStrategy({
      name: strategy.name,
      author: strategy.author,
      description: strategy.description,
      version: strategy.version,
      status: 'draft',
      metrics: { totalTrades: 0, winRate: 0, totalPnL: 0, sharpeRatio: 0 },
      tags: strategy.tags,
    });

    eventBus.emit(EventType.STRATEGY_CREATED, {
      strategyId: newStrategy.id,
      strategyName: newStrategy.name
    });

    onClose();
  };

  const renderAIMode = () => (
    <div style={{ padding: '8px' }}>
      {/* 返回按钮 */}
      <button
        onClick={() => { setMode('select'); setGeneratedStrategies([]); }}
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          padding: '8px 12px',
          borderRadius: '8px',
          border: 'none',
          background: '#334155',
          color: '#94a3b8',
          cursor: 'pointer',
          marginBottom: '16px',
          fontSize: '13px'
        }}
      >
        <RotateCcw size={14} />
        返回选择
      </button>

      <h3 style={{
        margin: '0 0 20px',
        fontSize: '18px',
        fontWeight: 'bold',
        color: '#e2e8f0'
      }}>
        <Sparkles size={20} style={{ color: '#8b5cf6', marginRight: '8px' }} />
        AI 智能创建策略
      </h3>

      {/* 策略描述输入 */}
      <div style={{ marginBottom: '16px' }}>
        <label style={{ display: 'block', marginBottom: '8px', color: '#94a3b8', fontSize: '13px' }}>
          描述你的策略想法 *
        </label>
        <textarea
          value={aiFormData.description}
          onChange={e => setAiFormData(f => ({ ...f, description: e.target.value }))}
          placeholder="例如：我想创建一个基于RSI超卖入场的趋势跟踪策略，适合高波动市场，止损设在2%..."
          style={{
            width: '100%',
            minHeight: '100px',
            padding: '12px',
            borderRadius: '8px',
            border: '1px solid #334155',
            background: '#0f172a',
            color: '#e2e8f0',
            fontSize: '13px',
            fontFamily: 'inherit',
            resize: 'vertical'
          }}
        />
      </div>

      {/* 配置选项 */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '16px' }}>
        {/* 交易品种 */}
        <div>
          <label style={{ display: 'block', marginBottom: '8px', color: '#94a3b8', fontSize: '13px' }}>
            交易品种
          </label>
          <select
            value={aiFormData.symbol}
            onChange={e => setAiFormData(f => ({ ...f, symbol: e.target.value }))}
            style={{
              width: '100%',
              padding: '10px 12px',
              borderRadius: '8px',
              border: '1px solid #334155',
              background: '#0f172a',
              color: '#e2e8f0',
              fontSize: '13px'
            }}
          >
            <option value="BTCUSDT">BTC/USDT</option>
            <option value="ETHUSDT">ETH/USDT</option>
            <option value="BNBUSDT">BNB/USDT</option>
            <option value="SOLUSDT">SOL/USDT</option>
            <option value="任意">任意品种</option>
          </select>
        </div>

        {/* 时间周期 */}
        <div>
          <label style={{ display: 'block', marginBottom: '8px', color: '#94a3b8', fontSize: '13px' }}>
            时间周期
          </label>
          <select
            value={aiFormData.timeframe}
            onChange={e => setAiFormData(f => ({ ...f, timeframe: e.target.value }))}
            style={{
              width: '100%',
              padding: '10px 12px',
              borderRadius: '8px',
              border: '1px solid #334155',
              background: '#0f172a',
              color: '#e2e8f0',
              fontSize: '13px'
            }}
          >
            {TIMEFRAMES.map(tf => (
              <option key={tf.value} value={tf.value}>{tf.label}</option>
            ))}
          </select>
        </div>

        {/* 策略类型 */}
        <div>
          <label style={{ display: 'block', marginBottom: '8px', color: '#94a3b8', fontSize: '13px' }}>
            策略类型
          </label>
          <select
            value={aiFormData.strategyType}
            onChange={e => setAiFormData(f => ({ ...f, strategyType: e.target.value as any }))}
            style={{
              width: '100%',
              padding: '10px 12px',
              borderRadius: '8px',
              border: '1px solid #334155',
              background: '#0f172a',
              color: '#e2e8f0',
              fontSize: '13px'
            }}
          >
            {STRATEGY_TYPES.map(t => (
              <option key={t.value} value={t.value}>{t.label}</option>
            ))}
          </select>
        </div>

        {/* 风险偏好 */}
        <div>
          <label style={{ display: 'block', marginBottom: '8px', color: '#94a3b8', fontSize: '13px' }}>
            风险偏好
          </label>
          <select
            value={aiFormData.riskTolerance}
            onChange={e => setAiFormData(f => ({ ...f, riskTolerance: e.target.value as any }))}
            style={{
              width: '100%',
              padding: '10px 12px',
              borderRadius: '8px',
              border: '1px solid #334155',
              background: '#0f172a',
              color: '#e2e8f0',
              fontSize: '13px'
            }}
          >
            {RISK_LEVELS.map(r => (
              <option key={r.value} value={r.value}>{r.label}</option>
            ))}
          </select>
        </div>
      </div>

      {/* 生成数量 */}
      <div style={{ marginBottom: '20px' }}>
        <label style={{ display: 'block', marginBottom: '8px', color: '#94a3b8', fontSize: '13px' }}>
          生成数量
        </label>
        <div style={{ display: 'flex', gap: '8px' }}>
          {[1, 2, 3].map(n => (
            <button
              key={n}
              onClick={() => setAiFormData(f => ({ ...f, generateCount: n }))}
              style={{
                flex: 1,
                padding: '10px',
                borderRadius: '8px',
                border: aiFormData.generateCount === n ? '2px solid #8b5cf6' : '1px solid #334155',
                background: aiFormData.generateCount === n ? '#8b5cf620' : 'transparent',
                color: aiFormData.generateCount === n ? '#a78bfa' : '#94a3b8',
                cursor: 'pointer',
                fontSize: '14px',
                fontWeight: 'bold'
              }}
            >
              {n} 个策略
            </button>
          ))}
        </div>
      </div>

      {/* 错误提示 */}
      {error && (
        <div style={{
          padding: '12px',
          borderRadius: '8px',
          background: '#ef444420',
          border: '1px solid #ef4444',
          color: '#f87171',
          fontSize: '13px',
          marginBottom: '16px',
          display: 'flex',
          alignItems: 'center',
          gap: '8px'
        }}>
          <AlertCircle size={16} />
          {error}
        </div>
      )}

      {/* 生成按钮 */}
      <button
        onClick={handleAIGenerate}
        disabled={isGenerating}
        style={{
          width: '100%',
          padding: '14px',
          borderRadius: '8px',
          border: 'none',
          background: isGenerating ? '#475569' : 'linear-gradient(135deg, #8b5cf6, #6366f1)',
          color: '#fff',
          fontSize: '14px',
          fontWeight: 'bold',
          cursor: isGenerating ? 'not-allowed' : 'pointer',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          gap: '8px'
        }}
      >
        {isGenerating ? (
          <>
            <Loader2 size={18} className="animate-spin" style={{ animation: 'spin 1s linear infinite' }} />
            正在生成策略...
          </>
        ) : (
          <>
            <Zap size={18} />
            使用 DeepSeek 生成
          </>
        )}
      </button>

      {/* 生成的策略预览 */}
      {generatedStrategies.length > 0 && (
        <div style={{ marginTop: '24px' }}>
          <h4 style={{ margin: '0 0 12px', fontSize: '14px', color: '#94a3b8' }}>
            生成的策略 ({generatedStrategies.length})
            {generatedStrategies.length > 1 && (
              <span style={{ fontWeight: 'normal' }}> - 点击选择</span>
            )}
          </h4>

          {/* 策略选择器 */}
          {generatedStrategies.length > 1 && (
            <div style={{ display: 'flex', gap: '8px', marginBottom: '12px' }}>
              {generatedStrategies.map((s, i) => (
                <button
                  key={i}
                  onClick={() => setSelectedIndex(i)}
                  style={{
                    flex: 1,
                    padding: '10px',
                    borderRadius: '8px',
                    border: selectedIndex === i ? '2px solid #8b5cf6' : '1px solid #334155',
                    background: selectedIndex === i ? '#8b5cf620' : 'transparent',
                    color: selectedIndex === i ? '#a78bfa' : '#94a3b8',
                    cursor: 'pointer',
                    fontSize: '12px',
                    fontWeight: 'bold'
                  }}
                >
                  #{i + 1}: {s.name.slice(0, 15)}...
                </button>
              ))}
            </div>
          )}

          {/* 策略详情卡片 */}
          <StrategyPreviewCard strategy={generatedStrategies[selectedIndex]} />

          {/* 创建按钮 */}
          <button
            onClick={handleAICreate}
            style={{
              width: '100%',
              marginTop: '16px',
              padding: '14px',
              borderRadius: '8px',
              border: 'none',
              background: 'linear-gradient(135deg, #10b981, #059669)',
              color: '#fff',
              fontSize: '14px',
              fontWeight: 'bold',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '8px'
            }}
          >
            <CheckCircle size={18} />
            创建策略
            <ArrowRight size={16} />
          </button>
        </div>
      )}
    </div>
  );

  // -----------------------------------------
  // 手动创建模式
  // -----------------------------------------

  const handleManualCreate = () => {
    if (!formData.name.trim()) {
      setError('请输入策略名称');
      return;
    }

    const newStrategy = addStrategy({
      name: formData.name,
      author: formData.author,
      description: formData.description,
      version: formData.version,
      status: 'draft',
      metrics: { totalTrades: 0, winRate: 0, totalPnL: 0, sharpeRatio: 0 },
      tags: formData.tags,
    });

    eventBus.emit(EventType.STRATEGY_CREATED, {
      strategyId: newStrategy.id,
      strategyName: newStrategy.name
    });

    onClose();
  };

  const renderManualMode = () => (
    <div style={{ padding: '8px' }}>
      {/* 返回按钮 */}
      <button
        onClick={() => setMode('select')}
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          padding: '8px 12px',
          borderRadius: '8px',
          border: 'none',
          background: '#334155',
          color: '#94a3b8',
          cursor: 'pointer',
          marginBottom: '16px',
          fontSize: '13px'
        }}
      >
        <RotateCcw size={14} />
        返回选择
      </button>

      <h3 style={{
        margin: '0 0 20px',
        fontSize: '18px',
        fontWeight: 'bold',
        color: '#e2e8f0'
      }}>
        <Settings size={20} style={{ color: '#94a3b8', marginRight: '8px' }} />
        手动创建策略
      </h3>

      {/* 基本信息 */}
      <div style={{ marginBottom: '16px' }}>
        <label style={{ display: 'block', marginBottom: '8px', color: '#94a3b8', fontSize: '13px' }}>
          策略名称 *
        </label>
        <input
          type="text"
          value={formData.name}
          onChange={e => setFormData(f => ({ ...f, name: e.target.value }))}
          placeholder="输入策略名称"
          style={{
            width: '100%',
            padding: '10px 12px',
            borderRadius: '8px',
            border: '1px solid #334155',
            background: '#0f172a',
            color: '#e2e8f0',
            fontSize: '13px'
          }}
        />
      </div>

      <div style={{ marginBottom: '16px' }}>
        <label style={{ display: 'block', marginBottom: '8px', color: '#94a3b8', fontSize: '13px' }}>
          描述
        </label>
        <textarea
          value={formData.description}
          onChange={e => setFormData(f => ({ ...f, description: e.target.value }))}
          placeholder="策略描述"
          style={{
            width: '100%',
            minHeight: '80px',
            padding: '10px 12px',
            borderRadius: '8px',
            border: '1px solid #334155',
            background: '#0f172a',
            color: '#e2e8f0',
            fontSize: '13px',
            fontFamily: 'inherit',
            resize: 'vertical'
          }}
        />
      </div>

      {/* 配置选项 */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '16px' }}>
        <div>
          <label style={{ display: 'block', marginBottom: '8px', color: '#94a3b8', fontSize: '13px' }}>
            版本
          </label>
          <input
            type="text"
            value={formData.version}
            onChange={e => setFormData(f => ({ ...f, version: e.target.value }))}
            style={{
              width: '100%',
              padding: '10px 12px',
              borderRadius: '8px',
              border: '1px solid #334155',
              background: '#0f172a',
              color: '#e2e8f0',
              fontSize: '13px'
            }}
          />
        </div>
        <div>
          <label style={{ display: 'block', marginBottom: '8px', color: '#94a3b8', fontSize: '13px' }}>
            时间周期
          </label>
          <select
            value={formData.timeframe}
            onChange={e => setFormData(f => ({ ...f, timeframe: e.target.value }))}
            style={{
              width: '100%',
              padding: '10px 12px',
              borderRadius: '8px',
              border: '1px solid #334155',
              background: '#0f172a',
              color: '#e2e8f0',
              fontSize: '13px'
            }}
          >
            {TIMEFRAMES.map(tf => (
              <option key={tf.value} value={tf.value}>{tf.label}</option>
            ))}
          </select>
        </div>
      </div>

      {/* 风险设置 */}
      <div style={{ marginBottom: '16px' }}>
        <label style={{ display: 'block', marginBottom: '8px', color: '#94a3b8', fontSize: '13px' }}>
          风险等级
        </label>
        <div style={{ display: 'flex', gap: '8px' }}>
          {RISK_LEVELS.map(r => (
            <button
              key={r.value}
              onClick={() => setFormData(f => ({ ...f, riskLevel: r.value }))}
              style={{
                flex: 1,
                padding: '10px',
                borderRadius: '8px',
                border: formData.riskLevel === r.value ? `2px solid ${r.color}` : '1px solid #334155',
                background: formData.riskLevel === r.value ? `${r.color}20` : 'transparent',
                color: formData.riskLevel === r.value ? r.color : '#94a3b8',
                cursor: 'pointer',
                fontSize: '12px'
              }}
            >
              {r.label}
            </button>
          ))}
        </div>
      </div>

      {error && (
        <div style={{
          padding: '12px',
          borderRadius: '8px',
          background: '#ef444420',
          border: '1px solid #ef4444',
          color: '#f87171',
          fontSize: '13px',
          marginBottom: '16px'
        }}>
          <AlertCircle size={16} style={{ marginRight: '8px' }} />
          {error}
        </div>
      )}

      <button
        onClick={handleManualCreate}
        style={{
          width: '100%',
          padding: '14px',
          borderRadius: '8px',
          border: 'none',
          background: 'linear-gradient(135deg, #10b981, #059669)',
          color: '#fff',
          fontSize: '14px',
          fontWeight: 'bold',
          cursor: 'pointer',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          gap: '8px'
        }}
      >
        <CheckCircle size={18} />
        创建策略
      </button>
    </div>
  );

  // -----------------------------------------
  // 渲染
  // -----------------------------------------

  return (
    <>
      {/* Backdrop */}
      <div
        onClick={onClose}
        style={{
          position: 'fixed',
          inset: 0,
          background: 'rgba(0, 0, 0, 0.7)',
          backdropFilter: 'blur(4px)',
          zIndex: 1000
        }}
      />

      {/* Dialog */}
      <div style={{
        position: 'fixed',
        top: '50%',
        left: '50%',
        transform: 'translate(-50%, -50%)',
        width: '90%',
        maxWidth: '560px',
        maxHeight: '90vh',
        overflowY: 'auto',
        background: '#1e293b',
        borderRadius: '16px',
        border: '1px solid #334155',
        boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.5)',
        zIndex: 1001
      }}>
        {/* Header */}
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          padding: '16px 20px',
          borderBottom: '1px solid #334155'
        }}>
          <span style={{ fontSize: '16px', fontWeight: 'bold', color: '#e2e8f0' }}>
            创建新策略
          </span>
          <button
            onClick={onClose}
            style={{
              padding: '8px',
              borderRadius: '8px',
              border: 'none',
              background: 'transparent',
              color: '#94a3b8',
              cursor: 'pointer'
            }}
          >
            <X size={20} />
          </button>
        </div>

        {/* Content */}
        <div style={{ padding: '20px' }}>
          {mode === 'select' && renderModeSelect()}
          {mode === 'ai' && renderAIMode()}
          {mode === 'manual' && renderManualMode()}
        </div>
      </div>

      {/* Animation keyframes */}
      <style>{`
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>
    </>
  );
}

// -----------------------------------------
// 策略预览卡片
// -----------------------------------------

function StrategyPreviewCard({ strategy }: { strategy: GeneratedStrategy }) {
  return (
    <div style={{
      background: '#0f172a',
      borderRadius: '12px',
      padding: '16px',
      border: '1px solid #334155'
    }}>
      {/* 标题 */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '12px' }}>
        <div style={{
          width: '36px',
          height: '36px',
          borderRadius: '8px',
          background: 'linear-gradient(135deg, #8b5cf6, #6366f1)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center'
        }}>
          <Sparkles size={18} color="#fff" />
        </div>
        <div>
          <div style={{ fontSize: '14px', fontWeight: 'bold', color: '#e2e8f0' }}>
            {strategy.name}
          </div>
          <div style={{ fontSize: '12px', color: '#64748b' }}>
            by {strategy.author}
          </div>
        </div>
        <div style={{
          marginLeft: 'auto',
          padding: '4px 8px',
          borderRadius: '4px',
          background: '#8b5cf620',
          color: '#a78bfa',
          fontSize: '11px',
          fontWeight: 'bold'
        }}>
          v{strategy.version}
        </div>
      </div>

      {/* 描述 */}
      <p style={{
        margin: '0 0 12px',
        fontSize: '13px',
        color: '#94a3b8',
        lineHeight: 1.5
      }}>
        {strategy.description}
      </p>

      {/* 标签 */}
      <div style={{ display: 'flex', gap: '6px', marginBottom: '12px', flexWrap: 'wrap' }}>
        {strategy.tags.map(tag => (
          <span key={tag} style={{
            padding: '4px 8px',
            borderRadius: '4px',
            background: '#334155',
            fontSize: '11px',
            color: '#94a3b8'
          }}>
            {tag}
          </span>
        ))}
        <span style={{
          padding: '4px 8px',
          borderRadius: '4px',
          background: '#334155',
          fontSize: '11px',
          color: '#94a3b8'
        }}>
          {strategy.timeframe}
        </span>
      </div>

      {/* 指标类型 */}
      <div style={{
        padding: '10px',
        borderRadius: '8px',
        background: '#1e293b',
        marginBottom: '12px'
      }}>
        <div style={{ fontSize: '11px', color: '#64748b', marginBottom: '4px' }}>
          指标类型
        </div>
        <div style={{ fontSize: '13px', color: '#e2e8f0', fontWeight: 'bold', textTransform: 'uppercase' }}>
          {strategy.indicators.type}
          {Object.keys(strategy.indicators.params).length > 0 && (
            <span style={{ fontSize: '11px', color: '#64748b', fontWeight: 'normal', marginLeft: '8px' }}>
              ({Object.entries(strategy.indicators.params).map(([k, v]) => `${k}: ${v}`).join(', ')})
            </span>
          )}
        </div>
      </div>

      {/* 入场/出场规则 */}
      <div style={{ marginBottom: '12px' }}>
        <div style={{ fontSize: '11px', color: '#64748b', marginBottom: '4px' }}>
          入场规则
        </div>
        <div style={{ fontSize: '12px', color: '#10b981', lineHeight: 1.5 }}>
          {strategy.entryRules}
        </div>
      </div>

      <div style={{ marginBottom: '12px' }}>
        <div style={{ fontSize: '11px', color: '#64748b', marginBottom: '4px' }}>
          出场规则
        </div>
        <div style={{ fontSize: '12px', color: '#f59e0b', lineHeight: 1.5 }}>
          {strategy.exitRules}
        </div>
      </div>

      {/* 风险管理 */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(3, 1fr)',
        gap: '8px'
      }}>
        {[
          { label: '止损', value: `${(strategy.riskManagement.stopLoss * 100).toFixed(1)}%`, color: '#ef4444' },
          { label: '止盈', value: `${(strategy.riskManagement.takeProfit * 100).toFixed(1)}%`, color: '#10b981' },
          { label: '最大仓位', value: `${(strategy.riskManagement.maxPositionSize * 100).toFixed(0)}%`, color: '#3b82f6' },
        ].map(item => (
          <div key={item.label} style={{
            padding: '8px',
            borderRadius: '6px',
            background: '#1e293b',
            textAlign: 'center'
          }}>
            <div style={{ fontSize: '11px', color: '#64748b' }}>{item.label}</div>
            <div style={{ fontSize: '14px', fontWeight: 'bold', color: item.color }}>
              {item.value}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
