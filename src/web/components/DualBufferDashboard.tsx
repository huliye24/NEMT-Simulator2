/**
 * Copyright 2026 NEMT Lab
 *
 * 双缓冲策略检验仪表板
 *
 * 功能：
 * 1. 显示从策略市场选择的策略
 * 2. 配置历史回测区间和策略参数
 * 3. 运行回测并查看详细结果
 * 4. 审核通过后开启实时执行
 * 5. 对比回测与实战的业绩差异
 * 6. 结果写回策略市场
 */

import React, { useCallback, useState } from 'react';
import {
  useDualBufferStore,
  useCurrentSession,
  useBacktestProgress,
  useBacktestPeriod,
  useBacktestConfig,
  useLiveKlines,
  useLiveNEMTState,
  useLivePrice,
  useLiveRunning,
  useSessions,
  type KlineData,
  type BacktestResult,
  type Trade,
} from '../stores/dualBufferStore';

// ============================================
// 样式
// ============================================

const colors = {
  bg: '#0f172a',
  card: '#1e293b',
  border: '#334155',
  text: '#e2e8f0',
  textMuted: '#64748b',
  accent: '#8b5cf6',
  accent2: '#6366f1',
  positive: '#22c55e',
  negative: '#ef4444',
  warning: '#fbbf24',
};

const css = {
  container: {
    padding: '24px',
    background: colors.bg,
    minHeight: '100vh',
    color: colors.text,
    fontFamily: 'system-ui, -apple-system, sans-serif',
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: '24px',
    flexWrap: 'wrap' as const,
    gap: '16px',
  },
  title: {
    fontSize: '24px',
    fontWeight: 'bold' as const,
    margin: 0,
    background: `linear-gradient(135deg, ${colors.accent}, ${colors.accent2})`,
    WebkitBackgroundClip: 'text',
    WebkitTextFillColor: 'transparent',
  },
  section: {
    background: colors.card,
    borderRadius: '12px',
    padding: '20px',
    border: `1px solid ${colors.border}`,
    marginBottom: '20px',
  },
  sectionTitle: {
    fontSize: '14px',
    fontWeight: 'bold' as const,
    color: colors.textMuted,
    marginBottom: '16px',
    textTransform: 'uppercase' as const,
    letterSpacing: '0.5px',
  },
  grid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
    gap: '16px',
  },
  grid3: {
    display: 'grid',
    gridTemplateColumns: 'repeat(3, 1fr)',
    gap: '12px',
  },
  metric: {
    background: colors.bg,
    borderRadius: '8px',
    padding: '16px',
    textAlign: 'center' as const,
  },
  metricValue: {
    fontSize: '24px',
    fontWeight: 'bold' as const,
    fontFamily: 'monospace',
  },
  metricLabel: {
    fontSize: '12px',
    color: colors.textMuted,
    marginTop: '4px',
  },
  input: {
    padding: '10px 14px',
    borderRadius: '8px',
    border: `1px solid ${colors.border}`,
    background: colors.bg,
    color: colors.text,
    fontSize: '14px',
    width: '100%',
    boxSizing: 'border-box' as const,
  },
  select: {
    padding: '10px 14px',
    borderRadius: '8px',
    border: `1px solid ${colors.border}`,
    background: colors.bg,
    color: colors.text,
    fontSize: '14px',
    cursor: 'pointer',
  },
  button: {
    padding: '12px 24px',
    borderRadius: '8px',
    border: 'none',
    fontSize: '14px',
    cursor: 'pointer',
    fontWeight: 'bold' as const,
    transition: 'all 0.2s',
  },
  btnPrimary: {
    background: `linear-gradient(135deg, ${colors.accent}, ${colors.accent2})`,
    color: '#fff',
  },
  btnDanger: {
    background: colors.negative,
    color: '#fff',
  },
  btnSuccess: {
    background: colors.positive,
    color: '#fff',
  },
  btnOutline: {
    background: 'transparent',
    border: `1px solid ${colors.border}`,
    color: colors.text,
  },
  row: {
    display: 'flex',
    gap: '12px',
    alignItems: 'center',
    flexWrap: 'wrap' as const,
  },
  label: {
    fontSize: '13px',
    color: colors.textMuted,
    minWidth: '80px',
  },
  progressBar: {
    height: '8px',
    background: colors.bg,
    borderRadius: '4px',
    overflow: 'hidden',
    marginTop: '8px',
  },
  progressFill: {
    height: '100%',
    background: `linear-gradient(90deg, ${colors.accent}, ${colors.accent2})`,
    transition: 'width 0.3s',
  },
  tabs: {
    display: 'flex',
    gap: '4px',
    marginBottom: '20px',
    background: colors.bg,
    padding: '4px',
    borderRadius: '8px',
  },
  tab: {
    padding: '8px 16px',
    borderRadius: '6px',
    fontSize: '13px',
    cursor: 'pointer',
    border: 'none',
    background: 'transparent',
    color: colors.textMuted,
    fontWeight: 'bold' as const,
  },
  tabActive: {
    background: colors.accent,
    color: '#fff',
  },
  chip: {
    display: 'inline-block',
    padding: '4px 8px',
    borderRadius: '4px',
    fontSize: '12px',
    fontWeight: 'bold' as const,
  },
  chipBuy: {
    background: 'rgba(34, 197, 94, 0.2)',
    color: colors.positive,
  },
  chipSell: {
    background: 'rgba(239, 68, 68, 0.2)',
    color: colors.negative,
  },
  empty: {
    textAlign: 'center',
    padding: '60px',
    color: colors.textMuted,
  },
  strategyCard: {
    background: `linear-gradient(135deg, ${colors.accent}20, ${colors.accent2}20)`,
    borderRadius: '12px',
    padding: '20px',
    border: `1px solid ${colors.accent}40`,
    marginBottom: '20px',
  },
};

// ============================================
// 子组件
// ============================================

function MetricCard({ label, value, color, sub }: {
  label: string; value: string | number; color?: string; sub?: string;
}) {
  return (
    <div style={css.metric}>
      <div style={{ ...css.metricValue, color: color || colors.text }}>
        {typeof value === 'number' ? value.toLocaleString() : value}
      </div>
      <div style={css.metricLabel}>{label}</div>
      {sub && <div style={{ fontSize: '11px', color: colors.textMuted }}>{sub}</div>}
    </div>
  );
}

function EquityChart({ data, color, height = 200 }: {
  data: { time: number; value: number }[]; color: string; height?: number;
}) {
  const canvasRef = React.useRef<HTMLCanvasElement>(null);

  React.useEffect(() => {
    if (!canvasRef.current || data.length === 0) return;
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const w = canvas.offsetWidth;
    const h = height;
    canvas.width = w * 2;
    canvas.height = h * 2;
    ctx.scale(2, 2);

    ctx.fillStyle = colors.bg;
    ctx.fillRect(0, 0, w, h);

    const values = data.map(d => d.value);
    const minVal = Math.min(...values);
    const maxVal = Math.max(...values);
    const range = maxVal - minVal || 1;

    ctx.strokeStyle = colors.border;
    ctx.lineWidth = 0.5;
    for (let i = 0; i <= 4; i++) {
      const y = (h / 4) * i;
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(w, y);
      ctx.stroke();
    }

    ctx.strokeStyle = color;
    ctx.lineWidth = 2;
    ctx.beginPath();
    data.forEach((d, i) => {
      const x = (i / (data.length - 1)) * w;
      const y = h - ((d.value - minVal) / range) * (h - 20);
      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    });
    ctx.stroke();

    ctx.lineTo(w, h);
    ctx.lineTo(0, h);
    ctx.closePath();
    ctx.fillStyle = color + '20';
    ctx.fill();

    ctx.fillStyle = colors.textMuted;
    ctx.font = '11px monospace';
    ctx.fillText(`$${maxVal.toFixed(0)}`, 5, 14);
    ctx.fillText(`$${minVal.toFixed(0)}`, 5, h - 5);
  }, [data, color, height]);

  return <canvas ref={canvasRef} style={{ width: '100%', height: `${height}px` }} />;
}

function KLineChart({ data, trades }: { data: KlineData[]; trades: Trade[] }) {
  const canvasRef = React.useRef<HTMLCanvasElement>(null);

  React.useEffect(() => {
    if (!canvasRef.current || data.length === 0) return;
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const w = canvas.offsetWidth;
    const h = 300;
    canvas.width = w * 2;
    canvas.height = h * 2;
    ctx.scale(2, 2);

    const padding = { top: 10, right: 10, bottom: 30, left: 10 };
    const chartW = w - padding.left - padding.right;
    const chartH = h - padding.top - padding.bottom;

    ctx.fillStyle = colors.card;
    ctx.fillRect(0, 0, w, h);

    const prices = data.flatMap(d => [d.high, d.low]);
    const minPrice = Math.min(...prices);
    const maxPrice = Math.max(...prices);
    const priceRange = maxPrice - minPrice || 1;

    const candleW = Math.max(1, chartW / data.length - 1);

    data.forEach((k, i) => {
      const x = padding.left + (i * chartW / data.length);
      const yHigh = padding.top + chartH * (1 - (k.high - minPrice) / priceRange);
      const yLow = padding.top + chartH * (1 - (k.low - minPrice) / priceRange);
      const yOpen = padding.top + chartH * (1 - (k.open - minPrice) / priceRange);
      const yClose = padding.top + chartH * (1 - (k.close - minPrice) / priceRange);

      const isUp = k.close >= k.open;
      ctx.strokeStyle = isUp ? colors.positive : colors.negative;
      ctx.fillStyle = isUp ? colors.positive : colors.negative;

      ctx.beginPath();
      ctx.moveTo(x + candleW / 2, yHigh);
      ctx.lineTo(x + candleW / 2, yLow);
      ctx.stroke();

      const bodyTop = Math.min(yOpen, yClose);
      const bodyH = Math.max(1, Math.abs(yClose - yOpen));
      ctx.fillRect(x, bodyTop, candleW, bodyH);
    });

    // 标记交易
    trades.forEach(trade => {
      const entryIdx = data.findIndex(d => d.time >= trade.entryTime);
      const exitIdx = data.findIndex(d => d.time >= trade.exitTime);
      if (entryIdx < 0 || exitIdx < 0) return;

      const entryX = padding.left + (entryIdx * chartW / data.length) + candleW / 2;
      const exitX = padding.left + (exitIdx * chartW / data.length) + candleW / 2;
      const y = padding.top + chartH / 2;

      ctx.strokeStyle = (trade.pnl > 0 ? colors.positive : colors.negative) + '80';
      ctx.lineWidth = 1;
      ctx.setLineDash([4, 4]);
      ctx.beginPath();
      ctx.moveTo(entryX, y);
      ctx.lineTo(exitX, y);
      ctx.stroke();
      ctx.setLineDash([]);

      ctx.fillStyle = trade.pnl > 0 ? colors.positive : colors.negative;
      ctx.beginPath();
      ctx.arc(entryX, y, 4, 0, Math.PI * 2);
      ctx.fill();
      ctx.beginPath();
      ctx.arc(exitX, y, 4, 0, Math.PI * 2);
      ctx.fill();
    });
  }, [data, trades]);

  return <canvas ref={canvasRef} style={{ width: '100%', height: '300px' }} />;
}

function TradeRow({ trade }: { trade: Trade }) {
  const entryTime = new Date(trade.entryTime).toLocaleDateString();
  const exitTime = new Date(trade.exitTime).toLocaleDateString();

  return (
    <tr style={{ borderBottom: `1px solid ${colors.border}` }}>
      <td style={{ padding: '10px', fontFamily: 'monospace' }}>{entryTime}</td>
      <td style={{ padding: '10px' }}>
        <span style={{ ...css.chip, ...(trade.type === 'LONG' ? css.chipBuy : css.chipSell) }}>
          {trade.type}
        </span>
      </td>
      <td style={{ padding: '10px', fontFamily: 'monospace' }}>${trade.entryPrice.toFixed(2)}</td>
      <td style={{ padding: '10px', fontFamily: 'monospace' }}>${trade.exitPrice.toFixed(2)}</td>
      <td style={{ padding: '10px', fontFamily: 'monospace', color: trade.pnl >= 0 ? colors.positive : colors.negative }}>
        {trade.pnl >= 0 ? '+' : ''}{trade.pnl.toFixed(2)}
      </td>
      <td style={{ padding: '10px', fontFamily: 'monospace', color: trade.pnlPercent >= 0 ? colors.positive : colors.negative }}>
        {trade.pnlPercent >= 0 ? '+' : ''}{trade.pnlPercent.toFixed(2)}%
      </td>
      <td style={{ padding: '10px', fontFamily: 'monospace' }}>{exitTime}</td>
    </tr>
  );
}

// ============================================
// 主组件
// ============================================

export function DualBufferDashboard() {
  const currentSession = useCurrentSession();
  const backtestProgress = useBacktestProgress();
  const backtestPeriod = useBacktestPeriod();
  const backtestConfig = useBacktestConfig();
  const liveKlines = useLiveKlines();
  const liveNEMTState = useLiveNEMTState();
  const currentPrice = useLivePrice();
  const liveRunning = useLiveRunning();
  const sessions = useSessions();

  const {
    runBacktest,
    approveBacktest,
    rejectBacktest,
    startLive,
    stopLive,
    setBacktestPeriod,
    setBacktestConfig,
    clearSession,
  } = useDualBufferStore();

  const [activeTab, setActiveTab] = useState<'config' | 'backtest' | 'live' | 'compare'>('config');
  const [localPeriod, setLocalPeriod] = useState(backtestPeriod);

  // 当策略被加载时，默认切换到配置标签
  React.useEffect(() => {
    if (currentSession) {
      setActiveTab('config');
    }
  }, [currentSession?.strategyId]);

  const handleRunBacktest = useCallback(() => {
    setBacktestPeriod(localPeriod);
    runBacktest().then(() => {
      setActiveTab('backtest');
    });
  }, [localPeriod, setBacktestPeriod, runBacktest]);

  const handleApprove = useCallback(() => {
    if (!currentSession?.backtestResult) return;
    approveBacktest(currentSession.strategyId, currentSession.backtestResult);
    setActiveTab('live');
    startLive();
  }, [currentSession, approveBacktest, startLive]);

  const handleReject = useCallback(() => {
    if (!currentSession) return;
    rejectBacktest(currentSession.strategyId);
    clearSession();
    setActiveTab('config');
  }, [currentSession, rejectBacktest, clearSession]);

  // 无策略时
  if (!currentSession) {
    return (
      <div style={css.container}>
        <div style={css.empty}>
          <div style={{ fontSize: '48px', marginBottom: '16px' }}>🧪</div>
          <div style={{ fontSize: '18px', fontWeight: 'bold', marginBottom: '8px' }}>
            暂无策略
          </div>
          <div style={{ fontSize: '14px' }}>
            请从「策略市场」选择一个策略，点击「回测」按钮进入双缓冲检验
          </div>
        </div>
      </div>
    );
  }

  const result = currentSession.backtestResult;

  return (
    <div style={css.container}>
      {/* 头部 */}
      <div style={css.header}>
        <div>
          <h1 style={css.title}>双缓冲检验</h1>
          <div style={{ fontSize: '13px', color: colors.textMuted, marginTop: '4px' }}>
            历史回测 + 实时执行 = 双重验证
          </div>
        </div>
      </div>

      {/* 策略信息卡片 */}
      <div style={css.strategyCard}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <div>
            <div style={{ fontSize: '18px', fontWeight: 'bold', color: colors.text, marginBottom: '4px' }}>
              {currentSession.strategyName}
            </div>
            <div style={{ fontSize: '13px', color: colors.textMuted }}>
              ID: {currentSession.strategyId}
            </div>
            <div style={{ fontSize: '13px', color: colors.textMuted, marginTop: '8px' }}>
              创建于: {new Date(currentSession.createdAt).toLocaleString()}
            </div>
          </div>
          <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
            {result && !liveRunning && (
              <span style={{
                padding: '6px 12px',
                borderRadius: '6px',
                fontSize: '12px',
                fontWeight: 'bold',
                background: result.totalReturn >= 0 ? colors.positive + '20' : colors.negative + '20',
                color: result.totalReturn >= 0 ? colors.positive : colors.negative,
              }}>
                {result.totalReturn >= 0 ? '+' : ''}{result.totalReturn.toFixed(2)}%
              </span>
            )}
            {liveRunning && (
              <span style={{
                padding: '6px 12px',
                borderRadius: '6px',
                fontSize: '12px',
                fontWeight: 'bold',
                background: colors.positive + '20',
                color: colors.positive,
              }}>
                LIVE
              </span>
            )}
          </div>
        </div>
      </div>

      {/* 标签页 */}
      <div style={css.tabs}>
        {(['config', 'backtest', 'live', 'compare'] as const).map(tab => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            style={{
              ...css.tab,
              ...(activeTab === tab ? css.tabActive : {}),
            }}
          >
            {tab === 'config' ? '配置' : tab === 'backtest' ? '回测结果' : tab === 'live' ? '实时执行' : '对比'}
          </button>
        ))}
      </div>

      {/* 配置标签页 */}
      {activeTab === 'config' && (
        <>
          <div style={css.section}>
            <div style={css.sectionTitle}>回测区间</div>
            <div style={css.grid}>
              <div>
                <div style={{ fontSize: '12px', color: colors.textMuted, marginBottom: '6px' }}>开始日期</div>
                <input
                  type="date"
                  value={localPeriod.startDate}
                  onChange={e => setLocalPeriod(p => ({ ...p, startDate: e.target.value }))}
                  style={css.input}
                />
              </div>
              <div>
                <div style={{ fontSize: '12px', color: colors.textMuted, marginBottom: '6px' }}>结束日期</div>
                <input
                  type="date"
                  value={localPeriod.endDate}
                  onChange={e => setLocalPeriod(p => ({ ...p, endDate: e.target.value }))}
                  style={css.input}
                />
              </div>
            </div>
          </div>

          <div style={css.section}>
            <div style={css.sectionTitle}>策略参数</div>
            <div style={css.grid}>
              <div>
                <div style={{ fontSize: '12px', color: colors.textMuted, marginBottom: '6px' }}>初始资金</div>
                <input
                  type="number"
                  value={backtestConfig.initialCapital}
                  onChange={e => setBacktestConfig({ initialCapital: parseFloat(e.target.value) })}
                  style={css.input}
                />
              </div>
              <div>
                <div style={{ fontSize: '12px', color: colors.textMuted, marginBottom: '6px' }}>仓位比例</div>
                <input
                  type="number"
                  step="0.1"
                  value={backtestConfig.positionSize}
                  onChange={e => setBacktestConfig({ positionSize: parseFloat(e.target.value) })}
                  style={css.input}
                />
              </div>
              <div>
                <div style={{ fontSize: '12px', color: colors.textMuted, marginBottom: '6px' }}>止损 %</div>
                <input
                  type="number"
                  step="0.5"
                  value={backtestConfig.stopLossPercent}
                  onChange={e => setBacktestConfig({ stopLossPercent: parseFloat(e.target.value) })}
                  style={css.input}
                />
              </div>
              <div>
                <div style={{ fontSize: '12px', color: colors.textMuted, marginBottom: '6px' }}>止盈 %</div>
                <input
                  type="number"
                  step="0.5"
                  value={backtestConfig.takeProfitPercent}
                  onChange={e => setBacktestConfig({ takeProfitPercent: parseFloat(e.target.value) })}
                  style={css.input}
                />
              </div>
            </div>
          </div>

          <div style={css.section}>
            <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
              <button
                onClick={handleRunBacktest}
                disabled={backtestProgress.backtesting}
                style={{
                  ...css.button,
                  ...css.btnPrimary,
                  ...(backtestProgress.backtesting ? { opacity: 0.5, cursor: 'not-allowed' } : {}),
                }}
              >
                {backtestProgress.backtesting ? `回测中... ${backtestProgress.progress}%` : '开始回测'}
              </button>
              {backtestProgress.backtesting && (
                <div style={{ flex: 1 }}>
                  <div style={css.progressBar}>
                    <div style={{ ...css.progressFill, width: `${backtestProgress.progress}%` }} />
                  </div>
                </div>
              )}
            </div>
          </div>
        </>
      )}

      {/* 回测结果标签页 */}
      {activeTab === 'backtest' && (
        <>
          {!result ? (
            <div style={css.empty}>
              <div>暂无回测结果</div>
            </div>
          ) : (
            <>
              <div style={css.section}>
                <div style={css.sectionTitle}>核心指标</div>
                <div style={css.grid}>
                  <MetricCard
                    label="总收益率"
                    value={`${result.totalReturn >= 0 ? '+' : ''}${result.totalReturn.toFixed(2)}%`}
                    color={result.totalReturn >= 0 ? colors.positive : colors.negative}
                    sub={`年化 ${result.annualizedReturn.toFixed(2)}%`}
                  />
                  <MetricCard
                    label="夏普比率"
                    value={result.sharpeRatio.toFixed(2)}
                    color={result.sharpeRatio > 1 ? colors.positive : colors.negative}
                  />
                  <MetricCard
                    label="最大回撤"
                    value={`-${result.maxDrawdown.toFixed(2)}%`}
                    color={colors.negative}
                  />
                  <MetricCard
                    label="胜率"
                    value={`${result.winRate.toFixed(1)}%`}
                    color={result.winRate > 50 ? colors.positive : colors.negative}
                    sub={`${result.winningTrades}胜 / ${result.losingTrades}负`}
                  />
                  <MetricCard
                    label="盈亏比"
                    value={result.profitFactor.toFixed(2)}
                    color={result.profitFactor > 1 ? colors.positive : colors.negative}
                  />
                  <MetricCard
                    label="交易次数"
                    value={result.totalTrades}
                    sub={`${result.totalBars} 根K线`}
                  />
                </div>
              </div>

              <div style={css.section}>
                <div style={css.sectionTitle}>权益曲线</div>
                <EquityChart data={result.equityCurve} color={colors.accent} />
              </div>

              <div style={css.section}>
                <div style={css.sectionTitle}>K线 + 交易标记</div>
                <KLineChart data={result.klines} trades={result.trades} />
              </div>

              <div style={css.section}>
                <div style={css.sectionTitle}>交易明细</div>
                <div style={{ maxHeight: '400px', overflow: 'auto' }}>
                  <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                    <thead>
                      <tr>
                        {['入场时间', '方向', '入场价', '出场价', '盈亏', '收益率', '出场时间'].map(h => (
                          <th key={h} style={{ padding: '10px', textAlign: 'left', color: colors.textMuted, borderBottom: `1px solid ${colors.border}`, fontWeight: 'bold', fontSize: '13px' }}>{h}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {result.trades.map(trade => (
                        <TradeRow key={trade.id} trade={trade} />
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* 审核按钮 */}
              <div style={css.section}>
                <div style={css.sectionTitle}>审核决策</div>
                <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
                  <div style={{ flex: 1 }}>
                    <div style={{ fontSize: '13px', color: colors.textMuted }}>
                      审核回测结果：胜率 {result.winRate.toFixed(1)}%，夏普 {result.sharpeRatio.toFixed(2)}，最大回撤 {result.maxDrawdown.toFixed(2)}%
                    </div>
                    <div style={{ fontSize: '12px', color: colors.textMuted, marginTop: '4px' }}>
                      通过 → 开启实时执行 | 不通过 → 归档策略
                    </div>
                  </div>
                  <button
                    onClick={handleReject}
                    style={{ ...css.button, ...css.btnDanger }}
                  >
                    不通过
                  </button>
                  <button
                    onClick={handleApprove}
                    style={{ ...css.button, ...css.btnSuccess }}
                  >
                    通过并实战
                  </button>
                </div>
              </div>
            </>
          )}
        </>
      )}

      {/* 实时执行标签页 */}
      {activeTab === 'live' && (
        <>
          <div style={css.section}>
            <div style={css.sectionTitle}>实时状态</div>
            <div style={css.grid}>
              <MetricCard
                label="状态"
                value={liveRunning ? '运行中' : '已停止'}
                color={liveRunning ? colors.positive : colors.textMuted}
              />
              <MetricCard
                label="当前价格"
                value={`$${currentPrice.toLocaleString(undefined, { minimumFractionDigits: 2 })}`}
              />
              <MetricCard
                label="NEMT 相位"
                value={liveNEMTState.phase}
                color={
                  liveNEMTState.phase === 'critical_up' ? colors.positive :
                  liveNEMTState.phase === 'critical_down' ? colors.negative : colors.warning
                }
              />
              <MetricCard
                label="增长率 ψ"
                value={`${liveNEMTState.psi.toFixed(3)}%`}
                color={liveNEMTState.psi >= 0 ? colors.positive : colors.negative}
              />
              <MetricCard
                label="衰减率 φ"
                value={`${liveNEMTState.phi.toFixed(3)}%`}
              />
              <MetricCard
                label="熵 S"
                value={liveNEMTState.entropy.toFixed(3)}
              />
            </div>
            <div style={{ marginTop: '16px' }}>
              {!liveRunning ? (
                <button onClick={startLive} style={{ ...css.button, ...css.btnPrimary }}>
                  启动实时执行
                </button>
              ) : (
                <button onClick={stopLive} style={{ ...css.button, ...css.btnDanger }}>
                  停止执行
                </button>
              )}
            </div>
          </div>

          {liveKlines.length > 0 && (
            <div style={css.section}>
              <div style={css.sectionTitle}>实时 K线</div>
              <KLineChart data={liveKlines} trades={[]} />
            </div>
          )}
        </>
      )}

      {/* 对比标签页 */}
      {activeTab === 'compare' && (
        <div style={css.section}>
          <div style={css.sectionTitle}>历史回测 vs 实时执行</div>
          {result || liveRunning ? (
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px' }}>
              {result && (
                <div>
                  <div style={{ fontSize: '13px', color: colors.accent, fontWeight: 'bold', marginBottom: '12px' }}>
                    历史回测
                  </div>
                  <EquityChart data={result.equityCurve} color={colors.accent} height={150} />
                  <div style={{ marginTop: '12px', ...css.grid3 }}>
                    <div style={css.metric}>
                      <div style={{ ...css.metricValue, fontSize: '16px' }}>{result.totalReturn.toFixed(1)}%</div>
                      <div style={css.metricLabel}>收益率</div>
                    </div>
                    <div style={css.metric}>
                      <div style={{ ...css.metricValue, fontSize: '16px' }}>{result.winRate.toFixed(0)}%</div>
                      <div style={css.metricLabel}>胜率</div>
                    </div>
                    <div style={css.metric}>
                      <div style={{ ...css.metricValue, fontSize: '16px' }}>{result.sharpeRatio.toFixed(2)}</div>
                      <div style={css.metricLabel}>夏普</div>
                    </div>
                  </div>
                </div>
              )}
              <div>
                <div style={{ fontSize: '13px', color: colors.positive, fontWeight: 'bold', marginBottom: '12px' }}>
                  实时执行 {liveRunning ? '(进行中)' : '(未开始)'}
                </div>
                {liveRunning && liveKlines.length > 0 ? (
                  <EquityChart
                    data={liveKlines.map((k, i) => ({ time: k.time, value: 10000 + i * 10 }))}
                    color={colors.positive}
                    height={150}
                  />
                ) : (
                  <div style={{ height: '150px', background: colors.bg, borderRadius: '8px', display: 'flex', alignItems: 'center', justifyContent: 'center', color: colors.textMuted }}>
                    暂无数据
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div style={css.empty}>暂无数据</div>
          )}
        </div>
      )}
    </div>
  );
}

export default DualBufferDashboard;
