import { ageLabel } from "@/lib/trade/format";
import type { TradingData } from "../../useTradingData";

export type StatusTone = "ok" | "warn" | "bad" | "muted";

export interface SystemStatusRow {
  key: string;
  label: string;
  value: string;
  detail: string;
  tone: StatusTone;
}

export interface SystemStatusSnapshot {
  label: "Connected" | "Degraded" | "Offline" | "Connecting";
  tone: StatusTone;
  rows: SystemStatusRow[];
  marketAge: string | null;
  accountAge: string | null;
}

function marketRow(data: TradingData): SystemStatusRow {
  if (!data.online) {
    return {
      key: "market",
      label: "Market Data",
      value: "Offline",
      detail: "No network connection",
      tone: "bad",
    };
  }
  if (data.feedError) {
    return {
      key: "market",
      label: "Market Data",
      value: "Degraded",
      detail: data.feedError,
      tone: "warn",
    };
  }
  if (!data.ticker) {
    return {
      key: "market",
      label: "Market Data",
      value: "Waiting",
      detail: "No ticker snapshot yet",
      tone: "muted",
    };
  }
  if (data.ticker.stale) {
    return {
      key: "market",
      label: "Market Data",
      value: "Delayed",
      detail: `${data.ticker.source === "demo" ? "Simulated feed" : "Binance"} · ${ageLabel(data.ticker.fetched_at)}`,
      tone: "warn",
    };
  }
  return {
    key: "market",
    label: "Market Data",
    value: "Live",
    detail: `${data.ticker.source === "demo" ? "Simulated feed" : "Binance"} · ${ageLabel(data.ticker.fetched_at)}`,
    tone: "ok",
  };
}

function accountRow(data: TradingData): SystemStatusRow {
  if (!data.balances) {
    return {
      key: "account",
      label: "Account Sync",
      value: "Waiting",
      detail: "No account snapshot yet",
      tone: "muted",
    };
  }
  if (data.balances.account_status === "NOT_CONFIGURED") {
    return {
      key: "account",
      label: "Account Sync",
      value: "Not configured",
      detail: data.balances.note ?? "No account configured",
      tone: "warn",
    };
  }
  if (!data.balances.connected) {
    return {
      key: "account",
      label: "Account Sync",
      value: "Error",
      detail: data.balances.note ?? data.balances.account_status,
      tone: "bad",
    };
  }
  if (data.balances.stale) {
    return {
      key: "account",
      label: "Account Sync",
      value: "Stale",
      detail: data.balances.fetched_at
        ? `${ageLabel(data.balances.fetched_at)} · ${data.balances.source}`
        : "Snapshot out of date",
      tone: "warn",
    };
  }
  return {
    key: "account",
    label: "Account Sync",
    value: "Synced",
    detail: `${data.balances.source === "demo" ? "DEMO ledger" : data.balances.source} · ${ageLabel(data.balances.fetched_at)}`,
    tone: "ok",
  };
}

export function buildSystemStatus(data: TradingData): SystemStatusSnapshot {
  const api: SystemStatusRow = !data.online
    ? {
        key: "api",
        label: "NEMT Cloud API",
        value: "Offline",
        detail: "Network unreachable",
        tone: "bad",
      }
    : data.coreError
      ? {
          key: "api",
          label: "NEMT Cloud API",
          value: "Degraded",
          detail: data.coreError,
          tone: "warn",
        }
      : data.system
        ? {
            key: "api",
            label: "NEMT Cloud API",
            value: "Connected",
            detail: `v${data.system.version} · ${data.system.mode}`,
            tone: "ok",
          }
        : {
            key: "api",
            label: "NEMT Cloud API",
            value: "Connecting",
            detail: "Waiting for system status",
            tone: "muted",
          };

  const market = marketRow(data);
  const account = accountRow(data);

  const execution: SystemStatusRow = {
    key: "execution",
    label: "Execution Service",
    value: "Not connected",
    detail: "Automated execution API is not connected",
    tone: "muted",
  };

  const freshness: SystemStatusRow = (() => {
    if (!data.online) {
      return {
        key: "freshness",
        label: "Data Freshness",
        value: "Offline",
        detail: "No live timestamps",
        tone: "bad",
      };
    }
    if (!data.ticker) {
      return {
        key: "freshness",
        label: "Data Freshness",
        value: "Waiting",
        detail: "Market timestamp unavailable",
        tone: "muted",
      };
    }
    if (data.ticker.stale || data.balances?.stale) {
      return {
        key: "freshness",
        label: "Data Freshness",
        value: "Delayed",
        detail: `Market ${ageLabel(data.ticker.fetched_at)}${data.balances ? ` · Account ${ageLabel(data.balances.fetched_at)}` : ""}`,
        tone: "warn",
      };
    }
    return {
      key: "freshness",
      label: "Data Freshness",
      value: "Fresh",
      detail: `Market ${ageLabel(data.ticker.fetched_at)}${data.balances ? ` · Account ${ageLabel(data.balances.fetched_at)}` : ""}`,
      tone: "ok",
    };
  })();

  const degraded = [api, market, account, freshness].some(
    (row) => row.tone === "warn" || row.tone === "bad"
  );
  const connecting = !data.system || !data.ticker || !data.balances;
  const offline = !data.online;

  return {
    label: offline ? "Offline" : degraded ? "Degraded" : connecting ? "Connecting" : "Connected",
    tone: offline ? "bad" : degraded ? "warn" : connecting ? "muted" : "ok",
    rows: [api, market, account, execution, freshness],
    marketAge: data.ticker ? ageLabel(data.ticker.fetched_at) : null,
    accountAge: data.balances ? ageLabel(data.balances.fetched_at) : null,
  };
}
