/**
 * NEMT 市场数据面板组件
 * 显示实时市场数据和K线图表
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  MarketData,
  TickerData,
  marketService,
  getMarketService
} from '../services/marketService';

interface MarketPanelProps {
  defaultSymbol?: string;
}

export const MarketPanel: React.FC<MarketPanelProps> = ({
  defaultSymbol = 'BTCUSDT'
}) => {
  const [symbols] = useState<string[]>([
    'BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT', 'XRPUSDT'
  ]);
  const [selectedSymbol, setSelectedSymbol] = useState(defaultSymbol);
  const [tickers, setTickers] = useState<TickerData[]>([]);
  const [currentTicker, setCurrentTicker] = useState<TickerData | null>(null);
  const [priceChange, setPriceChange] = useState<'up' | 'down' | 'neutral'>('neutral');

  // 初始化并订阅市场数据
  useEffect(() => {
    const service = getMarketService();
    
    // 获取初始行情
    setTickers(service.getAllTickers());
    setCurrentTicker(service.getTicker(selectedSymbol));

    // 订阅实时数据
    const unsubscribe = service.subscribe(selectedSymbol, (data: MarketData) => {
      setCurrentTicker({
        symbol: data.symbol,
        price: data.price,
        change_24h: data.change_24h,
        change_pct_24h: data.change_pct_24h,
        high_24h: data.high_24h,
        low_24h: data.low_24h,
        volume_24h: data.volume
      });
      
      // 检测价格变化方向
      setPriceChange(prev => {
        if (data.price > prev) return 'up';
        if (data.price < prev) return 'down';
        return 'neutral';
      });
    });

    // 启动服务
    service.start();

    return () => {
      unsubscribe();
    };
  }, [selectedSymbol]);

  // 格式化价格
  const formatPrice = (price: number, decimals: number = 2): string => {
    if (price >= 1000) {
      return price.toLocaleString('en-US', {
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals
      });
    } else if (price >= 1) {
      return price.toFixed(decimals);
    } else {
      return price.toFixed(4);
    }
  };

  // 格式化百分比
  const formatPercent = (percent: number): string => {
    const sign = percent >= 0 ? '+' : '';
    return `${sign}${percent.toFixed(2)}%`;
  };

  // 获取颜色
  const getPriceColor = (ticker: TickerData): string => {
    if (ticker.change_pct_24h > 0) return '#52c41a';
    if (ticker.change_pct_24h < 0) return '#ff4d4f';
    return '#666';
  };

  return (
    <div style={{
      background: 'white',
      borderRadius: '12px',
      padding: '20px',
      boxShadow: '0 2px 8px rgba(0,0,0,0.06)'
    }}>
      {/* 标题 */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        marginBottom: '16px'
      }}>
        <h3 style={{
          margin: 0,
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          fontSize: '16px',
          fontWeight: 600
        }}>
          <span style={{ fontSize: '20px' }}>📊</span>
          市场数据
        </h3>
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '6px',
          padding: '4px 12px',
          background: '#f5f5f5',
          borderRadius: '12px',
          fontSize: '12px',
          color: '#52c41a'
        }}>
          <span style={{
            width: '8px',
            height: '8px',
            borderRadius: '50%',
            background: '#52c41a',
            animation: 'pulse 2s infinite'
          }} />
          Live
        </div>
      </div>

      {/* 币种选择器 */}
      <div style={{
        display: 'flex',
        gap: '8px',
        marginBottom: '16px',
        flexWrap: 'wrap'
      }}>
        {symbols.map(symbol => (
          <button
            key={symbol}
            onClick={() => setSelectedSymbol(symbol)}
            style={{
              padding: '6px 12px',
              border: '1px solid',
              borderColor: selectedSymbol === symbol ? '#1890ff' : '#d9d9d9',
              borderRadius: '6px',
              background: selectedSymbol === symbol ? '#e6f7ff' : 'white',
              color: selectedSymbol === symbol ? '#1890ff' : '#666',
              cursor: 'pointer',
              fontSize: '13px',
              fontWeight: selectedSymbol === symbol ? 600 : 400,
              transition: 'all 0.2s'
            }}
          >
            {symbol.replace('USDT', '')}
          </button>
        ))}
      </div>

      {/* 当前价格显示 */}
      {currentTicker && (
        <div style={{
          background: '#fafafa',
          borderRadius: '8px',
          padding: '16px',
          marginBottom: '16px'
        }}>
          <div style={{
            display: 'flex',
            alignItems: 'baseline',
            gap: '12px',
            marginBottom: '8px'
          }}>
            <span style={{
              fontSize: '32px',
              fontWeight: 700,
              color: getPriceColor(currentTicker),
              transition: 'color 0.3s'
            }}>
              ${formatPrice(currentTicker.price)}
            </span>
            <span style={{
              padding: '4px 8px',
              borderRadius: '4px',
              background: getPriceColor(currentTicker) + '20',
              color: getPriceColor(currentTicker),
              fontSize: '14px',
              fontWeight: 600
            }}>
              {formatPercent(currentTicker.change_pct_24h)}
            </span>
          </div>
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(2, 1fr)',
            gap: '8px',
            fontSize: '13px',
            color: '#666'
          }}>
            <div>
              <span style={{ color: '#999' }}>24h 涨跌: </span>
              <span style={{ color: getPriceColor(currentTicker) }}>
                {currentTicker.change_24h >= 0 ? '+' : ''}
                ${formatPrice(Math.abs(currentTicker.change_24h))}
              </span>
            </div>
            <div>
              <span style={{ color: '#999' }}>24h 成交量: </span>
              <span>
                {(currentTicker.volume_24h / 1000000).toFixed(2)}M
              </span>
            </div>
            <div>
              <span style={{ color: '#999' }}>24h 最高: </span>
              <span style={{ color: '#52c41a' }}>
                ${formatPrice(currentTicker.high_24h)}
              </span>
            </div>
            <div>
              <span style={{ color: '#999' }}>24h 最低: </span>
              <span style={{ color: '#ff4d4f' }}>
                ${formatPrice(currentTicker.low_24h)}
              </span>
            </div>
          </div>
        </div>
      )}

      {/* 其他币种行情列表 */}
      <div>
        <h4 style={{
          margin: '0 0 12px',
          fontSize: '14px',
          fontWeight: 500,
          color: '#666'
        }}>
          其他币种
        </h4>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          {tickers
            .filter(t => t.symbol !== selectedSymbol)
            .slice(0, 4)
            .map(ticker => (
              <div
                key={ticker.symbol}
                onClick={() => setSelectedSymbol(ticker.symbol)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  padding: '10px 12px',
                  background: '#fafafa',
                  borderRadius: '6px',
                  cursor: 'pointer',
                  transition: 'background 0.2s'
                }}
                onMouseEnter={(e) => e.currentTarget.style.background = '#f0f0f0'}
                onMouseLeave={(e) => e.currentTarget.style.background = '#fafafa'}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span style={{ fontWeight: 600, fontSize: '14px' }}>
                    {ticker.symbol.replace('USDT', '')}
                  </span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                  <span style={{ fontWeight: 500 }}>
                    ${formatPrice(ticker.price)}
                  </span>
                  <span style={{
                    color: getPriceColor(ticker),
                    fontSize: '13px',
                    fontWeight: 500,
                    minWidth: '60px',
                    textAlign: 'right'
                  }}>
                    {formatPercent(ticker.change_pct_24h)}
                  </span>
                </div>
              </div>
            ))}
        </div>
      </div>

      {/* CSS 动画 */}
      <style>{`
        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.5; }
        }
      `}</style>
    </div>
  );
};

export default MarketPanel;
