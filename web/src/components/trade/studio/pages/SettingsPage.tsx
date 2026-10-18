"use client";

import { useState } from "react";
import { ApiError, tradeApi } from "@/lib/trade/api";
import { ageLabel, cn, fmtTime, fmtUSDT } from "@/lib/trade/format";
import type { CancelOpenOrdersResponse } from "@/lib/trade/types";
import { CardHeader, PageHeader, StatusDot } from "../common";
import { StudioIcon } from "../icons";
import type { StudioPageProps } from "../types";

interface SettingsPageProps extends StudioPageProps {
  onLogout: () => Promise<void>;
}

export default function SettingsPage({
  session,
  data,
  notify,
  navigate,
  onLogout,
}: SettingsPageProps) {
  const { system, balances, orders, online } = data;
  const isAdmin = session.user.roles.includes("admin");
  const [reason, setReason] = useState("");
  const [adminBusy, setAdminBusy] = useState<"pause" | "resume" | "cancelAll" | null>(null);
  const [cancelAllConfirmed, setCancelAllConfirmed] = useState(false);
  const [cancelAllResult, setCancelAllResult] = useState<CancelOpenOrdersResponse | null>(null);
  const [logoutBusy, setLogoutBusy] = useState(false);

  const paused = Boolean(system?.risk.pause_new_orders);

  async function handlePauseToggle() {
    if (!system || adminBusy) return;
    if (reason.trim().length < 3) {
      notify("warning", "请输入至少 3 个字符的操作原因，该原因会写入审计日志");
      return;
    }
    setAdminBusy(paused ? "resume" : "pause");
    try {
      const next = paused
        ? await tradeApi.resumeOrders(session.csrf_token, reason.trim())
        : await tradeApi.pauseOrders(session.csrf_token, reason.trim());
      setReason("");
      notify(
        "success",
        next.pause_new_orders
          ? "已暂停全部新订单；已成交仓位不受影响"
          : "已恢复新订单；每笔订单仍需通过服务端风控"
      );
      await data.refreshAll();
    } catch (error) {
      notify("error", error instanceof ApiError ? error.message : "管理员操作失败");
    } finally {
      setAdminBusy(null);
    }
  }

  async function handleCancelAll() {
    if (!cancelAllConfirmed || adminBusy) return;
    if (reason.trim().length < 3) {
      notify("warning", "请输入至少 3 个字符的操作原因，该原因会写入审计日志");
      return;
    }
    setAdminBusy("cancelAll");
    try {
      const result = await tradeApi.cancelOpenOrders(session.csrf_token, reason.trim(), true);
      setCancelAllResult(result);
      setCancelAllConfirmed(false);
      notify(result.ok ? "success" : "warning", result.message);
      await data.refreshAll();
    } catch (error) {
      notify("error", error instanceof ApiError ? error.message : "批量撤单失败");
    } finally {
      setAdminBusy(null);
    }
  }

  async function handleLogout() {
    if (logoutBusy) return;
    setLogoutBusy(true);
    try {
      await onLogout();
    } finally {
      setLogoutBusy(false);
    }
  }

  return (
    <div className="ns-page">
      <PageHeader
        eyebrow="ACCOUNT / SETTINGS"
        title="设置"
        description="账户、交易环境、服务端限额与管理员控制。所有安全边界由 NEMT Cloud 强制执行。"
      />

      <div className="ns-settings-layout">
        <div className="ns-settings-main">
          <section className="ns-card">
            <CardHeader
              title="当前账户"
              hint="会话由 HttpOnly Cookie 管理"
              action={<span className="ns-data-source-pill"><StatusDot tone={online ? "ok" : "bad"} pulse={online} />{online ? "在线" : "离线"}</span>}
            />
            <div className="ns-settings-profile">
              <span className="ns-settings-avatar">{session.user.username.slice(0, 1).toUpperCase()}</span>
              <div className="ns-settings-profile-copy">
                <div>
                  <strong>{session.user.username}</strong>
                  <span className={cn("ns-mode", `ns-mode-${session.mode.toLowerCase()}`)}>
                    <span className="ns-mode-dot" />
                    {session.mode}
                  </span>
                </div>
                <p>{session.user.roles.join(" · ")}</p>
              </div>
            </div>
            <dl className="ns-detail-list ns-detail-list-divided">
              <div>
                <dt>会话到期</dt>
                <dd>{fmtTime(session.expires_at)}</dd>
              </div>
              <div>
                <dt>服务端版本</dt>
                <dd>NEMT Cloud API v{system?.version ?? "—"}</dd>
              </div>
              <div>
                <dt>服务器时间</dt>
                <dd>{system?.server_time ? fmtTime(system.server_time) : "—"}</dd>
              </div>
              <div>
                <dt>账户数据</dt>
                <dd>{balances?.source === "demo" ? "DEMO 模拟账本" : balances?.source ?? "未连接"}</dd>
              </div>
            </dl>
          </section>

          <section className="ns-card">
            <CardHeader
              title="交易环境与能力"
              hint="由服务端配置决定，前端无法切换"
            />
            <div className="ns-capability-grid">
              <Capability
                label="环境"
                value={session.mode === "DEMO" ? "DEMO 模拟" : session.mode === "TESTNET" ? "TESTNET" : "LIVE 实盘"}
                ok={session.mode !== "LIVE"}
              />
              <Capability
                label="行情"
                value={data.feedError ? "连接异常" : data.ticker ? `${data.ticker.source === "demo" ? "SIM" : "Binance"} · ${ageLabel(data.ticker.fetched_at)}` : "等待"}
                ok={Boolean(data.ticker) && online}
              />
              <Capability
                label="下单写入"
                value={system?.trading_enabled ? (paused ? "已暂停" : "已启用") : "未启用"}
                ok={Boolean(system?.trading_enabled) && !paused}
              />
              <Capability
                label="LIVE 写入"
                value={system?.live_trading_available ? "需审批" : "不可用"}
                ok={false}
              />
            </div>
            <p className="ns-settings-note">
              {session.mode === "DEMO"
                ? "DEMO 订单只写入本地模拟账本，不发送至 Binance。行情可能来自真实公共接口或确定性模拟数据。"
                : session.mode === "TESTNET"
                  ? "TESTNET 订单仅发往 Binance Spot Testnet，凭据存于服务端。测试网结果不代表真实盈利能力。"
                  : "LIVE 实盘写入未在 V0.1 开放，需要独立的审批与门禁流程。"}
            </p>
          </section>

          <section className="ns-card">
            <CardHeader
              title="服务端风险限额"
              hint="硬限制由后端执行，界面不可覆盖"
              action={<span className="ns-chip ns-chip-brand"><StudioIcon name="shield" size={12} />FAIL-CLOSED</span>}
            />
            {system ? (
              <div className="ns-limit-grid">
                <Limit label="单笔名义金额" value={`${system.limits.min_order_notional} – ${system.limits.max_order_notional} USDT`} />
                <Limit label="单日累计上限" value={`${system.limits.max_daily_notional} USDT`} />
                <Limit label="最大持仓估值" value={`${system.limits.max_position_notional} USDT`} />
                <Limit label="未完成订单上限" value={`${system.limits.max_open_orders} 笔`} />
                <Limit label="下单频率" value={`${system.limits.max_orders_per_minute} 笔 / 分钟`} />
                <Limit label="行情过期阈值" value={`${system.limits.market_stale_seconds} 秒`} />
              </div>
            ) : (
              <p className="ns-settings-note">正在同步服务端限额…</p>
            )}
          </section>

          {isAdmin ? (
            <section className="ns-card ns-admin-card">
              <CardHeader
                title="管理员控制"
                hint="RBAC: admin · 所有操作写入审计日志"
                action={<span className="ns-chip ns-chip-danger"><StudioIcon name="lock" size={12} />KILL SWITCH</span>}
              />
              <div className="ns-admin-status">
                <div>
                  <span className="ns-admin-status-label">全局新订单开关</span>
                  <span className={cn("ns-status-chip", paused ? "is-rejected" : "is-filled")}>
                    {paused ? "PAUSED" : "ACTIVE"}
                  </span>
                </div>
                {paused ? (
                  <p>
                    {system?.risk.pause_reason ?? "管理员暂停"} · {system?.risk.pause_updated_by ?? "system"}
                    {system?.risk.pause_updated_at ? ` · ${fmtTime(system.risk.pause_updated_at)}` : ""}
                  </p>
                ) : (
                  <p>暂停只阻止新订单，不会自动平仓，也不会撤销未完成订单。</p>
                )}
              </div>

              <label className="ns-field">
                <span className="ns-field-label">操作原因（写入审计日志）</span>
                <span className="ns-input-wrap">
                  <input
                    className="ns-input"
                    value={reason}
                    maxLength={200}
                    onChange={(event) => setReason(event.target.value)}
                    placeholder="例如：行情异常，人工暂停"
                  />
                </span>
              </label>

              <div className="ns-admin-actions">
                <button
                  type="button"
                  className={cn("ns-btn", paused ? "ns-btn-outline" : "ns-btn-danger")}
                  onClick={() => void handlePauseToggle()}
                  disabled={Boolean(adminBusy) || !system}
                >
                  <StudioIcon name={paused ? "play" : "pause"} size={14} />
                  {adminBusy === "pause" || adminBusy === "resume"
                    ? "正在执行…"
                    : paused
                      ? "恢复新订单"
                      : "暂停全部新订单"}
                </button>
              </div>

              <div className="ns-admin-danger-zone">
                <div>
                  <h3>紧急撤单</h3>
                  <p>
                    撤销全部 {orders?.open_count ?? 0} 笔未完成订单。该操作不可逆，只处理未成交部分。
                  </p>
                </div>
                <label className="ns-confirm-check">
                  <input
                    type="checkbox"
                    checked={cancelAllConfirmed}
                    onChange={(event) => setCancelAllConfirmed(event.target.checked)}
                    disabled={Boolean(adminBusy)}
                  />
                  <span>我确认撤销全部未完成订单，并理解不会清空已成交仓位。</span>
                </label>
                <button
                  type="button"
                  className="ns-btn ns-btn-danger"
                  onClick={() => void handleCancelAll()}
                  disabled={Boolean(adminBusy) || !cancelAllConfirmed || (orders?.open_count ?? 0) === 0}
                >
                  <StudioIcon name="close" size={14} />
                  {adminBusy === "cancelAll" ? "正在撤销…" : "撤销全部未完成订单"}
                </button>
                {cancelAllResult ? (
                  <p className="ns-settings-note">{cancelAllResult.message}</p>
                ) : null}
              </div>
            </section>
          ) : null}
        </div>

        <aside className="ns-settings-side">
          <section className="ns-card">
            <div className="ns-side-card-head">
              <h2 className="ns-card-title">安全边界</h2>
              <StudioIcon name="lock" size={16} />
            </div>
            <div className="ns-security-list">
              <SecurityRow title="HttpOnly 会话" body="浏览器脚本无法读取登录 Cookie。" />
              <SecurityRow title="CSRF 保护" body="下单、撤单与管理操作需要会话令牌。" />
              <SecurityRow title="服务端密钥" body="交易所 API Key 不进入浏览器或本地缓存。" />
              <SecurityRow title="一次性确认" body="订单预览签发短期确认令牌，提交后立即作废。" />
            </div>
          </section>

          <section className="ns-card">
            <div className="ns-side-card-head">
              <h2 className="ns-card-title">DEMO 账户</h2>
              <span className="ns-chip">模拟</span>
            </div>
            <dl className="ns-detail-list">
              <div>
                <dt>可用 USDT</dt>
                <dd className="ns-number">
                  {balances ? fmtUSDT(balances.balances.find((item) => item.asset === "USDT")?.free) : "—"}
                </dd>
              </div>
              <div>
                <dt>未完成订单</dt>
                <dd>{orders?.open_count ?? 0}</dd>
              </div>
              <div>
                <dt>账户模式</dt>
                <dd>{session.mode}</dd>
              </div>
            </dl>
            <button type="button" className="ns-btn ns-btn-outline ns-btn-block" onClick={() => navigate("portfolio")}>
              查看资产明细
              <StudioIcon name="chevronRight" size={13} />
            </button>
          </section>

          <div className="ns-settings-footer-actions">
            <button
              type="button"
              className="ns-btn ns-btn-outline ns-btn-block ns-btn-danger-text"
              onClick={() => void handleLogout()}
              disabled={logoutBusy}
            >
              <StudioIcon name="logout" size={15} />
              {logoutBusy ? "正在退出…" : "退出登录"}
            </button>
            <p>NEMT Studio V0.1 · 不构成投资建议</p>
          </div>
        </aside>
      </div>
    </div>
  );
}

function Capability({ label, value, ok }: { label: string; value: string; ok: boolean }) {
  return (
    <div className="ns-capability">
      <span className="ns-capability-label">{label}</span>
      <span className={cn("ns-capability-value", ok ? "is-ok" : "is-off")}>{value}</span>
    </div>
  );
}

function Limit({ label, value }: { label: string; value: string }) {
  return (
    <div className="ns-limit">
      <span>{label}</span>
      <strong className="ns-number">{value}</strong>
    </div>
  );
}

function SecurityRow({ title, body }: { title: string; body: string }) {
  return (
    <div className="ns-security-row">
      <span className="ns-security-check"><StudioIcon name="check" size={11} /></span>
      <div>
        <strong>{title}</strong>
        <p>{body}</p>
      </div>
    </div>
  );
}
