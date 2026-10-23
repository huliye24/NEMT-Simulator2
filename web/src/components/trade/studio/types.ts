import type { Session } from "@/lib/trade/types";
import type { ToastKind } from "../workspace-shared";
import type { TradingData } from "../useTradingData";

export const STUDIO_SECTIONS = [
  "overview",
  "strategies",
  "research",
  "experiments",
  "execution",
  "markets",
  "portfolio",
  "settings",
] as const;

export type StudioSection = (typeof STUDIO_SECTIONS)[number];

export const EXECUTION_TABS = ["runs", "orders", "fills", "events", "risk"] as const;

export type ExecutionTab = (typeof EXECUTION_TABS)[number];

export interface StudioRoute {
  section: StudioSection;
  /** Execution sub-tab. Only meaningful when section === "execution". */
  tab?: ExecutionTab;
  /** Strategy identifier for the detail view. */
  id?: string;
}

export interface StudioNavigateOptions {
  tab?: ExecutionTab;
  id?: string;
}

export type StudioNavigate = (
  section: StudioSection,
  options?: StudioNavigateOptions
) => void;

export interface StudioPageProps {
  session: Session;
  data: TradingData;
  notify: (kind: ToastKind, message: string) => void;
  navigate: StudioNavigate;
  route: StudioRoute;
}

export type StudioNotify = StudioPageProps["notify"];
