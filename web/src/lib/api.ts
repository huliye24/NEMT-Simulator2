// NEMT Web Alpha — Data Access Layer
// ------------------------------------------------------------------
// Today: reads local JSON via static imports.
// Tomorrow: swap these for `fetch('/api/...')` calls to the FastAPI
//           NEMT Engine. Page/component code stays unchanged.
// ------------------------------------------------------------------

import marketData from "@/data/market.json";
import marketStateData from "@/data/market-state.json";
import reportData from "@/data/report.json";
import tradesData from "@/data/trades.json";
import portfolioData from "@/data/portfolio.json";
import journalData from "@/data/journal.json";

import analysisData from "@/data/analysis.json";

import type {
  AIReport,
  JournalEntry,
  MarketState,
  MarketSymbol,
  Portfolio,
  Trade,
  Analysis,
} from "./types";

/**
 * Simulate network latency to make the UI honest about future async work.
 * Kept short so dev is fast. Set to 0 in tests.
 */
const SIMULATED_LATENCY_MS = 0;

const wait = (ms: number) =>
  ms > 0 ? new Promise<void>((r) => setTimeout(r, ms)) : Promise.resolve();

// --------------------------------------------------------------------------
// Market
// --------------------------------------------------------------------------

export async function getMarketState(): Promise<MarketState> {
  await wait(SIMULATED_LATENCY_MS);
  return marketStateData as MarketState;
}

export async function getMarketSymbols(): Promise<MarketSymbol[]> {
  await wait(SIMULATED_LATENCY_MS);
  return marketData as MarketSymbol[];
}

export async function getMarketSymbol(symbol: string): Promise<MarketSymbol | undefined> {
  await wait(SIMULATED_LATENCY_MS);
  return (marketData as MarketSymbol[]).find((m) => m.symbol === symbol);
}

// --------------------------------------------------------------------------
// Reports (AI Reasoning Layer)
// --------------------------------------------------------------------------

export async function getReports(): Promise<AIReport[]> {
  await wait(SIMULATED_LATENCY_MS);
  return (reportData as AIReport[]).sort(
    (a, b) => new Date(b.generatedAt).getTime() - new Date(a.generatedAt).getTime()
  );
}

export async function getLatestReport(): Promise<AIReport | undefined> {
  const all = await getReports();
  return all[0];
}

export async function getReportsBySymbol(symbol: string): Promise<AIReport[]> {
  const all = await getReports();
  return all.filter((r) => r.symbol === symbol);
}

// --------------------------------------------------------------------------
// Trades & Portfolio
// --------------------------------------------------------------------------

export async function getTrades(): Promise<Trade[]> {
  await wait(SIMULATED_LATENCY_MS);
  return (tradesData as Trade[]).sort(
    (a, b) => new Date(b.openedAt).getTime() - new Date(a.openedAt).getTime()
  );
}

export async function getOpenTrades(): Promise<Trade[]> {
  const all = await getTrades();
  return all.filter((t) => t.status === "OPEN");
}

export async function getPortfolio(): Promise<Portfolio> {
  await wait(SIMULATED_LATENCY_MS);
  return portfolioData as Portfolio;
}

// --------------------------------------------------------------------------
// Analysis (AI Reasoning Layer)
// --------------------------------------------------------------------------

export async function getAnalyses(): Promise<Analysis[]> {
  await wait(SIMULATED_LATENCY_MS);
  return (analysisData as Analysis[]).sort(
    (a, b) => new Date(b.date).getTime() - new Date(a.date).getTime()
  );
}

export async function getLatestAnalysis(): Promise<Analysis | undefined> {
  const all = await getAnalyses();
  return all[0];
}

export async function getAnalysisById(id: string): Promise<Analysis | undefined> {
  const all = await getAnalyses();
  return all.find((a) => a.id === id);
}

export async function getJournal(): Promise<JournalEntry[]> {
  await wait(SIMULATED_LATENCY_MS);
  return (journalData as JournalEntry[]).sort(
    (a, b) => new Date(b.date).getTime() - new Date(a.date).getTime()
  );
}
