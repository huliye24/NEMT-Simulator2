# NEMT App — 实盘（LIVE）切换手册

更新：2026-10-21 · 适用代码：`backend/trade_app/`（23 个 pytest 全绿）
对应需求：把币安真实账户接进 `https://postyouth.club/trade` 并在站内真实下单。

> **一句话**：代码已经支持实盘下单，但默认关闭；**开启 = 用真钱**。本文是开启前的
> 唯一操作路径，跳步会失败或造成不可逆损失。

---

## 0. 2026-10-21 实测快照（先看这一节）

用你提供的 Key 在香港服务器（103.144.246.242）实测：

| 项目 | 结果 | 判定 |
|---|---|---|
| `/api/v3/account` | `HTTP 200` | ✅ Key 可用，IP 白名单已生效 |
| `accountType` | `SPOT` | ✅ |
| `canTrade` | `true` | ✅ 可下单 |
| **`canWithdraw`** | **`true`** | 🔴 **必须关闭** |
| 余额 | `0.69937212 USDT` / `0.0853 POL` / `0.00000479 BTC` | 🔴 不够下单 |
| BTCUSDT `minNotional` | `5.00000000 USDT` | 单笔最小 5 USDT |
| 站内 `?section=api` | `连接成功 · SPOT · 347ms · 允许交易` | ✅ 前端已接入 |

**结论：读链路已经打通并上线可用；下单卡在两件与代码无关的事上——提现权限没关、余额不足 5 USDT。**

---

## 1. 币安侧准备（你在后台做）

1. **关掉提现权限**（最高优先级）
   API 管理 → 该 Key → 编辑限制 → 取消「允许提现」→ 保存。
   页面上的红字告警 `⚠️ 该 Key 开启了提现权限，建议关闭` 就是这一项。
2. **权限只保留两项**：「允许读取」+「允许现货与杠杆交易」。不要开合约、划转、提现。
3. **IP 白名单**只留服务器出口 IP：
   - 网站后端：`103.144.246.242`
   - 本地开发（可选）：`111.243.104.215`
4. **充值**：单笔最小 5 USDT + 手续费，建议先充 **10–20 USDT** 做小额验收。
   顺带一提：`POL` 不在站点允许交易列表里（默认只有 `BTCUSDT`）。
5. 记下 Key/Secret，**验收完成后重新生成一对**（旧的已出现在聊天记录里）。

---

## 2. 服务器侧准备（我做 / 你做均可，逐条确认）

服务器：`root@103.144.246.242`，代码 `/opt/nemt-app`，venv `/opt/nemt-app/venv`，
环境文件 `/etc/nemt-app/api.env`（mode 600），数据 `/var/lib/nemt-app/nemt_app.sqlite3`。

必须同时满足，否则 `load_settings` 直接拒绝启动或风控拒绝下单：

```ini
NEMT_APP_MODE=LIVE
NEMT_MARKET_SOURCE=binance          # LIVE 不允许 demo 行情
NEMT_LIVE_TRADING_ENABLED=true      # 真正打开实盘写路径
NEMT_COOKIE_SECURE=true             # LIVE 强制
NEMT_SESSION_SECRET=<32+ 随机字符>   # 必须 >=32 位
NEMT_BINANCE_API_KEY=<Key>
NEMT_BINANCE_API_SECRET=<Secret>

# 操作员账号（>=12 位，DEMO 账号会被自动禁用）
NEMT_LIVE_ADMIN_USERNAME=ops
NEMT_LIVE_ADMIN_PASSWORD=<强密码>
NEMT_LIVE_TRADER_PASSWORD=<强密码>    # 可选，只读+交易，无 admin

# 限额：第一次先收窄，跑通再放开
NEMT_ALLOWED_SYMBOLS=BTCUSDT
NEMT_MIN_ORDER_NOTIONAL=5
NEMT_MAX_ORDER_NOTIONAL=20
NEMT_MAX_DAILY_NOTIONAL=50
NEMT_MAX_POSITION_NOTIONAL=100
NEMT_MAX_OPEN_ORDERS=2
NEMT_MAX_ORDERS_PER_MINUTE=5

NEMT_ALLOWED_ORIGINS=https://postyouth.club,https://www.postyouth.club
```

安全前置（不满足就不要开）：

- [ ] `/api/v1/auth/demo` 在 LIVE 下自动返回 404（代码已保证）
- [ ] 旧 `demo`/`viewer`/`admin` 账号在 LIVE 启动时被禁用（代码已保证）
- [ ] operator 密码不是 `nemt-demo` 这类默认值
- [ ] nginx Basic Auth 仍生效，且密码已更换（原密码曾交给多人）
- [ ] 已备份 `/var/lib/nemt-app/nemt_app.sqlite3`
- [ ] 已记住急停开关位置（见 §4）

---

## 3. 切换步骤

```bash
# 1) 备份数据库与环境文件
systemctl stop nemt-api
cp /var/lib/nemt-app/nemt_app.sqlite3 /root/nemt-app-backup-$(date +%F-%H%M).sqlite3
cp /etc/nemt-app/api.env /root/api.env.bak-$(date +%F-%H%M)

# 2) 部署当前代码（含 LIVE 闸门改造）
#    从本地 rsync/scp backend/ 后覆盖 /opt/nemt-app/backend/

# 3) 写入新的 api.env（见 §2），权限 600
chown nemtapp:nemtapp /etc/nemt-app/api.env && chmod 600 /etc/nemt-app/api.env

# 4) 启动并检查日志里没有 ConfigError
systemctl start nemt-api
journalctl -u nemt-api -n 40 --no-pager
```

启动日志里应能看到：

```
WARNING: NEMT_LIVE_TRADING_ENABLED is on. Orders are submitted to the Binance
production venue and spend real money. operator accounts=['ops']; max order=20 USDT; ...
```

看不到这行、或看到 `ConfigError`，说明闸门没满足，**不要继续**。

---

## 4. 验收（按顺序做，每步不过就停）

```bash
# a. 模式与闸门
curl -s http://127.0.0.1:8101/api/v1/system/status | python3 -m json.tool
#    期望：mode=LIVE, trading_enabled=true, live_trading_available=true,
#          account.connected=true, account.source=binance

# b. DEMO 后门确已关闭
curl -s -o /dev/null -w '%{http_code}\n' -X POST \
  http://127.0.0.1:8101/api/v1/auth/demo -H 'Content-Type: application/json' -d '{"account":"admin"}'
#    期望：404

# c. 真实余额
curl -s http://127.0.0.1:8101/api/v1/account/balances -b cookies.txt | python3 -m json.tool
```

然后在浏览器（`ops` 账号登录）用 **5–6 USDT 市价买 BTC**：

1. 预览 → 风控必须全部 ✅（`mode` 检查应显示"真实资金"字样）
2. 确认下单 → 订单状态 `FILLED` 或 `NEW`
3. **立刻去币安 App 的「订单/成交」核对**是否真有这一笔（金额、方向、时间）
4. 回站点核对订单历史、余额、手续费

急停（任何异常第一时间做）：

- 站点：设置 → 全局新订单开关（admin）
- 服务器：`curl -X POST .../api/v1/admin/pause-new-orders`（admin + CSRF）
- 兜底：币安后台直接**删除该 API Key**，站内所有下单立即失效

---

## 5. 回滚

```bash
systemctl stop nemt-api
cp /root/api.env.bak-<时间戳> /etc/nemt-app/api.env     # 切回 DEMO
systemctl start nemt-api
```

数据库不用回滚：DEMO 账本与真实余额是两套数据。若要把站点彻底恢复成纯演示，
把 `NEMT_APP_MODE` 改回 `DEMO` 并重启即可。

---

## 6. 已知缺口（开实盘前请知情）

- **没有 User Data Stream**：成交状态靠下单响应与 `clientOrderId` 对账，不做实时推送。
  挂单被外部撤销/部分成交时，站内状态可能滞后，需手动刷新。
- **没有后台对账 worker**（issue #13）：长时间挂单会与交易所产生偏差。
- **单账户共享**：服务端一对凭据服务所有登录用户，`ops` 与 `trader` 动的是同一个账户。
- **无 MFA/二次认证**：admin 操作只有 CSRF 与会话保护。
- **超时未知结果**：网络超时后不会重发 POST，会按 `clientOrderId` 查单，查不到则置
  `PENDING_RECONCILIATION`，需人工确认——这是刻意设计，避免重复下单。
- 站点仍依赖 nginx Basic Auth + 应用登录两层，公网可达。真要大额跑，建议再加一道 IP 限制。
