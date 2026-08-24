/**
 * Copyright 2026 NEMT Lab
 *
 * 上下文菜单系统 - 右键菜单
 */

import React, { useState, useEffect, useCallback, useRef } from 'react';
import { createPortal } from 'react-dom';

// ============================================
// 类型定义
// ============================================

export interface MenuItem {
  id: string;
  label: string;
  icon?: React.ReactNode;
  shortcut?: string;
  disabled?: boolean;
  hidden?: boolean;
  danger?: boolean;
  separator?: boolean;
  children?: MenuItem[];
}

export interface ContextMenuProps {
  items: MenuItem[];
  onSelect: (itemId: string) => void;
  onClose: () => void;
  x: number;
  y: number;
  parentMenuRef?: React.RefObject<HTMLElement>;
}

export interface ContextMenuState {
  open: boolean;
  x: number;
  y: number;
  items: MenuItem[];
  targetId?: string;
}

// ============================================
// 菜单项组件
// ============================================

const MenuItemComponent: React.FC<{
  item: MenuItem;
  onSelect: (id: string) => void;
  onHover: (id: string | null) => void;
  isHighlighted: boolean;
  isMac: boolean;
}> = ({ item, onSelect, onHover, isHighlighted, isMac }) => {
  if (item.separator) {
    return (
      <div
        style={{
          height: '1px',
          background: 'var(--border-primary, #334155)',
          margin: '4px 8px'
        }}
      />
    );
  }

  if (item.hidden) return null;

  const formatShortcut = (shortcut: string) => {
    return shortcut
      .replace(/CmdOrCtrl/g, isMac ? '⌘' : 'Ctrl')
      .replace(/Shift/g, '⇧')
      .replace(/Alt/g, '⌥')
      .replace(/\+/g, '');
  };

  return (
    <div
      onClick={(e) => {
        e.stopPropagation();
        if (!item.disabled && !item.children) {
          onSelect(item.id);
        }
      }}
      onMouseEnter={() => onHover(item.id)}
      onMouseLeave={() => onHover(null)}
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: '12px',
        padding: '8px 12px',
        cursor: item.disabled ? 'default' : 'pointer',
        background: isHighlighted
          ? (item.danger ? 'rgba(239, 68, 68, 0.15)' : 'rgba(139, 92, 246, 0.15)')
          : 'transparent',
        color: item.disabled
          ? 'var(--text-tertiary, #64748b)'
          : item.danger
            ? '#ef4444'
            : 'var(--text-primary, #e2e8f0)',
        borderRadius: '6px',
        margin: '2px 4px',
        transition: 'background 0.1s'
      }}
    >
      {item.icon && (
        <span style={{
          display: 'flex',
          alignItems: 'center',
          opacity: item.disabled ? 0.5 : 1
        }}>
          {item.icon}
        </span>
      )}
      <span style={{
        flex: 1,
        fontSize: '13px',
        opacity: item.disabled ? 0.5 : 1
      }}>
        {item.label}
      </span>
      {item.shortcut && (
        <span style={{
          fontSize: '11px',
          color: 'var(--text-tertiary, #64748b)',
          opacity: item.disabled ? 0.5 : 1
        }}>
          {formatShortcut(item.shortcut)}
        </span>
      )}
      {item.children && (
        <svg
          width="12"
          height="12"
          viewBox="0 0 12 12"
          fill="currentColor"
          style={{ opacity: 0.5 }}
        >
          <path d="M4.5 2.5L8.5 6L4.5 9.5" stroke="currentColor" strokeWidth="1.5" fill="none" />
        </svg>
      )}
    </div>
  );
};

// ============================================
// 子菜单组件
// ============================================

const SubMenu: React.FC<{
  items: MenuItem[];
  parentX: number;
  parentY: number;
  onSelect: (id: string) => void;
  onClose: () => void;
}> = ({ items, parentX, parentY, onSelect, onClose }) => {
  const [highlightedId, setHighlightedId] = useState<string | null>(null);
  const [openSubMenuId, setOpenSubMenuId] = useState<string | null>(null);
  const menuRef = useRef<HTMLDivElement>(null);
  const isMac = navigator.platform.toUpperCase().indexOf('MAC') >= 0;

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        onClose();
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [onClose]);

  // 计算子菜单位置
  const subMenuItems = items.filter(i => i.id === openSubMenuId && i.children);
  const subMenuX = parentX + 200;
  const subMenuY = parentY + (items.findIndex(i => i.id === openSubMenuId) * 36);

  return (
    <div
      ref={menuRef}
      style={{
        position: 'fixed',
        left: parentX,
        top: parentY,
        minWidth: '200px',
        background: 'var(--bg-secondary, #0f172a)',
        border: '1px solid var(--border-primary, #334155)',
        borderRadius: '12px',
        padding: '6px',
        boxShadow: '0 10px 40px rgba(0,0,0,0.4)',
        zIndex: 10001,
        backdropFilter: 'blur(12px)'
      }}
    >
      {items.map(item => (
        <MenuItemComponent
          key={item.id}
          item={item}
          onSelect={(id) => {
            if (item.children) {
              setOpenSubMenuId(id === openSubMenuId ? null : id);
            } else {
              onSelect(id);
            }
          }}
          onHover={(id) => {
            setHighlightedId(id);
            if (id) {
              const item = items.find(i => i.id === id);
              if (item?.children) {
                setOpenSubMenuId(id);
              }
            }
          }}
          isHighlighted={highlightedId === item.id}
          isMac={isMac}
        />
      ))}

      {/* 渲染打开的子菜单 */}
      {subMenuItems.map(subItem => (
        <SubMenu
          key={`sub-${subItem.id}`}
          items={subItem.children!}
          parentX={subMenuX}
          parentY={subMenuY}
          onSelect={onSelect}
          onClose={onClose}
        />
      ))}
    </div>
  );
};

// ============================================
// 上下文菜单组件
// ============================================

export const ContextMenu: React.FC<ContextMenuProps> = ({
  items,
  onSelect,
  onClose,
  x,
  y,
  parentMenuRef
}) => {
  const [highlightedId, setHighlightedId] = useState<string | null>(null);
  const menuRef = useRef<HTMLDivElement>(null);
  const isMac = navigator.platform.toUpperCase().indexOf('MAC') >= 0;

  // 调整菜单位置，确保不超出视口
  const adjustedPosition = useCallback(() => {
    const menuWidth = 220;
    const menuHeight = Math.min(items.length * 36 + 12, 400);

    let adjustedX = x;
    let adjustedY = y;

    if (typeof window !== 'undefined') {
      if (x + menuWidth > window.innerWidth) {
        adjustedX = window.innerWidth - menuWidth - 10;
      }
      if (y + menuHeight > window.innerHeight) {
        adjustedY = window.innerHeight - menuHeight - 10;
      }
    }

    return { x: adjustedX, y: adjustedY };
  }, [x, y, items.length]);

  const { x: adjustedX, y: adjustedY } = adjustedPosition();

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        onClose();
      }
    };

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    document.addEventListener('keydown', handleKeyDown);

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [onClose]);

  const handleSelect = useCallback((id: string) => {
    onSelect(id);
    onClose();
  }, [onSelect, onClose]);

  const handleHover = useCallback((id: string | null) => {
    setHighlightedId(id);
  }, []);

  return createPortal(
    <div
      ref={menuRef}
      style={{
        position: 'fixed',
        left: adjustedX,
        top: adjustedY,
        minWidth: '220px',
        background: 'var(--bg-secondary, #0f172a)',
        border: '1px solid var(--border-primary, #334155)',
        borderRadius: '12px',
        padding: '6px',
        boxShadow: '0 10px 40px rgba(0,0,0,0.4)',
        zIndex: 10000,
        backdropFilter: 'blur(12px)'
      }}
    >
      {items.map(item => (
        <MenuItemComponent
          key={item.id}
          item={item}
          onSelect={handleSelect}
          onHover={handleHover}
          isHighlighted={highlightedId === item.id}
          isMac={isMac}
        />
      ))}
    </div>,
    document.body
  );
};

// ============================================
// 上下文菜单 Hook
// ============================================

export function useContextMenu<T = any>() {
  const [menuState, setMenuState] = useState<ContextMenuState>({
    open: false,
    x: 0,
    y: 0,
    items: []
  });

  const targetRef = useRef<T | null>(null);

  const openMenu = useCallback((
    event: React.MouseEvent,
    items: MenuItem[],
    target?: T
  ) => {
    event.preventDefault();
    event.stopPropagation();

    targetRef.current = target || null;

    setMenuState({
      open: true,
      x: event.clientX,
      y: event.clientY,
      items
    });
  }, []);

  const closeMenu = useCallback(() => {
    setMenuState(prev => ({ ...prev, open: false }));
  }, []);

  const handleSelect = useCallback((itemId: string) => {
    return itemId;
  }, []);

  return {
    isOpen: menuState.open,
    position: { x: menuState.x, y: menuState.y },
    items: menuState.items,
    target: targetRef.current,
    openMenu,
    closeMenu,
    handleSelect
  };
}

// ============================================
// ContextMenuProvider
// ============================================

interface ContextMenuProviderProps {
  children: React.ReactNode;
}

const ContextMenuContext = React.createContext<{
  openMenu: (event: React.MouseEvent, items: MenuItem[], target?: any) => void;
} | null>(null);

export const ContextMenuProvider: React.FC<ContextMenuProviderProps> = ({ children }) => {
  const [menuState, setMenuState] = useState<ContextMenuState>({
    open: false,
    x: 0,
    y: 0,
    items: []
  });

  const openMenu = useCallback((
    event: React.MouseEvent,
    items: MenuItem[],
    target?: any
  ) => {
    event.preventDefault();
    event.stopPropagation();

    setMenuState({
      open: true,
      x: event.clientX,
      y: event.clientY,
      items
    });
  }, []);

  const closeMenu = useCallback(() => {
    setMenuState(prev => ({ ...prev, open: false }));
  }, []);

  const handleSelect = useCallback((itemId: string) => {
    closeMenu();
    return itemId;
  }, [closeMenu]);

  return (
    <ContextMenuContext.Provider value={{ openMenu }}>
      {children}
      {menuState.open && (
        <ContextMenu
          items={menuState.items}
          onSelect={handleSelect}
          onClose={closeMenu}
          x={menuState.x}
          y={menuState.y}
        />
      )}
    </ContextMenuContext.Provider>
  );
};

// ============================================
// 常用菜单构建器
// ============================================

export function buildContextMenu(items: {
  onEdit?: () => void;
  onDelete?: () => void;
  onDuplicate?: () => void;
  onStart?: () => void;
  onStop?: () => void;
  onExport?: () => void;
  customItems?: MenuItem[];
}): MenuItem[] {
  const result: MenuItem[] = [];

  if (items.onEdit) {
    result.push({ id: 'edit', label: '编辑', icon: '✏️' });
  }
  if (items.onDuplicate) {
    result.push({ id: 'duplicate', label: '复制', icon: '📋' });
  }
  if (items.onStart) {
    result.push({ id: 'start', label: '启动', icon: '▶️' });
  }
  if (items.onStop) {
    result.push({ id: 'stop', label: '停止', icon: '⏹️' });
  }
  if (items.onExport) {
    result.push({ id: 'export', label: '导出', icon: '📤' });
  }

  if (result.length > 0 && items.onDelete) {
    result.push({ id: 'separator', label: '', separator: true });
  }

  if (items.onDelete) {
    result.push({ id: 'delete', label: '删除', icon: '🗑️', danger: true });
  }

  if (items.customItems) {
    if (result.length > 0) {
      result.push({ id: 'separator-custom', label: '', separator: true });
    }
    result.push(...items.customItems);
  }

  return result;
}
