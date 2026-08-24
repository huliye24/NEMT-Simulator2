/**
 * Copyright 2026 NEMT Lab
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 */

import React, { useEffect, useState } from 'react';
import { TrendingUp, TrendingDown, Wifi, WifiOff, RefreshCw, Clock } from 'lucide-react';
import {
  useBinanceState,
  useBinancePrices,
  useBinanceConnected,
  usePlatformStore,
  MarketData
} from './store';
import { binanceService, BinanceTicker } from './binanceService';

interface MarketViewProps {
  className?: string;
}

const SYMBOLS = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT', 'ADAUSDT'];
const INTERVALS = ['1m', '5m', '15m', '1h', '4h', '1d'];

export const MarketView: React.FC<MarketViewProps> = ({ className }) => {
  const binanceState = useBinanceState();
  const prices = useBinancePrices();
  const isConnected = useBinanceConnected();
  const { connectBinance, disconnectBinance, setSelectedSymbol, setSelectedInterval } = usePlatformStore();

  const [loading, setLoading] = useState(false);

  // 自动连接
  useEffect(() => {
    if (!isConnected && !binanceState.connecting) {
      handleConnect();
    }
  }, []);

  const handleConnect = async () => {
    setLoading(true);
    try {
      await connectBinance([binanceState.selectedSymbol], binanceState.selectedInterval);
    } catch (error) {
      console.error('Failed to connect:', error);
    }
    setLoading(false);
  };

  const handleDisconnect = () => {
    disconnectBinance();
  };

  const handleRefresh = async () => {
    setLoading(true);
    try {
      const ticker = await binanceService.get24hrTicker(binanceState.selectedSymbol);
      console.log('Ticker data:', ticker);
    } catch (error) {
      console.error('Failed to refresh:', error);
    }
    setLoading(false);
  };

  const formatPrice = (price: number | undefined): string => {
    if (price === undefined) return '--';
    return price >= 1000 ? price.toFixed(2) : price.toFixed(6);
  };

  const formatVolume = (volume: number | undefined): string => {
    if (volume === undefined) return '--';
    if (volume >= 1e9) return (volume / 1e9).toFixed(2) + 'B';
    if (volume >= 1e6) return (volume / 1e6).toFixed(2) + 'M';
    if (volume >= 1e3) return (volume / 1e3).toFixed(2) + 'K';
    return volume.toFixed(2);
  };

  const currentPrice = prices[binanceState.selectedSymbol];

  return (
    <div className={className} style={{
      padding: '20px',
      height: '100%',
      overflow: 'auto',
      background: '#0a0f1a'
    }}>
      {/* 连接状态栏 */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        marginBottom: '20px',
        padding: '12px 16px',
        background: isConnected ? 'rgba(16, 185, 129, 0.1)' : 'rgba(239, 68, 68, 0.1)',
        borderRadius: '12px',
        border: `1px solid ${isConnected ? '#10b98133' : '#ef444433'}`
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          {isConnected ? (
            <Wifi size={20} color="#10b981" />
          ) : (
            <WifiOff size={20} color="#ef4444" />
          )}
          <span style={{
            color: isConnected ? '#10b981' : '#ef4444',
            fontWeight: 500
          }}>
            {isConnected ? '已连接 Binance' : '未连接'}
          </span>
          {binanceState.lastUpdate && (
            <span style={{ color: '#64748b', fontSize: '12px', display: 'flex', alignItems: 'center', gap: '4px' }}>
              <Clock size={12} />
              {new Date(binanceState.lastUpdate).toLocaleTimeString()}
            </span>
          )}
        </div>

        <div style={{ display: 'flex', gap: '8px' }}>
          <button
            onClick={handleRefresh}
            disabled={loading || !isConnected}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              padding: '8px 12px',
              background: '#1e293b',
              border: '1px solid #334155',
              borderRadius: '8px',
              color: '#e2e8f0',
              cursor: loading ? 'not-allowed' : 'pointer',
              opacity: loading ? 0.5 : 1
            }}
          >
            <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
            刷新
          </button>

          {isConnected ? (
            <button
              onClick={handleDisconnect}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                padding: '8px 12px',
                background: 'rgba(239, 68, 68, 0.1)',
                border: '1px solid #ef4444',
                borderRadius: '8px',
                color: '#ef4444',
                cursor: 'pointer'
              }}
            >
              <WifiOff size={14} />
              断开
            </button>
          ) : (
            <button
              onClick={handleConnect}
              disabled={loading}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                padding: '8px 12px',
                background: '#10b981',
                border: 'none',
                borderRadius: '8px',
                color: '#fff',
                cursor: loading ? 'not-allowed' : 'pointer',
                opacity: loading ? 0.7 : 1
              }}
            >
              <Wifi size={14} />
              连接
            </button>
          )}
        </div>
      </div>

      {/* 交易对选择 */}
      <div style={{ marginBottom: '20px' }}>
        <h3 style={{ margin: '0 0 12px', color: '#e2e8f0', fontSize: '14px' }}>交易对</h3>
        <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
          {SYMBOLS.map(symbol => (
            <button
              key={symbol}
              onClick={() => setSelectedSymbol(symbol)}
              style={{
                padding: '8px 16px',
                background: binanceState.selectedSymbol === symbol ? '#3b82f6' : '#1e293b',
                border: `1px solid ${binanceState.selectedSymbol === symbol ? '#3b82f6' : '#334155'}`,
                borderRadius: '8px',
                color: '#e2e8f0',
                cursor: 'pointer',
                fontWeight: binanceState.selectedSymbol === symbol ? 500 : 400
              }}
            >
              {symbol.replace('USDT', '')}
            </button>
          ))}
        </div>
      </div>

      {/* K线周期选择 */}
      <div style={{ marginBottom: '20px' }}>
        <h3 style={{ margin: '0 0 12px', color: '#e2e8f0', fontSize: '14px' }}>时间周期</h3>
        <div style={{ display: 'flex', gap: '8px' }}>
          {INTERVALS.map(interval => (
            <button
              key={interval}
              onClick={() => setSelectedInterval(interval)}
              style={{
                padding: '6px 12px',
                background: binanceState.selectedInterval === interval ? '#8b5cf6' : '#1e293b',
                border: `1px solid ${binanceState.selectedInterval === interval ? '#8b5cf6' : '#334155'}`,
                borderRadius: '6px',
                color: '#e2e8f0',
                cursor: 'pointer',
                fontSize: '12px'
              }}
            >
              {interval}
            </button>
          ))}
        </div>
      </div>

      {/* 当前价格卡片 */}
      {currentPrice && (
        <div style={{
          background: 'linear-gradient(135deg, #1e293b 0%, #0f172a 100%)',
          borderRadius: '16px',
          padding: '24px',
          marginBottom: '20px',
          border: '1px solid #334155'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
            <div>
              <span style={{ color: '#64748b', fontSize: '14px' }}>{currentPrice.symbol}</span>
            </div>
            <span style={{
              padding: '4px 8px',
              borderRadius: '4px',
              fontSize: '12px',
              background: currentPrice.changePercent24h >= 0 ? 'rgba(16, 185, 129, 0.2)' : 'rgba(239, 68, 68, 0.2)',
              color: currentPrice.changePercent24h >= 0 ? '#10b981' : '#ef4444'
            }}>
              {currentPrice.changePercent24h >= 0 ? '+' : ''}{currentPrice.changePercent24h.toFixed(2)}%
            </span>
          </div>

          <div style={{ fontSize: '32px', fontWeight: 700, color: '#e2e8f0', marginBottom: '8px' }}>
            ${formatPrice(currentPrice.price)}
          </div>

          <div style={{ display: 'flex', gap: '24px', color: '#64748b', fontSize: '13px' }}>
            <div>
              <span>24h 涨跌: </span>
              <span style={{ color: currentPrice.change24h >= 0 ? '#10b981' : '#ef4444' }}>
                {currentPrice.change24h >= 0 ? '+' : ''}{formatPrice(currentPrice.change24h)}
              </span>
            </div>
            <div>
              <span>24h 高: </span>
              <span style={{ color: '#10b981' }}>{formatPrice(currentPrice.high24h)}</span>
            </div>
            <div>
              <span>24h 低: </span>
              <span style={{ color: '#ef4444' }}>{formatPrice(currentPrice.low24h)}</span>
            </div>
          </div>

          <div style={{ marginTop: '12px', color: '#64748b', fontSize: '13px' }}>
            <span>24h 成交量: </span>
            <span style={{ color: '#e2e8f0' }}>${formatVolume(currentPrice.volume24h)}</span>
          </div>
        </div>
      )}

      {/* 价格列表 */}
      <div>
        <h3 style={{ margin: '0 0 12px', color: '#e2e8f0', fontSize: '14px' }}>实时价格</h3>
        <div style={{
          background: '#1e293b',
          borderRadius: '12px',
          overflow: 'hidden',
          border: '1px solid #334155'
        }}>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ background: '#0f172a' }}>
                <th style={{ padding: '12px 16px', textAlign: 'left', color: '#64748b', fontSize: '12px', fontWeight: 500 }}>交易对</th>
                <th style={{ padding: '12px 16px', textAlign: 'right', color: '#64748b', fontSize: '12px', fontWeight: 500 }}>价格</th>
                <th style={{ padding: '12px 16px', textAlign: 'right', color: '#64748b', fontSize: '12px', fontWeight: 500 }}>24h 涨跌</th>
                <th style={{ padding: '12px 16px', textAlign: 'right', color: '#64748b', fontSize: '12px', fontWeight: 500 }}>成交量</th>
              </tr>
            </thead>
            <tbody>
              {SYMBOLS.map(symbol => {
                const data = prices[symbol];
                return (
                  <tr
                    key={symbol}
                    onClick={() => setSelectedSymbol(symbol)}
                    style={{
                      cursor: 'pointer',
                      borderTop: '1px solid #334155'
                    }}
                  >
                    <td style={{ padding: '12px 16px', color: '#e2e8f0', fontWeight: 500 }}>
                      {symbol.replace('USDT', '')}
                    </td>
                    <td style={{ padding: '12px 16px', textAlign: 'right', color: '#e2e8f0' }}>
                      {data ? `$${formatPrice(data.price)}` : '--'}
                    </td>
                    <td style={{
                      padding: '12px 16px',
                      textAlign: 'right',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'flex-end',
                      gap: '4px',
                      color: data?.changePercent24h >= 0 ? '#10b981' : '#ef4444'
                    }}>
                      {data?.changePercent24h >= 0 ? <TrendingUp size={14} /> : <TrendingDown size={14} />}
                      {data ? `${data.changePercent24h >= 0 ? '+' : ''}${data.changePercent24h.toFixed(2)}%` : '--'}
                    </td>
                    <td style={{ padding: '12px 16px', textAlign: 'right', color: '#64748b' }}>
                      {data ? `$${formatVolume(data.volume24h)}` : '--'}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* 错误提示 */}
      {binanceState.error && (
        <div style={{
          marginTop: '16px',
          padding: '12px 16px',
          background: 'rgba(239, 68, 68, 0.1)',
          border: '1px solid #ef4444',
          borderRadius: '8px',
          color: '#ef4444',
          fontSize: '13px'
        }}>
          错误: {binanceState.error}
        </div>
      )}
    </div>
  );
};

export default MarketView;
