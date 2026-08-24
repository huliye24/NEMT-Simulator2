/**
 * Copyright 2026 NEMT Lab
 *
 * 数据可视化组件 - Canvas 渲染的高性能图表
 *
 * 特性：
 * - K线图 / 折线图 / 柱状图
 * - Canvas 渲染，高性能
 * - 缩放/平移交互
 * - 十字光标
 * - 实时数据流
 */

import React, { useRef, useEffect, useState, useCallback } from 'react';

// ============================================
// 类型定义
// ============================================

export interface CandlestickData {
  time: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume?: number;
}

export interface LineData {
  time: number;
  value: number;
}

export interface ChartConfig {
  width: number;
  height: number;
  background?: string;
  gridColor?: string;
  upColor?: string;
  downColor?: string;
  textColor?: string;
  crosshairColor?: string;
  showVolume?: boolean;
  showMA?: number[];
}

export interface ChartData {
  candles?: CandlestickData[];
  lines?: Array<{ name: string; data: LineData[]; color: string }>;
  volume?: LineData[];
}

// ============================================
// 颜色工具
// ============================================

const hexToRgb = (hex: string) => {
  const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
  return result ? {
    r: parseInt(result[1], 16),
    g: parseInt(result[2], 16),
    b: parseInt(result[3], 16)
  } : null;
};

const withAlpha = (hex: string, alpha: number) => {
  const rgb = hexToRgb(hex);
  if (!rgb) return hex;
  return `rgba(${rgb.r}, ${rgb.g}, ${rgb.b}, ${alpha})`;
};

// ============================================
// K线图组件
// ============================================

export const CandlestickChart: React.FC<{
  data: CandlestickData[];
  config?: Partial<ChartConfig>;
}> = ({ data, config = {} }) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [dimensions, setDimensions] = useState({ width: 800, height: 400 });
  const [mousePos, setMousePos] = useState<{ x: number; y: number } | null>(null);
  const [viewport, setViewport] = useState({ offset: 0, scale: 1 });

  const defaultConfig: ChartConfig = {
    width: dimensions.width,
    height: dimensions.height,
    background: '#0f172a',
    gridColor: '#1e293b',
    upColor: '#10b981',
    downColor: '#ef4444',
    textColor: '#94a3b8',
    crosshairColor: '#8b5cf6',
    showVolume: true,
    showMA: [5, 10, 20],
    ...config
  };

  // 计算价格范围
  const calculatePriceRange = useCallback(() => {
    if (data.length === 0) return { min: 0, max: 100 };

    const visibleData = data.slice(-Math.floor(100 * viewport.scale));
    let min = Infinity;
    let max = -Infinity;

    for (const candle of visibleData) {
      min = Math.min(min, candle.low);
      max = Math.max(max, candle.high);
    }

    const padding = (max - min) * 0.1;
    return { min: min - padding, max: max + padding };
  }, [data, viewport.scale]);

  // 绘制图表
  const draw = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const { width, height } = dimensions;
    const {
      background = '#0f172a',
      gridColor = '#1e293b',
      upColor = '#10b981',
      downColor = '#ef4444',
      textColor = '#94a3b8',
      crosshairColor = '#8b5cf6'
    } = defaultConfig;

    // 清空画布
    ctx.fillStyle = background;
    ctx.fillRect(0, 0, width, height);

    if (data.length === 0) {
      ctx.fillStyle = textColor;
      ctx.font = '14px sans-serif';
      ctx.textAlign = 'center';
      ctx.fillText('暂无数据', width / 2, height / 2);
      return;
    }

    const priceRange = calculatePriceRange();
    const chartHeight = defaultConfig.showVolume ? height * 0.75 : height;
    const volumeHeight = defaultConfig.showVolume ? height * 0.2 : 0;
    const padding = { top: 20, right: 60, bottom: volumeHeight > 0 ? 30 : 20, left: 10 };

    const chartWidth = width - padding.left - padding.right;
    const visibleCount = Math.floor(50 * viewport.scale);
    const candleWidth = chartWidth / visibleCount;

    // 绘制网格
    ctx.strokeStyle = gridColor;
    ctx.lineWidth = 1;
    for (let i = 0; i <= 4; i++) {
      const y = padding.top + (chartHeight - padding.top - padding.bottom) * (i / 4);
      ctx.beginPath();
      ctx.moveTo(padding.left, y);
      ctx.lineTo(width - padding.right, y);
      ctx.stroke();

      // 价格标签
      const price = priceRange.max - (priceRange.max - priceRange.min) * (i / 4);
      ctx.fillStyle = textColor;
      ctx.font = '10px monospace';
      ctx.textAlign = 'left';
      ctx.fillText(price.toFixed(2), width - padding.right + 5, y + 4);
    }

    // 绘制 K 线
    const visibleData = data.slice(-visibleCount);
    const maxVolume = Math.max(...(visibleData.map(c => c.volume || 0)));

    visibleData.forEach((candle, i) => {
      const x = padding.left + i * candleWidth;
      const isUp = candle.close >= candle.open;
      const color = isUp ? upColor : downColor;

      // 烛身
      const openY = padding.top + (1 - (candle.open - priceRange.min) / (priceRange.max - priceRange.min)) * (chartHeight - padding.top - padding.bottom);
      const closeY = padding.top + (1 - (candle.close - priceRange.min) / (priceRange.max - priceRange.min)) * (chartHeight - padding.top - padding.bottom);
      const highY = padding.top + (1 - (candle.high - priceRange.min) / (priceRange.max - priceRange.min)) * (chartHeight - padding.top - padding.bottom);
      const lowY = padding.top + (1 - (candle.low - priceRange.min) / (priceRange.max - priceRange.min)) * (chartHeight - padding.top - padding.bottom);

      // 影线
      ctx.strokeStyle = color;
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.moveTo(x + candleWidth / 2, highY);
      ctx.lineTo(x + candleWidth / 2, lowY);
      ctx.stroke();

      // 烛身
      const bodyTop = Math.min(openY, closeY);
      const bodyHeight = Math.max(1, Math.abs(openY - closeY));
      ctx.fillStyle = color;
      ctx.fillRect(x + candleWidth * 0.1, bodyTop, candleWidth * 0.8, bodyHeight);

      // 成交量
      if (defaultConfig.showVolume && candle.volume) {
        const volumeBarHeight = (candle.volume / maxVolume) * volumeHeight * 0.8;
        const volumeY = height - padding.bottom - volumeBarHeight;
        ctx.fillStyle = withAlpha(color, 0.5);
        ctx.fillRect(x + candleWidth * 0.2, volumeY, candleWidth * 0.6, volumeBarHeight);
      }
    });

    // 绘制十字光标
    if (mousePos) {
      ctx.strokeStyle = crosshairColor;
      ctx.setLineDash([5, 5]);
      ctx.lineWidth = 1;

      // 水平线
      ctx.beginPath();
      ctx.moveTo(padding.left, mousePos.y);
      ctx.lineTo(width - padding.right, mousePos.y);
      ctx.stroke();

      // 垂直线
      ctx.beginPath();
      ctx.moveTo(mousePos.x, padding.top);
      ctx.lineTo(mousePos.x, chartHeight);
      ctx.stroke();

      ctx.setLineDash([]);

      // 价格标签
      const hoverPrice = priceRange.max - (mousePos.y - padding.top) / (chartHeight - padding.top - padding.bottom) * (priceRange.max - priceRange.min);
      ctx.fillStyle = crosshairColor;
      ctx.fillRect(width - padding.right, mousePos.y - 10, 55, 20);
      ctx.fillStyle = '#fff';
      ctx.font = '10px monospace';
      ctx.textAlign = 'left';
      ctx.fillText(hoverPrice.toFixed(2), width - padding.right + 3, mousePos.y + 4);
    }

  }, [data, dimensions, defaultConfig, calculatePriceRange, viewport, mousePos]);

  // 响应尺寸变化
  useEffect(() => {
    const observer = new ResizeObserver((entries) => {
      for (const entry of entries) {
        setDimensions({
          width: entry.contentRect.width,
          height: entry.contentRect.height
        });
      }
    });

    if (canvasRef.current?.parentElement) {
      observer.observe(canvasRef.current.parentElement);
    }

    return () => observer.disconnect();
  }, []);

  // 绘制
  useEffect(() => {
    draw();
  }, [draw]);

  // 鼠标事件
  const handleMouseMove = (e: React.MouseEvent) => {
    const rect = canvasRef.current?.getBoundingClientRect();
    if (rect) {
      setMousePos({
        x: e.clientX - rect.left,
        y: e.clientY - rect.top
      });
    }
  };

  const handleMouseLeave = () => {
    setMousePos(null);
  };

  return (
    <div style={{ width: '100%', height: '100%', position: 'relative' }}>
      <canvas
        ref={canvasRef}
        width={dimensions.width}
        height={dimensions.height}
        onMouseMove={handleMouseMove}
        onMouseLeave={handleMouseLeave}
        style={{ display: 'block', cursor: 'crosshair' }}
      />

      {/* 缩放控制 */}
      <div style={{
        position: 'absolute',
        top: '10px',
        right: '10px',
        display: 'flex',
        flexDirection: 'column',
        gap: '4px'
      }}>
        <button
          onClick={() => setViewport(v => ({ ...v, scale: Math.min(v.scale * 1.2, 3) }))}
          style={{
            width: '28px',
            height: '28px',
            borderRadius: '4px',
            border: '1px solid #334155',
            background: '#1e293b',
            color: '#e2e8f0',
            cursor: 'pointer',
            fontSize: '16px'
          }}
        >
          +
        </button>
        <button
          onClick={() => setViewport(v => ({ ...v, scale: Math.max(v.scale / 1.2, 0.3) }))}
          style={{
            width: '28px',
            height: '28px',
            borderRadius: '4px',
            border: '1px solid #334155',
            background: '#1e293b',
            color: '#e2e8f0',
            cursor: 'pointer',
            fontSize: '16px'
          }}
        >
          -
        </button>
      </div>
    </div>
  );
};

// ============================================
// 折线图组件
// ============================================

export const LineChart: React.FC<{
  data: LineData[];
  config?: Partial<ChartConfig & { lineColor?: string; fill?: boolean }>;
}> = ({ data, config = {} }) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [dimensions, setDimensions] = useState({ width: 400, height: 200 });

  const defaultConfig = {
    width: dimensions.width,
    height: dimensions.height,
    background: '#0f172a',
    gridColor: '#1e293b',
    lineColor: '#8b5cf6',
    textColor: '#94a3b8',
    fill: true,
    ...config
  };

  useEffect(() => {
    const observer = new ResizeObserver((entries) => {
      for (const entry of entries) {
        setDimensions({
          width: entry.contentRect.width,
          height: entry.contentRect.height
        });
      }
    });

    if (canvasRef.current?.parentElement) {
      observer.observe(canvasRef.current.parentElement);
    }

    return () => observer.disconnect();
  }, []);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const { width, height } = dimensions;
    const { background, gridColor, lineColor, textColor, fill } = defaultConfig;

    ctx.fillStyle = background;
    ctx.fillRect(0, 0, width, height);

    if (data.length === 0) {
      ctx.fillStyle = textColor;
      ctx.font = '14px sans-serif';
      ctx.textAlign = 'center';
      ctx.fillText('暂无数据', width / 2, height / 2);
      return;
    }

    const padding = { top: 20, right: 20, bottom: 30, left: 10 };
    const chartWidth = width - padding.left - padding.right;
    const chartHeight = height - padding.top - padding.bottom;

    // 计算范围
    const values = data.map(d => d.value);
    let min = Math.min(...values);
    let max = Math.max(...values);
    const padding2 = (max - min) * 0.1 || 1;
    min -= padding2;
    max += padding2;

    // 绘制网格
    ctx.strokeStyle = gridColor;
    ctx.lineWidth = 1;
    for (let i = 0; i <= 4; i++) {
      const y = padding.top + chartHeight * (i / 4);
      ctx.beginPath();
      ctx.moveTo(padding.left, y);
      ctx.lineTo(width - padding.right, y);
      ctx.stroke();

      const value = max - (max - min) * (i / 4);
      ctx.fillStyle = textColor;
      ctx.font = '10px monospace';
      ctx.textAlign = 'left';
      ctx.fillText(value.toFixed(1), width - padding.right + 5, y + 4);
    }

    // 绘制线
    const stepX = chartWidth / (data.length - 1 || 1);

    // 填充
    if (fill) {
      ctx.beginPath();
      ctx.moveTo(padding.left, height - padding.bottom);
      data.forEach((point, i) => {
        const x = padding.left + i * stepX;
        const y = padding.top + (1 - (point.value - min) / (max - min)) * chartHeight;
        ctx.lineTo(x, y);
      });
      ctx.lineTo(padding.left + (data.length - 1) * stepX, height - padding.bottom);
      ctx.closePath();

      const gradient = ctx.createLinearGradient(0, padding.top, 0, height - padding.bottom);
      gradient.addColorStop(0, withAlpha(lineColor, 0.3));
      gradient.addColorStop(1, withAlpha(lineColor, 0));
      ctx.fillStyle = gradient;
      ctx.fill();
    }

    // 线条
    ctx.strokeStyle = lineColor;
    ctx.lineWidth = 2;
    ctx.beginPath();
    data.forEach((point, i) => {
      const x = padding.left + i * stepX;
      const y = padding.top + (1 - (point.value - min) / (max - min)) * chartHeight;
      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    });
    ctx.stroke();

    // 数据点
    data.forEach((point, i) => {
      const x = padding.left + i * stepX;
      const y = padding.top + (1 - (point.value - min) / (max - min)) * chartHeight;

      ctx.beginPath();
      ctx.arc(x, y, 3, 0, Math.PI * 2);
      ctx.fillStyle = lineColor;
      ctx.fill();
    });

  }, [data, dimensions, defaultConfig]);

  return (
    <canvas
      ref={canvasRef}
      width={dimensions.width}
      height={dimensions.height}
      style={{ display: 'block' }}
    />
  );
};

// ============================================
// 仪表盘组件
// ============================================

export const GaugeChart: React.FC<{
  value: number;
  min?: number;
  max?: number;
  label?: string;
  unit?: string;
  size?: number;
}> = ({
  value,
  min = 0,
  max = 100,
  label = '',
  unit = '%',
  size = 150
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const centerX = size / 2;
    const centerY = size / 2;
    const radius = size * 0.4;

    // 清空
    ctx.clearRect(0, 0, size, size);

    // 背景弧
    ctx.beginPath();
    ctx.arc(centerX, centerY, radius, Math.PI * 0.75, Math.PI * 2.25);
    ctx.strokeStyle = '#1e293b';
    ctx.lineWidth = size * 0.08;
    ctx.lineCap = 'round';
    ctx.stroke();

    // 进度弧
    const progress = Math.max(0, Math.min(1, (value - min) / (max - min)));
    const endAngle = Math.PI * 0.75 + progress * Math.PI * 1.5;

    const gradient = ctx.createLinearGradient(0, centerY - radius, 0, centerY + radius);
    gradient.addColorStop(0, '#ef4444');
    gradient.addColorStop(0.5, '#f59e0b');
    gradient.addColorStop(1, '#10b981');

    ctx.beginPath();
    ctx.arc(centerX, centerY, radius, Math.PI * 0.75, endAngle);
    ctx.strokeStyle = gradient;
    ctx.lineWidth = size * 0.08;
    ctx.lineCap = 'round';
    ctx.stroke();

    // 中心文字
    ctx.fillStyle = '#e2e8f0';
    ctx.font = `bold ${size * 0.15}px monospace`;
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(`${value.toFixed(1)}${unit}`, centerX, centerY);

    if (label) {
      ctx.fillStyle = '#64748b';
      ctx.font = `${size * 0.08}px sans-serif`;
      ctx.fillText(label, centerX, centerY + size * 0.12);
    }

  }, [value, min, max, label, unit, size]);

  return <canvas ref={canvasRef} width={size} height={size} />;
};

// ============================================
// 迷你图组件
// ============================================

export const Sparkline: React.FC<{
  data: number[];
  width?: number;
  height?: number;
  color?: string;
  showArea?: boolean;
}> = ({
  data,
  width = 80,
  height = 24,
  color = '#8b5cf6',
  showArea = true
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    ctx.clearRect(0, 0, width, height);

    if (data.length === 0) return;

    const min = Math.min(...data);
    const max = Math.max(...data);
    const range = max - min || 1;
    const stepX = width / (data.length - 1 || 1);

    if (showArea) {
      ctx.beginPath();
      ctx.moveTo(0, height);
      data.forEach((value, i) => {
        const x = i * stepX;
        const y = height - ((value - min) / range) * height * 0.9 - height * 0.05;
        ctx.lineTo(x, y);
      });
      ctx.lineTo(width, height);
      ctx.closePath();

      const gradient = ctx.createLinearGradient(0, 0, 0, height);
      gradient.addColorStop(0, withAlpha(color, 0.3));
      gradient.addColorStop(1, withAlpha(color, 0));
      ctx.fillStyle = gradient;
      ctx.fill();
    }

    ctx.strokeStyle = color;
    ctx.lineWidth = 1.5;
    ctx.beginPath();
    data.forEach((value, i) => {
      const x = i * stepX;
      const y = height - ((value - min) / range) * height * 0.9 - height * 0.05;
      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    });
    ctx.stroke();

  }, [data, width, height, color, showArea]);

  return <canvas ref={canvasRef} width={width} height={height} />;
};

// ============================================
// 工具函数
// ============================================

export function generateMockCandleData(count: number = 100): CandlestickData[] {
  const data: CandlestickData[] = [];
  let basePrice = 100;
  const now = Date.now();

  for (let i = 0; i < count; i++) {
    const volatility = 0.02;
    const change = (Math.random() - 0.5) * volatility * basePrice;

    const open = basePrice;
    const close = basePrice + change;
    const high = Math.max(open, close) + Math.random() * volatility * basePrice * 0.5;
    const low = Math.min(open, close) - Math.random() * volatility * basePrice * 0.5;
    const volume = Math.floor(Math.random() * 1000000);

    data.push({
      time: now - (count - i) * 60000, // 每分钟
      open,
      high,
      low,
      close,
      volume
    });

    basePrice = close;
  }

  return data;
}

export function generateMockLineData(count: number = 50): LineData[] {
  const data: LineData[] = [];
  let value = 50;
  const now = Date.now();

  for (let i = 0; i < count; i++) {
    value += (Math.random() - 0.5) * 5;
    value = Math.max(0, Math.min(100, value));

    data.push({
      time: now - (count - i) * 1000,
      value
    });
  }

  return data;
}
