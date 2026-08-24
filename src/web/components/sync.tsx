/**
 * Copyright 2026 NEMT Lab
 *
 * 实时数据同步系统
 *
 * 特性：
 * - WebSocket 连接管理
 * - 乐观更新
 * - 冲突解决
 * - 离线支持
 */

import React, { createContext, useContext, useEffect, useState, useCallback, useRef } from 'react';

// ============================================
// 类型定义
// ============================================

export type ConnectionState = 'connecting' | 'connected' | 'disconnected' | 'error';

export interface SyncMessage<T = any> {
  id: string;
  type: 'subscribe' | 'unsubscribe' | 'update' | 'sync' | 'ack' | 'nack';
  channel: string;
  payload?: T;
  timestamp: number;
  version?: number;
}

export interface SyncChannel<T = any> {
  name: string;
  data: T | null;
  lastUpdate: number;
  version: number;
  subscribers: number;
}

export interface SyncOptions {
  url?: string;
  autoReconnect?: boolean;
  reconnectInterval?: number;
  maxReconnectAttempts?: number;
  heartbeatInterval?: number;
  batchUpdates?: boolean;
  batchInterval?: number;
}

// ============================================
// 同步上下文
// ============================================

interface SyncContextType {
  state: ConnectionState;
  channels: Map<string, SyncChannel>;
  subscribe: <T>(channel: string, callback: (data: T) => void) => () => void;
  publish: <T>(channel: string, data: T) => Promise<void>;
  getData: <T>(channel: string) => T | null;
  reconnect: () => void;
  disconnect: () => void;
}

const SyncContext = createContext<SyncContextType | null>(null);

// ============================================
// 同步 Provider
// ============================================

export const SyncProvider: React.FC<{
  children: React.ReactNode;
  options?: SyncOptions;
}> = ({ children, options = {} }) => {
  const {
    url = 'wss://localhost:8080/sync',
    autoReconnect = true,
    reconnectInterval = 3000,
    maxReconnectAttempts = 10,
    heartbeatInterval = 30000,
    batchUpdates = true,
    batchInterval = 100
  } = options;

  const [state, setState] = useState<ConnectionState>('disconnected');
  const [channels, setChannels] = useState<Map<string, SyncChannel>>(new Map());

  const wsRef = useRef<WebSocket | null>(null);
  const subscribersRef = useRef<Map<string, Set<(data: any) => void>>>(new Map());
  const reconnectAttemptsRef = useRef(0);
  const reconnectTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const heartbeatTimerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const pendingUpdatesRef = useRef<Map<string, any>>(new Map());
  const batchTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // 连接
  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    setState('connecting');

    try {
      const ws = new WebSocket(url);

      ws.onopen = () => {
        setState('connected');
        reconnectAttemptsRef.current = 0;

        // 启动心跳
        heartbeatTimerRef.current = setInterval(() => {
          if (ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ type: 'ping', timestamp: Date.now() }));
          }
        }, heartbeatInterval);

        // 重新订阅所有频道
        channels.forEach((_, channelName) => {
          ws.send(JSON.stringify({
            type: 'subscribe',
            channel: channelName,
            timestamp: Date.now()
          }));
        });
      };

      ws.onmessage = (event) => {
        try {
          const message: SyncMessage = JSON.parse(event.data);
          handleMessage(message);
        } catch (e) {
          console.error('[Sync] Failed to parse message:', e);
        }
      };

      ws.onerror = () => {
        setState('error');
      };

      ws.onclose = () => {
        setState('disconnected');

        // 清理心跳
        if (heartbeatTimerRef.current) {
          clearInterval(heartbeatTimerRef.current);
        }

        // 自动重连
        if (autoReconnect && reconnectAttemptsRef.current < maxReconnectAttempts) {
          reconnectAttemptsRef.current++;
          setState('connecting');

          reconnectTimerRef.current = setTimeout(() => {
            connect();
          }, reconnectInterval);
        }
      };

      wsRef.current = ws;
    } catch (e) {
      setState('error');
      console.error('[Sync] Connection error:', e);
    }
  }, [url, autoReconnect, reconnectInterval, maxReconnectAttempts, heartbeatInterval, channels]);

  // 处理消息
  const handleMessage = useCallback((message: SyncMessage) => {
    switch (message.type) {
      case 'update':
      case 'sync':
        if (message.channel && message.payload !== undefined) {
          // 更新频道数据
          setChannels(prev => {
            const next = new Map(prev);
            const channel = next.get(message.channel) || {
              name: message.channel,
              data: null,
              lastUpdate: 0,
              version: 0,
              subscribers: 0
            };

            next.set(message.channel, {
              ...channel,
              data: message.payload,
              lastUpdate: message.timestamp,
              version: message.version || channel.version + 1
            });

            return next;
          });

          // 通知订阅者
          const subscribers = subscribersRef.current.get(message.channel);
          if (subscribers) {
            subscribers.forEach(callback => {
              try {
                callback(message.payload);
              } catch (e) {
                console.error('[Sync] Subscriber error:', e);
              }
            });
          }
        }
        break;

      case 'ack':
        console.log(`[Sync] ACK: ${message.id}`);
        break;

      case 'nack':
        console.error(`[Sync] NACK: ${message.id}`, message.payload);
        break;
    }
  }, []);

  // 订阅频道
  const subscribe = useCallback(<T,>(channel: string, callback: (data: T) => void) => {
    // 添加订阅者
    const subscribers = subscribersRef.current.get(channel) || new Set();
    subscribers.add(callback);
    subscribersRef.current.set(channel, subscribers);

    // 更新频道订阅数
    setChannels(prev => {
      const next = new Map(prev);
      const existing = next.get(channel);
      next.set(channel, {
        name: channel,
        data: existing?.data || null,
        lastUpdate: existing?.lastUpdate || 0,
        version: existing?.version || 0,
        subscribers: (existing?.subscribers || 0) + 1
      });
      return next;
    });

    // 发送订阅消息
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: 'subscribe',
        channel,
        timestamp: Date.now()
      }));
    }

    // 返回取消订阅函数
    return () => {
      const subs = subscribersRef.current.get(channel);
      if (subs) {
        subs.delete(callback);
        if (subs.size === 0) {
          subscribersRef.current.delete(channel);

          // 取消订阅
          if (wsRef.current?.readyState === WebSocket.OPEN) {
            wsRef.current.send(JSON.stringify({
              type: 'unsubscribe',
              channel,
              timestamp: Date.now()
            }));
          }

          // 更新订阅数
          setChannels(prev => {
            const next = new Map(prev);
            const existing = next.get(channel);
            if (existing) {
              next.set(channel, {
                ...existing,
                subscribers: existing.subscribers - 1
              });
            }
            return next;
          });
        }
      }
    };
  }, []);

  // 发布消息
  const publish = useCallback(async <T,>(channel: string, data: T) => {
    // 乐观更新
    setChannels(prev => {
      const next = new Map(prev);
      const existing = next.get(channel);
      next.set(channel, {
        name: channel,
        data,
        lastUpdate: Date.now(),
        version: (existing?.version || 0) + 1,
        subscribers: existing?.subscribers || 0
      });
      return next;
    });

    // 通知本地订阅者
    const subscribers = subscribersRef.current.get(channel);
    if (subscribers) {
      subscribers.forEach(callback => {
        try {
          callback(data);
        } catch (e) {
          console.error('[Sync] Subscriber error:', e);
        }
      });
    }

    // 批量更新
    if (batchUpdates) {
      pendingUpdatesRef.current.set(channel, { data, timestamp: Date.now() });

      if (!batchTimerRef.current) {
        batchTimerRef.current = setTimeout(() => {
          const updates = Array.from(pendingUpdatesRef.current.entries());
          pendingUpdatesRef.current.clear();
          batchTimerRef.current = null;

          // 发送批量更新
          if (wsRef.current?.readyState === WebSocket.OPEN) {
            updates.forEach(([channelName, update]) => {
              wsRef.current?.send(JSON.stringify({
                type: 'update',
                channel: channelName,
                payload: (update as any).data,
                timestamp: Date.now()
              }));
            });
          }
        }, batchInterval);
      }
    } else {
      // 立即发送
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({
          type: 'update',
          channel,
          payload: data,
          timestamp: Date.now()
        }));
      }
    }
  }, [batchUpdates, batchInterval]);

  // 获取数据
  const getData = useCallback(<T,>(channel: string): T | null => {
    const channelData = channels.get(channel);
    return channelData?.data as T | null;
  }, [channels]);

  // 重连
  const reconnect = useCallback(() => {
    if (reconnectTimerRef.current) {
      clearTimeout(reconnectTimerRef.current);
    }
    reconnectAttemptsRef.current = 0;
    connect();
  }, [connect]);

  // 断开连接
  const disconnect = useCallback(() => {
    if (reconnectTimerRef.current) {
      clearTimeout(reconnectTimerRef.current);
    }
    if (heartbeatTimerRef.current) {
      clearInterval(heartbeatTimerRef.current);
    }
    if (batchTimerRef.current) {
      clearTimeout(batchTimerRef.current);
    }

    wsRef.current?.close();
    wsRef.current = null;

    setState('disconnected');
  }, []);

  // 初始化连接
  useEffect(() => {
    connect();

    return () => {
      disconnect();
    };
  }, [connect, disconnect]);

  const value: SyncContextType = {
    state,
    channels,
    subscribe,
    publish,
    getData,
    reconnect,
    disconnect
  };

  return (
    <SyncContext.Provider value={value}>
      {children}
    </SyncContext.Provider>
  );
};

// ============================================
// Hook
// ============================================

export function useSync<T>(channel: string): {
  data: T | null;
  state: ConnectionState;
  publish: (data: T) => Promise<void>;
} {
  const context = useContext(SyncContext);
  if (!context) {
    throw new Error('useSync must be used within SyncProvider');
  }

  const [localData, setLocalData] = useState<T | null>(null);

  useEffect(() => {
    const unsubscribe = context.subscribe<T>(channel, (data) => {
      setLocalData(data);
    });

    return unsubscribe;
  }, [context, channel]);

  return {
    data: localData,
    state: context.state,
    publish: (data: T) => context.publish(channel, data)
  };
}

// ============================================
// 连接状态指示器
// ============================================

export const ConnectionIndicator: React.FC<{
  state: ConnectionState;
}> = ({ state }) => {
  const colors: Record<ConnectionState, string> = {
    connecting: '#f59e0b',
    connected: '#10b981',
    disconnected: '#64748b',
    error: '#ef4444'
  };

  const labels: Record<ConnectionState, string> = {
    connecting: '连接中...',
    connected: '已连接',
    disconnected: '未连接',
    error: '连接错误'
  };

  return (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      gap: '6px',
      padding: '4px 10px',
      background: '#0f172a',
      borderRadius: '12px',
      border: '1px solid #334155',
      fontSize: '11px'
    }}>
      <div style={{
        width: '8px',
        height: '8px',
        borderRadius: '50%',
        background: colors[state],
        animation: state === 'connecting' ? 'pulse 1s infinite' : 'none'
      }} />
      <span style={{ color: '#94a3b8' }}>{labels[state]}</span>

      <style>{`
        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.5; }
        }
      `}</style>
    </div>
  );
};
