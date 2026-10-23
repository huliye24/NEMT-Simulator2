import type { StudioIconName } from "./icons";
import type { StudioSection } from "./types";

export interface StudioNavItem {
  id: StudioSection;
  label: string;
  labelEn: string;
  icon: StudioIconName;
}

export interface StudioNavGroup {
  label: string;
  items: StudioNavItem[];
}

export const STUDIO_NAV_GROUPS: StudioNavGroup[] = [
  {
    label: "CORE WORKFLOW",
    items: [
      { id: "portfolio", label: "投资组合", labelEn: "Portfolio", icon: "assets" },
      { id: "markets", label: "市场", labelEn: "Markets", icon: "markets" },
      { id: "strategies", label: "策略", labelEn: "Strategies", icon: "strategies" },
      { id: "execution", label: "模拟盘", labelEn: "Paper Trading", icon: "play" },
    ],
  },
  {
    label: "SECONDARY",
    items: [
      { id: "research", label: "研究", labelEn: "Research", icon: "research" },
      { id: "experiments", label: "实验", labelEn: "Experiments", icon: "experiments" },
      { id: "settings", label: "个人空间", labelEn: "Space", icon: "user" },
      { id: "api", label: "设置", labelEn: "Settings", icon: "settings" },
    ],
  },
];

export const MOBILE_PRIMARY_NAV: StudioNavItem[] = [
  { id: "portfolio", label: "组合", labelEn: "Portfolio", icon: "assets" },
  { id: "markets", label: "市场", labelEn: "Markets", icon: "markets" },
  { id: "strategies", label: "策略", labelEn: "Strategies", icon: "strategies" },
  { id: "execution", label: "模拟盘", labelEn: "Paper Trading", icon: "play" },
];

export const SECTION_LABELS: Record<StudioSection, string> = {
  strategies: "策略",
  research: "研究",
  experiments: "实验",
  execution: "模拟盘",
  markets: "市场",
  portfolio: "投资组合",
  settings: "个人空间",
  api: "设置",
};
