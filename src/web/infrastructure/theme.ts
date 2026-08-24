/**
 * Copyright 2026 NEMT Lab
 *
 * 主题系统 - CSS 变量 + 动态主题切换
 */

import { useEffect, useCallback } from 'react';
import { usePlatformStore } from './store';

// ============================================
// 主题类型
// ============================================

export type Theme = 'dark' | 'light' | 'system';
export type ResolvedTheme = 'dark' | 'light';

export interface ThemeColors {
  // 背景
  bgPrimary: string;
  bgSecondary: string;
  bgTertiary: string;
  bgElevated: string;

  // 边框
  borderPrimary: string;
  borderSecondary: string;

  // 文本
  textPrimary: string;
  textSecondary: string;
  textTertiary: string;
  textInverse: string;

  // 强调色
  accent: string;
  accentHover: string;

  // 语义色
  success: string;
  warning: string;
  error: string;
  info: string;

  // 状态
  successBg: string;
  warningBg: string;
  errorBg: string;
  infoBg: string;
}

// ============================================
// 预设主题
// ============================================

export const darkTheme: ThemeColors = {
  bgPrimary: '#020617',
  bgSecondary: '#0f172a',
  bgTertiary: '#1e293b',
  bgElevated: '#334155',

  borderPrimary: '#334155',
  borderSecondary: '#475569',

  textPrimary: '#e2e8f0',
  textSecondary: '#94a3b8',
  textTertiary: '#64748b',
  textInverse: '#020617',

  accent: '#8b5cf6',
  accentHover: '#a78bfa',

  success: '#10b981',
  warning: '#f59e0b',
  error: '#ef4444',
  info: '#3b82f6',

  successBg: 'rgba(16, 185, 129, 0.1)',
  warningBg: 'rgba(245, 158, 11, 0.1)',
  errorBg: 'rgba(239, 68, 68, 0.1)',
  infoBg: 'rgba(59, 130, 246, 0.1)',
};

export const lightTheme: ThemeColors = {
  bgPrimary: '#ffffff',
  bgSecondary: '#f8fafc',
  bgTertiary: '#f1f5f9',
  bgElevated: '#e2e8f0',

  borderPrimary: '#e2e8f0',
  borderSecondary: '#cbd5e1',

  textPrimary: '#0f172a',
  textSecondary: '#475569',
  textTertiary: '#94a3b8',
  textInverse: '#ffffff',

  accent: '#7c3aed',
  accentHover: '#6d28d9',

  success: '#059669',
  warning: '#d97706',
  error: '#dc2626',
  info: '#2563eb',

  successBg: 'rgba(5, 150, 105, 0.1)',
  warningBg: 'rgba(217, 119, 6, 0.1)',
  errorBg: 'rgba(220, 38, 38, 0.1)',
  infoBg: 'rgba(37, 99, 235, 0.1)',
};

// ============================================
// 主题管理器
// ============================================

class ThemeManager {
  private currentTheme: Theme = 'dark';
  private listeners: Set<(theme: ResolvedTheme) => void> = new Set();

  constructor() {
    // 初始化
    this.init();

    // 监听系统主题变化
    if (typeof window !== 'undefined') {
      window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => {
        this.notifyListeners();
      });
    }
  }

  private init(): void {
    // 从 localStorage 读取保存的主题
    const saved = localStorage.getItem('nemt-theme') as Theme | null;
    if (saved) {
      this.currentTheme = saved;
    }

    // 应用主题
    this.applyTheme();
  }

  setTheme(theme: Theme): void {
    this.currentTheme = theme;
    localStorage.setItem('nemt-theme', theme);
    this.applyTheme();
    this.notifyListeners();
  }

  getTheme(): Theme {
    return this.currentTheme;
  }

  getResolvedTheme(): ResolvedTheme {
    if (this.currentTheme === 'system') {
      if (typeof window !== 'undefined') {
        return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
      }
      return 'dark';
    }
    return this.currentTheme;
  }

  getColors(): ThemeColors {
    const resolved = this.getResolvedTheme();
    return resolved === 'dark' ? darkTheme : lightTheme;
  }

  subscribe(listener: (theme: ResolvedTheme) => void): () => void {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }

  private applyTheme(): void {
    const resolved = this.getResolvedTheme();
    const colors = resolved === 'dark' ? darkTheme : lightTheme;

    // 设置 CSS 变量
    if (typeof document !== 'undefined') {
      const root = document.documentElement;

      // 背景
      root.style.setProperty('--bg-primary', colors.bgPrimary);
      root.style.setProperty('--bg-secondary', colors.bgSecondary);
      root.style.setProperty('--bg-tertiary', colors.bgTertiary);
      root.style.setProperty('--bg-elevated', colors.bgElevated);

      // 边框
      root.style.setProperty('--border-primary', colors.borderPrimary);
      root.style.setProperty('--border-secondary', colors.borderSecondary);

      // 文本
      root.style.setProperty('--text-primary', colors.textPrimary);
      root.style.setProperty('--text-secondary', colors.textSecondary);
      root.style.setProperty('--text-tertiary', colors.textTertiary);
      root.style.setProperty('--text-inverse', colors.textInverse);

      // 强调色
      root.style.setProperty('--accent', colors.accent);
      root.style.setProperty('--accent-hover', colors.accentHover);

      // 语义色
      root.style.setProperty('--success', colors.success);
      root.style.setProperty('--warning', colors.warning);
      root.style.setProperty('--error', colors.error);
      root.style.setProperty('--info', colors.info);

      // 状态色
      root.style.setProperty('--success-bg', colors.successBg);
      root.style.setProperty('--warning-bg', colors.warningBg);
      root.style.setProperty('--error-bg', colors.errorBg);
      root.style.setProperty('--info-bg', colors.infoBg);

      // 设置 data 属性
      root.setAttribute('data-theme', resolved);
    }
  }

  private notifyListeners(): void {
    const resolved = this.getResolvedTheme();
    this.listeners.forEach(listener => listener(resolved));
  }
}

// 全局主题管理器
export const themeManager = new ThemeManager();

// ============================================
// React Hook
// ============================================

export function useTheme() {
  const { theme: storeTheme, setTheme: storeSetTheme } = usePlatformStore();

  useEffect(() => {
    themeManager.setTheme(storeTheme);
  }, [storeTheme]);

  const setTheme = useCallback((theme: Theme) => {
    storeSetTheme(theme);
    themeManager.setTheme(theme);
  }, [storeSetTheme]);

  const colors = themeManager.getColors();
  const resolvedTheme = themeManager.getResolvedTheme();

  return {
    theme: storeTheme,
    resolvedTheme,
    colors,
    setTheme,
    toggleTheme: () => {
      const next = storeTheme === 'dark' ? 'light' : storeTheme === 'light' ? 'system' : 'dark';
      setTheme(next);
    }
  };
}

// ============================================
// 主题切换动画
// ============================================

export function withThemeTransition(
  callback: () => void,
  duration = 200
): void {
  const root = document.documentElement;

  // 添加过渡
  root.style.transition = `background-color ${duration}ms ease, color ${duration}ms ease`;

  // 执行回调
  callback();

  // 移除过渡
  setTimeout(() => {
    root.style.transition = '';
  }, duration);
}

// ============================================
// CSS 变量工具类
// ============================================

export const themeClasses = {
  // 背景类
  bg: {
    primary: 'bg-primary',
    secondary: 'bg-secondary',
    tertiary: 'bg-tertiary',
    elevated: 'bg-elevated'
  },

  // 文本类
  text: {
    primary: 'text-primary',
    secondary: 'text-secondary',
    tertiary: 'text-tertiary'
  },

  // 边框类
  border: {
    primary: 'border-primary',
    secondary: 'border-secondary'
  },

  // 状态类
  state: {
    success: 'state-success',
    warning: 'state-warning',
    error: 'state-error',
    info: 'state-info'
  }
};

// ============================================
// 全局样式注入
// ============================================

export function injectThemeStyles(): void {
  if (typeof document === 'undefined') return;

  const styleId = 'nemt-theme-styles';
  if (document.getElementById(styleId)) return;

  const style = document.createElement('style');
  style.id = styleId;
  style.textContent = `
    :root {
      /* 暗色主题 (默认) */
      --bg-primary: #020617;
      --bg-secondary: #0f172a;
      --bg-tertiary: #1e293b;
      --bg-elevated: #334155;
      --border-primary: #334155;
      --border-secondary: #475569;
      --text-primary: #e2e8f0;
      --text-secondary: #94a3b8;
      --text-tertiary: #64748b;
      --text-inverse: #020617;
      --accent: #8b5cf6;
      --accent-hover: #a78bfa;
      --success: #10b981;
      --warning: #f59e0b;
      --error: #ef4444;
      --info: #3b82f6;
    }

    [data-theme="light"] {
      --bg-primary: #ffffff;
      --bg-secondary: #f8fafc;
      --bg-tertiary: #f1f5f9;
      --bg-elevated: #e2e8f0;
      --border-primary: #e2e8f0;
      --border-secondary: #cbd5e1;
      --text-primary: #0f172a;
      --text-secondary: #475569;
      --text-tertiary: #94a3b8;
      --text-inverse: #ffffff;
      --accent: #7c3aed;
      --accent-hover: #6d28d9;
      --success: #059669;
      --warning: #d97706;
      --error: #dc2626;
      --info: #2563eb;
    }

    /* 过渡效果 */
    :root, [data-theme] {
      transition: background-color 0.2s ease, color 0.2s ease, border-color 0.2s ease;
    }

    /* 工具类 */
    .bg-primary { background-color: var(--bg-primary); }
    .bg-secondary { background-color: var(--bg-secondary); }
    .bg-tertiary { background-color: var(--bg-tertiary); }
    .bg-elevated { background-color: var(--bg-elevated); }

    .text-primary { color: var(--text-primary); }
    .text-secondary { color: var(--text-secondary); }
    .text-tertiary { color: var(--text-tertiary); }

    .border-primary { border-color: var(--border-primary); }
    .border-secondary { border-color: var(--border-secondary); }

    .accent { color: var(--accent); }
    .accent-bg { background-color: var(--accent); }

    .state-success { color: var(--success); }
    .state-warning { color: var(--warning); }
    .state-error { color: var(--error); }
    .state-info { color: var(--info); }
  `;

  document.head.appendChild(style);
}
