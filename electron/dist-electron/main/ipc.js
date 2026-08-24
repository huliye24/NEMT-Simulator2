"use strict";
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
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.IPCClient = void 0;
const electron_log_1 = __importDefault(require("electron-log"));
const ws_1 = __importDefault(require("ws"));
const DEFAULT_CONFIG = {
    gatewayUrl: process.env.NEMT_GATEWAY_URL || 'http://localhost:8080',
    timeout: 30000,
    maxRetries: 3,
    retryDelay: 1000,
};
class IPCClient {
    config;
    ws = null;
    wsConnected = false;
    wsSubscriptions = new Map();
    reconnectAttempts = 0;
    maxReconnectAttempts = 5;
    abortController = null;
    constructor(config = {}) {
        this.config = { ...DEFAULT_CONFIG, ...config };
        this.abortController = new AbortController();
    }
    /**
     * Fetch with timeout and retry support
     */
    async fetch(endpoint, options = {}) {
        const { timeout = this.config.timeout, retries = this.config.maxRetries, ...fetchOptions } = options;
        const url = `${this.config.gatewayUrl}${endpoint}`;
        let lastError = null;
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
                return response.json();
            }
            catch (error) {
                lastError = error instanceof Error ? error : new Error(String(error));
                if (attempt < retries) {
                    const delay = this.config.retryDelay * Math.pow(2, attempt);
                    electron_log_1.default.warn(`Request failed (attempt ${attempt + 1}/${retries + 1}), retrying in ${delay}ms: ${lastError.message}`);
                    await this.sleep(delay);
                }
            }
        }
        throw lastError || new Error('Request failed after retries');
    }
    sleep(ms) {
        return new Promise((resolve) => setTimeout(resolve, ms));
    }
    // ==========================================================================
    // Health Check
    // ==========================================================================
    async health() {
        return this.fetch('/health', { retries: 0 });
    }
    /**
     * Check if gateway is available (non-throwing)
     */
    async isGatewayAvailable() {
        try {
            await this.health();
            return true;
        }
        catch {
            return false;
        }
    }
    // ==========================================================================
    // Strategy API
    // ==========================================================================
    async listStrategies(params) {
        const query = new URLSearchParams();
        if (params?.type)
            query.set('type', params.type);
        if (params?.status)
            query.set('status', params.status);
        if (params?.page)
            query.set('page', String(params.page));
        if (params?.page_size)
            query.set('page_size', String(params.page_size));
        const endpoint = `/api/v1/strategies${query.toString() ? '?' + query.toString() : ''}`;
        return this.fetch(endpoint);
    }
    async getStrategy(id) {
        return this.fetch(`/api/v1/strategies/${id}`);
    }
    async createStrategy(data) {
        return this.fetch('/api/v1/strategies', {
            method: 'POST',
            body: JSON.stringify(data),
        });
    }
    async updateStrategy(id, data) {
        return this.fetch(`/api/v1/strategies/${id}`, {
            method: 'PUT',
            body: JSON.stringify(data),
        });
    }
    async deleteStrategy(id) {
        return this.fetch(`/api/v1/strategies/${id}`, {
            method: 'DELETE',
        });
    }
    // ==========================================================================
    // Capsule API
    // ==========================================================================
    async listCapsules(params) {
        const query = new URLSearchParams();
        if (params?.type)
            query.set('type', params.type);
        if (params?.version)
            query.set('version', params.version);
        const endpoint = `/api/v1/capsules${query.toString() ? '?' + query.toString() : ''}`;
        return this.fetch(endpoint);
    }
    async registerCapsule(data) {
        return this.fetch('/api/v1/capsules', {
            method: 'POST',
            body: JSON.stringify(data),
        });
    }
    // ==========================================================================
    // Backtest API
    // ==========================================================================
    async startBacktest(data) {
        return this.fetch('/api/v1/backtest', {
            method: 'POST',
            body: JSON.stringify(data),
        });
    }
    async getBacktest(id) {
        return this.fetch(`/api/v1/backtest/${id}`);
    }
    async getBacktestProgress(id) {
        return this.fetch(`/api/v1/backtest/${id}/progress`);
    }
    // ==========================================================================
    // Market Data API
    // ==========================================================================
    async getMarketData(symbol, interval = '1h', limit = 100) {
        return this.fetch(`/api/v1/market/${symbol}?interval=${interval}&limit=${limit}`);
    }
    async getLatestPrice(symbol) {
        return this.fetch(`/api/v1/market/${symbol}/latest`);
    }
    async getSupportedSymbols() {
        return this.fetch('/api/v1/market/symbols');
    }
    async getSupportedIntervals() {
        return this.fetch('/api/v1/market/intervals');
    }
    // ==========================================================================
    // WebSocket
    // ==========================================================================
    connectWebSocket() {
        return new Promise((resolve, reject) => {
            const wsUrl = this.config.gatewayUrl.replace('http', 'ws') + '/ws';
            this.ws = new ws_1.default(wsUrl);
            this.ws.onopen = () => {
                electron_log_1.default.info('WebSocket connected');
                this.wsConnected = true;
                this.reconnectAttempts = 0;
                resolve();
            };
            this.ws.onclose = () => {
                electron_log_1.default.info('WebSocket disconnected');
                this.wsConnected = false;
                this.attemptReconnect();
            };
            this.ws.onerror = (error) => {
                electron_log_1.default.error('WebSocket error:', error);
                reject(error);
            };
            this.ws.onmessage = (event) => {
                try {
                    const data = typeof event.data === 'string' ? event.data : event.data.toString();
                    const message = JSON.parse(data);
                    this.handleWebSocketMessage(message);
                }
                catch (error) {
                    electron_log_1.default.warn('Failed to parse WebSocket message:', error);
                }
            };
        });
    }
    attemptReconnect() {
        if (this.reconnectAttempts >= this.maxReconnectAttempts) {
            electron_log_1.default.error('Max reconnection attempts reached');
            return;
        }
        this.reconnectAttempts++;
        const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 30000);
        electron_log_1.default.info(`Attempting to reconnect in ${delay}ms (attempt ${this.reconnectAttempts})`);
        setTimeout(() => this.connectWebSocket(), delay);
    }
    handleWebSocketMessage(message) {
        const { type, data } = message;
        // Notify subscribers
        if (type && this.wsSubscriptions.has(type)) {
            for (const callback of this.wsSubscriptions.get(type)) {
                callback(data);
            }
        }
        // Also notify symbol-specific subscribers
        if (data?.symbol) {
            const symbolKey = `symbol:${data.symbol}`;
            if (this.wsSubscriptions.has(symbolKey)) {
                for (const callback of this.wsSubscriptions.get(symbolKey)) {
                    callback(data);
                }
            }
        }
    }
    subscribe(symbols, callback) {
        if (!this.ws || !this.wsConnected) {
            electron_log_1.default.warn('WebSocket not connected');
            return;
        }
        // Add callback
        for (const symbol of symbols) {
            const key = `symbol:${symbol}`;
            if (!this.wsSubscriptions.has(key)) {
                this.wsSubscriptions.set(key, new Set());
            }
            this.wsSubscriptions.get(key).add(callback);
        }
        // Send subscribe message
        this.ws.send(JSON.stringify({
            type: 'subscribe',
            symbols,
        }));
        electron_log_1.default.info(`Subscribed to: ${symbols.join(', ')}`);
    }
    unsubscribe(symbols, callback) {
        if (!this.ws || !this.wsConnected)
            return;
        for (const symbol of symbols) {
            const key = `symbol:${symbol}`;
            if (this.wsSubscriptions.has(key)) {
                if (callback) {
                    this.wsSubscriptions.get(key).delete(callback);
                }
                else {
                    this.wsSubscriptions.delete(key);
                }
            }
        }
        // Send unsubscribe message
        this.ws.send(JSON.stringify({
            type: 'unsubscribe',
            symbols,
        }));
        electron_log_1.default.info(`Unsubscribed from: ${symbols.join(', ')}`);
    }
    disconnectWebSocket() {
        if (this.ws) {
            this.ws.close();
            this.ws = null;
            this.wsConnected = false;
        }
    }
    isWebSocketConnected() {
        return this.wsConnected;
    }
    // ==========================================================================
    // Gateway Status
    // ==========================================================================
    /**
     * Get current gateway URL
     */
    getGatewayUrl() {
        return this.config.gatewayUrl;
    }
    /**
     * Update gateway URL
     */
    setGatewayUrl(url) {
        this.config.gatewayUrl = url;
        electron_log_1.default.info('Gateway URL updated:', url);
    }
    /**
     * Get connection status
     */
    getConnectionStatus() {
        return {
            http: true, // If we can make requests, HTTP is available
            websocket: this.wsConnected,
        };
    }
    // ==========================================================================
    // Cleanup
    // ==========================================================================
    /**
     * Destroy the client and cleanup resources
     */
    destroy() {
        this.disconnectWebSocket();
        this.abortController?.abort();
        this.wsSubscriptions.clear();
        electron_log_1.default.info('IPCClient destroyed');
    }
    // ==========================================================================
    // Python Communication (Legacy)
    // ==========================================================================
    async executePython(command, args = []) {
        // For backward compatibility - this would go through IPC
        electron_log_1.default.info('Python execute:', command);
        return null;
    }
}
exports.IPCClient = IPCClient;
exports.default = IPCClient;
