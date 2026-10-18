"use client";

import { cn, fmtPct, fmtPrice } from "@/lib/trade/format";
import type { Session, Ticker } from "@/lib/trade/types";
import type { TradingData } from "../../useTradingData";
import { ModePill, Spinner } from "../common";
import { StudioBrand, StudioIcon } from "../icons";
import { SECTION_LABELS } from "../navigation";
import SystemStatusIndicator from "../status/SystemStatusIndicator";
import type { StudioSection } from "../types";

interface StudioTopbarProps {
  session: Session;
  data: TradingData;
  section: StudioSection;
  collapsed: boolean;
  onToggleSidebar: () => void;
  onOpenMobileNav: () => void;
  onNavigate: (section: StudioSection) => void;
  onLogout: () => void;
}

function TickerSummary({ ticker, compact = false }: { ticker: Ticker | null; compact?: boolean }) {
  const change = Number(ticker?.price_change_percent ?? 0);
  const positive = change >= 0;
  return (
    <div className={cn("ns-ticker-summary", compact && "is-compact")}>
      <span className="ns-ticker-pair">
        BTC<span className="ns-ticker-pair-quote">/USDT</span>
      </span>
      <span className="ns-ticker-price">{fmtPrice(ticker?.last_price)}</span>
      <span className={cn("ns-ticker-change", positive ? "is-up" : "is-down")}>
        {fmtPct(ticker?.price_change_percent)}
      </span>
    </div>
  );
}

export default function StudioTopbar({
  session,
  data,
  section,
  collapsed,
  onToggleSidebar,
  onOpenMobileNav,
  onNavigate,
  onLogout,
}: StudioTopbarProps) {
  return (
    <header className="ns-topbar">
      <div className="ns-topbar-main">
        <div className="ns-topbar-left">
          <button
            type="button"
            className="ns-icon-btn ns-mobile-menu-btn"
            onClick={onOpenMobileNav}
            aria-label="打开导航"
          >
            <StudioIcon name="menu" size={20} />
          </button>
          <button
            type="button"
            className="ns-topbar-brand"
            onClick={() => onNavigate("overview")}
            aria-label="返回总览"
          >
            <StudioBrand />
          </button>
          <button
            type="button"
            className="ns-sidebar-toggle ns-desktop-only"
            onClick={onToggleSidebar}
            aria-label={collapsed ? "展开侧边栏" : "收起侧边栏"}
            title={collapsed ? "展开侧边栏" : "收起侧边栏"}
          >
            <StudioIcon name={collapsed ? "chevronRight" : "chevronLeft"} size={16} />
          </button>
        </div>

        <div className="ns-topbar-ticker">
          <TickerSummary ticker={data.ticker} />
        </div>

        <div className="ns-topbar-right">
          <button
            type="button"
            className="ns-icon-btn ns-topbar-refresh ns-desktop-only"
            onClick={() => void data.refreshAll()}
            disabled={data.syncing || !data.online}
            aria-label="刷新全部数据"
            title="刷新全部数据"
          >
            {data.syncing ? <Spinner size={15} /> : <StudioIcon name="refresh" size={16} />}
          </button>

          <SystemStatusIndicator data={data} session={session} />

          <ModePill mode={session.mode} />

          <span className="ns-topbar-separator ns-desktop-only" aria-hidden="true" />

          <button
            type="button"
            className="ns-user"
            onClick={() => onNavigate("settings")}
            aria-label={`账户 ${session.user.username}，打开设置`}
            title="账户设置"
          >
            <span className="ns-user-avatar" aria-hidden="true">
              {session.user.username.slice(0, 1).toUpperCase()}
            </span>
            <span className="ns-user-copy ns-desktop-only">
              <span className="ns-user-name">{session.user.username}</span>
              <span className="ns-user-role">
                {session.user.roles.includes("admin")
                  ? "Administrator"
                  : session.user.roles.includes("trader")
                    ? "Trader"
                    : "Viewer"}
              </span>
            </span>
          </button>

          <button
            type="button"
            className="ns-icon-btn ns-logout-btn ns-desktop-only"
            onClick={onLogout}
            aria-label="退出登录"
            title="退出登录"
          >
            <StudioIcon name="logout" size={17} />
          </button>
        </div>
      </div>

      <div className="ns-topbar-mobile">
        <button
          type="button"
          className="ns-mobile-ticker"
          onClick={() => onNavigate("markets")}
          aria-label="查看 BTC/USDT 行情"
        >
          <div className="ns-mobile-ticker-main">
            <span className="ns-mobile-ticker-symbol">BTC/USDT</span>
            <span className="ns-mobile-ticker-price">{fmtPrice(data.ticker?.last_price)}</span>
            <span
              className={cn(
                "ns-mobile-ticker-change",
                Number(data.ticker?.price_change_percent ?? 0) >= 0 ? "is-up" : "is-down"
              )}
            >
              {fmtPct(data.ticker?.price_change_percent)}
            </span>
          </div>
          <span className="ns-mobile-feed">
            行情
            <StudioIcon name="chevronRight" size={13} />
          </span>
        </button>
      </div>

      <span className="ns-sr-only" aria-live="polite">
        当前页面：{SECTION_LABELS[section]}
      </span>
    </header>
  );
}
