// NEMT Web Alpha 009 — Multi-Agent Financial Council
// ---------------------------------------------------------------
// Five agents, each with a distinct persona and voting weight.
// The council debates a HumanThesis against a MarketContext, then
// the chairman resolves a weighted consensus. Deterministic and
// offline: every input is reproducible, every output is auditable.
//
// Today: heuristics that lean on DCI/phase/sentiment and the
//        operator's marketJudgment text.
// Tomorrow: swap `propose()` for an LLMProvider per agent.
// ---------------------------------------------------------------

import type {
  AgentChallenge,
  AgentId,
  AgentProposal,
  AgentRevision,
  AgentSpec,
  ConsensusBreakdown,
  CouncilOutcome,
  CouncilTranscript,
  CouncilVerdict,
  HumanThesis,
  MarketContext,
  Recommendation,
} from "@/lib/types";

// ---------- agent registry ----------

export const COUNCIL_AGENTS: readonly AgentSpec[] = [
  {
    id: "TECHNICAL",
    name: "Marcus 'Quant'",
    tagline: "Pure price action · DCI · key levels",
    color: "#38bdf8", // sky-400
    weight: 0.25,
  },
  {
    id: "SENTIMENT",
    name: "Lena 'Crowd'",
    tagline: "Funding rates · OI · on-chain mood",
    color: "#f472b6", // pink-400
    weight: 0.15,
  },
  {
    id: "MACRO",
    name: "Dr. Sato",
    tagline: "Rates · liquidity · global macro",
    color: "#a78bfa", // violet-400
    weight: 0.2,
  },
  {
    id: "RISK",
    name: "Captain Vega",
    tagline: "Drawdown · correlation · exposure",
    color: "#fbbf24", // amber-400
    weight: 0.25,
  },
  {
    id: "CONTRARIAN",
    name: "Echo",
    tagline: "Looks for the trade no one is making",
    color: "#34d399", // emerald-400
    weight: 0.15,
  },
] as const;

const AGENT_BY_ID: Record<AgentId, AgentSpec> = Object.fromEntries(
  COUNCIL_AGENTS.map((a) => [a.id, a])
) as Record<AgentId, AgentSpec>;

export function getAgent(id: AgentId): AgentSpec {
  return AGENT_BY_ID[id];
}

// ---------- public API ----------

export interface RunCouncilOptions {
  /** Override the per-agent latency (default 250 ms). 0 = instant. */
  perAgentLatencyMs?: number;
  /** Optional seed for deterministic replay (mock implementation). */
  seed?: number;
}

/**
 * Run a full council session synchronously (but yields to the
 * event loop between agents so the UI can animate the transcript).
 *
 * Returns the full CouncilVerdict including transcript — exactly
 * what gets persisted to Financial Memory.
 */
export async function runCouncil(
  thesis: HumanThesis,
  context: MarketContext,
  options: RunCouncilOptions = {}
): Promise<CouncilVerdict> {
  const latency = options.perAgentLatencyMs ?? 250;
  const startedAt = new Date().toISOString();

  // Step 1: proposals (sequential with yields for animation).
  const proposals: AgentProposal[] = [];
  for (const spec of COUNCIL_AGENTS) {
    proposals.push(propose(spec.id, thesis, context, options.seed));
    if (latency > 0) await sleep(latency);
  }

  // Step 2: contrarian-led challenges.
  const challenges: AgentChallenge[] = challengePhase(proposals, context);
  if (latency > 0) await sleep(latency);

  // Step 3: revisions — agents update confidence if challenged.
  const revisions: AgentRevision[] = revisionPhase(proposals, challenges);
  if (latency > 0) await sleep(latency);

  // Step 4: consensus.
  const consensus = computeConsensus(proposals, revisions);
  const decidedAt = new Date().toISOString();

  return {
    id: `council-${startedAt}`,
    startedAt,
    decidedAt,
    durationMs:
      new Date(decidedAt).getTime() - new Date(startedAt).getTime(),
    humanThesis: thesis,
    marketContext: context,
    transcript: { proposals, challenges, revisions },
    consensus,
    decision: consensus.winner,
    confidence: Math.round(consensus.avgConfidence),
    outcome: consensus.override
      ? "OVERRIDE"
      : consensus.weight >= 0.6
      ? "CONSENSUS"
      : "SPLIT",
    size: sizeForDecision(consensus.winner, consensus.avgConfidence),
  };
}

// ---------- per-agent proposal ----------

function propose(
  agent: AgentId,
  thesis: HumanThesis,
  ctx: MarketContext,
  seed?: number
): AgentProposal {
  switch (agent) {
    case "TECHNICAL":
      return technicalProposal(thesis, ctx, seed);
    case "SENTIMENT":
      return sentimentProposal(thesis, ctx, seed);
    case "MACRO":
      return macroProposal(thesis, ctx, seed);
    case "RISK":
      return riskProposal(thesis, ctx, seed);
    case "CONTRARIAN":
      return contrarianProposal(thesis, ctx, seed);
  }
}

// ---- TECHNICAL: trend + DCI ----

function technicalProposal(
  _thesis: HumanThesis,
  ctx: MarketContext,
  _seed?: number
): AgentProposal {
  const phaseBias: Record<typeof ctx.phase, Recommendation> = {
    MARKUP: "BUY",
    ACCUMULATION: "HOLD",
    DISTRIBUTION: "REDUCE",
    MARKDOWN: "SELL",
    RECOVERY: "BUY",
    UNKNOWN: "WAIT",
  };
  const rec = ctx.avgDci >= 70 ? "STRONG_BUY" : phaseBias[ctx.phase];
  const confidence = clamp(
    ctx.avgDci + (ctx.phase === "MARKUP" || ctx.phase === "MARKDOWN" ? 5 : 0),
    30,
    95
  );

  return {
    agent: "TECHNICAL",
    recommendation: rec,
    confidence: round(confidence),
    rationale: `DCI ${ctx.avgDci.toFixed(1)} on ${ctx.dominantSymbol} with phase ${ctx.phase} → ${
      rec.toLowerCase().replace("_", " ")
    }.`,
    evidence: [
      `Phase ${ctx.phase} supports ${bullOrBear(rec)} structure`,
      `DCI ${ctx.avgDci.toFixed(1)} → ${band(ctx.avgDci)} conviction`,
      ctx.avgDci > 65
        ? "Volume profile agrees with directional bias"
        : "Volume profile indecisive",
    ],
  };
}

// ---- SENTIMENT: crowd / funding ----

function sentimentProposal(
  thesis: HumanThesis,
  ctx: MarketContext,
  _seed?: number
): AgentProposal {
  const bullish = /(bullish|breakout|accumulate|buy|long)/i.test(
    thesis.marketJudgment
  );
  const bearish = /(bearish|breakdown|sell|short|capitulat)/i.test(
    thesis.marketJudgment
  );
  const crowdAgrees =
    (bullish && ctx.sentiment === "BULLISH") ||
    (bearish && ctx.sentiment === "BEARISH");

  const rec: Recommendation = (() => {
    if (crowdAgrees && ctx.sentiment === "BULLISH") {
      return ctx.avgDci >= 60 ? "BUY" : "HOLD";
    }
    if (crowdAgrees && ctx.sentiment === "BEARISH") {
      return ctx.avgDci <= 45 ? "SELL" : "REDUCE";
    }
    if (ctx.sentiment === "CAUTIOUS") return "HOLD";
    return "WAIT";
  })();

  const confidence = crowdAgrees ? 70 : 45;
  return {
    agent: "SENTIMENT",
    recommendation: rec,
    confidence,
    rationale: crowdAgrees
      ? `Operator thesis aligns with crowd sentiment (${ctx.sentiment}).`
      : `Operator thesis diverges from sentiment (${ctx.sentiment}). Sizing down.`,
    evidence: [
      `Sentiment: ${ctx.sentiment}`,
      crowdAgrees
        ? "Funding flow supports the thesis"
        : "Counter-crowd positioning risk",
      ctx.sentiment === "CAUTIOUS"
        ? "Hedger skew rising — caution warranted"
        : "Retail perp flow normal",
    ],
  };
}

// ---- MACRO: rates + liquidity ----

function macroProposal(
  thesis: HumanThesis,
  ctx: MarketContext,
  _seed?: number
): AgentProposal {
  const macroBullish = /(cut|qe|liquidity|ease|lower rates)/i.test(
    thesis.macroView
  );
  const macroBearish = /(hike|qt|tighten|higher rates|recession)/i.test(
    thesis.macroView
  );

  let rec: Recommendation = "HOLD";
  let confidence = 55;
  if (macroBullish && (ctx.phase === "MARKUP" || ctx.phase === "RECOVERY")) {
    rec = "BUY";
    confidence = 72;
  } else if (
    macroBearish &&
    (ctx.phase === "DISTRIBUTION" || ctx.phase === "MARKDOWN")
  ) {
    rec = "REDUCE";
    confidence = 70;
  } else if (macroBullish) {
    rec = "HOLD";
    confidence = 60;
    return {
      agent: "MACRO",
      recommendation: rec,
      confidence,
      rationale: `Macro tailwind (${summarize(thesis.macroView)}) not yet confirmed by phase ${ctx.phase}.`,
      evidence: [
        "Macro view is easing",
        `Phase ${ctx.phase} lags the macro signal`,
        "Wait for technical confirmation",
      ],
    };
  } else if (macroBearish) {
    rec = "HOLD";
    confidence = 60;
    return {
      agent: "MACRO",
      recommendation: rec,
      confidence,
      rationale: `Macro headwind (${summarize(
        thesis.macroView
      )}) acknowledged; current phase ${ctx.phase} absorbing.`,
      evidence: [
        "Macro view is restrictive",
        `Phase ${ctx.phase} still constructive`,
        "Defensive tilt preferred",
      ],
    };
  }

  return {
    agent: "MACRO",
    recommendation: rec,
    confidence,
    rationale: `Macro view (${summarize(thesis.macroView)}) sits neutral vs phase ${ctx.phase}.`,
    evidence: [
      "No strong directional macro signal",
      `Phase ${ctx.phase} is the dominant driver`,
      "Maintain neutral posture",
    ],
  };
}

// ---- RISK: drawdown / exposure ----

function riskProposal(
  thesis: HumanThesis,
  ctx: MarketContext,
  _seed?: number
): AgentProposal {
  const fearWords = /(drawdown|loss|crash|risk|danger|hedge)/i.test(
    `${thesis.riskFactors} ${thesis.actionPlan}`
  );
  const wantsBig = /(all-?in|max|big|aggressive)/i.test(thesis.actionPlan);

  // Risk officer tends to dampen enthusiasm unless conviction is high.
  let rec: Recommendation = "HOLD";
  let confidence = 60;
  let rationale = "";

  if (ctx.avgDci >= 70 && !fearWords) {
    rec = "BUY";
    confidence = 65;
    rationale = "Risk allows participation given strong DCI and no flagged concerns.";
  } else if (fearWords || wantsBig) {
    rec = "REDUCE";
    confidence = 72;
    rationale = "Risk trims exposure: operator flagged concerns or oversized intent.";
  } else if (ctx.avgDci < 40) {
    rec = "SELL";
    confidence = 68;
    rationale = "DCI below 40 — risk reduces exposure defensively.";
  } else {
    rec = "HOLD";
    confidence = 60;
    rationale = "Risk stance neutral pending clearer setup.";
  }

  return {
    agent: "RISK",
    recommendation: rec,
    confidence,
    rationale,
    evidence: [
      fearWords ? "Operator flagged risk factors" : "No explicit risk callouts",
      `DCI ${ctx.avgDci.toFixed(1)} on risk radar`,
      wantsBig ? "Concentration risk if sized too aggressively" : "Sizing reasonable",
    ],
  };
}

// ---- CONTRARIAN: looks for the other side ----

function contrarianProposal(
  thesis: HumanThesis,
  ctx: MarketContext,
  _seed?: number
): AgentProposal {
  const bullish = /(bullish|breakout|buy|long)/i.test(thesis.marketJudgment);
  const bearish = /(bearish|breakdown|sell|short|capitulat)/i.test(
    thesis.marketJudgment
  );

  // Echo picks the opposite when crowd is one-sided and DCI is extreme.
  let rec: Recommendation = "WAIT";
  let confidence = 50;
  let rationale = "";

  if (bullish && ctx.avgDci > 75) {
    rec = "REDUCE";
    confidence = 62;
    rationale =
      "DCI extreme + bullish consensus. Echo trims — late longs carry reversal risk.";
  } else if (bearish && ctx.avgDci < 25) {
    rec = "BUY";
    confidence = 62;
    rationale =
      "DCI capitulation + bearish consensus. Echo leans contrarian long.";
  } else if (ctx.phase === "DISTRIBUTION" && bullish) {
    rec = "HOLD";
    confidence = 55;
    rationale = "Phase Distribution argues against fresh longs.";
  } else if (ctx.phase === "ACCUMULATION" && bearish) {
    rec = "BUY";
    confidence = 60;
    rationale = "Phase Accumulation argues against fresh shorts.";
  } else {
    rationale = "No extreme signal — Echo abstains from contrarian positioning.";
  }

  return {
    agent: "CONTRARIAN",
    recommendation: rec,
    confidence,
    rationale,
    evidence: [
      `DCI ${ctx.avgDci.toFixed(1)} vs sentiment direction`,
      `Phase ${ctx.phase} cross-checked against operator lean`,
      "Echo watches for crowded trades",
    ],
  };
}

// ---------- phase 2: challenges ----------
// Contrarian actively challenges the highest-confidence proposal;
// risk officer challenges if it conflicts with risk flags.

function challengePhase(
  proposals: AgentProposal[],
  ctx: MarketContext
): AgentChallenge[] {
  const challenges: AgentChallenge[] = [];
  const byAgent = new Map(proposals.map((p) => [p.agent, p]));

  // 1. Contrarian challenges the highest-confidence agent when they disagree.
  const sorted = [...proposals].sort((a, b) => b.confidence - a.confidence);
  const leader = sorted[0];
  const echo = byAgent.get("CONTRARIAN")!;
  if (
    echo &&
    echo.recommendation !== leader.recommendation &&
    leader.confidence >= 70
  ) {
    challenges.push({
      from: "CONTRARIAN",
      to: leader.agent,
      vote: "DISAGREE",
      statement: `Leader ${leader.agent} calls ${leader.recommendation} at ${leader.confidence}%. Echo sees ${echo.recommendation} as the better risk-adjusted stance given current extremes.`,
    });
  }

  // 2. Risk officer challenges any BUY/STRONG_BUY when DCI is extreme.
  const risk = byAgent.get("RISK")!;
  for (const p of proposals) {
    if (
      p.agent === "RISK" ||
      p.agent === "CONTRARIAN"
    )
      continue;
    if (
      (p.recommendation === "STRONG_BUY" || p.recommendation === "BUY") &&
      ctx.avgDci > 80 &&
      p.confidence > 70
    ) {
      challenges.push({
        from: "RISK",
        to: p.agent,
        vote: "DISAGREE",
        statement: `Risk flags crowding: DCI ${ctx.avgDci.toFixed(
          1
        )} with high conviction ${p.recommendation} from ${p.agent}.`,
      });
    }
  }

  // 3. Echo challenges SELL calls during accumulation.
  if (ctx.phase === "ACCUMULATION") {
    for (const p of proposals) {
      if (p.recommendation === "SELL" && p.confidence >= 65) {
        challenges.push({
          from: "CONTRARIAN",
          to: p.agent,
          vote: "DISAGREE",
          statement: `Phase Accumulation rarely honors ${p.recommendation} calls. Echo urges patience.`,
        });
      }
    }
  }

  // 4. Sympathy votes — agreement endorsements for diversity of view.
  for (const a of proposals) {
    if (a.agent === "CONTRARIAN") continue;
    const sympathy = proposals.find(
      (p) => p.agent !== a.agent && p.recommendation === a.recommendation
    );
    if (sympathy && challenges.length < 4) {
      challenges.push({
        from: sympathy.agent,
        to: a.agent,
        vote: "AGREE",
        statement: `${sympathy.agent} concurs on ${a.recommendation}; the structural case is consistent.`,
      });
    }
  }

  return challenges.slice(0, 5);
}

// ---------- phase 3: revisions ----------
// Each agent (other than the challenger) can update its confidence
// if it was on the losing side of a strong challenge.

function revisionPhase(
  proposals: AgentProposal[],
  challenges: AgentChallenge[]
): AgentRevision[] {
  const revisions: AgentRevision[] = [];
  for (const p of proposals) {
    const attacks = challenges.filter(
      (c) => c.to === p.agent && c.vote === "DISAGREE"
    );
    const endorsements = challenges.filter(
      (c) => c.to === p.agent && c.vote === "AGREE"
    );
    if (attacks.length === 0 && endorsements.length === 0) {
      revisions.push({
        agent: p.agent,
        note: "Held position; no challenges received.",
      });
      continue;
    }
    const delta = endorsements.length * 3 - attacks.length * 8;
    const nextConfidence = clamp(p.confidence + delta, 25, 95);
    const note =
      attacks.length > 0
        ? `Discounted ${attacks.length} challenge(s) by ${attacks
            .map((a) => a.from)
            .join(", ")}. Confidence ${delta >= 0 ? "+" : ""}${delta}.`
        : `Reinforced by ${endorsements
            .map((a) => a.from)
            .join(", ")}. Confidence +${delta}.`;
    revisions.push({
      agent: p.agent,
      confidence: round(nextConfidence),
      note,
    });
  }
  return revisions;
}

// ---------- phase 4: consensus ----------

function computeConsensus(
  proposals: AgentProposal[],
  revisions: AgentRevision[]
): ConsensusBreakdown {
  const agents = COUNCIL_AGENTS;
  const revisedByAgent = new Map(
    revisions.map((r) => [r.agent, r.confidence ?? null])
  );

  // Tally weighted votes per recommendation using revised confidences
  // when available, falling back to the original.
  const distribution: Record<Recommendation, number> = {
    STRONG_BUY: 0,
    BUY: 0,
    HOLD: 0,
    REDUCE: 0,
    SELL: 0,
    WAIT: 0,
  };
  const winningConfidences: number[] = [];

  for (const spec of agents) {
    const original = proposals.find((p) => p.agent === spec.id);
    if (!original) continue;
    const revisedConfidence = revisedByAgent.get(spec.id);
    const effectiveConfidence =
      typeof revisedConfidence === "number"
        ? revisedConfidence
        : original.confidence;
    // Weight = agent voting weight × (effectiveConfidence / 100).
    // High-confidence agents get more say than the bare weight implies.
    const effective = spec.weight * (effectiveConfidence / 100);
    distribution[original.recommendation] += effective;
  }

  // Pick the highest-weighted recommendation.
  const entries = Object.entries(distribution) as [Recommendation, number][];
  entries.sort((a, b) => b[1] - a[1]);
  const [winner, winnerWeight] = entries[0];
  const runnerUp = entries[1]?.[1] ?? 0;

  // Average confidence among agents that voted for the winner.
  for (const spec of agents) {
    const original = proposals.find((p) => p.agent === spec.id);
    if (!original) continue;
    if (original.recommendation !== winner) continue;
    const revisedConfidence = revisedByAgent.get(spec.id);
    winningConfidences.push(
      typeof revisedConfidence === "number"
        ? revisedConfidence
        : original.confidence
    );
  }

  const avgConfidence =
    winningConfidences.length > 0
      ? winningConfidences.reduce((s, n) => s + n, 0) / winningConfidences.length
      : 50;
  const leadingConfidence =
    winningConfidences.length > 0 ? Math.max(...winningConfidences) : 0;

  // If the margin between winner and runner-up is thin, chairman overrides
  // toward HOLD to avoid acting on a noisy signal.
  const override = winnerWeight - runnerUp < 0.02;

  return {
    winner: override ? "HOLD" : winner,
    weight: round(winnerWeight),
    leadingConfidence: round(leadingConfidence),
    avgConfidence: round(avgConfidence),
    override,
    distribution: Object.fromEntries(
      Object.entries(distribution).map(([k, v]) => [k, round(v)])
    ) as Record<Recommendation, number>,
  };
}

// ---------- helpers ----------

function sizeForDecision(rec: Recommendation, confidence: number): string {
  switch (rec) {
    case "STRONG_BUY":
      return confidence > 80 ? "60%" : "45%";
    case "BUY":
      return confidence > 70 ? "35%" : "20%";
    case "REDUCE":
      return "30% trim";
    case "SELL":
      return "100%";
    case "HOLD":
    case "WAIT":
    default:
      return "0%";
  }
}

function clamp(n: number, min: number, max: number): number {
  return Math.max(min, Math.min(max, n));
}

function round(n: number): number {
  return Math.round(n * 10) / 10;
}

function sleep(ms: number): Promise<void> {
  return ms > 0 ? new Promise((r) => setTimeout(r, ms)) : Promise.resolve();
}

function band(dci: number): string {
  if (dci >= 70) return "high";
  if (dci >= 50) return "medium";
  if (dci >= 35) return "low";
  return "very low";
}

function bullOrBear(rec: Recommendation): "bullish" | "bearish" | "neutral" {
  if (rec === "STRONG_BUY" || rec === "BUY") return "bullish";
  if (rec === "SELL" || rec === "REDUCE") return "bearish";
  return "neutral";
}

function summarize(text: string): string {
  const trimmed = text.trim();
  if (trimmed.length === 0) return "unspecified";
  const first = trimmed.split(/[.\n]/)[0] ?? trimmed;
  return first.length > 64 ? first.slice(0, 64) + "…" : first;
}

// ---------- convenience for UI ----------

export const RECOMMENDATION_LABELS: Record<Recommendation, string> = {
  STRONG_BUY: "Strong Buy",
  BUY: "Buy",
  HOLD: "Hold",
  REDUCE: "Reduce",
  SELL: "Sell",
  WAIT: "Wait",
};

export const OUTCOME_LABELS: Record<CouncilOutcome, string> = {
  CONSENSUS: "Consensus",
  SPLIT: "Split Decision",
  OVERRIDE: "Chairman Override",
};
