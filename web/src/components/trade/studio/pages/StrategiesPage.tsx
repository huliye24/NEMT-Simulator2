"use client";

import { useEffect, useMemo, useState } from "react";
import Image from "next/image";
import type { StudioPageProps } from "../types";
import { runClientBacktest, type BacktestCandle, type BacktestResult, type BacktestStrategy, type StrategyParameters } from "../backtest/engine";
import { compileStrategyScript, STRATEGY_SCRIPTS } from "../backtest/strategyScript";
import { StudioIcon } from "../icons";
import backtestMuse from "../assets/emergentix-backtest-muse-v1.png";
import styles from "./StrategiesPage.module.css";

interface KlinePayload { ok?: boolean; error?: string; candles?: BacktestCandle[]; }
interface StrategyProfile { id: string; name: string; version: string; engine: BacktestStrategy; description: string; parameters: StrategyParameters; sourceCode: string; readme?: string; testCode?: string; language?: "pine" | "python"; builtIn?: boolean; }
type RepositoryFiles = Record<string, string>;
interface StrategyRepository { id: string; name: string; description: string; files: RepositoryFiles; updatedAt: string; }
interface RepositoryRun { id: string; repositoryId: string; configFile: string; strategyFile: string; createdAt: string; result: BacktestResult; candles: BacktestCandle[]; }

const STORE_KEY = "emergentix.strategy.profiles.v1";
const REPOSITORY_STORE_KEY = "emergentix.strategy.repositories.v1";
const REPOSITORY_RUN_STORE_KEY = "emergentix.strategy.runs.v1";
const CORE_TEMPLATE = `"""Shared indicators, signals, execution assumptions and risk controls."""
from dataclasses import dataclass

@dataclass(frozen=True)
class StrategyConfig:
    symbol: str
    interval: str
    initial_equity: float = 10_000.0
    fee_rate: float = 0.001
    slippage_rate: float = 0.0005
    risk_fraction: float = 0.005
`;
const CRYPTO_TEMPLATE = `"""Crypto breakout strategy using shared core primitives."""
# EMERGENZIX_ENGINE: breakout
from .core import StrategyConfig

def run_backtest(candles: list[dict], config: StrategyConfig) -> dict:
    """Return summary, trades and equity_curve."""
    raise NotImplementedError("Implement crypto rules")
`;
const EQUITY_TEMPLATE = `"""Equity-session breakout strategy."""
from .core import StrategyConfig

def run_backtest(candles: list[dict], config: StrategyConfig) -> dict:
    """Handle exchange sessions and corporate-action-adjusted data."""
    raise NotImplementedError("Implement equity rules")
`;
const README_TEMPLATE = `# New Strategy

## Hypothesis

Describe the market behavior this strategy attempts to capture.

## Data

- Symbol: BTC/USDT
- Primary interval: 1h

## Risk

Document fees, slippage, position sizing and drawdown limits.
`;
const TEST_TEMPLATE = `from strategies.core import StrategyConfig

def test_default_config_is_research_safe() -> None:
    config = StrategyConfig(symbol="BTCUSDT", interval="1h")
    assert config.initial_equity > 0
`;
const DEFAULT_REPOSITORY: RepositoryFiles = {
  "README.md": README_TEMPLATE,
  "strategies/core.py": CORE_TEMPLATE,
  "strategies/crypto_breakout.py": CRYPTO_TEMPLATE,
  "strategies/equity_breakout.py": EQUITY_TEMPLATE,
  "configs/btcusdt_1h.yaml": "market: crypto\nsymbol: BTCUSDT\ninterval: 1h\nfee_rate: 0.001\nslippage_rate: 0.0005\nrisk_fraction: 0.005\n",
  "configs/aapl_1d.yaml": "market: equity\nsymbol: AAPL\ninterval: 1d\nfee_rate: 0.0005\nslippage_rate: 0.0002\nrisk_fraction: 0.005\n",
  "tests/test_core.py": TEST_TEMPLATE,
};
const INITIAL_REPOSITORIES: StrategyRepository[] = [{
  id: "emx-str-001",
  name: "EMERGENZIX_EMX_STR_001",
  description: "Trend Filter & Volatility Breakout · multi-market research strategy",
  files: { ...DEFAULT_REPOSITORY },
  updatedAt: "刚刚",
}];
const BUILT_INS: StrategyProfile[] = [
  { id: "nemt-v1", name: "NEMT 临界动量", version: "v1.0", engine: "nemt", description: "捕捉波动扩张中的临界相变与方向偏移。", parameters: { recentWindow: 20, baselineWindow: 30, threshold: .72, volatilityRatio: .92 }, sourceCode: STRATEGY_SCRIPTS.nemt, builtIn: true },
  { id: "ma-v1", name: "均线交叉", version: "v1.0", engine: "ma_cross", description: "快速均线穿越慢速均线时切换方向。", parameters: { fast: 9, slow: 21 }, sourceCode: STRATEGY_SCRIPTS.ma_cross, builtIn: true },
  { id: "rsi-v1", name: "RSI 均值回归", version: "v1.0", engine: "rsi_reversion", description: "在超买与超卖区域反向进入，回归中轴退出。", parameters: { period: 14, low: 30, high: 70 }, sourceCode: STRATEGY_SCRIPTS.rsi_reversion, builtIn: true },
  { id: "breakout-v1", name: "布林突破", version: "v1.0", engine: "breakout", description: "价格突破波动带时顺势进入，回到均值时退出。", parameters: { period: 20, multiplier: 2 }, sourceCode: STRATEGY_SCRIPTS.breakout, builtIn: true },
];
const SYMBOLS = ["BTCUSDT", "ETHUSDT", "SOLUSDT"];
const RANGE_BARS: Record<string, Record<string, number>> = {
  "7d": { "15m": 672, "1h": 168, "4h": 42, "1d": 7 },
  "30d": { "1h": 720, "4h": 180, "1d": 30 },
  "90d": { "4h": 540, "1d": 90 },
};

function fmt(value: number, digits = 2): string { return Number.isFinite(value) ? value.toFixed(digits) : "—"; }

function readmeBlocks(source: string) {
  return source.split("\n").map((line, index) => {
    if (line.startsWith("# ")) return <h1 key={index}>{line.slice(2)}</h1>;
    if (line.startsWith("## ")) return <h2 key={index}>{line.slice(3)}</h2>;
    if (line.startsWith("- ")) return <li key={index}>{line.slice(2)}</li>;
    return line ? <p key={index}>{line}</p> : <br key={index} />;
  });
}

function parseRepositoryConfig(source: string): Record<string, string> {
  return Object.fromEntries(source.split("\n").map((line) => line.split(":", 2)).filter((parts) => parts.length === 2).map(([key, value]) => [key.trim(), value.trim()]));
}

function playbackMetrics(run: RepositoryRun, candleIndex: number) {
  const completed = run.result.trades.filter((trade) => trade.exitIndex <= candleIndex);
  const allPnl = run.result.trades.reduce((sum, trade) => sum + trade.pnl, 0);
  const initialEquity = run.result.endingEquity - allPnl;
  let equity = initialEquity;
  let peak = initialEquity;
  let maxDrawdown = 0;
  let wins = 0;
  let grossProfit = 0;
  let grossLoss = 0;
  completed.forEach((trade) => {
    equity += trade.pnl;
    peak = Math.max(peak, equity);
    maxDrawdown = Math.max(maxDrawdown, peak > 0 ? (peak - equity) / peak * 100 : 0);
    if (trade.pnl > 0) { wins += 1; grossProfit += trade.pnl; } else { grossLoss += Math.abs(trade.pnl); }
  });
  return { completed, equity, totalReturn: initialEquity > 0 ? (equity - initialEquity) / initialEquity * 100 : 0, maxDrawdown, winRate: completed.length ? wins / completed.length * 100 : 0, profitFactor: grossLoss ? grossProfit / grossLoss : grossProfit ? 999 : 0 };
}

const TRADINGVIEW_INTERVALS: Record<string, string> = { "15m": "15", "1h": "60", "4h": "240", "1d": "D" };

function chartPoint(candles: BacktestCandle[], index: number): { x: number; y: number } {
  const values = candles.map((item) => item.close);
  const min = Math.min(...values);
  const span = Math.max(1, Math.max(...values) - min);
  return { x: 20 + index / Math.max(1, values.length - 1) * 960, y: 250 - ((candles[index]?.close ?? min) - min) / span * 220 };
}

export default function StrategiesPage({ notify }: StudioPageProps) {
  const [profiles, setProfiles] = useState<StrategyProfile[]>(BUILT_INS);
  const [activeId, setActiveId] = useState(BUILT_INS[0].id);
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState<StrategyProfile>(BUILT_INS[0]);
  const [draftNew, setDraftNew] = useState(false);
  const [codeDraft, setCodeDraft] = useState(BUILT_INS[0].sourceCode);
  const [newDialog, setNewDialog] = useState(false);
  const [newName, setNewName] = useState("新策略");
  const [newFiles, setNewFiles] = useState<RepositoryFiles>({ ...DEFAULT_REPOSITORY });
  const [newFile, setNewFile] = useState("README.md");
  const [addingFile, setAddingFile] = useState(false);
  const [newFilePath, setNewFilePath] = useState("");
  const [repositories, setRepositories] = useState<StrategyRepository[]>(INITIAL_REPOSITORIES);
  const [openRepositoryId, setOpenRepositoryId] = useState<string | null>(null);
  const [repositoryFile, setRepositoryFile] = useState("README.md");
  const [editingRepositoryId, setEditingRepositoryId] = useState<string | null>(null);
  const [repositoryTab, setRepositoryTab] = useState<"code" | "runs" | "config">("code");
  const [repositoryConfigFile, setRepositoryConfigFile] = useState("configs/btcusdt_1h.yaml");
  const [repositoryRuns, setRepositoryRuns] = useState<RepositoryRun[]>([]);
  const [repositoryRunBusy, setRepositoryRunBusy] = useState(false);
  const [playbackRun, setPlaybackRun] = useState<RepositoryRun | null>(null);
  const [playbackIndex, setPlaybackIndex] = useState(0);
  const [playbackPlaying, setPlaybackPlaying] = useState(false);
  const [playbackSpeed, setPlaybackSpeed] = useState<1 | 2 | 4>(1);
  const [workbenchOpen, setWorkbenchOpen] = useState(false);
  const [symbol, setSymbol] = useState("BTCUSDT");
  const [interval, setInterval] = useState("1h");
  const [range, setRange] = useState("30d");
  const [capital, setCapital] = useState(1000);
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<BacktestResult | null>(null);
  const [candles, setCandles] = useState<BacktestCandle[]>([]);
  const [selectedTrade, setSelectedTrade] = useState(0);
  const activeProfile = profiles.find((item) => item.id === activeId) ?? profiles[0] ?? BUILT_INS[0];
  const currentRepository = repositories.find((item) => item.id === openRepositoryId) ?? null;
  const currentRepositoryRuns = currentRepository ? repositoryRuns.filter((item) => item.repositoryId === currentRepository.id) : [];
  const latestRepositoryRun = currentRepositoryRuns[0] ?? null;

  useEffect(() => {
    try {
      const saved = JSON.parse(localStorage.getItem(STORE_KEY) ?? "[]") as StrategyProfile[];
      if (Array.isArray(saved) && saved.length) setProfiles([...BUILT_INS, ...saved.filter((item) => !item.builtIn).map((item) => ({ ...item, sourceCode: item.sourceCode ?? STRATEGY_SCRIPTS[item.engine] }))]);
    } catch { /* ignore damaged local strategy metadata */ }
    try {
      const savedRepositories = JSON.parse(localStorage.getItem(REPOSITORY_STORE_KEY) ?? "[]") as StrategyRepository[];
      if (Array.isArray(savedRepositories) && savedRepositories.length) setRepositories(savedRepositories);
    } catch { /* ignore damaged local repository metadata */ }
    try {
      const savedRuns = JSON.parse(localStorage.getItem(REPOSITORY_RUN_STORE_KEY) ?? "[]") as RepositoryRun[];
      if (Array.isArray(savedRuns)) setRepositoryRuns(savedRuns);
    } catch { /* ignore damaged local run metadata */ }
  }, []);

  useEffect(() => { setCodeDraft(activeProfile.sourceCode); }, [activeId, activeProfile.sourceCode]);

  useEffect(() => {
    if (!playbackRun || !playbackPlaying) return;
    const timer = window.setInterval(() => {
      setPlaybackIndex((current) => {
        const next = Math.min(playbackRun.candles.length - 1, current + playbackSpeed);
        if (next >= playbackRun.candles.length - 1) setPlaybackPlaying(false);
        return next;
      });
    }, 110);
    return () => window.clearInterval(timer);
  }, [playbackPlaying, playbackRun, playbackSpeed]);

  function beginEdit(): void {
    if (activeProfile.builtIn) {
      duplicate();
      return;
    }
    setDraft({ ...activeProfile, parameters: { ...activeProfile.parameters } });
    setDraftNew(false);
    setEditing(true);
  }

  function duplicate(): void {
    const copy: StrategyProfile = { ...activeProfile, id: `strategy-${Date.now()}`, name: `${activeProfile.name} 升级版`, version: "v1.1", parameters: { ...activeProfile.parameters }, builtIn: false };
    setProfiles((current) => [...current, copy]);
    setActiveId(copy.id);
    setDraft(copy);
    setDraftNew(true);
    setEditing(true);
  }

  function createStrategy(): void {
    setEditingRepositoryId(null);
    setNewName("新策略");
    setNewFiles({ ...DEFAULT_REPOSITORY });
    setNewFile("README.md");
    setAddingFile(false);
    setNewDialog(true);
  }

  function confirmCreateStrategy(runNow = false): void {
    if (!newName.trim()) { notify("error", "策略仓库名称不能为空"); return; }
    const strategySource = newFiles["strategies/crypto_breakout.py"] ?? Object.entries(newFiles).find(([path]) => path.startsWith("strategies/") && path.endsWith(".py"))?.[1] ?? "";
    if (!/\b(def|class)\s+/.test(strategySource)) { notify("error", "strategies/ 中至少需要一个包含函数或类的 Python 文件"); return; }
    if (editingRepositoryId) {
      const nextRepositories = repositories.map((item) => item.id === editingRepositoryId ? { ...item, name: newName.trim(), files: { ...newFiles }, updatedAt: "刚刚" } : item);
      setRepositories(nextRepositories);
      localStorage.setItem(REPOSITORY_STORE_KEY, JSON.stringify(nextRepositories));
      setOpenRepositoryId(editingRepositoryId);
      setRepositoryFile(newFile);
      setEditingRepositoryId(null);
      setNewDialog(false);
      notify("success", "策略仓库已保存");
      return;
    }
    const created: StrategyProfile = { id: `strategy-${Date.now()}`, name: newName.trim(), version: "v1.0", engine: "nemt", description: `Python 策略仓库 · ${Object.keys(newFiles).length} files`, parameters: {}, sourceCode: strategySource, readme: newFiles["README.md"], testCode: newFiles["tests/test_core.py"], language: "python", builtIn: false };
    const next = [...profiles, created];
    setProfiles(next);
    setActiveId(created.id);
    setDraft(created);
    setDraftNew(true);
    setCodeDraft(created.sourceCode);
    setWorkbenchOpen(true);
    localStorage.setItem(STORE_KEY, JSON.stringify(next.filter((item) => !item.builtIn)));
    const repository: StrategyRepository = { id: created.id, name: newName.trim(), description: "Python 3.11 quantitative strategy repository", files: { ...newFiles }, updatedAt: "刚刚" };
    const nextRepositories = [...repositories, repository];
    setRepositories(nextRepositories);
    localStorage.setItem(REPOSITORY_STORE_KEY, JSON.stringify(nextRepositories));
    setOpenRepositoryId(repository.id);
    setRepositoryFile("README.md");
    setNewDialog(false);
    if (runNow) notify("warning", "策略仓库已创建；接入 Python 回测服务后即可运行");
  }

  function addRepositoryFile(): void {
    const path = newFilePath.trim().replace(/^\/+/, "");
    if (!path) return;
    if (newFiles[path] !== undefined) { notify("error", "文件已存在"); return; }
    setNewFiles((current) => ({ ...current, [path]: path.endsWith(".py") ? "\n" : path.endsWith(".yaml") || path.endsWith(".yml") ? "symbol: BTCUSDT\ninterval: 1h\n" : "" }));
    setNewFile(path);
    setNewFilePath("");
    setAddingFile(false);
  }

  function openRepository(id: string): void {
    setOpenRepositoryId(id);
    setRepositoryFile("README.md");
    setRepositoryTab("code");
  }

  async function runRepositoryBacktest(repository: StrategyRepository): Promise<void> {
    if (repositoryRunBusy) return;
    const configFiles = Object.keys(repository.files).filter((path) => path.startsWith("configs/") && /\.ya?ml$/i.test(path));
    const configFile = repository.files[repositoryConfigFile] ? repositoryConfigFile : configFiles[0];
    if (!configFile) { notify("error", "仓库中没有可用的 YAML 运行配置"); setRepositoryTab("config"); return; }
    const config = parseRepositoryConfig(repository.files[configFile]);
    const strategyFile = config.market === "equity" ? "strategies/equity_breakout.py" : "strategies/crypto_breakout.py";
    const sourceCode = repository.files[strategyFile] ?? "";
    const engine: BacktestStrategy = sourceCode.includes("EMERGENZIX_ENGINE: ma_cross") ? "ma_cross" : sourceCode.includes("EMERGENZIX_ENGINE: rsi_reversion") ? "rsi_reversion" : "breakout";
    const runSymbol = (config.symbol || "BTCUSDT").replace("/", "");
    const runInterval = config.interval || "1h";
    const runCapital = Math.max(100, Number(config.initial_equity) || 1000);
    setRepositoryRunBusy(true);
    try {
      const tokenResponse = await fetch("/api/cli/token", { cache: "no-store" });
      const tokenPayload = await tokenResponse.json() as { token?: string };
      if (!tokenPayload.token) throw new Error("无法取得行情访问令牌");
      const response = await fetch("/api/cli", { method: "POST", headers: { "Content-Type": "application/json", "X-NEMT-CLI-Token": tokenPayload.token }, body: JSON.stringify({ cmd: "klines", symbol: runSymbol, interval: runInterval, limit: String(RANGE_BARS["30d"]?.[runInterval] ?? 500) }) });
      const payload = await response.json() as KlinePayload;
      if (!payload.ok || !payload.candles?.length) throw new Error(payload.error ?? "没有取得回测行情");
      const nextResult = runClientBacktest(payload.candles, engine, runCapital, runInterval, {});
      const nextRun: RepositoryRun = { id: `run-${Date.now()}`, repositoryId: repository.id, configFile, strategyFile, createdAt: new Date().toISOString(), result: nextResult, candles: payload.candles };
      const nextRuns = [nextRun, ...repositoryRuns].slice(0, 20);
      setRepositoryRuns(nextRuns);
      localStorage.setItem(REPOSITORY_RUN_STORE_KEY, JSON.stringify(nextRuns));
      setPlaybackRun(nextRun);
      setPlaybackIndex(Math.min(30, payload.candles.length - 1));
      setPlaybackPlaying(true);
      notify("success", `回测播放器已启动 · ${runSymbol} ${runInterval}`);
    } catch (cause) {
      notify("error", cause instanceof Error ? cause.message : "仓库回测失败");
    } finally { setRepositoryRunBusy(false); }
  }

  function returnToRepositories(): void {
    setWorkbenchOpen(false);
    setResult(null);
    setOpenRepositoryId(null);
  }

  function cancelEdit(): void {
    if (draftNew) {
      setProfiles((current) => current.filter((item) => item.id !== draft.id));
      setActiveId(BUILT_INS[0].id);
    }
    setDraftNew(false);
    setEditing(false);
  }

  function saveDraft(): void {
    if (!draft.name.trim() || !draft.version.trim()) { notify("error", "策略名称和版本不能为空"); return; }
    let compiled;
    try { compiled = compileStrategyScript(draft.sourceCode); } catch (cause) { notify("error", cause instanceof Error ? cause.message : "策略代码无法编译"); return; }
    const savedDraft = { ...draft, engine: compiled.engine, parameters: compiled.parameters, builtIn: false };
    const next = profiles.map((item) => item.id === draft.id ? savedDraft : item);
    setProfiles(next);
    localStorage.setItem(STORE_KEY, JSON.stringify(next.filter((item) => !item.builtIn)));
    setDraftNew(false);
    setEditing(false);
    setResult(null);
    notify("success", `策略 ${draft.name} ${draft.version} 已保存`);
  }

  function saveCodeVersion(): void {
    if (activeProfile.language === "python") {
      const next = profiles.map((item) => item.id === activeId ? { ...item, sourceCode: codeDraft } : item);
      setProfiles(next);
      localStorage.setItem(STORE_KEY, JSON.stringify(next.filter((item) => !item.builtIn)));
      notify("success", "strategy.py 已保存");
      return;
    }
    let compiled;
    try { compiled = compileStrategyScript(codeDraft); } catch (cause) { notify("error", cause instanceof Error ? cause.message : "策略代码无法编译"); return; }
    const nextProfile: StrategyProfile = activeProfile.builtIn
      ? { ...activeProfile, id: `strategy-${Date.now()}`, name: `${activeProfile.name} AI 版本`, version: "v1.1", sourceCode: codeDraft, engine: compiled.engine, parameters: compiled.parameters, builtIn: false }
      : { ...activeProfile, sourceCode: codeDraft, engine: compiled.engine, parameters: compiled.parameters, builtIn: false };
    const next = activeProfile.builtIn ? [...profiles, nextProfile] : profiles.map((item) => item.id === activeId ? nextProfile : item);
    setProfiles(next);
    setActiveId(nextProfile.id);
    localStorage.setItem(STORE_KEY, JSON.stringify(next.filter((item) => !item.builtIn)));
    notify("success", `策略代码已保存 · 周期 ${compiled.interval}`);
  }

  async function copyPineCode(): Promise<void> {
    try {
      await navigator.clipboard.writeText(draft.sourceCode);
      notify("success", "Pine 代码已复制，可粘贴到 TradingView Pine Editor");
    } catch { notify("error", "复制失败，请在编辑器中手动选择代码"); }
  }

  function openTradingView(): void {
    const url = `https://www.tradingview.com/chart/?symbol=BINANCE%3A${encodeURIComponent(symbol)}&interval=${TRADINGVIEW_INTERVALS[interval] ?? "60"}`;
    window.open(url, "_blank", "noopener,noreferrer");
  }

  const path = useMemo(() => {
    if (candles.length < 2) return "";
    return candles.map((_, index) => { const point = chartPoint(candles, index); return `${index ? "L" : "M"}${point.x.toFixed(1)} ${point.y.toFixed(1)}`; }).join(" ");
  }, [candles]);

  async function run(sourceCode = codeDraft): Promise<void> {
    if (busy) return;
    setWorkbenchOpen(true);
    if (!sourceCode.includes("//@version=6")) {
      notify("warning", "Python 策略仓库已就绪，等待受控回测服务接入");
      return;
    }
    setBusy(true);
    setResult(null);
    try {
      const compiled = compileStrategyScript(sourceCode);
      setInterval(compiled.interval);
      const tokenResponse = await fetch("/api/cli/token", { cache: "no-store" });
      const tokenPayload = await tokenResponse.json() as { token?: string };
      if (!tokenPayload.token) throw new Error("无法取得行情访问令牌");
      const response = await fetch("/api/cli", {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-NEMT-CLI-Token": tokenPayload.token },
        body: JSON.stringify({ cmd: "klines", symbol, interval: compiled.interval, limit: String(RANGE_BARS[range]?.[compiled.interval] ?? 500) }),
      });
      const payload = await response.json() as KlinePayload;
      if (!payload.ok || !payload.candles?.length) throw new Error(payload.error ?? "没有取得回测行情");
      const next = runClientBacktest(payload.candles, compiled.engine, capital, compiled.interval, compiled.parameters);
      setCandles(payload.candles);
      setResult(next);
      setSelectedTrade(0);
      notify("success", `回测完成 · ${payload.candles.length} 根 K 线 · ${next.tradeCount} 笔交易`);
    } catch (cause) {
      notify("error", cause instanceof Error ? cause.message : "回测失败");
    } finally { setBusy(false); }
  }

  const metrics = result ? [
    { label: "总收益", value: `${result.totalReturn >= 0 ? "+" : ""}${fmt(result.totalReturn)}%`, good: result.totalReturn >= 0 },
    { label: "最大回撤", value: `${fmt(result.maxDrawdown)}%`, good: result.maxDrawdown <= 15 },
    { label: "SHARPE", value: fmt(result.sharpe), good: result.sharpe >= 1.5 },
    { label: "胜率", value: `${fmt(result.winRate)}%`, good: result.winRate >= 50 },
    { label: "盈亏比", value: result.profitFactor >= 999 ? "∞" : fmt(result.profitFactor), good: result.profitFactor >= 1.2 },
    { label: "交易次数", value: String(result.tradeCount), good: result.tradeCount >= 10 },
  ] : [];
  const playbackWindowStart = playbackRun ? Math.max(0, playbackIndex - 119) : 0;
  const playbackCandles = playbackRun ? playbackRun.candles.slice(playbackWindowStart, playbackIndex + 1) : [];
  const playbackLow = playbackCandles.length ? Math.min(...playbackCandles.map((candle) => candle.low)) : 0;
  const playbackHigh = playbackCandles.length ? Math.max(...playbackCandles.map((candle) => candle.high)) : 1;
  const playbackSpan = Math.max(1, playbackHigh - playbackLow);
  const liveMetrics = playbackRun ? playbackMetrics(playbackRun, playbackIndex) : null;

  if (newDialog) return <div className={styles.repositoryPage}>
    <section className={styles.repositoryCreator} aria-labelledby="new-strategy-title">
      <header><button type="button" onClick={() => setNewDialog(false)} aria-label="返回策略仓库" title="返回"><StudioIcon name="chevronLeft" size={19} /></button><div><span>{editingRepositoryId ? "EDIT REPOSITORY" : "NEW REPOSITORY"}</span><h1 id="new-strategy-title">{editingRepositoryId ? "编辑策略仓库" : "创建策略仓库"}</h1></div></header>
      <div className={styles.repositoryMeta}><label><span>仓库名称</span><input autoFocus value={newName} onChange={(event) => setNewName(event.target.value)} placeholder="emx-str-002" /></label><div><span>PRIVATE</span><b>PYTHON 3.11</b></div></div>
      <div className={styles.repoEditor}><nav aria-label="策略仓库文件"><div className={styles.fileTreeHead}><span>FILES · {Object.keys(newFiles).length}</span><button type="button" onClick={() => setAddingFile(true)} aria-label="新建文件" title="新建文件"><StudioIcon name="plus" size={13} /></button></div>{addingFile ? <div className={styles.newFileRow}><input autoFocus value={newFilePath} onChange={(event) => setNewFilePath(event.target.value)} onKeyDown={(event) => { if (event.key === "Enter") addRepositoryFile(); if (event.key === "Escape") setAddingFile(false); }} placeholder="configs/ethusdt_4h.yaml" /><button type="button" onClick={addRepositoryFile}><StudioIcon name="check" size={12} /></button></div> : null}{Object.keys(newFiles).sort((a, b) => a.localeCompare(b)).map((file) => <button type="button" key={file} data-active={newFile === file ? "yes" : "no"} onClick={() => setNewFile(file)}><StudioIcon name={file.endsWith(".py") ? "fileText" : file.endsWith(".yaml") ? "sliders" : "research"} size={14} /><span>{file}</span></button>)}</nav><div><div className={styles.repoPath}><span>{newName || "new-strategy"}</span><b>/</b><strong>{newFile}</strong></div><textarea aria-label={newFile} spellCheck={false} value={newFiles[newFile] ?? ""} onChange={(event) => setNewFiles((current) => ({ ...current, [newFile]: event.target.value }))} /></div></div>
      <footer><button type="button" onClick={() => setNewDialog(false)} aria-label="取消" title="取消"><StudioIcon name="close" size={17} /></button><button type="button" onClick={() => confirmCreateStrategy(false)} aria-label="创建仓库" title="创建仓库"><StudioIcon name="check" size={18} /></button><button type="button" onClick={() => confirmCreateStrategy(true)} aria-label="创建并准备回测" title="创建并准备回测"><StudioIcon name="play" size={18} /></button></footer>
    </section>
  </div>;

  if (currentRepository && playbackRun && liveMetrics) return <div className={styles.playbackPage}>
    <header className={styles.playbackHeader}><button type="button" onClick={() => { setPlaybackPlaying(false); setPlaybackRun(null); setRepositoryTab("runs"); }} aria-label="返回策略仓库" title="返回仓库"><StudioIcon name="chevronLeft" size={18} /></button><div><span>BACKTEST PLAYER</span><h1>{currentRepository.name}</h1><p>{playbackRun.strategyFile} · {playbackRun.configFile}</p></div><div className={styles.playbackClock}><i data-live={playbackPlaying ? "yes" : "no"} />{playbackPlaying ? "RUNNING" : playbackIndex >= playbackRun.candles.length - 1 ? "COMPLETED" : "PAUSED"}<strong>{new Date(playbackRun.candles[playbackIndex]?.openTime ?? playbackRun.createdAt).toLocaleString("zh-CN")}</strong></div></header>
    <section className={styles.playbackMetrics}><article><span>当前权益</span><strong>{fmt(liveMetrics.equity)} USDT</strong></article><article data-positive={liveMetrics.totalReturn >= 0 ? "yes" : "no"}><span>总收益</span><strong>{liveMetrics.totalReturn >= 0 ? "+" : ""}{fmt(liveMetrics.totalReturn)}%</strong></article><article><span>最大回撤</span><strong>{fmt(liveMetrics.maxDrawdown)}%</strong></article><article><span>胜率</span><strong>{fmt(liveMetrics.winRate)}%</strong></article><article><span>盈亏比</span><strong>{liveMetrics.profitFactor >= 999 ? "∞" : fmt(liveMetrics.profitFactor)}</strong></article><article><span>已完成交易</span><strong>{liveMetrics.completed.length}</strong></article></section>
    <div className={styles.playbackWorkspace}><main><div className={styles.playbackChartHead}><div><strong>{parseRepositoryConfig(currentRepository.files[playbackRun.configFile] ?? "").symbol ?? "BTCUSDT"}</strong><span>{parseRepositoryConfig(currentRepository.files[playbackRun.configFile] ?? "").interval ?? "1h"} · {playbackIndex + 1}/{playbackRun.candles.length} K</span></div><div><span>{new Date(playbackRun.candles[0]?.openTime ?? playbackRun.createdAt).toLocaleDateString("zh-CN")}</span><b>→</b><span>{new Date(playbackRun.candles[playbackIndex]?.openTime ?? playbackRun.createdAt).toLocaleDateString("zh-CN")}</span></div></div>
      <svg className={styles.playbackChart} viewBox="0 0 1200 460" role="img" aria-label="逐根播放的回测 K 线与买卖点">
        <defs><pattern id="backtest-grid" width="100" height="76" patternUnits="userSpaceOnUse"><path d="M100 0H0V76" fill="none" stroke="#dce2e6" strokeWidth="1" /></pattern></defs><rect width="1200" height="460" fill="url(#backtest-grid)" />
        {playbackCandles.map((candle, index) => { const xStep = 1160 / Math.max(1, playbackCandles.length); const x = 20 + index * xStep + xStep / 2; const y = (price: number) => 25 + (playbackHigh - price) / playbackSpan * 385; const up = candle.close >= candle.open; return <g key={`${candle.openTime}-${index}`} data-up={up ? "yes" : "no"}><line className={styles.candleWick} x1={x} y1={y(candle.high)} x2={x} y2={y(candle.low)} /><rect className={styles.candleBody} x={x - Math.max(1.5, xStep * .28)} y={Math.min(y(candle.open), y(candle.close))} width={Math.max(3, xStep * .56)} height={Math.max(2, Math.abs(y(candle.open) - y(candle.close)))} /></g>; })}
        {playbackRun.result.trades.filter((trade) => trade.entryIndex >= playbackWindowStart && trade.entryIndex <= playbackIndex).map((trade, index) => { const localIndex = trade.entryIndex - playbackWindowStart; const candle = playbackRun.candles[trade.entryIndex]; const xStep = 1160 / Math.max(1, playbackCandles.length); const x = 20 + localIndex * xStep + xStep / 2; const y = 25 + (playbackHigh - candle.low) / playbackSpan * 385 + 14; return <g key={`entry-${trade.entryAt}-${index}`} className={styles.playbackMarker}><path d={`M${x} ${y} l-6 9 h12z`} data-side={trade.side} /><text x={x + 9} y={y + 9}>IN</text></g>; })}
        {liveMetrics.completed.filter((trade) => trade.exitIndex >= playbackWindowStart).map((trade, index) => { const localIndex = trade.exitIndex - playbackWindowStart; const candle = playbackRun.candles[trade.exitIndex]; const xStep = 1160 / Math.max(1, playbackCandles.length); const x = 20 + localIndex * xStep + xStep / 2; const y = 25 + (playbackHigh - candle.high) / playbackSpan * 385 - 11; return <g key={`exit-${trade.exitAt}-${index}`} className={styles.playbackMarker}><circle cx={x} cy={y} r="5" data-profit={trade.pnl >= 0 ? "yes" : "no"} /><text x={x + 9} y={y + 4}>OUT</text></g>; })}
      </svg>
      <div className={styles.playbackTimeline}><button type="button" onClick={() => setPlaybackIndex(0)} title="回到开始" aria-label="回到开始"><StudioIcon name="refresh" size={16} /></button><button type="button" onClick={() => setPlaybackPlaying((value) => !value)} title={playbackPlaying ? "暂停" : "播放"} aria-label={playbackPlaying ? "暂停" : "播放"}>{playbackPlaying ? <StudioIcon name="pause" size={17} /> : <StudioIcon name="play" size={17} />}</button><input type="range" min="0" max={Math.max(0, playbackRun.candles.length - 1)} value={playbackIndex} onChange={(event) => { setPlaybackPlaying(false); setPlaybackIndex(Number(event.target.value)); }} aria-label="回测时间轴" /><div>{([1, 2, 4] as const).map((speed) => <button type="button" key={speed} data-active={playbackSpeed === speed ? "yes" : "no"} onClick={() => setPlaybackSpeed(speed)}>{speed}×</button>)}</div></div></main>
      <aside><header><span>EVENT STREAM</span><strong>策略事件</strong></header><div>{liveMetrics.completed.slice(-8).reverse().map((trade, index) => <article key={`${trade.exitAt}-${index}`} data-profit={trade.pnl >= 0 ? "yes" : "no"}><i>{trade.pnl >= 0 ? "+" : "−"}</i><div><strong>{trade.side} · {trade.pnl >= 0 ? "盈利" : "亏损"}</strong><time>{new Date(trade.exitAt).toLocaleString("zh-CN")}</time></div><b>{trade.pnl >= 0 ? "+" : ""}{fmt(trade.pnl)} USDT</b></article>)}{liveMetrics.completed.length === 0 ? <p>播放器正在等待第一个完整交易信号……</p> : null}</div></aside></div>
  </div>;

  if (currentRepository) return <div className={styles.repositoryBrowser}>
    <header className={styles.browserHeader}>
      <button type="button" onClick={() => setOpenRepositoryId(null)} aria-label="返回策略仓库列表" title="返回仓库列表"><StudioIcon name="chevronLeft" size={18} /></button>
      <div><span>STRATEGY REPOSITORY</span><h1>{currentRepository.name}</h1><p>{currentRepository.description}</p></div>
      <b>PRIVATE</b>
    </header>
    <nav className={styles.repositoryTabs} aria-label="仓库导航"><button type="button" data-active={repositoryTab === "code" ? "yes" : "no"} onClick={() => setRepositoryTab("code")}><StudioIcon name="fileText" size={15} />代码</button><button type="button" data-active={repositoryTab === "runs" ? "yes" : "no"} onClick={() => setRepositoryTab("runs")}><StudioIcon name="activity" size={15} />回测记录 <small>{currentRepositoryRuns.length}</small></button><button type="button" data-active={repositoryTab === "config" ? "yes" : "no"} onClick={() => setRepositoryTab("config")}><StudioIcon name="sliders" size={15} />运行配置</button></nav>
    <div className={styles.repositoryBody}>
      <main>
        <div className={styles.repositoryToolbar}><button type="button"><StudioIcon name="trade" size={14} />main<StudioIcon name="chevronDown" size={12} /></button><span>{Object.keys(currentRepository.files).length} files</span><div /><button type="button" onClick={() => { setEditingRepositoryId(currentRepository.id); setNewFiles({ ...currentRepository.files }); setNewName(currentRepository.name); setNewFile("README.md"); setNewDialog(true); }}><StudioIcon name="plus" size={14} />添加文件</button><button type="button" className={styles.runRepository} disabled={repositoryRunBusy} onClick={() => void runRepositoryBacktest(currentRepository)}>{repositoryRunBusy ? <span className={styles.busyDot} /> : <StudioIcon name="play" size={14} />}{repositoryRunBusy ? "运行中" : "运行回测"}</button></div>
        {repositoryTab === "code" ? <><section className={styles.fileTable} aria-label="仓库文件列表">
          <header><strong>{currentRepository.name}</strong><span>策略仓库初始化</span><time>{currentRepository.updatedAt}</time></header>
          {Object.keys(currentRepository.files).sort((a, b) => a.localeCompare(b)).map((file) => <button type="button" key={file} onClick={() => setRepositoryFile(file)} data-selected={repositoryFile === file ? "yes" : "no"}><span><StudioIcon name={file.endsWith(".py") ? "fileText" : file.endsWith(".yaml") ? "sliders" : "research"} size={15} />{file}</span><em>{file === "README.md" ? "Document strategy hypothesis and risk" : file.startsWith("configs/") ? "Market and timeframe configuration" : file.startsWith("tests/") ? "Validate research assumptions" : "Strategy implementation"}</em><time>{currentRepository.updatedAt}</time></button>)}
        </section>
        {repositoryFile !== "README.md" ? <section className={styles.codePreview}><header><strong>{repositoryFile}</strong><button type="button" title="编辑文件" aria-label="编辑文件" onClick={() => { setEditingRepositoryId(currentRepository.id); setNewFiles({ ...currentRepository.files }); setNewName(currentRepository.name); setNewFile(repositoryFile); setNewDialog(true); }}><StudioIcon name="pencil" size={14} /></button></header><pre>{currentRepository.files[repositoryFile]}</pre></section> : null}
        <section className={styles.readmeCard}><header><StudioIcon name="research" size={16} /><strong>README</strong><span>策略说明</span></header><article>{readmeBlocks(currentRepository.files["README.md"] ?? "# Strategy")}</article></section></> : null}
        {repositoryTab === "config" ? <section className={styles.configPanel}><header><div><span>RUN CONFIGURATION</span><h2>选择本次回测配置</h2></div><p>币种、周期、手续费和风险参数均从 YAML 读取。</p></header><div>{Object.keys(currentRepository.files).filter((file) => file.startsWith("configs/") && /\.ya?ml$/i.test(file)).map((file) => { const config = parseRepositoryConfig(currentRepository.files[file]); return <button type="button" key={file} data-selected={repositoryConfigFile === file ? "yes" : "no"} onClick={() => setRepositoryConfigFile(file)}><StudioIcon name="sliders" size={18} /><span><strong>{config.symbol || file}</strong><small>{file}</small></span><b>{config.interval || "—"}</b><em>{config.market || "market"}</em></button>; })}</div></section> : null}
        {repositoryTab === "runs" ? <section className={styles.runPanel}>{latestRepositoryRun ? <><header><div><span>BACKTEST RESULT</span><h2>{latestRepositoryRun.configFile}</h2><p>{latestRepositoryRun.strategyFile} · {new Date(latestRepositoryRun.createdAt).toLocaleString("zh-CN")}</p></div><b>{latestRepositoryRun.result.endingEquity.toFixed(2)} USDT</b></header><div className={styles.runMetrics}><article><span>总收益</span><strong>{fmt(latestRepositoryRun.result.totalReturn)}%</strong></article><article><span>最大回撤</span><strong>{fmt(latestRepositoryRun.result.maxDrawdown)}%</strong></article><article><span>Sharpe</span><strong>{fmt(latestRepositoryRun.result.sharpe)}</strong></article><article><span>胜率</span><strong>{fmt(latestRepositoryRun.result.winRate)}%</strong></article><article><span>盈亏比</span><strong>{fmt(latestRepositoryRun.result.profitFactor)}</strong></article><article><span>交易次数</span><strong>{latestRepositoryRun.result.tradeCount}</strong></article></div><div className={styles.runTrades}>{latestRepositoryRun.result.trades.slice(0, 10).map((trade, index) => <div key={`${trade.entryAt}-${index}`}><span>{String(index + 1).padStart(2, "0")} · {trade.side}</span><time>{new Date(trade.entryAt).toLocaleString("zh-CN")}</time><strong data-profit={trade.pnl >= 0 ? "yes" : "no"}>{trade.pnl >= 0 ? "+" : ""}{fmt(trade.pnl)} USDT</strong></div>)}</div></> : <div className={styles.emptyRuns}><StudioIcon name="activity" size={28} /><h2>还没有回测记录</h2><p>先在“运行配置”中选择配置，然后点击右上角运行回测。</p><button type="button" onClick={() => setRepositoryTab("config")}>选择运行配置</button></div>}</section> : null}
      </main>
      <aside><h2>About</h2><p>{currentRepository.description}</p><div><span>Python</span><span>Backtest</span><span>Research</span></div><hr /><p><StudioIcon name="clock" size={14} />更新于 {currentRepository.updatedAt}</p><p><StudioIcon name="database" size={14} />{Object.keys(currentRepository.files).length} 个文件</p></aside>
    </div>
  </div>;

  return <div className={styles.backtestPage}>
    <header className={styles.backtestHead}>
      <div><span>BACKTEST COMPUTE / CODE FIRST</span><h1>策略回测</h1><p>AI 写策略代码；引擎读取代码中的周期和规则，载入历史数据并计算结果。</p></div>
      <div className={styles.headActions}>{workbenchOpen ? <button type="button" className={styles.iconButton} onClick={returnToRepositories} title="返回策略仓库" aria-label="返回策略仓库"><StudioIcon name="chevronLeft" size={19} /></button> : <button type="button" className={styles.iconButton} onClick={createStrategy} title="新建策略" aria-label="新建策略"><StudioIcon name="plus" size={19} /></button>}<button type="button" className={styles.iconButton} onClick={() => setWorkbenchOpen(true)} title="打开策略工作台" aria-label="打开策略工作台"><StudioIcon name="fileText" size={18} /></button><button type="button" className={styles.iconButtonPrimary} onClick={() => void run()} disabled={busy} title="运行回测" aria-label="运行回测">{busy ? <span className={styles.busyDot} /> : <StudioIcon name="play" size={19} />}</button></div>
    </header>

    {!workbenchOpen ? <section className={styles.heroEmpty} aria-label="策略仓库列表"><div className={styles.repositoryList}><header><span>YOUR REPOSITORIES</span><strong>{String(repositories.length).padStart(2, "0")}</strong></header>{repositories.map((repository, index) => <button type="button" key={repository.id} onClick={() => openRepository(repository.id)}><em>{String(index + 1).padStart(2, "0")}</em><span><strong>{repository.name}</strong><small>{repository.description}</small><i>{Object.keys(repository.files).length} FILES · PYTHON</i></span><StudioIcon name="chevronRight" size={18} /></button>)}<button type="button" className={styles.createRepositoryCard} onClick={createStrategy}><StudioIcon name="plus" size={18} /><span><strong>创建策略仓库</strong><small>README · Python · Config · Tests</small></span></button></div><figure><Image src={backtestMuse} alt="回测策略视觉角色" priority /></figure></section> : <><section className={styles.strategyWorkspace}>
      <div className={styles.strategyPicker}>
        <label><span>当前策略版本</span><select value={activeProfile.id} onChange={(event) => { setActiveId(event.target.value); setResult(null); setEditing(false); }}>{profiles.map((item) => <option key={item.id} value={item.id}>{item.name} · {item.version}{item.builtIn ? " · 内置" : ""}</option>)}</select></label>
        <div><strong>{activeProfile.name}</strong><span>{activeProfile.version} · {activeProfile.engine}</span><p>{activeProfile.description}</p></div>
        <button type="button" className={styles.saveIcon} onClick={saveCodeVersion} title={activeProfile.builtIn ? "保存为新版本" : "保存代码"} aria-label={activeProfile.builtIn ? "保存为新版本" : "保存代码"}><StudioIcon name="download" size={17} /></button>
      </div>
      <div className={styles.codeDesk}>
        <div><span>STRATEGY CODE</span><strong>{activeProfile.language === "python" ? "Python 3.11" : "Pine Script® v6"}</strong><em>{activeProfile.language === "python" ? "strategy.py" : "周期写在代码的 timeframe 中"}</em></div>
        <textarea aria-label="策略代码" spellCheck={false} value={codeDraft} onChange={(event) => setCodeDraft(event.target.value)} />
        <footer><span>NEMT_ENGINE · SANDBOX</span><div><button type="button" onClick={() => void navigator.clipboard.writeText(codeDraft).then(() => notify("success", "Pine 代码已复制"))} aria-label="复制代码" title="复制代码"><StudioIcon name="copy" size={15} /></button><button type="button" onClick={openTradingView} aria-label="在 TradingView 打开" title="在 TradingView 打开"><StudioIcon name="external" size={15} /></button></div></footer>
      </div>
    </section>

    <section className={styles.controls} aria-label="回测参数">
      <label><span>交易对</span><select value={symbol} onChange={(event) => setSymbol(event.target.value)}>{SYMBOLS.map((item) => <option key={item}>{item}</option>)}</select></label>
      <label><span>历史数据范围</span><select value={range} onChange={(event) => setRange(event.target.value)}><option value="7d">近 7 天</option><option value="30d">近 30 天</option><option value="90d">近 90 天</option></select></label>
      <label><span>初始资金（USDT）</span><input type="number" min="100" step="100" value={capital} onChange={(event) => setCapital(Math.max(100, Number(event.target.value) || 100))} /></label>
    </section>

    {!result ? null : <>
      <section className={styles.metricGrid}>{metrics.map((item) => <article key={item.label} data-good={item.good ? "yes" : "no"}><span>{item.label}</span><strong>{item.value}</strong></article>)}</section>
      <section className={styles.chartCard}>
        <div className={styles.chartTitle}><div><strong>{symbol}</strong><span>{interval} · {candles.length} 根 K 线</span></div><b>期末资金 {fmt(result.endingEquity)} USDT</b></div>
        <svg className={styles.chart} viewBox="0 0 1000 280" role="img" aria-label="价格走势与回测买卖位置">
          <path className={styles.priceLine} d={path} />
          {result.trades.map((trade, index) => { const entry = chartPoint(candles, trade.entryIndex); const exit = chartPoint(candles, trade.exitIndex); return <g key={`${trade.entryAt}-${index}`} className={styles.tradePoints} onClick={() => setSelectedTrade(index)}><circle cx={entry.x} cy={entry.y} r={selectedTrade === index ? 7 : 5} data-kind="entry"><title>{`入场 ${trade.entryPrice.toFixed(2)}`}</title></circle><circle cx={exit.x} cy={exit.y} r={selectedTrade === index ? 7 : 5} data-kind="exit"><title>{`出场 ${trade.exitPrice.toFixed(2)}`}</title></circle></g>; })}
        </svg>
        <div className={styles.legend}><span><i data-kind="entry" />入场</span><span><i data-kind="exit" />出场</span><em>点击图中圆点可定位交易</em></div>
      </section>
      <section className={styles.trades}>
        <div className={styles.tradeHead}><span># / 方向</span><span>入场时间 / 价格</span><span>出场时间 / 价格</span><span>收益</span></div>
        {result.trades.length === 0 ? <p>当前参数没有产生交易。</p> : result.trades.map((trade, index) => <button type="button" key={`${trade.exitAt}-${index}`} data-selected={selectedTrade === index ? "yes" : "no"} onClick={() => setSelectedTrade(index)}><span>{String(index + 1).padStart(2, "0")} · {trade.side === "LONG" ? "做多" : "做空"}</span><span>{new Date(trade.entryAt).toLocaleString("zh-CN")}<small>{fmt(trade.entryPrice)}</small></span><span>{new Date(trade.exitAt).toLocaleString("zh-CN")}<small>{fmt(trade.exitPrice)}</small></span><strong data-profit={trade.pnl >= 0 ? "yes" : "no"}>{trade.pnl >= 0 ? "+" : ""}{fmt(trade.pnl)} USDT<small>{trade.pnlPct >= 0 ? "+" : ""}{fmt(trade.pnlPct)}%</small></strong></button>)}
      </section>
    </>}</>}
  </div>;
}
