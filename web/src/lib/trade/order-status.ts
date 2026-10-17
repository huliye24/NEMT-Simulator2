import type { OrderStatus } from "./types";

export const ORDER_STATUS_LABEL: Record<OrderStatus, string> = {
  NEW: "未成交",
  PARTIALLY_FILLED: "部分成交",
  FILLED: "已成交",
  CANCELED: "已撤销",
  EXPIRED: "已过期",
  REJECTED: "已拒绝",
  PENDING_RECONCILIATION: "待对账",
};

export function orderStatusTone(status: OrderStatus): string {
  switch (status) {
    case "FILLED":
      return "text-emerald-400";
    case "PARTIALLY_FILLED":
      return "text-amber-300";
    case "NEW":
      return "text-cyan-300";
    case "REJECTED":
      return "text-rose-400";
    case "PENDING_RECONCILIATION":
      return "text-amber-300";
    default:
      return "text-slate-400";
  }
}

export function orderStatusChip(status: OrderStatus): string {
  switch (status) {
    case "FILLED":
      return "trade-chip-cyan text-emerald-300 border-emerald-400/25 bg-emerald-400/10";
    case "PARTIALLY_FILLED":
      return "trade-chip-amber";
    case "NEW":
      return "trade-chip-cyan";
    case "REJECTED":
      return "trade-chip-danger";
    case "PENDING_RECONCILIATION":
      return "trade-chip-amber";
    default:
      return "trade-chip";
  }
}

export function isOpenOrder(status: OrderStatus): boolean {
  return (
    status === "NEW" ||
    status === "PARTIALLY_FILLED" ||
    status === "PENDING_RECONCILIATION"
  );
}
