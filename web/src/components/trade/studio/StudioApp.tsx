"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { ApiError, tradeApi } from "@/lib/trade/api";
import { cn } from "@/lib/trade/format";
import type { Session } from "@/lib/trade/types";
import { useTradingData } from "../useTradingData";
import type { ToastKind } from "../workspace-shared";
import { InlineAlert, Spinner } from "./common";
import { StudioIcon } from "./icons";
import StudioLogin from "./StudioLogin";
import StudioSidebar from "./layout/StudioSidebar";
import StudioTopbar from "./layout/StudioTopbar";
import { MOBILE_PRIMARY_NAV, SECTION_LABELS } from "./navigation";
import ExecutionPage from "./pages/ExecutionPage";
import ExperimentsPage from "./pages/ExperimentsPage";
import MarketsPage from "./pages/MarketsPage";
import PortfolioPage from "./pages/PortfolioPage";
import ResearchPage from "./pages/ResearchPage";
import SettingsPage from "./pages/SettingsPage";
import StrategiesPage from "./pages/StrategiesPage";
import { STUDIO_SECTIONS, type StudioSection } from "./types";

interface ToastState {
  id: number;
  kind: ToastKind;
  message: string;
}

const LEGACY_SECTION_ALIASES: Record<string, StudioSection> = {
  overview: "portfolio",
  trade: "execution",
  orders: "execution",
  assets: "portfolio",
  market: "markets",
  strategy: "strategies",
  experiment: "experiments",
};

function isStudioSection(value: string | null): value is StudioSection {
  return Boolean(value && (STUDIO_SECTIONS as readonly string[]).includes(value));
}

function resolveSection(value: string | null): StudioSection | null {
  if (!value) return null;
  if (isStudioSection(value)) return value;
  return LEGACY_SECTION_ALIASES[value] ?? null;
}

function initialSection(): StudioSection {
  if (typeof window === "undefined") return "portfolio";
  const params = new URLSearchParams(window.location.search);
  const requested = resolveSection(params.get("section") ?? params.get("tab"));
  return requested ?? "portfolio";
}

function sectionUrl(section: StudioSection): string {
  return section === "portfolio" ? "/trade" : `/trade?section=${section}`;
}

export default function StudioApp({ initialLogin = false }: { initialLogin?: boolean }) {
  const [session, setSession] = useState<Session | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [showLogin, setShowLogin] = useState(initialLogin);
  const [checking, setChecking] = useState(!initialLogin);

  useEffect(() => {
    let cancelled = false;

    if (showLogin) {
      return () => {
        cancelled = true;
      };
    }

    tradeApi
      .getMe()
      .then((next) => {
        if (!cancelled) setSession(next);
      })
      .catch(async (error: unknown) => {
        if (cancelled) return;
        if (error instanceof ApiError && error.status === 401) {
          try {
            const guest = await tradeApi.demoLogin("demo");
            if (!cancelled) setSession(guest);
          } catch (guestError) {
            if (!cancelled) {
              setShowLogin(true);
              setNotice(
                guestError instanceof Error ? guestError.message : "访客模式暂不可用"
              );
            }
          }
        } else {
          setShowLogin(true);
          setNotice(
            error instanceof Error ? `无法连接 NEMT 服务端：${error.message}` : "无法连接 NEMT 服务端"
          );
        }
      })
      .finally(() => {
        if (!cancelled) setChecking(false);
      });

    return () => {
      cancelled = true;
    };
  }, [showLogin]);

  if (checking) {
    return (
      <div className="nemt-studio ns-boot">
        <div className="ns-boot-brand">
          <StudioBrandMarkLarge />
          <div>
            <strong>emergentix</strong>
            <span>涌现流派</span>
          </div>
        </div>
        <div className="ns-boot-status">
          <Spinner size={16} />
          <span>正在连接 Emergentix Cloud…</span>
        </div>
      </div>
    );
  }

  if (!session) {
    return (
      <StudioLogin
        notice={notice}
        onLoggedIn={(next) => {
          setNotice(null);
          setSession(next);
          setShowLogin(false);
          window.history.replaceState(null, "", "/trade");
        }}
      />
    );
  }

  return (
    <StudioWorkspace
      key={session.user.username}
      session={session}
      notice={notice}
      onClearNotice={() => setNotice(null)}
      onAuthLost={() => {
        setSession(null);
        setShowLogin(true);
        setNotice("会话已过期，请重新登录");
      }}
      onLogout={async () => {
        try {
          await tradeApi.logout(session.csrf_token);
        } catch {
          // The server session may already be gone. The UI must still not
          // pretend a local cache change revoked the server session.
        }
        setSession(null);
        setNotice(null);
        setShowLogin(true);
        window.history.replaceState(null, "", "/trade?login=1");
      }}
    />
  );
}

function StudioBrandMarkLarge() {
  return (
    <span className="ns-boot-mark" aria-hidden="true">
      <svg width="28" height="28" viewBox="0 0 24 24" fill="none">
        <path
          d="M18 5H6v14h12M6 12h9"
          stroke="currentColor"
          strokeWidth="2.4"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
        <circle cx="18" cy="19" r="1.5" fill="currentColor" />
      </svg>
    </span>
  );
}

function StudioWorkspace({
  session,
  notice,
  onClearNotice,
  onAuthLost,
  onLogout,
}: {
  session: Session;
  notice: string | null;
  onClearNotice: () => void;
  onAuthLost: () => void;
  onLogout: () => Promise<void>;
}) {
  const [section, setSection] = useState<StudioSection>(initialSection);
  const [mobileNavOpen, setMobileNavOpen] = useState(false);
  const [toast, setToast] = useState<ToastState | null>(null);
  const toastTimer = useRef<number | null>(null);
  const mainRef = useRef<HTMLElement>(null);
  const data = useTradingData(session, onAuthLost);

  useEffect(() => {
    document.title = `${SECTION_LABELS[section]} · emergentix`;
  }, [section]);

  useEffect(() => {
    function onPopState() {
      setSection(initialSection());
    }
    window.addEventListener("popstate", onPopState);
    return () => window.removeEventListener("popstate", onPopState);
  }, []);

  useEffect(() => {
    mainRef.current?.scrollTo({ top: 0, behavior: "auto" });
  }, [section]);

  useEffect(() => {
    function onKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") setMobileNavOpen(false);
    }
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, []);

  useEffect(() => {
    const previous = document.body.style.overflow;
    if (mobileNavOpen) document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = previous;
    };
  }, [mobileNavOpen]);

  useEffect(() => {
    return () => {
      if (toastTimer.current) window.clearTimeout(toastTimer.current);
    };
  }, []);

  const notify = useCallback((kind: ToastKind, message: string) => {
    if (toastTimer.current) window.clearTimeout(toastTimer.current);
    setToast({ id: Date.now(), kind, message });
    toastTimer.current = window.setTimeout(() => setToast(null), 5_500);
  }, []);

  const navigate = useCallback((next: StudioSection) => {
    setSection(next);
    setMobileNavOpen(false);
    if (typeof window !== "undefined") {
      window.history.pushState(null, "", sectionUrl(next));
    }
  }, []);

  const sectionProps = { session, data, notify, navigate };
  const issue = !data.online
    ? {
        tone: "danger" as const,
        title: "网络已断开",
        body: "行情轮询、账户刷新和交易写操作已暂停，恢复网络后会自动重试。",
      }
    : data.coreError
      ? {
          tone: "warn" as const,
          title: "状态同步异常",
          body: `${data.coreError}。交易入口会在服务端校验失败时保持禁用。`,
        }
      : data.feedError
        ? {
            tone: "warn" as const,
            title: "行情连接异常",
            body: data.feedError,
          }
        : null;

  return (
    <div
      className={cn("nemt-studio", mobileNavOpen && "is-nav-open")}
      data-mode={session.mode}
    >
      <StudioTopbar
        data={data}
        section={section}
        onOpenMobileNav={() => setMobileNavOpen(true)}
        onNavigate={navigate}
      />

      <StudioSidebar
        section={section}
        mobileOpen={mobileNavOpen}
        system={data.system}
        online={data.online}
        onNavigate={navigate}
        onCloseMobile={() => setMobileNavOpen(false)}
      />
      <button
        type="button"
        className="ns-sidebar-backdrop"
        aria-label="关闭导航"
        tabIndex={mobileNavOpen ? 0 : -1}
        onClick={() => setMobileNavOpen(false)}
      />

      <main className="ns-main" ref={mainRef}>
        <div className="ns-main-inner">
          {notice ? (
            <InlineAlert
              tone="warn"
              action={
                <button type="button" className="ns-text-link ns-text-link-sm" onClick={onClearNotice}>
                  关闭
                </button>
              }
            >
              <span>{notice}</span>
            </InlineAlert>
          ) : null}

          {issue ? (
            <InlineAlert
              tone={issue.tone}
              action={
                <button
                  type="button"
                  className="ns-text-link ns-text-link-sm"
                  onClick={() => void data.refreshAll()}
                  disabled={data.syncing}
                >
                  {data.syncing ? "重试中…" : "重试"}
                </button>
              }
            >
              <span className="ns-inline-alert-title">{issue.title}</span>
              <span className="ns-inline-alert-line">{issue.body}</span>
            </InlineAlert>
          ) : null}

          {section === "strategies" ? <StrategiesPage {...sectionProps} /> : null}
          {section === "research" ? <ResearchPage {...sectionProps} /> : null}
          {section === "experiments" ? <ExperimentsPage {...sectionProps} /> : null}
          {section === "execution" ? <ExecutionPage {...sectionProps} /> : null}
          {section === "markets" ? <MarketsPage {...sectionProps} /> : null}
          {section === "portfolio" ? <PortfolioPage {...sectionProps} /> : null}
          {section === "settings" ? (
            <SettingsPage {...sectionProps} onLogout={onLogout} />
          ) : null}
        </div>
      </main>

      <nav className="ns-mobile-nav" aria-label="移动端主导航">
        {MOBILE_PRIMARY_NAV.map((item) => {
          const active = section === item.id;
          return (
            <button
              type="button"
              key={item.id}
              className={cn("ns-mobile-nav-item", active && "is-active")}
              onClick={() => navigate(item.id)}
              aria-current={active ? "page" : undefined}
            >
              <span className="ns-mobile-nav-icon">
                <StudioIcon name={item.icon} size={20} />
              </span>
              <span>{item.label}</span>
            </button>
          );
        })}
      </nav>

      {toast ? (
        <div
          className={cn("ns-toast", `ns-toast-${toast.kind}`)}
          role={toast.kind === "error" ? "alert" : "status"}
        >
          <span className="ns-toast-icon">
            <StudioIcon
              name={toast.kind === "success" ? "check" : toast.kind === "error" ? "warning" : toast.kind === "warning" ? "warning" : "info"}
              size={16}
            />
          </span>
          <p>{toast.message}</p>
          <button
            type="button"
            className="ns-toast-close"
            onClick={() => setToast(null)}
            aria-label="关闭通知"
          >
            <StudioIcon name="close" size={14} />
          </button>
        </div>
      ) : null}
    </div>
  );
}
