/**
 * Copyright 2026 NEMT Lab
 *
 * Backtest UI Components
 * 回测 UI 组件
 */

import React, { useState, useRef, useEffect, useCallback } from 'react';
import type { BacktestMetrics, Trade, EquityPoint, BacktestStatus } from './types';
import { useBacktestStore } from './store';

// ============================================
// 样式
// ============================================

const styles: Record<string, React.CSSProperties> = {
  container: {
    display: 'flex',
    flexDirection: 'column',
    gap: '24px',
    padding: '24px',
    background: 'var(--bg-primary)',
    minHeight: '100%',
    color: 'var(--text-primary)',
  },
  header: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  title: {
    fontSize: '20px',
    fontWeight: 700,
    background: 'linear-gradient(135deg, #8b5cf6, #6366f1)',
    WebkitBackgroundClip: 'text',
    WebkitTextFillColor: 'transparent',
  },
  tabBar: {
    display: 'flex',
    gap: '4px',
    padding: '4px',
    background: 'var(--bg-secondary)',
    borderRadius: '12px',
    width: 'fit-content',
  },
  tab: {
    padding: '8px 20px',
    borderRadius: '8px',
    border: 'none',
    background: 'transparent',
    color: 'var(--text-secondary)',
    fontSize: '13px',
    fontWeight: 500,
    cursor: 'pointer',
    transition: 'all 0.2s',
  },
  tabActive: {
    background: 'var(--accent)',
    color: 'white',
    boxShadow: '0 2px 8px rgba(139, 92, 246, 0.4)',
  },
  grid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
    gap: '16px',
  },
  card: {
    background: 'var(--bg-secondary)',
    border: '1px solid var(--border)',
    borderRadius: '16px',
    padding: '20px',
  },
  cardTitle: {
    fontSize: '11px',
    fontWeight: 600,
    textTransform: 'uppercase',
    letterSpacing: '0.05em',
    color: 'var(--text-tertiary)',
    marginBottom: '8px',
  },
  metricValue: {
    fontSize: '24px',
    fontWeight: 700,
    fontFamily: 'monospace',
    color: 'var(--text-primary)',
  },
  metricUnit: {
    fontSize: '12px',
    color: 'var(--text-secondary)',
    marginLeft: '4px',
  },
  positive: { color: 'var(--success)' },
  negative: { color: 'var(--danger)' },
  chartContainer: {
    background: 'var(--bg-secondary)',
    border: '1px solid var(--border)',
    borderRadius: '16px',
    padding: '20px',
    height: '400px',
  },
  table: {
    width: '100%',
    borderCollapse: 'collapse',
    fontSize: '13px',
  },
  th: {
    textAlign: 'left',
    padding: '12px 16px',
    borderBottom: '1px solid var(--border)',
    color: 'var(--text-tertiary)',
    fontWeight: 600,
    fontSize: '11px',
    textTransform: 'uppercase',
    letterSpacing: '0.05em',
  },
  td: {
    padding: '12px 16px',
    borderBottom: '1px solid var(--border)',
    color: 'var(--text-secondary)',
    fontFamily: 'monospace',
  },
  button: {
    padding: '10px 20px',
    borderRadius: '8px',
    border: 'none',
    background: 'linear-gradient(135deg, #8b5cf6, #6366f1)',
    color: 'white',
    fontSize: '13px',
    fontWeight: 600,
    cursor: 'pointer',
    transition: 'all 0.2s',
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
  },
  buttonSecondary: {
    background: 'var(--bg-secondary)',
    border: '1px solid var(--border)',
    color: 'var(--text-primary)',
  },
  input: {
    padding: '10px 14px',
    borderRadius: '8px',
    border: '1px solid var(--border)',
    background: 'var(--bg-secondary)',
    color: 'var(--text-primary)',
    fontSize: '13px',
    fontFamily: 'monospace',
    outline: 'none',
    width: '100%',
  },
  select: {
    padding: '10px 14px',
    borderRadius: '8px',
    border: '1px solid var(--border)',
    background: 'var(--bg-secondary)',
    color: 'var(--text-primary)',
    fontSize: '13px',
    outline: 'none',
    cursor: 'pointer',
    minWidth: '120px',
  },
  formGroup: {
    display: 'flex',
    flexDirection: 'column',
    gap: '6px',
  },
  label: {
    fontSize: '11px',
    fontWeight: 600,
    color: 'var(--text-tertiary)',
    textTransform: 'uppercase',
    letterSpacing: '0.05em',
  },
  progressBar: {
    height: '4px',
    borderRadius: '2px',
    background: 'var(--bg-tertiary)',
    overflow: 'hidden',
  },
  progressFill: {
    height: '100%',
    background: 'linear-gradient(90deg, #8b5cf6, #6366f1)',
    transition: 'width 0.3s ease',
  },
  tag: {
    display: 'inline-flex',
    alignItems: 'center',
    padding: '2px 8px',
    borderRadius: '4px',
    fontSize: '10px',
    fontWeight: 600,
    textTransform: 'uppercase',
  },
};

// ============================================
// MetricCard 组件
// ============================================

interface MetricCardProps {
  title: string;
  value: number | string;
  unit?: string;
  positive?: boolean;
  negative?: boolean;
  icon?: React.ReactNode;
}

export function MetricCard({ title, value, unit, positive, negative, icon }: MetricCardProps) {
  const valueStyle: React.CSSProperties = {
    ...styles.metricValue,
    ...(positive ? styles.positive : {}),
    ...(negative ? styles.negative : {}),
  };

  return (
    <div style={styles.card}>
      <div style={styles.cardTitle}>{title}</div>
      <div style={{ display: 'flex', alignItems: 'baseline', gap: '8px' }}>
        {icon}
        <span style={valueStyle}>{value}</span>
        {unit && <span style={styles.metricUnit}>{unit}</span>}
      </div>
    </div>
  );
}

// ============================================
// ProgressBar 组件
// ============================================

interface ProgressBarProps {
  progress: number;
  showText?: boolean;
}

export function ProgressBar({ progress, showText = true }: ProgressBarProps) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
      <div style={{ flex: 1, ...styles.progressBar }}>
        <div style={{ ...styles.progressFill, width: `${Math.min(100, progress)}%` }} />
      </div>
      {showText && (
        <span style={{ fontSize: '12px', color: 'var(--text-secondary)', fontFamily: 'monospace', minWidth: '45px' }}>
          {progress.toFixed(1)}%
        </span>
      )}
    </div>
  );
}

// ============================================
// EquityChart 组件 (Canvas)
// ============================================

interface EquityChartProps {
  equity: EquityPoint[];
  trades?: Trade[];
  height?: number;
}

export function EquityChart({ equity, trades = [], height = 300 }: EquityChartProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    const container = containerRef.current;
    if (!canvas || !container || equity.length === 0) return;

    const dpr = window.devicePixelRatio || 1;
    const rect = container.getBoundingClientRect();
    canvas.width = rect.width * dpr;
    canvas.height = height * dpr;
    canvas.style.width = `${rect.width}px`;
    canvas.style.height = `${height}px`;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    ctx.scale(dpr, dpr);
    ctx.clearRect(0, 0, rect.width, height);

    const values = equity.map((e) => e.value);
    const min = Math.min(...values);
    const max = Math.max(...values);
    const range = max - min || 1;
    const pad = 20;
    const w = rect.width - pad * 2;
    const h = height - pad * 2;

    // 网格
    ctx.strokeStyle = 'rgba(255,255,255,0.05)';
    ctx.lineWidth = 1;
    for (let i = 0; i <= 4; i++) {
      const y = pad + (h * i) / 4;
      ctx.beginPath();
      ctx.moveTo(pad, y);
      ctx.lineTo(pad + w, y);
      ctx.stroke();
    }

    // 权益曲线
    const gradient = ctx.createLinearGradient(0, pad, 0, pad + h);
    gradient.addColorStop(0, 'rgba(139, 92, 246, 0.3)');
    gradient.addColorStop(1, 'rgba(139, 92, 246, 0)');

    ctx.beginPath();
    ctx.moveTo(pad, pad + h);
    for (let i = 0; i < equity.length; i++) {
      const x = pad + (i / (equity.length - 1)) * w;
      const y = pad + h - ((equity[i].value - min) / range) * h;
      ctx.lineTo(x, y);
    }
    ctx.lineTo(pad + w, pad + h);
    ctx.closePath();
    ctx.fillStyle = gradient;
    ctx.fill();

    // 线条
    ctx.beginPath();
    for (let i = 0; i < equity.length; i++) {
      const x = pad + (i / (equity.length - 1)) * w;
      const y = pad + h - ((equity[i].value - min) / range) * h;
      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    }
    ctx.strokeStyle = '#8b5cf6';
    ctx.lineWidth = 2;
    ctx.stroke();

    // 交易标记
    if (trades.length > 0) {
      const timeStart = equity[0].time;
      const timeEnd = equity[equity.length - 1].time;
      const timeRange = timeEnd - timeStart || 1;

      for (const trade of trades) {
        const x = pad + ((trade.exitTime - timeStart) / timeRange) * w;
        ctx.beginPath();
        ctx.arc(x, pad + h - ((equity.find((e) => e.time >= trade.exitTime)?.value ?? min) - min) / range * h, 4, 0, Math.PI * 2);
        ctx.fillStyle = trade.pnl >= 0 ? '#10b981' : '#ef4444';
        ctx.fill();
      }
    }

    // Y 轴标签
    ctx.fillStyle = '#64748b';
    ctx.font = '11px monospace';
    ctx.textAlign = 'right';
    ctx.fillText(`$${max.toLocaleString()}`, pad - 4, pad + 4);
    ctx.fillText(`$${min.toLocaleString()}`, pad - 4, pad + h + 4);
  }, [equity, trades, height]);

  return (
    <div ref={containerRef} style={{ width: '100%' }}>
      <canvas ref={canvasRef} style={{ display: 'block' }} />
    </div>
  );
}

// ============================================
// TradeTable 组件
// ============================================

interface TradeTableProps {
  trades: Trade[];
  onSelect?: (trade: Trade) => void;
  maxRows?: number;
}

export function TradeTable({ trades, onSelect, maxRows = 20 }: TradeTableProps) {
  const displayTrades = trades.slice(0, maxRows);

  const formatTime = (ts: number) => {
    const d = new Date(ts);
    return d.toLocaleString('zh-CN', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
  };

  return (
    <div style={{ overflowX: 'auto', maxHeight: '400px', overflowY: 'auto' }}>
      <table style={styles.table}>
        <thead>
          <tr>
            <th style={styles.th}>#</th>
            <th style={styles.th}>方向</th>
            <th style={styles.th}>入场时间</th>
            <th style={styles.th}>入场价</th>
            <th style={styles.th}>出场价</th>
            <th style={styles.th}>盈亏</th>
            <th style={styles.th}>收益率</th>
            <th style={styles.th}>持仓时间</th>
            <th style={styles.th}>出场原因</th>
          </tr>
        </thead>
        <tbody>
          {displayTrades.map((trade, i) => (
            <tr
              key={trade.id}
              style={{ cursor: onSelect ? 'pointer' : 'default' }}
              onClick={() => onSelect?.(trade)}
            >
              <td style={styles.td}>{i + 1}</td>
              <td style={styles.td}>
                <span
                  style={{
                    ...styles.tag,
                    background: trade.direction === 'long' ? 'rgba(16,185,129,0.15)' : 'rgba(239,68,68,0.15)',
                    color: trade.direction === 'long' ? '#10b981' : '#ef4444',
                  }}
                >
                  {trade.direction.toUpperCase()}
                </span>
              </td>
              <td style={styles.td}>{formatTime(trade.entryTime)}</td>
              <td style={styles.td}>${trade.entryPrice.toFixed(2)}</td>
              <td style={styles.td}>${trade.exitPrice.toFixed(2)}</td>
              <td style={{ ...styles.td, color: trade.pnl >= 0 ? '#10b981' : '#ef4444' }}>
                {trade.pnl >= 0 ? '+' : ''}{trade.pnl.toFixed(2)}
              </td>
              <td style={{ ...styles.td, color: trade.pnlPercent >= 0 ? '#10b981' : '#ef4444' }}>
                {trade.pnlPercent >= 0 ? '+' : ''}{trade.pnlPercent.toFixed(2)}%
              </td>
              <td style={styles.td}>{trade.duration}m</td>
              <td style={styles.td}>
                <span
                  style={{
                    ...styles.tag,
                    background:
                      trade.exitReason === 'roi'
                        ? 'rgba(139,92,246,0.15)'
                        : trade.exitReason === 'stop_loss'
                        ? 'rgba(239,68,68,0.15)'
                        : 'rgba(59,130,246,0.15)',
                    color:
                      trade.exitReason === 'roi'
                        ? '#8b5cf6'
                        : trade.exitReason === 'stop_loss'
                        ? '#ef4444'
                        : '#3b82f6',
                  }}
                >
                  {trade.exitReason}
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {trades.length > maxRows && (
        <div style={{ textAlign: 'center', padding: '12px', color: 'var(--text-tertiary)', fontSize: '12px' }}>
          显示 {maxRows} / {trades.length} 条交易
        </div>
      )}
    </div>
  );
}

// ============================================
// StatusBadge 组件
// ============================================

export function StatusBadge({ status }: { status: BacktestStatus }) {
  const config: Record<BacktestStatus, { color: string; bg: string; label: string }> = {
    idle: { color: '#94a3b8', bg: 'rgba(148,163,184,0.15)', label: '待运行' },
    loading: { color: '#f59e0b', bg: 'rgba(245,158,11,0.15)', label: '加载中' },
    running: { color: '#3b82f6', bg: 'rgba(59,130,246,0.15)', label: '运行中' },
    completed: { color: '#10b981', bg: 'rgba(16,185,129,0.15)', label: '已完成' },
    error: { color: '#ef4444', bg: 'rgba(239,68,68,0.15)', label: '错误' },
  };

  const c = config[status] || config.idle;

  return (
    <span
      style={{
        ...styles.tag,
        background: c.bg,
        color: c.color,
        display: 'inline-flex',
        alignItems: 'center',
        gap: '6px',
      }}
    >
      {status === 'running' && (
        <span
          style={{
            width: '6px',
            height: '6px',
            borderRadius: '50%',
            background: c.color,
            animation: 'pulse 1s infinite',
          }}
        />
      )}
      {c.label}
    </span>
  );
}
