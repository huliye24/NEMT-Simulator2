import type { Metadata } from "next";
import EmergentixHome from "@/components/EmergentixHome";
import { getMarketState, getMarketSymbols, getLatestReport, getPortfolio } from "@/lib/api";

export const metadata: Metadata = {
  title: "Emergentix — 涌现市场智能",
  description: "以涌现算法探索市场机会。市场结构研究、策略验证与风险控制，当前仅展示历史 DEMO 数据。",
};

export default async function DashboardPage() {
  const [state, symbols, latestReport, portfolio] = await Promise.all([
    getMarketState(),
    getMarketSymbols(),
    getLatestReport(),
    getPortfolio(),
  ]);

  return (
    <EmergentixHome
      state={state}
      symbols={symbols}
      latestReport={latestReport}
      portfolio={portfolio}
    />
  );
}
