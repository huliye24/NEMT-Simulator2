---
description: "创建完整的交易策略规范 — 策略假设、入场出场规则、NEMT 整合、风险管理"
---
name: write-strategy
prompt: |
  # /write-strategy -- 策略规范

  创建一份完整的交易策略规范文档，明确策略假设、入场出场规则、NEMT 整合方式和风险管理参数。

  ## 触发条件

  当用户提供以下类型的输入时触发：
  - 创建新的交易策略
  - 编写策略的完整规范
  - 描述策略的交易逻辑
  - 已有初步策略想法，需要完善规范

  ## 工作流

  ### Step 1: 理解策略

  接受任何形式的输入：
  - 策略名称（"Vortex Breakout"）
  - 策略描述（"基于涡旋理论的突破策略"）
  - 策略假设（"市场在临界状态会方向选择"）
  - 已有策略发现文档

  ### Step 2: 收集上下文

  询问式收集关键信息（最重要的优先）：

  #### 2.1 策略核心
  1. **策略类型**: 趋势跟踪 / 突破 / 均值回归 / 套利 / 混合
  2. **交易标的**: BTC/USDT, ETH/USDT, 全市场扫描
  3. **时间周期**: 1m / 5m / 15m / 1h / 4h / 1d
  4. **交易方向**: 只做多 / 只做空 / 多空双做

  #### 2.2 市场条件
  1. **适用市场**: 趋势市场 / 震荡市场 / 任意市场
  2. **波动率要求**: 高波动 / 中波动 / 低波动
  3. **流动性要求**: 高流动性 / 中流动性

  #### 2.3 NEMT 整合
  1. **目标相位**: stable / critical_up / critical_down / critical
  2. **ψ 阈值**: 入场所需的 ψ 值
  3. **熵 阈值**: 入场所需的熵值

  #### 2.4 风险参数
  1. **止损**: 固定止损 / 跟踪止损 [%]
  2. **止盈**: 固定止盈 / 分批止盈 [%]
  3. **仓位**: 单笔仓位 [%]
  4. **最大持仓**: 同时持仓数量

  #### 2.5 成功指标
  1. **目标胜率**: [%]
  2. **目标盈亏比**: [:1]
  3. **目标夏普**: [数值]
  4. **最大回撤容忍**: [%]

  ### Step 3: 生成策略规范

  应用规范模板，生成完整的策略文档：

  ```markdown
  # 策略规范: [策略名称]

  **版本**: 1.0.0
  **日期**: [今天]
  **状态**: 草稿
  **策略类型**: [类型]
  **交易标的**: [标的]
  **时间周期**: [周期]

  ---

  ## 1. 策略概述

  ### 1.1 策略描述
  [策略的核心思想，1-2 句话]

  ### 1.2 策略假设
  || # | 假设 | 类型 | 优先级 |
  ||---|-----|------|--------|
  || 1 | | Value/Feasibility/Risk/NEMT | P0/P1/P2 |

  ### 1.3 适用市场条件
  - **市场类型**: [趋势/震荡/任意]
  - **波动率**: [高/中/低]
  - **流动性**: [高/中/低]
  - **NEMT 相位**: [有效相位列表]

  ---

  ## 2. 入场规则

  ### 2.1 入场条件 (必须全部满足)

  #### 趋势条件
  - [条件1]
  - [条件2]

  #### 技术指标条件
  - [指标1] [比较符] [值]
  - [指标2] [比较符] [值]

  #### NEMT 条件
  - **相位**: [目标相位]
  - **ψ**: [值] 以上
  - **熵**: [值] 以上
  - **φ**: [值] 以下

  ### 2.2 入场信号

  ```python
  def should_enter(df, nemt_state):
      """
      入场条件检查
      返回: (bool, signal_type, confidence)
      """
      # 趋势条件
      trend_ok = ...

      # 技术指标条件
      indicator_ok = ...

      # NEMT 条件
      nemt_ok = (
          nemt_state.phase in TARGET_PHASES and
          nemt_state.psi > PSI_THRESHOLD and
          nemt_state.entropy > ENTROPY_THRESHOLD
      )

      if trend_ok and indicator_ok and nemt_ok:
          return (True, "BUY", confidence)

      return (False, "HOLD", 0)
  ```

  ### 2.3 入场执行

  - **信号类型**: [市价/限价/止损单]
  - **下单量**: [计算公式]
  - **滑点预留**: [%]

  ---

  ## 3. 出场规则

  ### 3.1 止损规则

  - **止损类型**: [固定/ATR/跟踪]
  - **止损位置**: [值]% / [ATR倍数]
  - **止损执行**: [市价/限价]

  ```python
  def get_stoploss(entry_price, atr=None):
      if FIXED_STOPLEOSS:
          return entry_price * (1 - STOPLOSS_PCT)
      else:
          return entry_price - atr * ATR_MULTIPLIER
  ```

  ### 3.2 止盈规则

  - **止盈类型**: [固定/分批/跟踪]
  - **止盈位置**: [值]%
  - **分批止盈**: [50% @ 2R, 50% @ 3R]

  ### 3.3 时间止损

  - **最大持仓时间**: [小时]
  - **超时处理**: [强制平仓/预警]

  ### 3.4 NEMT 出场

  - **相位反转出场**: [是/否]
  - **触发相位**: [列表]

  ### 3.5 出场执行

  - **信号类型**: [市价/限价]
  - **部分平仓**: [是/否]

  ---

  ## 4. 风险管理

  ### 4.1 仓位管理

  | 参数 | 值 | 说明 |
  |------|-----|------|
  | 单笔仓位 | [%] | 账户的 [%] |
  | 最大同时持仓 | [N] | 最多 [N] 个仓位 |
  | 最大总仓位 | [%] | 总持仓不超过 [%] |

  ### 4.2 风险控制

  | 控制 | 阈值 | 动作 |
  |------|------|------|
  | 日亏损限制 | [%] | 暂停交易 |
  | 周亏损限制 | [%] | 降低仓位 |
  | 最大回撤 | [%] | 策略归档 |

  ### 4.3 Kelly Criterion (可选)

  ```python
  def calculate_position_size(win_rate, avg_win, avg_loss):
      """
      Kelly Criterion 半仓
      """
      b = avg_win / avg_loss  # 盈亏比
      p = win_rate            # 胜率
      q = 1 - p

      kelly = (b * p - q) / b
      half_kelly = kelly * 0.5  # 半 Kelly 更保守

      return min(half_kelly, MAX_POSITION)
  ```

  ---

  ## 5. NEMT 整合

  ### 5.1 NEMT 状态机配置

  ```python
  NEMT_CONFIG = {
      "critical_entropy": 0.7,      # 临界熵阈值
      "critical_psi": 0.5,         # 临界ψ阈值
      "stable_psi": 0.3,           # 稳定ψ阈值
      "ema_alpha": 0.3,            # EMA 衰减因子
  }
  ```

  ### 5.2 NEMT 信号规则

  | 条件 | NEMT 相位 | ψ | 熵 | → 信号 |
  |------|-----------|---|-----|--------|
  | 临界上涨 | critical_up | > 0.5 | > 0.7 | BUY |
  | 稳定趋势 | stable | > 0.3 | < 0.5 | BUY (轻仓) |
  | 临界下跌 | critical_down | < -0.5 | > 0.7 | SELL |
  | 稳定下跌 | stable | < -0.3 | < 0.5 | SELL (轻仓) |
  | 方向不明 | critical | any | > 0.7 | HOLD |

  ### 5.3 NEMT 决策逻辑

  ```python
  def nemt_signal(psi, phi, entropy):
      if entropy > NEMT_CONFIG["critical_entropy"]:
          if psi > NEMT_CONFIG["critical_psi"]:
              return ("BUY", 0.9, "critical_up")
          elif psi < -NEMT_CONFIG["critical_psi"]:
              return ("SELL", 0.9, "critical_down")
          else:
              return ("HOLD", 0.0, "critical")
      elif entropy < 0.3:
          if abs(psi) > NEMT_CONFIG["stable_psi"]:
              direction = "BUY" if psi > 0 else "SELL"
              return (direction, 0.7, "stable")
      return ("HOLD", 0.0, "decay")
  ```

  ---

  ## 6. 回测配置

  ### 6.1 回测参数

  | 参数 | 值 |
  |------|-----|
  | 回测期 | [开始] ~ [结束] |
  | 初始资金 | [值] USDT |
  | 手续费率 | [值]% |
  | 滑点 | [值]% |

  ### 6.2 成功标准

  | 指标 | 目标 | 最低 | 优先级 |
  |------|------|------|--------|
  | 胜率 | >= [%] | >= [%] | P0 |
  | 夏普比率 | >= [值] | >= [值] | P0 |
  | 最大回撤 | <= [%] | <= [%] | P0 |
  | 盈亏比 | >= [:1] | >= [:1] | P1 |
  | 年化收益 | >= [%] | >= [%] | P1 |

  ### 6.3 样本外测试

  - **样本外期**: [开始] ~ [结束]
  - **样本外通过标准**: 同上

  ---

  ## 7. 策略代码

  ### 7.1 目录结构

  ```
  src/strategies/[strategy-name]/
  ├── index.ts
  ├── signals/
  │   ├── entry.ts
  │   ├── exit.ts
  │   └── nemt.ts
  ├── risk/
  │   ├── position.ts
  │   ├── stoploss.ts
  │   └── drawdown.ts
  └── tests/
      └── signals.test.ts
  ```

  ### 7.2 核心代码

  ```typescript
  // 策略核心逻辑
  export class Strategy {
      config: StrategyConfig;

      constructor(config: StrategyConfig) {
          this.config = config;
      }

      // 信号生成
      generateSignals(df: KLine[], nemtState: NEMTState): Signal[] {
          // 1. 检查 NEMT 条件
          // 2. 检查技术指标条件
          // 3. 生成信号
          return signals;
      }

      // 仓位计算
      calculatePosition(capital: number, signal: Signal): Position {
          // Kelly Criterion 或固定仓位
          return position;
      }

      // 止损计算
      calculateStoploss(entryPrice: number, atr?: number): number {
          return entryPrice * (1 - this.config.stoplossPercent / 100);
      }
  }
  ```

  ---

  ## 8. 开放问题

  || 问题 | 负责人 | 截止日期 |
  ||-----|-------|----------|
  || 1 | | |
  || 2 | | |

  ---

  ## 9. 变更历史

  || 版本 | 日期 | 变更 | 作者 |
  ||-----|-----|------|-----|
  || 1.0.0 | [今天] | 初始版本 | [用户] |
  ```

  ### Step 4: 检查点

  生成规范后，询问用户：
  - "入场条件是否需要调整？"
  - "NEMT 参数是否符合你的预期？"
  - "风险参数是否满足你的风险偏好？"

  ### Step 5: 建议下一步

  - "是否需要创建技术实施计划？使用 /plan-strategy"
  - "是否直接开始回测？使用 /backtest"
  - "是否需要调整任何参数？"

  ## 规则

  - 规范必须包含完整的入场/出场规则，可以直接用于编码
  - NEMT 整合是必填项
  - 风险管理参数必须明确
  - 成功标准必须可量化
  - 如果用户没有指定参数，使用 Constitution 中的默认值
