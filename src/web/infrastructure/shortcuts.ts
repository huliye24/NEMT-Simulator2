/**
 * Copyright 2026 NEMT Lab
 *
 * 键盘快捷键系统
 */

import { useEffect, useCallback, useRef } from 'react';

// ============================================
// 类型定义
// ============================================

export interface Shortcut {
  /** 快捷键描述 */
  description: string;
  /** 快捷键 (如 'CmdOrCtrl+K') */
  shortcut: string;
  /** 分类 */
  category: string;
  /** 执行函数 */
  action: () => void;
  /** 是否全局 (页面任何位置都响应) */
  global?: boolean;
  /** 优先级 */
  priority?: number;
}

export interface ShortcutGroup {
  name: string;
  shortcuts: Shortcut[];
}

// ============================================
// 快捷键解析
// ============================================

export function parseShortcut(shortcut: string): {
  cmdOrCtrl: boolean;
  shift: boolean;
  alt: boolean;
  key: string;
} {
  const parts = shortcut.toLowerCase().split('+');
  return {
    cmdOrCtrl: parts.includes('cmdorctrl'),
    shift: parts.includes('shift'),
    alt: parts.includes('alt'),
    key: parts[parts.length - 1]
  };
}

// ============================================
// 快捷键匹配
// ============================================

export function matchesShortcut(
  event: KeyboardEvent,
  shortcut: string
): boolean {
  const parsed = parseShortcut(shortcut);

  const isMac = navigator.platform.toUpperCase().indexOf('MAC') >= 0;

  // 检查修饰键
  const cmdOrCtrlMatch = parsed.cmdOrCtrl
    ? (isMac ? event.metaKey : event.ctrlKey)
    : (!event.metaKey && !event.ctrlKey);

  const shiftMatch = parsed.shift === event.shiftKey;
  const altMatch = parsed.alt === event.altKey;

  // 检查主键
  const keyMatch = event.key.toLowerCase() === parsed.key;

  return cmdOrCtrlMatch && shiftMatch && altMatch && keyMatch;
}

// ============================================
// 快捷键管理 Hook
// ============================================

export function useKeyboardShortcuts(shortcuts: Shortcut[]): void {
  useEffect(() => {
    const handler = (event: KeyboardEvent) => {
      // 忽略在输入框中的按键
      const target = event.target as HTMLElement;
      const isInput = target.tagName === 'INPUT'
        || target.tagName === 'TEXTAREA'
        || target.isContentEditable;

      for (const shortcut of shortcuts) {
        if (matchesShortcut(event, shortcut.shortcut)) {
          // 如果是全局快捷键或在非输入区域
          if (shortcut.global || !isInput) {
            event.preventDefault();
            event.stopPropagation();
            shortcut.action();
            break;
          }
        }
      }
    };

    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [shortcuts]);
}

// ============================================
// 快捷键 Provider
// ============================================

type ShortcutHandler = (shortcut: Shortcut) => void;

class ShortcutManager {
  private shortcuts: Map<string, Shortcut> = new Map();
  private listeners: Set<ShortcutHandler> = new Set();

  /**
   * 注册快捷键
   */
  register(shortcut: Shortcut): void {
    const key = this.getKey(shortcut.shortcut);
    this.shortcuts.set(key, shortcut);
    this.notifyListeners(shortcut);
  }

  /**
   * 注销快捷键
   */
  unregister(shortcutKey: string): void {
    const key = this.getKey(shortcutKey);
    this.shortcuts.delete(key);
  }

  /**
   * 获取快捷键
   */
  get(shortcutKey: string): Shortcut | undefined {
    return this.shortcuts.get(this.getKey(shortcutKey));
  }

  /**
   * 获取所有快捷键
   */
  getAll(): Shortcut[] {
    return Array.from(this.shortcuts.values());
  }

  /**
   * 按分类获取
   */
  getByCategory(category: string): Shortcut[] {
    return this.getAll().filter(s => s.category === category);
  }

  /**
   * 处理按键
   */
  handleKeyDown(event: KeyboardEvent): boolean {
    for (const shortcut of this.shortcuts.values()) {
      if (matchesShortcut(event, shortcut.shortcut)) {
        const target = event.target as HTMLElement;
        const isInput = target.tagName === 'INPUT'
          || target.tagName === 'TEXTAREA'
          || target.isContentEditable;

        if (shortcut.global || !isInput) {
          event.preventDefault();
          shortcut.action();
          return true;
        }
      }
    }
    return false;
  }

  /**
   * 生成唯一键
   */
  private getKey(shortcut: string): string {
    return shortcut.toLowerCase().replace(/\s+/g, '');
  }

  /**
   * 订阅变化
   */
  subscribe(listener: ShortcutHandler): () => void {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }

  /**
   * 通知监听器
   */
  private notifyListeners(shortcut: Shortcut): void {
    this.listeners.forEach(listener => listener(shortcut));
  }

  /**
   * 清空所有快捷键
   */
  clear(): void {
    this.shortcuts.clear();
  }
}

// 全局快捷键管理器
export const shortcutManager = new ShortcutManager();

// ============================================
// 常用快捷键定义
// ============================================

export const COMMON_SHORTCUTS = {
  // 全局
  COMMAND_PALETTE: {
    shortcut: 'CmdOrCtrl+K',
    description: '打开命令面板',
    category: '全局',
    global: true
  },
  QUICK_SEARCH: {
    shortcut: 'CmdOrCtrl+P',
    description: '快速搜索',
    category: '全局',
    global: true
  },
  SETTINGS: {
    shortcut: 'CmdOrCtrl+,',
    description: '打开设置',
    category: '全局',
    global: true
  },
  HELP: {
    shortcut: 'CmdOrCtrl+?',
    description: '显示帮助',
    category: '全局',
    global: true
  },

  // 导航
  STRATEGIES: {
    shortcut: 'G S',
    description: '跳转到策略市场',
    category: '导航',
    global: true
  },
  CONTAINERS: {
    shortcut: 'G C',
    description: '跳转到容器管理',
    category: '导航',
    global: true
  },
  CAPSULES: {
    shortcut: 'G M',
    description: '跳转到胶囊市场',
    category: '导航',
    global: true
  },

  // 操作
  NEW_STRATEGY: {
    shortcut: 'CmdOrCtrl+N',
    description: '新建策略',
    category: '操作',
    global: true
  },
  SAVE: {
    shortcut: 'CmdOrCtrl+S',
    description: '保存',
    category: '操作',
    global: true
  },
  UNDO: {
    shortcut: 'CmdOrCtrl+Z',
    description: '撤销',
    category: '操作',
    global: true
  },
  REDO: {
    shortcut: 'CmdOrCtrl+Shift+Z',
    description: '重做',
    category: '操作',
    global: true
  },

  // 视图
  TOGGLE_SIDEBAR: {
    shortcut: 'CmdOrCtrl+B',
    description: '切换侧边栏',
    category: '视图',
    global: true
  },
  FULLSCREEN: {
    shortcut: 'F11',
    description: '全屏',
    category: '视图',
    global: true
  },
  ZOOM_IN: {
    shortcut: 'CmdOrCtrl+=',
    description: '放大',
    category: '视图',
    global: true
  },
  ZOOM_OUT: {
    shortcut: 'CmdOrCtrl+-',
    description: '缩小',
    category: '视图',
    global: true
  },

  // ESC
  CLOSE_MODAL: {
    shortcut: 'Escape',
    description: '关闭弹窗',
    category: '操作',
    global: true
  }
};

// ============================================
// 快捷键 Hook
// ============================================

export function useShortcuts(shortcuts: Shortcut[]): void {
  useEffect(() => {
    shortcuts.forEach(shortcut => {
      shortcutManager.register(shortcut);
    });

    return () => {
      shortcuts.forEach(shortcut => {
        shortcutManager.unregister(shortcut.shortcut);
      });
    };
  }, [shortcuts]);
}

// ============================================
// 快捷键提示组件数据
// ============================================

export function getShortcutGroups(shortcuts: Shortcut[]): ShortcutGroup[] {
  const groups: Map<string, Shortcut[]> = new Map();

  shortcuts.forEach(shortcut => {
    const existing = groups.get(shortcut.category) || [];
    existing.push(shortcut);
    groups.set(shortcut.category, existing);
  });

  return Array.from(groups.entries()).map(([name, shortcuts]) => ({
    name,
    shortcuts
  }));
}

// ============================================
// 格式化快捷键显示
// ============================================

export function formatShortcut(shortcut: string): string {
  const isMac = navigator.platform.toUpperCase().indexOf('MAC') >= 0;

  return shortcut
    .replace(/CmdOrCtrl/g, isMac ? '⌘' : 'Ctrl')
    .replace(/Shift/g, isMac ? '⇧' : 'Shift')
    .replace(/Alt/g, isMac ? '⌥' : 'Alt')
    .replace(/\+/g, ' + ');
}
