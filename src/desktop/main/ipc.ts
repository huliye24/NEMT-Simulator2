/**
 * IPC Client - Go Gateway Communication Module
 *
 * Responsibilities:
 * - Connect to Go Gateway service
 * - HTTP/WS communication
 * - Request/response handling
 *
 * Features:
 * - Automatic retry with exponential backoff
 * - Request timeout handling
 * - WebSocket reconnection
 * - Request queue management
 */

import log from 'electron-log';

export interface IPCConfig {
  gatewayUrl: string;
  timeout: number;
  maxRetries: number;
  retryDelay: number;
}

const DEFAULT_CONFIG: IPCConfig = {
  gatewayUrl: process.env.NEMT_GATEWAY_URL || 'http://localhost:8080',
  timeout: 30000,
  maxRetries: 3,
  retryDelay: 1000,
};

export interface APIResponse<T = any> {
  success: boolean;
  data?: T;
  error?: {
    code: string;
    message: string;
  };
  meta?: {
    timestamp: number;
    page?: number;
    page_size?: number;
    total_count?: number;
  };
}

export interface RequestOptions extends RequestInit {
  timeout?: number;
  retries?: number;
}

class IPCClient {
  private config: IPCConfig;
  private ws: WebSocket | null = null;
  private wsConnected = false;
  private wsSubscriptions: Map<string, Set<(data: any) => void>> = new Map();
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;

  constructor(config: Partial<IPCConfig> = {}) {
    this.config = { ...DEFAULT_CONFIG, ...config };
  }

  private async fetch<T>(
    endpoint: string,
    options: RequestOptions = {}
  ): Promise<T> {
    const {
      timeout = this.config.timeout,
      retries = this.config.maxRetries,
      ...fetchOptions
    } = options;

    const url = `${this.config.gatewayUrl}${endpoint}`;
    let lastError: Error | null = null;

    for (let attempt = 0; attempt <= retries; attempt++) {
      try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), timeout);

        const response = await fetch(url, {
          ...fetchOptions,
          signal: controller.signal,
          headers: {
            'Content-Type': 'application/json',
            ...fetchOptions.headers,
          },
        });

        clearTimeout(timeoutId);

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        return response.json() as T;
      } catch (error) {
        lastError = error instanceof Error ? error : new Error(String(error));

        if (attempt < retries) {
          const delay = this.config.retryDelay * Math.pow(2, attempt);
          log.warn(
            `Request failed (attempt ${attempt + 1}/${retries + 1}), retrying in ${delay}ms: ${lastError.message}`
          );
          await this.sleep(delay);
        }
      }
    }

    throw lastError || new Error('Request failed after retries');
  }

  private sleep(ms: number): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }

  async health(): Promise<APIResponse> {
    return this.fetch<APIResponse>('/health', { retries: 0 });
  }

  async isGatewayAvailable(): Promise<boolean> {
    try {
      await this.health();
      return true;
    } catch {
      return false;
    }
  }

  async listStrategies(params?: {
    type?: string;
    status?: string;
    page?: number;
    page_size?: number;
  }): Promise<APIResponse> {
    const query = new URLSearchParams();
    if (params?.type) query.set('type', params.type);
    if (params?.status) query.set('status', params.status);
    if (params?.page) query.set('page', String(params.page));
    if (params?.page_size) query.set('page_size', String(params.page_size));

    const endpoint = `/api/v1/strategies${query.toString() ? '?' + query.toString() : ''}`;
    return this.fetch<APIResponse>(endpoint);
  }

  async getStrategy(id: string): Promise<APIResponse> {
    return this.fetch<APIResponse>(`/api/v1/strategies/${id}`);
  }

  async createStrategy(data: {
    name: string;
    author?: string;
    type?: number;
    code?: string;
  }): Promise<APIResponse> {
    return this.fetch<APIResponse>('/api/v1/strategies', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async listCapsules(params?: {
    type?: string;
    version?: string;
  }): Promise<APIResponse> {
    const query = new URLSearchParams();
    if (params?.type) query.set('type', params.type);
    if (params?.version) query.set('version', params.version);

    const endpoint = `/api/v1/capsules${query.toString() ? '?' + query.toString() : ''}`;
    return this.fetch<APIResponse>(endpoint);
  }

  async startBacktest(data: {
    strategy_id: string;
    symbol: string;
    interval?: string;
    start_time?: number;
    end_time?: number;
    initial_capital?: number;
  }): Promise<APIResponse> {
    return this.fetch<APIResponse>('/api/v1/backtest', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async getBacktest(id: string): Promise<APIResponse> {
    return this.fetch<APIResponse>(`/api/v1/backtest/${id}`);
  }

  async getMarketData(symbol: string, interval = '1h', limit = 100): Promise<APIResponse> {
    return this.fetch<APIResponse>(
      `/api/v1/market/${symbol}?interval=${interval}&limit=${limit}`
    );
  }

  connectWebSocket(): Promise<void> {
    return new Promise((resolve, reject) => {
      const wsUrl = this.config.gatewayUrl.replace('http', 'ws') + '/ws';
      this.ws = new WebSocket(wsUrl);

      this.ws.onopen = () => {
        log.info('WebSocket connected');
        this.wsConnected = true;
        this.reconnectAttempts = 0;
        resolve();
      };

      this.ws.onclose = () => {
        log.info('WebSocket disconnected');
        this.wsConnected = false;
        this.attemptReconnect();
      };

      this.ws.onerror = (error) => {
        log.error('WebSocket error:', error);
        reject(error);
      };

      this.ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          this.handleWebSocketMessage(message);
        } catch (error) {
          log.warn('Failed to parse WebSocket message:', error);
        }
      };
    });
  }

  private attemptReconnect(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      log.error('Max reconnection attempts reached');
      return;
    }

    this.reconnectAttempts++;
    const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 30000);

    log.info(`Attempting to reconnect in ${delay}ms (attempt ${this.reconnectAttempts})`);
    setTimeout(() => this.connectWebSocket(), delay);
  }

  private handleWebSocketMessage(message: any): void {
    const { type, data } = message;

    if (type && this.wsSubscriptions.has(type)) {
      for (const callback of this.wsSubscriptions.get(type)!) {
        callback(data);
      }
    }

    if (data?.symbol) {
      const symbolKey = `symbol:${data.symbol}`;
      if (this.wsSubscriptions.has(symbolKey)) {
        for (const callback of this.wsSubscriptions.get(symbolKey)!) {
          callback(data);
        }
      }
    }
  }

  subscribe(symbols: string[], callback: (data: any) => void): void {
    if (!this.ws || !this.wsConnected) {
      log.warn('WebSocket not connected');
      return;
    }

    for (const symbol of symbols) {
      const key = `symbol:${symbol}`;
      if (!this.wsSubscriptions.has(key)) {
        this.wsSubscriptions.set(key, new Set());
      }
      this.wsSubscriptions.get(key)!.add(callback);
    }

    this.ws.send(JSON.stringify({
      type: 'subscribe',
      symbols,
    }));

    log.info(`Subscribed to: ${symbols.join(', ')}`);
  }

  unsubscribe(symbols: string[], callback?: (data: any) => void): void {
    if (!this.ws || !this.wsConnected) return;

    for (const symbol of symbols) {
      const key = `symbol:${symbol}`;
      if (this.wsSubscriptions.has(key)) {
        if (callback) {
          this.wsSubscriptions.get(key)!.delete(callback);
        } else {
          this.wsSubscriptions.delete(key);
        }
      }
    }

    this.ws.send(JSON.stringify({
      type: 'unsubscribe',
      symbols,
    }));

    log.info(`Unsubscribed from: ${symbols.join(', ')}`);
  }

  disconnectWebSocket(): void {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
      this.wsConnected = false;
    }
  }

  isWebSocketConnected(): boolean {
    return this.wsConnected;
  }

  destroy(): void {
    this.disconnectWebSocket();
    this.wsSubscriptions.clear();
    log.info('IPCClient destroyed');
  }
}

export default IPCClient;
