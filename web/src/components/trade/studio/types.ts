import type { Session } from "@/lib/trade/types";
import type { ToastKind } from "../workspace-shared";
import type { TradingData } from "../useTradingData";

export const STUDIO_SECTIONS = [
  "portfolio",
  "strategies",
  "research",
  "experiments",
  "execution",
  "markets",
  "settings",
  "api",
] as const;

export type StudioSection = (typeof STUDIO_SECTIONS)[number];

export interface StudioPageProps {
  session: Session;
  data: TradingData;
  notify: (kind: ToastKind, message: string) => void;
  navigate: (section: StudioSection) => void;
}

export type StudioNotify = StudioPageProps["notify"];
