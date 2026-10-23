# NEMT 信号引擎（相位 / 动量）

更新：2026-10-21 · 代码：`backend/trade_app/signals.py` · API：`/api/v1/signals/nemt`
参考实现：`src/web/strategy/nemt/nemtCalculator.ts`（服务端与其保持同一套公式）

> 只读信号。它**不下单**；页面上「按信号开仓」是人点出来的，而且开的是**模拟仓**。

---

## 1. 三个指标

| 指标 | 公式 | 单位 |
|---|---|---|
| **ψ psi** 动量 | `EMA(returns, α=0.3) × 100` | 每根 K 线的百分比 |
| **φ phi** 波动 | `stdev(returns) × √(24×365) × 100` | 年化 % |
| **S entropy** 熵 | `H(价格直方图) / log2(分箱数)`，分箱 `min(10, n/5)` | 0–1 |

其中 `returns_i = (close_i − close_{i−1}) / close_{i−1}`。

## 2. 相位判定（与参考实现一致）

```
S > 0.7  且 ψ >  0.5  → critical_up    → 做多
S > 0.7  且 ψ < −0.5  → critical_down  → 做空
S > 0.7  其余          → critical       → 等待（方向不明）
S < 0.15 且 |ψ| > 0.3 → stable         → 不开新仓
S < 0.15 其余          → decay          → 离场
其余                   → stable         → 不开新仓
```

阈值可用环境变量改：`NEMT_NEMT_CRITICAL_ENTROPY`（0.7）、`NEMT_NEMT_CRITICAL_PSI`（0.5）、
`NEMT_NEMT_STABLE_PSI`（0.3）、`NEMT_NEMT_EMA_ALPHA`（0.3）、`NEMT_NEMT_LOW_ENTROPY`（0.15）。

> **信号天然稀少**。要求「熵高 + 动量强」同时成立，本质是**只做临界突破**，
> 横盘时它会一直说"等待"。这不是 bug，是纪律。想更频繁就把 `CRITICAL_PSI` 调低，
> 但会显著增加假信号。

## 3. 交易建议怎么算

方向确定后：

| 项目 | 算法 |
|---|---|
| 止损 | `1.5 × ATR(14)`，夹在 1%–5% 之间 |
| 止盈 | 止损距离 × 2（盈亏比 1:2） |
| 单笔风险 | 权益 × `NEMT_NEMT_RISK_PER_TRADE_PCT`（默认 1%）= 20U 账户的 **0.2U** |
| 名义仓位 | `风险 ÷ 止损%`，例如 0.2U ÷ 1% = 20U |
| 杠杆 | `ceil(名义 ÷ (权益×95%))`，上限 10x；这样保证金 + 手续费一定放得下 |
| 强度 | `0.6 × min(|ψ|/0.5, 1) + 0.4 × min(S/0.7, 1)`，0–100 |

## 4. API

```http
GET /api/v1/signals/nemt?interval=15m&symbols=BTCUSDT,ETHUSDT,SOLUSDT
```

返回（`cards[]` 每张一个币种）：

```json
{
  "interval": "15m",
  "equity": "20.00000000",
  "risk_per_trade_pct": "1",
  "thresholds": {"critical_entropy": "0.7", "critical_psi": "0.5", "stable_psi": "0.3", "low_entropy": "0.15"},
  "cards": [{
    "symbol": "BTCUSDT", "interval": "15m", "mark_price": "83512.01",
    "phase": "critical_down", "phase_label": "临界下跌", "direction": "SHORT",
    "action_label": "可以做空", "strength": 100,
    "psi": "-0.016", "phi": "19.0", "entropy": "0.869",
    "entry": "83512.01", "stop_loss": "84347.13", "take_profit": "81841.77",
    "stop_pct": "0.01", "risk_usdt": "0.2",
    "suggested_notional": "20.00", "suggested_leverage": 2,
    "reasons": ["熵 0.87 高于临界值 0.7，动量 ψ=-0.016% 为负", "..."]
  }]
}
```

## 5. 界面

`/trade?section=strategies` 顶部「NEMT 实时看单」：

- 每张卡片：币种 / 周期 / 标记价、相位徽章、ψ H φ、强度条、一句话理由
- 可执行信号额外显示：入场 · 止损 · 止盈、建议仓位与风险、**「按信号做多/做空（模拟）」按钮**
- 点击按钮 = 用建议仓位开一张**模拟合约**，然后自动跳到执行页；止损止盈需要你自己按（尚未做挂单）
- 30 秒自动刷新，可切 15m / 1h / 4h

## 6. 已验证

- `backend/tests/test_signals.py` 13 个测试：ψ/φ/S 公式、相位规则、ATR、卡片方向、风险仓位不超过现金、HTTP 路由
- 真实行情实测：15m/1h/4h 三币种均返回合理状态；横盘时全部 `critical`（等待）
- 端到端：点「按信号做空」→ 生成 BTC/USDT SHORT 2x 模拟仓（0.0002396 @ 83,474.25，保证金 10U）→ 跳到执行页

## 7. 已知缺口

- **止损/止盈不会自动执行**：卡片给的是价位，模拟盘要先手动平仓。需要下一期做「挂单式止盈止损」或在轮询里检查价格触发。
- **没有回测**：这套阈值是基于参考实现，没有在本仓库跑过历史统计。
- **没有资金费率/持仓量**：`nemt_signals.py` 里的涡旋/共振用了 OI、MVRV 等数据，这里只做纯 K 线版。
