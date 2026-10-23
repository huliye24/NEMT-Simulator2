export interface BacktestCandle {
  openTime: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export type BacktestStrategy = "nemt" | "ma_cross" | "rsi_reversion" | "breakout";

export interface StrategyParameters {
  fast?: number;
  slow?: number;
  period?: number;
  low?: number;
  high?: number;
  multiplier?: number;
  recentWindow?: number;
  baselineWindow?: number;
  threshold?: number;
  volatilityRatio?: number;
}

export interface BacktestTrade {
  side: "LONG" | "SHORT";
  entryIndex: number;
  exitIndex: number;
  entryAt: string;
  exitAt: string;
  entryPrice: number;
  exitPrice: number;
  pnl: number;
  pnlPct: number;
}

export interface BacktestResult {
  totalReturn: number;
  maxDrawdown: number;
  sharpe: number;
  winRate: number;
  profitFactor: number;
  tradeCount: number;
  endingEquity: number;
  trades: BacktestTrade[];
  equity: number[];
}

const PERIODS_PER_YEAR: Record<string, number> = {
  "5m": 105_120,
  "15m": 35_040,
  "1h": 8_760,
  "4h": 2_190,
  "1d": 365,
};

function sma(values: number[], period: number): Array<number | null> {
  const output: Array<number | null> = Array(values.length).fill(null);
  let sum = 0;
  values.forEach((value, index) => {
    sum += value;
    if (index >= period) sum -= values[index - period];
    if (index >= period - 1) output[index] = sum / period;
  });
  return output;
}

function standardDeviation(values: number[]): number {
  if (values.length === 0) return 0;
  const mean = values.reduce((sum, value) => sum + value, 0) / values.length;
  return Math.sqrt(values.reduce((sum, value) => sum + (value - mean) ** 2, 0) / values.length);
}

function rsi(values: number[], period = 14): Array<number | null> {
  const output: Array<number | null> = Array(values.length).fill(null);
  if (values.length <= period) return output;
  let gains = 0;
  let losses = 0;
  for (let index = 1; index <= period; index += 1) {
    const change = values[index] - values[index - 1];
    gains += Math.max(change, 0);
    losses += Math.max(-change, 0);
  }
  let averageGain = gains / period;
  let averageLoss = losses / period;
  output[period] = averageLoss === 0 ? 100 : 100 - 100 / (1 + averageGain / averageLoss);
  for (let index = period + 1; index < values.length; index += 1) {
    const change = values[index] - values[index - 1];
    averageGain = (averageGain * (period - 1) + Math.max(change, 0)) / period;
    averageLoss = (averageLoss * (period - 1) + Math.max(-change, 0)) / period;
    output[index] = averageLoss === 0 ? 100 : 100 - 100 / (1 + averageGain / averageLoss);
  }
  return output;
}

function targets(strategy: BacktestStrategy, closes: number[], parameters: StrategyParameters): number[] {
  if (strategy === "ma_cross") {
    const fast = sma(closes, parameters.fast ?? 9);
    const slow = sma(closes, parameters.slow ?? 21);
    return closes.map((_, index) => fast[index] === null || slow[index] === null ? 0 : (fast[index] as number) > (slow[index] as number) ? 1 : -1);
  }
  if (strategy === "rsi_reversion") {
    const values = rsi(closes, parameters.period ?? 14);
    let state = 0;
    return values.map((value) => {
      if (value === null) return 0;
      if (state === 0 && value < (parameters.low ?? 30)) state = 1;
      else if (state === 0 && value > (parameters.high ?? 70)) state = -1;
      else if (state === 1 && value >= 50) state = 0;
      else if (state === -1 && value <= 50) state = 0;
      return state;
    });
  }
  if (strategy === "breakout") {
    let state = 0;
    return closes.map((close, index) => {
      const period = parameters.period ?? 20;
      if (index < period) return 0;
      const window = closes.slice(index - period, index);
      const mean = window.reduce((sum, value) => sum + value, 0) / window.length;
      const deviation = standardDeviation(window);
      if (close > mean + deviation * (parameters.multiplier ?? 2)) state = 1;
      else if (close < mean - deviation * (parameters.multiplier ?? 2)) state = -1;
      else if ((state === 1 && close < mean) || (state === -1 && close > mean)) state = 0;
      return state;
    });
  }

  // NEMT lightweight phase proxy: direction requires both displacement and
  // expanding local volatility, keeping noise inside the stable state.
  const recentWindow = parameters.recentWindow ?? 20;
  const baselineWindow = parameters.baselineWindow ?? 30;
  return closes.map((close, index) => {
    if (index < baselineWindow) return 0;
    const recent = closes.slice(index - recentWindow, index);
    const baseline = closes.slice(index - baselineWindow, index);
    const mean = recent.reduce((sum, value) => sum + value, 0) / recent.length;
    const recentVolatility = standardDeviation(recent);
    const baselineVolatility = standardDeviation(baseline);
    const displacement = baselineVolatility === 0 ? 0 : (close - mean) / baselineVolatility;
    const critical = recentVolatility > baselineVolatility * (parameters.volatilityRatio ?? 0.92);
    if (critical && displacement > (parameters.threshold ?? 0.72)) return 1;
    if (critical && displacement < -(parameters.threshold ?? 0.72)) return -1;
    return Math.abs(displacement) < 0.2 ? 0 : 0;
  });
}

export function runClientBacktest(
  candles: BacktestCandle[],
  strategy: BacktestStrategy,
  startingEquity: number,
  interval: string,
  parameters: StrategyParameters = {}
): BacktestResult {
  const feeRate = 0.0005;
  const slippage = 0.0005;
  const signals = targets(strategy, candles.map((item) => item.close), parameters);
  const trades: BacktestTrade[] = [];
  const equity: number[] = [];
  let cash = startingEquity;
  let position = 0;
  let quantity = 0;
  let entryPrice = 0;
  let entryIndex = 0;

  function close(index: number, rawPrice: number): void {
    if (position === 0) return;
    const exitPrice = rawPrice * (position > 0 ? 1 - slippage : 1 + slippage);
    const gross = quantity * (exitPrice - entryPrice) * position;
    const fees = Math.abs(quantity) * (entryPrice + exitPrice) * feeRate;
    const pnl = gross - fees;
    cash += pnl;
    trades.push({
      side: position > 0 ? "LONG" : "SHORT",
      entryIndex,
      exitIndex: index,
      entryAt: candles[entryIndex].openTime,
      exitAt: candles[index].openTime,
      entryPrice,
      exitPrice,
      pnl,
      pnlPct: (pnl / Math.max(1, cash - pnl)) * 100,
    });
    position = 0;
    quantity = 0;
  }

  for (let index = 1; index < candles.length; index += 1) {
    const desired = signals[index - 1];
    const price = candles[index].open;
    if (desired !== position) {
      close(index, price);
      if (desired !== 0) {
        position = desired;
        entryIndex = index;
        entryPrice = price * (desired > 0 ? 1 + slippage : 1 - slippage);
        quantity = cash / entryPrice;
      }
    }
    const unrealized = position === 0 ? 0 : quantity * (candles[index].close - entryPrice) * position;
    equity.push(cash + unrealized);
  }
  if (position !== 0) close(candles.length - 1, candles.at(-1)?.close ?? entryPrice);
  if (equity.length) equity[equity.length - 1] = cash;

  let peak = startingEquity;
  let maxDrawdown = 0;
  equity.forEach((value) => {
    peak = Math.max(peak, value);
    maxDrawdown = Math.max(maxDrawdown, peak > 0 ? ((peak - value) / peak) * 100 : 0);
  });
  const returns = equity.slice(1).map((value, index) => equity[index] > 0 ? value / equity[index] - 1 : 0);
  const averageReturn = returns.length ? returns.reduce((sum, value) => sum + value, 0) / returns.length : 0;
  const returnDeviation = standardDeviation(returns);
  const sharpe = returnDeviation > 0 ? (averageReturn / returnDeviation) * Math.sqrt(PERIODS_PER_YEAR[interval] ?? 35_040) : 0;
  const wins = trades.filter((trade) => trade.pnl > 0);
  const grossWin = wins.reduce((sum, trade) => sum + trade.pnl, 0);
  const grossLoss = Math.abs(trades.filter((trade) => trade.pnl <= 0).reduce((sum, trade) => sum + trade.pnl, 0));

  return {
    totalReturn: ((cash / startingEquity) - 1) * 100,
    maxDrawdown,
    sharpe,
    winRate: trades.length ? (wins.length / trades.length) * 100 : 0,
    profitFactor: grossLoss > 0 ? grossWin / grossLoss : grossWin > 0 ? 999 : 0,
    tradeCount: trades.length,
    endingEquity: cash,
    trades,
    equity,
  };
}
