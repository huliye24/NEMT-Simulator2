// NEMT Web Alpha — Shared Type Definitions
// Future-proof API surface; FastAPI will return data matching these shapes.

export type MarketPhase =
  | "ACCUMULATION"
  | "MARKUP"
  | "DISTRIBUTION"
  | "MARKDOWN"
  | "RECOVERY"
  | "UNKNOWN";

export type Sentiment = "BULLISH" | "BEARISH" | "NEUTRAL" | "CAUTIOUS";

export type Recommendation = "STRONG_BUY" | "BUY" | "HOLD" | "REDUCE" | "SELL" | "WAIT";

export type TradeSide = "LONG" | "SHORT";
export type TradeStatus = "OPEN" | "CLOSED" | "CANCELLED";

export interface DCI {
  /** Directional Confidence Index, 0–100 */
  value: number;
  /** Human-readable band */
  band: "VERY_LOW" | "LOW" | "MEDIUM" | "HIGH" | "VERY_HIGH";
}

export interface MarketSymbol {
  symbol: string;            // e.g. "BTCUSDT"
  display: string;           // e.g. "BTC/USDT"
  price: number;
  change24h: number;         // percent, e.g. 1.42 means +1.42%
  volume24h: number;         // quote-volume USDT
  high24h: number;
  low24h: number;
  phase: MarketPhase;
  dci: DCI;
  confidence: number;        // 0–100
  updatedAt: string;         // ISO timestamp
}

export interface MarketState {
  /** Aggregate market-wide phase */
  phase: MarketPhase;
  /** Average DCI across tracked symbols */
  avgDci: number;
  /** Average AI confidence */
  avgConfidence: number;
  /** Overall sentiment */
  sentiment: Sentiment;
  /** Number of symbols tracked */
  trackedSymbols: number;
  /** Active signal count */
  activeSignals: number;
  /** Last update ISO */
  asOf: string;
}

export interface AIReport {
  id: string;
  title: string;
  symbol: string;
  summary: string;
  reasoning: string[];       // bullet list of reasoning steps
  recommendation: Recommendation;
  confidence: number;        // 0–100
  dci: number;               // 0–100
  phase: MarketPhase;
  generatedAt: string;       // ISO
  author: string;            // e.g. "NEMT Council"
}

export interface Trade {
  id: string;
  symbol: string;
  side: TradeSide;
  entry: number;
  exit?: number;
  size: number;              // base asset
  pnl?: number;              // realized PnL in quote
  pnlPct?: number;           // realized PnL percent
  status: TradeStatus;
  openedAt: string;
  closedAt?: string;
  reason: string;
}

export interface JournalEntry {
  id: string;
  date: string;              // YYYY-MM-DD
  title: string;
  body: string;
  tags: string[];
  mood: Sentiment;
}

export interface PortfolioPosition {
  symbol: string;
  side: TradeSide;
  size: number;
  entry: number;
  mark: number;
  pnl: number;
  pnlPct: number;
}

export interface Portfolio {
  capital: number;           // cash + equity at cost, USDT
  equity: number;            // mark-to-market equity, USDT
  pnl: number;               // total unrealized + realized, USDT
  pnlPct: number;            // percent vs starting capital
  positions: PortfolioPosition[];
  /** Starting capital baseline */
  startingCapital: number;
}

export interface KpiCard {
  label: string;
  value: string;
  delta?: number;            // optional percent change
  hint?: string;
}
