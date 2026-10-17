"use client";

import { useCallback, useMemo, useRef, useState } from "react";
import { Card } from "./Card";
import { runCouncil, COUNCIL_AGENTS, getAgent, RECOMMENDATION_LABELS } from "@/lib/council";
import {
  Memory,
  notifyMemoryChanged,
} from "@/lib/memory";
import type {
  CouncilVerdict,
  HumanThesis,
  MarketContext,
  Recommendation,
} from "@/lib/types";
import { classNames, formatRelativeTime } from "@/lib/format";

const REC_TONE: Record<Recommendation, string> = {
  STRONG_BUY: "text-emerald-300 bg-emerald-500/10 ring-emerald-500/30",
  BUY: "text-emerald-300 bg-emerald-500/10 ring-emerald-500/20",
  HOLD: "text-slate-300 bg-slate-500/10 ring-slate-500/30",
  REDUCE: "text-amber-300 bg-amber-500/10 ring-amber-500/30",
  SELL: "text-rose-300 bg-rose-500/10 ring-rose-500/30",
  WAIT: "text-slate-300 bg-slate-500/10 ring-slate-500/20",
};

interface CouncilPanelProps {
  thesis: HumanThesis | null;
  marketContext: MarketContext;
}

/**
 * Renders the council session — 5 proposals, contrarian-led
 * challenges, revisions, and the chairman's consensus. The body
 * animates in stages so the operator can follow the debate.
 */
export default function CouncilPanel({
  thesis,
  marketContext,
}: CouncilPanelProps) {
  const [verdict, setVerdict] = useState<CouncilVerdict | null>(null);
  const [isRunning, setIsRunning] = useState(false);
  const [stage, setStage] = useState<
    "idle" | "proposals" | "challenges" | "revisions" | "consensus"
  >("idle");
  const cancelRef = useRef(false);

  const canRun = !!thesis && !isRunning;

  const start = useCallback(async () => {
    if (!thesis) return;
    cancelRef.current = false;
    setIsRunning(true);
    setVerdict(null);
    setStage("proposals");

    // We run the council in one shot (it's already async-yielded
    // internally), but reveal stages by checking the partial
    // transcript as it grows. To keep this simple, we run fully
    // and then animate. For longer sessions this would be a
    // streamed generator.
    const startTs = Date.now();
    const result = await runCouncil(thesis, marketContext, {
      perAgentLatencyMs: 0,
    });
    if (cancelRef.current) {
      setIsRunning(false);
      setStage("idle");
      return;
    }
    void startTs;

    // Reveal stages sequentially for visual feedback.
    setStage("proposals");
    await wait(150);
    setStage("challenges");
    await wait(150);
    setStage("revisions");
    await wait(150);
    setStage("consensus");
    setVerdict(result);

    await Memory.Council.add(result);
    notifyMemoryChanged();
    setIsRunning(false);
  }, [thesis, marketContext]);

  const cancel = () => {
    cancelRef.current = true;
  };

  const proposals = verdict?.transcript.proposals ?? [];
  const challenges = verdict?.transcript.challenges ?? [];
  const revisions = verdict?.transcript.revisions ?? [];

  return (
    <Card
      accent
      title="Multi-Agent Council"
      subtitle="5 agents · debate · consensus"
      rightSlot={<CouncilStatusBadge running={isRunning} stage={stage} />}
    >
      <div className="flex items-center gap-3 mb-4">
        <button
          onClick={start}
          disabled={!canRun}
          className={classNames(
            "px-4 py-2 rounded-md text-[12px] uppercase tracking-wider font-semibold transition-all",
            canRun
              ? "bg-amber-500 text-slate-900 hover:bg-amber-400"
              : "bg-slate-800 text-slate-500 cursor-not-allowed"
          )}
        >
          {verdict ? "Reconvene Council" : "Convene Council"}
        </button>
        {isRunning && (
          <button
            onClick={cancel}
            className="text-[11px] uppercase tracking-wider text-rose-300 hover:text-rose-200"
          >
            Cancel
          </button>
        )}
        {verdict && (
          <span className="ml-auto text-[11px] text-slate-500">
            Decided {formatRelativeTime(verdict.decidedAt)} ·{" "}
            {verdict.durationMs}ms
          </span>
        )}
      </div>

      {!thesis && (
        <div className="text-[12px] text-slate-500 italic">
          Submit a Human Thesis above to convene the council.
        </div>
      )}

      {/* Roster strip */}
      <div className="flex flex-wrap gap-2 mb-4">
        {COUNCIL_AGENTS.map((agent) => {
          const proposal = proposals.find((p) => p.agent === agent.id);
          const revealed = !!proposal && stage !== "idle";
          return (
            <AgentChip
              key={agent.id}
              agent={agent}
              proposal={proposal}
              revealed={revealed}
            />
          );
        })}
      </div>

      {/* Stage-by-stage transcript */}
      {verdict && (
        <div className="space-y-4">
          <StageSection
            label="1 · Proposals"
            visible={stage !== "idle"}
          >
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {proposals.map((p) => (
                <ProposalCard key={p.agent} proposal={p} />
              ))}
            </div>
          </StageSection>

          <StageSection label="2 · Challenges" visible={stage !== "idle"}>
            {challenges.length === 0 ? (
              <Empty text="No challenges raised — quiet session." />
            ) : (
              <ul className="space-y-2">
                {challenges.map((c, i) => (
                  <ChallengeRow key={i} challenge={c} />
                ))}
              </ul>
            )}
          </StageSection>

          <StageSection label="3 · Revisions" visible={stage !== "idle"}>
            <ul className="space-y-1.5 text-[12px]">
              {revisions.map((r) => (
                <li
                  key={r.agent}
                  className="flex items-start gap-2 text-slate-400"
                >
                  <span
                    className="font-semibold text-slate-200 uppercase tracking-wider text-[10px] mt-0.5"
                    style={{ color: getAgent(r.agent).color }}
                  >
                    {r.agent}
                  </span>
                  <span className="flex-1">{r.note}</span>
                  {r.confidence !== undefined && (
                    <span className="nemt-mono text-amber-300">
                      → {r.confidence}%
                    </span>
                  )}
                </li>
              ))}
            </ul>
          </StageSection>

          <StageSection
            label="4 · Consensus"
            visible={stage === "consensus" || stage === "idle"}
          >
            <ConsensusSummary verdict={verdict} />
          </StageSection>
        </div>
      )}
    </Card>
  );
}

// ---------- helpers ----------

function wait(ms: number): Promise<void> {
  return new Promise((r) => setTimeout(r, ms));
}

// ---------- subcomponents ----------

function CouncilStatusBadge({
  running,
  stage,
}: {
  running: boolean;
  stage: string;
}) {
  const label = !running
    ? stage === "idle"
      ? "standby"
      : "decided"
    : stage;
  return (
    <span
      className={classNames(
        "text-[10px] uppercase tracking-wider px-2 py-1 rounded ring-1",
        running
          ? "bg-blue-500/10 text-blue-300 ring-blue-500/30"
          : stage === "idle"
          ? "bg-slate-800 text-slate-400 ring-slate-700"
          : "bg-emerald-500/10 text-emerald-300 ring-emerald-500/30"
      )}
    >
      <span className="inline-flex items-center gap-1.5">
        <span
          className={classNames(
            "w-1.5 h-1.5 rounded-full",
            running
              ? "bg-blue-400 animate-pulse"
              : stage === "idle"
              ? "bg-slate-500"
              : "bg-emerald-400"
          )}
        />
        {label}
      </span>
    </span>
  );
}

function AgentChip({
  agent,
  proposal,
  revealed,
}: {
  agent: (typeof COUNCIL_AGENTS)[number];
  proposal?: { recommendation: Recommendation; confidence: number };
  revealed: boolean;
}) {
  return (
    <div
      className={classNames(
        "flex items-center gap-2 px-2.5 py-1.5 rounded-md ring-1 transition-all",
        revealed
          ? "bg-slate-900 ring-amber-500/20"
          : "bg-slate-900/40 ring-slate-700/40"
      )}
    >
      <span
        className="w-2 h-2 rounded-full shrink-0"
        style={{ backgroundColor: agent.color }}
      />
      <div className="flex flex-col leading-tight">
        <span className="text-[11px] font-semibold text-slate-200">
          {agent.name}
        </span>
        <span className="text-[9px] uppercase tracking-wider text-slate-500">
          w={agent.weight.toFixed(2)}
        </span>
      </div>
      {proposal && (
        <span
          className={classNames(
            "ml-2 text-[9px] uppercase tracking-wider px-1.5 py-0.5 rounded ring-1",
            REC_TONE[proposal.recommendation]
          )}
        >
          {RECOMMENDATION_LABELS[proposal.recommendation]} ·{" "}
          {proposal.confidence}%
        </span>
      )}
    </div>
  );
}

function StageSection({
  label,
  visible,
  children,
}: {
  label: string;
  visible: boolean;
  children: React.ReactNode;
}) {
  if (!visible) return null;
  return (
    <section className="space-y-2">
      <h4 className="text-[10px] uppercase tracking-[0.18em] text-slate-500">
        {label}
      </h4>
      {children}
    </section>
  );
}

function ProposalCard({
  proposal,
}: {
  proposal: { agent: import("@/lib/types").AgentProposal["agent"]; recommendation: Recommendation; confidence: number; rationale: string; evidence: string[] };
}) {
  const agent = getAgent(proposal.agent);
  return (
    <div className="bg-slate-900/60 rounded-md p-3 ring-1 ring-slate-800">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <span
            className="w-2 h-2 rounded-full"
            style={{ backgroundColor: agent.color }}
          />
          <span className="text-[12px] font-semibold text-slate-100">
            {agent.name}
          </span>
          <span className="text-[10px] uppercase tracking-wider text-slate-500">
            {agent.tagline}
          </span>
        </div>
        <span
          className={classNames(
            "text-[10px] uppercase tracking-wider px-2 py-0.5 rounded ring-1",
            REC_TONE[proposal.recommendation]
          )}
        >
          {RECOMMENDATION_LABELS[proposal.recommendation]} · {proposal.confidence}%
        </span>
      </div>
      <p className="text-[12px] text-slate-300 leading-relaxed">
        {proposal.rationale}
      </p>
      <ul className="mt-2 space-y-1">
        {proposal.evidence.map((e, i) => (
          <li
            key={i}
            className="text-[11px] text-slate-500 pl-3 relative before:content-['–'] before:absolute before:left-0 before:text-amber-500/50"
          >
            {e}
          </li>
        ))}
      </ul>
    </div>
  );
}

function ChallengeRow({
  challenge,
}: {
  challenge: import("@/lib/types").AgentChallenge;
}) {
  const fromColor = getAgent(challenge.from).color;
  const toColor = getAgent(challenge.to).color;
  const agree = challenge.vote === "AGREE";
  return (
    <li
      className={classNames(
        "flex items-start gap-2 text-[12px] px-3 py-2 rounded-md ring-1",
        agree
          ? "bg-emerald-500/5 ring-emerald-500/20"
          : "bg-rose-500/5 ring-rose-500/20"
      )}
    >
      <span
        className="text-[10px] uppercase tracking-wider font-semibold"
        style={{ color: fromColor }}
      >
        {challenge.from}
      </span>
      <span
        className={classNames(
          "text-[10px] uppercase tracking-wider",
          agree ? "text-emerald-300" : "text-rose-300"
        )}
      >
        {challenge.vote === "AGREE" ? "agrees with" : "challenges"}
      </span>
      <span
        className="text-[10px] uppercase tracking-wider font-semibold"
        style={{ color: toColor }}
      >
        {challenge.to}
      </span>
      <span className="flex-1 text-slate-300 text-[12px]">
        — {challenge.statement}
      </span>
    </li>
  );
}

function Empty({ text }: { text: string }) {
  return (
    <div className="text-[12px] text-slate-500 italic px-3 py-2">
      {text}
    </div>
  );
}

function ConsensusSummary({ verdict }: { verdict: CouncilVerdict }) {
  const distribution = Object.entries(verdict.consensus.distribution)
    .map(([rec, w]) => ({ rec: rec as Recommendation, w }))
    .filter((d) => d.w > 0)
    .sort((a, b) => b.w - a.w);
  const totalWeight = distribution.reduce((s, d) => s + d.w, 0) || 1;

  return (
    <div className="bg-slate-900/60 rounded-md p-4 ring-1 ring-amber-500/20 space-y-3">
      <div className="flex items-center justify-between flex-wrap gap-2">
        <div className="flex items-center gap-2">
          <span className="text-[10px] uppercase tracking-[0.18em] text-slate-500">
            Chairman
          </span>
          <span
            className={classNames(
              "text-base font-bold px-3 py-1.5 rounded-md ring-1",
              REC_TONE[verdict.consensus.winner]
            )}
          >
            {RECOMMENDATION_LABELS[verdict.consensus.winner]}
          </span>
          <span className="text-[11px] text-slate-400">
            @ {verdict.confidence}% confidence
          </span>
        </div>
        <div className="text-[11px] text-slate-500 flex items-center gap-2">
          <span className="uppercase tracking-wider">Size</span>
          <span className="nemt-mono text-amber-300">{verdict.size}</span>
        </div>
      </div>

      {verdict.outcome === "OVERRIDE" && (
        <div className="text-[11px] text-amber-300 bg-amber-500/5 ring-1 ring-amber-500/20 rounded px-3 py-2">
          Chairman Override — vote distribution was too close to call;
          defaulted to HOLD.
        </div>
      )}

      <div>
        <div className="text-[10px] uppercase tracking-[0.18em] text-slate-500 mb-2">
          Vote Distribution
        </div>
        <ul className="space-y-1.5">
          {distribution.map((d) => {
            const pct = (d.w / totalWeight) * 100;
            return (
              <li
                key={d.rec}
                className="flex items-center gap-3 text-[12px]"
              >
                <span
                  className={classNames(
                    "w-24 text-[10px] uppercase tracking-wider px-1.5 py-0.5 rounded ring-1",
                    REC_TONE[d.rec]
                  )}
                >
                  {RECOMMENDATION_LABELS[d.rec]}
                </span>
                <div className="flex-1 h-2 bg-slate-800 rounded-full overflow-hidden">
                  <div
                    className={classNames(
                      "h-full transition-all",
                      d.rec === verdict.consensus.winner
                        ? "bg-amber-400"
                        : "bg-slate-500"
                    )}
                    style={{ width: `${pct}%` }}
                  />
                </div>
                <span className="nemt-mono text-[11px] text-slate-400 w-16 text-right">
                  {(d.w * 100).toFixed(1)}%
                </span>
              </li>
            );
          })}
        </ul>
      </div>

      <div className="grid grid-cols-3 gap-3 pt-3 border-t border-slate-800 text-[11px]">
        <Stat label="Winning weight" value={`${(verdict.consensus.weight * 100).toFixed(1)}%`} />
        <Stat label="Leading agent" value={`@ ${verdict.consensus.leadingConfidence}%`} />
        <Stat
          label="Outcome"
          value={verdict.outcome.toLowerCase()}
          tone={verdict.outcome === "CONSENSUS" ? "up" : "warn"}
        />
      </div>
    </div>
  );
}

function Stat({
  label,
  value,
  tone = "neutral",
}: {
  label: string;
  value: string;
  tone?: "up" | "down" | "warn" | "neutral";
}) {
  const cls =
    tone === "up"
      ? "text-emerald-300"
      : tone === "down"
      ? "text-rose-300"
      : tone === "warn"
      ? "text-amber-300"
      : "text-slate-200";
  return (
    <div>
      <div className="text-[10px] uppercase tracking-wider text-slate-500">
        {label}
      </div>
      <div className={classNames("nemt-mono font-semibold text-[13px]", cls)}>
        {value}
      </div>
    </div>
  );
}
