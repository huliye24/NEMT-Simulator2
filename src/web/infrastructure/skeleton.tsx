/**
 * Copyright 2026 NEMT Lab
 *
 * 骨架屏组件 - 加载占位动画
 */

import React from 'react';

// ============================================
// 类型定义
// ============================================

export interface SkeletonProps {
  width?: string | number;
  height?: string | number;
  borderRadius?: string | number;
  className?: string;
  style?: React.CSSProperties;
  animation?: 'pulse' | 'wave' | 'none';
  variant?: 'text' | 'circular' | 'rectangular';
}

export interface SkeletonTextProps {
  lines?: number;
  width?: string | number;
  spacing?: number;
  lastLineWidth?: string | number;
}

// ============================================
// 基础骨架组件
// ============================================

export const Skeleton: React.FC<SkeletonProps> = ({
  width = '100%',
  height = '20px',
  borderRadius = '4px',
  className,
  style,
  animation = 'wave',
  variant = 'rectangular'
}) => {
  const isCircular = variant === 'circular';
  const isText = variant === 'text';

  const actualHeight = isText ? '1em' : height;
  const actualBorderRadius = isCircular
    ? '50%'
    : isText
      ? '4px'
      : borderRadius;

  const animationStyle = animation === 'none'
    ? {}
    : animation === 'pulse'
      ? {
          animation: 'skeleton-pulse 1.5s ease-in-out infinite'
        }
      : {
          background: 'linear-gradient(90deg, var(--bg-tertiary, #1e293b) 25%, var(--bg-elevated, #334155) 50%, var(--bg-tertiary, #1e293b) 75%)',
          backgroundSize: '200% 100%',
          animation: 'skeleton-wave 1.5s ease-in-out infinite'
        };

  return (
    <>
      <style>{`
        @keyframes skeleton-pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.4; }
        }
        @keyframes skeleton-wave {
          0% { background-position: 200% 0; }
          100% { background-position: -200% 0; }
        }
      `}</style>
      <div
        className={className}
        style={{
          width: typeof width === 'number' ? `${width}px` : width,
          height: typeof actualHeight === 'number' ? `${actualHeight}px` : actualHeight,
          borderRadius: typeof actualBorderRadius === 'number' ? `${actualBorderRadius}px` : actualBorderRadius,
          background: animation === 'none'
            ? 'var(--bg-tertiary, #1e293b)'
            : animation === 'pulse'
              ? 'var(--bg-tertiary, #1e293b)'
              : undefined,
          ...animationStyle,
          ...style
        }}
      />
    </>
  );
};

// ============================================
// 文本骨架
// ============================================

export const SkeletonText: React.FC<SkeletonTextProps> = ({
  lines = 3,
  width = '100%',
  spacing = 8,
  lastLineWidth = '60%'
}) => {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: `${spacing}px` }}>
      {Array.from({ length: lines }).map((_, index) => (
        <Skeleton
          key={index}
          variant="text"
          width={index === lines - 1 ? lastLineWidth : width}
          height={16}
          animation="wave"
        />
      ))}
    </div>
  );
};

// ============================================
// 头像骨架
// ============================================

export const SkeletonAvatar: React.FC<{
  size?: number;
  shape?: 'circle' | 'square';
}> = ({ size = 40, shape = 'circle' }) => {
  return (
    <Skeleton
      variant="circular"
      width={size}
      height={size}
      borderRadius={shape === 'circle' ? '50%' : '8px'}
    />
  );
};

// ============================================
// 卡片骨架
// ============================================

export const SkeletonCard: React.FC<{
  avatar?: boolean;
  rows?: number;
  showActions?: boolean;
}> = ({ avatar = true, rows = 3, showActions = true }) => {
  return (
    <div style={{
      padding: '20px',
      background: 'var(--bg-tertiary, #1e293b)',
      borderRadius: '12px',
      display: 'flex',
      flexDirection: 'column',
      gap: '16px'
    }}>
      {avatar && (
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <Skeleton variant="circular" width={40} height={40} />
          <div style={{ flex: 1 }}>
            <Skeleton variant="text" width="40%" height={14} />
            <div style={{ marginTop: '4px' }}>
              <Skeleton variant="text" width="25%" height={12} />
            </div>
          </div>
        </div>
      )}

      <SkeletonText lines={rows} />

      {showActions && (
        <div style={{ display: 'flex', gap: '8px', marginTop: '8px' }}>
          <Skeleton width={80} height={32} borderRadius="6px" />
          <Skeleton width={60} height={32} borderRadius="6px" />
        </div>
      )}
    </div>
  );
};

// ============================================
// 列表骨架
// ============================================

export const SkeletonList: React.FC<{
  count?: number;
  avatar?: boolean;
  rows?: number;
}> = ({ count = 5, avatar = true, rows = 2 }) => {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
      {Array.from({ length: count }).map((_, index) => (
        <div
          key={index}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '12px',
            padding: '12px',
            background: 'var(--bg-tertiary, #1e293b)',
            borderRadius: '8px'
          }}
        >
          {avatar && <Skeleton variant="circular" width={40} height={40} />}
          <div style={{ flex: 1 }}>
            <Skeleton variant="text" width="30%" height={14} />
            <div style={{ marginTop: '8px' }}>
              <SkeletonText lines={rows} spacing={4} />
            </div>
          </div>
        </div>
      ))}
    </div>
  );
};

// ============================================
// 表格骨架
// ============================================

export const SkeletonTable: React.FC<{
  columns?: number;
  rows?: number;
}> = ({ columns = 4, rows = 5 }) => {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
      {/* 表头 */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: `repeat(${columns}, 1fr)`,
        gap: '12px',
        padding: '12px 16px',
        background: 'var(--bg-secondary, #0f172a)',
        borderRadius: '8px 8px 0 0'
      }}>
        {Array.from({ length: columns }).map((_, index) => (
          <Skeleton key={index} width="80%" height={14} animation="none" />
        ))}
      </div>

      {/* 表格行 */}
      {Array.from({ length: rows }).map((_, rowIndex) => (
        <div
          key={rowIndex}
          style={{
            display: 'grid',
            gridTemplateColumns: `repeat(${columns}, 1fr)`,
            gap: '12px',
            padding: '16px',
            background: 'var(--bg-tertiary, #1e293b)',
            borderRadius: rowIndex === rows - 1 ? '0 0 8px 8px' : '0'
          }}
        >
          {Array.from({ length: columns }).map((_, colIndex) => (
            <Skeleton key={colIndex} width="90%" height={14} animation="wave" />
          ))}
        </div>
      ))}
    </div>
  );
};

// ============================================
// 图表骨架
// ============================================

export const SkeletonChart: React.FC<{
  height?: number;
}> = ({ height = 200 }) => {
  return (
    <div style={{
      height,
      display: 'flex',
      alignItems: 'flex-end',
      gap: '8px',
      padding: '20px',
      background: 'var(--bg-tertiary, #1e293b)',
      borderRadius: '12px'
    }}>
      {Array.from({ length: 12 }).map((_, index) => {
        const randomHeight = 30 + Math.random() * 70;
        return (
          <Skeleton
            key={index}
            width="100%"
            height={`${randomHeight}%`}
            borderRadius="4px 4px 0 0"
            animation="wave"
            style={{
              animationDelay: `${index * 0.1}s`,
              flex: 1
            }}
          />
        );
      })}
    </div>
  );
};

// ============================================
// 内容块骨架
// ============================================

export const SkeletonBlock: React.FC<{
  rows?: number;
  withHeader?: boolean;
}> = ({ rows = 4, withHeader = true }) => {
  return (
    <div style={{
      padding: '24px',
      background: 'var(--bg-tertiary, #1e293b)',
      borderRadius: '12px'
    }}>
      {withHeader && (
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: '20px',
          paddingBottom: '16px',
          borderBottom: '1px solid var(--border-primary, #334155)'
        }}>
          <Skeleton width={200} height={24} />
          <Skeleton width={100} height={32} borderRadius="6px" />
        </div>
      )}

      <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
        {Array.from({ length: rows }).map((_, index) => (
          <div
            key={index}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '16px'
            }}
          >
            <Skeleton variant="circular" width={40} height={40} />
            <div style={{ flex: 1 }}>
              <Skeleton width="60%" height={16} />
              <div style={{ marginTop: '8px' }}>
                <Skeleton width="40%" height={12} />
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

// ============================================
// 全局加载骨架
// ============================================

export const LoadingSkeleton: React.FC = () => {
  return (
    <div style={{ padding: '24px' }}>
      {/* 头部 */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        marginBottom: '24px'
      }}>
        <div>
          <Skeleton width={200} height={28} />
          <div style={{ marginTop: '8px' }}>
            <Skeleton width={150} height={16} />
          </div>
        </div>
        <Skeleton width={120} height={40} borderRadius="8px" />
      </div>

      {/* 网格 */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))',
        gap: '20px'
      }}>
        {Array.from({ length: 4 }).map((_, index) => (
          <SkeletonCard key={index} />
        ))}
      </div>
    </div>
  );
};
