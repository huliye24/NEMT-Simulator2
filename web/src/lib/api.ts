// API Layer - Future FastAPI Backend Integration
// Current: Mock Data Mode
// Future: Replace with real API calls

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const USE_MOCK = true; // Toggle this to switch between mock and real API

// Types
export interface MarketData {
  symbol: string;
  price: number;
  phase: string;
  dci: number;
  confidence: number;
  risk: string;
}

export interface AIAnalysis {
  summary: string;
  recommendation: "buy" | "sell" | "hold" | "watch";
  reasoning: string;
  timestamp: string;
}

export interface Trade {
  id: string;
  symbol: string;
  type: "long" | "short";
  amount: number;
  entryPrice: number;
  status: "open" | "closed";
  pnl?: number;
}

// Mock Data
const mockMarketData: MarketData[] = [
  { symbol: "BTC/USDT", price: 67432.50, phase: "markup", dci: 72.5, confidence: 0.85, risk: "medium" },
  { symbol: "ETH/USDT", price: 3456.20, phase: "accumulation", dci: 45.2, confidence: 0.78, risk: "low" },
  { symbol: "SOL/USDT", price: 145.80, phase: "distribution", dci: 68.4, confidence: 0.65, risk: "high" },
];

const mockAnalysis: AIAnalysis = {
  summary: "市场处于 markup 阶段，DCI 指标显示强劲动能",
  recommendation: "buy",
  reasoning: "价格突破关键阻力位，DCI 指数上升至 72.5，成交量放大确认趋势",
  timestamp: new Date().toISOString(),
};

// API Client
class NEMTApiClient {
  private baseUrl: string;
  private useMock: boolean;

  constructor(baseUrl: string = API_BASE_URL, useMock: boolean = USE_MOCK) {
    this.baseUrl = baseUrl;
    this.useMock = useMock;
  }

  // Market API
  async getMarketData(): Promise<MarketData[]> {
    if (this.useMock) {
      return new Promise((resolve) => {
        setTimeout(() => resolve(mockMarketData), 500);
      });
    }

    const response = await fetch(`${this.baseUrl}/api/market`);
    if (!response.ok) throw new Error("Failed to fetch market data");
    return response.json();
  }

  // AI Analysis API
  async getAIAnalysis(symbol?: string): Promise<AIAnalysis> {
    if (this.useMock) {
      return new Promise((resolve) => {
        setTimeout(() => resolve(mockAnalysis), 800);
      });
    }

    const url = symbol
      ? `${this.baseUrl}/api/analysis?symbol=${symbol}`
      : `${this.baseUrl}/api/analysis`;
    const response = await fetch(url);
    if (!response.ok) throw new Error("Failed to fetch AI analysis");
    return response.json();
  }

  // Trade API
  async executeTrade(trade: Omit<Trade, "id" | "status">): Promise<Trade> {
    if (this.useMock) {
      return new Promise((resolve) => {
        setTimeout(() => {
          resolve({
            ...trade,
            id: `trade_${Date.now()}`,
            status: "open",
          });
        }, 1000);
      });
    }

    const response = await fetch(`${this.baseUrl}/api/trades`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(trade),
    });
    if (!response.ok) throw new Error("Failed to execute trade");
    return response.json();
  }

  async getTrades(): Promise<Trade[]> {
    if (this.useMock) {
      return new Promise((resolve) => {
        setTimeout(() => resolve([]), 500);
      });
    }

    const response = await fetch(`${this.baseUrl}/api/trades`);
    if (!response.ok) throw new Error("Failed to fetch trades");
    return response.json();
  }

  // Health Check
  async healthCheck(): Promise<{ status: string; version: string }> {
    if (this.useMock) {
      return { status: "ok", version: "mock-alpha" };
    }

    const response = await fetch(`${this.baseUrl}/health`);
    if (!response.ok) throw new Error("Health check failed");
    return response.json();
  }
}

// Export singleton instance
export const apiClient = new NEMTApiClient();

// Export for testing
export { NEMTApiClient };
