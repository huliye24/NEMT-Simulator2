/**
 * Copyright 2026 NEMT Lab
 *
 * 拖拽排序系统 - 基于 @dnd-kit
 */

import React, { useState, useCallback, useRef } from 'react';

// ============================================
// 类型定义
// ============================================

export interface DragItem<T = any> {
  id: string;
  index: number;
  data: T;
}

export interface DragState {
  activeId: string | null;
  activeIndex: number | null;
  overId: string | null;
  overIndex: number | null;
}

export interface SortableProps<T> {
  items: T[];
  onReorder: (items: T[]) => void;
  renderItem: (item: T, index: number, dragHandleProps?: any) => React.ReactNode;
  keyExtractor: (item: T) => string;
  itemHeight?: number;
  animationDuration?: number;
  className?: string;
  style?: React.CSSProperties;
  disabled?: boolean;
  handleDragStart?: (item: T, index: number) => void;
  handleDragEnd?: (item: T, index: number, newIndex: number) => void;
}

// ============================================
// 拖拽上下文
// ============================================

const DragContext = React.createContext<{
  activeId: string | null;
  activeIndex: number | null;
  overId: string | null;
  overIndex: number | null;
  registerItem: (id: string, index: number, element: HTMLElement) => void;
  unregisterItem: (id: string) => void;
  onDragStart: (id: string) => void;
  onDragEnd: () => void;
  onDragOver: (id: string) => void;
} | null>(null);

// ============================================
// 可排序列表组件
// ============================================

export function SortableList<T>({
  items,
  onReorder,
  renderItem,
  keyExtractor,
  itemHeight = 80,
  animationDuration = 200,
  className,
  style,
  disabled = false,
  handleDragStart,
  handleDragEnd
}: SortableProps<T>) {
  const [dragState, setDragState] = useState<DragState>({
    activeId: null,
    activeIndex: null,
    overId: null,
    overIndex: null
  });

  const itemRefs = useRef<Map<string, HTMLElement>>(new Map());
  const dragStartPos = useRef<{ x: number; y: number } | null>(null);

  // 注册项目
  const registerItem = useCallback((id: string, index: number, element: HTMLElement) => {
    itemRefs.current.set(id, element);
  }, []);

  // 注销项目
  const unregisterItem = useCallback((id: string) => {
    itemRefs.current.delete(id);
  }, []);

  // 获取项目索引
  const getItemIndex = useCallback((id: string): number => {
    return items.findIndex(item => keyExtractor(item) === id);
  }, [items, keyExtractor]);

  // 拖拽开始
  const onDragStart = useCallback((id: string) => {
    const index = getItemIndex(id);
    setDragState({
      activeId: id,
      activeIndex: index,
      overId: id,
      overIndex: index
    });
    handleDragStart?.(items[index], index);
  }, [getItemIndex, items, handleDragStart]);

  // 拖拽结束
  const onDragEnd = useCallback(() => {
    const { activeIndex, overIndex } = dragState;

    if (activeIndex !== null && overIndex !== null && activeIndex !== overIndex) {
      const newItems = [...items];
      const [removed] = newItems.splice(activeIndex, 1);
      newItems.splice(overIndex, 0, removed);
      onReorder(newItems);
      handleDragEnd?.(removed, activeIndex, overIndex);
    }

    setDragState({
      activeId: null,
      activeIndex: null,
      overId: null,
      overIndex: null
    });
    dragStartPos.current = null;
  }, [dragState, items, onReorder, handleDragEnd]);

  // 拖拽经过
  const onDragOver = useCallback((id: string) => {
    const index = getItemIndex(id);
    setDragState(prev => ({
      ...prev,
      overId: id,
      overIndex: index
    }));
  }, [getItemIndex]);

  // 处理鼠标/触摸事件
  const handlePointerDown = useCallback((e: React.PointerEvent, id: string) => {
    if (disabled) return;

    const target = e.target as HTMLElement;
    if (target.closest('[data-no-drag]')) return;

    e.preventDefault();
    dragStartPos.current = { x: e.clientX, y: e.clientY };

    onDragStart(id);

    const handlePointerMove = (moveEvent: PointerEvent) => {
      if (!dragStartPos.current) return;

      const dx = Math.abs(moveEvent.clientX - dragStartPos.current.x);
      const dy = Math.abs(moveEvent.clientY - dragStartPos.current.y);

      // 移动超过 5px 开始拖拽
      if (dx > 5 || dy > 5) {
        document.body.style.cursor = 'grabbing';

        // 找到被覆盖的项目
        const elementsUnder = document.elementsFromPoint(moveEvent.clientX, moveEvent.clientY);
        for (const el of elementsUnder) {
          if (el.hasAttribute('data-sortable-id')) {
            const overId = el.getAttribute('data-sortable-id');
            if (overId && overId !== dragState.activeId) {
              onDragOver(overId);
              break;
            }
          }
        }
      }
    };

    const handlePointerUp = () => {
      document.body.style.cursor = '';
      document.removeEventListener('pointermove', handlePointerMove);
      document.removeEventListener('pointerup', handlePointerUp);
      onDragEnd();
    };

    document.addEventListener('pointermove', handlePointerMove);
    document.addEventListener('pointerup', handlePointerUp);
  }, [disabled, onDragStart, onDragOver, onDragEnd, dragState.activeId]);

  const contextValue = {
    ...dragState,
    registerItem,
    unregisterItem,
    onDragStart,
    onDragEnd,
    onDragOver
  };

  return (
    <DragContext.Provider value={contextValue}>
      <div
        className={className}
        style={{
          ...style,
          position: 'relative'
        }}
      >
        {items.map((item, index) => {
          const id = keyExtractor(item);
          const isActive = dragState.activeId === id;
          const isOver = dragState.overId === id && dragState.activeId !== id;

          let transform = '';
          if (dragState.activeIndex !== null && dragState.overIndex !== null && dragState.activeId) {
            if (dragState.activeIndex < dragState.overIndex) {
              if (index > dragState.activeIndex && index <= dragState.overIndex) {
                transform = `translateY(-${itemHeight}px)`;
              }
            } else if (dragState.activeIndex > dragState.overIndex) {
              if (index >= dragState.overIndex && index < dragState.activeIndex) {
                transform = `translateY(${itemHeight}px)`;
              }
            }
          }

          return (
            <div
              key={id}
              data-sortable-id={id}
              ref={(el) => {
                if (el) registerItem(id, index, el);
              }}
              onPointerDown={(e) => handlePointerDown(e, id)}
              style={{
                transform,
                transition: isActive ? 'none' : `transform ${animationDuration}ms ease`,
                opacity: isActive ? 0.5 : 1,
                zIndex: isActive ? 1000 : 1,
                position: isActive ? 'relative' : 'relative',
                background: isOver ? 'var(--bg-tertiary, #1e293b)' : 'transparent',
                borderRadius: '8px',
                cursor: disabled ? 'default' : 'grab',
                touchAction: 'none'
              }}
            >
              {renderItem(item, index, {
                'data-no-drag': '',
                style: { cursor: disabled ? 'default' : 'grab' }
              })}
            </div>
          );
        })}
      </div>
    </DragContext.Provider>
  );
}

// ============================================
// 拖拽把手组件
// ============================================

export function DragHandle({
  style,
  className,
  label = '拖拽'
}: {
  style?: React.CSSProperties;
  className?: string;
  label?: string;
}) {
  return (
    <div
      {...{ 'data-no-drag': '' }}
      className={className}
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        width: '24px',
        height: '24px',
        cursor: 'grab',
        borderRadius: '4px',
        ...style
      }}
      title={label}
    >
      <svg width="12" height="20" viewBox="0 0 12 20" fill="currentColor">
        <circle cx="3" cy="4" r="2" />
        <circle cx="9" cy="4" r="2" />
        <circle cx="3" cy="10" r="2" />
        <circle cx="9" cy="10" r="2" />
        <circle cx="3" cy="16" r="2" />
        <circle cx="9" cy="16" r="2" />
      </svg>
    </div>
  );
}

// ============================================
// 拖拽遮罩层 (用于列表间拖拽)
// ============================================

export function DropIndicator({
  position,
  height = 2
}: {
  position: 'before' | 'after';
  height?: number;
}) {
  return (
    <div
      style={{
        position: 'absolute',
        left: 0,
        right: 0,
        height: `${height}px`,
        background: 'var(--accent, #8b5cf6)',
        borderRadius: '1px',
        top: position === 'before' ? '-1px' : 'auto',
        bottom: position === 'after' ? '-1px' : 'auto',
        zIndex: 1000
      }}
    />
  );
}

// ============================================
// 拖拽预览组件
// ============================================

export function DragPreview({
  item,
  position
}: {
  item: React.ReactNode;
  position: { x: number; y: number };
}) {
  return (
    <div
      style={{
        position: 'fixed',
        left: position.x,
        top: position.y,
        transform: 'translate(-50%, -50%) rotate(2deg)',
        pointerEvents: 'none',
        zIndex: 10000,
        opacity: 0.9,
        boxShadow: '0 20px 40px rgba(0,0,0,0.3)',
        borderRadius: '8px',
        background: 'var(--bg-secondary, #0f172a)'
      }}
    >
      {item}
    </div>
  );
}

// ============================================
// 拖拽排序 Hook
// ============================================

export function useSortable<T>(
  items: T[],
  keyExtractor: (item: T) => string,
  onReorder: (items: T[]) => void
) {
  const [isDragging, setIsDragging] = useState(false);
  const [activeItem, setActiveItem] = useState<T | null>(null);

  const handleDragStart = useCallback((item: T) => {
    setIsDragging(true);
    setActiveItem(item);
  }, []);

  const handleDragEnd = useCallback((item: T, oldIndex: number, newIndex: number) => {
    setIsDragging(false);
    setActiveItem(null);
  }, []);

  return {
    isDragging,
    activeItem,
    SortableComponent: (
      <SortableList
        items={items}
        keyExtractor={keyExtractor}
        onReorder={onReorder}
        renderItem={(item, index) => item as any}
        handleDragStart={handleDragStart}
        handleDragEnd={handleDragEnd}
      />
    )
  };
}
