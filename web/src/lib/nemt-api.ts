// NEMT API Client Configuration
// ------------------------------------------------------------------
// Toggle between Mock and Real API
// ------------------------------------------------------------------

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const USE_REAL_API = process.env.NEXT_PUBLIC_USE_REAL_API === "true" || false;

// Types
export interface MarketStateResponse {
  symbol: string;
  phase: string;
  dci: number;
  signal: string;
  confidence: number;
  price: number;
  change24h: number;
  timestamp: string;
}

export interface AnalysisReportResponse {
  symbol: string;
  summary: string;
  reasoning: string[];
  recommendation: string;
  confidence: number;
  dci: number;
  phase: string;
  generated_at: string;
  author: string;
}

export interface SimulationSignalResponse {
  symbol: string;
  signal: string;
  entry_price: number;
  stop_loss: number;
  take_profit: number;
  confidence: number;
  timestamp: string;
}

// API Client
class NEMTApiClient {
  private baseUrl: string;
  private useRealApi: boolean;

  constructor(baseUrl: string = API_BASE_URL, useRealApi: boolean = USE_REAL_API) {
    this.baseUrl = baseUrl;
    this.useRealApi = useRealApi;
  }

  // Market API
  async getMarketState(symbol: string = "BTCUSDT"): Promise<MarketStateResponse> {
    if (!this.useRealApi) {
      return this._getMockMarketState(symbol);
    }

    const response = await fetch(`${this.baseUrl}/market/state?symbol=${symbol}`);
    if (!response.ok) throw new Error("Failed to fetch market state");
    return response.json();
  }

  async getAllMarketStates(): Promise<{ states: MarketStateResponse[]; count: number }> {
    if (!this.useRealApi) {
      const symbols = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT", "ADAUSDT"];
      const states = await Promise.all(symbols.map((s) => this._getMockMarketState(s)));
      return { states, count: states.length };
    }

    const response = await fetch(`${this.baseUrl}/market/states`);
    if (!response.ok) throw new Error("Failed to fetch market states");
    return response.json();
  }

  // Analysis API
  async getAnalysisReport(symbol: string = "BTCUSDT"): Promise<AnalysisReportResponse> {
    if (!this.useRealApi) {
      return this._getMockAnalysisReport(symbol);
    }

    const response = await fetch(`${this.baseUrl}/analysis/report?symbol=${symbol}`);
    if (!response.ok) throw new Error("Failed to fetch analysis report");
    return response.json();
  }

  // Simulation API
  async getSimulationSignal(symbol: string = "BTCUSDT"): Promise<SimulationSignalResponse> {
    if (!this.useRealApi) {
      return this._getMockSimulationSignal(symbol);
    }

    const response = await fetch(`${this.baseUrl}/simulation/signal?symbol=${symbol}`);
    if (!response.ok) throw new Error("Failed to fetch simulation signal");
    return response.json();
  }

  // Health Check
  async healthCheck(): Promise<{ status: string; engine: string }> {
    if (!this.useRealApi) {
      return { status: "ok", engine: "mock" };
    }

    const response = await fetch(`${this.baseUrl}/health`);
    if (!response.ok) throw new Error("Health check failed");
    return response.json();
  }

  // Mock Data Generators
  private async _getMockMarketState(symbol: string): Promise<MarketStateResponse> {
    await this._delay(300);

    const phases = ["ACCUMULATION", "MARKUP", "DISTRIBUTION", "MARKDOWN"];
    const signals = ["WAIT", "BUY", "SELL", "STRONG_BUY", "REDUCE"];
    const symbolHash = symbol.split("").reduce((a, b) => a + b.charCodeAt(0), 0) % 5;

    return {
      symbol,
      phase: phases[symbolHash % phases.length],
      dci: Math.round(50 + Math.random() * 30),
      signal: signals[symbolHash % signals.length],
      confidence: Math.round(60 + Math.random() * 30),
      price: Math.round(20000 + Math.random() * 50000),
      change24h: Math.round((Math.random() - 0.5) * 10 * 100) / 100,
      timestamp: new Date().toISOString(),
    };
  }

  private async _getMockAnalysisReport(symbol: string): Promise<AnalysisReportResponse> {
    await this._delay(500);

    const state = await this._getMockMarketState(symbol);

    return {
      symbol,
      summary: `${symbol} 当前处于 ${state.phase} 阶段。DCI ${state.dci} 显示${state.dci > 60 ? "强劲" : "温和"}动能。`,
      reasoning: [
        `DCI ${state.dci} 处于 ${state.dci > 60 ? "HIGH" : "MEDIUM"} band`,
        `Phase ${state.phase} 确认`,
        "成交量与价格走势一致",
        "链上指标支持当前判断",
      ],
      recommendation: state.signal,
      confidence: state.confidence,
      dci: state.dci,
      phase: state.phase,
      generated_at: new Date().toISOString(),
      author: "NEMT Engine",
    };
  }

  private async _getMockSimulationSignal(symbol: string): Promise<SimulationSignalResponse> {
    await this._delay(400);

    const state = await this._getMockMarketState(symbol);

    return {
      symbol,
      signal: state.signal,
      entry_price: state.price,
      stop_loss: Math.round(state.price * 0.95),
      take_profit: Math.round(state.price * 1.1),
      confidence: state.confidence,
      timestamp: new Date().toISOString(),
    };
  }

  private _delay(ms: number): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }
}

// Export singleton
export const nemtApi = new NEMTApiClient();

// Export for testing
export { NEMTApiClient };
