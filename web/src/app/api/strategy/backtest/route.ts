import { spawn } from "node:child_process";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { randomUUID } from "node:crypto";
import { getCliToken } from "@/lib/studio/cliToken";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

const BINANCE_HOSTS = Array.from(
  new Set(
    [
      process.env.NEMT_BINANCE_HOST,
      "https://data-api.binance.vision",
      "https://api.binance.com",
    ]
      .filter((host): host is string => Boolean(host && host.trim()))
      .map((host) => host.trim().replace(/\/+$/, ""))
  )
);
const MAX_FILES = 80;
const MAX_TOTAL_BYTES = 2_000_000;

interface KlineRow {
  open_time: number;
  open: string;
  high: string;
  low: string;
  close: string;
  volume: string;
  close_time: number;
}

async function fetchKlines(symbol: string, interval: string, limit: number): Promise<KlineRow[]> {
  const query = new URLSearchParams({
    symbol,
    interval,
    limit: String(Math.min(1000, Math.max(50, limit))),
  });
  const failures: string[] = [];
  for (const host of BINANCE_HOSTS) {
    try {
      const response = await fetch(`${host}/api/v3/klines?${query.toString()}`, {
        cache: "no-store",
        signal: AbortSignal.timeout(15_000),
      });
      if (!response.ok) {
        failures.push(`${host} HTTP ${response.status}`);
        continue;
      }
      const rows = (await response.json()) as unknown[][];
      return rows.map((row) => ({
        open_time: Number(row[0]),
        open: String(row[1]),
        high: String(row[2]),
        low: String(row[3]),
        close: String(row[4]),
        volume: String(row[5]),
        close_time: Number(row[6]),
      }));
    } catch (error) {
      failures.push(`${host} ${error instanceof Error ? error.message : "unreachable"}`);
    }
  }
  throw new Error(`行情源不可达：${failures.join("；")}`);
}

function writeCsv(filePath: string, rows: KlineRow[]): void {
  const lines = ["open_time,open,high,low,close,volume,close_time"];
  for (const row of rows) {
    lines.push(
      `${row.open_time},${row.open},${row.high},${row.low},${row.close},${row.volume},${row.close_time}`
    );
  }
  fs.writeFileSync(filePath, `${lines.join("\n")}\n`, "utf8");
}

function safeRelativePath(raw: string): string | null {
  const normalized = raw.replace(/\\/g, "/").replace(/^\/+/, "");
  const parts = normalized.split("/").filter((part) => part.length > 0);
  if (!parts.length || parts.some((part) => part === "." || part === "..")) return null;
  return parts.join("/");
}

function pythonExecutable(): string {
  const candidates = [
    process.env.NEMT_PYTHON,
    path.join(process.cwd(), "..", "venv", "Scripts", "python.exe"),
    path.join(process.cwd(), "..", ".venv-bt", "Scripts", "python.exe"),
    "python",
  ];
  for (const candidate of candidates) {
    if (!candidate) continue;
    if (candidate === "python" || fs.existsSync(candidate)) return candidate;
  }
  return "python";
}

function json(payload: unknown, status = 200) {
  return Response.json(payload, { status });
}

export async function POST(request: Request) {
  if (process.env.NODE_ENV === "production" && process.env.NEMT_ALLOW_LOCAL_STRATEGY_RUNNER !== "1") {
    return json({ ok: false, error: "本地策略执行仅在开发环境可用" }, 403);
  }

  const expected = await getCliToken();
  const token = request.headers.get("x-nemt-cli-token") ?? "";
  if (token !== expected) return json({ ok: false, error: "token 无效" }, 401);

  let body: {
    files?: Record<string, unknown>;
    entry?: string;
    initialEquity?: number;
    feeRate?: number;
    slippageRate?: number;
    bars?: number;
    symbol?: string;
  };
  try {
    body = (await request.json()) as typeof body;
  } catch {
    return json({ ok: false, error: "请求体不是合法 JSON" }, 400);
  }

  const files = body.files;
  if (!files || typeof files !== "object" || Array.isArray(files)) {
    return json({ ok: false, error: "缺少策略文件" }, 400);
  }
  const entries = Object.entries(files);
  if (!entries.length || entries.length > MAX_FILES) {
    return json({ ok: false, error: "策略文件数量不合法" }, 400);
  }
  let totalBytes = 0;
  for (const [, content] of entries) {
    if (typeof content !== "string") return json({ ok: false, error: "策略文件必须是文本" }, 400);
    totalBytes += Buffer.byteLength(content, "utf8");
  }
  if (totalBytes > MAX_TOTAL_BYTES) return json({ ok: false, error: "策略文件过大" }, 400);

  const entry = typeof body.entry === "string" ? safeRelativePath(body.entry) : null;
  if (!entry || !entry.endsWith(".py") || !(entry in files)) {
    return json({ ok: false, error: "请选择仓库中的 Python 策略入口" }, 400);
  }

  const runDir = path.join(process.cwd(), ".next", "strategy-runs", randomUUID());
  try {
    for (const [rawPath, content] of entries) {
      const relative = safeRelativePath(rawPath);
      if (!relative) return json({ ok: false, error: `非法文件路径：${rawPath}` }, 400);
      const target = path.join(runDir, relative);
      if (!target.startsWith(runDir + path.sep)) return json({ ok: false, error: "非法文件路径" }, 400);
      fs.mkdirSync(path.dirname(target), { recursive: true });
      fs.writeFileSync(target, content as string, "utf8");
    }

    const bars = Number.isFinite(body.bars) ? Math.min(1000, Math.max(50, Number(body.bars))) : 1000;
    const symbol = typeof body.symbol === "string" && /^[A-Z0-9]{5,20}$/i.test(body.symbol) ? body.symbol.toUpperCase() : "BTCUSDT";
    const [hourly, fourHour] = await Promise.all([fetchKlines(symbol, "1h", bars), fetchKlines(symbol, "4h", bars)]);
    const hourlyCsv = path.join(runDir, "__hourly.csv");
    const fourCsv = path.join(runDir, "__four_hour.csv");
    writeCsv(hourlyCsv, hourly);
    writeCsv(fourCsv, fourHour);

    const configPath = path.join(runDir, "__config.json");
    fs.writeFileSync(
      configPath,
      JSON.stringify({
        initial_equity: Number.isFinite(body.initialEquity) ? Number(body.initialEquity) : 10_000,
        fee_rate: Number.isFinite(body.feeRate) ? Number(body.feeRate) : 0.001,
        slippage_rate: Number.isFinite(body.slippageRate) ? Number(body.slippageRate) : 0.0005,
      }),
      "utf8"
    );

    const runner = path.join(process.cwd(), "scripts", "strategy_runner.py");
    const outputPath = path.join(runDir, "__result.json");
    const entryPath = path.join(runDir, entry);
    const python = pythonExecutable();
    const child = spawn(python, [runner, entryPath, hourlyCsv, fourCsv, configPath, outputPath], {
      cwd: runDir,
      stdio: "ignore",
      windowsHide: true,
    });
    const exitCode = await new Promise<number>((resolve) => {
      const timer = setTimeout(() => {
        child.kill();
        resolve(-1);
      }, 90_000);
      child.on("exit", (code) => {
        clearTimeout(timer);
        resolve(code ?? -1);
      });
      child.on("error", () => {
        clearTimeout(timer);
        resolve(-1);
      });
    });

    if (!fs.existsSync(outputPath)) {
      return json({
        ok: false,
        error: exitCode === -1 ? "策略执行超时" : `策略进程退出（code ${exitCode}），没有生成结果`,
      });
    }
    const result = JSON.parse(fs.readFileSync(outputPath, "utf8")) as {
      ok?: boolean;
      error?: string;
      traceback?: string;
      summary?: unknown;
      trades?: unknown;
      equity_curve?: unknown;
    };
    if (!result.ok) {
      return json({ ok: false, error: result.error ?? "策略执行失败", traceback: result.traceback });
    }
    return json({
      ok: true,
      entry,
      symbol,
      bars: { hourly: hourly.length, four_hour: fourHour.length },
      summary: result.summary,
      trades: result.trades,
      equity_curve: result.equity_curve,
    });
  } catch (error) {
    return json({ ok: false, error: error instanceof Error ? error.message : "策略执行失败" });
  } finally {
    fs.rmSync(runDir, { recursive: true, force: true });
  }
}
