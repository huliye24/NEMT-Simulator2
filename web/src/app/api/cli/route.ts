import { getCliToken } from "@/lib/studio/cliToken";
import { portfolioSnapshot } from "@/lib/studio/demoPortfolio";

export const dynamic = "force-dynamic";

// Binance's public REST endpoint is blocked or flaky on some networks. Keep an
// ordered list of hosts and fail over: an explicit NEMT_BINANCE_HOST wins, then
// the canonical API, then the official market-data mirror.
const DEFAULT_BINANCE_HOSTS = ["https://api.binance.com", "https://data-api.binance.vision"];
const BINANCE_HOSTS = Array.from(
  new Set(
    [process.env.NEMT_BINANCE_HOST, ...DEFAULT_BINANCE_HOSTS]
      .filter((host): host is string => Boolean(host && host.trim()))
      .map((host) => host.trim().replace(/\/+$/, ""))
  )
);
const UPSTREAM_TIMEOUT_MS = 4_000;
const HOST_COOLDOWN_MS = 60_000;

// Remember the last host that answered so paginated backtest requests do not
// pay the timeout of a blocked host on every page.
let preferredHost: string | null = null;
const hostCooldownUntil = new Map<string, number>();

function orderedHosts(): string[] {
  const now = Date.now();
  const healthy = BINANCE_HOSTS.filter((host) => (hostCooldownUntil.get(host) ?? 0) <= now);
  const candidates = healthy.length ? healthy : BINANCE_HOSTS;
  if (preferredHost && candidates.includes(preferredHost)) {
    return [preferredHost, ...candidates.filter((host) => host !== preferredHost)];
  }
  return candidates;
}

const CORS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "content-type, x-nemt-cli-token",
  "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
};

const COMMANDS = [
  { cmd: "help", args: "", desc: "列出全部命令（无需 token）" },
  { cmd: "status", args: "", desc: "服务状态、服务器时间、运行时长" },
  { cmd: "portfolio", args: "", desc: "当前策略与持仓快照（含均价、盈亏、批次）" },
  { cmd: "quote", args: "symbol=BTCUSDT", desc: "24 小时行情（币安公开接口）" },
  { cmd: "klines", args: "symbol=BTCUSDT&interval=15m&limit=100&endTime=毫秒", desc: "K 线序列（endTime 用于向前翻页）" },
  { cmd: "symbols", args: "query=BTC", desc: "交易对检索" },
];

const STARTED_AT = Date.now();

export async function OPTIONS() {
  return new Response(null, { status: 204, headers: CORS });
}

export async function GET(request: Request) {
  return handle(request);
}

export async function POST(request: Request) {
  return handle(request);
}

async function fetchUpstream(
  path: string,
  query: Record<string, string | number | undefined>
): Promise<{ payload: unknown; host: string }> {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(query)) {
    if (value !== undefined && value !== null && value !== "") search.set(key, String(value));
  }

  const failures: string[] = [];
  for (const host of orderedHosts()) {
    try {
      const response = await fetch(`${host}${path}?${search.toString()}`, {
        cache: "no-store",
        signal: AbortSignal.timeout(UPSTREAM_TIMEOUT_MS),
      });
      if (!response.ok) {
        failures.push(`${host} HTTP ${response.status}`);
        hostCooldownUntil.set(host, Date.now() + HOST_COOLDOWN_MS);
        continue;
      }
      preferredHost = host;
      hostCooldownUntil.delete(host);
      return { payload: await response.json(), host };
    } catch (error) {
      const reason = error instanceof Error ? error.message : "unreachable";
      failures.push(`${host} ${reason}`);
      hostCooldownUntil.set(host, Date.now() + HOST_COOLDOWN_MS);
    }
  }

  throw new Error(
    `上游行情接口不可达（已尝试 ${BINANCE_HOSTS.length} 个主机；可用 NEMT_BINANCE_HOST 指定镜像）：${failures.join("；")}`
  );
}

async function handle(request: Request) {
  const url = new URL(request.url);
  const params: Record<string, string> = {};
  for (const [key, value] of url.searchParams) params[key] = value;

  if (request.method === "POST") {
    const body = (await request.json().catch(() => null)) as Record<string, string> | null;
    if (body) {
      for (const [key, value] of Object.entries(body)) {
        if (value !== undefined && value !== null) params[key] = String(value);
      }
    }
  }

  const cmd = (params.cmd ?? "help").toLowerCase();
  const token = params.token ?? request.headers.get("x-nemt-cli-token") ?? "";

  if (cmd === "help") {
    return json({
      ok: true,
      name: "nemt-cli",
      version: "1.0.0",
      usage: "GET /api/cli?cmd=<command>&token=<token>&...args",
      auth: "token 可通过 query ?token= 或请求头 x-nemt-cli-token 传入；help 免鉴权",
      commands: COMMANDS,
    });
  }

  const expected = await getCliToken();
  if (token !== expected) {
    return json({ ok: false, error: "token 无效，请到 设置 → CLI 接口 复制最新 token" }, 401);
  }

  try {
    switch (cmd) {
      case "status":
        return json({
          ok: true,
          cmd,
          serverTime: new Date().toISOString(),
          uptimeSeconds: Math.round((Date.now() - STARTED_AT) / 1000),
          version: "1.0.0",
          strategies: portfolioSnapshot().length,
          marketHosts: BINANCE_HOSTS,
        });

      case "portfolio": {
        const strategies = portfolioSnapshot();
        return json({
          ok: true,
          cmd,
          totalUnrealized: Number(strategies.reduce((sum, item) => sum + item.unrealized, 0).toFixed(2)),
          totalRealized: Number(strategies.reduce((sum, item) => sum + item.realized, 0).toFixed(2)),
          strategies,
        });
      }

      case "quote": {
        const symbol = (params.symbol ?? "BTCUSDT").toUpperCase();
        const { payload, host } = await fetchUpstream("/api/v3/ticker/24hr", { symbol });
        const ticker = payload as Record<string, unknown>;
        return json({
          ok: true,
          cmd,
          source: host,
          symbol: ticker.symbol,
          lastPrice: Number(ticker.lastPrice),
          priceChangePercent: Number(ticker.priceChangePercent),
          high24h: Number(ticker.highPrice),
          low24h: Number(ticker.lowPrice),
          volume24h: Number(ticker.volume),
          quoteVolume24h: Number(ticker.quoteVolume),
        });
      }

      case "klines": {
        const symbol = (params.symbol ?? "BTCUSDT").toUpperCase();
        const interval = params.interval ?? "15m";
        const limit = Math.min(1000, Math.max(1, Number(params.limit ?? 100)));
        const endTime = Number(params.endTime);
        const startTime = Number(params.startTime);
        const { payload, host } = await fetchUpstream("/api/v3/klines", {
          symbol,
          interval,
          limit,
          endTime: Number.isFinite(endTime) && endTime > 0 ? Math.floor(endTime) : undefined,
          startTime: Number.isFinite(startTime) && startTime > 0 ? Math.floor(startTime) : undefined,
        });
        if (!Array.isArray(payload)) {
          return json({ ok: false, cmd, error: "币安返回了非预期的 K 线数据" }, 200);
        }
        return json({
          ok: true,
          cmd,
          source: host,
          symbol,
          interval,
          count: payload.length,
          candles: (payload as unknown[][]).map((row) => ({
            openTime: new Date(Number(row[0])).toISOString(),
            open: Number(row[1]),
            high: Number(row[2]),
            low: Number(row[3]),
            close: Number(row[4]),
            volume: Number(row[5]),
          })),
        });
      }

      case "symbols": {
        const query = (params.query ?? "").toUpperCase();
        const { payload, host } = await fetchUpstream("/api/v3/exchangeInfo", {});
        const data = payload as { symbols?: Array<Record<string, unknown>> };
        const list = (data.symbols ?? [])
          .filter((item) => item.status === "TRADING")
          .map((item) => ({
            symbol: String(item.symbol),
            base: String(item.baseAsset),
            quote: String(item.quoteAsset),
          }))
          .filter((item) => !query || item.symbol.includes(query))
          .slice(0, 200);
        return json({ ok: true, cmd, source: host, count: list.length, symbols: list });
      }

      default:
        return json({ ok: false, error: `未知命令 ${cmd}，用 cmd=help 查看列表` }, 400);
    }
  } catch (error) {
    const reason = error instanceof Error ? error.message : "执行失败";
    return json({ ok: false, cmd, error: reason }, 200);
  }
}

function json(payload: unknown, status = 200) {
  return Response.json(payload, { status, headers: CORS });
}
