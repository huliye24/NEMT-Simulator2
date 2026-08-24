---
description: "启动实时交易 — 在双缓冲系统中执行策略，实时监控信号和持仓"
---
name: live-trade
prompt: |
  # /live-trade -- 实时交易

  在 NEMT 双缓冲系统中启动策略的实时交易执行，实时监控信号、持仓和风险管理。

  ## 触发条件

  当用户提供以下类型的输入时触发：
  - 启动策略的实时交易
  - 从回测切换到实战
  - 执行策略信号
  - 管理实时持仓

  ## 前提条件

  实时交易需要：
  1. **策略通过回测审核** — 胜率 >= 50%, 夏普 >= 1.5, 最大回撤 <= 20%
  2. **策略规范** — 入场/出场规则
  3. **风险管理配置** — 仓位、止损、止盈
  4. **实盘账户** — 模拟或实盘资金

  如果回测未通过，要求用户确认是否继续（风险自负）。

  ## 工作流

  ### Step 1: 交易前准备

  #### 1.1 确认策略状态

  ```typescript
  interface PreTradeCheck {
      strategy: {
          id: string;
          name: string;
          backtestPassed: boolean;
          backtestResult: BacktestMetrics;
      };
      account: {
          balance: number;
          availableMargin: number;
          riskLevel: 'low' | 'medium' | 'high';
      };
      market: {
          symbol: string;
          lastPrice: number;
          volatility24h: number;
          nemtPhase: NEMTPhase;
      };
  }
  ```

  #### 1.2 风险预检

  - [ ] 账户余额充足
  - [ ] 市场无异常波动
  - [ ] NEMT 相位适合开仓
  - [ ] 今日未达亏损上限
  - [ ] 未超过最大持仓数量

  #### 1.3 连接市场数据

  ```typescript
  // 连接 Binance WebSocket
  await binance.connect(['BTCUSDT'], '1h');

  // 订阅 K线流
  binance.subscribeKlines('BTCUSDT', (kline) => {
      // 处理新 K线
      processNewKline(kline);
  });

  // 订阅实时价格
  binance.subscribeTicker('BTCUSDT', (ticker) => {
      // 更新当前价格
      currentPrice = parseFloat(ticker.lastPrice);
  });
  ```

  ### Step 2: 实时信号监控

  #### 2.1 信号生成循环

  ```typescript
  async function startSignalMonitor(strategy: Strategy, config: MonitorConfig) {
      const nemtState = { psi: 0, phi: 0, entropy: 0, phase: 'stable' };
      let currentKlines: KLine[] = [];

      // WebSocket K线回调
      function onNewKline(kline: KLine) {
          // 添加到历史
          currentKlines.push(kline);
          if (currentKlines.length > MAX_KLINES) {
              currentKlines.shift();
          }

          // 重新计算 NEMT 状态
          nemtState = calculateNEMTState(currentKlines);

          // 检查入场信号
          checkEntrySignals(strategy, nemtState, currentKlines);

          // 检查出场信号
          checkExitSignals(strategy, nemtState);
      }
  }
  ```

  #### 2.2 NEMT 信号检查

  ```typescript
  function checkEntrySignals(
      strategy: Strategy,
      nemtState: NEMTState,
      klines: KLine[]
  ) {
      const { phase, psi, entropy } = nemtState;

      // 检查是否已有持仓
      if (hasOpenPosition(strategy.id)) {
          return;
      }

      // 检查风控限制
      if (!passesRiskChecks()) {
          log('Risk check failed, skipping entry');
          return;
      }

      // 生成信号
      const signal = strategy.checkEntry(nemtState, indicators);

      if (signal) {
          // 计算信心度
          const confidence = calculateConfidence(nemtState, signal);

          // 信心度超过阈值才执行
          if (confidence >= strategy.minConfidence) {
              executeEntry(strategy, signal, nemtState);
          }
      }
  }

  function calculateConfidence(nemtState: NEMTState, signal: Signal): number {
      let confidence = 0.5; // 基础信心度

      // 相位权重
      if (signal.type === 'BUY' && nemtState.phase === 'critical_up') {
          confidence += 0.3;
      } else if (signal.type === 'SELL' && nemtState.phase === 'critical_down') {
          confidence += 0.3;
      }

      // ψ 值权重
      confidence += Math.min(Math.abs(nemtState.psi) / 10, 0.2);

      return Math.min(confidence, 1.0);
  }
  ```

  ### Step 3: 订单执行

  #### 3.1 入场执行

  ```typescript
  async function executeEntry(
      strategy: Strategy,
      signal: Signal,
      nemtState: NEMTState
  ): Promise<Trade> {

      // 计算仓位
      const positionSize = calculatePositionSize(
          account.balance,
          strategy,
          signal
      );

      // 计算下单价格
      const orderPrice = currentPrice;

      // 计算止损止盈
      const stoploss = calculateStoploss(orderPrice, strategy);
      const takeprofit = calculateTakeprofit(orderPrice, strategy);

      // 创建订单
      const order = await binance.placeOrder({
          symbol: 'BTCUSDT',
          side: signal.type === 'BUY' ? 'BUY' : 'SELL',
          type: 'MARKET',
          quantity: positionSize,
      });

      // 记录持仓
      const position: Position = {
          id: generatePositionId(),
          strategyId: strategy.id,
          type: signal.type,
          entryPrice: order.fillPrice,
          size: positionSize,
          stoploss,
          takeprofit,
          entryTime: Date.now(),
          nemtPhase: nemtState.phase,
          nemtPsi: nemtState.psi,
      };

      // 保存持仓
      savePosition(position);

      log(`[${strategy.name}] ${signal.type} @ ${order.fillPrice}, size: ${positionSize}`);

      return position;
  }
  ```

  #### 3.2 出场执行

  ```typescript
  async function checkExitSignals(strategy: Strategy, nemtState: NEMTState) {
      const position = getOpenPosition(strategy.id);
      if (!position) return;

      const { type, entryPrice, stoploss, takeprofit } = position;

      // 1. 止损检查
      if (currentPrice <= stoploss) {
          await executeExit(position, 'STOPLOSS');
          return;
      }

      // 2. 止盈检查
      if (currentPrice >= takeprofit) {
          await executeExit(position, 'TAKEPROFIT');
          return;
      }

      // 3. NEMT 出场 (相位反转)
      if (shouldExitOnPhaseChange(position, nemtState)) {
          await executeExit(position, 'NEMT_PHASE_CHANGE');
          return;
      }

      // 4. 时间止损
      if (Date.now() - position.entryTime > MAX_HOLDING_TIME) {
          await executeExit(position, 'TIME_STOP');
          return;
      }
  }

  function shouldExitOnPhaseChange(position: Position, nemtState: NEMTState): boolean {
      // 只在有盈利时根据 NEMT 出场
      const unrealizedPnL = calculateUnrealizedPnL(position);

      if (unrealizedPnL <= 0) return false;

      // 相位从临界变为稳定或衰减
      const phases = ['critical_up', 'critical_down', 'critical'];
      const newPhases = ['stable', 'decay'];

      if (phases.includes(position.nemtPhase) && newPhases.includes(nemtState.phase)) {
          return true;
      }

      return false;
  }

  async function executeExit(position: Position, reason: ExitReason): Promise<void> {
      const order = await binance.placeOrder({
          symbol: 'BTCUSDT',
          side: position.type === 'LONG' ? 'SELL' : 'BUY',
          type: 'MARKET',
          quantity: position.size,
      });

      const realizedPnL = calculateRealizedPnL(position, order.fillPrice);

      // 记录交易
      const trade: Trade = {
          ...position,
          exitPrice: order.fillPrice,
          exitTime: Date.now(),
          realizedPnL,
          exitReason: reason,
      };

      saveTrade(trade);
      removePosition(position.id);

      log(`[EXIT] ${position.type} @ ${order.fillPrice}, PnL: ${realizedPnL}, reason: ${reason}`);
  }
  ```

  ### Step 4: 实时监控面板

  #### 4.1 监控数据

  ```typescript
  interface LiveMonitorData {
      // 账户
      balance: number;
      availableMargin: number;
      unrealizedPnL: number;

      // 市场
      currentPrice: number;
      priceChange24h: number;
      volatility24h: number;

      // NEMT
      nemtPhase: NEMTPhase;
      psi: number;
      phi: number;
      entropy: number;

      // 持仓
      positions: Position[];
      openCount: number;

      // 今日统计
      todayTrades: number;
      todayPnL: number;
      todayWinRate: number;

      // 风控状态
      dailyLossUsed: number;
      weeklyLossUsed: number;
      riskLevel: 'normal' | 'warning' | 'danger';
  }
  ```

  #### 4.2 实时更新

  ```typescript
  function updateMonitorPanel(data: LiveMonitorData) {
      // 更新 DOM 或 React 状态
      dualBufferStore.updateLiveState({
          positions: data.positions,
          currentPrice: data.currentPrice,
          nemtState: {
              phase: data.nemtPhase,
              psi: data.psi,
              phi: data.phi,
              entropy: data.entropy,
          },
          todayPnL: data.todayPnL,
          riskLevel: data.riskLevel,
      });
  }
  ```

  ### Step 5: 风险管理

  #### 5.1 实时风控规则

  ```typescript
  function passesRiskChecks(): boolean {
      const { balance, openPositions, todayPnL, dailyLossLimit } = getAccountState();

      // 1. 日亏损检查
      if (todayPnL <= -dailyLossLimit * balance) {
          log('Daily loss limit reached');
          pauseAllTrades();
          return false;
      }

      // 2. 最大持仓检查
      if (openPositions.length >= MAX_POSITIONS) {
          log('Max positions reached');
          return false;
      }

      // 3. 单笔仓位检查
      const positionValue = balance * MAX_POSITION_PER_TRADE;
      if (positionValue > MAX_POSITION_VALUE) {
          log('Max position value exceeded');
          return false;
      }

      return true;
  }
  ```

  #### 5.2 应急机制

  ```typescript
  // 市场异常检测
  function detectMarketAnomaly(): boolean {
      const volatilityChange = (currentVolatility - historicalVolatility) / historicalVolatility;

      // 波动率突变超过 300%
      if (volatilityChange > 3) {
          log('Market anomaly: extreme volatility');
          return true;
      }

      // 价格闪崩/闪崩 (1分钟内波动超过 10%)
      if (priceChange1min > 0.1 || priceChange1min < -0.1) {
          log('Market anomaly: flash crash/spike');
          return true;
      }

      return false;
  }

  // 应急处理
  async function handleEmergency(reason: string) {
      log(`EMERGENCY: ${reason}`);

      // 1. 暂停开新仓
      pauseNewEntries();

      // 2. 关闭所有持仓
      await closeAllPositions('EMERGENCY');

      // 3. 通知
      await notifyUser(`应急处理: ${reason}`);

      // 4. 保存状态
      saveEmergencyState(reason);
  }
  ```

  ### Step 6: 交易记录

  #### 6.1 交易日志格式

  ```typescript
  interface TradeLog {
      id: string;
      strategyId: string;
      strategyName: string;
      type: 'BUY' | 'SELL';
      entryTime: number;
      exitTime: number;
      entryPrice: number;
      exitPrice: number;
      size: number;
      realizedPnL: number;
      realizedPnLPercent: number;
      exitReason: ExitReason;
      nemtPhase: NEMTPhase;
      nemtPsi: number;
      commission: number;
      slippage: number;
  }
  ```

  #### 6.2 统计分析

  ```typescript
  interface LiveStats {
      totalTrades: number;
      winningTrades: number;
      losingTrades: number;
      winRate: number;
      totalPnL: number;
      totalPnLPercent: number;
      avgWin: number;
      avgLoss: number;
      profitFactor: number;
      currentStreak: number;
      maxStreak: number;
      sharpeRatio: number;
      maxDrawdown: number;
  }
  ```

  ### Step 7: 停止交易

  ```typescript
  async function stopLiveTrade(strategyId?: string) {
      if (strategyId) {
          // 停止指定策略
          await closePositionByStrategy(strategyId);
          removeMonitor(strategyId);
      } else {
          // 停止所有策略
          await closeAllPositions('MANUAL_STOP');
          removeAllMonitors();
      }

      // 断开 WebSocket
      binance.disconnect();

      // 保存交易记录
      saveTradeHistory();

      log('Live trade stopped');
  }
  ```

    ## freqtrade 整合

  实时交易模块借鉴 freqtrade 的交易执行设计：

  ### BinanceAdapter

  ```typescript
  import { BinanceAdapter } from 'web/src/strategy';

  // 创建适配器
  const exchange = new BinanceAdapter({
    testnet: true,  // 测试网
    apiKey: 'your_api_key',
    secretKey: 'your_secret_key',
  });

  // 下单
  const order = await exchange.placeOrder({
    symbol: 'BTCUSDT',
    side: 'buy',
    type: 'market',
    amount: 0.01,
  });

  // WebSocket 订阅
  exchange.connectWebSocket((data) => {
    console.log(data);
  });

  exchange.subscribeKlines('BTCUSDT', '1h', (kline) => {
    console.log('New K-line:', kline);
  });
  ```

  ### Dry Run 模式

  freqtrade 支持 Dry Run (模拟交易)，NEMT 也支持：

  ```typescript
  // 模拟交易，不使用真实资金
  const config = {
    bot: { mode: 'dry_run' },
    exchange: { testnet: true },
  };
  ```

  ## 参考资料

  - freqtrade 文档: https://www.freqtrade.io
  - Binance API: https://developers.binance.com
