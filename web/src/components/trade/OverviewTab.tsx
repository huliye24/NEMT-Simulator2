"use client";

import type { WorkspaceData } from "./workspace-shared";
import { ORDER_STATUS_LABEL, orderStatusChip } from "@/lib/trade/order-status";
import {
  ageLabel,
  cn,
  fmtCompact,
  fmtPrice,
  fmtQty,
  fmtTime,
  fmtUSDT,
  isoToClock,
} from "@/lib/trade/format";
import type { Order, TradeTabKey } from "@/lib/trade/types";
import {
  Divider,
  Icon,
  ModeBadge,
  SectionHeader,
  SourceBadge,
  Spinner,
  StatusDot,
  type Tone,
} from "./ui";

interface OverviewProps {
  data: WorkspaceData;
  onNavigate: (tab: TradeTabKey) => void;
}

function findBalance(data: WorkspaceData, asset: string): { free: number; locked: number } {
  const balance = data.balances?.balances.find((item) => item.asset === asset);
  return {
    free: Number(balance?.free ?? 0),
    locked: Number(balance?.locked ?? 0),
  };
}

function statusTone(ok: boolean, degraded = false): Tone {
  if (ok) return "ok";
  return degraded ? "warn" : "bad";
}

export default function OverviewTab({ data, onNavigate }: OverviewProps) {
  const { system, ticker, balances, orders, online, feedError } = data;
  const usdt = findBalance(data, "USDT");
  const btc = findBalance(data, "BTC");
  const lastPrice = Number(ticker?.last_price ?? 0);
  const estimatedValue = usdt.free + usdt.locked + (btc.free + btc.locked) * lastPrice;
  const change = Number(ticker?.price_change_percent ?? 0);
  const positive = change >= 0;
  const flags = system?.flags ?? {};
  const paused = Boolean(system?.risk.pause_new_orders);
  const feedStale = Boolean(ticker?.stale) || !online;
  const recentOrders = orders?.orders.slice(0, 3) ?? [];

  if (!system || !ticker) {
    return <OverviewSkeleton />;
  }

  const statuses: { label: string; ok: boolean; tone: Tone; note: string }[] = [
    {
      label: "服务端",
      ok: Boolean(flags.server_ok),
      tone: statusTone(Boolean(flags.server_ok)),
      note: "NEMT Cloud API",
    },
    {
      label: "登录",
      ok: Boolean(flags.authenticated),
      tone: statusTone(Boolean(flags.authenticated)),
      note: system.user.username,
    },
    {
      label: "行情",
      ok: Boolean(flags.market_fresh) && online,
      tone: statusTone(Boolean(flags.market_fresh) && online, Boolean(flags.market_fresh)),
      note: ticker.source === "demo" ? "SIM" : "Binance",
    },
    {
      label: "账户",
      ok: Boolean(flags.account_connected),
      tone: statusTone(
        Boolean(flags.account_connected),
        balances?.account_status === "NOT_CONFIGURED"
      ),
      note: balances?.source === "demo" ? "模拟账本" : "交易所",
    },
    {
      label: "交易",
      ok: Boolean(flags.trading_enabled) && !paused,
      tone: paused ? "bad" : statusTone(Boolean(flags.trading_enabled), true),
      note: paused ? "已暂停" : system.mode === "LIVE" ? "未开放" : "仅限本环境",
    },
  ];

  return (
    <div className="space-y-4">
      {system.mode === "DEMO" ? (
        <div className="flex items-center gap-2.5 rounded-xl border border-amber-300/15 bg-amber-300/[0.05] px-3.5 py-2.5">
          <Icon name="info" size={15} className="text-amber-300/80 flex-none" />
          <p className="text-[11px] leading-relaxed text-amber-100/65">
            DEMO 演示环境 · 本地模拟账本 · 订单不会发送到任何交易所
          </p>
        </div>
      ) : null}

      {paused ? (
        <div className="rounded-xl border border-rose-400/25 bg-rose-400/[0.07] px-3.5 py-3">
          <div className="flex items-center gap-2 text-[12px] font-semibold text-rose-200">
            <Icon name="pause" size={14} />
            全局暂停新订单已启用
          </div>
          <p className="mt-1 text-[11px] leading-relaxed text-rose-200/60">
            {system.risk.pause_reason ?? "管理员已暂停新订单"} ·{" "}
            {system.risk.pause_updated_by ?? "system"} · {fmtTime(system.risk.pause_updated_at)}
          </p>
          <p className="mt-1 text-[10px] text-rose-200/40">
            暂停只阻止新订单，不会自动平掉已成交仓位。
          </p>
        </div>
      ) : null}

      {feedStale || feedError ? (
        <div className="rounded-xl border border-amber-300/20 bg-amber-300/[0.06] px-3.5 py-2.5">
          <div className="flex items-center gap-2 text-[11px] font-semibold text-amber-200">
            <Icon name="wifiOff" size={14} />
            {!online ? "设备已离线" : ticker.stale ? "行情已过期" : "行情连接异常"}
          </div>
          <p className="mt-0.5 text-[10px] text-amber-100/45">
            {feedError ?? "为避免错误成交，新订单已禁用；恢复后状态会自动刷新。"}
          </p>
        </div>
      ) : null}

      {/* Price hero */}
      <section className="trade-card trade-card-accent overflow-hidden">
        <div className="trade-glass-highlight p-4">
          <div className="flex items-center justify-between gap-3">
            <div className="flex items-center gap-2">
              <div className="w-7 h-7 rounded-full bg-gradient-to-br from-amber-300 to-amber-600 text-[11px] font-black text-amber-950 flex items-center justify-center">
                ₿
              </div>
              <div>
                <p className="text-[13px] font-semibold tracking-wide text-slate-200">
                  BTC<span className="text-slate-500">/USDT</span>
                </p>
                <p className="text-[10px] text-slate-500">Spot · Binance</p>
              </div>
            </div>
            <SourceBadge source={ticker.source} stale={ticker.stale} />
          </div>

          <div className="mt-4 flex items-end justify-between gap-3">
            <div className="min-w-0">
              <p className="trade-number text-[34px] leading-none font-semibold tracking-[-0.04em] text-slate-50">
                {fmtPrice(ticker.last_price)}
              </p>
              <div className="mt-2 flex items-center gap-2">
                <span
                  className={cn(
                    "trade-number text-[12px] font-semibold",
                    positive ? "trade-up" : "trade-down"
                  )}
                >
                  {positive ? "+" : ""}
                  {fmtPrice(ticker.price_change)} ({positive ? "+" : ""}
                  {Number(ticker.price_change_percent).toFixed(2)}%)
                </span>
                <span className="text-[10px] text-slate-600">24H</span>
              </div>
            </div>
            <div className="text-right flex-none">
              <p className="text-[10px] uppercase tracking-wider text-slate-600">Feed age</p>
              <p className="trade-number text-[12px] text-slate-400 mt-0.5">
                {ageLabel(ticker.fetched_at)}
              </p>
            </div>
          </div>

          <div className="mt-4 grid grid-cols-3 gap-2">
            <MiniStat label="24H 高" value={fmtPrice(ticker.high_price)} />
            <MiniStat label="24H 低" value={fmtPrice(ticker.low_price)} />
            <MiniStat label="24H 量" value={fmtCompact(ticker.volume)} suffix="BTC" />
          </div>
        </div>

        <div className="grid grid-cols-5 border-t border-white/[0.06]">
          {statuses.map((item) => (
            <div
              key={item.label}
              className="flex flex-col items-center gap-1.5 py-3 border-r border-white/[0.04] last:border-r-0"
            >
              <div className="flex items-center gap-1.5">
                <StatusDot tone={item.tone} pulse={item.ok} />
                <span className="text-[10px] font-medium text-slate-400">{item.label}</span>
              </div>
              <span className={cn("text-[9px]", item.ok ? "text-slate-600" : "text-rose-300/70")}>
                {item.note}
              </span>
            </div>
          ))}
        </div>
      </section>

      {/* Portfolio snapshot */}
      <section>
        <SectionHeader
          title="账户余额"
          hint={
            balances
              ? `${balances.source === "demo" ? "DEMO 账本" : "Binance"} · ${ageLabel(
                  balances.fetched_at
                )}`
              : "等待账户快照"
          }
          action={
            balances?.stale ? (
              <span className="trade-chip trade-chip-amber">STALE</span>
            ) : null
          }
        />
        <div className="grid grid-cols-2 gap-3">
          <div className="trade-card p-3.5">
            <p className="text-[10px] uppercase tracking-wider text-slate-500">可用 USDT</p>
            <p className="trade-number text-[19px] font-semibold text-slate-100 mt-1.5">
              {fmtUSDT(usdt.free)}
            </p>
            <p className="text-[10px] text-slate-600 mt-1">
              冻结 {fmtUSDT(usdt.locked)} USDT
            </p>
          </div>
          <div className="trade-card p-3.5">
            <p className="text-[10px] uppercase tracking-wider text-slate-500">可用 BTC</p>
            <p className="trade-number text-[19px] font-semibold text-slate-100 mt-1.5">
              {fmtQty(btc.free)}
            </p>
            <p className="text-[10px] text-slate-600 mt-1">
              冻结 {fmtQty(btc.locked)} BTC
            </p>
          </div>
        </div>
        <div className="trade-card-flat mt-2.5 px-3.5 py-2.5 flex items-center justify-between">
          <span className="text-[10px] text-slate-500">
            组合估值（非盈亏）
          </span>
          <span className="trade-number text-[12px] text-slate-300">
            ≈ {fmtUSDT(estimatedValue)} USDT
          </span>
        </div>
      </section>

      {/* Quick actions */}
      <section className="grid grid-cols-3 gap-2.5">
        <QuickAction
          icon="market"
          label="行情"
          hint="K 线与 24H"
          onClick={() => onNavigate("market")}
        />
        <QuickAction
          icon="trade"
          label="下单"
          hint={paused || !flags.trading_enabled ? "当前禁用" : "预览后确认"}
          onClick={() => onNavigate("trade")}
          disabled={!flags.trading_enabled || paused}
        />
        <QuickAction
          icon="orders"
          label="订单"
          hint={orders ? `${orders.open_count} 笔未完成` : "查看状态"}
          onClick={() => onNavigate("orders")}
        />
      </section>

      {/* Recent orders */}
      <section>
        <SectionHeader
          title="最近订单"
          hint={orders ? `${orders.count} 条记录` : "—"}
          action={
            <button
              type="button"
              onClick={() => onNavigate("orders")}
              className="text-[11px] text-cyan-300/80 font-medium"
            >
              全部 →
            </button>
          }
        />
        <div className="trade-card overflow-hidden">
          {recentOrders.length === 0 ? (
            <div className="px-4 py-7 text-center">
              <p className="text-[12px] text-slate-500">还没有订单</p>
              <p className="text-[10px] text-slate-600 mt-1">
                在 DEMO 环境先试一笔小额市价单，确认完整流程。
              </p>
            </div>
          ) : (
            recentOrders.map((order, index) => (
              <RecentOrderRow key={order.id} order={order} showDivider={index > 0} />
            ))
          )}
        </div>
      </section>

      {/* Risk limits */}
      <section className="trade-card-flat p-3.5">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Icon name="shield" size={14} className="text-cyan-400/70" />
            <span className="text-[11px] font-semibold text-slate-300">服务端风控限额</span>
          </div>
          <span className="trade-chip trade-chip-cyan">FAIL-CLOSED</span>
        </div>
        <div className="mt-2.5 grid grid-cols-3 gap-2 text-center">
          <LimitsCell label="单笔上限" value={`${system.limits.max_order_notional} U`} />
          <LimitsCell label="当日上限" value={`${system.limits.max_daily_notional} U`} />
          <LimitsCell label="未完成单" value={`${system.limits.max_open_orders}`} />
        </div>
      </section>

      <div className="flex items-center justify-between px-1 pt-1 pb-2 text-[10px] text-slate-600">
        <div className="flex items-center gap-2">
          <ModeBadge mode={system.mode} />
          <span>v{system.version}</span>
        </div>
        <div className="flex items-center gap-1.5">
          <Icon name="clock" size={11} />
          <span>数据 {ageLabel(ticker.fetched_at)}</span>
          <span>·</span>
          <span className="trade-number">{isoToClock(system.server_time)}</span>
        </div>
      </div>
    </div>
  );
}

function MiniStat({
  label,
  value,
  suffix,
}: {
  label: string;
  value: string;
  suffix?: string;
}) {
  return (
    <div className="rounded-lg bg-black/20 px-2.5 py-2">
      <p className="text-[9px] uppercase tracking-wider text-slate-600">{label}</p>
      <p className="trade-number text-[11px] text-slate-400 mt-0.5 truncate">
        {value}
        {suffix ? <span className="text-slate-600"> {suffix}</span> : null}
      </p>
    </div>
  );
}

function LimitsCell({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg bg-black/20 py-2">
      <p className="text-[9px] text-slate-600">{label}</p>
      <p className="trade-number text-[11px] text-slate-300 mt-0.5">{value}</p>
    </div>
  );
}

function QuickAction({
  icon,
  label,
  hint,
  onClick,
  disabled,
}: {
  icon: "market" | "trade" | "orders";
  label: string;
  hint: string;
  onClick: () => void;
  disabled?: boolean;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      className={cn(
        "trade-card flex flex-col items-start p-3 text-left transition-colors",
        disabled ? "opacity-50" : "hover:border-cyan-300/25 active:bg-white/[0.02]"
      )}
    >
      <span className="w-8 h-8 rounded-xl bg-cyan-400/10 border border-cyan-300/15 text-cyan-300 flex items-center justify-center">
        <Icon name={icon} size={15} />
      </span>
      <span className="text-[12px] font-semibold text-slate-200 mt-2.5">{label}</span>
      <span className="text-[9px] text-slate-600 mt-0.5">{hint}</span>
    </button>
  );
}

function RecentOrderRow({ order, showDivider }: { order: Order; showDivider: boolean }) {
  const isBuy = order.side === "BUY";
  return (
    <>
      {showDivider ? <Divider /> : null}
      <div className="flex items-center gap-3 px-3.5 py-3">
        <span
          className={cn(
            "w-8 h-8 rounded-lg flex items-center justify-center text-[12px] font-bold",
            isBuy
              ? "bg-emerald-400/10 text-emerald-300"
              : "bg-rose-400/10 text-rose-300"
          )}
        >
          {isBuy ? "买" : "卖"}
        </span>
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <span className="text-[12px] font-semibold text-slate-200">
              {order.symbol}
            </span>
            <span className="text-[9px] uppercase text-slate-600">{order.type}</span>
          </div>
          <p className="trade-number text-[10px] text-slate-500 mt-0.5 truncate">
            {fmtQty(order.filled_qty)} / {fmtQty(order.quantity)} @{" "}
            {order.avg_fill_price ? fmtPrice(order.avg_fill_price) : order.price ? fmtPrice(order.price) : "MARKET"}
          </p>
        </div>
        <div className="text-right flex-none">
          <span className={cn("trade-chip", orderStatusChip(order.status))}>
            {ORDER_STATUS_LABEL[order.status]}
          </span>
          <p className="text-[9px] text-slate-600 mt-1">{fmtTime(order.created_at)}</p>
        </div>
      </div>
    </>
  );
}

function OverviewSkeleton() {
  return (
    <div className="space-y-4" aria-hidden="true">
      <div className="trade-skeleton h-[248px] !rounded-[18px]" />
      <div className="grid grid-cols-2 gap-3">
        <div className="trade-skeleton h-[88px] !rounded-[18px]" />
        <div className="trade-skeleton h-[88px] !rounded-[18px]" />
      </div>
      <div className="trade-skeleton h-[92px] !rounded-[18px]" />
      <div className="trade-skeleton h-[150px] !rounded-[18px]" />
      <div className="flex items-center justify-center gap-2 py-3 text-[11px] text-slate-600">
        <Spinner size={12} />
        正在同步服务器、行情与账户…
      </div>
    </div>
  );
}
