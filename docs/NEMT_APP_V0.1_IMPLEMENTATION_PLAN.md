# NEMT App V0.1 — 开发实施方案（2026-10-17）

> **状态：开发任务说明 / 尚未实现。**  
> 开发总任务：[#5](https://github.com/huliye24/NEMT-Simulator2/issues/5)  
> 适用范围：NEMT App V0.1 — Binance Spot Testnet 手机交易终端。  
> 目标：**App 优先、交易闭环优先、研究成果逐步接入**。先建立真实行情与可核对的模拟订单反馈，然后再推进受限实盘。**本计划不授权任何真实资金交易。**

## 1. 项目目标与非目标

### V0.1 必须完成
1. 手机可访问的 React PWA（总览 / 行情 / 资产 / 下单 / 订单记录 / 设置）。
2. 云端身份认证、RBAC 与 Binance 凭据安全管理。
3. BTCUSDT 现货行情、K 线、只读账户余额和连接状态。
4. Binance Spot Testnet 市价/限价下单、撤单、部分成交、失败与重连恢复。
5. 每单服务端风险校验、人工确认、唯一 clientOrderId、持久化订单和交易审计。
6. 异常告警、停止新开仓机制、部署与可复现 E2E 测试。

### 明确不做
- V0.1 不做桌面软件，不强制原生 Android/iOS；PWA 作为最短路径。
- 不做期货/合约、杠杆、提现、划转、自动复制交易。
- 不要求 MATLAB/GPU 常驻或参与下单，也不把现有 NEMT 信号直接接到真金白银订单。
- 不以任何截图、模拟收益或 Testnet PnL 证明策略盈利。

### 后续扩展（V0.2+）
- NEMT Signal → 候选交易建议 → 人工审批 → 下单；待独立回测、滚动样本外、滑点/手续费/可交易性和纸面交易结果达标后，才考虑自动化策略。
- MATLAB/GPU 作为**离线研究流水线**，产出版本化模型/策略，不能直接更改生产风控与订单系统。

## 2. 当前仓库可复用资产与已发现风险

| 当前路径 | 建议 |
|---|---|
| `web/` | 现有 React 18 + TypeScript + Vite；保留 NEMT 实验页面，新增手机优先 /trade 路由与 PWA |
| `quant-mvp/collector/main.go` | 复用 Go WebSocket 连接与 Redis 代码，但**先修行情字段和 Kline 解码** |
| `quant-mvp/docker-compose.yml` | Redis 映射宿主机端口 6379；部署前取消公网暴露或仅 localhost |
| `binance_fetcher.py` | 可用于历史行情；缺少交易所账户安全适配层，不应作为完整下单 SDK |
| `nemt_execution.py`, `nemt_risk.py` | 作为研究/策略参考，不能直接视为已验证的实盘风控 |
| `matlab/`, `experiments.py` | 研究环境继续保留，不进入 V0.1 的交易同步调用链 |
| `quant-mvp/calculator/backtest/` | 回测实验代码需独立审查，不能用它验证生产订单一致性 |

**行情解析必须先修正：** Binance `@ticker` 中 `p` 是 24 小时**价格变化额**，`c` 才是**最新成交价**。当前 Go `BinanceTicker.Price` 使用 `json:"p"`，不应将该值显示为现价。另 `@kline` 的 OHLC 在嵌套 `k` 对象中，Kline 可能是 raw 流事件或 combined 流 `{stream,data}`，当前代码按顶层 OHLC/数组解析，需要重写并加回归测试。这是准确性优先的 P0 风险，详见 [#8](https://github.com/huliye24/NEMT-Simulator2/issues/8)。

## 3. 推荐生产架构

```text
NEMT React PWA (Android Chrome / Desktop Browser)
   │ HTTPS / WSS    (无 Binance API Key)
   ▼
FastAPI /api/v1 ── Auth, Session, RBAC, Rate Limit
   ├── Market API ← Go Binance WS collector ← Public Spot feed
   │                 └── Redis (private)
   ├── Account API ── BinanceSpotAdapter (read-only)
   ├── Order API ──── PREVIEW → AUTH → RISK → STORE → SEND → RECONCILE
   │                    │                     │
   │                 Risk Engine          Binance Spot Testnet
   ├── Admin API ──── PAUSE_NEW_ORDERS / RESUME (audited)
   └── Audit / Status / Alerts
               │
          PostgreSQL (private)
               │
       Backup / monitoring / recovery

Offline research: NEMT theory + MATLAB + GPU → versioned research output
                  （与生产交易链路物理/权限隔离）
```

### 建议依赖
- 前端：延续 `web/` 的 React/TypeScript/Vite；PWA manifest/service worker；E2E 可用 Playwright。
- 后端：FastAPI + Pydantic + SQLAlchemy/Alembic + PostgreSQL；API 契约从 OpenAPI 自动生成前端类型。
- 市场采集：保留 Go + Redis Stream，避免不必要的全量技术重写。
- 秘密管理：云托管 secret manager 或同等方案；开发仅用本地测试凭据，生产不得向开发人员散发明文密钥。
- CI/CD：GitHub Actions + Docker；使用独立 TESTNET staging。

### 环境隔离
| 环境 | 主要用途 | API/凭据 | 是否允许提交订单 |
|---|---|---|---|
| DEMO | UI 离线演示/单元测试 | 固定 mock 数据 | 仅本地模拟 |
| TESTNET | 交易所模拟成交与验收 | 专用 Spot Testnet Key | 是，仅 Testnet |
| LIVE-READONLY | 正式账户余额查询 | 只读正式 Key | 否 |
| LIVE-TRADING | 独立批准的受限真钱现货 | 单独的交易 Key 和门禁 | 默认否，详见 #15 |

`mode` 来源必须由服务端配置/已批准账户映射决定；前端的模式选择不是授权依据。
生产账户是否可用须确认币安规则与用户所在司法辖区要求。禁止绕过区域或账户限制。

## 4. API 契约（V0.1 建议）

下列路径为**拟定接口**，非现有代码实现；团队以 OpenAPI 作为最终协议来源。

| 方法 | 路径 | 权限 | 功能 |
|---|---|---|---|
| GET | `/api/v1/health` | 无/内部 | liveness/readiness |
| GET | `/api/v1/system/status` | viewer | 模式、暂停状态、延迟、行情/账户新鲜度 |
| GET | `/api/v1/market/ticker?symbol=BTCUSDT` | viewer | 最新价和更新时间 |
| GET | `/api/v1/market/klines` | viewer | 交易对/周期/起止时间 |
| GET | `/api/v1/account/balances` | viewer | 只读可用/冻结余额 |
| GET | `/api/v1/orders` | viewer | 已提交订单及成交状态 |
| POST | `/api/v1/orders/preview` | trader | 服务器验证精度、余额、风控与费用预估 |
| POST | `/api/v1/orders` | trader + re-auth | 消耗一次性确认令牌，执行 Testnet 下单 |
| POST | `/api/v1/orders/{id}/cancel` | trader + re-auth | 指定订单撤单 |
| POST | `/api/v1/admin/pause-new-orders` | admin + re-auth | 阻止后续新单，不代表平仓 |
| POST | `/api/v1/admin/resume-new-orders` | admin + re-auth | 重新启用符合限额的交易操作 |
| GET | `/api/v1/audit/events` | admin | 查询脱敏交易审计日志 |

所有交易变更必须生成 request ID、actor、mode、risk_decision、server_timestamp、订单幂等标识与审计链路。接口返回须包括 stale/error/mode 明确信息，不能只凭 HTTP 200 显示「已成交」。

## 5. 订单状态与风控规范

### 交易链路
1. UI 读取行情和余额，填写订单表单（BTCUSDT / side / type / price / qty）。
2. `preview` 在服务器验证 `exchangeInfo` 过滤器、金额与仓位限制，返回有效期较短的审批/预览标识。
3. 用户在手机二次确认；服务端检查会话、MFA/re-auth、确认标识、模式、资金与风险硬限额。
4. 数据库先持久化内部订单与唯一 `clientOrderId`，原子预留预算/敞口。
5. 仅 TESTNET adapter 发起 Binance 请求，设置超时；**超时或结果未知时查单对账，严禁盲目重发订单**。
6. User Data Stream 或 REST reconciliation 更新状态及 fills；每个 exchange trade ID 去重。
7. UI 由服务端持久化状态显示 NEW / PARTIALLY_FILLED / FILLED / CANCELED / EXPIRED / REJECTED；未知状态标记为 `PENDING_RECONCILIATION`。

### 最小独立风控
- 模式和授权、交易对 allowlist、单笔最大名义金额、日交易预算、日损失阈值、最大持仓、未完成订单额度。
- 行情/余额/连接 stale、无法估值、风控服务不可用、额度无法原子锁定 → fail closed。
- `PAUSE_NEW_ORDERS` 只暂停新订单；`CANCEL_OPEN_ORDERS` 是单独操作；已成交头寸仍需人工检查风险。
- 所有阈值配置在服务器，不能由前端参数直接放宽；LIVE 默认禁止。
- 市价单估算有滑点和成交金额变化风险；不能用预览价作为保证成交价。

## 6. 数据库建议最小表

- `users`, `sessions`, `roles`
- `exchange_accounts`（仅记录密钥引用和账户权限/模式，**不存明文 Secret**）
- `balances_snapshot`（余额及 UTC 时间戳）
- `order_requests`（幂等 ID、预览及确认信息）
- `orders`（内部 ID、交易所 ID、交易对、方向、数量、状态、模式）
- `fills`（交易 ID、成交数量/价格、手续费、币种）
- `risk_policies`, `risk_decisions`, `risk_reservations`
- `audit_events`, `service_heartbeats`

写库/发单一致性与事件恢复采用业务事务、唯一约束、单次发送锁及定时 reconciliation 解决，不假设跨数据库与币安 API 可获得分布式原子事务。

## 7. 开发顺序与认领矩阵

| 阶段 | Issue | 负责人类型 | 交付依赖 |
|---|---|---|---|
| A 工程底座 | [#6](https://github.com/huliye24/NEMT-Simulator2/issues/6) | Backend/DevOps | 无 |
| A API/认证 | [#7](https://github.com/huliye24/NEMT-Simulator2/issues/7) | Backend/Security | #6 |
| A 公共行情 | [#8](https://github.com/huliye24/NEMT-Simulator2/issues/8) | Go/Backend | #6，API 契约 #7 |
| B 只读币安 | [#9](https://github.com/huliye24/NEMT-Simulator2/issues/9) | Backend | #6、#7 |
| B 独立风控 | [#11](https://github.com/huliye24/NEMT-Simulator2/issues/11) | Backend/Risk | #6、#7、#9 |
| B Testnet 订单 | [#10](https://github.com/huliye24/NEMT-Simulator2/issues/10) | Backend/Exchange | #7、#9、#11 |
| B 交易对账 | [#13](https://github.com/huliye24/NEMT-Simulator2/issues/13) | Backend/Data | #7、#9、#10 |
| A→C 手机 PWA | [#12](https://github.com/huliye24/NEMT-Simulator2/issues/12) | Frontend | mock 可提前开发；验收需真实 API |
| C 质量/部署 | [#14](https://github.com/huliye24/NEMT-Simulator2/issues/14) | QA/DevOps | 与开发并行，最终依赖 #6–#13 |
| D 实盘审批 | [#15](https://github.com/huliye24/NEMT-Simulator2/issues/15) | Owner/Security | 独立后续，不属于 Testnet MVP 完成条件 |

**可并行认领建议**：1 人负责 #6/#7，1 人负责 #8/#9/#10/#11/#13，1 人负责 #12，另有人协助 #14 安全、测试和部署；实际安排以团队资源为准。任何人都不应绕过评审直接修改 LIVE 写单开关。

## 8. 测试矩阵（每个相关 PR 要提供证据）

| 用例 | 预期结果 |
|---|---|
| 无密钥启动 DEMO | UI 正常展示 mock，禁止外部写单 |
| 在 TESTNET 展示 BTC 行情 | 最新价取 `c`，24h 变化取 `p`；K 线取嵌套 `k` |
| WebSocket 断开 1 分钟再恢复 | UI 显示 stale，后台回补/重新同步 |
| TESTNET 限价单后撤单 | 状态经过 NEW 到 CANCELED，订单库与交易所一致 |
| TESTNET 市价单成交 | 记录实际 fills、手续费和最终数量 |
| 部分成交后取消余量 | 既保留已成交部分，又正确记录剩余取消 |
| 手动双击提交 / 网络超时 | 无双重订单，查单修复未知状态 |
| Binance 429/418/5xx | 有限退避、限频、告警，不能盲目重复发单 |
| 未授权角色调用 POST /orders | 403；无外部副作用 |
| 测试前端伪造 LIVE 模式 | 服务器拒绝 |
| 超过配置金额/风险额度 | 服务端拒绝且留痕 |
| 风控不可用或行情过期 | fail closed，无新订单 |
| 暂停交易后刷新页面 | 暂停状态持续生效，不能绕过 |
| 重启后台服务 | 未终结订单重建/对账 |
| 日志和浏览器存储检查 | 无 API 密钥、签名和 Secret |
| 构建 PWA 并测试手机 | 375px 无溢出、流程可触控、断网交易不可提交 |

## 9. PR 交付规范（交给每位开发者）

每个 Issue 建立独立分支，例如 `feat/nemt-app-06-binance-spot-adapter`。一个可合并 PR 至少包含：
1. 对应 Issue（`Closes #编号`），变化范围与已知风险。
2. 代码、配置样例、迁移及版本化 OpenAPI（若适用）。
3. `lint`/`typecheck`/单元测试通过记录，必要的 Testnet 集成测试证据。
4. 截图或录像（UI）；审计日志/订单事件脱敏示例（后端）。
5. 数据库/订单/环境变更对应回滚方式，避免生产不可逆操作。
6. 审查人复核安全边界、环境配置、幂等和订单对账，不允许未经测试直接合入生产。

## 10. 里程碑（按验收 Gate，而非不现实的时间承诺）

- **Gate A：只读联通** —— #6、#7、#8、#9 完成，手机看到准确行情、只读余额，未授权写单不可能。
- **Gate B：模拟实战** —— #10、#11、#13 完成，Testnet 可买卖/撤单/对账、风控拒单、故障恢复。
- **Gate C：可交付 App** —— #12、#14 完成，移动 PWA/QA/CI/安全部署/操作手册齐全。
- **Gate D：真钱交易准入** —— #15 独立审批，所有条件满足方可受限启用；不影响 V0.1（Testnet）的交付。

## 11. 交易所官方资料（实现时须复核最新版本）

- Spot REST / 签名 / 速率限制：https://developers.binance.com/en/docs/products/spot/rest-api
- Spot Testnet Streams：https://developers.binance.com/zh-CN/docs/products/spot/testnet/web-socket-streams
- Spot User Data Stream：https://developers.binance.com/en/docs/catalog/core-trading-spot-trading/api/ws-api/user-data-stream
- 官方 Spot WS payload 参考：https://github.com/binance/binance-spot-api-docs/blob/master/web-socket-streams.md

> **给开发负责人：** 先认领 [#6](https://github.com/huliye24/NEMT-Simulator2/issues/6)，同步安排前端在 mock API 上推进 [#12](https://github.com/huliye24/NEMT-Simulator2/issues/12)。交易所对接先只读、后 Testnet；实盘写权限不得因技术上“能调用 API”就提前开放。
