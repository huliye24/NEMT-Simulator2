import type { BacktestStrategy, StrategyParameters } from "./engine";

export interface CompiledStrategyScript {
  engine: BacktestStrategy;
  parameters: StrategyParameters;
  interval: string;
}

function numberInput(source: string, variable: string): number | undefined {
  const pattern = new RegExp(`(?:int|float)\\s+${variable}\\s*=\\s*input\\.(?:int|float)\\(\\s*([0-9.]+)`, "i");
  const match = source.match(pattern);
  return match ? Number(match[1]) : undefined;
}

export function compileStrategyScript(source: string): CompiledStrategyScript {
  if (!source.includes("//@version=6")) throw new Error("策略代码必须使用 //@version=6");
  if (!/\bstrategy\s*\(/.test(source)) throw new Error("缺少 strategy(...) 声明");
  const engine = source.match(/\/\/\s*NEMT_ENGINE:\s*(nemt|ma_cross|rsi_reversion|breakout)/i)?.[1] as BacktestStrategy | undefined;
  if (!engine) throw new Error("缺少受支持的 // NEMT_ENGINE: ... 声明");
  const interval = source.match(/string\s+timeframe\s*=\s*input\.timeframe\(\s*"([^"]+)"/i)?.[1] ?? "1h";
  if (!["15m", "1h", "4h", "1d"].includes(interval)) throw new Error("timeframe 当前仅支持 15m、1h、4h、1d");
  if (engine === "ma_cross") {
    const fast = numberInput(source, "fastLength") ?? 9;
    const slow = numberInput(source, "slowLength") ?? 21;
    if (fast >= slow) throw new Error("fastLength 必须小于 slowLength");
    return { engine, parameters: { fast, slow }, interval };
  }
  if (engine === "rsi_reversion") {
    const period = numberInput(source, "rsiLength") ?? 14;
    const low = numberInput(source, "oversold") ?? 30;
    const high = numberInput(source, "overbought") ?? 70;
    if (low >= high) throw new Error("oversold 必须小于 overbought");
    return { engine, parameters: { period, low, high }, interval };
  }
  if (engine === "breakout") return { engine, parameters: { period: numberInput(source, "bbLength") ?? 20, multiplier: numberInput(source, "bbMultiplier") ?? 2 }, interval };
  const recentWindow = numberInput(source, "recentWindow") ?? 20;
  const baselineWindow = numberInput(source, "baselineWindow") ?? 30;
  if (recentWindow >= baselineWindow) throw new Error("recentWindow 必须小于 baselineWindow");
  return { engine, parameters: { recentWindow, baselineWindow, threshold: numberInput(source, "threshold") ?? .72, volatilityRatio: numberInput(source, "volatilityRatio") ?? .92 }, interval };
}

export const STRATEGY_SCRIPTS: Record<BacktestStrategy, string> = {
  ma_cross: `//@version=6
// NEMT_ENGINE: ma_cross
strategy("MA Cross", overlay=true, initial_capital=1000)
string timeframe = input.timeframe("1h", "Strategy timeframe")
int fastLength = input.int(9, "Fast length", minval=2)
int slowLength = input.int(21, "Slow length", minval=3)
float fastMA = ta.sma(close, fastLength)
float slowMA = ta.sma(close, slowLength)
if ta.crossover(fastMA, slowMA)
    strategy.entry("Long", strategy.long)
if ta.crossunder(fastMA, slowMA)
    strategy.entry("Short", strategy.short)
plot(fastMA, "Fast MA", color.aqua)
plot(slowMA, "Slow MA", color.orange)`,
  rsi_reversion: `//@version=6
// NEMT_ENGINE: rsi_reversion
strategy("RSI Reversion", overlay=true, initial_capital=1000)
string timeframe = input.timeframe("1h", "Strategy timeframe")
int rsiLength = input.int(14, "RSI length", minval=2)
float oversold = input.float(30, "Oversold")
float overbought = input.float(70, "Overbought")
float value = ta.rsi(close, rsiLength)
if ta.crossover(value, oversold)
    strategy.entry("Long", strategy.long)
if ta.crossunder(value, overbought)
    strategy.entry("Short", strategy.short)
if ta.cross(value, 50)
    strategy.close_all()
plot(value, "RSI", color.aqua)`,
  breakout: `//@version=6
// NEMT_ENGINE: breakout
strategy("Bollinger Breakout", overlay=true, initial_capital=1000)
string timeframe = input.timeframe("4h", "Strategy timeframe")
int bbLength = input.int(20, "Length", minval=5)
float bbMultiplier = input.float(2.0, "Multiplier", minval=0.5)
float basis = ta.sma(close, bbLength)
float deviation = ta.stdev(close, bbLength) * bbMultiplier
if ta.crossover(close, basis + deviation)
    strategy.entry("Long", strategy.long)
if ta.crossunder(close, basis - deviation)
    strategy.entry("Short", strategy.short)
if ta.cross(close, basis)
    strategy.close_all()
plot(basis, "Basis", color.orange)`,
  nemt: `//@version=6
// NEMT_ENGINE: nemt
strategy("NEMT Critical Momentum", overlay=true, initial_capital=1000)
string timeframe = input.timeframe("1h", "Strategy timeframe")
int recentWindow = input.int(20, "Recent window", minval=5)
int baselineWindow = input.int(30, "Baseline window", minval=10)
float threshold = input.float(0.72, "Critical threshold", minval=0.1)
float volatilityRatio = input.float(0.92, "Volatility ratio", minval=0.1)
float displacement = (close - ta.sma(close, baselineWindow)) / ta.stdev(close, baselineWindow)
float expansion = ta.stdev(close, recentWindow) / ta.stdev(close, baselineWindow)
if displacement > threshold and expansion > volatilityRatio
    strategy.entry("Long", strategy.long)
if displacement < -threshold and expansion > volatilityRatio
    strategy.entry("Short", strategy.short)
if math.abs(displacement) < threshold * 0.35
    strategy.close_all()
plot(displacement, "NEMT displacement", color.aqua)`,
};
