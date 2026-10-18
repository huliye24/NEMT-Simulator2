"use client";

import { useEffect, useRef, useState } from "react";
import { cn, fmtTime } from "@/lib/trade/format";
import type { Session } from "@/lib/trade/types";
import type { TradingData } from "../../useTradingData";
import { ModePill, StatusDot } from "../common";
import { StudioIcon } from "../icons";
import { buildSystemStatus } from "./system-status";

export default function SystemStatusIndicator({
  data,
  session,
}: {
  data: TradingData;
  session: Session;
}) {
  const [open, setOpen] = useState(false);
  const rootRef = useRef<HTMLDivElement>(null);
  const panelRef = useRef<HTMLDivElement>(null);
  const snapshot = buildSystemStatus(data);

  useEffect(() => {
    if (!open) return;

    function onPointerDown(event: PointerEvent) {
      if (!rootRef.current?.contains(event.target as Node)) {
        setOpen(false);
      }
    }

    function onKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") setOpen(false);
    }

    document.addEventListener("pointerdown", onPointerDown);
    document.addEventListener("keydown", onKeyDown);
    panelRef.current?.focus();
    return () => {
      document.removeEventListener("pointerdown", onPointerDown);
      document.removeEventListener("keydown", onKeyDown);
    };
  }, [open]);

  return (
    <div className="ns-system" ref={rootRef}>
      <button
        type="button"
        className={cn("ns-system-trigger", `is-${snapshot.tone}`)}
        aria-haspopup="dialog"
        aria-expanded={open}
        aria-label={`系统状态：${snapshot.label}`}
        onClick={() => setOpen((current) => !current)}
      >
        <StatusDot tone={snapshot.tone === "ok" ? "ok" : snapshot.tone === "warn" ? "warn" : snapshot.tone === "bad" ? "bad" : "muted"} pulse={snapshot.tone === "ok"} />
        <span className="ns-system-trigger-label">{snapshot.label}</span>
        <StudioIcon name="chevronDown" size={12} className="ns-system-trigger-chevron" />
      </button>

      {open ? (
        <div
          className="ns-system-popover"
          role="dialog"
          aria-label="System status details"
          tabIndex={-1}
          ref={panelRef}
        >
          <div className="ns-system-popover-head">
            <div>
              <p className="ns-system-popover-eyebrow">SYSTEM STATUS</p>
              <h2>运行状态</h2>
            </div>
            <ModePill mode={session.mode} compact />
          </div>

          <div className="ns-system-rows">
            {snapshot.rows.map((row) => (
              <div className="ns-system-row" key={row.key}>
                <span className="ns-system-row-dot">
                  <StatusDot tone={row.tone === "ok" ? "ok" : row.tone === "warn" ? "warn" : row.tone === "bad" ? "bad" : "muted"} />
                </span>
                <span className="ns-system-row-copy">
                  <strong>{row.label}</strong>
                  <span>{row.detail}</span>
                </span>
                <span className={cn("ns-system-row-value", `is-${row.tone}`)}>{row.value}</span>
              </div>
            ))}
          </div>

          <div className="ns-system-foot">
            <span>
              Market {snapshot.marketAge ?? "—"} · Account {snapshot.accountAge ?? "—"}
            </span>
            <span className="ns-number">
              {data.system?.server_time ? fmtTime(data.system.server_time) : "—"}
            </span>
          </div>
        </div>
      ) : null}
    </div>
  );
}
