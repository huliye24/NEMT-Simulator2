import type { TradingData } from "../../useTradingData";

export function findAsset(data: TradingData, asset: string) {
  const item = data.balances?.balances.find((entry) => entry.asset === asset);
  return {
    asset,
    free: Number(item?.free ?? 0),
    locked: Number(item?.locked ?? 0),
    total: Number(item?.total ?? 0),
    raw: item ?? null,
  };
}

export function accountEquity(data: TradingData): number {
  const usdt = findAsset(data, "USDT");
  const btc = findAsset(data, "BTC");
  const btcPrice = Number(data.ticker?.last_price ?? 0);
  return usdt.total + btc.total * btcPrice;
}
