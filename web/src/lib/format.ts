// NEMT UI — formatting & display helpers

export function formatPrice(value: number, opts?: { digits?: number }): string {
  const digits =
    opts?.digits ?? (value >= 1000 ? 2 : value >= 1 ? 4 : 4);
  return value.toLocaleString("en-US", {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  });
}

export function formatPercent(value: number, opts?: { digits?: number; signed?: boolean }): string {
  const digits = opts?.digits ?? 2;
  const signed = opts?.signed ?? true;
  const sign = signed && value > 0 ? "+" : "";
  return `${sign}${value.toFixed(digits)}%`;
}

export function formatUsd(value: number, opts?: { compact?: boolean }): string {
  if (opts?.compact) {
    const abs = Math.abs(value);
    if (abs >= 1e9) return `$${(value / 1e9).toFixed(2)}B`;
    if (abs >= 1e6) return `$${(value / 1e6).toFixed(2)}M`;
    if (abs >= 1e3) return `$${(value / 1e3).toFixed(2)}K`;
  }
  return `$${value.toLocaleString("en-US", { maximumFractionDigits: 2 })}`;
}

export function formatRelativeTime(iso: string): string {
  const then = new Date(iso).getTime();
  const now = Date.now();
  const diff = Math.max(0, now - then);
  const sec = Math.floor(diff / 1000);
  if (sec < 60) return `${sec}s ago`;
  const min = Math.floor(sec / 60);
  if (min < 60) return `${min}m ago`;
  const hr = Math.floor(min / 60);
  if (hr < 24) return `${hr}h ago`;
  const day = Math.floor(hr / 24);
  return `${day}d ago`;
}

export function classNames(...parts: Array<string | false | null | undefined>): string {
  return parts.filter(Boolean).join(" ");
}

/** Color band for a DCI value 0-100. */
export function dciColor(value: number): "up" | "warn" | "down" | "neutral" {
  if (value >= 65) return "up";
  if (value >= 50) return "warn";
  if (value >= 35) return "neutral";
  return "down";
}
