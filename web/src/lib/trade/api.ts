import type {
  ApiErrorBody,
  Balances,
  CancelOpenOrdersResponse,
  FlagState,
  Health,
  Klines,
  Order,
  OrderCreateResponse,
  OrderPreview,
  OrderPreviewPayload,
  OrdersResponse,
  PaperCloseResult,
  PaperEquity,
  PaperFills,
  PaperOpenPayload,
  PaperPositions,
  Session,
  SignalsResponse,
  StrategyBoard,
  SystemStatus,
  Ticker,
} from "./types";

const BASE = "/api/v1";

export class ApiError extends Error {
  status: number;
  code: string;
  requestId: string | null;
  details: Record<string, unknown> | null;

  constructor(
    status: number,
    code: string,
    message: string,
    requestId: string | null = null,
    details: Record<string, unknown> | null = null
  ) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
    this.requestId = requestId;
    this.details = details;
  }
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers);
  if (init.body && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  headers.set("Accept", "application/json");

  let response: Response;
  try {
    response = await fetch(`${BASE}${path}`, {
      ...init,
      headers,
      credentials: "same-origin",
      cache: "no-store",
    });
  } catch {
    throw new ApiError(
      0,
      "network_error",
      typeof navigator !== "undefined" && !navigator.onLine
        ? "网络已断开，交易写操作已禁用"
        : "无法连接 NEMT 服务端，请检查网络或后端状态"
    );
  }

  const text = await response.text();
  let payload: unknown = null;
  if (text) {
    try {
      payload = JSON.parse(text);
    } catch {
      payload = null;
    }
  }

  if (!response.ok) {
    const errorBody = (payload as { error?: ApiErrorBody } | null)?.error;
    throw new ApiError(
      response.status,
      errorBody?.code ?? "http_error",
      errorBody?.message ?? `请求失败（HTTP ${response.status}）`,
      errorBody?.request_id ?? response.headers.get("x-request-id"),
      errorBody?.details ?? null
    );
  }
  return payload as T;
}

function csrfHeader(csrfToken: string): HeadersInit {
  return { "X-CSRF-Token": csrfToken };
}

export const tradeApi = {
  health(): Promise<Health> {
    return request<Health>("/health");
  },

  getMe(): Promise<Session> {
    return request<Session>("/auth/me");
  },

  login(username: string, password: string): Promise<Session> {
    return request<Session>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ username, password }),
    });
  },

  demoLogin(account: "viewer" | "demo" | "admin" = "demo"): Promise<Session> {
    return request<Session>("/auth/demo", {
      method: "POST",
      body: JSON.stringify({ account }),
    });
  },

  logout(csrfToken: string): Promise<void> {
    return request<void>("/auth/logout", {
      method: "POST",
      headers: csrfHeader(csrfToken),
    });
  },

  getSystemStatus(): Promise<SystemStatus> {
    return request<SystemStatus>("/system/status");
  },

  getTicker(symbol = "BTCUSDT"): Promise<Ticker> {
    return request<Ticker>(`/market/ticker?symbol=${encodeURIComponent(symbol)}`);
  },

  getKlines(symbol: string, interval: string, limit = 90): Promise<Klines> {
    const query = new URLSearchParams({
      symbol,
      interval,
      limit: String(limit),
    });
    return request<Klines>(`/market/klines?${query.toString()}`);
  },

  getBalances(): Promise<Balances> {
    return request<Balances>("/account/balances");
  },

  listOrders(status?: "open" | "closed", limit = 100): Promise<OrdersResponse> {
    const query = new URLSearchParams({ limit: String(limit) });
    if (status) query.set("status", status);
    return request<OrdersResponse>(`/orders?${query.toString()}`);
  },

  previewOrder(csrfToken: string, payload: OrderPreviewPayload): Promise<OrderPreview> {
    return request<OrderPreview>("/orders/preview", {
      method: "POST",
      headers: csrfHeader(csrfToken),
      body: JSON.stringify(payload),
    });
  },

  createOrder(
    csrfToken: string,
    confirmationToken: string,
    idempotencyKey: string
  ): Promise<OrderCreateResponse> {
    return request<OrderCreateResponse>("/orders", {
      method: "POST",
      headers: csrfHeader(csrfToken),
      body: JSON.stringify({
        confirmation_token: confirmationToken,
        idempotency_key: idempotencyKey,
      }),
    });
  },

  cancelOrder(csrfToken: string, orderId: string): Promise<Order> {
    return request<Order>(`/orders/${encodeURIComponent(orderId)}/cancel`, {
      method: "POST",
      headers: csrfHeader(csrfToken),
    });
  },

  pauseOrders(csrfToken: string, reason: string): Promise<FlagState> {
    return request<FlagState>("/admin/pause-new-orders", {
      method: "POST",
      headers: csrfHeader(csrfToken),
      body: JSON.stringify({ reason }),
    });
  },

  resumeOrders(csrfToken: string, reason: string): Promise<FlagState> {
    return request<FlagState>("/admin/resume-new-orders", {
      method: "POST",
      headers: csrfHeader(csrfToken),
      body: JSON.stringify({ reason }),
    });
  },

  cancelOpenOrders(
    csrfToken: string,
    reason: string,
    confirm: boolean
  ): Promise<CancelOpenOrdersResponse> {
    return request<CancelOpenOrdersResponse>("/admin/cancel-open-orders", {
      method: "POST",
      headers: csrfHeader(csrfToken),
      body: JSON.stringify({ confirm, reason }),
    });
  },

  // --- Paper trading (纸上交易): simulated money, real quotes -------------

  getPaperPositions(): Promise<PaperPositions> {
    return request<PaperPositions>("/paper/positions");
  },

  getPaperFills(limit = 50): Promise<PaperFills> {
    return request<PaperFills>(`/paper/fills?limit=${limit}`);
  },

  getPaperEquity(limit = 200): Promise<PaperEquity> {
    return request<PaperEquity>(`/paper/equity?limit=${limit}`);
  },

  openPaperPosition(
    csrfToken: string,
    payload: PaperOpenPayload
  ): Promise<PaperPositions> {
    return request<PaperPositions>("/paper/positions", {
      method: "POST",
      headers: csrfHeader(csrfToken),
      body: JSON.stringify(payload),
    });
  },

  closePaperPosition(
    csrfToken: string,
    positionId: string,
    fraction = "1"
  ): Promise<PaperCloseResult> {
    return request<PaperCloseResult>(
      `/paper/positions/${encodeURIComponent(positionId)}/close`,
      {
        method: "POST",
        headers: csrfHeader(csrfToken),
        body: JSON.stringify({ fraction }),
      }
    );
  },

  resetPaperAccount(csrfToken: string): Promise<{ account: PaperPositions["account"] }> {
    return request<{ account: PaperPositions["account"] }>("/paper/reset", {
      method: "POST",
      headers: csrfHeader(csrfToken),
    });
  },

  // --- NEMT signal board (相位/动量) --------------------------------------

  getSignals(interval = "15m"): Promise<SignalsResponse> {
    return request<SignalsResponse>(
      `/signals/nemt?interval=${encodeURIComponent(interval)}`
    );
  },

  // --- Strategy board (auto trader) ---------------------------------------

  getStrategyBoard(): Promise<StrategyBoard> {
    return request<StrategyBoard>("/strategy/board");
  },

  setAutoTrade(
    csrfToken: string,
    enabled: boolean
  ): Promise<{ enabled: boolean; last_run_at: string | null }> {
    return request<{ enabled: boolean; last_run_at: string | null }>(
      "/strategy/auto-trade",
      {
        method: "POST",
        headers: csrfHeader(csrfToken),
        body: JSON.stringify({ enabled }),
      }
    );
  },

  runAutoTradeOnce(
    csrfToken: string
  ): Promise<{ decisions: unknown[]; count: number }> {
    return request<{ decisions: unknown[]; count: number }>(
      "/strategy/run-once",
      { method: "POST", headers: csrfHeader(csrfToken) }
    );
  },
};

export function riskReasonsFromError(error: unknown): string[] {
  if (!(error instanceof ApiError) || !error.details) return [];
  const risk = error.details.risk as { reasons?: unknown } | undefined;
  if (!risk || !Array.isArray(risk.reasons)) return [];
  return risk.reasons.filter((item): item is string => typeof item === "string");
}
