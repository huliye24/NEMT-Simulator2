"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { ApiError, tradeApi } from "@/lib/trade/api";
import { ageLabel, cn, fmtPct, fmtPrice } from "@/lib/trade/format";
import type { Session, TradeTabKey } from "@/lib/trade/types";
import LoginScreen from "./LoginScreen";
import MarketTab from "./MarketTab";
import OrdersTab from "./OrdersTab";
import OverviewTab from "./OverviewTab";
import SettingsTab from "./SettingsTab";
import TradeTab from "./TradeTab";
import { useTradingData } from "./useTradingData";
import type { ToastKind } from "./workspace-shared";
import {
  BrandMark,
  Icon,
  ModeBadge,
  Spinner,
  StatusDot,
} from "./ui";

const TABS: {
  key: TradeTabKey;
  label: string;
  icon: "overview" | "market" | "trade" | "orders" | "settings";
}[] = [
  { key: "overview", label: "总览", icon: "overview" },
  { key: "market", label: "行情", icon: "market" },
  { key: "trade", label: "交易", icon: "trade" },
  { key: "orders", label: "订单", icon: "orders" },
  { key: "settings", label: "设置", icon: "settings" },
];

function isTradeTab(value: string | null): value is TradeTabKey {
  return TABS.some((tab) => tab.key === value);
}

interface ToastState {
  id: number;
  kind: ToastKind;
  message: string;
}

function initialTab(): TradeTabKey {
  if (typeof window === "undefined") return "overview";
  const requested = new URLSearchParams(window.location.search).get("tab");
  return isTradeTab(requested) ? requested : "overview";
}

export default function TradeApp() {
  const [session, setSession] = useState<Session | null>(null);
  const [checking, setChecking] = useState(true);
  const [notice, setNotice] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    tradeApi
      .getMe()
      .then((next) => {
        if (!cancelled) setSession(next);
      })
      .catch((error: unknown) => {
        if (cancelled) return;
        if (!(error instanceof ApiError) || error.status !== 401) {
          setNotice(
            error instanceof Error
              ? `无法恢复会话：${error.message}`
              : "无法连接 NEMT 服务端"
          );
        }
      })
      .finally(() => {
        if (!cancelled) setChecking(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (process.env.NODE_ENV !== "production") return;
    if (!("serviceWorker" in navigator)) return;
    const register = () => {
      navigator.serviceWorker
        .register("/sw.js", { scope: "/", updateViaCache: "none" })
        .catch(() => {
          // PWA support is best-effort; the trading app never depends on it.
        });
    };
    if (document.readyState === "complete") register();
    else window.addEventListener("load", register, { once: true });
    return () => window.removeEventListener("load", register);
  }, []);

  if (checking) {
    return (
      <div className="trade-shell flex items-center justify-center px-6">
        <div className="flex flex-col items-center text-center">
          <div className="relative">
            <div className="absolute inset-0 -m-5 rounded-full bg-cyan-400/10 blur-2xl" />
            <BrandMark size={66} className="relative" />
          </div>
          <p className="mt-4 text-[12px] tracking-[0.18em] text-slate-400 font-semibold">
            NEMT TRADE
          </p>
          <div className="mt-3 flex items-center gap-2 text-[10px] text-slate-600">
            <Spinner size={12} />
            正在连接 NEMT Cloud API…
          </div>
        </div>
      </div>
    );
  }

  if (!session) {
    return (
      <LoginScreen
        notice={notice}
        onLoggedIn={(next) => {
          setNotice(null);
          setSession(next);
        }}
      />
    );
  }

  return (
    <TradingWorkspace
      key={session.user.username}
      session={session}
      onAuthLost={() => {
        setSession(null);
        setNotice("会话已过期，请重新登录");
      }}
      onLogout={() => {
        setSession(null);
        setNotice(null);
      }}
    />
  );
}

function TradingWorkspace({
  session,
  onAuthLost,
  onLogout,
}: {
  session: Session;
  onAuthLost: () => void;
  onLogout: () => void;
}) {
  const [tab, setTab] = useState<TradeTabKey>(initialTab);
  const [toast, setToast] = useState<ToastState | null>(null);
  const toastTimer = useRef<number | null>(null);
  const data = useTradingData(session, onAuthLost);

  const notify = useCallback((kind: ToastKind, message: string) => {
    if (toastTimer.current) window.clearTimeout(toastTimer.current);
    setToast({ id: Date.now(), kind, message });
    toastTimer.current = window.setTimeout(() => setToast(null), 5_000);
  }, []);

  useEffect(() => {
    return () => {
      if (toastTimer.current) window.clearTimeout(toastTimer.current);
    };
  }, []);

  function selectTab(next: TradeTabKey) {
    setTab(next);
    const url = next === "overview" ? "/trade" : `/trade?tab=${next}`;
    window.history.replaceState(null, "", url);
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  const ticker = data.ticker;
  const change = Number(ticker?.price_change_percent ?? 0);
  const online = data.online;
  const feedHealthy =
    online && Boolean(ticker) && !ticker?.stale && !data.feedError;

  return (
    <div className="trade-shell pb-24">
      <header className="sticky top-0 z-40 trade-safe-top">
        <div className="bg-[#04070c]/88 backdrop-blur-xl border-b border-white/[0.06]">
          <div className="max-w-[560px] mx-auto px-4">
            <div className="h-[52px] flex items-center justify-between gap-3">
              <button
                type="button"
                onClick={() => selectTab("overview")}
                className="flex items-center gap-2 min-w-0"
                aria-label="NEMT Trade 总览"
              >
                <BrandMark size={27} />
                <span className="text-[13px] font-bold tracking-[0.08em] text-slate-100">
                  NEMT
                </span>
                <span className="text-[9px] font-semibold tracking-[0.18em] text-cyan-300/80">
                  TRADE
                </span>
              </button>

              <div className="flex items-center gap-1.5">
                <ModeBadge mode={session.mode} />
                <div
                  className={cn(
                    "w-7 h-7 rounded-full border flex items-center justify-center",
                    feedHealthy
                      ? "border-emerald-400/20 bg-emerald-400/[0.05] text-emerald-300"
                      : "border-amber-400/20 bg-amber-400/[0.05] text-amber-300"
                  )}
                  title={feedHealthy ? "行情连接正常" : "行情连接异常"}
                >
                  <StatusDot
                    tone={feedHealthy ? "ok" : online ? "warn" : "bad"}
                    pulse={feedHealthy}
                    size={7}
                  />
                </div>
                <button
                  type="button"
                  onClick={() => void data.refreshAll()}
                  disabled={data.syncing || !online}
                  className="w-8 h-8 rounded-full border border-white/[0.08] bg-white/[0.02] flex items-center justify-center text-slate-500 disabled:opacity-40 active:text-cyan-300"
                  aria-label="刷新全部数据"
                >
                  {data.syncing ? <Spinner size={13} /> : <Icon name="refresh" size={14} />}
                </button>
              </div>
            </div>

            <div className="flex items-center justify-between gap-3 pb-2.5 -mt-0.5">
              <div className="flex items-baseline gap-2 min-w-0">
                <span className="text-[10px] text-slate-500">BTC/USDT</span>
                <span className="trade-number text-[13px] font-semibold text-slate-200">
                  {fmtPrice(ticker?.last_price)}
                </span>
                <span
                  className={cn(
                    "trade-number text-[10px] font-semibold",
                    change >= 0 ? "trade-up" : "trade-down"
                  )}
                >
                  {fmtPct(ticker?.price_change_percent)}
                </span>
              </div>
              <div className="flex items-center gap-2 text-[9px] text-slate-600 flex-none">
                <span>{!online ? "离线" : ticker ? ageLabel(ticker.fetched_at) : "等待行情"}</span>
                {data.system?.risk.pause_new_orders ? (
                  <span className="flex items-center gap-1 text-rose-300/80">
                    <StatusDot tone="bad" size={5} />
                    已暂停
                  </span>
                ) : null}
              </div>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-[560px] mx-auto px-4 pt-4 pb-8">
        {data.coreError && online ? (
          <div className="mb-4 flex items-start justify-between gap-3 rounded-xl border border-amber-300/20 bg-amber-300/[0.06] px-3.5 py-2.5">
            <div className="flex items-start gap-2 min-w-0">
              <Icon name="warning" size={13} className="text-amber-300 mt-0.5 flex-none" />
              <p className="text-[10px] leading-relaxed text-amber-100/65">
                状态同步异常：{data.coreError}。交易按钮会在服务端恢复前保持禁用。
              </p>
            </div>
            <button
              type="button"
              onClick={() => void data.refreshAll()}
              className="text-[10px] font-semibold text-amber-200/80 flex-none"
            >
              重试
            </button>
          </div>
        ) : null}

        {tab === "overview" ? (
          <OverviewTab data={data} onNavigate={selectTab} />
        ) : tab === "market" ? (
          <MarketTab data={data} onTrade={() => selectTab("trade")} />
        ) : tab === "trade" ? (
          <TradeTab
            session={session}
            data={data}
            notify={notify}
            onOrdersChanged={data.refreshAll}
          />
        ) : tab === "orders" ? (
          <OrdersTab
            session={session}
            data={data}
            notify={notify}
            refreshAll={data.refreshAll}
          />
        ) : (
          <SettingsTab
            session={session}
            data={data}
            notify={notify}
            onLogout={onLogout}
            refreshAll={data.refreshAll}
          />
        )}
      </main>

      <nav
        className="trade-bottom-nav fixed bottom-0 left-0 right-0 z-50"
        aria-label="主导航"
      >
        <div className="max-w-[560px] mx-auto grid grid-cols-5 gap-1 px-2 pt-1.5">
          {TABS.map((item) => {
            const active = tab === item.key;
            return (
              <button
                key={item.key}
                type="button"
                onClick={() => selectTab(item.key)}
                className={cn("trade-nav-item", active && "trade-nav-item-active")}
                aria-current={active ? "page" : undefined}
              >
                {item.key === "trade" ? (
                  <span
                    className={cn(
                      "w-7 h-7 rounded-full flex items-center justify-center -mt-0.5 transition-colors",
                      active
                        ? "bg-gradient-to-br from-cyan-300 to-cyan-600 text-[#03131a] shadow-[0_4px_16px_rgba(16,219,233,0.25)]"
                        : "bg-white/[0.05] text-slate-400"
                    )}
                  >
                    <Icon name="trade" size={15} strokeWidth={2.2} />
                  </span>
                ) : (
                  <Icon name={item.icon} size={18} />
                )}
                <span>{item.label}</span>
              </button>
            );
          })}
        </div>
      </nav>

      {toast ? (
        <div
          className={cn("trade-toast", `trade-toast-${toast.kind}`)}
          role="status"
          onClick={() => setToast(null)}
        >
          <div className="flex items-start gap-2.5">
            <span className="mt-0.5 flex-none">
              {toast.kind === "success" ? (
                <Icon name="check" size={14} />
              ) : toast.kind === "error" ? (
                <Icon name="warning" size={14} />
              ) : (
                <Icon name="info" size={14} />
              )}
            </span>
            <p className="leading-relaxed flex-1">{toast.message}</p>
            <span className="text-[10px] opacity-50 flex-none">关闭</span>
          </div>
        </div>
      ) : null}
    </div>
  );
}
