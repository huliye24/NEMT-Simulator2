---
description: "运行历史回测 — 在双缓冲系统中验证策略有效性，生成绩效报告"
---
name: backtest
prompt: |
  # /backtest -- 历史回测

  在 NEMT 双缓冲系统中运行策略的历史回测，验证策略在历史数据上的有效性，生成详细的绩效报告。

  ## 触发条件

  当用户提供以下类型的输入时触发：
  - 运行策略回测
  - 验证策略历史表现
  - 优化策略参数
  - 对比策略表现

  ## 前提条件

  回测需要以下输入：
  1. **策略规范** (from /write-strategy) — 包含入场/出场规则
  2. **策略配置** — 包含 NEMT 参数和风控参数
  3. **回测区间** — 开始日期和结束日期
  4. **交易对** — 如 BTC/USDT
  5. **K线周期** — 如 1h, 4h, 1d

  如果缺少任何条件，要求用户提供。

  ## 工作流

  ### Step 1: 收集回测配置

  #### 1.1 必填参数

  | 参数 | 示例 | 说明 |
  |------|------|------|
  | strategy_id | strategy_1 | 策略 ID |
  | strategy_name | Vortex Breakout | 策略名称 |
  | symbol | BTCUSDT | 交易对 |
  | interval | 1h | K线周期 |
  | start_date | 2025-01-01 | 回测开始 |
  | end_date | 2025-12-31 | 回测结束 |

  #### 1.2 可选参数

  | 参数 | 默认值 | 说明 |
  |------|--------|------|
  | initial_capital | 10000 | 初始资金 |
  | commission_rate | 0.001 | 手续费率 |
  | slippage | 0.0005 | 滑点 |

  #### 1.3 策略参数

  从策略规范或用户提供提取：
  - NEMT 参数 (critical_entropy, critical_psi, etc.)
  - 风控参数 (stoploss, takeprofit, position_size)
  - 技术指标参数 (RSI, MACD, etc.)

  ### Step 2: 数据准备

  #### 2.1 获取市场数据

  使用 Binance API 获取 K线数据：

  ```python
  # 获取历史 K线数据
  klines = binance.get_klines(
      symbol="BTCUSDT",
      interval="1h",
      limit=1000,
      start_time=start_ts,
      end_time=end_ts
  )

  # 数据结构
  # {
  #     "openTime": 1704067200000,
  #     "open": "37500.00",
  #     "high": "38000.00",
  #     "low": "37000.00",
  #     "close": "37800.00",
  #     "volume": "1200.00",
  #     "closeTime": 1704070800000
  # }
  ```

  #### 2.2 计算 NEMT 状态

  对每个 K 线计算 NEMT 状态：

  ```typescript
  function calculateNEMTState(klines: KLine[]): NEMTState {
      // 1. 计算收益率
      const returns = calculateReturns(klines);

      // 2. 计算 ψ (增长率)
      const psi = calculatePsi(returns);

      // 3. 计算 φ (衰减率)
      const phi = calculatePhi(returns);

      // 4. 计算熵
      const entropy = calculateEntropy(klines);

      // 5. 确定相位
      const phase = determinePhase(psi, phi, entropy);

      return { psi, phi, entropy, phase };
  }
  ```

  #### 2.3 计算技术指标

  ```typescript
  function calculateIndicators(df: DataFrame): Indicators {
      return {
          rsi: calculateRSI(df.close, 14),
          macd: calculateMACD(df.close),
          atr: calculateATR(df, 14),
          bb: calculateBollingerBands(df.close),
          adx: calculateADX(df),
      };
  }
  ```

  ### Step 3: 回测执行

  #### 3.1 回测循环

  ```typescript
  async function runBacktest(config: BacktestConfig): Promise<BacktestResult> {
      const { klines, strategy, nemtParams, riskParams } = config;

      // 初始化
      let capital = config.initialCapital;
      let peakCapital = capital;
      let maxDrawdown = 0;
      let maxDrawdownDuration = 0;
      const trades: Trade[] = [];
      const equityCurve: EquityPoint[] = [];

      // 遍历 K线 (从索引 20 开始，确保有足够数据计算指标)
      for (let i = 20; i < klines.length; i++) {
          const currentKline = klines[i];
          const historyKlines = klines.slice(0, i + 1);

          // 1. 计算当前 NEMT 状态 (使用历史数据，不包含当前)
          const nemtState = calculateNEMTState(historyKlines.slice(0, -1));

          // 2. 计算技术指标
          const indicators = calculateIndicators(historyKlines);

          // 3. 检查是否持仓
          if (!currentPosition) {
              // 生成入场信号
              const signal = strategy.checkEntry(nemtState, indicators);
              if (signal.type === 'BUY' || signal.type === 'SELL') {
                  // 计算仓位
                  const positionSize = calculatePositionSize(
                      capital,
                      signal,
                      riskParams
                  );

                  // 开仓
                  currentPosition = {
                      type: signal.type,
                      entryPrice: currentKline.close,
                      entryTime: currentKline.openTime,
                      size: positionSize,
                      stoploss: calculateStoploss(currentKline.close, riskParams),
                      takeprofit: calculateTakeprofit(currentKline.close, riskParams),
                  };
              }
          } else {
              // 检查出场条件
              const exitSignal = strategy.checkExit(currentPosition, currentKline, nemtState);

              if (exitSignal.shouldExit) {
                  // 平仓
                  const pnl = calculatePnL(currentPosition, currentKline, exitSignal.reason);
                  trades.push({
                      ...currentPosition,
                      exitPrice: currentKline.close,
                      exitTime: currentKline.openTime,
                      pnl,
                      reason: exitSignal.reason,
                  });

                  capital += pnl;
                  currentPosition = null;
              }
          }

          // 更新权益曲线
          equityCurve.push({
              time: currentKline.openTime,
              value: capital,
          });

          // 更新最大回撤
          if (capital > peakCapital) {
              peakCapital = capital;
          }
          const drawdown = (peakCapital - capital) / peakCapital;
          if (drawdown > maxDrawdown) {
              maxDrawdown = drawdown;
          }
      }

      // 平仓未结束持仓
      if (currentPosition) {
          // ...
      }

      return {
          trades,
          equityCurve,
          metrics: calculateMetrics(trades, equityCurve, maxDrawdown),
      };
  }
  ```

  #### 3.2 NEMT 信号整合

  ```typescript
  function checkEntry(nemtState: NEMTState, indicators: Indicators): Signal | null {
      const { phase, psi, entropy } = nemtState;

      // NEMT 条件
      const nemtOk = (
          phase === 'critical_up' ||
          (phase === 'stable' && psi > 0.3)
      );

      if (!nemtOk) return null;

      // 技术指标条件
      const rsiOk = indicators.rsi < 70 && indicators.rsi > 30;
      const trendOk = indicators.macd.histogram > 0;

      if (nemtOk && rsiOk && trendOk) {
          return { type: 'BUY', confidence: 0.8 };
      }

      return null;
  }
  ```

  ### Step 4: 绩效计算

  #### 4.1 核心指标

  ```typescript
  function calculateMetrics(
      trades: Trade[],
      equityCurve: EquityPoint[],
      maxDrawdown: number
  ): BacktestMetrics {

      const totalReturn = (finalCapital - initialCapital) / initialCapital;
      const years = tradingDays / 252;
      const annualizedReturn = Math.pow(finalCapital / initialCapital, 1 / years) - 1;

      // 夏普比率
      const dailyReturns = calculateDailyReturns(equityCurve);
      const avgReturn = dailyReturns.reduce((a, b) => a + b) / dailyReturns.length;
      const stdReturn = Math.sqrt(
          dailyReturns.reduce((sum, r) => sum + (r - avgReturn) ** 2, 0) / dailyReturns.length
      );
      const sharpeRatio = (avgReturn / stdReturn) * Math.sqrt(252);

      // 索提诺比率
      const negativeReturns = dailyReturns.filter(r => r < 0);
      const stdDownside = Math.sqrt(
          negativeReturns.reduce((sum, r) => sum + r ** 2, 0) / negativeReturns.length
      );
      const sortinoRatio = (avgReturn / stdDownside) * Math.sqrt(252);

      // 交易统计
      const winningTrades = trades.filter(t => t.pnl > 0);
      const losingTrades = trades.filter(t => t.pnl <= 0);
      const winRate = winningTrades.length / trades.length;

      return {
          totalReturn: totalReturn * 100,
          annualizedReturn: annualizedReturn * 100,
          sharpeRatio,
          sortinoRatio,
          maxDrawdown: maxDrawdown * 100,
          totalTrades: trades.length,
          winningTrades: winningTrades.length,
          losingTrades: losingTrades.length,
          winRate: winRate * 100,
          avgWin: avg(winningTrades.map(t => t.pnl)),
          avgLoss: avg(losingTrades.map(t => t.pnl)),
          profitFactor: totalWin / Math.abs(totalLoss),
      };
  }
  ```

  #### 4.2 NEMT 特有指标

  ```typescript
  function calculateNEMTMetrics(trades: Trade[], klines: KLine[]): NEMTMetrics {
      // ψ 准确率
      const psiCorrect = trades.filter(t => {
          const phase = getPhaseAtTime(t.entryTime);
          return (
              (phase === 'critical_up' && t.pnl > 0) ||
              (phase === 'critical_down' && t.pnl < 0)
          );
      });

      // 各相位胜率
      const phaseStats = {};
      for (const phase of ['stable', 'critical_up', 'critical_down', 'critical']) {
          const phaseTrades = trades.filter(t => getPhaseAtTime(t.entryTime) === phase);
          const wins = phaseTrades.filter(t => t.pnl > 0).length;
          phaseStats[phase] = {
              count: phaseTrades.length,
              wins,
              winRate: phaseTrades.length > 0 ? wins / phaseTrades.length : 0,
          };
      }

      return {
          psiAccuracy: psiCorrect.length / trades.length,
          phaseStats,
      };
  }
  ```

  ### Step 5: 生成报告

  #### 5.1 回测摘要

  ```markdown
  ## 回测报告: [策略名称]

  **回测时间**: [执行时间]
  **回测区间**: [开始] ~ [结束]
  **交易对**: [交易对]
  **周期**: [周期]

  ---

  ### 核心指标

  | 指标 | 值 | 评级 |
  |------|-----|------|
  | 总收益率 | [+/-]XX.XX% | 🟢/🟡/🔴 |
  | 年化收益率 | XX.XX% | 🟢/🟡/🔴 |
  | 夏普比率 | X.XX | 🟢/🟡/🔴 |
  | 索提诺比率 | X.XX | 🟢/🟡/🔴 |
  | 最大回撤 | -XX.XX% | 🟢/🟡/🔴 |
  | 胜率 | XX.X% | 🟢/🟡/🔴 |
  | 盈亏比 | X.XX | 🟢/🟡/🔴 |
  | 盈利因子 | X.XX | 🟢/🟡/🔴 |
  | 交易次数 | XXX | |

  评级标准:
  - 🟢 优秀: 超过目标
  - 🟡 合格: 达到最低要求
  - 🔴 不合格: 未达到最低要求

  ---

  ### NEMT 指标

  | 指标 | 值 |
  |------|-----|
  | ψ 准确率 | XX.X% |
  | 临界上涨胜率 | XX.X% |
  | 临界下跌胜率 | XX.X% |
  | 稳定相位胜率 | XX.X% |

  ---

  ### 交易明细

  [交易表格]

  ---

  ### 权益曲线

  [图表]

  ---

  ### 结论

  **通过/不通过**: 🟢/🔴

  [详细分析]
  ```

  #### 5.2 可视化

  生成以下图表：
  1. **权益曲线** — 资金变化
  2. **回撤曲线** — 回撤深度
  3. **交易标记图** — K线 + 交易点
  4. **月度收益** — 每月收益柱状图
  5. **相位分布** — 各相位交易占比

  ### Step 6: 审核决策

  根据 Constitution 中的标准判断：

  | 指标 | 最低要求 | 目标 | 当前 |
  |------|----------|------|------|
  | 胜率 | >= 50% | >= 55% | XX% |
  | 夏普比率 | >= 1.5 | >= 2.0 | X.XX |
  | 最大回撤 | <= 20% | <= 15% | XX% |
  | 盈亏比 | >= 1.2 | >= 1.5 | X.XX |

  - **全部通过** → 建议进入实战
  - **部分通过** → 建议优化或调整
  - **未通过** → 建议重新设计策略

  ### Step 7: 建议下一步

  - "是否通过审核？"
  - "是否需要调整参数？"
  - "是否进入实战？使用 /live-trade"
  - "是否保存回测结果？"

## freqtrade 整合

本模块借鉴 freqtrade 的回测引擎设计：

- **BacktestEngine**: `web/src/strategy/backtest/backtestEngine.ts`
- **策略接口**: `web/src/strategy/interfaces/IStrategy.ts`
- **技术指标**: `web/src/strategy/indicators/technicalIndicators.ts`
- **Binance 适配器**: `web/src/strategy/exchange/binanceAdapter.ts`

### 使用示例

```typescript
import {
  BacktestEngine,
  runBacktest,
  printBacktestResult,
  createNEMTStrategy,
  BinanceDataProvider,
  calculateAllIndicators,
  createDataFrame,
} from 'web/src/strategy';

// 1. 创建策略
const strategy = createNEMTStrategy('My Strategy', {
  nemtConfig: {
    nemtCriticalPsi: 0.5,
    nemtCriticalEntropy: 0.7,
  },
});

// 2. 获取数据
const provider = new BinanceDataProvider();
const klines = await provider.getHistoricalKlines(
  'BTCUSDT', '1h', startTime, endTime
);
const df = createDataFrame(klines);

// 3. 计算指标
df.indicators = calculateAllIndicators(df.high, df.low, df.close, df.volume);

// 4. 运行回测
const config = {
  initialCapital: 10000,
  commissionRate: 0.001,
  slippage: 0.0005,
  startDate,
  endDate,
  pair: 'BTCUSDT',
  timeframe: '1h',
};

const result = await runBacktest(config, strategy, df, provider);
printBacktestResult(result);
```

## 核心概念

### IStrategy 接口

借鉴 freqtrade IStrategy，定义了策略的标准接口：

| 方法 | 说明 |
|------|------|
| `populateIndicators()` | 计算技术指标 |
| `populateEntryTrend()` | 定义入场信号 |
| `populateExitTrend()` | 定义出场信号 |
| `customStoploss()` | 自定义止损 |
| `confirmTradeEntry()` | 入场确认 |
| `confirmTradeExit()` | 出场确认 |

### 信号格式

```typescript
// 入场信号
dataframe.enterLong = 1  // 做多
dataframe.enterShort = 1  // 做空

// 出场信号
dataframe.exitLong = 1   // 平多
dataframe.exitShort = 1  // 平空
```

## QuantConnect Lean 整合

本模块借鉴 Lean 的事件驱动架构和参数优化：

### AlgorithmManager

借鉴 Lean 的 QCAlgorithm：

```typescript
import { QCAlgorithm, AlgorithmManager, MomentumAlgorithm } from 'web/src/strategy';

class MyAlgorithm extends QCAlgorithm {
  name = 'MyAlgorithm';

  Initialize(): void {
    this.SetStartDate(2025, 1, 1);
    this.SetCash(10000);
    this.AddCrypto('BTCUSDT', '1h');
  }

  OnData(slice: Slice): void {
    const price = this.CurrentPrice('BTCUSDT');
    const history = this.History('BTCUSDT', 20);
    // 策略逻辑
  }

  OnEndOfDay(symbol?: string): void {
    console.log(`End of day: ${this.account.portfolioValue}`);
  }
}

// 运行算法
const algo = new MyAlgorithm();
const manager = new AlgorithmManager(algo);
manager.Initialize();
manager.Start();
```

### Optimizer

借鉴 Lean Optimizer：

```typescript
import { optimizeStrategy, GridSearchOptimizer } from 'web/src/strategy';

const result = await optimizeStrategy(strategy, [
  { name: 'rsi_period', min: 10, max: 30, step: 2 },
  { name: 'rsi_oversold', min: 20, max: 40, step: 5 },
], {
  objective: 'sharpe_ratio',
  constraint: { objective: 'max_drawdown', operator: '<=', value: 20 },
}, runBacktest);

printOptimizationReport(result);
```

### 参考资料

- Lean 文档: https://www.quantconnect.com/docs/
- Lean GitHub: https://github.com/QuantConnect/Lean
