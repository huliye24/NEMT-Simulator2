/**
 * Copyright 2026 NEMT Lab
 *
 * UI Store - 独立管理 UI 相关状态
 * 遵循原则：单一职责，只管 UI
 */

import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';

// ============================================
// 类型定义
// ============================================

export type Theme = 'dark' | 'light' | 'system';
export type ViewId = 'strategies' | 'containers' | 'capsules' | 'monitor' | 'terminal' | 'market' | 'execution' | 'dualbuffer' | 'backtest' | 'position';

// ============================================
// 状态接口
// ============================================

interface UIState {
  // 主题
  theme: Theme;

  // 侧边栏
  sidebarCollapsed: boolean;

  // 命令面板
  commandPaletteOpen: boolean;

  // 当前视图
  activeView: ViewId;

  // 初始化状态
  isInitialized: boolean;
}

// ============================================
// Actions 接口
// ============================================

interface UIActions {
  // 主题
  setTheme: (theme: Theme) => void;

  // 侧边栏
  toggleSidebar: () => void;
  setSidebarCollapsed: (collapsed: boolean) => void;

  // 命令面板
  toggleCommandPalette: () => void;
  openCommandPalette: () => void;
  closeCommandPalette: () => void;

  // 视图
  setActiveView: (view: ViewId) => void;

  // 初始化
  setInitialized: (initialized: boolean) => void;

  // 重置
  reset: () => void;
}

// ============================================
// Store 创建
// ============================================

export const useUIStore = create<UIState & UIActions>()(
  persist(
    (set) => ({
      // 初始状态
      theme: 'dark',
      sidebarCollapsed: false,
      commandPaletteOpen: false,
      activeView: 'strategies',
      isInitialized: false,

      // 主题
      setTheme: (theme) => {
        set({ theme });
        // 应用主题到 document
        document.documentElement.setAttribute('data-theme', theme);
      },

      // 侧边栏
      toggleSidebar: () => {
        set(state => ({ sidebarCollapsed: !state.sidebarCollapsed }));
      },

      setSidebarCollapsed: (collapsed) => {
        set({ sidebarCollapsed: collapsed });
      },

      // 命令面板
      toggleCommandPalette: () => {
        set(state => ({ commandPaletteOpen: !state.commandPaletteOpen }));
      },

      openCommandPalette: () => {
        set({ commandPaletteOpen: true });
      },

      closeCommandPalette: () => {
        set({ commandPaletteOpen: false });
      },

      // 视图
      setActiveView: (view) => {
        set({ activeView: view });
      },

      // 初始化
      setInitialized: (initialized) => {
        set({ isInitialized: initialized });
      },

      // 重置
      reset: () => {
        set({
          theme: 'dark',
          sidebarCollapsed: false,
          commandPaletteOpen: false,
          activeView: 'strategies',
          isInitialized: false,
        });
      },
    }),
    {
      name: 'nemt-ui-storage',
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        theme: state.theme,
        sidebarCollapsed: state.sidebarCollapsed,
        activeView: state.activeView,
      })
    }
  )
);

// ============================================
// 选择器 (Selectors)
// ============================================

export const useTheme = () => useUIStore(state => state.theme);

export const useSidebarCollapsed = () => useUIStore(state => state.sidebarCollapsed);

export const useCommandPaletteOpen = () => useUIStore(state => state.commandPaletteOpen);

export const useActiveView = () => useUIStore(state => state.activeView);

export const useIsInitialized = () => useUIStore(state => state.isInitialized);

// 便捷的视图切换
export const useNavigateTo = () => {
  const setActiveView = useUIStore(state => state.setActiveView);
  return (view: ViewId) => setActiveView(view);
};

// 主题检测
export const useIsDarkMode = () => {
  const theme = useUIStore(state => state.theme);
  if (theme === 'system') {
    return window.matchMedia('(prefers-color-scheme: dark)').matches;
  }
  return theme === 'dark';
};
