export type FillAction = "OPEN" | "ADD" | "REDUCE" | "CLOSE";

export interface Fill {
  /** 成交时间戳（毫秒） */
  at: number;
  action: FillAction;
  qty: number;
  price: number;
  fee: number;
}

export interface OpenLot {
  qty: number;
  price: number;
  at: number;
}

export interface PositionSummary {
  /** 当前持仓数量（正数） */
  qty: number;
  /** 剩余批次的加权平均成本 */
  avgCost: number;
  /** 已实现盈亏 */
  realized: number;
  /** 未实现盈亏 */
  unrealized: number;
  /** 累计手续费 */
  fees: number;
  /** FIFO 之后仍然持有的批次 */
  lots: OpenLot[];
  /** 价格相对均价的变动百分比 */
  priceChangePct: number;
}

const OPEN_ACTIONS: FillAction[] = ["OPEN", "ADD"];

/**
 * 按先进先出把成交流水折算成持仓：
 * 开仓/加仓入队，减仓/平仓从最早的批次开始消耗。
 */
export function summarize(
  fills: Fill[],
  mark: number,
  side: "LONG" | "SHORT" | "NEUTRAL"
): PositionSummary {
  const sorted = [...fills].sort((a, b) => a.at - b.at);
  const lots: OpenLot[] = [];
  let realized = 0;
  let fees = 0;

  for (const fill of sorted) {
    fees += fill.fee;
    if (OPEN_ACTIONS.includes(fill.action)) {
      lots.push({ qty: fill.qty, price: fill.price, at: fill.at });
      continue;
    }
    let remaining = fill.qty;
    while (remaining > 1e-9 && lots.length) {
      const lot = lots[0];
      const take = Math.min(lot.qty, remaining);
      const diff = side === "SHORT" ? lot.price - fill.price : fill.price - lot.price;
      realized += diff * take;
      lot.qty -= take;
      remaining -= take;
      if (lot.qty <= 1e-9) lots.shift();
    }
  }

  const qty = lots.reduce((total, lot) => total + lot.qty, 0);
  const cost = lots.reduce((total, lot) => total + lot.qty * lot.price, 0);
  const avgCost = qty > 0 ? cost / qty : 0;
  const unrealized =
    qty > 0 ? (side === "SHORT" ? avgCost - mark : mark - avgCost) * qty : 0;
  const priceChangePct = avgCost > 0 ? ((mark - avgCost) / avgCost) * 100 : 0;

  return { qty, avgCost, realized, unrealized, fees, lots, priceChangePct };
}

export const ACTION_LABEL: Record<FillAction, string> = {
  OPEN: "开仓",
  ADD: "加仓",
  REDUCE: "减仓",
  CLOSE: "平仓",
};

export interface FillRow extends Fill {
  /** 这一笔产生的已实现盈亏（开仓为 0） */
  realized: number;
  /** 这一笔成交后的持仓数量 */
  qtyAfter: number;
}

/** 逐笔标注：动作、已实现盈亏、成交后持仓 */
export function annotateFills(fills: Fill[], side: "LONG" | "SHORT" | "NEUTRAL"): FillRow[] {
  const sorted = [...fills].sort((a, b) => a.at - b.at);
  const lots: OpenLot[] = [];
  return sorted.map((fill) => {
    let realized = 0;
    if (OPEN_ACTIONS.includes(fill.action)) {
      lots.push({ qty: fill.qty, price: fill.price, at: fill.at });
    } else {
      let remaining = fill.qty;
      while (remaining > 1e-9 && lots.length) {
        const lot = lots[0];
        const take = Math.min(lot.qty, remaining);
        const diff = side === "SHORT" ? lot.price - fill.price : fill.price - lot.price;
        realized += diff * take;
        lot.qty -= take;
        remaining -= take;
        if (lot.qty <= 1e-9) lots.shift();
      }
    }
    const qtyAfter = lots.reduce((total, lot) => total + lot.qty, 0);
    return { ...fill, realized, qtyAfter };
  });
}
