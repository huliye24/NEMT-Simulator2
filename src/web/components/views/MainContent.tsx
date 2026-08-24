/**
 * Copyright 2026 NEMT Lab
 *
 * 主内容区域 - 根据当前视图显示不同内容
 */

import React from 'react';
import { useActiveView } from '../../stores';
import { StrategiesView } from '../strategy';
import { NEMTDashboard } from '../NEMTDashboard';
import { DualBufferDashboard } from '../DualBufferDashboard';
import { BacktestView } from '../../strategy/backtest';
import { PositionManager } from '../position/PositionManager';
import {
  ContainersView,
  CapsulesView,
  MonitorView,
  TerminalView,
  MarketView
} from './PlaceholderViews';

const viewComponents: Record<string, React.ComponentType> = {
  strategies: StrategiesView,
  execution: NEMTDashboard,
  backtest: BacktestView,
  dualbuffer: DualBufferDashboard,
  containers: ContainersView,
  capsules: CapsulesView,
  position: PositionManager,
  monitor: MonitorView,
  terminal: TerminalView,
  market: MarketView,
};

export function MainContent() {
  const activeView = useActiveView();

  const ViewComponent = viewComponents[activeView] || StrategiesView;

  return <ViewComponent />;
}
