/**
 * Copyright 2026 NEMT Lab
 *
 * NEMT Platform - 策略容器平台
 *
 * 核心理念：NEMT 不生产策略，而是策略运行的容器
 * 类似抖音：平台提供基础设施，KOL/开发者提供内容
 *
 * 架构：采用组件化设计，每个组件独立职责
 * - stores/: 状态管理 (策略/胶囊/币安/UI)
 * - components/: UI 组件 (platform/strategy/views)
 * - events/: 事件总线 (Store 间通信)
 */

// 初始化 i18n
import './infrastructure/i18n';
// 初始化主题样式
import { injectThemeStyles } from './infrastructure/theme';
injectThemeStyles();

// React
import React, { useEffect } from 'react';

// 基础设施
import { ErrorBoundary, setupGlobalErrorHandlers } from './infrastructure/errorBoundary';
import { useKeyboardShortcuts, COMMON_SHORTCUTS } from './infrastructure/shortcuts';
import { useUIStore, useStrategyStore } from './stores';

// 组件
import { PlatformHeader, Sidebar, CommandPalette } from './components/platform';
import { MainContent } from './components/views';

// 演化系统
import { evolutionEngine } from './evolution/engine';

// Electron 集成
import { useElectron } from './hooks/useElectron';

import './index.css';

// ============================================
// Electron 集成 Hook
// ============================================

function useElectronIntegration() {
  const { isElectron, api, gatewayStatus } = useElectron();

  useEffect(() => {
    if (isElectron) {
      console.log('[NEMT] Running in Electron mode');
      console.log('[NEMT] Gateway status:', gatewayStatus);

      // 注册菜单事件
      if (api?.menu) {
        api.menu.onRunSimulation(() => {
          console.log('[NEMT] Menu: Run Simulation');
          // 触发模拟运行
        });

        api.menu.onStopSimulation(() => {
          console.log('[NEMT] Menu: Stop Simulation');
          // 停止模拟
        });

        api.menu.onSettings(() => {
          console.log('[NEMT] Menu: Settings');
          // 打开设置
        });
      }
    }
  }, [isElectron, api, gatewayStatus]);

  return { isElectron, gatewayStatus };
}

// ============================================
// 快捷键 Hook
// ============================================

function useAppShortcuts() {
  const { setActiveView, toggleCommandPalette, toggleSidebar } = useUIStore();
  const addStrategy = useStrategyStore(state => state.addStrategy);

  useKeyboardShortcuts([
    {
      ...COMMON_SHORTCUTS.COMMAND_PALETTE,
      action: toggleCommandPalette,
      priority: 100
    },
    {
      ...COMMON_SHORTCUTS.TOGGLE_SIDEBAR,
      action: toggleSidebar,
      priority: 90
    },
    {
      ...COMMON_SHORTCUTS.STRATEGIES,
      action: () => setActiveView('strategies'),
      priority: 80
    },
    {
      ...COMMON_SHORTCUTS.CONTAINERS,
      action: () => setActiveView('containers'),
      priority: 80
    },
    {
      ...COMMON_SHORTCUTS.CAPSULES,
      action: () => setActiveView('capsules'),
      priority: 80
    },
    {
      ...COMMON_SHORTCUTS.NEW_STRATEGY,
      action: () => addStrategy({
        name: '新策略',
        author: 'User',
        description: '这是一个新创建的策略',
        version: '1.0.0',
        status: 'draft',
        metrics: { totalTrades: 0, winRate: 0, totalPnL: 0, sharpeRatio: 0 },
        tags: ['新策略']
      }),
      priority: 90
    }
  ]);
}

// ============================================
// 主应用组件
// ============================================

function NEMTPlatform() {
  // Electron 集成
  const { isElectron, gatewayStatus } = useElectronIntegration();

  // 初始化全局错误处理
  useEffect(() => {
    setupGlobalErrorHandlers();
    console.log('[NEMT Platform] Initialized');
  }, []);

  // 注册快捷键
  useAppShortcuts();

  return (
    <div style={{ minHeight: '100vh', background: '#020617', color: '#e2e8f0' }}>
      {/* Electron Gateway 状态指示器 */}
      {isElectron && (
        <div style={{
          position: 'fixed',
          bottom: 16,
          right: 16,
          padding: '8px 12px',
          background: gatewayStatus.connected ? 'rgba(34, 197, 94, 0.2)' : 'rgba(239, 68, 68, 0.2)',
          border: `1px solid ${gatewayStatus.connected ? '#22c55e' : '#ef4444'}`,
          borderRadius: 8,
          fontSize: 12,
          zIndex: 9999,
        }}>
          {gatewayStatus.connected ? 'Gateway: Connected' : 'Gateway: Offline'}
        </div>
      )}

      {/* 头部 */}
      <PlatformHeader />

      {/* 主体区域 */}
      <div style={{ display: 'flex' }}>
        {/* 侧边栏 */}
        <Sidebar />

        {/* 主内容 */}
        <main style={{ flex: 1, padding: '24px 32px' }}>
          <MainContent />
        </main>
      </div>

      {/* 命令面板 */}
      <CommandPalette />

      {/* 全局样式 */}
      <style>{`
        * { box-sizing: border-box; }
        body { margin: 0; }
        button:hover { opacity: 0.9; }
        button:active { transform: scale(0.98); }
      `}</style>
    </div>
  );
}

// ============================================
// 应用入口 (带错误边界)
// ============================================

function App() {
  return (
    <ErrorBoundary>
      <NEMTPlatform />
    </ErrorBoundary>
  );
}

export default App;
