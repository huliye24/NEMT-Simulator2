import type {
  Balances,
  Kline,
  Klines,
  OrdersResponse,
  Session,
  SystemStatus,
  Ticker,
} from "@/lib/trade/types";

const BASE_PRICE = 81_920;

export function createLocalTicker(): Ticker {
  const now = new Date().toISOString();
  return {
    symbol: "BTCUSDT",
    last_price: "81996.70",
    price_change: "381.93",
    price_change_percent: "0.47",
    high_price: "82264.18",
    low_price: "81084.42",
    volume: "12483.72",
    quote_volume: "1024389124.66",
    event_time: now,
    fetched_at: now,
    source: "demo",
    stale: false,
  };
}

export function createLocalBalances(): Balances {
  return {
    mode: "DEMO",
    account_status: "CONNECTED",
    connected: true,
    source: "demo",
    fetched_at: new Date().toISOString(),
    stale: false,
    note: "本地 DEMO 账户",
    balances: [
      { asset: "USDT", free: "10000.00", locked: "0.00", total: "10000.00" },
      { asset: "BTC", free: "0.002", locked: "0.000", total: "0.002" },
    ],
  };
}

export function createLocalOrders(): OrdersResponse {
  return { orders: [], count: 0, open_count: 0, status_filter: null };
}

export function createLocalSystem(session: Session): SystemStatus {
  const now = new Date().toISOString();
  return {
    mode: "DEMO",
    version: "local",
    server_time: now,
    server_ok: true,
    authenticated: true,
    user: session.user,
    flags: {},
    trading_enabled: false,
    live_trading_available: false,
    market: {
      status: "ok",
      source: "demo",
      last_price: "81996.70",
      fetched_at: now,
      age_seconds: 0,
      stale: false,
    },
    account: {
      status: "CONNECTED",
      connected: true,
      source: "demo",
      fetched_at: now,
      stale: false,
      note: "本地 DEMO 账户",
    },
    risk: {
      pause_new_orders: false,
      pause_reason: null,
      pause_updated_at: null,
      pause_updated_by: null,
    },
    limits: {
      min_order_notional: "10",
      max_order_notional: "1000",
      max_daily_notional: "10000",
      max_position_notional: "5000",
      max_open_orders: 5,
      max_orders_per_minute: 10,
      market_stale_seconds: 30,
      account_stale_seconds: 60,
    },
  };
}

const INTERVAL_MS: Record<string, number> = {
  "1m": 60_000,
  "5m": 300_000,
  "15m": 900_000,
  "1h": 3_600_000,
  "4h": 14_400_000,
  "1d": 86_400_000,
};

export function createLocalKlines(interval: string, limit = 120): Klines {
  const step = INTERVAL_MS[interval] ?? INTERVAL_MS["15m"];
  const end = Math.floor(Date.now() / step) * step;
  const items: Kline[] = Array.from({ length: limit }, (_, index) => {
    const phase = index / 8;
    const trend = index * 3.1;
    const wave = Math.sin(phase) * 155 + Math.sin(index / 3.1) * 48;
    const open = BASE_PRICE - 245 + trend + wave;
    const close = open + Math.sin(index * 1.73) * 54 + 8;
    const high = Math.max(open, close) + 22 + (index % 7) * 5;
    const low = Math.min(open, close) - 20 - (index % 5) * 6;
    const openTime = end - (limit - index) * step;
    return {
      open_time: openTime,
      open_time_iso: new Date(openTime).toISOString(),
      open: open.toFixed(2),
      high: high.toFixed(2),
      low: low.toFixed(2),
      close: close.toFixed(2),
      volume: (6 + Math.abs(Math.sin(index / 4)) * 18 + (index % 9) * 1.7).toFixed(3),
      close_time: openTime + step - 1,
      is_closed: index < limit - 1,
    };
  });

  return {
    symbol: "BTCUSDT",
    interval,
    source: "demo",
    stale: false,
    fetched_at: new Date().toISOString(),
    items,
  };
}
