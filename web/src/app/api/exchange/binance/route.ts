import { createHmac } from "node:crypto";

const HOSTS = {
  live: "https://api.binance.com",
  testnet: "https://testnet.binance.vision",
} as const;

const CORS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "content-type, x-mbx-apikey",
  "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
};

/**
 * 解析目标节点：显式传入的自定义地址 > 环境变量 > 官方域名。
 * 返回 null 表示自定义地址不合法。
 */
function resolveBase(testnet: boolean, override: string): string | null {
  const fallback = testnet ? HOSTS.testnet : (process.env.NEMT_BINANCE_HOST ?? HOSTS.live);
  if (!override) return fallback.replace(/\/+$/, "");
  if (!/^https:\/\/[A-Za-z0-9.-]+(:\d+)?$/i.test(override)) return null;
  return override.replace(/\/+$/, "");
}

/** 免鉴权的连通性探测 */
export async function GET(request: Request) {
  const url = new URL(request.url);
  const testnet = url.searchParams.get("testnet") === "1";
  const base = testnet ? HOSTS.testnet : HOSTS.live;
  const started = Date.now();
  try {
    const res = await fetch(`${base}/api/v3/ping`, { cache: "no-store" });
    return Response.json(
      { ok: res.ok, host: base, latencyMs: Date.now() - started, status: res.status },
      { headers: CORS }
    );
  } catch (error) {
    return Response.json(
      { ok: false, host: base, error: error instanceof Error ? error.message : "请求失败" },
      { headers: CORS }
    );
  }
}

export async function OPTIONS() {
  return new Response(null, { status: 204, headers: CORS });
}

interface CredsBody {
  apiKey?: string;
  apiSecret?: string;
  testnet?: boolean;
  baseUrl?: string;
}

/**
 * 用 API Key + Secret 调 /api/v3/account 验证连接。
 * 签名在服务端完成，Secret 只在这次请求里出现，不写盘、不写日志。
 */
export async function POST(request: Request) {
  let body: CredsBody | null = null;
  try {
    body = (await request.json()) as CredsBody;
  } catch {
    return Response.json({ ok: false, error: "请求体不是合法 JSON" }, { status: 400, headers: CORS });
  }

  const apiKey = (body?.apiKey ?? "").trim();
  const apiSecret = (body?.apiSecret ?? "").trim();
  const testnet = Boolean(body?.testnet);

  if (!apiKey || !apiSecret) {
    return Response.json({ ok: false, error: "请填写 API Key 和 Secret" }, { status: 400, headers: CORS });
  }

  const base = resolveBase(testnet, (body?.baseUrl ?? "").trim());
  if (!base) {
    return Response.json(
      { ok: false, error: "自定义节点必须是 https:// 开头的地址" },
      { status: 400, headers: CORS }
    );
  }
  const query = `timestamp=${Date.now()}&recvWindow=5000`;
  const signature = createHmac("sha256", apiSecret).update(query).digest("hex");
  const started = Date.now();

  try {
    const res = await fetch(`${base}/api/v3/account?${query}&signature=${signature}`, {
      headers: { "X-MBX-APIKEY": apiKey },
      cache: "no-store",
    });
    const payload = (await res.json()) as {
      msg?: string;
      code?: number;
      accountType?: string;
      canTrade?: boolean;
      canWithdraw?: boolean;
      canDeposit?: boolean;
      balances?: Array<{ asset: string; free: string; locked: string }>;
    };

    if (!res.ok) {
      const hint =
        payload.code === -2015
          ? "API Key 无效、IP 未加白名单，或该 Key 没有读取权限"
          : payload.code === -1021
            ? "本机时间与币安服务器偏差过大，请校准系统时间"
            : (payload.msg ?? "币安拒绝了这次请求");
      return Response.json(
        { ok: false, host: base, code: payload.code, error: hint },
        { status: 200, headers: CORS }
      );
    }

    const balances = (payload.balances ?? [])
      .map((item) => ({
        asset: item.asset,
        free: Number(item.free),
        locked: Number(item.locked),
        total: Number(item.free) + Number(item.locked),
      }))
      .filter((item) => item.total > 0)
      .sort((a, b) => b.total - a.total)
      .slice(0, 8);

    return Response.json(
      {
        ok: true,
        host: base,
        latencyMs: Date.now() - started,
        testnet,
        accountType: payload.accountType ?? "UNKNOWN",
        canTrade: Boolean(payload.canTrade),
        canWithdraw: Boolean(payload.canWithdraw),
        canDeposit: Boolean(payload.canDeposit),
        balances,
      },
      { headers: CORS }
    );
  } catch (error) {
    return Response.json(
      {
        ok: false,
        host: base,
        error: `无法连接币安服务器（${error instanceof Error ? error.message : "网络错误"}）—— 国内网络需要在「自定义节点」填写可用的代理地址`,
      },
      { status: 200, headers: CORS }
    );
  }
}
