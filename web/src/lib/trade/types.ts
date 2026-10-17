export type Mode = "DEMO" | "TESTNET" | "LIVE";
export type Role = "viewer" | "trader" | "admin";
export type OrderSide = "BUY" | "SELL";
export type OrderKind = "MARKET" | "LIMIT";
export type OrderStatus =
  | "NEW"
  | "PARTIALLY_FILLED"
  | "FILLED"
  | "CANCELED"
  | "EXPIRED"
  | "REJECTED"
  | "PENDING_RECONCILIATION";

export interface User {
  username: string;
  roles: Role[];
}

export interface Session {
  authenticated: boolean;
  user: User;
  csrf_token: string;
  expires_at: string;
  mode: Mode;
}

export interface Health {
  status: string;
  mode: Mode;
  version: string;
  server_time: string;
}

export interface Ticker {
  symbol: string;
  last_price: string;
  price_change: string;
  price_change_percent: string;
  high_price: string;
  low_price: string;
  volume: string;
  quote_volume: string;
  event_time: string | null;
  fetched_at: string;
  source: "binance" | "demo";
  stale: boolean;
}

export interface Kline {
  open_time: number;
  open_time_iso: string;
  open: string;
  high: string;
  low: string;
  close: string;
  volume: string;
  close_time: number;
  is_closed: boolean;
}

export interface Klines {
  symbol: string;
  interval: string;
  source: "binance" | "demo";
  stale: boolean;
  fetched_at: string;
  items: Kline[];
}

export interface Balance {
  asset: string;
  free: string;
  locked: string;
  total: string;
}

export interface Balances {
  mode: Mode;
  account_status: "CONNECTED" | "NOT_CONFIGURED" | "DISCONNECTED" | "ERROR";
  connected: boolean;
  source: "demo" | "binance" | "none";
  fetched_at: string | null;
  stale: boolean;
  note: string | null;
  balances: Balance[];
}

export interface RiskCheck {
  code: string;
  passed: boolean;
  message: string;
}

export interface RiskDecision {
  approved: boolean;
  checked_at: string;
  reasons: string[];
  checks: RiskCheck[];
}

export interface OrderDraft {
  symbol: string;
  side: OrderSide;
  type: OrderKind;
  time_in_force: string;
  quantity: string;
  price: string | null;
  latest_price: string;
  estimated_notional: string;
  estimated_fee: string;
  fee_asset: string;
  normalized: boolean;
}

export interface OrderPreview {
  preview_token: string;
  expires_at: string;
  draft: OrderDraft;
  risk: RiskDecision;
  warnings: string[];
  mode: Mode;
  market_source: "binance" | "demo";
  market_fetched_at: string;
  account_fetched_at: string | null;
  account_stale: boolean;
}

export interface Fill {
  id: string;
  exchange_trade_id: string | null;
  price: string;
  quantity: string;
  commission: string;
  commission_asset: string | null;
  filled_at: string;
}

export interface Order {
  id: string;
  client_order_id: string;
  exchange_order_id: string | null;
  mode: Mode;
  symbol: string;
  side: OrderSide;
  type: OrderKind;
  time_in_force: string | null;
  price: string | null;
  quantity: string;
  filled_qty: string;
  avg_fill_price: string | null;
  status: OrderStatus;
  fee: string;
  fee_asset: string | null;
  reserved_amount: string;
  reserved_asset: string | null;
  error_code: string | null;
  error_message: string | null;
  created_at: string;
  updated_at: string;
  submitted_at: string | null;
  risk: RiskDecision | null;
  fills: Fill[];
}

export interface OrderCreateResponse {
  order: Order;
  replayed: boolean;
}

export interface OrdersResponse {
  orders: Order[];
  count: number;
  open_count: number;
  status_filter: string | null;
}

export interface FlagState {
  pause_new_orders: boolean;
  pause_reason: string | null;
  pause_updated_at: string | null;
  pause_updated_by: string | null;
}

export interface Limits {
  min_order_notional: string;
  max_order_notional: string;
  max_daily_notional: string;
  max_position_notional: string;
  max_open_orders: number;
  max_orders_per_minute: number;
  market_stale_seconds: number;
  account_stale_seconds: number;
}

export interface MarketHealth {
  status: "ok" | "stale" | "unavailable";
  source: "binance" | "demo" | null;
  last_price: string | null;
  fetched_at: string | null;
  age_seconds: number | null;
  stale: boolean;
}

export interface AccountHealth {
  status: Balances["account_status"];
  connected: boolean;
  source: Balances["source"];
  fetched_at: string | null;
  stale: boolean;
  note: string | null;
}

export interface SystemStatus {
  mode: Mode;
  version: string;
  server_time: string;
  server_ok: boolean;
  authenticated: boolean;
  user: User;
  flags: Record<string, boolean>;
  trading_enabled: boolean;
  live_trading_available: boolean;
  market: MarketHealth;
  account: AccountHealth;
  risk: FlagState;
  limits: Limits;
}

export interface OrderPreviewPayload {
  symbol: string;
  side: OrderSide;
  type: OrderKind;
  quantity: string;
  price?: string;
  time_in_force?: "GTC";
}

export interface CancelOpenOrdersResponse {
  ok: boolean;
  canceled: number;
  failed: { order_id: string; code: string; message: string }[];
  message: string;
}

export interface ApiErrorBody {
  code: string;
  message: string;
  request_id: string | null;
  details: Record<string, unknown> | null;
}

export type TradeTabKey = "overview" | "market" | "trade" | "orders" | "settings";
