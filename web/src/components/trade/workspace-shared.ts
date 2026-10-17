import type { Order } from "@/lib/trade/types";
import type { TradingData } from "./useTradingData";

export interface WorkspaceData {
  system: TradingData["system"];
  ticker: TradingData["ticker"];
  balances: TradingData["balances"];
  orders: TradingData["orders"];
  online: boolean;
  syncing: boolean;
  feedError: string | null;
  coreError: string | null;
  lastTickAt: number | null;
}

export const STALE_THRESHOLD_MS = 20_000;

export function canCancelOrder(order: Order): boolean {
  return order.status === "NEW" || order.status === "PARTIALLY_FILLED";
}

export type ToastKind = "success" | "error" | "warning" | "info";
