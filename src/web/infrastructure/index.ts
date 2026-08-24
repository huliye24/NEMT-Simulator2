/**
 * Copyright 2026 NEMT Lab
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 */

// 基础设施模块导出

// 错误处理
export { ErrorBoundary, errorCollector, setupGlobalErrorHandlers, ErrorSeverity } from './errorBoundary';
export type { AppError, ErrorBoundaryProps, ErrorBoundaryState } from './errorBoundary';

export { withRetry, withCircuitRetry, CircuitBreaker, CircuitState, defaultCircuitBreaker, calculateDelay, sleep, isRetryable, RetryableErrorType } from './retry';
export type { RetryConfig, RetryResult, CircuitBreakerConfig } from './retry';

// 状态管理
export { usePlatformStore, useStrategies, useSelectedStrategy, useCapsules, useActiveView, useTheme } from './store';
export { useBinanceState, useBinancePrices, useBinanceConnected } from './store';
export { stateHistory } from './store';
export type { StateSnapshot, Strategy, StrategyStatus, StrategyMetrics, Capsule, CapsuleType, CapsuleStatus, ViewId, Theme, BinanceState, MarketData } from './store';

// 币安服务
export { binanceService, fetchKlines, fetchPrice, fetchPrices } from './binanceService';
export type { BinanceKline, BinanceTicker, BinanceConfig, BinanceConnectionState } from './binanceService';

// 键盘快捷键
export { useKeyboardShortcuts, COMMON_SHORTCUTS } from './shortcuts';
export type { Shortcut } from './shortcuts';

// 主题
export { injectThemeStyles } from './theme';

// 拖拽排序
export { SortableList, DragHandle } from './dragSort';

// 性能监控
export { PerformanceIndicator } from './performance';
export type { PerformanceMetrics } from './performance';

// 通知
export { Notification } from './notification';
export type { NotificationType, NotificationOptions } from './notification';

// 工具提示
export { Tooltip } from './tooltip';
export type { TooltipProps } from './tooltip';

// 骨架屏
export { Skeleton, SkeletonText } from './skeleton';
export type { SkeletonProps } from './skeleton';

// 上下文菜单
export { ContextMenu } from './contextMenu';
export type { ContextMenuProps } from './contextMenu';

// 虚拟列表
export { VirtualList } from './virtualList';
export type { VirtualListProps } from './virtualList';

// 市场视图
export { MarketView } from './MarketView';
