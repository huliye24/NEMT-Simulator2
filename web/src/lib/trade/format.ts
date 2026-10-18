export function cn(...values: Array<string | false | null | undefined>): string {
  return values.filter(Boolean).join(" ");
}

const priceFormatter = new Intl.NumberFormat("en-US", {
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});

const compactFormatter = new Intl.NumberFormat("en-US", {
  notation: "compact",
  maximumFractionDigits: 1,
});

export function num(value: string | number | null | undefined): number {
  if (value === null || value === undefined || value === "") return 0;
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : 0;
}

export function fmtPrice(value: string | number | null | undefined): string {
  const parsed = num(value);
  if (!parsed) return "—";
  if (parsed >= 1000) return priceFormatter.format(parsed);
  return parsed.toLocaleString("en-US", { maximumFractionDigits: 6 });
}

export function fmtUSDT(value: string | number | null | undefined): string {
  const parsed = num(value);
  if (!parsed) return "0.00";
  return priceFormatter.format(parsed);
}

export function fmtCompact(value: string | number | null | undefined): string {
  const parsed = num(value);
  if (!parsed) return "—";
  return compactFormatter.format(parsed);
}

export function fmtQty(value: string | number | null | undefined): string {
  if (value === null || value === undefined || value === "") return "—";
  const text = String(value);
  if (!text.includes(".")) return text;
  return text.replace(/0+$/, "").replace(/\.$/, "");
}

export function fmtPct(value: string | number | null | undefined): string {
  const parsed = num(value);
  const sign = parsed > 0 ? "+" : "";
  return `${sign}${parsed.toFixed(2)}%`;
}

export function fmtTime(iso: string | null | undefined): string {
  if (!iso) return "—";
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return "—";
  return date.toLocaleString("zh-CN", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: false,
  });
}

export function ageLabel(fetchedAt: string | null | undefined): string {
  if (!fetchedAt) return "未知";
  const seconds = Math.max(0, Math.floor((Date.now() - new Date(fetchedAt).getTime()) / 1000));
  if (seconds < 3) return "刚刚";
  if (seconds < 60) return `${seconds}s 前`;
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m 前`;
  return `${Math.floor(seconds / 3600)}h 前`;
}

export function roundDown(value: number, decimals: number): number {
  if (!Number.isFinite(value) || value <= 0) return 0;
  const factor = 10 ** decimals;
  return Math.floor(value * factor) / factor;
}

export function isoToClock(iso: string | null | undefined): string {
  if (!iso) return "--:--:--";
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return "--:--:--";
  return date.toLocaleTimeString("zh-CN", { hour12: false });
}

export function fmtNumber(value: string | number | null | undefined): string {
  const parsed = num(value);
  if (!parsed) return "0";
  return parsed.toLocaleString("en-US", { maximumFractionDigits: 2 });
}

export function formatTime(iso: string | number | null | undefined): string {
  if (!iso) return "—";
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return "—";
  return date.toLocaleString("zh-CN", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  });
}
