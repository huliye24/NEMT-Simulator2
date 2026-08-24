/**
 * Copyright 2026 NEMT Lab
 *
 * 事件类型统一导出
 */

export { EventType } from './eventBus';
export { eventBus } from './eventBus';

export type {
  StrategyCreatedPayload,
  StrategyUpdatedPayload,
  StrategyStatusChangedPayload,
  CapsuleStatusChangedPayload,
  MarketPriceUpdatedPayload,
  ViewChangedPayload,
  ThemeChangedPayload,
} from './eventBus';
