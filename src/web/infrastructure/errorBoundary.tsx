/**
 * Copyright 2026 NEMT Lab
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 */

import React, { Component, ErrorInfo, ReactNode } from 'react';
import { AlertTriangle, RefreshCw, Home, Copy, CheckCircle } from 'lucide-react';

// ============================================
// 错误类型定义
// ============================================

export enum ErrorSeverity {
  FATAL = 'fatal',        // 致命错误，应用无法继续
  CRITICAL = 'critical',  // 严重错误，部分功能不可用
  WARNING = 'warning',    // 警告，不影响核心功能
  INFO = 'info'           // 信息
}

export interface AppError {
  id: string;
  message: string;
  stack?: string;
  severity: ErrorSeverity;
  timestamp: number;
  context?: Record<string, unknown>;
  componentStack?: string;
}

export interface ErrorBoundaryProps {
  children: ReactNode;
  fallback?: ReactNode;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
  /** 错误恢复后是否重置状态 */
  resetOnChange?: boolean;
  /** 是否显示错误详情 */
  showDetails?: boolean;
}

export interface ErrorBoundaryState {
  hasError: boolean;
  error: AppError | null;
  errorId: string | null;
}

// ============================================
// 错误日志收集器
// ============================================

class ErrorCollector {
  private errors: AppError[] = [];
  private maxErrors = 100;
  private listeners: Set<(error: AppError) => void> = new Set();

  /**
   * 记录错误
   */
  log(error: Error, severity: ErrorSeverity = ErrorSeverity.CRITICAL, context?: Record<string, unknown>): string {
    const id = this.generateId();
    const appError: AppError = {
      id,
      message: error.message || 'Unknown error',
      stack: error.stack,
      severity,
      timestamp: Date.now(),
      context
    };

    this.errors.unshift(appError);

    // 限制存储数量
    if (this.errors.length > this.maxErrors) {
      this.errors = this.errors.slice(0, this.maxErrors);
    }

    // 通知监听器
    this.listeners.forEach(listener => listener(appError));

    // 输出到控制台
    console.error(`[NEMT Error] [${severity}] ${id}:`, error);

    return id;
  }

  /**
   * 生成唯一 ID
   */
  private generateId(): string {
    return `err_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  /**
   * 获取所有错误
   */
  getErrors(): AppError[] {
    return [...this.errors];
  }

  /**
   * 获取错误数量
   */
  getErrorCount(): number {
    return this.errors.length;
  }

  /**
   * 获取特定严重级别的错误
   */
  getErrorsBySeverity(severity: ErrorSeverity): AppError[] {
    return this.errors.filter(e => e.severity === severity);
  }

  /**
   * 清除所有错误
   */
  clear(): void {
    this.errors = [];
  }

  /**
   * 清除特定错误
   */
  removeError(id: string): void {
    this.errors = this.errors.filter(e => e.id !== id);
  }

  /**
   * 订阅错误
   */
  subscribe(listener: (error: AppError) => void): () => void {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }

  /**
   * 导出错误日志
   */
  export(): string {
    return JSON.stringify({
      exportedAt: new Date().toISOString(),
      count: this.errors.length,
      errors: this.errors
    }, null, 2);
  }
}

// 全局错误收集器实例
export const errorCollector = new ErrorCollector();

// ============================================
// 全局错误处理器
// ============================================

export function setupGlobalErrorHandlers(): void {
  // 处理未捕获的 Promise 拒绝
  window.addEventListener('unhandledrejection', (event) => {
    const error = event.reason instanceof Error
      ? event.reason
      : new Error(String(event.reason));

    errorCollector.log(error, ErrorSeverity.CRITICAL, {
      type: 'unhandledrejection',
      timestamp: event.timeStamp
    });
  });

  // 处理未捕获的错误
  window.addEventListener('error', (event) => {
    const error = new Error(event.message);
    error.stack = event.error?.stack;

    errorCollector.log(error, ErrorSeverity.CRITICAL, {
      type: 'uncaughterror',
      filename: event.filename,
      lineno: event.lineno,
      colno: event.colno
    });
  });
}

// ============================================
// 错误边界组件
// ============================================

export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false, error: null, errorId: null };
  }

  static getDerivedStateFromError(error: Error): Partial<ErrorBoundaryState> {
    return {
      hasError: true,
      errorId: errorCollector.log(error, ErrorSeverity.CRITICAL)
    };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    // 更新错误详情
    this.setState(prev => ({
      error: {
        id: prev.errorId || '',
        message: error.message,
        stack: error.stack,
        severity: ErrorSeverity.CRITICAL,
        timestamp: Date.now(),
        componentStack: errorInfo.componentStack || undefined
      }
    }));

    // 调用错误回调
    this.props.onError?.(error, errorInfo);
  }

  componentDidUpdate(prevProps: ErrorBoundaryProps): void {
    if (this.props.resetOnChange && prevProps.children !== this.props.children) {
      this.handleReset();
    }
  }

  handleReset = (): void => {
    this.setState({ hasError: false, error: null, errorId: null });
  };

  handleRetry = (): void => {
    this.handleReset();
  };

  handleCopyError = (): void => {
    if (this.state.error) {
      navigator.clipboard.writeText(
        `${this.state.error.message}\n\n${this.state.error.stack || ''}`
      );
    }
  };

  render(): ReactNode {
    if (this.state.hasError && this.state.error) {
      // 自定义错误 UI
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <ErrorFallback
          error={this.state.error}
          onReset={this.handleReset}
          onRetry={this.handleRetry}
          onCopy={this.handleCopyError}
          showDetails={this.props.showDetails ?? true}
        />
      );
    }

    return this.props.children;
  }
}

// ============================================
// 错误展示组件
// ============================================

interface ErrorFallbackProps {
  error: AppError;
  onReset: () => void;
  onRetry: () => void;
  onCopy: () => void;
  showDetails?: boolean;
}

const ErrorFallback: React.FC<ErrorFallbackProps> = ({
  error,
  onReset,
  onRetry,
  onCopy,
  showDetails = true
}) => {
  const [copied, setCopied] = React.useState(false);

  const handleCopy = () => {
    onCopy();
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const severityConfig = {
    [ErrorSeverity.FATAL]: { color: '#ef4444', label: '致命错误' },
    [ErrorSeverity.CRITICAL]: { color: '#f97316', label: '严重错误' },
    [ErrorSeverity.WARNING]: { color: '#eab308', label: '警告' },
    [ErrorSeverity.INFO]: { color: '#3b82f6', label: '信息' }
  };

  const config = severityConfig[error.severity];

  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      background: '#020617',
      padding: '24px'
    }}>
      <div style={{
        maxWidth: '600px',
        width: '100%',
        background: '#1e293b',
        borderRadius: '16px',
        border: `1px solid ${config.color}44`,
        overflow: 'hidden'
      }}>
        {/* 头部 */}
        <div style={{
          background: `${config.color}11`,
          padding: '20px 24px',
          borderBottom: `1px solid ${config.color}22`
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <div style={{
              width: '48px',
              height: '48px',
              borderRadius: '12px',
              background: `${config.color}22`,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}>
              <AlertTriangle size={24} color={config.color} />
            </div>
            <div>
              <h2 style={{
                margin: 0,
                fontSize: '18px',
                color: config.color
              }}>
                {config.label}
              </h2>
              <p style={{
                margin: '4px 0 0',
                fontSize: '13px',
                color: '#94a3b8'
              }}>
                错误 ID: {error.id}
              </p>
            </div>
          </div>
        </div>

        {/* 内容 */}
        <div style={{ padding: '24px' }}>
          <div style={{
            background: '#0f172a',
            borderRadius: '8px',
            padding: '16px',
            marginBottom: '20px'
          }}>
            <p style={{
              margin: 0,
              color: '#e2e8f0',
              fontSize: '14px',
              lineHeight: 1.6
            }}>
              {error.message || '发生了一个未知错误'}
            </p>
          </div>

          {showDetails && error.stack && (
            <div style={{ marginBottom: '20px' }}>
              <h4 style={{
                margin: '0 0 8px',
                fontSize: '13px',
                color: '#94a3b8',
                textTransform: 'uppercase',
                letterSpacing: '1px'
              }}>
                错误堆栈
              </h4>
              <pre style={{
                background: '#0f172a',
                borderRadius: '8px',
                padding: '16px',
                margin: 0,
                overflow: 'auto',
                maxHeight: '200px',
                fontSize: '12px',
                color: '#94a3b8',
                fontFamily: 'monospace',
                whiteSpace: 'pre-wrap'
              }}>
                {error.stack}
              </pre>
            </div>
          )}

          {/* 操作按钮 */}
          <div style={{ display: 'flex', gap: '12px' }}>
            <button
              onClick={onRetry}
              style={{
                flex: 1,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '8px',
                padding: '12px 20px',
                borderRadius: '8px',
                border: 'none',
                background: '#10b981',
                color: '#fff',
                cursor: 'pointer',
                fontSize: '14px',
                fontWeight: '500'
              }}
            >
              <RefreshCw size={16} />
              重试
            </button>

            <button
              onClick={handleCopy}
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '8px',
                padding: '12px 20px',
                borderRadius: '8px',
                border: '1px solid #475569',
                background: 'transparent',
                color: '#94a3b8',
                cursor: 'pointer',
                fontSize: '14px'
              }}
            >
              {copied ? <CheckCircle size={16} /> : <Copy size={16} />}
              {copied ? '已复制' : '复制错误'}
            </button>

            <button
              onClick={onReset}
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '8px',
                padding: '12px 20px',
                borderRadius: '8px',
                border: '1px solid #475569',
                background: 'transparent',
                color: '#94a3b8',
                cursor: 'pointer',
                fontSize: '14px'
              }}
            >
              <Home size={16} />
              首页
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

// ============================================
// 带错误边界的组件包装器
// ============================================

export function withErrorBoundary<P extends object>(
  Component: React.ComponentType<P>,
  fallback?: ReactNode
): React.FC<P> {
  return function WithErrorBoundary(props: P) {
    return (
      <ErrorBoundary fallback={fallback}>
        <Component {...props} />
      </ErrorBoundary>
    );
  };
}
