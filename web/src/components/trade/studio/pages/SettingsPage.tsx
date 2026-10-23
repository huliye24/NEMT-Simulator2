"use client";

import { useState, type ReactNode } from "react";
import { ApiError, tradeApi } from "@/lib/trade/api";
import { ageLabel, cn, fmtTime } from "@/lib/trade/format";
import type { CancelOpenOrdersResponse } from "@/lib/trade/types";
import { EmptyState, StatusDot } from "../common";
import {
  EditorialPage,
  Masthead,
  StatusTag,
} from "../editorial/Editorial";
import { StudioIcon, type StudioIconName } from "../icons";
import { buildSystemStatus, SystemStatusDetails } from "../layout/SystemStatus";
import type { StudioPageProps } from "../types";

interface SettingsPageProps extends StudioPageProps {
  sidebarCollapsed: boolean;
  onToggleSidebar: () => void;
  onLogout: () => Promise<void>;
}

const SETTINGS_SECTIONS: {
  id: "account" | "environment" | "connections" | "risk" | "preferences" | "about";
  label: string;
  labelEn: string;
  icon: StudioIconName;
}[] = [
  { id: "account", label: "账户", labelEn: "Account", icon: "overview" },
  { id: "environment", label: "环境", labelEn: "Environment", icon: "database" },
  { id: "connections", label: "连接", labelEn: "Connections", icon: "activity" },
  { id: "risk", label: "风控与权限", labelEn: "Risk & Permissions", icon: "shield" },
  { id: "preferences", label: "偏好", labelEn: "Preferences", icon: "sliders" },
  { id: "about", label: "关于", labelEn: "About", icon: "info" },
];

type SettingsSectionId = (typeof SETTINGS_SECTIONS)[number]["id"];

export default function SettingsPage({
  session,
  data,
  notify,
  sidebarCollapsed,
  onToggleSidebar,
  onLogout,
}: SettingsPageProps) {
  const { system, balances, orders, online } = data;
  const [section, setSection] = useState<SettingsSectionId>("account");
  const [reason, setReason] = useState("");
  const [adminBusy, setAdminBusy] = useState<"pause" | "resume" | "cancelAll" | null>(null);
  const [cancelAllConfirmed, setCancelAllConfirmed] = useState(false);
  const [cancelAllResult, setCancelAllResult] = useState<CancelOpenOrdersResponse | null>(null);
  const [logoutBusy, setLogoutBusy] = useState(false);
  const isAdmin = session.user.roles.includes("admin");
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

  const status = buildSystemStatus(data, session.mode);

  return (
    <EditorialPage className="nsx-settings">
      <Masthead
        compact
        kicker="ACCOUNT / SETTINGS · 07"
        title="设置"
        accent="Clarity at the system boundary."
        lead="账户、环境、连接、风控权限与界面偏好。服务端安全边界不可由前端覆盖。"
        issue={{ label: "SETTINGS", value: "07", note: "SYSTEM BOUNDARIES" }}
        actions={
          <>
            <StatusTag tone={online ? "ok" : "bad"}>
              {online ? "Online" : "Offline"}
            </StatusTag>
            <StatusTag tone="brand">{session.mode}</StatusTag>
          </>
        }
      />

      <div className="ns-settings-shell">
        <nav className="ns-settings-nav" aria-label="设置分类">
          {SETTINGS_SECTIONS.map((item) => (
            <button
              key={item.id}
              type="button"
              className={cn("ns-settings-nav-item", section === item.id && "is-active")}
              onClick={() => setSection(item.id)}
              aria-current={section === item.id ? "page" : undefined}
            >
              <StudioIcon name={item.icon} size={16} />
              <span>
                {item.label}
                <em>{item.labelEn}</em>
              </span>
              <StudioIcon name="chevronRight" size={13} />
            </button>
          ))}
        </nav>

        <div className="ns-settings-content">
          {section === "account" ? (
            <section className="ns-card ns-settings-panel">
              <SettingsHead
                title="Account"
                hint="会话由 HttpOnly Cookie 管理"
                chip={
                  <span className="ns-data-source-pill">
                    <StatusDot tone={online ? "ok" : "bad"} pulse={online} />
                    {online ? "Online" : "Offline"}
                  </span>
                }
              />
              <div className="ns-settings-profile">
                <span className="ns-settings-avatar">
                  {session.user.username.slice(0, 1).toUpperCase()}
                </span>
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
                <button
                  type="button"
                  className="ns-btn ns-btn-outline ns-btn-sm ns-btn-danger-text"
                  onClick={() => void handleLogout()}
                  disabled={logoutBusy}
                >
                  <StudioIcon name="logout" size={14} />
                  {logoutBusy ? "正在退出…" : "退出登录"}
                </button>
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
          ) : null}

          {section === "environment" ? (
            <section className="ns-card ns-settings-panel">
              <SettingsHead
                title="Environment"
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
                  value={
                    data.feedError
                      ? "连接异常"
                      : data.ticker
                        ? `${data.ticker.source === "demo" ? "SIM" : "Binance"} · ${ageLabel(data.ticker.fetched_at)}`
                        : "等待"
                  }
                  ok={Boolean(data.ticker) && online}
                />
                <Capability
                  label="订单写入"
                  value={system?.trading_enabled ? (paused ? "已暂停" : "DEMO 已启用") : "未启用"}
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
                  ? "DEMO 订单只写入本地模拟账本，不发送至 Binance。Studio 主工作台不提供人工下单。"
                  : session.mode === "TESTNET"
                    ? "TESTNET 订单仅发往 Binance Spot Testnet，凭据存于服务端。测试结果不代表真实盈利能力。"
                    : "LIVE 实盘写入未开放，需要独立审批、授权与执行服务。"}
              </p>
            </section>
          ) : null}

          {section === "connections" ? (
            <section className="ns-card ns-settings-panel">
              <SettingsHead
                title="Connections"
                hint="全局唯一完整状态视图；Topbar 状态点提供同一信息"
                chip={
                  <span className={cn("ns-status-pill", `is-${status.tone}`)}>
                    <StatusDot tone={status.tone} pulse={status.tone === "ok"} />
                    {status.label}
                  </span>
                }
              />
              <SystemStatusDetails model={status} className="ns-settings-status" />
            </section>
          ) : null}

          {section === "risk" ? (
            <div className="ns-settings-stack">
              <section className="ns-card ns-settings-panel">
                <SettingsHead
                  title="Server Risk Limits"
                  hint="硬限制由后端执行，界面不可覆盖"
                  chip={
                    <span className="ns-chip ns-chip-brand">
                      <StudioIcon name="shield" size={12} />
                      FAIL-CLOSED
                    </span>
                  }
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
                <p className="ns-settings-note">
                  这些限额属于服务端订单守护。策略级风险审批与执行服务仍为 Not Connected。
                </p>
              </section>

              {isAdmin ? (
                <section className="ns-card ns-settings-panel ns-admin-card">
                  <SettingsHead
                    title="Admin Controls"
                    hint="RBAC: admin · 所有操作写入审计日志"
                    chip={
                      <span className="ns-chip ns-chip-danger">
                        <StudioIcon name="lock" size={12} />
                        KILL SWITCH
                      </span>
                    }
                  />
                  <div className="ns-admin-status">
                    <div>
                      <span className="ns-admin-status-label">全局新订单开关</span>
                      <span className={cn("ns-status-chip", paused ? "is-rejected" : "is-filled")}>
                        {paused ? "PAUSED" : "ACTIVE"}
                      </span>
                    </div>
                    <p>
                      {paused
                        ? `${system?.risk.pause_reason ?? "管理员暂停"} · ${
                            system?.risk.pause_updated_by ?? "system"
                          }${
                            system?.risk.pause_updated_at
                              ? ` · ${fmtTime(system.risk.pause_updated_at)}`
                              : ""
                          }`
                        : "暂停只阻止新订单，不会自动平仓，也不会撤销未完成订单。"}
                    </p>
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
              ) : (
                <section className="ns-card ns-settings-panel">
                  <EmptyState
                    compact
                    icon="lock"
                    title="当前账户没有管理员权限"
                    body="管理员暂停与紧急撤单仅对 admin 角色开放，服务端会再次校验权限。"
                  />
                </section>
              )}
            </div>
          ) : null}

          {section === "preferences" ? (
            <section className="ns-card ns-settings-panel">
              <SettingsHead
                title="Preferences"
                hint="界面偏好仅保存在本机浏览器"
              />
              <div className="ns-pref-row">
                <div>
                  <strong>侧边栏收起</strong>
                  <p>切换桌面端侧边栏状态；下次打开 Studio 时沿用该设置。</p>
                </div>
                <button
                  type="button"
                  role="switch"
                  aria-checked={sidebarCollapsed}
                  className={cn("ns-switch", sidebarCollapsed && "is-on")}
                  onClick={onToggleSidebar}
                >
                  <span />
                </button>
              </div>
              <div className="ns-pref-row">
                <div>
                  <strong>导航语言</strong>
                  <p>中文导航，保留英文业务副标题。</p>
                </div>
                <span className="ns-chip">简体中文 · 固定</span>
              </div>
              <div className="ns-pref-row">
                <div>
                  <strong>数据刷新</strong>
                  <p>行情 5 秒、账户与订单 15 秒由工作台统一管理。</p>
                </div>
                <span className="ns-chip">System managed</span>
              </div>
              <p className="ns-settings-note">
                不在此处保存 API Secret、交易密钥或策略参数；敏感凭据始终留在服务端。
              </p>
            </section>
          ) : null}

          {section === "about" ? (
            <section className="ns-card ns-settings-panel">
              <SettingsHead
                title="NEMT Studio"
                hint="Research-driven, strategy-first quantitative investment workspace"
                chip={<span className="ns-chip ns-chip-brand">V3.1 Studio</span>}
              />
              <dl className="ns-detail-list ns-detail-list-divided">
                <div>
                  <dt>API 版本</dt>
                  <dd>v{system?.version ?? "—"}</dd>
                </div>
                <div>
                  <dt>环境</dt>
                  <dd>{session.mode}</dd>
                </div>
                <div>
                  <dt>执行服务</dt>
                  <dd>Not Connected</dd>
                </div>
                <div>
                  <dt>构建</dt>
                  <dd>V3.1 · Editorial research system</dd>
                </div>
              </dl>
              <div className="ns-about-principles">
                <span>Research discovers.</span>
                <span>Experiments validate.</span>
                <span>Strategies decide.</span>
                <span>Execution acts.</span>
                <span>Risk controls.</span>
                <span>Portfolio measures.</span>
              </div>
              <p className="ns-settings-note">
                NEMT Studio 不构成投资建议。DEMO 数据不代表真实收益；LIVE
                交易未开放，所有关键风控由服务端强制执行。
              </p>
            </section>
          ) : null}
        </div>
      </div>
    </EditorialPage>
  );
}

function SettingsHead({
  title,
  hint,
  chip,
}: {
  title: string;
  hint: string;
  chip?: ReactNode;
}) {
  return (
    <div className="ns-settings-head">
      <div>
        <h2>{title}</h2>
        <p>{hint}</p>
      </div>
      {chip ? <div className="ns-settings-head-chip">{chip}</div> : null}
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
