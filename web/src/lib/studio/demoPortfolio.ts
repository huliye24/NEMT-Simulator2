import { summarize, type Fill } from "./positionMath";

export type StrategyState = "运行中" | "已暂停";
export type Market = "PERPETUAL" | "SPOT" | "HEDGE";
export type LegSide = "LONG" | "SHORT" | "NEUTRAL";

export interface Leg {
  symbol: string;
  market: Market;
  side: LegSide;
  leverage: number;
  unit: string;
  mark: string;
  margin: string;
  fills: Fill[];
}

export interface Strategy {
  id: string;
  name: string;
  code: string;
  version: string;
  timeframe: string;
  state: StrategyState;
  signal: string;
  risk: string;
  legs: Leg[];
}

const HOUR = 3_600_000;
const NOW = Date.now();

/**
 * 演示用组合：一个策略可以只做单币，也可以是一篮子组合；
 * 每条腿由多笔成交（分批建仓 / 加仓 / 减仓）构成。
 */
export const STRATEGIES: Strategy[] = [
  {
    id: "emg-01", name: "NEMT Momentum", code: "EMG-01", version: "v1.8", timeframe: "15m",
    state: "运行中", signal: "17:42 加仓", risk: "62%",
    legs: [
      {
        symbol: "BTC/USDT", market: "PERPETUAL", side: "LONG", leverage: 5, unit: "BTC",
        mark: "82,176.80", margin: "6.8%",
        fills: [
          { at: NOW - 6 * HOUR, action: "OPEN", qty: 0.015, price: 81200.0, fee: 0.49 },
          { at: NOW - 5 * HOUR, action: "ADD", qty: 0.012, price: 81540.0, fee: 0.39 },
          { at: NOW - 4 * HOUR, action: "ADD", qty: 0.01, price: 81880.0, fee: 0.33 },
          { at: NOW - 2 * HOUR, action: "REDUCE", qty: 0.005, price: 82050.0, fee: 0.16 },
          { at: NOW - 1 * HOUR, action: "ADD", qty: 0.01, price: 81990.0, fee: 0.33 },
        ],
      },
      {
        symbol: "SOL/USDT", market: "PERPETUAL", side: "LONG", leverage: 3, unit: "SOL",
        mark: "143.06", margin: "3.1%",
        fills: [
          { at: NOW - 7 * HOUR, action: "OPEN", qty: 1.6, price: 141.2, fee: 0.09 },
          { at: NOW - 3 * HOUR, action: "ADD", qty: 1.6, price: 142.44, fee: 0.09 },
        ],
      },
    ],
  },
  {
    id: "mr-21", name: "Mean Revert 21", code: "MR-21", version: "v2.3", timeframe: "1h",
    state: "已暂停", signal: "等待人工确认", risk: "18%",
    legs: [
      {
        symbol: "ETH/USDT", market: "PERPETUAL", side: "SHORT", leverage: 3, unit: "ETH",
        mark: "3,119.70", margin: "4.2%",
        fills: [
          { at: NOW - 9 * HOUR, action: "OPEN", qty: 0.4, price: 3132.4, fee: 0.5 },
          { at: NOW - 8 * HOUR, action: "ADD", qty: 0.21, price: 3121.0, fee: 0.26 },
        ],
      },
    ],
  },
  {
    id: "arb-04", name: "Basis Neutral", code: "ARB-04", version: "v1.2", timeframe: "1h",
    state: "运行中", signal: "17:38 再平衡", risk: "34%",
    legs: [
      {
        symbol: "BTC-PERP", market: "HEDGE", side: "NEUTRAL", leverage: 2, unit: "BTC",
        mark: "82,176.80", margin: "2.9%",
        fills: [
          { at: NOW - 10 * HOUR, action: "OPEN", qty: 0.02, price: 81990.0, fee: 0.65 },
          { at: NOW - 5 * HOUR, action: "REDUCE", qty: 0.002, price: 82120.0, fee: 0.07 },
        ],
      },
    ],
  },
];

export function toNumber(value: string): number {
  return Number(value.replace(/[^0-9.-]/g, ""));
}

export function signed(value: number, digits = 2): string {
  return `${value > 0 ? "+" : ""}${value.toFixed(digits)}`;
}

export function legSummary(leg: Leg) {
  return summarize(leg.fills, toNumber(leg.mark), leg.side);
}

/** 把组合拍平成持仓快照，供 CLI / 外部 AI 读取 */
export function portfolioSnapshot() {
  return STRATEGIES.map((strategy) => {
    const legs = strategy.legs.map((leg) => {
      const s = legSummary(leg);
      return {
        symbol: leg.symbol,
        market: leg.market,
        side: leg.side,
        leverage: leg.leverage,
        qty: Number(s.qty.toFixed(6)),
        avgCost: Number(s.avgCost.toFixed(2)),
        mark: toNumber(leg.mark),
        unrealized: Number(s.unrealized.toFixed(2)),
        realized: Number(s.realized.toFixed(2)),
        fees: Number(s.fees.toFixed(2)),
        margin: leg.margin,
        lots: s.lots.map((lot) => ({ qty: lot.qty, price: lot.price, at: new Date(lot.at).toISOString() })),
        fills: leg.fills.length,
      };
    });
    const unrealized = legs.reduce((sum, leg) => sum + leg.unrealized, 0);
    const realized = legs.reduce((sum, leg) => sum + leg.realized, 0);
    return {
      id: strategy.id,
      name: strategy.name,
      code: strategy.code,
      version: strategy.version,
      timeframe: strategy.timeframe,
      state: strategy.state,
      risk: strategy.risk,
      legCount: legs.length,
      unrealized: Number(unrealized.toFixed(2)),
      realized: Number(realized.toFixed(2)),
      legs,
    };
  });
}
