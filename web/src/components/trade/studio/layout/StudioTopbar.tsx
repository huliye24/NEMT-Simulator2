"use client";

import { cn, fmtPct, fmtPrice, fmtUSDT } from "@/lib/trade/format";
import type { TradingData } from "../../useTradingData";
import { accountEquity } from "../account/utils";
import { StudioBrand, StudioIcon } from "../icons";
import { SECTION_LABELS } from "../navigation";
import type { StudioSection } from "../types";

interface StudioTopbarProps {
  data: TradingData;
  section: StudioSection;
  onOpenMobileNav: () => void;
  onNavigate: (section: StudioSection) => void;
}

function BalanceSummary({ data }: { data: TradingData }) {
  const equity = accountEquity(data);
  return (
    <div className="ns-ticker-summary">
      <span className="ns-ticker-pair">账户余额</span>
      <span className="ns-ticker-price">{data.balances ? fmtUSDT(equity) : "—"}</span>
      <span className="ns-ticker-pair-quote">USDT</span>
    </div>
  );
}

export default function StudioTopbar({
  data,
  section,
  onOpenMobileNav,
  onNavigate,
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
            onClick={() => onNavigate("portfolio")}
            aria-label="返回投资组合"
          >
            <StudioBrand />
          </button>
        </div>

        <div className="ns-topbar-right">
          <div className="ns-topbar-ticker" aria-label="实时账户余额">
            <BalanceSummary data={data} />
          </div>
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
