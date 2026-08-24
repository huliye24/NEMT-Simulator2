/**
 * Copyright 2026 NEMT Lab
 *
 * NEMT 市场仪表板 - 实时市场数据、NEMT 状态和交易信号
 */

import React, { useEffect, useState, useCallback, useRef } from 'react';
import {
  useExecutionStore,
  useExecutionState,
  useCurrentPrice,
  useKlines,
  useNEMTState,
  useSignals,
  useLastSignal,
  type KlineData,
  type NEMTSignal,
} from '../stores/nemtExecutionStore';

// ============================================
// 样式
// ============================================

const styles: Record<string, React.CSSProperties> = {
  container: {
    padding: '24px',
    background: '#0f172a',
    minHeight: '100vh',
    color: '#e2e8f0',
    fontFamily: 'system-ui, -apple-system, sans-serif',
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '24px',
  },
  title: {
    fontSize: '24px',
    fontWeight: 'bold',
    margin: 0,
    background: 'linear-gradient(135deg, #8b5cf6, #6366f1)',
    WebkitBackgroundClip: 'text',
    WebkitTextFillColor: 'transparent',
  },
  controls: {
    display: 'flex',
    gap: '12px',
  },
  select: {
    padding: '8px 16px',
    borderRadius: '8px',
    border: '1px solid #334155',
    background: '#1e293b',
    color: '#e2e8f0',
    fontSize: '14px',
    cursor: 'pointer',
  },
  button: {
    padding: '8px 16px',
    borderRadius: '8px',
    border: 'none',
    fontSize: '14px',
    cursor: 'pointer',
    fontWeight: '500',
    transition: 'all 0.2s',
  },
  buttonPrimary: {
    background: 'linear-gradient(135deg, #8b5cf6, #6366f1)',
    color: '#fff',
  },
  buttonDanger: {
    background: '#ef4444',
    color: '#fff',
  },
  buttonDisabled: {
    opacity: 0.5,
    cursor: 'not-allowed',
  },
  grid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(4, 1fr)',
    gap: '16px',
    marginBottom: '24px',
  },
  card: {
    background: '#1e293b',
    borderRadius: '12px',
    padding: '20px',
    border: '1px solid #334155',
  },
  cardTitle: {
    fontSize: '12px',
    color: '#94a3b8',
    marginBottom: '8px',
    textTransform: 'uppercase',
    letterSpacing: '0.5px',
  },
  cardValue: {
    fontSize: '28px',
    fontWeight: 'bold',
    fontFamily: 'monospace',
  },
  cardSub: {
    fontSize: '12px',
    color: '#64748b',
    marginTop: '4px',
  },
  positive: {
    color: '#22c55e',
  },
  negative: {
    color: '#ef4444',
  },
  grid2: {
    display: 'grid',
    gridTemplateColumns: '1fr 1fr',
    gap: '16px',
    marginBottom: '24px',
  },
  chartContainer: {
    background: '#1e293b',
    borderRadius: '12px',
    padding: '20px',
    border: '1px solid #334155',
    height: '400px',
  },
  signalList: {
    background: '#1e293b',
    borderRadius: '12px',
    padding: '20px',
    border: '1px solid #334155',
    maxHeight: '400px',
    overflow: 'auto',
  },
  signalItem: {
    padding: '12px',
    borderRadius: '8px',
    marginBottom: '8px',
    background: '#0f172a',
    border: '1px solid #334155',
  },
  signalHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '8px',
  },
  signalType: {
    padding: '4px 12px',
    borderRadius: '4px',
    fontWeight: 'bold',
    fontSize: '14px',
  },
  typeBuy: {
    background: 'rgba(34, 197, 94, 0.2)',
    color: '#22c55e',
  },
  typeSell: {
    background: 'rgba(239, 68, 68, 0.2)',
    color: '#ef4444',
  },
  typeHold: {
    background: 'rgba(100, 116, 139, 0.2)',
    color: '#64748b',
  },
  signalDetails: {
    display: 'grid',
    gridTemplateColumns: 'repeat(3, 1fr)',
    gap: '8px',
    fontSize: '12px',
  },
  detailItem: {
    display: 'flex',
    justifyContent: 'space-between',
  },
  detailLabel: {
    color: '#64748b',
  },
  detailValue: {
    fontFamily: 'monospace',
  },
  nemtMetrics: {
    display: 'grid',
    gridTemplateColumns: 'repeat(3, 1fr)',
    gap: '12px',
  },
  metric: {
    textAlign: 'center' as const,
    padding: '12px',
    background: '#0f172a',
    borderRadius: '8px',
  },
  metricValue: {
    fontSize: '24px',
    fontWeight: 'bold',
    fontFamily: 'monospace',
  },
  metricLabel: {
    fontSize: '11px',
    color: '#64748b',
    marginTop: '4px',
  },
  phaseIndicator: {
    display: 'inline-block',
    padding: '4px 12px',
    borderRadius: '4px',
    fontSize: '12px',
    fontWeight: 'bold',
    marginLeft: '12px',
  },
  phaseStable: { background: 'rgba(34, 197, 94, 0.2)', color: '#22c55e' },
  phaseCritical: { background: 'rgba(251, 191, 36, 0.2)', color: '#fbbf24' },
  phaseCriticalUp: { background: 'rgba(34, 197, 94, 0.3)', color: '#4ade80' },
  phaseCriticalDown: { background: 'rgba(239, 68, 68, 0.3)', color: '#f87171' },
  phaseDecay: { background: 'rgba(100, 116, 139, 0.2)', color: '#94a3b8' },
  priceHeader: {
    display: 'flex',
    alignItems: 'baseline',
    gap: '16px',
  },
  loading: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    height: '200px',
    color: '#64748b',
  },
  empty: {
    textAlign: 'center',
    padding: '40px',
    color: '#64748b',
  },
  connectionStatus: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    fontSize: '13px',
  },
  statusDot: {
    width: '8px',
    height: '8px',
    borderRadius: '50%',
  },
};

// ============================================
// 子组件
// ============================================

/** 价格卡片 */
function PriceCard({ price, change, changePercent }: { price: number; change: number; changePercent: number }) {
  const isPositive = changePercent >= 0;
  const color = isPositive ? styles.positive : styles.negative;

  return (
    <div style={styles.card}>
      <div style={styles.cardTitle}>当前价格</div>
      <div style={styles.cardValue}>
        ${price.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
      </div>
      <div style={{ ...styles.cardSub, ...color }}>
        {isPositive ? '+' : ''}{change.toFixed(2)} ({isPositive ? '+' : ''}{changePercent.toFixed(2)}%)
      </div>
    </div>
  );
}

/** NEMT 状态卡片 */
function NEMTStateCard({ state }: { state: ReturnType<typeof useNEMTState> }) {
  const getPhaseStyle = () => {
    switch (state.phase) {
      case 'stable': return styles.phaseStable;
      case 'critical': return styles.phaseCritical;
      case 'critical_up': return styles.phaseCriticalUp;
      case 'critical_down': return styles.phaseCriticalDown;
      default: return styles.phaseDecay;
    }
  };

  const getPhaseText = () => {
    switch (state.phase) {
      case 'stable': return '稳定';
      case 'critical': return '临界';
      case 'critical_up': return '临界上涨';
      case 'critical_down': return '临界下跌';
      default: return '衰减';
    }
  };

  return (
    <div style={styles.card}>
      <div style={styles.cardTitle}>NEMT 状态</div>
      <div style={{ marginBottom: '16px' }}>
        <span style={{ ...styles.cardValue, fontSize: '20px' }}>
          {getPhaseText()}
        </span>
        <span style={{ ...styles.phaseIndicator, ...getPhaseStyle() }}>
          {state.phase}
        </span>
      </div>
      <div style={styles.nemtMetrics}>
        <div style={styles.metric}>
          <div style={{ ...styles.metricValue, color: '#8b5cf6' }}>{state.psi.toFixed(3)}%</div>
          <div style={styles.metricLabel}>ψ 增长率</div>
        </div>
        <div style={styles.metric}>
          <div style={{ ...styles.metricValue, color: '#6366f1' }}>{state.phi.toFixed(3)}%</div>
          <div style={styles.metricLabel}>φ 衰减率</div>
        </div>
        <div style={styles.metric}>
          <div style={{ ...styles.metricValue, color: '#f59e0b' }}>{state.entropy.toFixed(3)}</div>
          <div style={styles.metricLabel}>S 熵</div>
        </div>
      </div>
      <div style={{ marginTop: '16px', fontSize: '12px', color: '#64748b' }}>
        <div>波幅: {state.waveAmplitude.toFixed(3)}% | 频率: {state.waveFrequency.toFixed(3)}</div>
      </div>
    </div>
  );
}

/** 信号列表 */
function SignalList({ signals }: { signals: NEMTSignal[] }) {
  const getTypeStyle = (type: string) => {
    switch (type) {
      case 'BUY': return styles.typeBuy;
      case 'SELL': return styles.typeSell;
      default: return styles.typeHold;
    }
  };

  const formatTime = (time: number) => {
    return new Date(time).toLocaleTimeString();
  };

  if (signals.length === 0) {
    return (
      <div style={styles.signalList}>
        <div style={styles.cardTitle}>交易信号</div>
        <div style={styles.empty}>暂无信号</div>
      </div>
    );
  }

  return (
    <div style={styles.signalList}>
      <div style={styles.cardTitle}>交易信号 ({signals.length})</div>
      {signals.slice(0, 10).map(signal => (
        <div key={signal.id} style={styles.signalItem}>
          <div style={styles.signalHeader}>
            <span style={{ ...styles.signalType, ...getTypeStyle(signal.type) }}>
              {signal.type}
            </span>
            <span style={{ fontSize: '12px', color: '#64748b' }}>
              {formatTime(signal.time)}
            </span>
          </div>
          <div style={{ fontSize: '13px', color: '#94a3b8', marginBottom: '8px' }}>
            {signal.reason}
          </div>
          <div style={styles.signalDetails}>
            <div style={styles.detailItem}>
              <span style={styles.detailLabel}>价格</span>
              <span style={styles.detailValue}>${signal.price.toFixed(2)}</span>
            </div>
            <div style={styles.detailItem}>
              <span style={styles.detailLabel}>置信度</span>
              <span style={styles.detailValue}>{signal.confidence}%</span>
            </div>
            <div style={styles.detailItem}>
              <span style={styles.detailLabel}>强度</span>
              <span style={styles.detailValue}>{signal.strength.toFixed(2)}</span>
            </div>
            <div style={styles.detailItem}>
              <span style={styles.detailLabel}>止损</span>
              <span style={{ ...styles.detailValue, color: '#ef4444' }}>${signal.stopLoss.toFixed(2)}</span>
            </div>
            <div style={styles.detailItem}>
              <span style={styles.detailLabel}>止盈</span>
              <span style={{ ...styles.detailValue, color: '#22c55e' }}>${signal.takeProfit.toFixed(2)}</span>
            </div>
            <div style={styles.detailItem}>
              <span style={styles.detailLabel}>盈亏比</span>
              <span style={styles.detailValue}>{signal.riskReward.toFixed(2)}</span>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}

/** K线图 (Canvas) */
function CandlestickChart({ data, lastSignal }: { data: KlineData[]; lastSignal: NEMTSignal | null }) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    if (!canvasRef.current || data.length === 0) return;

    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const width = canvas.width = canvas.offsetWidth * 2;
    const height = canvas.height = canvas.offsetHeight * 2;
    ctx.scale(2, 2);

    const w = canvas.offsetWidth;
    const h = canvas.offsetHeight;
    const padding = { top: 20, right: 60, bottom: 30, left: 10 };
    const chartWidth = w - padding.left - padding.right;
    const chartHeight = h - padding.top - padding.bottom;

    // 清除画布
    ctx.fillStyle = '#1e293b';
    ctx.fillRect(0, 0, w, h);

    // 计算价格范围
    const prices = data.flatMap(d => [d.high, d.low]);
    const minPrice = Math.min(...prices);
    const maxPrice = Math.max(...prices);
    const priceRange = maxPrice - minPrice;

    // 计算数量范围
    const volumes = data.map(d => d.volume);
    const maxVolume = Math.max(...volumes);

    // 绘制网格
    ctx.strokeStyle = '#334155';
    ctx.lineWidth = 0.5;
    for (let i = 0; i <= 4; i++) {
      const y = padding.top + (chartHeight / 4) * i;
      ctx.beginPath();
      ctx.moveTo(padding.left, y);
      ctx.lineTo(w - padding.right, y);
      ctx.stroke();
    }

    // 绘制K线
    const candleWidth = Math.max(2, chartWidth / data.length - 2);

    data.forEach((kline, i) => {
      const x = padding.left + (i * chartWidth / data.length);
      const yHigh = padding.top + chartHeight * (1 - (kline.high - minPrice) / priceRange);
      const yLow = padding.top + chartHeight * (1 - (kline.low - minPrice) / priceRange);
      const yOpen = padding.top + chartHeight * (1 - (kline.open - minPrice) / priceRange);
      const yClose = padding.top + chartHeight * (1 - (kline.close - minPrice) / priceRange);

      const isUp = kline.close >= kline.open;
      ctx.strokeStyle = isUp ? '#22c55e' : '#ef4444';
      ctx.fillStyle = isUp ? '#22c55e' : '#ef4444';

      // 影线
      ctx.beginPath();
      ctx.moveTo(x + candleWidth / 2, yHigh);
      ctx.lineTo(x + candleWidth / 2, yLow);
      ctx.stroke();

      // 实体
      const bodyTop = Math.min(yOpen, yClose);
      const bodyHeight = Math.max(1, Math.abs(yClose - yOpen));
      ctx.fillRect(x, bodyTop, candleWidth, bodyHeight);

      // 成交量柱
      const volHeight = (kline.volume / maxVolume) * 40;
      ctx.fillStyle = isUp ? 'rgba(34, 197, 94, 0.3)' : 'rgba(239, 68, 68, 0.3)';
      ctx.fillRect(x, h - padding.bottom - volHeight, candleWidth, volHeight);
    });

    // 绘制价格标签
    ctx.fillStyle = '#64748b';
    ctx.font = '11px monospace';
    ctx.textAlign = 'left';
    for (let i = 0; i <= 4; i++) {
      const price = minPrice + (priceRange / 4) * (4 - i);
      const y = padding.top + (chartHeight / 4) * i;
      ctx.fillText(price.toFixed(2), w - padding.right + 5, y + 4);
    }

    // 标记最新信号
    if (lastSignal) {
      const signalIndex = data.findIndex(d => Math.abs(d.close - lastSignal.price) < (priceRange / 10));
      if (signalIndex >= 0) {
        const x = padding.left + (signalIndex * chartWidth / data.length) + candleWidth / 2;
        const y = padding.top + chartHeight * (1 - (lastSignal.price - minPrice) / priceRange);

        ctx.strokeStyle = lastSignal.type === 'BUY' ? '#22c55e' : lastSignal.type === 'SELL' ? '#ef4444' : '#fbbf24';
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.arc(x, y, 8, 0, Math.PI * 2);
        ctx.stroke();

        ctx.fillStyle = lastSignal.type === 'BUY' ? '#22c55e' : lastSignal.type === 'SELL' ? '#ef4444' : '#fbbf24';
        ctx.beginPath();
        ctx.arc(x, y, 4, 0, Math.PI * 2);
        ctx.fill();
      }
    }

  }, [data, lastSignal]);

  return (
    <div style={styles.chartContainer}>
      <div style={styles.cardTitle}>K线图</div>
      <canvas
        ref={canvasRef}
        style={{ width: '100%', height: 'calc(100% - 30px)', display: 'block' }}
      />
    </div>
  );
}

// ============================================
// 主组件
// ============================================

export function NEMTDashboard() {
  const { connected, connecting, error, isRunning } = useExecutionState();
  const currentPrice = useCurrentPrice();
  const klines = useKlines();
  const nemtState = useNEMTState();
  const signals = useSignals();
  const lastSignal = useLastSignal();

  const {
    connect,
    disconnect,
    startExecution,
    stopExecution,
    setSymbol,
    setInterval,
  } = useExecutionStore();

  const [selectedSymbol, setSelectedSymbol] = useState('BTCUSDT');
  const [selectedInterval, setSelectedInterval] = useState('1h');

  const handleConnect = useCallback(() => {
    connect(selectedSymbol, selectedInterval);
    startExecution();
  }, [connect, selectedSymbol, selectedInterval, startExecution]);

  const handleDisconnect = useCallback(() => {
    disconnect();
    stopExecution();
  }, [disconnect, stopExecution]);

  const handleSymbolChange = useCallback((e: React.ChangeEvent<HTMLSelectElement>) => {
    setSelectedSymbol(e.target.value);
    setSymbol(e.target.value);
  }, [setSymbol]);

  const handleIntervalChange = useCallback((e: React.ChangeEvent<HTMLSelectElement>) => {
    setSelectedInterval(e.target.value);
    setInterval(e.target.value);
  }, [setInterval]);

  const getConnectionStatusColor = () => {
    if (connected) return '#22c55e';
    if (connecting) return '#fbbf24';
    return '#64748b';
  };

  const getConnectionStatusText = () => {
    if (connected) return '已连接';
    if (connecting) return '连接中...';
    return '未连接';
  };

  return (
    <div style={styles.container}>
      {/* 头部 */}
      <div style={styles.header}>
        <div>
          <h1 style={styles.title}>NEMT 策略执行</h1>
          <div style={styles.connectionStatus}>
            <span style={{ ...styles.statusDot, background: getConnectionStatusColor() }} />
            <span>{getConnectionStatusText()}</span>
            {connected && <span> | {selectedSymbol} | {selectedInterval}</span>}
          </div>
        </div>
        <div style={styles.controls}>
          <select
            value={selectedSymbol}
            onChange={handleSymbolChange}
            disabled={connected}
            style={styles.select}
          >
            <option value="BTCUSDT">BTC/USDT</option>
            <option value="ETHUSDT">ETH/USDT</option>
            <option value="SOLUSDT">SOL/USDT</option>
            <option value="BNBUSDT">BNB/USDT</option>
          </select>
          <select
            value={selectedInterval}
            onChange={handleIntervalChange}
            disabled={connected}
            style={styles.select}
          >
            <option value="1m">1 分钟</option>
            <option value="5m">5 分钟</option>
            <option value="15m">15 分钟</option>
            <option value="1h">1 小时</option>
            <option value="4h">4 小时</option>
            <option value="1d">1 天</option>
          </select>
          {!connected ? (
            <button
              onClick={handleConnect}
              style={{ ...styles.button, ...styles.buttonPrimary }}
              disabled={connecting}
            >
              {connecting ? '连接中...' : '开始执行'}
            </button>
          ) : (
            <button
              onClick={handleDisconnect}
              style={{ ...styles.button, ...styles.buttonDanger }}
            >
              停止
            </button>
          )}
        </div>
      </div>

      {/* 错误提示 */}
      {error && (
        <div style={{
          padding: '12px',
          marginBottom: '24px',
          background: 'rgba(239, 68, 68, 0.1)',
          border: '1px solid #ef4444',
          borderRadius: '8px',
          color: '#ef4444',
        }}>
          错误: {error}
        </div>
      )}

      {/* 价格和状态卡片 */}
      <div style={styles.grid}>
        <PriceCard
          price={currentPrice || 0}
          change={useExecutionStore.getState().priceChange24h}
          changePercent={useExecutionStore.getState().priceChangePercent24h}
        />
        <NEMTStateCard state={nemtState} />
        <div style={styles.card}>
          <div style={styles.cardTitle}>市场状态</div>
          <div style={styles.nemtMetrics}>
            <div style={styles.metric}>
              <div style={{ ...styles.metricValue, color: '#64748b' }}>{klines.length}</div>
              <div style={styles.metricLabel}>K线数量</div>
            </div>
            <div style={styles.metric}>
              <div style={{ ...styles.metricValue, color: '#8b5cf6' }}>{signals.length}</div>
              <div style={styles.metricLabel}>信号总数</div>
            </div>
            <div style={styles.metric}>
              <div style={{
                ...styles.metricValue,
                color: lastSignal?.type === 'BUY' ? '#22c55e' : lastSignal?.type === 'SELL' ? '#ef4444' : '#64748b'
              }}>
                {lastSignal?.type || 'HOLD'}
              </div>
              <div style={styles.metricLabel}>最新信号</div>
            </div>
          </div>
        </div>
        <div style={styles.card}>
          <div style={styles.cardTitle}>执行状态</div>
          <div style={styles.nemtMetrics}>
            <div style={styles.metric}>
              <div style={{ ...styles.metricValue, color: isRunning ? '#22c55e' : '#64748b' }}>
                {isRunning ? '运行中' : '已停止'}
              </div>
              <div style={styles.metricLabel}>状态</div>
            </div>
            <div style={styles.metric}>
              <div style={{ ...styles.metricValue, color: '#64748b' }}>
                {lastSignal ? new Date(lastSignal.time).toLocaleTimeString() : '--'}
              </div>
              <div style={styles.metricLabel}>最后更新</div>
            </div>
            <div style={styles.metric}>
              <div style={{ ...styles.metricValue, color: '#6366f1' }}>
                {nemtState.criticalThreshold}
              </div>
              <div style={styles.metricLabel}>临界阈值</div>
            </div>
          </div>
        </div>
      </div>

      {/* 图表和信号 */}
      <div style={styles.grid2}>
        <CandlestickChart data={klines} lastSignal={lastSignal} />
        <SignalList signals={signals} />
      </div>
    </div>
  );
}

export default NEMTDashboard;
