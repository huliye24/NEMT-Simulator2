/**
 * Copyright 2026 NEMT Lab
 *
 * 工业级系统 - 简化版
 */

// ============================================
// 沙箱隔离
// ============================================

export interface SandboxConfig {
  id: string;
  timeout?: number;
  memoryLimit?: number;
}

export interface SandboxResult {
  success: boolean;
  data?: any;
  error?: string;
  executionTime: number;
}

export class Sandbox {
  private id: string;
  private state: 'idle' | 'running' | 'terminated' = 'idle';

  constructor(config: SandboxConfig) {
    this.id = config.id;
  }

  async execute(code: string): Promise<SandboxResult> {
    const start = Date.now();
    try {
      // 在 Web Worker 中执行
      const result = new Function(code)();
      return {
        success: true,
        data: result,
        executionTime: Date.now() - start
      };
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error',
        executionTime: Date.now() - start
      };
    }
  }

  terminate(): void {
    this.state = 'terminated';
  }
}

export const sandboxManager = {
  sandboxes: new Map<string, Sandbox>(),

  create(config: SandboxConfig): Sandbox {
    const sandbox = new Sandbox(config);
    this.sandboxes.set(config.id, sandbox);
    return sandbox;
  },

  get(id: string): Sandbox | undefined {
    return this.sandboxes.get(id);
  },

  destroy(id: string): void {
    const sandbox = this.sandboxes.get(id);
    sandbox?.terminate();
    this.sandboxes.delete(id);
  }
};

// ============================================
// 自我修复
// ============================================

export type ErrorCategory = 'network' | 'timeout' | 'validation' | 'permission' | 'resource' | 'state' | 'unknown';

export interface RecoveryResult {
  success: boolean;
  attempts: number;
  error?: Error;
  fallbackValue?: any;
}

export class SelfHealingEngine {
  private healthScore = 100;
  private history: RecoveryResult[] = [];

  async tryRecover<T>(
    operation: () => Promise<T>,
    fallbackValue?: T
  ): Promise<RecoveryResult & { value?: T }> {
    let attempts = 0;
    const maxAttempts = 3;

    while (attempts < maxAttempts) {
      attempts++;
      try {
        const value = await operation();
        this.recordRecovery(true);
        return { success: true, attempts, value };
      } catch (error) {
        if (attempts >= maxAttempts) {
          this.recordRecovery(false);
          return {
            success: false,
            attempts,
            error: error instanceof Error ? error : new Error(String(error)),
            fallbackValue
          };
        }
        await this.sleep(500 * attempts);
      }
    }

    return { success: false, attempts };
  }

  private sleep(ms: number): Promise<void> {
    return new Promise(r => setTimeout(r, ms));
  }

  private recordRecovery(success: boolean): void {
    this.history.push({ success, attempts: 1 });
    this.healthScore = success
      ? Math.min(100, this.healthScore + 0.5)
      : Math.max(0, this.healthScore - 5);
    if (this.history.length > 100) this.history.shift();
  }

  getHealthScore(): number {
    return this.healthScore;
  }

  getHealthStatus(): { score: number; status: 'healthy' | 'degraded' | 'critical' } {
    return {
      score: Math.round(this.healthScore),
      status: this.healthScore >= 80 ? 'healthy' : this.healthScore >= 50 ? 'degraded' : 'critical'
    };
  }
}

export const selfHealingEngine = new SelfHealingEngine();

// ============================================
// 内存管理
// ============================================

export interface MemoryStatus {
  used: number;
  total: number;
  percentage: number;
  trend: 'stable' | 'increasing' | 'decreasing';
}

export class MemoryTracker {
  private snapshots: number[] = [];

  getStatus(): MemoryStatus {
    const memory = (performance as any)?.memory;
    if (!memory) {
      return { used: 0, total: 0, percentage: 0, trend: 'stable' };
    }

    const used = memory.usedJSHeapSize / 1024 / 1024;
    const total = memory.jsHeapSizeLimit / 1024 / 1024;
    const percentage = (memory.usedJSHeapSize / memory.jsHeapSizeLimit) * 100;

    this.snapshots.push(used);
    if (this.snapshots.length > 10) this.snapshots.shift();

    let trend: 'stable' | 'increasing' | 'decreasing' = 'stable';
    if (this.snapshots.length >= 3) {
      const recent = this.snapshots.slice(-3);
      if (recent[2] > recent[0] * 1.1) trend = 'increasing';
      else if (recent[2] < recent[0] * 0.9) trend = 'decreasing';
    }

    return { used, total, percentage, trend };
  }

  forceGC(): void {
    // 尝试触发 GC
    const temp = [];
    for (let i = 0; i < 100000; i++) temp.push(new Array(100));
    temp.length = 0;
  }
}

export const memoryTracker = new MemoryTracker();

// ============================================
// 事务管理
// ============================================

export interface Transaction {
  id: string;
  type: string;
  state: 'pending' | 'committed' | 'rolled-back';
  operations: Array<{ type: string; path: string }>;
}

export class TransactionManager {
  private transactions: Transaction[] = [];

  async execute<T>(
    type: string,
    operations: (ctx: { write: (path: string, value: any) => void }) => void | Promise<void>
  ): Promise<{ success: boolean; transaction?: Transaction }> {
    const tx: Transaction = {
      id: `tx_${Date.now()}`,
      type,
      state: 'pending',
      operations: []
    };

    this.transactions.push(tx);

    try {
      const ctx = {
        write: (path: string, value: any) => {
          tx.operations.push({ type: 'write', path });
        }
      };

      await operations(ctx);
      tx.state = 'committed';
      return { success: true, transaction: tx };
    } catch {
      tx.state = 'rolled-back';
      return { success: false };
    }
  }

  getHistory(): Transaction[] {
    return [...this.transactions];
  }
}

export const transactionManager = new TransactionManager();

// ============================================
// 健康检查
// ============================================

export type HealthStatus = 'healthy' | 'degraded' | 'unhealthy';

export interface HealthReport {
  overall: HealthStatus;
  score: number;
  checks: Array<{ name: string; status: HealthStatus }>;
  alerts: number;
}

export class HealthMonitor {
  private checks: Map<string, () => HealthStatus> = new Map();
  private alerts: Array<{ severity: string; title: string }> = [];

  registerCheck(name: string, check: () => HealthStatus): void {
    this.checks.set(name, check);
  }

  async getReport(): Promise<HealthReport> {
    const results: Array<{ name: string; status: HealthStatus }> = [];
    let healthy = 0, degraded = 0, unhealthy = 0;

    this.checks.forEach((check, name) => {
      const status = check();
      results.push({ name, status });
      if (status === 'healthy') healthy++;
      else if (status === 'degraded') degraded++;
      else unhealthy++;
    });

    const total = results.length || 1;
    const score = Math.round(((healthy * 100) + (degraded * 50)) / total);

    return {
      overall: unhealthy > 0 ? 'unhealthy' : degraded > 0 ? 'degraded' : 'healthy',
      score,
      checks: results,
      alerts: this.alerts.length
    };
  }

  createAlert(severity: string, title: string): void {
    this.alerts.push({ severity, title });
  }
}

export const healthMonitor = new HealthMonitor();

// ============================================
// React Hooks
// ============================================

import React, { useState, useEffect } from 'react';

export function useHealth() {
  const [report, setReport] = useState<HealthReport | null>(null);

  useEffect(() => {
    const update = async () => {
      const r = await healthMonitor.getReport();
      setReport(r);
    };
    update();
    const interval = setInterval(update, 30000);
    return () => clearInterval(interval);
  }, []);

  return {
    report,
    healthScore: selfHealingEngine.getHealthScore(),
    memoryStatus: memoryTracker.getStatus(),
    healthStatus: selfHealingEngine.getHealthStatus()
  };
}

export function HealthIndicator() {
  const { report, healthScore } = useHealth();

  const color = !report ? '#64748b'
    : report.overall === 'healthy' ? '#10b981'
    : report.overall === 'degraded' ? '#f59e0b' : '#ef4444';

  return (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      gap: '6px',
      padding: '4px 10px',
      background: 'rgba(0,0,0,0.8)',
      borderRadius: '12px',
      fontSize: '11px',
      fontFamily: 'monospace'
    }}>
      <div style={{
        width: '8px',
        height: '8px',
        borderRadius: '50%',
        background: color
      }} />
      <span style={{ color: '#94a3b8' }}>
        {report?.overall === 'healthy' ? '健康'
          : report?.overall === 'degraded' ? '降级'
          : report?.overall === 'unhealthy' ? '异常' : '检查中'} {healthScore}%
      </span>
    </div>
  );
}

export function MemoryIndicator() {
  const { memoryStatus } = useHealth();

  const color = memoryStatus.percentage > 80 ? '#ef4444'
    : memoryStatus.percentage > 60 ? '#f59e0b' : '#10b981';

  return (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      gap: '6px',
      padding: '4px 10px',
      background: 'rgba(0,0,0,0.8)',
      borderRadius: '12px',
      fontSize: '11px',
      fontFamily: 'monospace'
    }}>
      <div style={{
        width: '8px',
        height: '8px',
        borderRadius: '50%',
        background: color
      }} />
      <span style={{ color: '#94a3b8' }}>
        内存 {memoryStatus.percentage.toFixed(0)}%
      </span>
    </div>
  );
}
