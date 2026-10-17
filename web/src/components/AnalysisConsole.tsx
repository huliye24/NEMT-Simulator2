"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import HumanThesisInput from "./HumanThesisInput";
import DecisionLog from "./DecisionLog";
import AIReasoningCard from "./AIReasoningCard";
import CouncilPanel from "./CouncilPanel";
import CouncilHistory from "./CouncilHistory";
import { Card } from "./Card";
import { Memory, notifyMemoryChanged, type ThesisDraft } from "@/lib/memory";
import type {
  AIReasoning,
  Analysis,
  HumanThesis,
  MarketContext,
  Recommendation,
} from "@/lib/types";
import { classNames } from "@/lib/format";

type AnalysisMode = "legacy" | "council";

interface AnalysisConsoleProps {
  /** Seed data from the server-rendered page (mock JSON). */
  initialAnalyses: Analysis[];
  /** Current market snapshot, used to populate the MarketContext on submit. */
  marketContext: MarketContext;
}

/**
 * The interactive half of the Analysis page. The server-rendered
 * page streams in mock analyses + market context; this component
 * merges those with locally-stored analyses (from the Financial
 * Memory layer) and lets the user submit a new HumanThesis that
 * gets persisted, decided, and appended to the Decision Log.
 */
export default function AnalysisConsole({
  initialAnalyses,
  marketContext,
}: AnalysisConsoleProps) {
  const [analyses, setAnalyses] = useState<Analysis[]>(initialAnalyses);
  const [hydrated, setHydrated] = useState(false);
  const [latest, setLatest] = useState<Analysis | null>(
    initialAnalyses[0] ?? null
  );

  // Hydrate from memory on mount, then merge with mock seed.
  useEffect(() => {
    let cancelled = false;
    (async () => {
      const local = await Memory.Analyses.list();
      if (cancelled) return;
      // Local wins on id collisions.
      const merged: Analysis[] = mergeAnalyses(initialAnalyses, local);
      setAnalyses(merged);
      setLatest(merged[0] ?? null);
      setHydrated(true);
    })();
    return () => {
      cancelled = true;
    };
  }, [initialAnalyses]);

  // Draft persistence: restore on mount, write on edit.
  const [draft, setDraft] = useState<ThesisDraft | null>(null);
  const [mode, setMode] = useState<AnalysisMode>("council");
  // Snapshot of the latest thesis for the Council panel. Updated when
  // the user submits; council reads from this.
  const [lastThesis, setLastThesis] = useState<HumanThesis | null>(null);
  useEffect(() => {
    let cancelled = false;
    Memory.ThesisDraft.get().then((d) => {
      if (!cancelled && d) setDraft(d);
    });
    return () => {
      cancelled = true;
    };
  }, []);

  const updateDraft = useCallback(async (next: ThesisDraft) => {
    setDraft(next);
    await Memory.ThesisDraft.set(next);
  }, []);

  const onSubmit = useCallback(
    async (thesis: {
      macroView: string;
      marketJudgment: string;
      riskFactors: string;
      actionPlan: string;
    }) => {
      // Deterministic local "AI": choose an action from the current
      // market context + the user's bias in marketJudgment.
      const reasoning = synthesizeReasoning(thesis, marketContext);
      const id = `local-${Date.now()}`;
      const next: Analysis = {
        id,
        date: new Date().toISOString(),
        humanThesis: {
          macroView: thesis.macroView,
          marketJudgment: thesis.marketJudgment,
          riskFactors: thesis.riskFactors,
          actionPlan: thesis.actionPlan,
        },
        marketContext,
        aiReasoning: reasoning,
        finalDecision: {
          action: reasoning.recommendation,
          size: sizeForRecommendation(reasoning.recommendation),
          entry:
            reasoning.recommendation === "BUY" ||
            reasoning.recommendation === "STRONG_BUY"
              ? marketContext.keyLevels.support * 1.01
              : reasoning.recommendation === "SELL" ||
                reasoning.recommendation === "REDUCE"
              ? marketContext.keyLevels.resistance * 0.99
              : null,
          stopLoss:
            reasoning.recommendation === "BUY" ||
            reasoning.recommendation === "STRONG_BUY"
              ? marketContext.keyLevels.support * 0.98
              : null,
          takeProfit:
            reasoning.recommendation === "BUY" ||
            reasoning.recommendation === "STRONG_BUY"
              ? marketContext.keyLevels.resistance
              : null,
        },
        result: {
          status: "PENDING",
          pnl: null,
          exitPrice: null,
        },
      };

      // Persist to memory and update UI immediately.
      await Memory.Analyses.add(next);
      setAnalyses((prev) => [next, ...prev]);
      setLatest(next);
      setLastThesis(next.humanThesis);
      notifyMemoryChanged();

      // Clear the draft so the next session starts clean.
      await Memory.ThesisDraft.clear();
      setDraft(null);
    },
    [marketContext]
  );

  const totalCount = analyses.length;
  const pendingCount = useMemo(
    () => analyses.filter((a) => a.result.status === "PENDING").length,
    [analyses]
  );

  return (
    <div className="space-y-6">
      <ModeToggle mode={mode} onChange={setMode} />

      <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
        {/* Left: input + active reasoning */}
        <div className="lg:col-span-3 space-y-6">
          <div className="space-y-2">
            <DraftRestoredNotice draft={draft} hydrated={hydrated} />
          </div>
          <HumanThesisInputWithDraft
            draft={draft}
            onDraftChange={updateDraft}
            onSubmit={(thesis) => {
              setLastThesis({
                macroView: thesis.macroView,
                marketJudgment: thesis.marketJudgment,
                riskFactors: thesis.riskFactors,
                actionPlan: thesis.actionPlan,
              });
              return onSubmit(thesis);
            }}
          />

          {mode === "legacy" && latest && (
            <div>
              <SectionLabel
                title="Latest AI Reasoning"
                hint={`${totalCount} total · ${pendingCount} pending`}
              />
              <AIReasoningCard
                reasoning={latest.aiReasoning}
                marketContext={latest.marketContext}
              />
            </div>
          )}

          {mode === "council" && (
            <CouncilPanel thesis={lastThesis} marketContext={marketContext} />
          )}
        </div>

        {/* Right: decision log + memory controls */}
        <div className="lg:col-span-2 space-y-6">
          {mode === "council" && <CouncilHistory />}
          <Card
            title="Financial Memory"
            subtitle="what persists in this browser"
            accent
          >
            <MemorySummary />
          </Card>
          <DecisionLogWithHeader analyses={analyses} />
        </div>
      </div>
    </div>
  );
}

// ---------- mode toggle ----------

function ModeToggle({
  mode,
  onChange,
}: {
  mode: AnalysisMode;
  onChange: (m: AnalysisMode) => void;
}) {
  return (
    <div className="inline-flex rounded-md ring-1 ring-amber-500/20 overflow-hidden">
      <button
        onClick={() => onChange("council")}
        className={classNames(
          "px-4 py-2 text-[11px] uppercase tracking-wider font-semibold transition-all flex items-center gap-2",
          mode === "council"
            ? "bg-amber-500 text-slate-900"
            : "bg-slate-900 text-slate-400 hover:text-slate-200"
        )}
      >
        <span className="w-1.5 h-1.5 rounded-full bg-current" />
        Council · 009
      </button>
      <button
        onClick={() => onChange("legacy")}
        className={classNames(
          "px-4 py-2 text-[11px] uppercase tracking-wider font-semibold transition-all",
          mode === "legacy"
            ? "bg-amber-500 text-slate-900"
            : "bg-slate-900 text-slate-400 hover:text-slate-200"
        )}
      >
        Legacy AI
      </button>
    </div>
  );
}

// ---------- helpers ----------

function DraftRestoredNotice({
  draft,
  hydrated,
}: {
  draft: ThesisDraft | null;
  hydrated: boolean;
}) {
  if (!hydrated || !draft) return null;
  const minutes = Math.max(
    0,
    Math.floor((Date.now() - new Date(draft.updatedAt).getTime()) / 60000)
  );
  return (
    <div className="text-[11px] text-slate-500 flex items-center gap-2">
      <span className="w-1.5 h-1.5 rounded-full bg-amber-400" />
      Restored unsaved thesis from {minutes}m ago
    </div>
  );
}

function SectionLabel({ title, hint }: { title: string; hint?: string }) {
  return (
    <div className="flex items-end justify-between">
      <h2 className="text-sm font-semibold uppercase tracking-[0.14em] text-slate-300">
        {title}
      </h2>
      {hint && <span className="text-[11px] text-slate-500">{hint}</span>}
    </div>
  );
}

function mergeAnalyses(seed: Analysis[], local: Analysis[]): Analysis[] {
  const byId = new Map<string, Analysis>();
  // Seed first so local can override on collisions.
  for (const a of seed) byId.set(a.id, a);
  for (const a of local) byId.set(a.id, a);
  return Array.from(byId.values()).sort(
    (a, b) => new Date(b.date).getTime() - new Date(a.date).getTime()
  );
}

function synthesizeReasoning(
  thesis: { marketJudgment: string; riskFactors: string },
  ctx: MarketContext
): AIReasoning {
  const bullish = /(bullish|breakout|break out|up|buy|long)/i.test(
    thesis.marketJudgment
  );
  const bearish = /(bearish|breakdown|break down|down|sell|short|capitulat)/i.test(
    thesis.marketJudgment
  );

  const recommendation: Recommendation = (() => {
    if (ctx.avgDci >= 70 && bullish) return "STRONG_BUY";
    if (bullish && ctx.avgDci >= 50) return "BUY";
    if (bearish && ctx.avgDci <= 40) return "SELL";
    if (bearish) return "REDUCE";
    return "HOLD";
  })();

  const confidence = Math.max(
    30,
    Math.min(
      95,
      Math.round(
        ctx.avgDci * 0.55 +
          (thesis.marketJudgment.length > 30 ? 25 : 10) +
          (recommendation === "STRONG_BUY" || recommendation === "SELL" ? 5 : 0)
      )
    )
  );

  const riskLevel: AIReasoning["riskAssessment"]["level"] =
    confidence >= 75 ? "LOW" : confidence >= 55 ? "MEDIUM" : "HIGH";

  const riskFactors = thesis.riskFactors
    ? thesis.riskFactors
        .split(/[,，\n]/)
        .map((s) => s.trim())
        .filter(Boolean)
    : [];

  return {
    marketInterpretation: `Phase ${ctx.phase} with avg DCI ${ctx.avgDci.toFixed(
      1
    )}. User thesis leans ${bullish ? "bullish" : bearish ? "bearish" : "neutral"}.`,
    riskAssessment: {
      level: riskLevel,
      factors:
        riskFactors.length > 0
          ? riskFactors
          : [
              `Phase ${ctx.phase} carries typical transition risk`,
              `Sentiment currently ${ctx.sentiment}`,
            ],
    },
    recommendation,
    confidence,
    reasoning: [
      `Avg DCI ${ctx.avgDci.toFixed(1)} → ${ctx.avgDci >= 60 ? "high" : ctx.avgDci >= 45 ? "medium" : "low"} directional conviction`,
      `Phase ${ctx.phase} → ${
        ctx.phase === "MARKUP" || ctx.phase === "RECOVERY"
          ? "trend-following bias"
          : ctx.phase === "MARKDOWN" || ctx.phase === "DISTRIBUTION"
          ? "defensive bias"
          : "wait for confirmation"
      }`,
      `Sentiment ${ctx.sentiment} → ${
        ctx.sentiment === "BULLISH" ? "supports longs" : ctx.sentiment === "BEARISH" ? "supports cuts" : "neutral"
      }`,
      `Human thesis aligns with ${
        recommendation === "STRONG_BUY" || recommendation === "BUY"
          ? "long"
          : recommendation === "SELL" || recommendation === "REDUCE"
          ? "short"
          : "wait"
      } bias`,
    ],
  };
}

function sizeForRecommendation(rec: Recommendation): string {
  switch (rec) {
    case "STRONG_BUY":
      return "60%";
    case "BUY":
      return "40%";
    case "REDUCE":
      return "30%";
    case "SELL":
      return "100%";
    default:
      return "0%";
  }
}

// ---------- subcomponents ----------

function HumanThesisInputWithDraft({
  draft,
  onDraftChange,
  onSubmit,
}: {
  draft: ThesisDraft | null;
  onDraftChange: (d: ThesisDraft) => void | Promise<void>;
  onSubmit: (t: {
    macroView: string;
    marketJudgment: string;
    riskFactors: string;
    actionPlan: string;
  }) => void | Promise<void>;
}) {
  const [macro, setMacro] = useState(draft?.macroView ?? "");
  const [judgment, setJudgment] = useState(draft?.marketJudgment ?? "");
  const [risk, setRisk] = useState(draft?.riskFactors ?? "");
  const [plan, setPlan] = useState(draft?.actionPlan ?? "");

  // When a draft is restored after mount, hydrate the fields.
  useEffect(() => {
    if (draft) {
      setMacro(draft.macroView);
      setJudgment(draft.marketJudgment);
      setRisk(draft.riskFactors);
      setPlan(draft.actionPlan);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [draft?.updatedAt]);

  const persist = (next: {
    macroView: string;
    marketJudgment: string;
    riskFactors: string;
    actionPlan: string;
  }) => {
    onDraftChange({ ...next, updatedAt: new Date().toISOString() });
  };

  return (
    <CustomThesisInput
      values={{
        macroView: macro,
        marketJudgment: judgment,
        riskFactors: risk,
        actionPlan: plan,
      }}
      onChange={(patch) => {
        const next = {
          macroView: patch.macroView ?? macro,
          marketJudgment: patch.marketJudgment ?? judgment,
          riskFactors: patch.riskFactors ?? risk,
          actionPlan: patch.actionPlan ?? plan,
        };
        if (patch.macroView !== undefined) setMacro(patch.macroView);
        if (patch.marketJudgment !== undefined) setJudgment(patch.marketJudgment);
        if (patch.riskFactors !== undefined) setRisk(patch.riskFactors);
        if (patch.actionPlan !== undefined) setPlan(patch.actionPlan);
        persist(next);
      }}
      onSubmit={async () => {
        await onSubmit({
          macroView: macro,
          marketJudgment: judgment,
          riskFactors: risk,
          actionPlan: plan,
        });
      }}
    />
  );
}

function CustomThesisInput({
  values,
  onChange,
  onSubmit,
}: {
  values: {
    macroView: string;
    marketJudgment: string;
    riskFactors: string;
    actionPlan: string;
  };
  onChange: (patch: Partial<typeof values>) => void;
  onSubmit: () => void | Promise<void>;
}) {
  const isValid = !!values.macroView && !!values.marketJudgment;
  return (
    <div className="nemt-panel p-6">
      <div className="flex items-center gap-2 mb-6">
        <span className="w-2 h-2 bg-amber-400 rounded-full" />
        <h2 className="text-lg font-semibold text-white">Human Thesis</h2>
        <span className="text-xs text-slate-500 ml-2">
          Saved automatically · Submit when ready
        </span>
      </div>
      <Field
        label="Macro View"
        required
        value={values.macroView}
        onChange={(v) => onChange({ macroView: v })}
        placeholder="e.g., Fed rate cut expectations rising, liquidity improving..."
      />
      <Field
        label="Market Judgment"
        required
        value={values.marketJudgment}
        onChange={(v) => onChange({ marketJudgment: v })}
        placeholder="e.g., BTC breaking key resistance, trend turning bullish..."
      />
      <Field
        label="Risk Factors"
        value={values.riskFactors}
        onChange={(v) => onChange({ riskFactors: v })}
        placeholder="e.g., Short-term overbought, potential pullback..."
        minHeight={60}
      />
      <Field
        label="Action Plan"
        value={values.actionPlan}
        onChange={(v) => onChange({ actionPlan: v })}
        placeholder="e.g., Scale in gradually, set stop loss at..."
        minHeight={60}
      />
      <button
        onClick={onSubmit}
        disabled={!isValid}
        className={classNames(
          "w-full py-3 rounded-lg font-medium transition-all mt-4",
          "bg-linear-to-r from-amber-500 to-amber-600 text-white",
          "hover:from-amber-400 hover:to-amber-500",
          "disabled:opacity-50 disabled:cursor-not-allowed"
        )}
      >
        Commit to Memory & Generate Decision
      </button>
    </div>
  );
}

function Field({
  label,
  value,
  onChange,
  placeholder,
  required,
  minHeight = 80,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
  required?: boolean;
  minHeight?: number;
}) {
  return (
    <div className="mb-4">
      <label className="block text-xs text-slate-500 uppercase tracking-wider mb-2">
        {label} {required && <span className="text-amber-400">*</span>}
      </label>
      <textarea
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="w-full bg-nemt-bg-deep border border-nemt-border rounded-lg px-4 py-3 text-sm text-white placeholder:text-slate-600 focus:outline-none focus:border-amber-500/50 resize-none"
        style={{ minHeight }}
      />
    </div>
  );
}

function DecisionLogWithHeader({ analyses }: { analyses: Analysis[] }) {
  return (
    <Card
      title="Decision Log"
      subtitle="locally-stored + mock history"
      accent
    >
      <div className="-m-2">
        <div className="px-2">
          <DecisionLog analyses={analyses.slice(0, 6)} />
        </div>
      </div>
    </Card>
  );
}

function MemorySummary() {
  const { analyses, journal, pinned, verdicts, ready } = useMemoryState();
  return (
    <ul className="space-y-2 text-[13px]">
      <Row label="Analyses" value={analyses} ready={ready} />
      <Row label="Council verdicts" value={verdicts} ready={ready} />
      <Row label="Journal entries" value={journal} ready={ready} />
      <Row label="Pinned" value={pinned} ready={ready} />
      <li className="pt-2 mt-2 border-t border-nemt-border">
        <button
          onClick={async () => {
            if (!confirm("Forget all locally-stored Financial Memory?")) return;
            await Memory.Forget.all();
            window.location.reload();
          }}
          className="text-[11px] uppercase tracking-wider text-rose-300 hover:text-rose-200 transition-colors"
        >
          Forget Everything →
        </button>
      </li>
    </ul>
  );
}

function Row({
  label,
  value,
  ready,
}: {
  label: string;
  value: number;
  ready: boolean;
}) {
  return (
    <li className="flex items-center justify-between">
      <span className="text-slate-400">{label}</span>
      <span className="nemt-mono text-slate-100">
        {ready ? value : "…"}
      </span>
    </li>
  );
}

// Local re-implementation of useMemoryCounts that doesn't trigger
// re-renders from internal state changes outside this component.
function useMemoryState() {
  const [s, setS] = useState({
    analyses: 0,
    journal: 0,
    pinned: 0,
    verdicts: 0,
    ready: false,
  });
  useEffect(() => {
    let cancelled = false;
    const refresh = async () => {
      const sum = await Memory.Stats.summary();
      if (!cancelled) setS({ ...sum, ready: true });
    };
    refresh();
    const onChange = () => refresh();
    window.addEventListener("nemt:memory-changed", onChange);
    return () => {
      cancelled = true;
      window.removeEventListener("nemt:memory-changed", onChange);
    };
  }, []);
  return s;
}
