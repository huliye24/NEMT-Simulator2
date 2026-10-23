# NEMT 模拟盘（纸上交易 / Forward Test）

更新：2026-10-21 · 代码：`backend/trade_app/paper.py` · API 前缀 `/api/v1/paper`

> 这是**用真实行情、花虚拟钱**的前向测试环境，用于验证策略和纪律，不是回测，
> 也不是实盘。它**不持有任何 API 密钥，不可能发出真实订单**。

---

## 1. 它是什么（不是回测）

| 方式 | 数据 | 钱 | 验证什么 |
|---|---|---|---|
| 回测 Backtest | 历史 K 线 | 虚拟 | 策略逻辑是否成立（易过拟合） |
| **模拟盘 Paper** | **实时行情** | **虚拟** | **执行纪律、仓位、盈亏手感、心理** |
| 测试网 Testnet | 实时行情 | 假钱 | 接口、签名、延迟、异常 |
| 实盘 Live | 实时行情 | 真钱 | 滑点、情绪、真实亏损 |

英文叫 **paper trading**，强调"跑实时行情向前推进"时叫 **forward test**（前向测试）。
freqtrade 里对应 `dry-run`。

---

## 2. 账户与规则

| 项目 | 默认值 | 环境变量 |
|---|---|---|
| 初始虚拟权益 | **20 USDT** | `NEMT_PAPER_INITIAL_EQUITY` |
| 支持币种 | **BTCUSDT / ETHUSDT / SOLUSDT** | `NEMT_PAPER_SYMBOLS` |
| 最小单笔名义价值 | 5 USDT（与币安 `minNotional` 一致） | `NEMT_PAPER_MIN_NOTIONAL` |
| 现货手续费 | 0.10%（taker） | `NEMT_PAPER_TAKER_FEE_SPOT` |
| 合约手续费 | 0.05%（taker） | `NEMT_PAPER_TAKER_FEE_PERP` |
| 滑点 | 5 bps（买入成交在标记价之上、卖出在之下） | `NEMT_PAPER_SLIPPAGE_BPS` |
| 维持保证金率 | 0.4% | `NEMT_PAPER_MAINTENANCE_MARGIN_RATE` |
| 资金费率结算 | 每 8 小时（UTC 00/08/16） | `NEMT_PAPER_FUNDING_INTERVAL_HOURS` |
| 最大杠杆 | 10x（**逐仓**） | `NEMT_PAPER_MAX_LEVERAGE` |

---

## 3. 记账恒等式（出问题先查这个）

```
equity = cash + Σ(现货 qty × mark) + Σ(合约 margin + 合约浮动盈亏)
```

- 开合约：`cash -= margin + fee`，钱从现金挪进保证金，**权益只减少手续费**。
- 平合约：`cash += 释放保证金 + 毛利 - fee`。
- 现货买入：`cash -= 名义额 + fee`，资产以 `qty × mark` 计入权益。
- `realized_pnl` 是**毛利**，`fees` / `funding` 单独记录（和交易所账单一致）；
  `equity` 已经扣掉全部费用，所以**只信 equity**。

金额全程 `Decimal` + TEXT 存储。**SQL 里绝不做金额加减**——SQLite 会把 TEXT
转成 REAL，浮点误差会污染账本。所有更新都是「读出 TEXT → Decimal 计算 → 写回」。

---

## 4. 合约模型（逐仓）

| 项目 | 公式 |
|---|---|
| 保证金 | `名义价值 / 杠杆` |
| 强平价（多） | `entry × (1 − 1/leverage + mmr)` |
| 强平价（空） | `entry × (1 + 1/leverage − mmr)` |
| 爆仓处理 | 以强平价强制平仓，**该仓位保证金全部损失** |
| 资金费 | 每次结算 `qty × mark × fundingRate`；多头付正费率 |

> 强平价在开仓时就固定（逐仓特性），不会随权益变化漂移。

---

## 5. API

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/v1/paper/account` | 权益、现金、浮动/已实现盈亏、手续费、资金费、收益率 |
| GET | `/api/v1/paper/positions` | 持仓 + 账户快照（含标记价、强平价、保证金率） |
| POST | `/api/v1/paper/positions` | 开仓：`symbol / market(SPOT\|PERP) / side / notional / leverage` |
| POST | `/api/v1/paper/positions/{id}/close` | 平仓：`fraction`（0–1，支持部分减仓） |
| GET | `/api/v1/paper/fills` | 逐笔成交（开/减/平/强平） |
| GET | `/api/v1/paper/equity` | 权益曲线快照点 |
| POST | `/api/v1/paper/reset` | 重置回 20 USDT（练习用） |

写操作需要 `trader` 角色 + CSRF 头，读取需要 `viewer` 角色，与实盘接口同一套鉴权。

---

## 6. 已验证（2026-10-21，真实行情）

```
权益重置 20.00 USDT
PERP LONG  BTCUSDT  8U  5x  qty=0.00009571 @ 83587.78  强平 67204.58
SPOT LONG  ETHUSDT  6U  1x  qty=0.00242963 @ 2469.51
PERP SHORT SOLUSDT  5U  3x  qty=0.04673052 @ 107.00    强平 142.23

t+0s   权益 19.9780  现金 10.7208  浮动 -0.0095  手续费 0.0125
t+12s  权益 19.9777  现金 10.7208  浮动 -0.0098
```

权益下降 0.022 = 开仓手续费 0.0125 + 滑点成本，符合预期。
单元测试 35 个全绿（`backend/tests/test_paper.py` 12 个）。

---

## 7. 完成状态

已上线（本地已验证）：
- 引擎：`backend/trade_app/paper.py`，35 个后端测试里 12 个专测模拟盘
- API：`/api/v1/paper/*` 七个端点
- **UI：`/trade?section=execution` 已接真实数据**，5 秒轮询刷新浮动盈亏，
  显示账户摘要 / 模拟开仓条 / 持仓表（含强平价）/ 成交记录，支持部分减仓与重置

尚未完成：
- **NEMT 信号引擎**：策略页 6 套策略仍是展示文案，没有真信号。
- **分析笔记**：你写的分析还没有入口。
- **未部署**：代码在本地，服务器跑的还是旧版本。

---

## 8. 20 USDT 的现实约束（别自欺）

| 项目 | 20U 意味着 |
|---|---|
| 现货 | BTC ≈ 83.5k 时只能买 0.00024 BTC |
| 最小单 | 5 USDT → 最多拆 4 笔 |
| 合约 10x | 名义 200U，反向 1% = 亏 2U = 权益 −10% |
| 手续费 | 合约来回 0.1% ≈ 0.02U；做 50 次 = −5% |
| 单笔风险 | 建议 1–2U（权益 5–10%），止损 1–2% |

**结论：20U 用来练流程和纪律，练不出收益。** 它的价值是暴露"会不会乱开单""止损守不守"，
不是证明策略能赚钱。
