"use client";

import { cn } from "@/lib/trade/format";
import type { SystemStatus } from "@/lib/trade/types";
import { StudioIcon } from "../icons";
import { STUDIO_NAV_GROUPS } from "../navigation";
import type { StudioSection } from "../types";

interface StudioSidebarProps {
  section: StudioSection;
  mobileOpen: boolean;
  system: SystemStatus | null;
  online: boolean;
  onNavigate: (section: StudioSection) => void;
  onCloseMobile: () => void;
}

/**
 * Icon-only navigation rail.
 *
 * The rail is intentionally fixed-width: every destination keeps a single
 * recognizable glyph, and the label lives in the accessible name plus the
 * native tooltip instead of taking permanent horizontal space.
 */
export default function StudioSidebar({
  section,
  mobileOpen,
  system,
  online,
  onNavigate,
  onCloseMobile,
}: StudioSidebarProps) {
  const statusLabel = `Emergentix Cloud ${online ? "已连接" : "离线"}`;
  const statusMeta = `API v${system?.version ?? "—"} · ${system?.mode ?? "DEMO"}`;

  return (
    <aside className={cn("ns-sidebar", mobileOpen && "is-mobile-open")} aria-label="主导航">
      <div className="ns-sidebar-mobile-head">
        <button
          type="button"
          className="ns-sidebar-mobile-close"
          onClick={onCloseMobile}
          aria-label="关闭导航"
        >
          <StudioIcon name="close" size={18} />
        </button>
      </div>

      <div className="ns-sidebar-scroll">
        {STUDIO_NAV_GROUPS.map((group) => (
          <nav className="ns-nav-group" key={group.label} aria-label={group.label}>
            {group.items.map((item) => {
              const active = section === item.id;
              const label = `${item.label} · ${item.labelEn}`;
              return (
                <button
                  type="button"
                  key={item.id}
                  className={cn("ns-nav-item", active && "is-active")}
                  onClick={() => onNavigate(item.id)}
                  aria-current={active ? "page" : undefined}
                  aria-label={label}
                  title={label}
                >
                  <span className="ns-nav-icon">
                    <StudioIcon name={item.icon} size={18} />
                  </span>
                  {active ? <span className="ns-nav-active-bar" aria-hidden="true" /> : null}
                </button>
              );
            })}
          </nav>
        ))}
      </div>

      <div className="ns-sidebar-footer">
        <div
          className="ns-sidebar-status"
          title={`${statusLabel} · ${statusMeta}`}
          aria-label={`${statusLabel} · ${statusMeta}`}
          role="status"
        >
          <span className={cn("ns-sidebar-status-dot", online ? "is-online" : "is-offline")} />
        </div>
      </div>
    </aside>
  );
}
