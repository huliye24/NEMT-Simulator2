"use client";

import { cn } from "@/lib/trade/format";
import { StudioBrand, StudioIcon } from "../icons";
import { STUDIO_NAV_GROUPS } from "../navigation";
import type { StudioSection } from "../types";

interface StudioSidebarProps {
  section: StudioSection;
  collapsed: boolean;
  mobileOpen: boolean;
  onNavigate: (section: StudioSection) => void;
  onToggleCollapsed: () => void;
  onCloseMobile: () => void;
}

export default function StudioSidebar({
  section,
  collapsed,
  mobileOpen,
  onNavigate,
  onToggleCollapsed,
  onCloseMobile,
}: StudioSidebarProps) {
  return (
    <aside
      className={cn("ns-sidebar", collapsed && "is-collapsed", mobileOpen && "is-mobile-open")}
      aria-label="主导航"
    >
      <div className="ns-sidebar-mobile-head">
        <StudioBrand compact />
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
            <p className="ns-nav-label">{group.label}</p>
            {group.items.map((item) => {
              const active = section === item.id;
              return (
                <button
                  type="button"
                  key={item.id}
                  className={cn("ns-nav-item", active && "is-active")}
                  onClick={() => onNavigate(item.id)}
                  aria-current={active ? "page" : undefined}
                  title={`${item.label} · ${item.labelEn}`}
                >
                  <span className="ns-nav-icon">
                    <StudioIcon name={item.icon} size={18} />
                  </span>
                  <span className="ns-nav-copy">
                    <span className="ns-nav-text">{item.label}</span>
                    <span className="ns-nav-english">{item.labelEn}</span>
                  </span>
                  {active ? <span className="ns-nav-active-bar" aria-hidden="true" /> : null}
                </button>
              );
            })}
          </nav>
        ))}
      </div>

      <div className="ns-sidebar-footer">
        <div className="ns-sidebar-controls">
          <button
            type="button"
            className="ns-sidebar-collapse"
            onClick={onToggleCollapsed}
            aria-label={collapsed ? "展开侧边栏" : "收起侧边栏"}
            title={collapsed ? "展开侧边栏" : "收起侧边栏"}
          >
            <StudioIcon
              name={collapsed ? "chevronRight" : "chevronLeft"}
              size={17}
            />
            <span className="ns-sidebar-collapse-label">收起导航</span>
          </button>
        </div>
      </div>
    </aside>
  );
}
