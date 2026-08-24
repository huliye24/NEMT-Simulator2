/**
 * NEMT 执行框架卡片组件
 * 展示第七章：预测→信号→验证→加仓 的执行状态
 */

import React from 'react';
import { 
  Target, 
  Zap, 
  Shield, 
  Plus, 
  TrendingUp, 
  CheckCircle, 
  AlertTriangle,
  Clock,
  X
} from 'lucide-react';
import { ExecutionCard } from '../services/executionFramework';

interface ExecutionCardProps {
  card: ExecutionCard;
  compact?: boolean;
}

export const ExecutionCardComponent: React.FC<ExecutionCardProps> = ({ card, compact = false }) => {
  const directionColors: Record<string, string> = {
    strongly_bullish: '#52c41a',
    cautiously_bullish: '#73d13d',
    neutral: '#8c8c8c',
    cautiously_bearish: '#ff7a45',
    strongly_bearish: '#ff4d4f',
    watch: '#faad14',
  };

  const directionLabels: Record<string, string> = {
    strongly_bullish: '强烈看多',
    cautiously_bullish: '谨慎看多',
    neutral: '中性',
    cautiously_bearish: '谨慎看空',
    strongly_bearish: '强烈看空',
    watch: '观望',
  };

  const cycleLabels: Record<string, string> = {
    monthly: '月线级别',
    weekly: '周线级别',
    daily: '日线级别',
    none: '不交易',
  };

  const signalTypeLabels: Record<string, string> = {
    vortex_breakout: '涡旋突破',
    stochastic_resonance: '随机共振',
    trend_pullback: '趋势回调',
    none: '无信号',
  };

  const phaseLabels: Record<string, string> = {
    A: 'A 相-高噪声',
    B: 'B 相-临界',
    C: 'C 相-涡旋',
    D: 'D 相-趋势',
  };

  if (compact) {
    return (
      <div style={{
        background: 'white',
        borderRadius: '8px',
        padding: '12px 16px',
        boxShadow: '0 1px 4px rgba(0,0,0,0.08)',
        display: 'flex',
        alignItems: 'center',
        gap: '16px',
      }}>
        {/* 狩猎模式 */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <Target size={16} style={{ color: card.prediction.huntingMode === 'on' ? '#52c41a' : '#d9d9d9' }} />
          <span style={{ 
            fontSize: '12px', 
            fontWeight: 600,
            color: card.prediction.huntingMode === 'on' ? '#52c41a' : '#999'
          }}>
            狩猎 {card.prediction.huntingMode === 'on' ? '开启' : '关闭'}
          </span>
        </div>

        {/* 方向 */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <TrendingUp size={16} style={{ color: directionColors[card.prediction.directionBias] }} />
          <span style={{ fontSize: '12px', color: directionColors[card.prediction.directionBias] }}>
            {directionLabels[card.prediction.directionBias]}
          </span>
        </div>

        {/* 信号 */}
        {card.currentSignal && card.currentSignal.type !== 'none' && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <Zap size={16} style={{ color: '#722ed1' }} />
            <span style={{ fontSize: '12px', color: '#722ed1' }}>
              {signalTypeLabels[card.currentSignal.type]}
            </span>
          </div>
        )}

        {/* 持仓 */}
        {card.position && (
          <div style={{ 
            padding: '4px 8px', 
            background: card.position.pnlPercent >= 0 ? '#f6ffed' : '#fff2f0',
            borderRadius: '4px',
            fontSize: '12px',
            color: card.position.pnlPercent >= 0 ? '#52c41a' : '#ff4d4f'
          }}>
            持仓 {card.position.pnlPercent >= 0 ? '+' : ''}{card.position.pnlPercent.toFixed(1)}%
          </div>
        )}
      </div>
    );
  }

  // 完整版
  return (
    <div style={{
      background: 'white',
      borderRadius: '12px',
      padding: '20px',
      boxShadow: '0 2px 8px rgba(0,0,0,0.08)',
      marginBottom: '16px',
    }}>
      <div style={{ 
        display: 'flex', 
        alignItems: 'center', 
        justifyContent: 'space-between',
        marginBottom: '16px',
        paddingBottom: '12px',
        borderBottom: '1px solid #f0f0f0'
      }}>
        <h4 style={{ margin: 0, display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Target size={18} style={{ color: '#1890ff' }} />
          NEMT 执行框架
        </h4>
        <span style={{ 
          fontSize: '12px', 
          padding: '4px 8px',
          borderRadius: '4px',
          background: card.prediction.huntingMode === 'on' ? '#f6ffed' : '#fafafa',
          color: card.prediction.huntingMode === 'on' ? '#52c41a' : '#999',
          fontWeight: 600
        }}>
          狩猎模式 {card.prediction.huntingMode === 'on' ? '开启' : '关闭'}
        </span>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '16px' }}>
        {/* 预测 */}
        <div style={{ padding: '12px', background: '#fafafa', borderRadius: '8px' }}>
          <div style={{ fontSize: '11px', color: '#999', marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '4px' }}>
            <TrendingUp size={12} />
            预测
          </div>
          <div style={{ fontSize: '14px', fontWeight: 600, color: directionColors[card.prediction.directionBias] }}>
            {directionLabels[card.prediction.directionBias]}
          </div>
          <div style={{ fontSize: '12px', color: '#666', marginTop: '4px' }}>
            {cycleLabels[card.prediction.cycleLevel]}
          </div>
          <div style={{ fontSize: '11px', color: '#999', marginTop: '4px' }}>
            宏观 {card.prediction.macroScore}/10 | 链上 {card.prediction.onchainScore}/10
          </div>
        </div>

        {/* 信号 */}
        <div style={{ padding: '12px', background: '#fafafa', borderRadius: '8px' }}>
          <div style={{ fontSize: '11px', color: '#999', marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '4px' }}>
            <Zap size={12} />
            信号
          </div>
          {card.currentSignal && card.currentSignal.type !== 'none' ? (
            <>
              <div style={{ fontSize: '14px', fontWeight: 600, color: '#722ed1' }}>
                {signalTypeLabels[card.currentSignal.type]}
              </div>
              <div style={{ fontSize: '12px', color: '#666', marginTop: '4px' }}>
                {card.currentSignal.phase ? phaseLabels[card.currentSignal.phase] || card.currentSignal.phase : ''}
                {card.currentSignal.maturity ? ` 成熟度 ${card.currentSignal.maturity}` : ''}
              </div>
              <div style={{ fontSize: '11px', color: '#52c41a', marginTop: '4px' }}>
                置信度 {(card.currentSignal.confidence * 100).toFixed(0)}%
              </div>
            </>
          ) : (
            <div style={{ fontSize: '12px', color: '#999' }}>
              无有效信号
            </div>
          )}
        </div>

        {/* 验证 */}
        <div style={{ padding: '12px', background: '#fafafa', borderRadius: '8px' }}>
          <div style={{ fontSize: '11px', color: '#999', marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '4px' }}>
            <Shield size={12} />
            验证
          </div>
          {card.verification ? (
            <>
              <div style={{ 
                fontSize: '14px', 
                fontWeight: 600, 
                color: card.verification.passed 
                  ? (card.verification.confidence === 'full' ? '#52c41a' : '#faad14') 
                  : '#ff4d4f' 
              }}>
                {card.verification.passed 
                  ? (card.verification.confidence === 'full' ? '验证通过' : '谨慎通过') 
                  : '验证失败'}
              </div>
              <div style={{ fontSize: '11px', color: '#999', marginTop: '4px' }}>
                通过 {card.verification.passedCount}/{card.verification.totalWeight} 项
              </div>
            </>
          ) : (
            <div style={{ fontSize: '12px', color: '#999' }}>
              待验证
            </div>
          )}
        </div>

        {/* 持仓 */}
        <div style={{ padding: '12px', background: '#fafafa', borderRadius: '8px' }}>
          <div style={{ fontSize: '11px', color: '#999', marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '4px' }}>
            <Plus size={12} />
            持仓
          </div>
          {card.position ? (
            <>
              <div style={{ 
                fontSize: '14px', 
                fontWeight: 600, 
                color: card.position.pnlPercent >= 0 ? '#52c41a' : '#ff4d4f' 
              }}>
                {card.position.pnlPercent >= 0 ? '+' : ''}{card.position.pnlPercent.toFixed(1)}%
              </div>
              <div style={{ fontSize: '11px', color: '#999', marginTop: '4px' }}>
                入场 ${card.position.entryPrice.toFixed(0)} | 止损 ${card.position.stopLoss.toFixed(0)}
              </div>
              {card.addPositionTiming && (
                <div style={{ fontSize: '11px', color: '#1890ff', marginTop: '4px' }}>
                  加仓时机: {card.addPositionTiming}
                </div>
              )}
            </>
          ) : (
            <div style={{ fontSize: '12px', color: '#999' }}>
              无持仓
            </div>
          )}
        </div>
      </div>

      {/* 止盈状态 */}
      {card.position && (
        <div style={{ 
          marginTop: '12px', 
          padding: '12px', 
          background: '#f9f9f9', 
          borderRadius: '8px',
          display: 'flex',
          gap: '12px',
          flexWrap: 'wrap'
        }}>
          <span style={{ fontSize: '12px', color: '#666', fontWeight: 500 }}>止盈触发:</span>
          {[
            { key: 'tier1Triggered', label: 'MVRV/NUPL', color: '#faad14' },
            { key: 'tier2Triggered', label: '交易所流入', color: '#52c41a' },
            { key: 'tier3Triggered', label: 'DCI破位', color: '#1890ff' },
            { key: 'tier4Triggered', label: '宏观恶化', color: '#ff4d4f' },
          ].map(item => {
            const triggered = (card.takeProfitStatus as any)[item.key];
            return (
              <div 
                key={item.key}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '4px',
                  fontSize: '11px',
                  color: triggered ? item.color : '#d9d9d9'
                }}
              >
                {triggered ? <CheckCircle size={12} /> : <Clock size={12} />}
                {item.label}
              </div>
            );
          })}
        </div>
      )}

      {/* 冷静期 */}
      {card.cooldownUntil && (
        <div style={{
          marginTop: '12px',
          padding: '8px 12px',
          background: '#fff2f0',
          borderRadius: '6px',
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          fontSize: '12px',
          color: '#ff4d4f'
        }}>
          <Clock size={14} />
          冷静期至: {new Date(card.cooldownUntil).toLocaleString('zh-CN')}
        </div>
      )}

      {/* 离场原因 */}
      {card.exitReason && (
        <div style={{
          marginTop: '12px',
          padding: '8px 12px',
          background: '#fafafa',
          borderRadius: '6px',
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          fontSize: '12px',
          color: '#666'
        }}>
          <X size={14} />
          上次离场: {card.exitReason}
        </div>
      )}
    </div>
  );
};

export default ExecutionCardComponent;
