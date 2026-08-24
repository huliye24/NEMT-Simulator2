/**
 * Copyright 2026 NEMT Lab
 *
 * Backtest View
 * 回测主视图页面
 */

import React, { useState, useEffect, useCallback, useMemo } from 'react';
import {
  MetricCard,
  ProgressBar,
  EquityChart,
  TradeTable,
  StatusBadge,
} from './components';
import {
  useBacktestStore,
  useBacktestProgress,
} from './store';
import type {
  BacktestConfig,
  Trade,
  BacktestResult,
  DataFrame,
} from './types';
import type { StrategyName } from './engineCore';
import {
  loadFromBinance,
  generateMockData,
  validateData,
  cacheData,
  getCachedData,
} from './dataLoader';
import { runBacktest, runTurtleBacktest } from './engineCore';

// ============================================
// 样式
// ============================================

const s = {
  container: {
    display: 'flex',
    flexDirection: 'column' as const,
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
    flexWrap: 'wrap' as const,
    gap: '16px',
  },
  title: {
    fontSize: '22px',
    fontWeight: 700,
    background: 'linear-gradient(135deg, #8b5cf6, #6366f1)',
    WebkitBackgroundClip: 'text',
    WebkitTextFillColor: 'transparent',
  },
  headerActions: {
    display: 'flex',
    gap: '8px',
    alignItems: 'center',
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
    fontFamily: 'inherit',
  },
  grid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
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
    textTransform: 'uppercase' as const,
    letterSpacing: '0.05em',
    color: 'var(--text-tertiary)',
    marginBottom: '12px',
  },
  chartCard: {
    background: 'var(--bg-secondary)',
    border: '1px solid var(--border)',
    borderRadius: '16px',
    padding: '20px',
  },
  formGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))',
    gap: '16px',
  },
  formGroup: {
    display: 'flex',
    flexDirection: 'column' as const,
    gap: '6px',
  },
  label: {
    fontSize: '11px',
    fontWeight: 600,
    color: 'var(--text-tertiary)',
    textTransform: 'uppercase' as const,
    letterSpacing: '0.05em',
  },
  input: {
    padding: '10px 14px',
    borderRadius: '8px',
    border: '1px solid var(--border)',
    background: 'var(--bg-primary)',
    color: 'var(--text-primary)',
    fontSize: '13px',
    fontFamily: 'monospace',
    outline: 'none',
    transition: 'border-color 0.2s',
    width: '100%',
    boxSizing: 'border-box' as const,
  },
  select: {
    padding: '10px 14px',
    borderRadius: '8px',
    border: '1px solid var(--border)',
    background: 'var(--bg-primary)',
    color: 'var(--text-primary)',
    fontSize: '13px',
    outline: 'none',
    cursor: 'pointer',
    fontFamily: 'inherit',
    width: '100%',
    boxSizing: 'border-box' as const,
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
    fontFamily: 'inherit',
  },
  buttonSecondary: {
    background: 'var(--bg-secondary)',
    border: '1px solid var(--border)',
    color: 'var(--text-primary)',
  },
  buttonDanger: {
    background: 'rgba(239,68,68,0.1)',
    border: '1px solid rgba(239,68,68,0.3)',
    color: '#ef4444',
  },
  progressSection: {
    background: 'var(--bg-secondary)',
    border: '1px solid var(--border)',
    borderRadius: '16px',
    padding: '20px',
  },
  errorBox: {
    padding: '16px',
    borderRadius: '12px',
    background: 'rgba(239,68,68,0.1)',
    border: '1px solid rgba(239,68,68,0.3)',
    color: '#ef4444',
    fontSize: '13px',
  },
  emptyState: {
    display: 'flex',
    flexDirection: 'column' as const,
    alignItems: 'center',
    justifyContent: 'center',
    padding: '60px 20px',
    color: 'var(--text-tertiary)',
    textAlign: 'center' as const,
    gap: '12px',
  },
  section: {
    background: 'var(--bg-secondary)',
    border: '1px solid var(--border)',
    borderRadius: '16px',
    padding: '20px',
  },
  sectionTitle: {
    fontSize: '14px',
    fontWeight: 600,
    color: 'var(--text-primary)',
    marginBottom: '16px',
  },
};

// ============================================
// Tab 配置
// ============================================

type TabId = 'config' | 'results' | 'trades' | 'settings';

const TABS: { id: TabId; label: string }[] = [
  { id: 'config', label: '配置' },
  { id: 'results', label: '回测结果' },
  { id: 'trades', label: '交易记录' },
  { id: 'settings', label: '高级设置' },
];

// ============================================
// BacktestView 主组件
// ============================================

export function BacktestView() {
  const [activeTab, setActiveTab] = useState<TabId>('config');
  const [data, setData] = useState<DataFrame | null>(null);
  const [selectedTrade, setSelectedTrade] = useState<Trade | null>(null);
  const [dataStats, setDataStats] = useState<string>('');

  const {
    config,
    setConfig,
    status,
    result,
    trades,
    error,
    setStatus,
    setResult,
    setError,
    reset,
  } = useBacktestStore();

  const progress = useBacktestProgress();

  // ============================================
  // 运行回测
  // ============================================

  const handleRun = useCallback(async () => {
    try {
      setError(null);
      setStatus('loading');

      // 加载数据
      const cacheKey = `binance_${config.pair}_${config.timeframe}`;
      let df = getCachedData(cacheKey);

      if (!df) {
        const endTime = config.endDate || Date.now();
        const startTime = config.startDate || endTime - 90 * 24 * 60 * 60 * 1000;

        const raw = await loadFromBinance(
          config.pair,
          config.timeframe,
          startTime,
          endTime,
          1000
        );
        df = raw;
        cacheData(cacheKey, df);
      }

      setData(df);

      // 验证数据
      const validation = validateData(df);
      if (!validation.valid) {
        throw new Error(`数据验证失败: ${validation.errors.join(', ')}`);
      }

      setDataStats(
        `${validation.stats.bars} 根K线 | ` +
        `${new Date(validation.stats.startTime).toLocaleDateString('zh-CN')} - ` +
        `${new Date(validation.stats.endTime).toLocaleDateString('zh-CN')} | ` +
        `$${validation.stats.priceRange.min.toFixed(0)} - $${validation.stats.priceRange.max.toFixed(0)}`
      );

      setStatus('running');

      // 根据策略类型运行回测
      let backtestResult;
      if (config.strategy === 'turtle') {
        backtestResult = runTurtleBacktest(df, {
          initialCapital: config.initialCapital,
          commissionRate: config.commissionRate,
          stoploss: 0.1,
          canShort: false,
        });
      } else {
        backtestResult = runBacktest({
          df,
          strategy: config.strategy as any,
          initialCapital: config.initialCapital,
          commissionRate: config.commissionRate,
          stoploss: 0.1,
          canShort: false,
        });
      }

      setResult(backtestResult);
      setStatus('completed');
      setActiveTab('results');
    } catch (err) {
      setError((err as Error).message);
      setStatus('error');
    }
  }, [config, setError, setStatus, setResult]);

  // ============================================
  // 生成模拟数据
  // ============================================

  const handleGenerateMock = useCallback(() => {
    try {
      setError(null);
      setStatus('loading');

      const df = generateMockData(500, 3600000, 50000, 0.02, 0.0001);
      setData(df);
      cacheData('mock_btc', df);

      setDataStats(
        `${df.close.length} 根K线 | 模拟数据 | $50000 ±20%`
      );

      // 根据策略类型运行回测
      let backtestResult;
      if (config.strategy === 'turtle') {
        backtestResult = runTurtleBacktest(df, {
          initialCapital: config.initialCapital,
        });
      } else {
        backtestResult = runBacktest({
          df,
          strategy: config.strategy as any,
          initialCapital: config.initialCapital,
          commissionRate: config.commissionRate,
          stoploss: 0.1,
          canShort: false,
        });
      }

      setResult(backtestResult);
      setStatus('completed');
      setActiveTab('results');
    } catch (err) {
      setError((err as Error).message);
      setStatus('error');
    }
  }, [config, setError, setStatus, setResult]);

  // ============================================
  // 重置
  // ============================================

  const handleReset = useCallback(() => {
    reset();
    setData(null);
    setSelectedTrade(null);
    setDataStats('');
    setActiveTab('config');
  }, [reset]);

  // ============================================
  // 渲染 Tab
  // ============================================

  const renderConfigTab = () => (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* 快速操作 */}
      <div style={s.section}>
        <div style={s.sectionTitle}>快速开始</div>
        <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
          <button
            style={s.button}
            onClick={handleGenerateMock}
            disabled={status === 'running' || status === 'loading'}
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <polygon points="5,3 19,12 5,21" />
            </svg>
            使用模拟数据运行
          </button>
          <button
            style={{ ...s.button, ...s.buttonSecondary }}
            onClick={handleRun}
            disabled={status === 'running' || status === 'loading'}
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              <path d="M9 12l2 2 4-4" />
            </svg>
            从 Binance 加载并运行
          </button>
        </div>

        {dataStats && (
          <div style={{ marginTop: '16px', fontSize: '12px', color: 'var(--text-secondary)', fontFamily: 'monospace' }}>
            {dataStats}
          </div>
        )}
      </div>

      {/* 数据配置 */}
      <div style={s.section}>
        <div style={s.sectionTitle}>数据配置</div>
        <div style={s.formGrid}>
          <div style={s.formGroup}>
            <label style={s.label}>交易对</label>
            <input
              style={s.input}
              value={config.pair}
              onChange={(e) => setConfig({ pair: e.target.value })}
              placeholder="BTCUSDT"
            />
          </div>
          <div style={s.formGroup}>
            <label style={s.label}>时间周期</label>
            <select
              style={s.select}
              value={config.timeframe}
              onChange={(e) => setConfig({ timeframe: e.target.value as any })}
            >
              <option value="1m">1 分钟</option>
              <option value="5m">5 分钟</option>
              <option value="15m">15 分钟</option>
              <option value="30m">30 分钟</option>
              <option value="1h">1 小时</option>
              <option value="4h">4 小时</option>
              <option value="1d">1 天</option>
            </select>
          </div>
          <div style={s.formGroup}>
            <label style={s.label}>开始日期</label>
            <input
              style={s.input}
              type="date"
              value={new Date(config.startDate).toISOString().split('T')[0]}
              onChange={(e) => setConfig({ startDate: new Date(e.target.value).getTime() })}
            />
          </div>
          <div style={s.formGroup}>
            <label style={s.label}>结束日期</label>
            <input
              style={s.input}
              type="date"
              value={new Date(config.endDate).toISOString().split('T')[0]}
              onChange={(e) => setConfig({ endDate: new Date(e.target.value).getTime() })}
            />
          </div>
        </div>
      </div>

      {/* 资金配置 */}
      <div style={s.section}>
        <div style={s.sectionTitle}>资金配置</div>
        <div style={s.formGrid}>
          <div style={s.formGroup}>
            <label style={s.label}>初始资金 (USDT)</label>
            <input
              style={s.input}
              type="number"
              value={config.initialCapital}
              onChange={(e) => setConfig({ initialCapital: parseFloat(e.target.value) || 10000 })}
              min={100}
            />
          </div>
          <div style={s.formGroup}>
            <label style={s.label}>手续费率</label>
            <select
              style={s.select}
              value={config.commissionRate}
              onChange={(e) => setConfig({ commissionRate: parseFloat(e.target.value) })}
            >
              <option value={0.001}>Binance 标准 (0.1%)</option>
              <option value={0.0005}>Binance VIP 1 (0.05%)</option>
              <option value={0.0002}>Binance VIP 3 (0.02%)</option>
              <option value={0.00075}>OKX (0.075%)</option>
            </select>
          </div>
          <div style={s.formGroup}>
            <label style={s.label}>滑点</label>
            <select
              style={s.select}
              value={config.slippage}
              onChange={(e) => setConfig({ slippage: parseFloat(e.target.value) })}
            >
              <option value={0.0005}>0.05% (低)</option>
              <option value={0.001}>0.1% (中)</option>
              <option value={0.002}>0.2% (高)</option>
            </select>
          </div>
        </div>
      </div>
    </div>
  );

  const renderResultsTab = () => {
    if (!result) {
      return (
        <div style={s.emptyState}>
          <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" opacity="0.3">
            <path d="M3 3v18h18" />
            <path d="M18 17V9" />
            <path d="M13 17V5" />
            <path d="M8 17v-3" />
          </svg>
          <div style={{ fontSize: '14px', fontWeight: 600 }}>暂无回测结果</div>
          <div style={{ fontSize: '12px' }}>请先配置并运行回测</div>
        </div>
      );
    }

    const { metrics } = result;

    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
        {/* 核心指标 */}
        <div style={s.grid}>
          <MetricCard
            title="总收益率"
            value={metrics.totalReturn >= 0 ? `+${metrics.totalReturn.toFixed(2)}` : metrics.totalReturn.toFixed(2)}
            unit="%"
            positive={metrics.totalReturn > 0}
            negative={metrics.totalReturn < 0}
          />
          <MetricCard
            title="年化收益率"
            value={metrics.annualizedReturn >= 0 ? `+${metrics.annualizedReturn.toFixed(2)}` : metrics.annualizedReturn.toFixed(2)}
            unit="%"
            positive={metrics.annualizedReturn > 0}
            negative={metrics.annualizedReturn < 0}
          />
          <MetricCard
            title="夏普比率"
            value={metrics.sharpeRatio.toFixed(2)}
            positive={metrics.sharpeRatio > 1}
            negative={metrics.sharpeRatio < 0}
          />
          <MetricCard
            title="索提诺比率"
            value={metrics.sortinoRatio.toFixed(2)}
            positive={metrics.sortinoRatio > 1}
            negative={metrics.sortinoRatio < 0}
          />
          <MetricCard
            title="最大回撤"
            value={metrics.maxDrawdown >= 0 ? `-${metrics.maxDrawdown.toFixed(2)}` : metrics.maxDrawdown.toFixed(2)}
            unit="%"
            negative={metrics.maxDrawdown > 0}
          />
          <MetricCard
            title="胜率"
            value={metrics.winRate.toFixed(1)}
            unit="%"
            positive={metrics.winRate > 50}
            negative={metrics.winRate < 40}
          />
        </div>

        {/* 交易指标 */}
        <div style={s.grid}>
          <MetricCard title="总交易数" value={metrics.totalTrades} />
          <MetricCard title="盈利交易" value={metrics.winningTrades} />
          <MetricCard title="亏损交易" value={metrics.losingTrades} />
          <MetricCard title="盈亏比" value={metrics.profitFactor === Infinity ? '∞' : metrics.profitFactor.toFixed(2)} />
          <MetricCard title="平均盈利" value={`+${metrics.avgWin.toFixed(2)}`} unit="$" positive />
          <MetricCard title="平均亏损" value={metrics.avgLoss.toFixed(2)} unit="$" negative />
        </div>

        {/* 权益曲线 */}
        <div style={s.chartCard}>
          <div style={{ ...s.cardTitle, marginBottom: '16px' }}>权益曲线</div>
          <EquityChart equity={result.equityCurve} trades={result.trades} height={320} />
        </div>

        {/* 回测信息 */}
        <div style={{ fontSize: '11px', color: 'var(--text-tertiary)', fontFamily: 'monospace', padding: '0 4px' }}>
          运行时间: {result.runtime.toFixed(2)}ms | 回测周期: {new Date(result.config.startDate).toLocaleDateString('zh-CN')} - {new Date(result.config.endDate).toLocaleDateString('zh-CN')} | 初始资金: ${result.config.initialCapital.toLocaleString()}
        </div>
      </div>
    );
  };

  const renderTradesTab = () => {
    if (trades.length === 0) {
      return (
        <div style={s.emptyState}>
          <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" opacity="0.3">
            <path d="M12 2v20M17 5H9.5a3.5 3.5 0 000 7h5a3.5 3.5 0 010 7H6" />
          </svg>
          <div style={{ fontSize: '14px', fontWeight: 600 }}>暂无交易记录</div>
        </div>
      );
    }

    return (
      <div style={s.section}>
        <TradeTable trades={trades} onSelect={setSelectedTrade} maxRows={50} />
      </div>
    );
  };

  const renderSettingsTab = () => (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      <div style={s.section}>
        <div style={s.sectionTitle}>策略设置</div>
        <div style={s.formGrid}>
          <div style={s.formGroup}>
            <label style={s.label}>策略</label>
            <select
              style={s.select}
              value={config.strategy}
              onChange={(e) => setConfig({ strategy: e.target.value as any })}
            >
              <option value="ma_cross">均线交叉 (MA Cross)</option>
              <option value="rsi">RSI 超买超卖</option>
              <option value="bollinger">布林带策略</option>
              <option value="macd">MACD 策略</option>
              <option value="combo">组合策略</option>
              <option value="turtle">海龟交易法 (Turtle)</option>
            </select>
          </div>
          <div style={s.formGroup}>
            <label style={s.label}>止损</label>
            <select style={s.select} defaultValue="0.1">
              <option value={0.05}>5%</option>
              <option value={0.1}>10%</option>
              <option value={0.15}>15%</option>
              <option value={0.2}>20%</option>
            </select>
          </div>
          <div style={s.formGroup}>
            <label style={s.label}>止盈</label>
            <select style={s.select} defaultValue="0.05">
              <option value={0.03}>3%</option>
              <option value={0.05}>5%</option>
              <option value={0.1}>10%</option>
              <option value={0.15}>15%</option>
            </select>
          </div>
          <div style={s.formGroup}>
            <label style={s.label}>最大持仓</label>
            <select style={s.select} defaultValue="1">
              <option value={1}>1</option>
              <option value={2}>2</option>
              <option value={3}>3</option>
              <option value={5}>5</option>
            </select>
          </div>
        </div>
      </div>

      <div style={s.section}>
        <div style={s.sectionTitle}>高级选项</div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          <label style={{ display: 'flex', alignItems: 'center', gap: '10px', fontSize: '13px', color: 'var(--text-secondary)', cursor: 'pointer' }}>
            <input type="checkbox" defaultChecked style={{ width: '16px', height: '16px', accentColor: '#8b5cf6' }} />
            使用追踪止损
          </label>
          <label style={{ display: 'flex', alignItems: 'center', gap: '10px', fontSize: '13px', color: 'var(--text-secondary)', cursor: 'pointer' }}>
            <input type="checkbox" defaultChecked style={{ width: '16px', height: '16px', accentColor: '#8b5cf6' }} />
            使用出场信号
          </label>
          <label style={{ display: 'flex', alignItems: 'center', gap: '10px', fontSize: '13px', color: 'var(--text-secondary)', cursor: 'pointer' }}>
            <input type="checkbox" style={{ width: '16px', height: '16px', accentColor: '#8b5cf6' }} />
            允许做空
          </label>
        </div>
      </div>
    </div>
  );

  // ============================================
  // 渲染
  // ============================================

  return (
    <div style={s.container}>
      {/* Header */}
      <div style={s.header}>
        <div style={s.title}>回测引擎</div>
        <div style={s.headerActions}>
          <StatusBadge status={status} />
          {(status === 'completed' || status === 'error') && (
            <button style={{ ...s.button, ...s.buttonDanger }} onClick={handleReset}>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M3 12a9 9 0 109-9 9.75 9.75 0 00-6.74 2.74L3 8" />
                <path d="M3 3v5h5" />
              </svg>
              重置
            </button>
          )}
        </div>
      </div>

      {/* Tab Bar */}
      <div style={s.tabBar}>
        {TABS.map((tab) => (
          <button
            key={tab.id}
            style={{
              ...s.tab,
              ...(activeTab === tab.id ? s.tabActive : {}),
            }}
            onClick={() => setActiveTab(tab.id)}
          >
            {tab.label}
            {tab.id === 'trades' && result && (
              <span
                style={{
                  marginLeft: '6px',
                  padding: '1px 6px',
                  borderRadius: '10px',
                  fontSize: '10px',
                  background: 'rgba(255,255,255,0.1)',
                }}
              >
                {result.trades.length}
              </span>
            )}
          </button>
        ))}
      </div>

      {/* 进度条 */}
      {(status === 'running' || status === 'loading') && (
        <div style={s.progressSection}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px', fontSize: '12px', color: 'var(--text-secondary)' }}>
            <span>{status === 'loading' ? '加载数据...' : '回测运行中...'}</span>
            <span>{progress.completedTrades} / {progress.totalBars} 步</span>
          </div>
          <ProgressBar progress={progress.progress} />
        </div>
      )}

      {/* Error */}
      {error && <div style={s.errorBox}>{error}</div>}

      {/* Tab Content */}
      {activeTab === 'config' && renderConfigTab()}
      {activeTab === 'results' && renderResultsTab()}
      {activeTab === 'trades' && renderTradesTab()}
      {activeTab === 'settings' && renderSettingsTab()}
    </div>
  );
}

export default BacktestView;
