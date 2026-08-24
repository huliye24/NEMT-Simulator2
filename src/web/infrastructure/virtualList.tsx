/**
 * Copyright 2026 NEMT Lab
 *
 * 虚拟化列表组件 - 支持大量数据的高性能渲染
 */

import React, { useRef, useEffect, useState, useCallback, useMemo } from 'react';

// ============================================
// 类型定义
// ============================================

export interface VirtualListProps<T> {
  /** 数据源 */
  items: T[];
  /** 行渲染函数 */
  renderItem: (item: T, index: number) => React.ReactNode;
  /** 行高度 (固定高度或动态高度函数) */
  itemHeight: number | ((index: number) => number);
  /** 可视区域高度 */
  height: number;
  /** 容器类名 */
  className?: string;
  /** 容器样式 */
  style?: React.CSSProperties;
  /** 行类名 */
  itemClassName?: string;
  /** overscan 数量 (预渲染的行数) */
  overscan?: number;
  /** 滚动位置 */
  scrollOffset?: number;
  /** 滚动回调 */
  onScroll?: (event: React.UIEvent<HTMLDivElement>) => void;
  /** 滚动到底部回调 */
  onEndReached?: () => void;
  /** 到底部触发距离 */
  endReachedThreshold?: number;
  /** 空状态渲染 */
  renderEmpty?: () => React.ReactNode;
  /** 加载状态 */
  loading?: boolean;
  /** 加载渲染 */
  renderLoading?: () => React.ReactNode;
}

export interface VirtualListRow<T> {
  index: number;
  item: T;
  offset: number;
  size: number;
}

// ============================================
// 工具函数
// ============================================

/**
 * 计算行偏移和尺寸
 */
function calculateRows<T>(
  items: T[],
  itemHeight: number | ((index: number) => number),
  scrollTop: number,
  containerHeight: number,
  overscan: number
): VirtualListRow<T>[] {
  const rows: VirtualListRow<T>[] = [];

  // 计算固定高度或获取动态高度
  const getHeight = (index: number): number => {
    if (typeof itemHeight === 'function') {
      return itemHeight(index);
    }
    return itemHeight;
  };

  // 计算总高度
  const totalHeight = items.reduce((sum, _, index) => sum + getHeight(index), 0);

  // 如果没有数据，返回空
  if (items.length === 0) return [];

  // 计算可视区域覆盖的范围
  const startIndex = findStartIndex(items, itemHeight, scrollTop);
  const endIndex = findEndIndex(items, itemHeight, scrollTop, containerHeight);

  // 添加 overscan
  const visibleStart = Math.max(0, startIndex - overscan);
  const visibleEnd = Math.min(items.length - 1, endIndex + overscan);

  // 计算可见行的偏移
  let currentOffset = 0;
  for (let i = 0; i < visibleStart; i++) {
    currentOffset += getHeight(i);
  }

  // 生成可见行
  for (let i = visibleStart; i <= visibleEnd; i++) {
    const size = getHeight(i);
    rows.push({
      index: i,
      item: items[i],
      offset: currentOffset,
      size
    });
    currentOffset += size;
  }

  return rows;
}

/**
 * 二分查找找到起始索引
 */
function findStartIndex<T>(
  items: T[],
  itemHeight: number | ((index: number) => number),
  scrollTop: number
): number {
  const getHeight = (index: number): number => {
    if (typeof itemHeight === 'function') {
      return itemHeight(index);
    }
    return itemHeight;
  };

  let low = 0;
  let high = items.length - 1;
  let result = 0;

  while (low <= high) {
    const mid = Math.floor((low + high) / 2);
    let offset = 0;
    for (let i = 0; i < mid; i++) {
      offset += getHeight(i);
    }

    if (offset < scrollTop) {
      low = mid + 1;
    } else {
      result = mid;
      high = mid - 1;
    }
  }

  return result;
}

/**
 * 找到结束索引
 */
function findEndIndex<T>(
  items: T[],
  itemHeight: number | ((index: number) => number),
  scrollTop: number,
  containerHeight: number
): number {
  const getHeight = (index: number): number => {
    if (typeof itemHeight === 'function') {
      return itemHeight(index);
    }
    return itemHeight;
  };

  let totalHeight = 0;
  let index = 0;

  for (let i = 0; i < items.length; i++) {
    const height = getHeight(i);
    if (totalHeight + height > scrollTop + containerHeight) {
      index = i;
      break;
    }
    totalHeight += height;
  }

  return index;
}

// ============================================
// 虚拟化列表组件
// ============================================

export function VirtualList<T>({
  items,
  renderItem,
  itemHeight,
  height,
  className,
  style,
  itemClassName,
  overscan = 3,
  scrollOffset,
  onScroll,
  onEndReached,
  endReachedThreshold = 200,
  renderEmpty,
  loading,
  renderLoading
}: VirtualListProps<T>) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [scrollTop, setScrollTop] = useState(scrollOffset || 0);
  const [containerHeight, setContainerHeight] = useState(height);

  // 计算总高度
  const totalHeight = useMemo(() => {
    if (typeof itemHeight === 'function') {
      return items.reduce((sum, _, index) => sum + itemHeight(index), 0);
    }
    return items.length * itemHeight;
  }, [items, itemHeight]);

  // 计算可见行
  const rows = useMemo(() => {
    return calculateRows(items, itemHeight, scrollTop, containerHeight, overscan);
  }, [items, itemHeight, scrollTop, containerHeight, overscan]);

  // 处理滚动
  const handleScroll = useCallback((event: React.UIEvent<HTMLDivElement>) => {
    const target = event.currentTarget;
    setScrollTop(target.scrollTop);

    // 触发回调
    onScroll?.(event);

    // 检查是否到达底部
    if (onEndReached) {
      const { scrollTop: st, scrollHeight, clientHeight } = target;
      const distanceFromBottom = scrollHeight - st - clientHeight;

      if (distanceFromBottom < endReachedThreshold) {
        onEndReached();
      }
    }
  }, [onScroll, onEndReached, endReachedThreshold]);

  // 同步外部滚动位置
  useEffect(() => {
    if (scrollOffset !== undefined && containerRef.current) {
      containerRef.current.scrollTop = scrollOffset;
      setScrollTop(scrollOffset);
    }
  }, [scrollOffset]);

  // 同步容器高度
  useEffect(() => {
    setContainerHeight(height);
  }, [height]);

  // 空状态
  if (items.length === 0) {
    if (renderEmpty) {
      return <div style={{ height, ...style }}>{renderEmpty()}</div>;
    }
    return (
      <div
        className={className}
        style={{ height, display: 'flex', alignItems: 'center', justifyContent: 'center', ...style }}
      >
        <div style={{ color: '#64748b', textAlign: 'center' }}>
          <div style={{ marginBottom: '8px', fontSize: '24px' }}>📭</div>
          <div>暂无数据</div>
        </div>
      </div>
    );
  }

  return (
    <div
      ref={containerRef}
      className={className}
      style={{
        height,
        overflow: 'auto',
        position: 'relative',
        ...style
      }}
      onScroll={handleScroll}
    >
      {/* 占位元素，撑起滚动区域 */}
      <div style={{ height: totalHeight, position: 'relative' }}>
        {/* 渲染可见行 */}
        {rows.map(row => (
          <div
            key={row.index}
            className={itemClassName}
            style={{
              position: 'absolute',
              top: 0,
              left: 0,
              right: 0,
              height: row.size,
              transform: `translateY(${row.offset}px)`,
              willChange: 'transform'
            }}
          >
            {renderItem(row.item, row.index)}
          </div>
        ))}
      </div>

      {/* 加载状态 */}
      {loading && renderLoading && (
        <div style={{
          position: 'absolute',
          bottom: 0,
          left: 0,
          right: 0,
          padding: '16px',
          textAlign: 'center'
        }}>
          {renderLoading()}
        </div>
      )}
    </div>
  );
}

// ============================================
// 虚拟化网格组件
// ============================================

export interface VirtualGridProps<T> {
  items: T[];
  renderItem: (item: T, index: number) => React.ReactNode;
  columnCount: number;
  rowHeight: number;
  gap?: number;
  height: number;
  className?: string;
  style?: React.CSSProperties;
  overscan?: number;
}

export function VirtualGrid<T>({
  items,
  renderItem,
  columnCount,
  rowHeight,
  gap = 0,
  height,
  className,
  style,
  overscan = 2
}: VirtualGridProps<T>) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [scrollTop, setScrollTop] = useState(0);
  const [containerHeight, setContainerHeight] = useState(height);

  const rowCount = Math.ceil(items.length / columnCount);
  const totalHeight = rowCount * (rowHeight + gap) - gap;

  // 计算可见行
  const visibleRange = useMemo(() => {
    const startRow = Math.max(0, Math.floor(scrollTop / (rowHeight + gap)) - overscan);
    const visibleRows = Math.ceil(containerHeight / (rowHeight + gap)) + overscan * 2;
    const endRow = Math.min(rowCount - 1, startRow + visibleRows);

    return { startRow, endRow };
  }, [scrollTop, containerHeight, rowHeight, gap, rowCount, overscan]);

  const handleScroll = useCallback((event: React.UIEvent<HTMLDivElement>) => {
    setScrollTop(event.currentTarget.scrollTop);
  }, []);

  useEffect(() => {
    setContainerHeight(height);
  }, [height]);

  return (
    <div
      ref={containerRef}
      className={className}
      style={{
        height,
        overflow: 'auto',
        position: 'relative',
        ...style
      }}
      onScroll={handleScroll}
    >
      <div style={{ height: totalHeight, position: 'relative' }}>
        {Array.from({ length: visibleRange.endRow - visibleRange.startRow + 1 }, (_, i) => {
          const rowIndex = visibleRange.startRow + i;
          const startIndex = rowIndex * columnCount;
          const rowItems = items.slice(startIndex, startIndex + columnCount);

          return (
            <div
              key={rowIndex}
              style={{
                position: 'absolute',
                top: rowIndex * (rowHeight + gap),
                left: 0,
                right: 0,
                height: rowHeight,
                display: 'flex',
                gap: gap
              }}
            >
              {rowItems.map((item, colIndex) => (
                <div key={startIndex + colIndex} style={{ flex: 1 }}>
                  {renderItem(item, startIndex + colIndex)}
                </div>
              ))}
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ============================================
// 无限滚动 Hook
// ============================================

export function useInfiniteScroll<T>({
  data,
  fetchMore,
  hasMore,
  threshold = 200
}: {
  data: T[];
  fetchMore: () => Promise<void>;
  hasMore: boolean;
  threshold?: number;
}) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [loading, setLoading] = useState(false);

  const handleScroll = useCallback(async () => {
    if (!containerRef.current || loading || !hasMore) return;

    const { scrollTop, scrollHeight, clientHeight } = containerRef.current;
    const distanceFromBottom = scrollHeight - scrollTop - clientHeight;

    if (distanceFromBottom < threshold) {
      setLoading(true);
      try {
        await fetchMore();
      } finally {
        setLoading(false);
      }
    }
  }, [fetchMore, hasMore, threshold, loading]);

  return {
    containerRef,
    handleScroll,
    loading
  };
}

// ============================================
// 虚拟化列表滚动位置 Hook
// ============================================

export function useVirtualizedScrollPosition() {
  const positionRef = useRef<Map<string, number>>(new Map());

  const savePosition = useCallback((key: string, position: number) => {
    positionRef.current.set(key, position);
  }, []);

  const getPosition = useCallback((key: string): number => {
    return positionRef.current.get(key) || 0;
  }, []);

  const clearPosition = useCallback((key: string) => {
    positionRef.current.delete(key);
  }, []);

  return {
    savePosition,
    getPosition,
    clearPosition
  };
}
