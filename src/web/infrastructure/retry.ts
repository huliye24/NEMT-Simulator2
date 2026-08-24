/**
 * Copyright 2026 NEMT Lab
 *
 * 重试机制 - 指数退避算法
 */

// ============================================
// 错误分类
// ============================================

export enum RetryableErrorType {
  NETWORK_ERROR = 'network_error',
  TIMEOUT = 'timeout',
  SERVER_ERROR = 'server_error',
  RATE_LIMIT = 'rate_limit',
  SERVICE_UNAVAILABLE = 'service_unavailable',
  UNKNOWN = 'unknown'
}

export interface RetryConfig {
  /** 最大重试次数 */
  maxRetries: number;
  /** 初始延迟 (毫秒) */
  initialDelay: number;
  /** 最大延迟 (毫秒) */
  maxDelay: number;
  /** 退避乘数 */
  backoffMultiplier: number;
  /** 是否添加随机抖动 */
  jitter: boolean;
  /** 重试条件 */
  shouldRetry?: (error: unknown, attempt: number) => boolean;
}

export interface RetryResult<T> {
  success: boolean;
  data?: T;
  error?: unknown;
  attempts: number;
  totalTime: number;
  lastError?: unknown;
}

// 默认配置
const DEFAULT_CONFIG: RetryConfig = {
  maxRetries: 3,
  initialDelay: 1000,
  maxDelay: 30000,
  backoffMultiplier: 2,
  jitter: true,
  shouldRetry: (error, attempt) => {
    // 默认重试条件：网络错误、5xx服务器错误、429限流
    if (error instanceof TypeError) return true; // 网络错误
    if (error instanceof Error) {
      const status = (error as any).status || (error as any).response?.status;
      if (status === 429 || status === 503) return true;
      if (status >= 500) return true;
    }
    return false;
  }
};

// ============================================
// 重试工具函数
// ============================================

/**
 * 计算延迟时间 (指数退避 + 抖动)
 */
export function calculateDelay(
  attempt: number,
  config: RetryConfig
): number {
  // 指数退避
  let delay = config.initialDelay * Math.pow(config.backoffMultiplier, attempt);

  // 限制最大延迟
  delay = Math.min(delay, config.maxDelay);

  // 添加随机抖动 (0-25% 的延迟)
  if (config.jitter) {
    const jitter = delay * (0.25 * Math.random());
    delay += jitter;
  }

  return Math.floor(delay);
}

/**
 * 等待指定时间
 */
export function sleep(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * 判断错误是否可重试
 */
export function isRetryable(error: unknown, config: RetryConfig): boolean {
  if (config.shouldRetry) {
    return config.shouldRetry(error, 0);
  }
  return DEFAULT_CONFIG.shouldRetry?.(error, 0) ?? false;
}

// ============================================
// 重试装饰器
// ============================================

/**
 * 带重试的函数执行
 */
export async function withRetry<T>(
  fn: () => Promise<T>,
  config: Partial<RetryConfig> = {}
): Promise<RetryResult<T>> {
  const mergedConfig: RetryConfig = { ...DEFAULT_CONFIG, ...config };
  const startTime = Date.now();
  let lastError: unknown;

  for (let attempt = 0; attempt <= mergedConfig.maxRetries; attempt++) {
    try {
      const data = await fn();
      return {
        success: true,
        data,
        attempts: attempt + 1,
        totalTime: Date.now() - startTime
      };
    } catch (error) {
      lastError = error;

      // 检查是否应该重试
      const shouldRetry = mergedConfig.shouldRetry?.(error, attempt)
        ?? isRetryable(error, mergedConfig);

      if (!shouldRetry || attempt === mergedConfig.maxRetries) {
        return {
          success: false,
          error: lastError,
          attempts: attempt + 1,
          totalTime: Date.now() - startTime,
          lastError
        };
      }

      // 计算延迟并等待
      const delay = calculateDelay(attempt, mergedConfig);
      console.log(`[Retry] Attempt ${attempt + 1} failed, retrying in ${delay}ms...`);
      await sleep(delay);
    }
  }

  return {
    success: false,
    error: lastError,
    attempts: mergedConfig.maxRetries + 1,
    totalTime: Date.now() - startTime,
    lastError
  };
}

// ============================================
// 断路器模式
// ============================================

export enum CircuitState {
  CLOSED = 'closed',     // 正常，允许请求通过
  OPEN = 'open',         // 断开，拒绝所有请求
  HALF_OPEN = 'half_open' // 半开，允许一个请求测试
}

export interface CircuitBreakerConfig {
  /** 失败次数阈值 (打开断路器) */
  failureThreshold: number;
  /** 成功次数阈值 (关闭断路器) */
  successThreshold: number;
  /** 半开状态超时 (毫秒) */
  halfOpenTimeout: number;
  /** 监控时间窗口 (毫秒) */
  windowTime: number;
}

export class CircuitBreaker {
  private state: CircuitState = CircuitState.CLOSED;
  private failureCount = 0;
  private successCount = 0;
  private lastFailureTime = 0;
  private lastSuccessTime = 0;
  private recentFailures: number[] = [];

  constructor(private config: CircuitBreakerConfig) {}

  /**
   * 执行受保护的函数
   */
  async execute<T>(fn: () => Promise<T>): Promise<T> {
    // 检查断路器状态
    if (this.state === CircuitState.OPEN) {
      // 检查是否应该转换到半开状态
      if (Date.now() - this.lastFailureTime >= this.config.halfOpenTimeout) {
        this.state = CircuitState.HALF_OPEN;
        console.log('[CircuitBreaker] State: OPEN -> HALF_OPEN');
      } else {
        throw new Error('Circuit breaker is OPEN. Request rejected.');
      }
    }

    try {
      const result = await fn();
      this.onSuccess();
      return result;
    } catch (error) {
      this.onFailure();
      throw error;
    }
  }

  /**
   * 成功回调
   */
  private onSuccess(): void {
    this.lastSuccessTime = Date.now();

    if (this.state === CircuitState.HALF_OPEN) {
      this.successCount++;
      if (this.successCount >= this.config.successThreshold) {
        this.state = CircuitState.CLOSED;
        this.failureCount = 0;
        this.successCount = 0;
        console.log('[CircuitBreaker] State: HALF_OPEN -> CLOSED');
      }
    } else {
      this.failureCount = Math.max(0, this.failureCount - 1);
    }

    // 清理过期失败记录
    this.cleanupRecentFailures();
  }

  /**
   * 失败回调
   */
  private onFailure(): void {
    this.lastFailureTime = Date.now();
    this.failureCount++;
    this.recentFailures.push(Date.now());

    if (this.state === CircuitState.HALF_OPEN) {
      this.state = CircuitState.OPEN;
      this.successCount = 0;
      console.log('[CircuitBreaker] State: HALF_OPEN -> OPEN');
    } else if (this.failureCount >= this.config.failureThreshold) {
      this.state = CircuitState.OPEN;
      console.log('[CircuitBreaker] State: CLOSED -> OPEN');
    }

    this.cleanupRecentFailures();
  }

  /**
   * 清理过期失败记录
   */
  private cleanupRecentFailures(): void {
    const now = Date.now();
    this.recentFailures = this.recentFailures.filter(
      time => now - time < this.config.windowTime
    );
  }

  /**
   * 获取当前状态
   */
  getState(): CircuitState {
    return this.state;
  }

  /**
   * 获取失败次数
   */
  getFailureCount(): number {
    return this.failureCount;
  }

  /**
   * 重置断路器
   */
  reset(): void {
    this.state = CircuitState.CLOSED;
    this.failureCount = 0;
    this.successCount = 0;
    this.recentFailures = [];
    console.log('[CircuitBreaker] Reset to CLOSED');
  }

  /**
   * 获取统计信息
   */
  getStats(): {
    state: CircuitState;
    failureCount: number;
    recentFailureCount: number;
    lastFailureTime: number;
    lastSuccessTime: number;
  } {
    return {
      state: this.state,
      failureCount: this.failureCount,
      recentFailureCount: this.recentFailures.length,
      lastFailureTime: this.lastFailureTime,
      lastSuccessTime: this.lastSuccessTime
    };
  }
}

// ============================================
// 默认断路器实例
// ============================================

export const defaultCircuitBreaker = new CircuitBreaker({
  failureThreshold: 5,
  successThreshold: 2,
  halfOpenTimeout: 30000,
  windowTime: 60000
});

// ============================================
// 带断路器的重试
// ============================================

export async function withCircuitRetry<T>(
  fn: () => Promise<T>,
  circuitBreaker: CircuitBreaker = defaultCircuitBreaker,
  retryConfig: Partial<RetryConfig> = {}
): Promise<RetryResult<T>> {
  return circuitBreaker.execute(() => withRetry(fn, retryConfig));
}
