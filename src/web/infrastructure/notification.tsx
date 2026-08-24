/**
 * Copyright 2026 NEMT Lab
 *
 * 消息通知系统 - Toast 通知
 */

import React, { useState, useCallback, useEffect, useRef } from 'react';
import { createPortal } from 'react-dom';

// ============================================
// 类型定义
// ============================================

export type NotificationType = 'success' | 'error' | 'warning' | 'info';

export interface Notification {
  id: string;
  type: NotificationType;
  title: string;
  message?: string;
  duration?: number;
  persistent?: boolean;
  action?: {
    label: string;
    onClick: () => void;
  };
  icon?: React.ReactNode;
}

export interface NotificationOptions {
  type?: NotificationType;
  title: string;
  message?: string;
  duration?: number;
  persistent?: boolean;
  action?: {
    label: string;
    onClick: () => void;
  };
  icon?: React.ReactNode;
}

// ============================================
// 通知图标
// ============================================

const NotificationIcon: React.FC<{ type: NotificationType }> = ({ type }) => {
  const icons: Record<NotificationType, React.ReactNode> = {
    success: (
      <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
        <circle cx="10" cy="10" r="9" stroke="#10b981" strokeWidth="2" />
        <path d="M6 10L9 13L14 7" stroke="#10b981" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    ),
    error: (
      <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
        <circle cx="10" cy="10" r="9" stroke="#ef4444" strokeWidth="2" />
        <path d="M7 7L13 13M13 7L7 13" stroke="#ef4444" strokeWidth="2" strokeLinecap="round" />
      </svg>
    ),
    warning: (
      <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
        <path d="M10 2L18 17H2L10 2Z" stroke="#f59e0b" strokeWidth="2" strokeLinejoin="round" />
        <path d="M10 8V11M10 14H10.01" stroke="#f59e0b" strokeWidth="2" strokeLinecap="round" />
      </svg>
    ),
    info: (
      <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
        <circle cx="10" cy="10" r="9" stroke="#3b82f6" strokeWidth="2" />
        <path d="M10 9V14M10 6H10.01" stroke="#3b82f6" strokeWidth="2" strokeLinecap="round" />
      </svg>
    )
  };

  return <>{icons[type]}</>;
};

// ============================================
// 单个通知组件
// ============================================

const NotificationItem: React.FC<{
  notification: Notification;
  onClose: (id: string) => void;
}> = ({ notification, onClose }) => {
  const [isExiting, setIsExiting] = useState(false);
  const [isVisible, setIsVisible] = useState(false);
  const progressRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // 入场动画
    requestAnimationFrame(() => {
      setIsVisible(true);
    });

    // 自动关闭
    if (!notification.persistent && notification.duration !== 0) {
      const duration = notification.duration || 4000;
      const timer = setTimeout(() => {
        handleClose();
      }, duration);

      return () => clearTimeout(timer);
    }
  }, [notification]);

  const handleClose = useCallback(() => {
    setIsExiting(true);
    setTimeout(() => {
      onClose(notification.id);
    }, 200);
  }, [notification.id, onClose]);

  const handleAction = useCallback(() => {
    notification.action?.onClick();
    handleClose();
  }, [notification.action, handleClose]);

  const colors = {
    success: { bg: '#10b981', border: '#10b98133' },
    error: { bg: '#ef4444', border: '#ef444433' },
    warning: { bg: '#f59e0b', border: '#f59e0b33' },
    info: { bg: '#3b82f6', border: '#3b82f633' }
  };

  const color = colors[notification.type];

  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'flex-start',
        gap: '12px',
        padding: '16px',
        background: 'var(--bg-secondary, #0f172a)',
        border: `1px solid ${color.border}`,
        borderLeft: `3px solid ${color.bg}`,
        borderRadius: '12px',
        boxShadow: '0 10px 40px rgba(0,0,0,0.3)',
        maxWidth: '400px',
        transform: isVisible ? 'translateX(0)' : 'translateX(100%)',
        opacity: isExiting ? 0 : 1,
        transition: 'transform 0.3s ease, opacity 0.2s ease',
        backdropFilter: 'blur(12px)'
      }}
    >
      <div style={{ flexShrink: 0, marginTop: '2px' }}>
        {notification.icon || <NotificationIcon type={notification.type} />}
      </div>

      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{
          fontWeight: 600,
          color: 'var(--text-primary, #e2e8f0)',
          marginBottom: notification.message ? '4px' : 0
        }}>
          {notification.title}
        </div>

        {notification.message && (
          <div style={{
            fontSize: '13px',
            color: 'var(--text-secondary, #94a3b8)',
            lineHeight: 1.5
          }}>
            {notification.message}
          </div>
        )}

        {notification.action && (
          <button
            onClick={handleAction}
            style={{
              marginTop: '12px',
              padding: '6px 12px',
              background: color.bg,
              color: '#fff',
              border: 'none',
              borderRadius: '6px',
              fontSize: '12px',
              fontWeight: 500,
              cursor: 'pointer',
              transition: 'opacity 0.15s'
            }}
            onMouseEnter={(e) => e.currentTarget.style.opacity = '0.9'}
            onMouseLeave={(e) => e.currentTarget.style.opacity = '1'}
          >
            {notification.action.label}
          </button>
        )}
      </div>

      <button
        onClick={handleClose}
        style={{
          flexShrink: 0,
          width: '24px',
          height: '24px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          background: 'transparent',
          border: 'none',
          borderRadius: '4px',
          cursor: 'pointer',
          color: 'var(--text-tertiary, #64748b)',
          transition: 'background 0.15s'
        }}
        onMouseEnter={(e) => {
          e.currentTarget.style.background = 'var(--bg-tertiary, #1e293b)';
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.background = 'transparent';
        }}
      >
        <svg width="14" height="14" viewBox="0 0 14 14" fill="currentColor">
          <path d="M11 3L3 11M3 3L11 11" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
        </svg>
      </button>

      {/* 进度条 */}
      {!notification.persistent && notification.duration !== 0 && (
        <div
          style={{
            position: 'absolute',
            bottom: 0,
            left: 0,
            right: 0,
            height: '2px',
            background: 'var(--bg-tertiary, #1e293b)',
            borderRadius: '0 0 12px 12px',
            overflow: 'hidden'
          }}
        >
          <div
            ref={progressRef}
            style={{
              height: '100%',
              background: color.bg,
              animation: `progress-${notification.id} ${notification.duration || 4000}ms linear forwards`
            }}
          />
          <style>{`
            @keyframes progress-${notification.id} {
              from { width: 100%; }
              to { width: 0%; }
            }
          `}</style>
        </div>
      )}
    </div>
  );
};

// ============================================
// 通知容器
// ============================================

const NotificationContainer: React.FC<{
  notifications: Notification[];
  onClose: (id: string) => void;
}> = ({ notifications, onClose }) => {
  return createPortal(
    <div
      style={{
        position: 'fixed',
        top: '20px',
        right: '20px',
        display: 'flex',
        flexDirection: 'column',
        gap: '12px',
        zIndex: 10001,
        maxHeight: 'calc(100vh - 40px)',
        overflowY: 'auto'
      }}
    >
      {notifications.map(notification => (
        <NotificationItem
          key={notification.id}
          notification={notification}
          onClose={onClose}
        />
      ))}
    </div>,
    document.body
  );
};

// ============================================
// 通知管理器
// ============================================

class NotificationManager {
  private notifications: Notification[] = [];
  private listeners: Set<(notifications: Notification[]) => void> = new Set();

  private notify(): void {
    this.listeners.forEach(listener => listener([...this.notifications]));
  }

  /**
   * 显示通知
   */
  show(options: NotificationOptions): string {
    const id = `notification_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

    const notification: Notification = {
      id,
      type: options.type || 'info',
      title: options.title,
      message: options.message,
      duration: options.duration,
      persistent: options.persistent,
      action: options.action,
      icon: options.icon
    };

    this.notifications.push(notification);
    this.notify();

    return id;
  }

  /**
   * 关闭通知
   */
  close(id: string): void {
    this.notifications = this.notifications.filter(n => n.id !== id);
    this.notify();
  }

  /**
   * 关闭所有通知
   */
  closeAll(): void {
    this.notifications = [];
    this.notify();
  }

  /**
   * 获取所有通知
   */
  getAll(): Notification[] {
    return [...this.notifications];
  }

  /**
   * 便捷方法
   */
  success(title: string, message?: string, options?: Partial<NotificationOptions>): string {
    return this.show({ type: 'success', title, message, ...options });
  }

  error(title: string, message?: string, options?: Partial<NotificationOptions>): string {
    return this.show({ type: 'error', title, message, duration: 0, ...options });
  }

  warning(title: string, message?: string, options?: Partial<NotificationOptions>): string {
    return this.show({ type: 'warning', title, message, ...options });
  }

  info(title: string, message?: string, options?: Partial<NotificationOptions>): string {
    return this.show({ type: 'info', title, message, ...options });
  }

  /**
   * 订阅变化
   */
  subscribe(listener: (notifications: Notification[]) => void): () => void {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }
}

// 全局通知管理器
export const notificationManager = new NotificationManager();

// 便捷方法
export const notify = {
  show: (options: NotificationOptions) => notificationManager.show(options),
  success: (title: string, message?: string) => notificationManager.success(title, message),
  error: (title: string, message?: string) => notificationManager.error(title, message),
  warning: (title: string, message?: string) => notificationManager.warning(title, message),
  info: (title: string, message?: string) => notificationManager.info(title, message),
  close: (id: string) => notificationManager.close(id),
  closeAll: () => notificationManager.closeAll()
};

// ============================================
// 通知 Hook
// ============================================

export function useNotification() {
  const [notifications, setNotifications] = useState<Notification[]>([]);

  useEffect(() => {
    // 初始加载
    setNotifications(notificationManager.getAll());

    // 订阅变化
    const unsubscribe = notificationManager.subscribe(setNotifications);

    return unsubscribe;
  }, []);

  const show = useCallback((options: NotificationOptions) => {
    return notificationManager.show(options);
  }, []);

  const close = useCallback((id: string) => {
    notificationManager.close(id);
  }, []);

  const closeAll = useCallback(() => {
    notificationManager.closeAll();
  }, []);

  return {
    notifications,
    show,
    close,
    closeAll,
    success: (title: string, message?: string) => notificationManager.success(title, message),
    error: (title: string, message?: string) => notificationManager.error(title, message),
    warning: (title: string, message?: string) => notificationManager.warning(title, message),
    info: (title: string, message?: string) => notificationManager.info(title, message)
  };
}

// ============================================
// 通知 Provider
// ============================================

export const NotificationProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { notifications, close } = useNotification();

  return (
    <>
      {children}
      <NotificationContainer notifications={notifications} onClose={close} />
    </>
  );
};
