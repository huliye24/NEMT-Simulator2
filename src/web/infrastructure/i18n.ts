/**
 * Copyright 2026 NEMT Lab
 *
 * 国际化系统 - react-i18next 集成
 */

import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';

// ============================================
// 语言包
// ============================================

const resources = {
  'zh-CN': {
    translation: {
      // 通用
      common: {
        save: '保存',
        cancel: '取消',
        delete: '删除',
        edit: '编辑',
        create: '创建',
        search: '搜索',
        loading: '加载中...',
        noData: '暂无数据',
        confirm: '确认',
        success: '成功',
        error: '错误',
        warning: '警告',
        info: '信息'
      },

      // 导航
      nav: {
        strategies: '策略市场',
        containers: '容器管理',
        capsules: '胶囊市场',
        monitor: '监控面板',
        terminal: '终端',
        market: '数据市场',
        settings: '设置',
        help: '帮助'
      },

      // 策略
      strategy: {
        name: '策略名称',
        author: '作者',
        description: '描述',
        status: '状态',
        version: '版本',
        tags: '标签',
        metrics: '指标',
        totalTrades: '交易数',
        winRate: '胜率',
        totalPnL: '盈亏',
        sharpeRatio: '夏普比率',
        createStrategy: '创建策略',
        editStrategy: '编辑策略',
        deleteStrategy: '删除策略',
        startStrategy: '启动策略',
        stopStrategy: '停止策略'
      },

      // 状态
      status: {
        draft: '草稿',
        testing: '测试中',
        running: '运行中',
        paused: '已暂停',
        archived: '已归档'
      },

      // 胶囊
      capsule: {
        market: '市场胶囊',
        signal: '信号胶囊',
        risk: '风控胶囊',
        execution: '执行胶囊',
        brain: '大脑胶囊',
        monitor: '监控胶囊',
        instances: '实例',
        active: '在线',
        inactive: '离线',
        error: '错误'
      },

      // 平台
      platform: {
        title: 'NEMT Platform',
        subtitle: '策略容器平台',
        tagline: '抖音不生产视频，NEMT 不生产策略',
        onlineStrategies: '在线策略',
        containerInstances: '容器实例',
        todayTrades: '今日交易'
      },

      // 快捷键
      shortcuts: {
        title: '快捷键',
        commandPalette: '命令面板',
        newStrategy: '新建策略',
        save: '保存',
        undo: '撤销',
        redo: '重做',
        toggleSidebar: '切换侧边栏',
        fullscreen: '全屏'
      },

      // 错误
      error: {
        title: '出错了',
        fatal: '致命错误',
        critical: '严重错误',
        warning: '警告',
        retry: '重试',
        goHome: '返回首页',
        copyError: '复制错误',
        errorId: '错误 ID'
      },

      // 设置
      settings: {
        title: '设置',
        theme: '主题',
        dark: '深色',
        light: '浅色',
        system: '跟随系统',
        language: '语言',
        notifications: '通知'
      }
    }
  },

  'en-US': {
    translation: {
      // General
      common: {
        save: 'Save',
        cancel: 'Cancel',
        delete: 'Delete',
        edit: 'Edit',
        create: 'Create',
        search: 'Search',
        loading: 'Loading...',
        noData: 'No data',
        confirm: 'Confirm',
        success: 'Success',
        error: 'Error',
        warning: 'Warning',
        info: 'Info'
      },

      // Navigation
      nav: {
        strategies: 'Strategies',
        containers: 'Containers',
        capsules: 'Capsules',
        monitor: 'Monitor',
        terminal: 'Terminal',
        market: 'Data Market',
        settings: 'Settings',
        help: 'Help'
      },

      // Strategy
      strategy: {
        name: 'Strategy Name',
        author: 'Author',
        description: 'Description',
        status: 'Status',
        version: 'Version',
        tags: 'Tags',
        metrics: 'Metrics',
        totalTrades: 'Total Trades',
        winRate: 'Win Rate',
        totalPnL: 'P&L',
        sharpeRatio: 'Sharpe Ratio',
        createStrategy: 'Create Strategy',
        editStrategy: 'Edit Strategy',
        deleteStrategy: 'Delete Strategy',
        startStrategy: 'Start Strategy',
        stopStrategy: 'Stop Strategy'
      },

      // Status
      status: {
        draft: 'Draft',
        testing: 'Testing',
        running: 'Running',
        paused: 'Paused',
        archived: 'Archived'
      },

      // Capsule
      capsule: {
        market: 'Market Capsule',
        signal: 'Signal Capsule',
        risk: 'Risk Capsule',
        execution: 'Execution Capsule',
        brain: 'Brain Capsule',
        monitor: 'Monitor Capsule',
        instances: 'Instances',
        active: 'Active',
        inactive: 'Inactive',
        error: 'Error'
      },

      // Platform
      platform: {
        title: 'NEMT Platform',
        subtitle: 'Strategy Container Platform',
        tagline: 'TikTok doesn\'t create videos, NEMT doesn\'t create strategies',
        onlineStrategies: 'Online Strategies',
        containerInstances: 'Container Instances',
        todayTrades: 'Today\'s Trades'
      },

      // Shortcuts
      shortcuts: {
        title: 'Shortcuts',
        commandPalette: 'Command Palette',
        newStrategy: 'New Strategy',
        save: 'Save',
        undo: 'Undo',
        redo: 'Redo',
        toggleSidebar: 'Toggle Sidebar',
        fullscreen: 'Fullscreen'
      },

      // Error
      error: {
        title: 'Something went wrong',
        fatal: 'Fatal Error',
        critical: 'Critical Error',
        warning: 'Warning',
        retry: 'Retry',
        goHome: 'Go Home',
        copyError: 'Copy Error',
        errorId: 'Error ID'
      },

      // Settings
      settings: {
        title: 'Settings',
        theme: 'Theme',
        dark: 'Dark',
        light: 'Light',
        system: 'System',
        language: 'Language',
        notifications: 'Notifications'
      }
    }
  }
};

// ============================================
// 初始化 i18next
// ============================================

i18n
  .use(initReactI18next)
  .init({
    resources,
    lng: localStorage.getItem('nemt-language') || 'zh-CN',
    fallbackLng: 'zh-CN',
    interpolation: {
      escapeValue: false
    },
    react: {
      useSuspense: false
    }
  });

// ============================================
// 语言切换工具
// ============================================

export function changeLanguage(lang: string): void {
  localStorage.setItem('nemt-language', lang);
  i18n.changeLanguage(lang);
}

export function getCurrentLanguage(): string {
  return i18n.language;
}

export function getAvailableLanguages(): { code: string; name: string }[] {
  return [
    { code: 'zh-CN', name: '简体中文' },
    { code: 'en-US', name: 'English' }
  ];
}

// ============================================
// 格式化工具
// ============================================

export function formatNumber(value: number, options?: Intl.NumberFormatOptions): string {
  return new Intl.NumberFormat(i18n.language, options).format(value);
}

export function formatCurrency(value: number, currency = 'USD'): string {
  return new Intl.NumberFormat(i18n.language, {
    style: 'currency',
    currency
  }).format(value);
}

export function formatPercent(value: number, decimals = 1): string {
  return new Intl.NumberFormat(i18n.language, {
    style: 'percent',
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals
  }).format(value);
}

export function formatDate(date: Date | string | number, options?: Intl.DateTimeFormatOptions): string {
  const d = typeof date === 'string' || typeof date === 'number' ? new Date(date) : date;
  return new Intl.DateTimeFormat(i18n.language, {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    ...options
  }).format(d);
}

export function formatRelativeTime(date: Date | string | number): string {
  const d = typeof date === 'string' || typeof date === 'number' ? new Date(date) : date;
  const now = new Date();
  const diff = now.getTime() - d.getTime();

  const minutes = Math.floor(diff / 60000);
  const hours = Math.floor(diff / 3600000);
  const days = Math.floor(diff / 86400000);

  const rtf = new Intl.RelativeTimeFormat(i18n.language, { numeric: 'auto' });

  if (minutes < 60) {
    return rtf.format(-minutes, 'minute');
  } else if (hours < 24) {
    return rtf.format(-hours, 'hour');
  } else {
    return rtf.format(-days, 'day');
  }
}

// ============================================
// Hooks
// ============================================

export { useTranslation } from 'react-i18next';

export function useFormat() {
  return {
    number: formatNumber,
    currency: formatCurrency,
    percent: formatPercent,
    date: formatDate,
    relativeTime: formatRelativeTime
  };
}

export default i18n;
