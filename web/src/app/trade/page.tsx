import type { Metadata } from "next";
import TradeApp from "@/components/trade/TradeApp";

export const metadata: Metadata = {
  title: "Trade",
  description:
    "NEMT Trade — mobile-first Binance Spot DEMO/Testnet terminal. Server-side risk controls, one-time confirmation and no browser-held exchange keys.",
};

export default function TradePage() {
  return <TradeApp />;
}
