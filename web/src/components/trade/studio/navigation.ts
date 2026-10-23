import type { StudioIconName } from "./icons";
import type {
  ExecutionTab,
  StudioRoute,
  StudioSection,
} from "./types";
import { EXECUTION_TABS, STUDIO_SECTIONS } from "./types";

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
    label: "WORKSPACE",
    items: [
      { id: "overview", label: "总览", labelEn: "Overview", icon: "overview" },
      { id: "strategies", label: "策略", labelEn: "Strategies", icon: "strategies" },
      { id: "research", label: "研究", labelEn: "Research", icon: "research" },
      { id: "experiments", label: "实验", labelEn: "Experiments", icon: "experiments" },
      { id: "execution", label: "执行", labelEn: "Execution", icon: "execution" },
      { id: "markets", label: "市场", labelEn: "Markets", icon: "markets" },
    ],
  },
  {
    label: "ACCOUNT",
    items: [
      { id: "portfolio", label: "组合", labelEn: "Portfolio", icon: "assets" },
      { id: "settings", label: "设置", labelEn: "Settings", icon: "settings" },
    ],
  },
];

export const MOBILE_PRIMARY_NAV: StudioNavItem[] = [
  { id: "overview", label: "总览", labelEn: "Overview", icon: "overview" },
  { id: "strategies", label: "策略", labelEn: "Strategies", icon: "strategies" },
  { id: "research", label: "研究", labelEn: "Research", icon: "research" },
  { id: "execution", label: "执行", labelEn: "Execution", icon: "execution" },
  { id: "markets", label: "行情", labelEn: "Markets", icon: "markets" },
  { id: "portfolio", label: "组合", labelEn: "Portfolio", icon: "assets" },
];

export const SECTION_LABELS: Record<StudioSection, string> = {
  overview: "总览",
  strategies: "策略",
  research: "研究",
  experiments: "实验",
  execution: "执行",
  markets: "市场行情",
  portfolio: "资产组合",
  settings: "设置",
};

/**
 * Legacy acceptance rules: old top-level sections and ?tab= values must keep
 * resolving after Orders moved into Execution and Trade/Assets were renamed.
 */
const LEGACY_TAB_SECTIONS: Record<string, StudioRoute> = {
  overview: { section: "overview" },
  market: { section: "markets" },
  markets: { section: "markets" },
  trade: { section: "execution", tab: "runs" },
  execution: { section: "execution", tab: "runs" },
  orders: { section: "execution", tab: "orders" },
  assets: { section: "portfolio" },
  portfolio: { section: "portfolio" },
  strategies: { section: "strategies" },
  research: { section: "research" },
  experiments: { section: "experiments" },
  settings: { section: "settings" },
};

const LEGACY_SECTION_ALIASES: Record<string, StudioRoute> = {
  ...LEGACY_TAB_SECTIONS,
  trade: { section: "execution", tab: "runs" },
  orders: { section: "execution", tab: "orders" },
  assets: { section: "portfolio" },
};

function isStudioSection(value: string | null): value is StudioSection {
  return Boolean(value && (STUDIO_SECTIONS as readonly string[]).includes(value));
}

function isExecutionTab(value: string | null): value is ExecutionTab {
  return Boolean(value && (EXECUTION_TABS as readonly string[]).includes(value));
}

/** Parse both the current route and the pre-refactor query parameters. */
export function parseStudioRoute(search: string): StudioRoute {
  const params = new URLSearchParams(search);
  const requestedSection = params.get("section");
  const requestedTab = params.get("tab");
  const id = params.get("id") ?? undefined;

  let route: StudioRoute = { section: "overview" };

  if (requestedSection) {
    if (isStudioSection(requestedSection)) {
      route = { section: requestedSection };
    } else if (LEGACY_SECTION_ALIASES[requestedSection]) {
      route = { ...LEGACY_SECTION_ALIASES[requestedSection] };
    }
  } else if (requestedTab) {
    const legacy = LEGACY_TAB_SECTIONS[requestedTab];
    if (legacy) route = { ...legacy };
  }

  if (route.section === "execution" && requestedTab) {
    if (isExecutionTab(requestedTab)) {
      route.tab = requestedTab;
    } else if (requestedTab === "orders") {
      route.tab = "orders";
    }
  }

  if (id && route.section === "strategies") {
    route.id = id;
  }

  return route;
}

/** Build the canonical /trade URL for a route. */
export function studioRouteUrl(route: StudioRoute): string {
  const params = new URLSearchParams();

  if (route.section !== "overview") {
    params.set("section", route.section);
  }

  if (
    route.section === "execution" &&
    route.tab &&
    route.tab !== "runs"
  ) {
    params.set("tab", route.tab);
  }

  if (route.id && route.section === "strategies") {
    params.set("id", route.id);
  }

  const query = params.toString();
  return query ? `/trade?${query}` : "/trade";
}
