// Market State Data
export interface MarketState {
  symbol: string;
  price: number;
  phase: "accumulation" | "markup" | "distribution" | "markdown";
  dci: number; // Dynamic Cycle Index
  confidence: number;
  risk: "low" | "medium" | "high";
}

export const mockMarketData: MarketState[] = [
  { symbol: "BTC/USDT", price: 67432.50, phase: "markup", dci: 72.5, confidence: 0.85, risk: "medium" },
  { symbol: "ETH/USDT", price: 3456.20, phase: "accumulation", dci: 45.2, confidence: 0.78, risk: "low" },
  { symbol: "SOL/USDT", price: 145.80, phase: "distribution", dci: 68.4, confidence: 0.65, risk: "high" },
];

// AI Report Data
export interface AIReport {
  summary: string;
  recommendation: "buy" | "sell" | "hold" | "watch";
  reasoning: string;
}

export const mockAIReport: AIReport = {
  summary: "市场处于 markup 阶段，DCI 指标显示强劲动能",
  recommendation: "buy",
  reasoning: "1. 价格突破关键阻力位\n2. DCI 指数上升至 72.5\n3. 成交量放大确认趋势\n4. 风险可控，建议分批建仓",
};

// Trade Memory Data
export interface TradeMemory {
  date: string;
  human_thesis: string;
  ai_reasoning: string;
  result: "win" | "loss" | "pending";
  pnl?: number;
}

export const mockTradeMemory: TradeMemory[] = [
  {
    date: "2025-08-20",
    human_thesis: "BTC 突破 65k 阻力位，趋势转多",
    ai_reasoning: "DCI 确认上升趋势，建议买入",
    result: "win",
    pnl: 1250.50,
  },
  {
    date: "2025-08-18",
    human_thesis: "ETH 在 3.2k 支撑企稳",
    ai_reasoning: "Phase 处于 accumulation，建议观望",
    result: "loss",
    pnl: -320.00,
  },
  {
    date: "2025-08-15",
    human_thesis: "SOL 突破前高",
    ai_reasoning: "Distribution phase 警告，不建议追多",
    result: "pending",
  },
];
