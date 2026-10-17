# NEMT-Simulator2 代码与能力审计

审计日期：2026-10-17
审计对象：本地仓库 `E:\NEMT Simulator`（remote `huliye24/NEMT-Simulator2`，分支 `feature/mcp-quant-sync`，HEAD `b943002`）
审计目的：为「收敛为以 NEMT 理论验证为核心的个人 BTC 量化研究系统」提供复用决策依据

## 0. 前置检查结果（强制项）

### 0.1 AGENTS.md 已读

已读取根目录 `AGENTS.md`（14692 字节）。其中第 346–373 行内嵌了方向锁规则：

- **允许修改**：`/web/src/components`、`/web/src/stores`、`/web/src/pages`、`/web/src/hooks`、`/web/src/utils`、`/nemt_os/services`、`/docs`
- **禁止修改**：`/core`、`/database`、`/auth`、`/.git`

本次改造将只写入 `docs/` 与 `nemt_os/services/`，符合方向锁。

### 0.2 `.cursor/rules/DIRECTION_LOCK.md` 不存在 —— 明确报告

**该文件不存在。** 已做三重确认：

1. `.cursor/rules/` 目录下只有 `mattpocock-skills/` 与 `nemt-plugins/` 两个子目录，无 `DIRECTION_LOCK.md`
2. 全仓库 `find -iname "*DIRECTION_LOCK*"` 无任何结果
3. 全仓库 grep `direction_lock|方向锁` 仅命中 `AGENTS.md`（指向该缺失文件）、`tools/cloud_dev/cloud_dev/UPLOAD_PLAN_200_STEPS.md`、`web/node_modules/axe-core/locales/zh_CN.json`（无关）

AGENTS.md 第 3 行与第 347 行两处要求「必须先读取 `.cursor/rules/DIRECTION_LOCK.md」**，但该文件缺失。本次以 **AGENTS.md 内嵌的方向锁章节（346–373 行）作为权威约束来源**，未虚构文件内容。建议后续补建该文件。

### 0.3 Git 状态

分支 `feature/mcp-quant-sync`，**存在 26 项未提交改动**（12 修改 / 5 删除 / 9 未跟踪，如 `.codex/`、`btc_data.csv`、`web/src/lib/council.ts`、`web/src/components/CouncilPanel.tsx` 等）。

**本次审计为纯只读操作，未提交、未暂存、未回滚、未删除任何文件。** 后续实现阶段同样只在允许目录新增文件，不触碰任何已有改动。

### 0.4 重要环境事实：本地工作树 ≠ GitHub remote 快照

GitHub `main` 分支只有 2 个提交、2445 个文件；本地分支是 `feature/mcp-quant-sync`，HEAD `b943002`，包含 Electron、`web/src/app`、`nemt_os/` 分层后端等大量未推送内容。**审计以本地工作树为准。**

---

## 1. Binance 数据获取

| # | 路径 | 行数 | 端点 | 需 Key | 返回结构 | 时间戳 | 校验 | 缓存 | 主流程 |
|---|---|---|---|---|---|---|---|---|---|
| A | `binance_fetcher.py` | 492 | `/api/v3/klines` | 否 | DataFrame 12 列 + symbol | ms→naive datetime | 无 | 写 `matlab_data/*.csv` | **否**（孤立） |
| B | `data_fetcher.py` | 218 | 同上 | 否 | DataFrame 12 列 | ms→naive | 全行去重，**不排序** | 写 `btc_data.csv` | **是**（`main.py:35`、两个 `api_server_prod.py`） |
| C | `quant-sync-server/data_fetcher.py` | 106 | 同上 | 否 | DataFrame，列名与 A/B **不一致** | 同上 | 无 | `data/*.csv` | 否 |
| D | `services/quant-sync-server/quant-sync-server/data_fetcher.py` | — | 同上 | 否 | 同 C 但内容又不同 | 同上 | 无 | — | 否 |
| E | `NEMT-Simulator2/{binance_fetcher,data_fetcher}.py` | — | — | — | 与 A/B **逐字节相同**（嵌套副本） | — | — | — | 否 |
| F | `fetch_binance_to_cos.py` | 487 | 同上 | 否 | `List[Dict]` | **本地时区 ISO 字符串（有毒）** | **有** `validate_klines` / `validate_price` | JSON→COS→删本地 | 被 `schedule_fetch.py:66` 调用 |
| G | `src/nemt-os/nemt/market_providers/binance_provider.py` | 590 | REST + WS | 否 | `KLine` dataclass | ms→datetime | 无 | 内存 | 被 `market_providers/factory.py` 惰性导入 |
| H | `src/web/strategy/exchange/binanceAdapter.ts` | 492 | testnet | 交易需 | — | ms | 无 | 缓存永不被填充（bug） | 前端 |
| I | `src/web/infrastructure/binanceService.ts` | 552 | `api.binance.com` | 否 | `BinanceKline` 11 字段 | ms | 无 | 有重试+熔断 | 前端 |
| J | `src/web/strategy/backtest/dataLoader.ts` | 424 | 同上 | 否 | 列式 | ms | **有** `validateData` | 恒空（`_raw` 不存在） | 前端 |
| K | `quant-mvp/collector/main.go` | 257 | WS→Redis | 否 | — | — | — | Redis | **死代码**（`subscribeKlines` 未被 main 调用） |
| M | `backend/services/binance_connector.py` | 196 | — | — | **纯 mock 随机价** | — | — | — | 空壳 |

### 现有本地数据（关键约束）

```
btc_data.csv                        1000 行 1m   2026-08-24 07:29 → 2026-08-25 00:08
data/1h/BTC_20260405_168rows.csv     168 行 1h   2026-04-05 起
matlab_data/BTC_1h.csv               720 行 1h   2026-03-13 → 2026-04-12
nemt_os/data/                        空
backtest/data/cache/                 空
```

**⚠️ 最长历史样本仅 720 根 1h（约 30 天）**，远不满足第四阶段「至少覆盖一个完整牛熊周期」的要求。第四阶段必须显式报告数据不足，或先补数据。

### 重复分组

- **G1 历史 REST→DataFrame**：A / B / C / D / E —— 同一分页逻辑抄 5 遍，列名三套互不兼容
- **G2 历史 REST→dict+校验**：F（全仓唯一带 OHLC 关系校验者）
- **G3 Provider 抽象**：G(Python) / H / I / J(TS)
- **G4 实时流**：K / G 的 WS / I 的 connect —— 第一阶段全部不需要

### 未来数据泄漏

**统一风险：A/B/F/G/I/J 的 `endTime` 默认取 `datetime.now()`，最后一根 K 线是未收盘的。** 事件检测若直接消费，等于用未定盘的 high/low/close 触发信号。

- `binance_fetcher.py` 的 `fetch_range` 对 `end_date` 多加 `86400*1000`，整日越界
- `fetch_binance_to_cos.py`：`days=2` 但 `limit=1000`，1m 需 2880 根，被静默截断
- **没有任何实现剔除未收盘 bar**

### 复用决策

**选定：G 的抽象内核 + F 的校验函数。**

理由：G 是唯一有 Provider 抽象（继承 `BaseMarketProvider`，返回 `KLine` dataclass，同目录已有 `csv_provider.py` / `mock_provider.py` / `factory.py`，可单测可切换）；G 的 `get_history_by_days` 分页终止条件正确（A/B 靠 `close_time+interval_ms` 推进，F 根本不分页）。F 的 `validate_klines()` / `validate_price()` 是全仓唯一做过 OHLC 关系与非正价检查的代码，直接搬用不重写。

必须修复：落盘前剔除未收盘 bar；时间戳统一为 **UTC ms epoch int64**（废弃 F 的本地时区字符串、A/B 的 naive datetime）；强制 `sort_values` + `drop_duplicates('open_time')`。

---

## 2. NEMT / NLS 计算与信号

| 变量 | 路径 | 函数:行 | 定义 | 输出范围 / 缺失处理 |
|---|---|---|---|---|
| psi | `nemt_core.py` | `initialize_state:61`, `evolve:101` | `(p-mean(p))/std(p)` **全序列 z-score**，虚部=0 | — |
| psi | `nemt_os/nemt/nEMT_core/nls_solver.py` | `initialize_state:97`, `evolve:163` | 同上（自研 Complex 类） | std=0→全 0 |
| psi | `quant-sync-server/high_performance_nls.py` | `_initialize:182` | 同上 + `1e-10` 防零除 | — |
| alpha/beta/eta | 三处 dataclass | `NEMTParams:41` / `NLSParams:12` / `NLSConfig` | **全部硬编码常数，零处从数据估计** | α=0.1 或 0.5，β=1.0，η=noise_level |
| DCI #1 | `nemt_signals.py` | `compute_dci:133` | `max(上涨根数, 下跌根数)/n`，窗口 24 | [0.5,1.0]；n<2 → **硬返 0.5 伪造中性** |
| DCI #2 | `enhanced_phase_detector.py` | `_compute_dci:338` | 同公式但**无窗口**，取全数组 | len<2 → 返 0.5 |
| DCI #3 | `services/cloud-memory/.../mcp_server_enhanced.py` | `compute_dci:237` | **符号变号率** `sign_changes/(w-1)`，与 NEMT 无关 | 另一个量，命名污染 |
| spectral_width #1 | `nemt_core.py` | `compute_spectral_width:178` | 正半轴、**功率加权**二阶矩 | <1e-10 → 0.0 |
| spectral_width #2 | `nemt_os/nEMT_core/nls_solver.py` | `compute_spectral_width:256` | fftshift 双边、**幅度**加权 | 退化 → **硬编码 0.02** |
| spectral_width #3 | `nemt_os/nemt/emt_core/spectral_analyzer.py` | `compute_spectral_width:78` | 正半轴、先 /max 归一化、功率加权 | 0.0 |
| spectral_width #4 | `high_performance_nls.py` | `_spectral_analysis:430` | fftshift 后取正半、/max、功率加权 | 0.0 |
| spectral_width #5 | `enhanced_phase_detector.py` | `_compute_spectral_width:353` | **❌ 假指标**：`np.std(功率谱)`，**完全不用频率轴** | len<10 → **硬返 0.05** |
| spectral_width #6 | `nemt_model_node.py` | `_run_fallback_analysis:585` | 同上假公式 | 降级路径 |
| spectral_width #7 | `web-vite-backup/.../nemtCore.ts` | `computeSpectralWidth:387` | 幅度加权 | NaN → **`0.015 + Math.random()*0.01` 随机数** |
| vortex_score | `nemt_signals.py` | `detect_vortex:222` | 4 条件：BBW<20 分位(L253)、量比 40–60%(L273)、OI 高且变幅<5%(L283)、资金费率 7 日均值<1e-4(L291)；**满足 ≥3 即判定**(L298)；maturity = `条件数*2.5*min(oi_ratio,2)`(L305) | **无上界，可达 20** |
| resonance_score | `nemt_signals.py` | `detect_resonance:323` | ①长周期评分≥4(L406) ②DCI 波动率∈[0.08,0.15](L410) ③外部事件标志(L420)；三者 AND(L423) | confidence **恒 = 1.0**（三条件已 AND，退化为常数） |
| market_phase #1 | `nemt_signals.py` | `determine_phase:444` | 共振→C；涡旋→B；DCI<0.55→A；DCI>0.65→D | 置信度**可 >1 或为负**，未裁剪 |
| market_phase #2 | `nemt_state_machine.py` | `_evaluate_phase_transition:268` | 第三套优先级 | 与 #1 冲突 |
| market_phase #3 | `nemt_os/nemt/emt_core/phase_detector.py` | `detect:104` | **仅看谱宽阈值** 0.025/0.020/0.015 | 与前两者完全不同 |

### 数值方法

Euler / RK4 / SSFM 混用且**互相不可比**：

- 离散化不同：Euler/RK4 用二阶差分 `(ψ[i-1]-2ψ[i]+ψ[i+1])/dx²`；SSFM 用 `-4π²f²`（`high_performance_nls.py:396`）
- 边界条件不同：Euler 用单边（`nemt_core.py:91`）；SSFM 经 FFT 隐含周期性
- `nls_solver.py:158` 用 `/dx` 而非 `/dx²`（**量纲错误**）
- 噪声尺度不同：Euler `dt*noise`（L139）；SSFM `sqrt(dt)*noise`（L412）

**唯一正经积分器是 `quant-sync-server/high_performance_nls.py`**：`_evolve_euler:285`、`_evolve_leapfrog:310`、`_evolve_rk4:352`、`_evolve_ssfm:385`（真分裂步傅里叶）。

### 未来数据泄漏（精确到行）

| # | 位置 | 问题 |
|---|---|---|
| **L1** | `nemt_core.py:72`、`NEMT-Simulator2/nemt_core.py:72`、`nemt_os/nemt/nEMT_core/nls_solver.py:110`、`nemt_os/nemt/emt_core/nls_solver.py:69`、`high_performance_nls.py:184` | **全样本 mean/std 归一化**。`experiments.py:58` 把整段序列传给 `initialize_state`，用未来 K 线构造 ψ。**流式且只传回看窗时不泄漏** → 高危模式 |
| **L2** | `nemt_signals.py:255` `np.percentile(bbw_history, 20)` | 对**整段** bbw_history 求分位，无 `[-N:]` 截断；同函数 L282 却写了 `oi_values[-30:]`。**同一函数内窗口策略自相矛盾**，按全历史调用即前视 |
| **L3** | `nemt_model_node.py:585` | `np.mean(returns)` 全序列去均值后再 FFT |
| **L4** | `enhanced_phase_detector.py:343` | `returns=np.diff(prices)` 对整段取差分，无窗口 |

未发现 `shift(-1)` / `rolling(center=True)`（命中项全在 vendored `freqtrade/`）。

### 「其实没被真正算出来」的项（重要）

1. **`enhanced_phase_detector.py` 的 vortex_score 从不计算** —— 仅为入参（L261），未传时 L318 `vortex_score or 0.0` **静默变 0.0**，且该 0.0 进入 `_determine_phase:503` 的决策评分
2. **`resonance.confidence` 退化常数** —— `nemt_signals.py:431` 为 `conditions_met/3.0`，而 L423 已硬性 AND，触发时恒为 1.0；`nemt_state_machine.py:286` 的 `>=0.6` 阈值永真，是死代码
3. **spectral_width #5/#6 是假的** —— 返回 `np.std(功率谱数组值)`，不含频率轴，与「谱宽」定义无关
4. **TS `nemtCore.ts:418` 返回随机数** `0.015 + Math.random()*0.01`，不可复现
5. `nls_solver.py:274/287` 硬编码返 0.02 占位
6. **alpha/beta/eta 零处从数据估计**；`η(x,t)` 的时空结构完全未实现
7. `nemt_signals.py:156` 数据不足返回 DCI=0.5 伪装中性信号

### 复用决策

**选定 `quant-sync-server/high_performance_nls.py` 作为 NLS 内核。**

理由：唯一同时提供 Euler/Leapfrog/RK4/SSFM 的实现，SSFM 是 NLS 标准保结构算法且已有精度基准（`self:611-621` 以 RK4 为参考）；`_initialize:184` 有防零除；退化时返回 0.0 **不伪造值**（对比 nls_solver 返 0.02、TS 返随机数、enhanced 返 0.05）；参数全量写入 `result.stats`（L265-272），最适合做可复现信封。

配套修复：psi 改为**滚动窗 z-score**（固定 lookback=128/256）；spectral_width 统一为**正半轴 + 功率加权 + 不归一化**，删除其余 6 份；DCI/vortex 的 BBW/OI 分位数统一加 `[-30:]` 截断；修 `nls_solver.py:158` 的 `/dx` → `/dx²`。

需废弃但暂不删除：`nemt_core.py`、`nemt_os/nemt/nEMT_core/nls_solver.py`、`nemt_os/nemt/emt_core/`（旧快照，三份 md5 完全相同）、`NEMT-Simulator2/` 嵌套副本、`web-vite-backup/`。

---

## 3. 策略 / 回测 / 风控 / 绩效

### 3.1 真实存在

| 路径 | 行数 | 内容 |
|---|---|---|
| `nemt_os/nemt/backtest.py` | 412 | `NEMTEngine`：`load_data` / `run` / `_process_bar` / `_execute_signal` / `_finalize`。分层：`MarketLayer` + `DataLayer` + `SignalLayer` + `StrategyPool` + `ExecutionLayer` + `RiskLayer` + `Dashboard`。配置含 `slippage_bps`、`commission_bps` |
| `nemt_os/nemt/execution.py` | 412 | `Order` / `Position` / `Trade` / `ExecutionLayer`。`slippage_bps=1.0`、`commission_bps=5.0` 默认 |
| `nemt_os/nemt/strategy.py` | 398 | 策略池 + `calculate_sharpe(returns, risk_free_rate=0.02)` (L44) |
| `nemt_os/nemt/core/position_capsule.py` | — | `_update_max_drawdown` (L578) |
| `quant-mvp/calculator/backtest/backtest.py` | — | 依赖 redis，docker-compose 微服务遗留，未接入主流程 |
| `nemt_controller.py`、`nemt_execution.py`、`nemt_risk.py` | — | 根目录理论实现（规则最全） |

**注**：AGENTS.md 描述的 `web/src/strategy/`、`web/src/trader/`、`web/src/ai/`（freqtrade/Lean/vnpy 风格 BacktestEngine、Optimizer、Alpha158、DeepSeek 策略等）**在本地工作树中不存在**。`web/src/` 下无 `strategy` 目录。AGENTS.md 第 149–182 行描述的是规划态，不是现状。vendored 的 `freqtrade/`、`vnpy/`、`Lean/` 目录存在但未被本地 Python 代码 import。

### 3.2 回测引擎逐项核查（以 `nemt_os/nemt/` 为准）

| 检查项 | 结论 | 证据 |
|---|---|---|
| 成交时机 | **❌ 当根 close 成交** | `backtest.py:190` `current_price = closes[-1]`，随后同 bar 内 `_execute_signal`。**非 next-bar open**，存在前视 |
| 手续费 | ✅ 双边 | `execution.py:215` `commission = executed_price * quantity * commission_bps / 10000`；`L225` `self.current_capital -= commission`。买卖均走 `execute_order` |
| 滑点 | ✅ 有，方向正确 | `execution.py:206-212`：买 `price*(1+slippage)`、卖 `price*(1-slippage)` |
| **滑点随机性** | **❌ 无种子** | `execution.py:261` `random.uniform(-0.5, 0.5)` —— **不可复现** |
| mark-to-market | ✅ 正确 | `execution.py:331-334` `get_equity()` = `current_capital + Σ(quantity * current_price)` |
| 未平仓结算 | 需确认 | `_finalize` (L327) 存在，实现细节待实现阶段核对 |
| 负现金防护 | 需确认 | `get_available_capital` (L336) 存在 |
| Sharpe | ⚠️ 有但粗糙 | `strategy.py:44`，年化因子与周期耦合未显式化 |
| Sortino / payoff_ratio / exposure | ❌ 未见 | 全仓无实现 |
| profit_factor | ✅ 有 | `execution.py:367` |
| max_drawdown | ✅ 有 | `nemt_os/nemt/core/position_capsule.py:578` |

### 3.3 复用决策

**选定 `nemt_os/nemt/execution.py` 的计费与权益模型作为回测内核基础。**

理由：它是全仓唯一同时正确处理**双边手续费 + 方向正确滑点 + mark-to-market 权益**的实现，这三点正是可信回测的地基，重写风险高于改造成本。

必改项：
1. **成交时机改为 next-bar open**（`backtest.py:190` 的 `closes[-1]` 只用于生成信号，成交价取下一根 `open`）
2. **滑点引入确定性种子**（`execution.py:261` 的 `random.uniform` 改为注入的 `np.random.default_rng(seed)`）
3. 补齐 Sortino / payoff_ratio / exposure / annualized_return
4. Sharpe 年化因子按 timeframe 显式化（1h → 8760）

`quant-mvp/calculator/backtest/backtest.py` 标记为**非主路径**（依赖 redis，与 CPU 单机约束冲突）。

---

## 4. 全局结论

### 4.1 唯一版本选定汇总

| 能力 | 选定实现 | 状态 |
|---|---|---|
| Binance 数据获取 | `src/nemt-os/nemt/market_providers/binance_provider.py` 内核 + `fetch_binance_to_cos.py` 的 `validate_klines`/`validate_price` | 需补未收盘 bar 剔除 + UTC 统一 |
| NLS / psi / spectral_width | `quant-sync-server/high_performance_nls.py` | 需改滚动窗 psi + 统一谱宽定义 |
| DCI / vortex / phase | `nemt_signals.py`（`compute_dci:133`、`detect_vortex:222`、`determine_phase:444`） | 需加分位数窗口截断 + 裁剪越界置信度 |
| 回测计费 / 权益 | `nemt_os/nemt/execution.py` | 需改 next-bar open + 确定性种子 |
| 回测主循环结构 | `nemt_os/nemt/backtest.py` 的 `NEMTEngine` 分层 | 需改成交时机 |

### 4.2 需废弃但**暂不删除**的模块

按方向锁与「不删除旧代码」纪律，以下标记为 **non-canonical**，仅在新主链路明确标注 canonical 后自然让位：

- `binance_fetcher.py`、`data_fetcher.py`、`NEMT-Simulator2/`（嵌套逐字节副本）、`quant-sync-server/data_fetcher.py`、`services/.../data_fetcher.py`
- `nemt_core.py`、`nemt_os/nemt/nEMT_core/nls_solver.py`、`nemt_os/nemt/emt_core/`（旧快照）
- `enhanced_phase_detector.py`（vortex/resonance 实为常量 0，谱宽为假公式）
- `nemt_model_node.py:585`（假谱宽降级路径）
- `web-vite-backup/.../nemtCore.ts`（随机数谱宽）
- `quant-mvp/collector/main.go`、`quant-mvp/calculator/`（Go + Redis 微服务遗留）
- `backend/services/binance_connector.py`（纯 mock 空壳）
- `nemt_volatility_model.py`、`nemt_spatial_temporal.py`、`nemt_economic_analysis.py`、`nemt_probability_execution.py`（引用数 = 0 的孤儿）

### 4.3 阻塞性风险（必须在第四阶段前解决）

**R1 · 历史数据不足。** 现有最长 1h 样本 720 根（30 天），无法覆盖一个完整牛熊周期。第四阶段实验必须显式报告数据不足，或先用 Binance 公共接口补齐 2018 年至今的 BTCUSDT 1h 数据并缓存。

**R2 · 谱宽定义分裂为 7 份且 2 份为假公式。** 在变量注册表冻结定义之前，任何实验结果都不可复现、不可比较。

**R3 · alpha/beta/eta 无数据估计。** NLS 三参数全程为硬编码常数，理论上的「从市场估计 α（流动性）、β（非线性强度）」从未实现。第一阶段将明确记录为已知缺口，不假装已实现。

---

## 5. 审计纪律声明

- 本次审计为**纯只读**，未修改、未删除、未提交任何文件
- 所有结论均来自实际代码读取，行号为审计时状态
- 未发现但可能存在的能力，将在实现阶段补充
