/**
 * Copyright 2026 NEMT Lab
 *
 * Tooltip 组件 - 悬浮提示
 */

import React, { useState, useRef, useCallback, useEffect } from 'react';
import { createPortal } from 'react-dom';

// ============================================
// 类型定义
// ============================================

export type TooltipPosition = 'top' | 'bottom' | 'left' | 'right';
export type TooltipTrigger = 'hover' | 'click' | 'focus';

export interface TooltipProps {
  content: React.ReactNode;
  children: React.ReactElement;
  position?: TooltipPosition;
  trigger?: TooltipTrigger | TooltipTrigger[];
  delay?: number;
  disabled?: boolean;
  maxWidth?: number;
  className?: string;
  style?: React.CSSProperties;
}

// ============================================
// Tooltip 组件
// ============================================

export const Tooltip: React.FC<TooltipProps> = ({
  content,
  children,
  position = 'top',
  trigger = 'hover',
  delay = 200,
  disabled = false,
  maxWidth = 280,
  className,
  style
}) => {
  const [isVisible, setIsVisible] = useState(false);
  const [tooltipPosition, setTooltipPosition] = useState({ x: 0, y: 0 });
  const triggerRef = useRef<HTMLElement>(null);
  const tooltipRef = useRef<HTMLDivElement>(null);
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const triggers = Array.isArray(trigger) ? trigger : [trigger];

  // 计算 Tooltip 位置
  const calculatePosition = useCallback(() => {
    if (!triggerRef.current) return { x: 0, y: 0 };

    const rect = triggerRef.current.getBoundingClientRect();
    const gap = 8;

    let x = 0;
    let y = 0;

    switch (position) {
      case 'top':
        x = rect.left + rect.width / 2;
        y = rect.top - gap;
        break;
      case 'bottom':
        x = rect.left + rect.width / 2;
        y = rect.bottom + gap;
        break;
      case 'left':
        x = rect.left - gap;
        y = rect.top + rect.height / 2;
        break;
      case 'right':
        x = rect.right + gap;
        y = rect.top + rect.height / 2;
        break;
    }

    return { x, y };
  }, [position]);

  // 显示 Tooltip
  const showTooltip = useCallback(() => {
    if (disabled || !content) return;

    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }

    timeoutRef.current = setTimeout(() => {
      const pos = calculatePosition();
      setTooltipPosition(pos);
      setIsVisible(true);
    }, delay);
  }, [disabled, content, delay, calculatePosition]);

  // 隐藏 Tooltip
  const hideTooltip = useCallback(() => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
      timeoutRef.current = null;
    }
    setIsVisible(false);
  }, []);

  // 切换显示
  const toggleTooltip = useCallback(() => {
    if (isVisible) {
      hideTooltip();
    } else {
      showTooltip();
    }
  }, [isVisible, showTooltip, hideTooltip]);

  // 事件处理
  const handleMouseEnter = useCallback(() => {
    if (triggers.includes('hover')) {
      showTooltip();
    }
  }, [triggers, showTooltip]);

  const handleMouseLeave = useCallback(() => {
    if (triggers.includes('hover')) {
      hideTooltip();
    }
  }, [triggers, hideTooltip]);

  const handleClick = useCallback(() => {
    if (triggers.includes('click')) {
      toggleTooltip();
    }
  }, [triggers, toggleTooltip]);

  const handleFocus = useCallback(() => {
    if (triggers.includes('focus')) {
      showTooltip();
    }
  }, [triggers, showTooltip]);

  const handleBlur = useCallback(() => {
    if (triggers.includes('focus')) {
      hideTooltip();
    }
  }, [triggers, hideTooltip]);

  // 清理
  useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, []);

  // 计算 Tooltip 样式
  const getTooltipStyle = (): React.CSSProperties => {
    const style: React.CSSProperties = {
      position: 'fixed',
      left: tooltipPosition.x,
      top: tooltipPosition.y,
      maxWidth,
      padding: '8px 12px',
      background: 'var(--bg-secondary, #0f172a)',
      border: '1px solid var(--border-primary, #334155)',
      borderRadius: '8px',
      boxShadow: '0 4px 20px rgba(0,0,0,0.3)',
      fontSize: '13px',
      color: 'var(--text-primary, #e2e8f0)',
      lineHeight: 1.5,
      zIndex: 10000,
      pointerEvents: 'none',
      transform: 'translate(-50%, -50%)',
      transition: 'opacity 0.15s ease',
      opacity: isVisible ? 1 : 0,
      backdropFilter: 'blur(8px)'
    };

    return style;
  };

  // 渲染触发器
  const triggerProps = {
    ref: triggerRef,
    onMouseEnter: handleMouseEnter,
    onMouseLeave: handleMouseLeave,
    onClick: handleClick,
    onFocus: handleFocus,
    onBlur: handleBlur
  };

  const child = React.cloneElement(children, triggerProps);

  return (
    <>
      {child}
      {createPortal(
        <div
          ref={tooltipRef}
          className={className}
          style={getTooltipStyle()}
          role="tooltip"
        >
          {content}
        </div>,
        document.body
      )}
    </>
  );
};

// ============================================
// Rich Tooltip - 带标题和描述
// ============================================

export interface RichTooltipProps extends Omit<TooltipProps, 'content'> {
  title?: React.ReactNode;
  description?: React.ReactNode;
  footer?: React.ReactNode;
  image?: React.ReactNode;
}

export const RichTooltip: React.FC<RichTooltipProps> = ({
  title,
  description,
  footer,
  image,
  children,
  maxWidth = 320,
  ...props
}) => {
  const content = (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
      {image && (
        <div style={{
          margin: '-8px -12px 8px -12px',
          borderRadius: '8px 8px 0 0',
          overflow: 'hidden'
        }}>
          {image}
        </div>
      )}
      {title && (
        <div style={{
          fontWeight: 600,
          color: 'var(--text-primary, #e2e8f0)'
        }}>
          {title}
        </div>
      )}
      {description && (
        <div style={{
          color: 'var(--text-secondary, #94a3b8)',
          fontSize: '12px'
        }}>
          {description}
        </div>
      )}
      {footer && (
        <div style={{
          marginTop: '4px',
          paddingTop: '8px',
          borderTop: '1px solid var(--border-primary, #334155)',
          fontSize: '11px',
          color: 'var(--text-tertiary, #64748b)'
        }}>
          {footer}
        </div>
      )}
    </div>
  );

  return (
    <Tooltip content={content} maxWidth={maxWidth} {...props}>
      {children}
    </Tooltip>
  );
};

// ============================================
// Tooltip 装饰器
// ============================================

export function withTooltip<P extends object>(
  Component: React.ComponentType<P>,
  tooltipContent: React.ReactNode | ((props: P) => React.ReactNode),
  tooltipProps?: Partial<TooltipProps>
) {
  return function TooltipWrapper(props: P) {
    const content = typeof tooltipContent === 'function'
      ? tooltipContent(props)
      : tooltipContent;

    return (
      <Tooltip content={content} {...tooltipProps}>
        <Component {...props} />
      </Tooltip>
    );
  };
}
