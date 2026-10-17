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

// AI Reasoning Layer Types
export interface HumanThesis {
  macroView: string;
  marketJudgment: string;
  riskFactors: string;
  actionPlan: string;
}

export interface MarketContext {
  phase: MarketPhase;
  dominantSymbol: string;
  avgDci: number;
  sentiment: Sentiment;
  keyLevels: {
    support: number;
    resistance: number;
  };
}

export interface RiskAssessment {
  level: "LOW" | "MEDIUM" | "HIGH";
  factors: string[];
}

export interface AIReasoning {
  marketInterpretation: string;
  riskAssessment: RiskAssessment;
  recommendation: Recommendation;
  confidence: number;
  reasoning: string[];
}

export interface FinalDecision {
  action: Recommendation;
  size: string;
  entry: number | null;
  stopLoss: number | null;
  takeProfit: number | null;
}

export interface AnalysisResult {
  status: "PENDING" | "CLOSED" | "SKIPPED";
  pnl: number | null;
  exitPrice: number | null;
}

export interface Analysis {
  id: string;
  date: string;
  humanThesis: HumanThesis;
  marketContext: MarketContext;
  aiReasoning: AIReasoning;
  finalDecision: FinalDecision;
  result: AnalysisResult;
}

// ==========================================================================
// Multi-Agent Council (Alpha 009)
// --------------------------------------------------------------------------
// A debate record: 5 agents propose, contrarian challenges, chairman
// resolves to a weighted consensus. The full transcript is stored so the
// operator can audit the reasoning chain end-to-end.
// ==========================================================================

export type AgentId =
  | "TECHNICAL"
  | "SENTIMENT"
  | "MACRO"
  | "RISK"
  | "CONTRARIAN";

export type Vote = "AGREE" | "DISAGREE" | "ABSTAIN";

export interface AgentSpec {
  id: AgentId;
  /** Display name shown in the transcript */
  name: string;
  /** Short tagline for tooltips / headers */
  tagline: string;
  /** Hex color used for the agent's card accent */
  color: string;
  /** Voting weight in consensus (must sum to 1.0 across all agents) */
  weight: number;
}

export interface AgentProposal {
  agent: AgentId;
  /** Initial recommendation from this agent's first pass. */
  recommendation: Recommendation;
  /** 0–100. */
  confidence: number;
  /** Plain-language rationale shown in the debate panel. */
  rationale: string;
  /** Supporting evidence points (max ~3). */
  evidence: string[];
}

export interface AgentChallenge {
  from: AgentId;
  to: AgentId;
  vote: Vote;
  /** A single-sentence rebuttal or endorsement. */
  statement: string;
}

export interface AgentRevision {
  agent: AgentId;
  /** Optional revision after seeing challenges (only if agent changed mind). */
  recommendation?: Recommendation;
  confidence?: number;
  /** A note explaining whether the challenge moved the needle. */
  note: string;
}

export interface CouncilTranscript {
  proposals: AgentProposal[];
  /** Contrarian-led challenges before deliberation. */
  challenges: AgentChallenge[];
  /** Optional revisions after challenges were aired. */
  revisions: AgentRevision[];
}

export type CouncilOutcome = "CONSENSUS" | "SPLIT" | "OVERRIDE";

export interface ConsensusBreakdown {
  /** Weighted vote tally for the winning recommendation. */
  winner: Recommendation;
  /** Sum of weights that voted for the winner. */
  weight: number;
  /** Highest individual agent confidence in support of winner. */
  leadingConfidence: number;
  /** Mean confidence of agents that voted with the winner. */
  avgConfidence: number;
  /** Was the chairman forced to override because no majority? */
  override: boolean;
  /** Per-recommendation weight distribution (audit trail). */
  distribution: Record<Recommendation, number>;
}

export interface CouncilVerdict {
  id: string;
  /** ISO timestamp when the session started. */
  startedAt: string;
  /** ISO timestamp when consensus was reached. */
  decidedAt: string;
  /** Session duration in ms. */
  durationMs: number;
  humanThesis: HumanThesis;
  marketContext: MarketContext;
  transcript: CouncilTranscript;
  consensus: ConsensusBreakdown;
  /** The single recommendation the chairman signs off on. */
  decision: Recommendation;
  /** Aggregated confidence from the consensus calculation. */
  confidence: number;
  /** Overall verdict tag. */
  outcome: CouncilOutcome;
  /** Sizing rule derived from the decision + confidence. */
  size: string;
}
