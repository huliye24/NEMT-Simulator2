/**
 * Copyright 2026 NEMT Lab
 *
 * 事件 Hook - 在 React 组件中使用事件总线
 */

import { useEffect } from 'react';
import { eventBus } from './eventBus';

// ============================================
// Hook 类型
// ============================================

type UnsubscribeFn = () => void;

// ============================================
// Hooks
// ============================================

/**
 * 订阅事件的 Hook
 */
export function useEvent<T = unknown>(
  event: string,
  listener: (payload: T) => void,
  deps: React.DependencyList = []
): void {
  useEffect(() => {
    const unsubscribe = eventBus.on(event, listener);
    return unsubscribe;
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [event, ...deps]);
}

/**
 * 订阅事件并在卸载时自动取消
 */
export function useEventSubscription<T = unknown>(
  event: string,
  listener: (payload: T) => void
): void {
  useEffect(() => {
    const unsubscribe = eventBus.on<T>(event, listener);
    return unsubscribe;
  }, [event, listener]);
}

/**
 * 等待特定事件发生一次
 */
export function useEventOnce<T = unknown>(
  event: string,
  listener: (payload: T) => void
): void {
  useEffect(() => {
    eventBus.once<T>(event, listener);
  }, [event, listener]);
}

/**
 * 发布事件的 Hook（用于触发事件）
 */
export function useEmit() {
  return <T = unknown>(event: string, payload?: T) => {
    eventBus.emit<T>(event, payload);
  };
}

/**
 * 获取事件统计（调试用）
 */
export function useEventStats(): Record<string, number> {
  return eventBus.getStats();
}

/**
 * 等待特定事件（异步）
 */
export function waitForEvent<T = unknown>(
  event: string,
  timeout = 5000
): Promise<T> {
  return eventBus.waitFor<T>(event, timeout);
}
