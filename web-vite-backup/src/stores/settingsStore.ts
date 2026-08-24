/**
 * Copyright 2026 NEMT Lab
 *
 * Settings Store - 管理应用设置
 */

import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';

// ============================================
// 类型定义
// ============================================

export type Theme = 'dark' | 'light' | 'system';
export type Language = 'zh-CN' | 'en-US';

export interface Settings {
  // 通用
  theme: Theme;
  language: Language;
  
  // 交易
  defaultContractMultiplier: number;
  slippageBps: number;
  
  // 系统
  gatewayUrl: string;
  debugMode: boolean;
  shortcutsHint: boolean;
  notifications: boolean;
}

// ============================================
// 默认值
// ============================================

const defaultSettings: Settings = {
  theme: 'dark',
  language: 'zh-CN',
  defaultContractMultiplier: 1,
  slippageBps: 0,
  gatewayUrl: 'http://localhost:8080',
  debugMode: false,
  shortcutsHint: true,
  notifications: true,
};

// ============================================
// Store 接口
// ============================================

interface SettingsState extends Settings {
  // 弹窗状态
  settingsOpen: boolean;
  
  // 临时编辑状态
  pendingSettings: Settings | null;
  hasUnsavedChanges: boolean;
  
  // 操作
  openSettings: () => void;
  closeSettings: () => void;
  toggleSettings: () => void;
  
  // 更新设置
  updateSettings: (settings: Partial<Settings>) => void;
  resetSettings: () => void;
  
  // 临时编辑
  startEditing: () => void;
  saveAndClose: () => void;
  discardChanges: () => void;
}

// ============================================
// Store 创建
// ============================================

export const useSettingsStore = create<SettingsState>()(
  persist(
    (set, get) => ({
      ...defaultSettings,
      settingsOpen: false,
      pendingSettings: null,
      hasUnsavedChanges: false,
      
      // 弹窗控制
      openSettings: () => {
        const state = get();
        set({
          settingsOpen: true,
          pendingSettings: {
            theme: state.theme,
            language: state.language,
            defaultContractMultiplier: state.defaultContractMultiplier,
            slippageBps: state.slippageBps,
            gatewayUrl: state.gatewayUrl,
            debugMode: state.debugMode,
            shortcutsHint: state.shortcutsHint,
            notifications: state.notifications,
          },
          hasUnsavedChanges: false,
        });
      },
      closeSettings: () => set({ settingsOpen: false }),
      toggleSettings: () => set(state => ({ settingsOpen: !state.settingsOpen })),
      
      // 更新设置（仅更新 pending）
      updateSettings: (newSettings) => set(state => ({
        pendingSettings: state.pendingSettings ? { ...state.pendingSettings, ...newSettings } : null,
        hasUnsavedChanges: true,
      })),
      
      // 保存并关闭
      saveAndClose: () => {
        const { pendingSettings } = get();
        if (pendingSettings) {
          set({
            ...pendingSettings,
            settingsOpen: false,
            pendingSettings: null,
            hasUnsavedChanges: false,
          });
        }
      },
      
      // 放弃更改
      discardChanges: () => set({
        settingsOpen: false,
        pendingSettings: null,
        hasUnsavedChanges: false,
      }),
      
      // 重置
      resetSettings: () => {
        const state = get();
        set({
          ...defaultSettings,
          pendingSettings: { ...defaultSettings },
          hasUnsavedChanges: true,
        });
      },
    }),
    {
      name: 'nemt-settings-storage',
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        theme: state.theme,
        language: state.language,
        defaultContractMultiplier: state.defaultContractMultiplier,
        slippageBps: state.slippageBps,
        gatewayUrl: state.gatewayUrl,
        debugMode: state.debugMode,
        shortcutsHint: state.shortcutsHint,
        notifications: state.notifications,
      }),
    }
  )
);

// ============================================
// 便捷 Hooks
// ============================================

export const useSettingsTheme = () => useSettingsStore(state => state.theme);
export const useGatewayUrl = () => useSettingsStore(state => state.gatewayUrl);
export const useDebugMode = () => useSettingsStore(state => state.debugMode);
