/**
 * NEMT Simulator - WebSocket Market Data Hook
 * 
 * Provides real-time market data via WebSocket connection.
 * Used for live ticker updates and market streaming.
 */

import { useEffect, useState, useCallback, useRef } from 'react';

export interface TickerData {
  symbol: string;
  price: number;
  change: number;
  changePercent: number;
  volume: number;
  timestamp: number;
  high24h?: number;
  low24h?: number;
}

export interface KLineData {
  symbol: string;
  interval: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  timestamp: number;
}

interface WebSocketMessage {
  type: string;
  data?: any;
  error?: string;
}

interface UseLocalMarketOptions {
  /** WebSocket endpoint URL */
  url?: string;
  /** Symbols to subscribe to */
  symbols: string[];
  /** Auto-connect on mount */
  autoConnect?: boolean;
  /** Reconnect on error */
  autoReconnect?: boolean;
  /** Reconnect delay in ms */
  reconnectDelay?: number;
  /** Maximum reconnection attempts */
  maxReconnectAttempts?: number;
}

/**
 * Hook for WebSocket-based market data streaming.
 * 
 * @param options - Configuration options
 * @returns Market data state and connection controls
 * 
 * @example
 * ```tsx
 * function MarketTicker() {
 *   const { ticker, isConnected, subscribe, unsubscribe } = useLocalMarket({
 *     symbols: ['BTC/USDT', 'ETH/USDT'],
 *   });
 * 
 *   return (
 *     <div>
 *       {ticker && <span>{ticker.price}</span>}
 *       {isConnected ? 'Connected' : 'Disconnected'}
 *     </div>
 *   );
 * }
 * ```
 */
export function useLocalMarket(options: UseLocalMarketOptions) {
  const {
    url = 'ws://localhost:8080/ws',
    symbols,
    autoConnect = true,
    autoReconnect = true,
    reconnectDelay = 3000,
    maxReconnectAttempts = 5,
  } = options;

  const [ticker, setTicker] = useState<Map<string, TickerData>>(new Map());
  const [klines, setKlines] = useState<Map<string, KLineData[]>>(new Map());
  const [isConnected, setIsConnected] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdate, setLastUpdate] = useState<number>(Date.now());

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

    setIsConnecting(true);
    setError(null);

    try {
      const ws = new WebSocket(url);

      ws.onopen = () => {
        console.log('[WebSocket] Connected to', url);
        setIsConnected(true);
        setIsConnecting(false);
        reconnectAttemptsRef.current = 0;

        // Subscribe to symbols
        if (symbols.length > 0) {
          ws.send(JSON.stringify({
            type: 'subscribe',
            symbols,
          }));
        }
      };

      ws.onclose = (event) => {
        console.log('[WebSocket] Disconnected', event.code, event.reason);
        setIsConnected(false);
        setIsConnecting(false);

        // Auto reconnect
        if (autoReconnect && reconnectAttemptsRef.current < maxReconnectAttempts) {
          reconnectAttemptsRef.current++;
          console.log(`[WebSocket] Reconnecting in ${reconnectDelay}ms (attempt ${reconnectAttemptsRef.current})`);
          reconnectTimeoutRef.current = setTimeout(connect, reconnectDelay);
        }
      };

      ws.onerror = (event) => {
        console.error('[WebSocket] Error', event);
        setError('WebSocket connection error');
        setIsConnecting(false);
      };

      ws.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);
          handleMessage(message);
        } catch (e) {
          console.error('[WebSocket] Failed to parse message:', e);
        }
      };

      wsRef.current = ws;
    } catch (e) {
      console.error('[WebSocket] Failed to connect:', e);
      setError(String(e));
      setIsConnecting(false);
    }
  }, [url, symbols, autoReconnect, reconnectDelay, maxReconnectAttempts]);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    if (wsRef.current) {
      wsRef.current.close(1000, 'Client disconnect');
      wsRef.current = null;
    }

    setIsConnected(false);
    setIsConnecting(false);
  }, []);

  const handleMessage = useCallback((message: WebSocketMessage) => {
    const { type, data } = message;

    switch (type) {
      case 'ticker':
        if (data?.symbol) {
          setTicker(prev => {
            const newMap = new Map(prev);
            newMap.set(data.symbol, data as TickerData);
            return newMap;
          });
          setLastUpdate(Date.now());
        }
        break;

      case 'kline':
        if (data?.symbol && data?.interval) {
          setKlines(prev => {
            const key = `${data.symbol}:${data.interval}`;
            const newMap = new Map(prev);
            const existing = newMap.get(key) || [];
            // Keep last 100 klines
            const updated = [...existing, data as KLineData].slice(-100);
            newMap.set(key, updated);
            return newMap;
          });
        }
        break;

      case 'error':
        console.error('[WebSocket] Server error:', message.error);
        setError(message.error || 'Unknown error');
        break;

      case 'subscribed':
        console.log('[WebSocket] Subscribed to:', data?.symbols);
        break;

      case 'unsubscribed':
        console.log('[WebSocket] Unsubscribed from:', data?.symbols);
        break;

      default:
        console.log('[WebSocket] Unknown message type:', type);
    }
  }, []);

  const subscribe = useCallback((newSymbols: string[]) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: 'subscribe',
        symbols: newSymbols,
      }));
    }
  }, []);

  const unsubscribe = useCallback((symbolsToRemove: string[]) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: 'unsubscribe',
        symbols: symbolsToRemove,
      }));
    }
  }, []);

  // Auto connect on mount
  useEffect(() => {
    if (autoConnect) {
      connect();
    }

    return () => {
      disconnect();
    };
  }, [autoConnect, connect, disconnect]);

  // Re-subscribe when symbols change
  useEffect(() => {
    if (isConnected && symbols.length > 0) {
      subscribe(symbols);
    }
  }, [symbols, isConnected, subscribe]);

  return {
    // Connection state
    isConnected,
    isConnecting,
    error,
    lastUpdate,

    // Market data
    ticker,
    klines,

    // Get specific ticker
    getTicker: (symbol: string) => ticker.get(symbol),
    getKlines: (symbol: string, interval: string = '1m') => 
      klines.get(`${symbol}:${interval}`),

    // Controls
    connect,
    disconnect,
    subscribe,
    unsubscribe,
  };
}

/**
 * Hook for single symbol ticker data.
 * 
 * @param symbol - Trading pair symbol
 * @param options - WebSocket options
 * @returns Ticker data for the symbol
 */
export function useTicker(symbol: string, options?: Partial<UseLocalMarketOptions>) {
  const result = useLocalMarket({
    symbols: [symbol],
    ...options,
  });

  return {
    ticker: result.ticker.get(symbol),
    isConnected: result.isConnected,
    error: result.error,
    lastUpdate: result.lastUpdate,
  };
}

/**
 * Hook for managing a ticker list display.
 * 
 * @param symbols - Array of trading pair symbols
 * @param options - WebSocket options
 * @returns Map of ticker data keyed by symbol
 */
export function useTickers(
  symbols: string[],
  options?: Partial<UseLocalMarketOptions>
) {
  const result = useLocalMarket({
    symbols,
    ...options,
  });

  return {
    tickers: result.ticker,
    isConnected: result.isConnected,
    error: result.error,
    lastUpdate: result.lastUpdate,
    reconnect: result.connect,
  };
}
