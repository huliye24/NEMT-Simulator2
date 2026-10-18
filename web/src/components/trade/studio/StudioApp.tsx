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
import {
  MOBILE_PRIMARY_NAV,
  SECTION_LABELS,
  parseStudioRoute,
  studioRouteUrl,
} from "./navigation";
import ExecutionPage from "./pages/ExecutionPage";
import ExperimentsPage from "./pages/ExperimentsPage";
import MarketsPage from "./pages/MarketsPage";
import OverviewPage from "./pages/OverviewPage";
import PortfolioPage from "./pages/PortfolioPage";
import ResearchPage from "./pages/ResearchPage";
import SettingsPage from "./pages/SettingsPage";
import StrategiesPage from "./pages/StrategiesPage";
import type {
  StudioNavigateOptions,
  StudioRoute,
  StudioSection,
} from "./types";

interface ToastState {
  id: number;
  kind: ToastKind;
  message: string;
}

function initialRoute(): StudioRoute {
  if (typeof window === "undefined") return { section: "overview" };
  return parseStudioRoute(window.location.search);
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
            <strong>NEMT</strong>
            <span>STUDIO</span>
          </div>
        </div>
        <div className="ns-boot-status">
          <Spinner size={16} />
          <span>正在连接 NEMT Cloud…</span>
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
          d="M5 18V6l14 12V6"
          stroke="currentColor"
          strokeWidth="2.4"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
        <circle cx="19" cy="18" r="1.5" fill="currentColor" />
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
  const [route, setRoute] = useState<StudioRoute>(initialRoute);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(() => {
    if (typeof window === "undefined") return false;
    try {
      return window.localStorage.getItem("nemt-studio-sidebar-collapsed") === "1";
    } catch {
      return false;
    }
  });
  const [mobileNavOpen, setMobileNavOpen] = useState(false);
  const [toast, setToast] = useState<ToastState | null>(null);
  const toastTimer = useRef<number | null>(null);
  const mainRef = useRef<HTMLElement>(null);
  const data = useTradingData(session, onAuthLost);

  useEffect(() => {
    document.title = `${SECTION_LABELS[route.section]} · NEMT Studio`;
  }, [route.section]);

  useEffect(() => {
    function onPopState() {
      setRoute(parseStudioRoute(window.location.search));
    }
    window.addEventListener("popstate", onPopState);
    return () => window.removeEventListener("popstate", onPopState);
  }, []);

  useEffect(() => {
    mainRef.current?.scrollTo({ top: 0, behavior: "auto" });
  }, [route]);

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

  const navigate = useCallback(
    (section: StudioSection, options?: StudioNavigateOptions) => {
      const next: StudioRoute = { section };
      if (section === "execution") {
        next.tab = options?.tab ?? "runs";
      }
      if (options?.id && section === "strategies") {
        next.id = options.id;
      }
      setRoute(next);
      setMobileNavOpen(false);
      if (typeof window !== "undefined") {
        const url = studioRouteUrl(next);
        if (url !== `${window.location.pathname}${window.location.search}`) {
          window.history.pushState(null, "", url);
        }
      }
    },
    []
  );

  function toggleCollapsed() {
    setSidebarCollapsed((current) => {
      const next = !current;
      try {
        window.localStorage.setItem("nemt-studio-sidebar-collapsed", next ? "1" : "0");
      } catch {
        // Local preference is optional.
      }
      return next;
    });
  }

  const sectionProps = { session, data, notify, navigate, route };
  const issue = !data.online
    ? {
        tone: "danger" as const,
        title: "网络已断开",
        body: "行情轮询、账户刷新和执行写操作已暂停，恢复网络后会自动重试。",
      }
    : data.coreError
      ? {
          tone: "warn" as const,
          title: "NEMT Cloud 状态同步异常",
          body: `${data.coreError}。只读数据仍保留在最近一次成功同步的快照中。`,
        }
      : null;

  return (
    <div
      className={cn("nemt-studio", mobileNavOpen && "is-nav-open")}
      data-collapsed={sidebarCollapsed ? "true" : "false"}
      data-mode={session.mode}
      data-section={route.section}
    >
      <StudioTopbar
        session={session}
        data={data}
        section={route.section}
        collapsed={sidebarCollapsed}
        onToggleSidebar={toggleCollapsed}
        onOpenMobileNav={() => setMobileNavOpen(true)}
        onNavigate={navigate}
        onLogout={() => void onLogout()}
      />

      <StudioSidebar
        section={route.section}
        collapsed={sidebarCollapsed}
        mobileOpen={mobileNavOpen}
        onNavigate={navigate}
        onToggleCollapsed={toggleCollapsed}
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

          {route.section === "overview" ? <OverviewPage {...sectionProps} /> : null}
          {route.section === "strategies" ? <StrategiesPage {...sectionProps} /> : null}
          {route.section === "research" ? <ResearchPage {...sectionProps} /> : null}
          {route.section === "experiments" ? <ExperimentsPage {...sectionProps} /> : null}
          {route.section === "execution" ? <ExecutionPage {...sectionProps} /> : null}
          {route.section === "markets" ? <MarketsPage {...sectionProps} /> : null}
          {route.section === "portfolio" ? <PortfolioPage {...sectionProps} /> : null}
          {route.section === "settings" ? (
            <SettingsPage
              {...sectionProps}
              sidebarCollapsed={sidebarCollapsed}
              onToggleSidebar={toggleCollapsed}
              onLogout={onLogout}
            />
          ) : null}
        </div>
      </main>

      <nav className="ns-mobile-nav" aria-label="移动端主导航">
        {MOBILE_PRIMARY_NAV.map((item) => {
          const active = route.section === item.id;
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
