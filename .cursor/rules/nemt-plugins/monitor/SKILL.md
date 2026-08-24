---
description: "监控策略表现 — 对比回测与实战，分析偏差，持续优化"
---
name: monitor
prompt: |
  # /monitor -- 策略监控

  持续监控策略表现，对比回测与实战数据，分析偏差，识别问题，提供优化建议。

  ## 触发条件

  当用户提供以下类型的输入时触发：
  - 查看策略表现
  - 对比回测与实战
  - 分析策略偏差
  - 优化策略参数
  - 生成监控报告

  ## 监控维度

  ### 1. 绩效监控

  #### 1.1 核心指标

  | 指标 | 回测值 | 实战值 | 偏差 | 状态 |
  |------|--------|--------|------|------|
  | 胜率 | XX% | XX% | ±X% | 🟢/🟡/🔴 |
  | 夏普比率 | X.XX | X.XX | ±X% | 🟢/🟡/🔴 |
  | 最大回撤 | -XX% | -XX% | ±X% | 🟢/🟡/🔴 |
  | 盈亏比 | X.XX | X.XX | ±X% | 🟢/🟡/🔴 |
  | 年化收益 | XX% | XX% | ±X% | 🟢/🟡/🔴 |

  #### 1.2 偏差分析

  ```typescript
  interface PerformanceDeviation {
      metric: string;
      backtestValue: number;
      liveValue: number;
      deviation: number;       // 偏差百分比
      deviationThreshold: number; // 阈值
      status: 'good' | 'warning' | 'critical';
      cause: string;
      recommendation: string;
  }

  function analyzeDeviation(
      backtest: BacktestMetrics,
      live: LiveMetrics
  ): PerformanceDeviation[] {
      const deviations: PerformanceDeviation[] = [];

      // 胜率偏差
      const winRateDev = (live.winRate - backtest.winRate) / backtest.winRate;
      deviations.push({
          metric: 'winRate',
          backtestValue: backtest.winRate,
          liveValue: live.winRate,
          deviation: winRateDev,
          deviationThreshold: 0.1, // 10%
          status: Math.abs(winRateDev) <= 0.1 ? 'good' : winRateDev < -0.2 ? 'critical' : 'warning',
          cause: winRateDev < 0 ? '可能市场条件变化或执行力下降' : '表现超出预期',
          recommendation: winRateDev < 0 ? '检查入场信号是否被正确执行' : '考虑适当加仓',
      });

      // 最大回撤偏差
      const drawdownDev = (live.maxDrawdown - backtest.maxDrawdown) / backtest.maxDrawdown;
      deviations.push({
          metric: 'maxDrawdown',
          backtestValue: backtest.maxDrawdown,
          liveValue: live.maxDrawdown,
          deviation: drawdownDev,
          deviationThreshold: 0.5, // 50%
          status: drawdownDev <= 0.5 ? 'good' : drawdownDev > 1 ? 'critical' : 'warning',
          cause: '可能是滑点、执行延迟或市场流动性问题',
          recommendation: drawdownDev > 0.5 ? '降低仓位或收紧止损' : '风险可控',
      });

      // ... 其他指标类似

      return deviations;
  }
  ```

  ### 2. NEMT 监控

  #### 2.1 相位分布

  ```typescript
  interface PhaseDistribution {
      phase: NEMTPhase;
      backtestPercent: number;
      livePercent: number;
      deviation: number;
      avgWinRate: number;
      signal: 'increase' | 'decrease' | 'maintain';
  }

  function analyzePhaseDistribution(
      backtestTrades: Trade[],
      liveTrades: Trade[]
  ): PhaseDistribution[] {
      const phases: NEMTPhase[] = ['stable', 'critical_up', 'critical_down', 'critical', 'decay'];
      const distributions: PhaseDistribution[] = [];

      for (const phase of phases) {
          const btTrades = backtestTrades.filter(t => t.nemtPhase === phase);
          const ltTrades = liveTrades.filter(t => t.nemtPhase === phase);

          const btPercent = btTrades.length / backtestTrades.length;
          const ltPercent = ltTrades.length / liveTrades.length;

          const btWinRate = btTrades.filter(t => t.pnl > 0).length / btTrades.length;
          const ltWinRate = ltTrades.filter(t => t.pnl > 0).length / ltTrades.length;

          distributions.push({
              phase,
              backtestPercent: btPercent,
              livePercent: ltPercent,
              deviation: Math.abs(ltPercent - btPercent),
              avgWinRate: ltWinRate,
              signal: ltWinRate > btWinRate ? 'increase' : ltWinRate < btWinRate * 0.8 ? 'decrease' : 'maintain',
          });
      }

      return distributions;
  }
  ```

  #### 2.2 ψ 值分析

  ```typescript
  interface PsiAnalysis {
      avgPsi: number;
      psiAccuracy: number;
      psiDirectionBias: number; // 正 = 多头倾向
      signal: string;
  }

  function analyzePsi(backtestTrades: Trade[], liveTrades: Trade[]): PsiAnalysis {
      const backtestAvgPsi = avg(backtestTrades.map(t => t.nemtPsi));
      const liveAvgPsi = avg(liveTrades.map(t => t.nemtPsi));

      const backtestPsiCorrect = backtestTrades.filter(t =>
          (t.nemtPhase === 'critical_up' && t.pnl > 0) ||
          (t.nemtPhase === 'critical_down' && t.pnl < 0)
      ).length / backtestTrades.length;

      const livePsiCorrect = liveTrades.filter(t =>
          (t.nemtPhase === 'critical_up' && t.pnl > 0) ||
          (t.nemtPhase === 'critical_down' && t.pnl < 0)
      ).length / liveTrades.length;

      return {
          avgPsi: liveAvgPsi,
          psiAccuracy: livePsiCorrect,
          psiDirectionBias: liveAvgPsi > 0 ? 1 : liveAvgPsi < 0 ? -1 : 0,
          signal: livePsiCorrect > backtestPsiCorrect
              ? 'ψ 信号质量提升'
              : livePsiCorrect < backtestPsiCorrect * 0.8
              ? 'ψ 信号质量下降，建议调整阈值'
              : 'ψ 信号质量稳定',
      };
  }
  ```

  ### 3. 交易执行监控

  #### 3.1 执行质量

  ```typescript
  interface ExecutionQuality {
      avgSlippage: number;        // 平均滑点
      maxSlippage: number;         // 最大滑点
      slippagePercentile95: number; // 95 分位滑点
      executionLatency: number;    // 执行延迟 (ms)
      missedSignals: number;        // 错过的信号数
      rejectedOrders: number;       // 被拒绝的订单数
      status: 'excellent' | 'good' | 'warning' | 'poor';
  }

  function analyzeExecutionQuality(trades: Trade[]): ExecutionQuality {
      const slippages = trades.map(t =>
          Math.abs(t.executionPrice - t.expectedPrice) / t.expectedPrice
      );

      return {
          avgSlippage: avg(slippages),
          maxSlippage: max(slippages),
          slippagePercentile95: percentile(slippages, 0.95),
          executionLatency: avg(trades.map(t => t.executionTime - t.signalTime)),
          missedSignals: calculateMissedSignals(),
          rejectedOrders: calculateRejectedOrders(),
          status: avg(slippages) < 0.001 ? 'excellent'
              : avg(slippages) < 0.005 ? 'good'
              : avg(slippages) < 0.01 ? 'warning'
              : 'poor',
      };
  }
  ```

  ### 4. 风险监控

  #### 4.1 风险指标

  ```typescript
  interface RiskMetrics {
      currentDrawdown: number;    // 当前回撤
      maxDrawdown: number;         // 历史最大回撤
      exposure: number;             // 当前敞口
      leverage: number;             // 杠杆率
      varDaily: number;            // 日 VaR
      varWeekly: number;           // 周 VaR
      sharpeRatio: number;         // 夏普比率
      sortinoRatio: number;        // 索提诺比率
      calmarRatio: number;         // 卡玛比率
      riskLevel: 'low' | 'medium' | 'high' | 'critical';
  }

  function calculateRiskMetrics(account: Account, trades: Trade[]): RiskMetrics {
      const returns = calculateDailyReturns(trades);
      const currentDrawdown = calculateCurrentDrawdown(account, trades);
      const maxDrawdown = calculateMaxDrawdown(trades);

      const varDaily = percentile(returns, 0.05) * account.balance;
      const varWeekly = percentile(returns, 0.05) * Math.sqrt(7) * account.balance;

      const sharpe = calculateSharpeRatio(returns);
      const sortino = calculateSortinoRatio(returns);
      const calmar = (account.annualizedReturn / maxDrawdown) || 0;

      return {
          currentDrawdown,
          maxDrawdown,
          exposure: calculateExposure(account),
          leverage: calculateLeverage(account),
          varDaily,
          varWeekly,
          sharpeRatio: sharpe,
          sortinoRatio: sortino,
          calmarRatio: calmar,
          riskLevel: currentDrawdown > 0.2 ? 'critical'
              : currentDrawdown > 0.1 ? 'high'
              : currentDrawdown > 0.05 ? 'medium'
              : 'low',
      };
  }
  ```

  #### 4.2 风险预警

  ```typescript
  interface RiskAlert {
      level: 'info' | 'warning' | 'danger';
      metric: string;
      value: number;
      threshold: number;
      message: string;
      action: string;
  }

  function checkRiskAlerts(metrics: RiskMetrics): RiskAlert[] {
      const alerts: RiskAlert[] = [];

      if (metrics.currentDrawdown > 0.15) {
          alerts.push({
              level: 'danger',
              metric: 'currentDrawdown',
              value: metrics.currentDrawdown,
              threshold: 0.15,
              message: '当前回撤超过 15%',
              action: '立即降低仓位，暂停新开仓',
          });
      } else if (metrics.currentDrawdown > 0.1) {
          alerts.push({
              level: 'warning',
              metric: 'currentDrawdown',
              value: metrics.currentDrawdown,
              threshold: 0.1,
              message: '当前回撤超过 10%',
              action: '密切关注，考虑减仓',
          });
      }

      if (metrics.exposure > 0.8) {
          alerts.push({
              level: 'warning',
              metric: 'exposure',
              value: metrics.exposure,
              threshold: 0.8,
              message: '风险敞口超过 80%',
              action: '避免加仓，考虑部分平仓',
          });
      }

      return alerts;
  }
  ```

  ### 5. North Star 指标

  #### 5.1 策略健康度

  ```typescript
  interface StrategyHealthScore {
      overall: number;         // 0-100
      performance: number;      // 0-100
      risk: number;            // 0-100
      execution: number;        // 0-100
      nemt: number;            // 0-100
      status: 'healthy' | 'caution' | 'unhealthy';
  }

  function calculateHealthScore(
      performance: PerformanceMetrics,
      risk: RiskMetrics,
      execution: ExecutionQuality,
      nemt: NEMTMetrics
  ): StrategyHealthScore {
      // 绩效得分 (权重 40%)
      const performanceScore = (
          (performance.winRate >= 50 ? 100 : performance.winRate * 2) * 0.2 +
          (performance.sharpeRatio >= 1.5 ? 100 : performance.sharpeRatio / 1.5 * 100) * 0.2
      );

      // 风险得分 (权重 30%)
      const riskScore = (
          (risk.maxDrawdown <= 0.2 ? 100 : (1 - risk.maxDrawdown) * 125) * 0.3
      );

      // 执行得分 (权重 15%)
      const executionScore = (
          (execution.avgSlippage <= 0.001 ? 100 : (0.01 - execution.avgSlippage) / 0.009 * 100) * 0.15
      );

      // NEMT 得分 (权重 15%)
      const nemtScore = (
          nemt.psiAccuracy >= 0.6 ? 100 : nemt.psiAccuracy / 0.6 * 100
      ) * 0.15;

      const overall = performanceScore + riskScore + executionScore + nemtScore;

      return {
          overall,
          performance: performanceScore,
          risk: riskScore,
          execution: executionScore,
          nemt: nemtScore,
          status: overall >= 80 ? 'healthy'
              : overall >= 60 ? 'caution'
              : 'unhealthy',
      };
  }
  ```

  ### 6. 生成监控报告

  #### 6.1 报告格式

  ```markdown
  # 策略监控报告: [策略名称]

  **报告时间**: [时间]
  **监控周期**: [开始] ~ [结束]
  **策略状态**: 🟢 正常 / 🟡 注意 / 🔴 异常

  ---

  ## 1. 健康度评分

  || 维度 | 得分 | 状态 |
  ||------|------|------|
  || 整体 | XX/100 | 🟢/🟡/🔴 |
  || 绩效 | XX/100 | 🟢/🟡/🔴 |
  || 风险 | XX/100 | 🟢/🟡/🔴 |
  || 执行 | XX/100 | 🟢/🟡/🔴 |
  || NEMT | XX/100 | 🟢/🟡/🔴 |

  ---

  ## 2. 回测 vs 实战对比

  | 指标 | 回测 | 实战 | 偏差 | 状态 |
  |------|------|------|------|------|
  | 胜率 | XX% | XX% | ±X% | 🟢/🟡/🔴 |
  | 夏普 | X.XX | X.XX | ±X% | 🟢/🟡/🔴 |
  | 最大回撤 | -XX% | -XX% | ±X% | 🟢/🟡/🔴 |

  ---

  ## 3. NEMT 分析

  ### 3.1 相位分布
  | 相位 | 回测占比 | 实战占比 | 实战胜率 | 信号 |
  |------|----------|----------|----------|------|
  | stable | XX% | XX% | XX% | ↑/↓/→ |
  | critical_up | XX% | XX% | XX% | ↑/↓/→ |
  | critical_down | XX% | XX% | XX% | ↑/↓/→ |

  ### 3.2 ψ 分析
  - 平均 ψ: XX
  - ψ 准确率: XX%
  - 建议: [优化建议]

  ---

  ## 4. 风险状态

  | 指标 | 值 | 阈值 | 状态 |
  |------|-----|------|------|
  | 当前回撤 | -XX% | -15% | 🟢/🟡/🔴 |
  | 风险敞口 | XX% | 80% | 🟢/🟡/🔴 |
  | 日 VaR | $XXX | $XXX | 🟢/🟡/🔴 |

  ### 风险预警
  - 🟡 [警告内容]
  - 🔴 [危险内容]

  ---

  ## 5. 执行质量

  | 指标 | 值 | 评级 |
  |------|-----|------|
  | 平均滑点 | X.XX bp | 🟢/🟡/🔴 |
  | 执行延迟 | XXX ms | 🟢/🟡/🔴 |
  | 信号命中率 | XX% | 🟢/🟡/🔴 |

  ---

  ## 6. 优化建议

  ### 优先级 P0
  1. [紧急优化项]
  2. [紧急优化项]

  ### 优先级 P1
  1. [重要优化项]
  2. [重要优化项]

  ### 优先级 P2
  1. [可选优化项]
  2. [可选优化项]

  ---

  ## 7. 下一步行动

  - [ ] [行动项1]
  - [ ] [行动项2]
  - [ ] [行动项3]
  ```

  ## 规则

  - 监控报告必须每日生成
  - 偏差超过阈值必须触发预警
  - 风险等级变化必须通知用户
  - 优化建议必须可执行
  - 所有数据必须保存到监控 Store
