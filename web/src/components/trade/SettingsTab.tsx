"use client";

import Link from "next/link";
import { useState } from "react";
import { ApiError, tradeApi } from "@/lib/trade/api";
import { ageLabel, cn, fmtTime, fmtUSDT } from "@/lib/trade/format";
import type { CancelOpenOrdersResponse, Session } from "@/lib/trade/types";
import type { ToastKind, WorkspaceData } from "./workspace-shared";
import {
  BrandMark,
  Divider,
  Icon,
  KeyValue,
  ModeBadge,
  SectionHeader,
  Spinner,
  StatusDot,
} from "./ui";

export default function SettingsTab({
  session,
  data,
  notify,
  onLogout,
  refreshAll,
}: {
  session: Session;
  data: WorkspaceData;
  notify: (kind: ToastKind, message: string) => void;
  onLogout: () => void;
  refreshAll: () => Promise<void>;
}) {
  const { system, balances, orders, online } = data;
  const isAdmin = session.user.roles.includes("admin");
  const [reason, setReason] = useState("");
  const [adminBusy, setAdminBusy] = useState<"pause" | "resume" | "cancelAll" | null>(
    null
  );
  const [cancelAllConfirmed, setCancelAllConfirmed] = useState(false);
  const [cancelAllResult, setCancelAllResult] =
    useState<CancelOpenOrdersResponse | null>(null);
  const [logoutBusy, setLogoutBusy] = useState(false);
  const [standalone] = useState(
    () =>
      typeof window !== "undefined" &&
      window.matchMedia("(display-mode: standalone)").matches
  );

  async function handlePauseToggle() {
    if (!system || adminBusy) return;
    if (reason.trim().length < 3) {
      notify("warning", "请输入至少 3 个字符的操作原因（会写入审计日志）");
      return;
    }
    const paused = system.risk.pause_new_orders;
    setAdminBusy(paused ? "resume" : "pause");
    try {
      const state = paused
        ? await tradeApi.resumeOrders(session.csrf_token, reason.trim())
        : await tradeApi.pauseOrders(session.csrf_token, reason.trim());
      setReason("");
      notify(
        "success",
        state.pause_new_orders
          ? "已暂停全部新订单；已成交仓位不会被平掉"
          : "已恢复新订单（仍需逐单通过风控）"
      );
      await refreshAll();
    } catch (error) {
      notify(
        "error",
        error instanceof ApiError ? error.message : "管理员操作失败"
      );
    } finally {
      setAdminBusy(null);
    }
  }

  async function handleCancelAll() {
    if (!cancelAllConfirmed || adminBusy) return;
    if (reason.trim().length < 3) {
      notify("warning", "请输入至少 3 个字符的操作原因（会写入审计日志）");
      return;
    }
    setAdminBusy("cancelAll");
    try {
      const result = await tradeApi.cancelOpenOrders(
        session.csrf_token,
        reason.trim(),
        true
      );
      setCancelAllResult(result);
      setCancelAllConfirmed(false);
      notify(result.ok ? "success" : "warning", result.message);
      await refreshAll();
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
      await tradeApi.logout(session.csrf_token);
    } catch {
      // A local cookie clear still requires a page reload if the server is
      // unreachable; never pretend the server session was revoked.
    } finally {
      setLogoutBusy(false);
      onLogout();
    }
  }

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-[17px] font-semibold text-slate-100">设置</h1>
        <p className="text-[10px] text-slate-500 mt-0.5">
          账户、环境、风控与管理员控制
        </p>
      </div>

      <section className="trade-card p-4">
        <div className="flex items-center gap-3">
          <div className="w-11 h-11 rounded-2xl border border-cyan-300/20 bg-cyan-400/[0.07] flex items-center justify-center">
            <BrandMark size={26} />
          </div>
          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-2">
              <p className="text-[14px] font-semibold text-slate-100">
                {session.user.username}
              </p>
              <ModeBadge mode={session.mode} />
            </div>
            <p className="text-[10px] text-slate-500 mt-1">
              {session.user.roles.map((role) => (
                <span key={role} className="trade-chip !min-h-[18px] !text-[8px] mr-1">
                  {role}
                </span>
              ))}
            </p>
          </div>
          <StatusDot tone={online ? "ok" : "bad"} pulse={online} />
        </div>
        <Divider className="my-3" />
        <KeyValue label="会话到期" value={fmtTime(session.expires_at)} tone="muted" />
        <KeyValue
          label="服务端"
          value={`NEMT Cloud API v${system?.version ?? "—"}`}
          tone="muted"
        />
        <KeyValue
          label="服务器时间"
          value={system ? fmtTime(system.server_time) : "—"}
          tone="muted"
        />
      </section>

      <section className="hidden">
        <SectionHeader title="环境与能力" hint="由服务端配置决定，前端无法切换" />
        <div className="trade-card-flat p-4 space-y-3">
          <div className="flex items-start gap-3">
            <div className="w-8 h-8 rounded-lg bg-amber-400/[0.08] border border-amber-300/15 text-amber-300 flex items-center justify-center flex-none">
              <Icon name="info" size={14} />
            </div>
            <div>
              <p className="text-[11px] font-semibold text-slate-300">
                {session.mode === "DEMO"
                  ? "DEMO · 本地模拟"
                  : session.mode === "TESTNET"
                    ? "TESTNET · 模拟交易所"
                    : "LIVE · 只读评估"}
              </p>
              <p className="text-[10px] leading-relaxed text-slate-500 mt-1">
                {session.mode === "DEMO"
                  ? "订单进入本地模拟账本，不会发送到 Binance；行情可能来自真实公共接口或确定性回退数据。"
                  : session.mode === "TESTNET"
                    ? "订单只会发往 Binance Spot Testnet，凭据仅存服务端。模拟盘结果不代表真实盈利能力。"
                    : "V0.1 不提供 LIVE 下单路径；实盘需要 Issue #15 独立审批门禁。"}
              </p>
            </div>
          </div>
          <div className="grid grid-cols-3 gap-2 text-center">
            <CapabilityCell
              label="只读"
              value={balances?.connected ? "可用" : "未连接"}
              ok={Boolean(balances?.connected)}
            />
            <CapabilityCell
              label="下单"
              value={system?.trading_enabled ? "已启用" : "禁用"}
              ok={Boolean(system?.trading_enabled)}
            />
            <CapabilityCell
              label="LIVE 写入"
              value="不可用"
              ok={false}
            />
          </div>
        </div>
      </section>

      <section>
        <SectionHeader
          title="交易所账户"
          hint={balances ? `数据 ${ageLabel(balances.fetched_at)}` : "等待快照"}
          action={
            balances?.stale ? (
              <span className="trade-chip trade-chip-amber">STALE</span>
            ) : null
          }
        />
        <div className="trade-card-flat p-4">
          <div className="flex items-center justify-between gap-3">
            <div className="flex items-center gap-2">
              <StatusDot
                tone={balances?.connected ? "ok" : "bad"}
                pulse={Boolean(balances?.connected)}
              />
              <p className="text-[11px] font-semibold text-slate-300">
                {balances?.account_status ?? "UNKNOWN"}
              </p>
            </div>
            <span className="trade-chip">
              {balances?.source === "binance"
                ? "BINANCE READ-ONLY"
                : balances?.source === "demo"
                  ? "DEMO LEDGER"
                  : "NOT CONFIGURED"}
            </span>
          </div>
          <p className="text-[10px] leading-relaxed text-slate-500 mt-2">
            {balances?.note ?? "尚未获取账户说明。"}
          </p>
          {balances && balances.balances.length > 0 ? (
            <div className="mt-3 grid grid-cols-2 gap-2">
              {balances.balances
                .filter((item) => item.asset === "USDT" || item.asset === "BTC")
                .map((item) => (
                  <div key={item.asset} className="rounded-lg bg-black/20 px-2.5 py-2">
                    <p className="text-[9px] text-slate-600">{item.asset}</p>
                    <p className="trade-number text-[11px] text-slate-300 mt-0.5">
                      {item.free}
                    </p>
                    <p className="text-[8px] text-slate-600 mt-0.5">
                      冻结 {item.locked}
                    </p>
                  </div>
                ))}
            </div>
          ) : null}
          <p className="mt-3 text-[9px] leading-relaxed text-slate-600">
            Binance Key/Secret 只从服务端环境变量读取，不出现在浏览器、localStorage
            或日志中。账户查询使用只读接口；Testnet 下单需服务端显式开启。
          </p>
        </div>
      </section>

      <section className="hidden">
        <SectionHeader title="风险限额" hint="硬限制由后端执行，移动端不可修改" />
        <div className="trade-card-flat p-4">
          {system ? (
            <>
              <KeyValue
                label="单笔名义金额"
                value={`${system.limits.min_order_notional} – ${system.limits.max_order_notional} USDT`}
              />
              <KeyValue label="单日累计上限" value={`${system.limits.max_daily_notional} USDT`} />
              <KeyValue label="最大持仓估值" value={`${system.limits.max_position_notional} USDT`} />
              <KeyValue label="未完成订单上限" value={`${system.limits.max_open_orders} 笔`} />
              <KeyValue label="下单频率" value={`${system.limits.max_orders_per_minute} 笔 / 分钟`} />
              <KeyValue
                label="行情过期阈值"
                value={`${system.limits.market_stale_seconds} 秒`}
              />
              <KeyValue
                label="账户过期阈值"
                value={`${system.limits.account_stale_seconds} 秒`}
              />
              <Divider className="my-2" />
              <div className="flex items-center justify-between">
                <span className="text-[10px] text-slate-500">当前暂停新订单</span>
                <span
                  className={cn(
                    "trade-chip",
                    system.risk.pause_new_orders
                      ? "trade-chip-danger"
                      : "trade-chip-cyan text-emerald-300 border-emerald-400/25 bg-emerald-400/10"
                  )}
                >
                  {system.risk.pause_new_orders ? "PAUSED" : "ACTIVE"}
                </span>
              </div>
              {system.risk.pause_new_orders ? (
                <p className="text-[9px] leading-relaxed text-rose-200/55 mt-2">
                  {system.risk.pause_reason} · {system.risk.pause_updated_by} ·{" "}
                  {fmtTime(system.risk.pause_updated_at)}
                </p>
              ) : null}
            </>
          ) : (
            <p className="text-[11px] text-slate-500">加载中…</p>
          )}
        </div>
      </section>

      {isAdmin ? (
        <section>
          <SectionHeader
            title="管理员控制"
            hint="RBAC: admin · 所有操作写入审计"
            action={<span className="trade-chip trade-chip-danger">KILL SWITCH</span>}
          />
          <div className="trade-card border-rose-400/15 p-4">
            <div className="flex items-start gap-3">
              <div className="w-8 h-8 rounded-lg bg-rose-400/[0.08] border border-rose-400/20 text-rose-300 flex items-center justify-center flex-none">
                <Icon name="pause" size={14} />
              </div>
              <div className="min-w-0">
                <p className="text-[11px] font-semibold text-slate-300">全局新订单开关</p>
                <p className="text-[10px] leading-relaxed text-slate-500 mt-1">
                  暂停只阻止新订单；不会自动平掉已成交仓位，也不会撤销未完成订单。
                </p>
              </div>
            </div>

            <label className="block mt-3">
              <span className="text-[10px] text-slate-500">操作原因（写入审计）</span>
              <input
                className="trade-input !min-h-[44px] mt-1.5 !text-[13px]"
                value={reason}
                onChange={(event) => setReason(event.target.value)}
                placeholder="例如：发现行情异常，人工暂停"
                maxLength={200}
              />
            </label>

            <button
              type="button"
              onClick={() => void handlePauseToggle()}
              disabled={Boolean(adminBusy) || !system}
              className={cn(
                "trade-btn w-full mt-2.5",
                system?.risk.pause_new_orders
                  ? "trade-btn-outline"
                  : "trade-btn-danger"
              )}
            >
              {adminBusy === "pause" || adminBusy === "resume" ? (
                <Spinner size={14} />
              ) : (
                <Icon name={system?.risk.pause_new_orders ? "play" : "pause"} size={14} />
              )}
              {system?.risk.pause_new_orders ? "恢复新订单" : "暂停全部新订单"}
            </button>

            <Divider className="my-4" />

            <p className="text-[10px] leading-relaxed text-slate-500">
              紧急撤销全部未完成订单（{orders?.open_count ?? 0} 笔）。该操作不可逆，
              只处理未成交部分；已成交仓位保持原样。
            </p>
            <label className="mt-2.5 flex items-start gap-2.5 cursor-pointer">
              <input
                type="checkbox"
                checked={cancelAllConfirmed}
                onChange={(event) => setCancelAllConfirmed(event.target.checked)}
                className="mt-0.5 h-4 w-4 accent-rose-400"
                disabled={Boolean(adminBusy)}
              />
              <span className="text-[10px] leading-relaxed text-slate-500">
                我确认撤销全部未完成订单，并理解不会清空已成交仓位。
              </span>
            </label>
            <button
              type="button"
              onClick={() => void handleCancelAll()}
              disabled={
                Boolean(adminBusy) ||
                !cancelAllConfirmed ||
                (orders?.open_count ?? 0) === 0
              }
              className="trade-btn trade-btn-outline w-full mt-2.5 !border-rose-400/25 !text-rose-300"
            >
              {adminBusy === "cancelAll" ? <Spinner size={14} /> : <Icon name="close" size={14} />}
              撤销全部未完成订单
            </button>

            {cancelAllResult ? (
              <div
                className={cn(
                  "mt-3 rounded-xl border px-3 py-2.5 text-[10px] leading-relaxed",
                  cancelAllResult.ok
                    ? "border-emerald-400/20 bg-emerald-400/[0.05] text-emerald-200/70"
                    : "border-rose-400/20 bg-rose-400/[0.05] text-rose-200/70"
                )}
              >
                {cancelAllResult.message}
                {cancelAllResult.failed.length > 0 ? (
                  <ul className="mt-1 space-y-0.5">
                    {cancelAllResult.failed.map((failure) => (
                      <li key={failure.order_id}>
                        {failure.order_id} · {failure.code}: {failure.message}
                      </li>
                    ))}
                  </ul>
                ) : null}
              </div>
            ) : null}

            <p className="text-[9px] leading-relaxed text-slate-600 mt-3">
              V0.1 管理操作要求 admin 会话 + CSRF + 明确原因；MFA/双人复核尚未实现。
            </p>
          </div>
        </section>
      ) : null}

      <section className="hidden">
        <SectionHeader title="安装与隐私" />
        <div className="trade-card-flat p-4 space-y-3">
          <div className="flex items-start gap-3">
            <div className="w-8 h-8 rounded-lg bg-cyan-400/[0.07] border border-cyan-300/15 text-cyan-300 flex items-center justify-center flex-none">
              <Icon name="download" size={14} />
            </div>
            <div>
              <p className="text-[11px] font-semibold text-slate-300">
                {standalone ? "已作为独立应用运行" : "安装到主屏幕"}
              </p>
              <p className="text-[10px] leading-relaxed text-slate-500 mt-1">
                {standalone
                  ? "当前为 standalone 模式，可使用离线说明页，但下单始终需要实时服务端。"
                  : "Android Chrome 菜单 → 添加到主屏幕 / 安装应用。离线可查看说明页，但不会缓存 API 或排队交易。"}
              </p>
            </div>
          </div>
          <Divider />
          <div className="flex items-start gap-3">
            <div className="w-8 h-8 rounded-lg bg-emerald-400/[0.06] border border-emerald-400/15 text-emerald-300 flex items-center justify-center flex-none">
              <Icon name="shield" size={14} />
            </div>
            <div>
              <p className="text-[11px] font-semibold text-slate-300">安全边界</p>
              <p className="text-[10px] leading-relaxed text-slate-500 mt-1">
                会话 Cookie 为 HttpOnly；写操作需要 CSRF 令牌；Service Worker
                永不缓存 /api 响应；浏览器不接触任何交易所密钥。
              </p>
            </div>
          </div>
        </div>
      </section>

      <section className="space-y-2">
        <Link
          href="/"
          className="trade-btn trade-btn-outline w-full !justify-between !px-4"
        >
          <span className="flex items-center gap-2">
            <BrandMark size={16} />
            返回 NEMT 研究终端
          </span>
          <Icon name="external" size={13} />
        </Link>
        <button
          type="button"
          onClick={() => void handleLogout()}
          disabled={logoutBusy}
          className="trade-btn trade-btn-outline w-full !justify-between !px-4 !text-rose-300"
        >
          <span className="flex items-center gap-2">
            {logoutBusy ? <Spinner size={14} /> : <Icon name="logout" size={14} />}
            {logoutBusy ? "正在切换…" : "切换账户"}
          </span>
          <Icon name="chevronRight" size={13} />
        </button>
      </section>

      <div className="hidden">
        NEMT App V0.1 · {system?.mode ?? session.mode} · 不构成投资建议
        <br />
        总资产/估值仅用于界面展示，不代表真实盈亏或可提取资金
        {balances?.source === "demo"
          ? ` · 模拟余额 ${fmtUSDT(
              balances.balances.find((item) => item.asset === "USDT")?.total
            )} USDT`
          : ""}
      </div>
    </div>
  );
}

function CapabilityCell({
  label,
  value,
  ok,
}: {
  label: string;
  value: string;
  ok: boolean;
}) {
  return (
    <div className="rounded-lg bg-black/20 py-2">
      <p className="text-[9px] text-slate-600">{label}</p>
      <p
        className={cn(
          "text-[10px] font-semibold mt-0.5",
          ok ? "text-emerald-300" : "text-slate-500"
        )}
      >
        {value}
      </p>
    </div>
  );
}
