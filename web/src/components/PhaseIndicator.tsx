"use client";

import type { MarketPhase } from "@/lib/types";

interface PhaseIndicatorProps {
  phase: MarketPhase;
  size?: "sm" | "md" | "lg";
}

const phaseConfig: Record<MarketPhase, { label: string; color: string; bg: string }> = {
  ACCUMULATION: {
    label: "A",
    color: "text-emerald-400",
    bg: "bg-emerald-500/10 border-emerald-500/30",
  },
  MARKUP: {
    label: "B",
    color: "text-amber-400",
    bg: "bg-amber-500/10 border-amber-500/30",
  },
  DISTRIBUTION: {
    label: "C",
    color: "text-orange-400",
    bg: "bg-orange-500/10 border-orange-500/30",
  },
  MARKDOWN: {
    label: "D",
    color: "text-red-400",
    bg: "bg-red-500/10 border-red-500/30",
  },
  RECOVERY: {
    label: "R",
    color: "text-blue-400",
    bg: "bg-blue-500/10 border-blue-500/30",
  },
  UNKNOWN: {
    label: "?",
    color: "text-slate-400",
    bg: "bg-slate-500/10 border-slate-500/30",
  },
};

export default function PhaseIndicator({ phase, size = "md" }: PhaseIndicatorProps) {
  const config = phaseConfig[phase] || phaseConfig.UNKNOWN;

  const sizeClasses = {
    sm: "w-6 h-6 text-xs",
    md: "w-8 h-8 text-sm",
    lg: "w-10 h-10 text-base",
  };

  return (
    <div
      className={`
        inline-flex items-center justify-center
        rounded-lg border font-mono font-bold
        ${config.bg} ${config.color}
        ${sizeClasses[size]}
      `}
      title={phase}
    >
      {config.label}
    </div>
  );
}
