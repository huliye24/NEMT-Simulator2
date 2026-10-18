"use client";

import { useEffect, useRef, useState } from "react";
import { ageLabel, cn, fmtTime } from "@/lib/trade/format";
import type { Session } from "@/lib/trade/types";
import type { TradingData } from "../../useTradingData";
import { ModePill, Spinner, StatusDot } from "../common";
import { StudioIcon } from "../icons";

export type StatusTone = "ok" | "warn" | "bad" | "muted" | "brand";

export interface StatusRow {
  id: string;
  label: string;
  value: string;
  tone: StatusTone;
  hint: string;
}

export interface SystemStatusModel {
  tone: StatusTone;
  label: string;
  rows: StatusRow[];
  lastUpdatedAt: string | null;
  mode: Session["mode"];
}

function marketRow(data: TradingData): StatusRow {
  if (!data.online) {
    return {
      id: "market",
      label: "Market Data",
      value: "Offline",
      tone: "bad",
      hint: "网络离线，行情轮询已暂停",
    };
  }
  if (data.feedError) {
    return {
      id: "market",
      label: "Market Data",
      value: "Error",
      tone: "bad",
      hint: data.feedError,
    };
  }
  if (!data.ticker) {
    return {
      id: "market",
      label: "Market Data",
      value: "Waiting",
      tone: "muted",
      hint: "等待 BTC/USDT 行情快照",
    };
  }
  if (data.ticker.stale) {
    return {
      id: "market",
      label: "Market Data",
      value: "Delayed",
      tone: "warn",
      hint: `数据 ${ageLabel(data.ticker.fetched_at)} · 超过新鲜度阈值`,
    };
  }
  return {
    id: "market",
    label: "Market Data",
    value: "Fresh",
    tone: "ok",
    hint: `${data.ticker.source === "demo" ? "DEMO feed" : "Binance"} · ${ageLabel(
      data.ticker.fetched_at
    )}`,
  };
}

function accountRow(data: TradingData): StatusRow {
  const balances = data.balances;
  if (!balances) {
    return {
      id: "account",
      label: "Account Sync",
      value: data.coreError ? "Error" : "Loading",
      tone: data.coreError ? "bad" : "muted",
      hint: data.coreError ?? "等待账户快照",
    };
  }
  if (!balances.connected) {
    const configured = balances.account_status !== "NOT_CONFIGURED";
    return {
      id: "account",
      label: "Account Sync",
      value: configured ? "Disconnected" : "Not Configured",
      tone: configured ? "bad" : "muted",
      hint: balances.note ?? "账户只读同步未建立",
    };
  }
  return {
    id: "account",
    label: "Account Sync",
    value: balances.stale ? "Stale" : "Synced",
    tone: balances.stale ? "warn" : "ok",
    hint: `${
      balances.source === "demo" ? "DEMO 模拟账本" : "Binance 只读账户"
    } · ${ageLabel(balances.fetched_at)}`,
  };
}

export function buildSystemStatus(
  data: TradingData,
  mode: Session["mode"]
): SystemStatusModel {
  const system = data.system;
  const cloud: StatusRow = !data.online
    ? {
        id: "cloud",
        label: "NEMT Cloud API",
        value: "Offline",
        tone: "bad",
        hint: "浏览器网络离线",
      }
    : data.coreError
      ? {
          id: "cloud",
          label: "NEMT Cloud API",
          value: "Degraded",
          tone: "warn",
          hint: data.coreError,
        }
      : system
        ? {
            id: "cloud",
            label: "NEMT Cloud API",
            value: "Connected",
            tone: "ok",
            hint: `服务端 v${system.version} · ${system.mode}`,
          }
        : {
            id: "cloud",
            label: "NEMT Cloud API",
            value: "Connecting",
            tone: "muted",
            hint: "等待首次状态同步",
          };

  const execution: StatusRow = {
    id: "execution",
    label: "Execution Service",
    value: "Not Connected",
    tone: "warn",
    hint: "策略执行服务尚未接入，不展示虚构运行实例",
  };

  const paused = Boolean(system?.risk.pause_new_orders);
  const trading: StatusRow = !system
    ? {
        id: "trading",
        label: "Trading Availability",
        value: "Unknown",
        tone: "muted",
        hint: "服务端交易状态未同步",
      }
    : paused
      ? {
          id: "trading",
          label: "Trading Availability",
          value: "Paused",
          tone: "warn",
          hint: system.risk.pause_reason ?? "管理员已暂停新订单",
        }
      : {
          id: "trading",
          label: "Trading Availability",
          value: system.trading_enabled ? "Restricted" : "Disabled",
          tone: system.trading_enabled ? "warn" : "muted",
          hint: system.trading_enabled
            ? "仅服务器订单守护可用；策略执行未授权"
            : "服务端未开放订单写入",
        };

  const overall: { tone: StatusTone; label: string } = !data.online
    ? { tone: "bad", label: "Offline" }
    : data.coreError || data.feedError
      ? { tone: "warn", label: "Degraded" }
      : system
        ? { tone: "ok", label: "Connected" }
        : { tone: "muted", label: "Connecting" };

  const timestamps = [data.ticker?.fetched_at, data.balances?.fetched_at]
    .filter((value): value is string => Boolean(value))
    .sort((a, b) => new Date(b).getTime() - new Date(a).getTime());

  return {
    ...overall,
    mode,
    rows: [cloud, marketRow(data), accountRow(data), execution, trading],
    lastUpdatedAt: timestamps[0] ?? system?.server_time ?? null,
  };
}

export function SystemStatusButton({
  model,
  open,
  onClick,
}: {
  model: SystemStatusModel;
  open: boolean;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      className={cn("ns-status-trigger", open && "is-open")}
      onClick={onClick}
      aria-haspopup="dialog"
      aria-expanded={open}
      title="查看系统状态"
    >
      <StatusDot tone={model.tone} pulse={model.tone === "ok"} size={7} />
      <span className="ns-status-trigger-label">{model.label}</span>
      <ModePill mode={model.mode} compact />
      <StudioIcon name="chevronDown" size={13} className="ns-status-trigger-chevron" />
    </button>
  );
}

export function SystemStatusDetails({
  model,
  className = "",
}: {
  model: SystemStatusModel;
  className?: string;
}) {
  return (
    <div className={cn("ns-status-details", className)}>
      <ul className="ns-status-rows">
        {model.rows.map((row) => (
          <li className="ns-status-row" key={row.id}>
            <div className="ns-status-row-main">
              <StatusDot tone={row.tone} pulse={row.tone === "ok"} size={6} />
              <span className="ns-status-row-label">{row.label}</span>
              <span className={cn("ns-status-row-value", `is-${row.tone}`)}>
                {row.value}
              </span>
            </div>
            <p className="ns-status-row-hint">{row.hint}</p>
          </li>
        ))}
      </ul>
      <p className="ns-status-foot">
        <StudioIcon name="clock" size={11} />
        最近数据 {model.lastUpdatedAt ? `${fmtTime(model.lastUpdatedAt)} · ${ageLabel(model.lastUpdatedAt)}` : "—"}
      </p>
      <p className="ns-status-note">
        连接正常、服务正常、数据新鲜和交易可用是四个独立状态，不可相互替代。
      </p>
    </div>
  );
}

export function SystemStatusMenu({
  model,
  onRefresh,
  syncing,
}: {
  model: SystemStatusModel;
  onRefresh: () => void;
  syncing: boolean;
}) {
  const [open, setOpen] = useState(false);
  const wrapRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    function onPointerDown(event: MouseEvent | TouchEvent) {
      if (wrapRef.current && !wrapRef.current.contains(event.target as Node)) {
        setOpen(false);
      }
    }
    function onKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") setOpen(false);
    }
    document.addEventListener("pointerdown", onPointerDown);
    document.addEventListener("keydown", onKeyDown);
    return () => {
      document.removeEventListener("pointerdown", onPointerDown);
      document.removeEventListener("keydown", onKeyDown);
    };
  }, [open]);

  return (
    <div className="ns-status-menu" ref={wrapRef}>
      <SystemStatusButton model={model} open={open} onClick={() => setOpen((value) => !value)} />
      {open ? (
        <div className="ns-status-popover" role="dialog" aria-label="系统状态">
          <div className="ns-status-popover-head">
            <div>
              <h2>System Status</h2>
              <p>连接、服务、数据与交易权限</p>
            </div>
            <div className="ns-status-popover-actions">
              <button
                type="button"
                className="ns-icon-btn ns-icon-btn-sm"
                onClick={onRefresh}
                disabled={syncing}
                aria-label="刷新系统状态"
                title="刷新系统状态"
              >
                {syncing ? <Spinner size={13} /> : <StudioIcon name="refresh" size={14} />}
              </button>
              <button
                type="button"
                className="ns-icon-btn ns-icon-btn-sm"
                onClick={() => setOpen(false)}
                aria-label="关闭系统状态"
              >
                <StudioIcon name="close" size={14} />
              </button>
            </div>
          </div>
          <SystemStatusDetails model={model} />
        </div>
      ) : null}
    </div>
  );
}
