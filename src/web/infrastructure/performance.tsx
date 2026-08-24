/**
 * Copyright 2026 NEMT Lab
 *
 * 性能监控 - Web Vitals + 自定义指标
 */

import React from 'react';

// ============================================
// 类型定义
// ============================================

export interface PerformanceMetrics {
  // Core Web Vitals
  FCP?: number;      // First Contentful Paint
  LCP?: number;      // Largest Contentful Paint
  FID?: number;      // First Input Delay
  CLS?: number;      // Cumulative Layout Shift
  TTFB?: number;     // Time to First Byte

  // 自定义指标
  FMP?: number;      // First Meaningful Paint
  TTI?: number;      // Time to Interactive
  TBT?: number;      // Total Blocking Time

  // 内存
  jsHeapSize?: number;
  usedJSHeapSize?: number;
  totalJSHeapSize?: number;

  // 网络
  resources: ResourceMetric[];
  apiCalls: ApiMetric[];

  // 渲染
  fps: number;
  frameTime: number;

  // 时间戳
  timestamp: number;
}

export interface ResourceMetric {
  name: string;
  type: string;
  duration: number;
  size: number;
  cached: boolean;
}

export interface ApiMetric {
  url: string;
  method: string;
  status: number;
  duration: number;
  timestamp: number;
  error?: string;
}

// ============================================
// 性能监控器
// ============================================

class PerformanceMonitor {
  private metrics: PerformanceMetrics[] = [];
  private maxMetrics = 100;
  private observers: PerformanceObserver[] = [];
  private apiInterceptor: ((event: ApiMetric) => void) | null = null;
  private lastFrameTime = 0;
  private frameCount = 0;
  private fps = 0;
  private rafId: number | null = null;

  constructor() {
    if (typeof window !== 'undefined') {
      this.init();
    }
  }

  /**
   * 初始化监控
   */
  private init(): void {
    // 观察布局偏移
    this.observeLayoutShift();

    // 观察长任务
    this.observeLongTasks();

    // 观察资源加载
    this.observeResources();

    // 观察首屏
    this.observePaint();

    // 观察首次输入
    this.observeFirstInput();

    // FPS 监控
    this.startFPSMonitor();

    // 内存监控 (如果有)
    this.monitorMemory();

    // 收集基础指标
    this.collectBaselineMetrics();
  }

  /**
   * 观察布局偏移
   */
  private observeLayoutShift(): void {
    if ('PerformanceObserver' in window) {
      try {
        const observer = new PerformanceObserver((list) => {
          for (const entry of list.getEntries()) {
            const metric = this.getCurrentMetrics();
            if (metric) {
              metric.CLS = (metric.CLS || 0) + (entry as any).value;
            }
          }
        });

        observer.observe({ type: 'layout-shift', buffered: true });
        this.observers.push(observer);
      } catch (e) {
        console.warn('CLS observation not supported');
      }
    }
  }

  /**
   * 观察长任务
   */
  private observeLongTasks(): void {
    if ('PerformanceObserver' in window) {
      try {
        const observer = new PerformanceObserver((list) => {
          for (const entry of list.getEntries()) {
            const metric = this.getCurrentMetrics();
            if (metric) {
              metric.TBT = (metric.TBT || 0) + (entry as any).duration - 50; // 50ms 阈值
            }
          }
        });

        observer.observe({ type: 'longtask', buffered: true });
        this.observers.push(observer);
      } catch (e) {
        console.warn('Long task observation not supported');
      }
    }
  }

  /**
   * 观察资源加载
   */
  private observeResources(): void {
    if ('PerformanceObserver' in window) {
      try {
        const observer = new PerformanceObserver((list) => {
          const metric = this.getCurrentMetrics();
          if (metric) {
            for (const entry of list.getEntries()) {
              const resource = entry as PerformanceResourceTiming;
              metric.resources.push({
                name: resource.name,
                type: resource.initiatorType,
                duration: resource.responseEnd - resource.startTime,
                size: resource.transferSize || 0,
                cached: (resource.transferSize || 0) === 0
              });
            }
          }
        });

        observer.observe({ type: 'resource', buffered: true });
        this.observers.push(observer);
      } catch (e) {
        console.warn('Resource observation not supported');
      }
    }
  }

  /**
   * 观察首屏
   */
  private observePaint(): void {
    if ('PerformanceObserver' in window) {
      try {
        const observer = new PerformanceObserver((list) => {
          const metric = this.getCurrentMetrics();
          for (const entry of list.getEntries()) {
            if (entry.name === 'first-contentful-paint') {
              if (metric) metric.FCP = entry.startTime;
            }
            if (entry.name === 'first-paint') {
              if (metric) metric.FMP = entry.startTime;
            }
          }
        });

        observer.observe({ type: 'paint', buffered: true });
        this.observers.push(observer);
      } catch (e) {
        console.warn('Paint observation not supported');
      }
    }
  }

  /**
   * 观察首次输入
   */
  private observeFirstInput(): void {
    if ('PerformanceObserver' in window) {
      try {
        const observer = new PerformanceObserver((list) => {
          const entry = list.getEntries()[0];
          if (entry) {
            const metric = this.getCurrentMetrics();
            if (metric) {
              metric.FID = (entry as any).processingStart - entry.startTime;
            }
          }
        });

        observer.observe({ type: 'first-input', buffered: true });
        this.observers.push(observer);
      } catch (e) {
        console.warn('First input observation not supported');
      }
    }
  }

  /**
   * FPS 监控
   */
  private startFPSMonitor(): void {
    const measureFPS = () => {
      const now = performance.now();
      const delta = now - this.lastFrameTime;
      this.lastFrameTime = now;

      const currentFPS = 1000 / delta;

      // 平滑 FPS
      this.fps = this.fps * 0.9 + currentFPS * 0.1;

      const metric = this.getCurrentMetrics();
      if (metric) {
        metric.fps = Math.round(this.fps);
        metric.frameTime = Math.round(delta);
      }

      this.rafId = requestAnimationFrame(measureFPS);
    };

    this.rafId = requestAnimationFrame(measureFPS);
  }

  /**
   * 内存监控
   */
  private monitorMemory(): void {
    const memory = (performance as any).memory;
    if (memory) {
      const metric = this.getCurrentMetrics();
      if (metric) {
        metric.jsHeapSize = memory.jsHeapSizeLimit;
        metric.usedJSHeapSize = memory.usedJSHeapSize;
        metric.totalJSHeapSize = memory.totalJSHeapSize;
      }
    }
  }

  /**
   * 收集基础指标
   */
  private collectBaselineMetrics(): void {
    if (typeof window === 'undefined') return;

    const timing = performance.timing;
    const navigation = performance.navigation;

    const metric: PerformanceMetrics = {
      resources: [],
      apiCalls: [],
      fps: this.fps,
      frameTime: 0,
      timestamp: Date.now(),
      TTFB: timing.responseStart - timing.requestStart
    };

    // 计算 LCP (简化版)
    try {
      const paintEntries = performance.getEntriesByType('paint');
      const lcpEntry = paintEntries
        .filter(p => p.entryType === 'largest-contentful-paint')
        .pop();
      if (lcpEntry) {
        metric.LCP = lcpEntry.startTime;
      }
    } catch (e) {
      // LCP 不可用
    }

    this.metrics.push(metric);
  }

  /**
   * 获取当前指标
   */
  private getCurrentMetrics(): PerformanceMetrics | null {
    if (this.metrics.length === 0) {
      this.metrics.push({
        resources: [],
        apiCalls: [],
        fps: 0,
        frameTime: 0,
        timestamp: Date.now()
      });
    }
    return this.metrics[this.metrics.length - 1];
  }

  /**
   * 记录 API 调用
   */
  recordApiCall(call: ApiMetric): void {
    const metric = this.getCurrentMetrics();
    if (metric) {
      metric.apiCalls.push(call);
    }
  }

  /**
   * 记录自定义事件
   */
  mark(name: string): void {
    if (typeof performance !== 'undefined' && 'mark' in performance) {
      (performance as any).mark(name);
    }
  }

  /**
   * 测量两个标记之间的时长
   */
  measure(name: string, startMark: string, endMark: string): number {
    if (typeof performance !== 'undefined' && 'measure' in performance) {
      try {
        (performance as any).measure(name, startMark, endMark);
        const entries = (performance as any).getEntriesByName(name);
        return entries[entries.length - 1]?.duration || 0;
      } catch (e) {
        return 0;
      }
    }
    return 0;
  }

  /**
   * 获取所有指标
   */
  getMetrics(): PerformanceMetrics[] {
    return [...this.metrics];
  }

  /**
   * 获取最新指标
   */
  getLatestMetrics(): PerformanceMetrics | null {
    return this.metrics[this.metrics.length - 1] || null;
  }

  /**
   * 获取汇总指标
   */
  getSummary(): {
    avgFPS: number;
    avgFrameTime: number;
    totalResources: number;
    totalApiCalls: number;
    avgResponseTime: number;
    errorRate: number;
    webVitals: {
      FCP?: number;
      LCP?: number;
      FID?: number;
      CLS?: number;
      TTFB?: number;
    };
  } {
    const latest = this.getLatestMetrics() || {
      resources: [],
      apiCalls: [],
      fps: 0,
      frameTime: 0,
      timestamp: Date.now(),
      FCP: 0, LCP: 0, FID: 0, CLS: 0, TTFB: 0
    };

    const allMetrics = this.getMetrics();
    const avgFPS = allMetrics.reduce((sum, m) => sum + m.fps, 0) / Math.max(allMetrics.length, 1);
    const avgFrameTime = allMetrics.reduce((sum, m) => sum + m.frameTime, 0) / Math.max(allMetrics.length, 1);

    const allApiCalls = allMetrics.flatMap(m => m.apiCalls);
    const avgResponseTime = allApiCalls.length > 0
      ? allApiCalls.reduce((sum, c) => sum + c.duration, 0) / allApiCalls.length
      : 0;
    const errorRate = allApiCalls.length > 0
      ? allApiCalls.filter(c => c.status >= 400).length / allApiCalls.length
      : 0;

    return {
      avgFPS: Math.round(avgFPS),
      avgFrameTime: Math.round(avgFrameTime),
      totalResources: latest.resources.length,
      totalApiCalls: allApiCalls.length,
      avgResponseTime: Math.round(avgResponseTime),
      errorRate: Math.round(errorRate * 100),
      webVitals: {
        FCP: latest.FCP,
        LCP: latest.LCP,
        FID: latest.FID,
        CLS: latest.CLS,
        TTFB: latest.TTFB
      }
    };
  }

  /**
   * 清除历史指标
   */
  clear(): void {
    this.metrics = [];
  }

  /**
   * 停止监控
   */
  stop(): void {
    this.observers.forEach(observer => observer.disconnect());
    this.observers = [];

    if (this.rafId !== null) {
      cancelAnimationFrame(this.rafId);
      this.rafId = null;
    }
  }
}

// 全局性能监控器
export const performanceMonitor = new PerformanceMonitor();

// ============================================
// React Hook
// ============================================

export function usePerformance() {
  const [metrics, setMetrics] = React.useState<PerformanceMetrics | null>(null);
  const [summary, setSummary] = React.useState<ReturnType<typeof performanceMonitor.getSummary> | null>(null);

  React.useEffect(() => {
    // 初始加载
    setMetrics(performanceMonitor.getLatestMetrics());
    setSummary(performanceMonitor.getSummary());

    // 定期更新
    const interval = setInterval(() => {
      setMetrics(performanceMonitor.getLatestMetrics());
      setSummary(performanceMonitor.getSummary());
    }, 1000);

    return () => clearInterval(interval);
  }, []);

  return {
    metrics,
    summary,
    mark: performanceMonitor.mark.bind(performanceMonitor),
    measure: performanceMonitor.measure.bind(performanceMonitor),
    recordApiCall: performanceMonitor.recordApiCall.bind(performanceMonitor),
    getSummary: performanceMonitor.getSummary.bind(performanceMonitor)
  };
}

// ============================================
// 性能指标展示组件
// ============================================

export const PerformanceIndicator: React.FC<{
  showDetails?: boolean;
}> = ({ showDetails = false }) => {
  const { metrics, summary } = usePerformance();

  const fpsColor = metrics && metrics.fps >= 50
    ? '#10b981'
    : metrics && metrics.fps >= 30
      ? '#f59e0b'
      : '#ef4444';

  return (
    <div style={{
      position: 'fixed',
      bottom: '20px',
      left: '20px',
      display: 'flex',
      gap: '8px',
      fontFamily: 'monospace',
      fontSize: '11px',
      zIndex: 9999
    }}>
      {/* FPS */}
      {metrics && (
        <div style={{
          padding: '4px 8px',
          background: 'rgba(0,0,0,0.8)',
          borderRadius: '4px',
          color: fpsColor
        }}>
          {metrics.fps} FPS
        </div>
      )}

      {/* 帧时间 */}
      {metrics && (
        <div style={{
          padding: '4px 8px',
          background: 'rgba(0,0,0,0.8)',
          borderRadius: '4px',
          color: '#94a3b8'
        }}>
          {metrics.frameTime}ms
        </div>
      )}

      {/* 内存 */}
      {metrics?.usedJSHeapSize && (
        <div style={{
          padding: '4px 8px',
          background: 'rgba(0,0,0,0.8)',
          borderRadius: '4px',
          color: '#94a3b8'
        }}>
          {Math.round(metrics.usedJSHeapSize / 1024 / 1024)}MB
        </div>
      )}

      {/* 详细信息 */}
      {showDetails && summary && (
        <div style={{
          padding: '8px 12px',
          background: 'rgba(0,0,0,0.9)',
          borderRadius: '8px',
          color: '#e2e8f0',
          maxWidth: '300px'
        }}>
          <div style={{ marginBottom: '8px', fontWeight: 600 }}>Web Vitals</div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '4px', fontSize: '10px' }}>
            <div>FCP: {summary.webVitals.FCP?.toFixed(0) || '-'}ms</div>
            <div>LCP: {summary.webVitals.LCP?.toFixed(0) || '-'}ms</div>
            <div>FID: {summary.webVitals.FID?.toFixed(0) || '-'}ms</div>
            <div>CLS: {summary.webVitals.CLS?.toFixed(3) || '-'}</div>
          </div>
        </div>
      )}
    </div>
  );
};
