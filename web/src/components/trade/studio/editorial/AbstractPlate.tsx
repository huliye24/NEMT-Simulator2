import type { ReactNode } from "react";
import { cn } from "@/lib/trade/format";

export type ArtVariant =
  | "field"
  | "index"
  | "research"
  | "compute"
  | "execution"
  | "empty";

/* Line art only. These shapes are editorial illustrations, never market data. */

function ArtGrid({ id }: { id: string }) {
  return (
    <>
      <defs>
        <pattern
          id={id}
          width="32"
          height="32"
          patternUnits="userSpaceOnUse"
        >
          <path
            d="M32 0H0V32"
            fill="none"
            stroke="currentColor"
            strokeOpacity="0.1"
          />
        </pattern>
      </defs>
      <rect width="640" height="320" fill={`url(#${id})`} />
    </>
  );
}

function FieldArt() {
  return (
    <svg viewBox="0 0 640 320" aria-hidden="true">
      <ArtGrid id="nsx-grid-field" />
      <path
        className="nsx-art-cyan"
        d="M48 250C120 190 164 286 230 214S348 104 412 166s96 22 178-92"
      />
      <path
        className="nsx-art-red"
        d="M44 278C126 232 178 306 264 242s112-136 170-78 84 46 160-20"
      />
      <path className="nsx-art-ink" d="M48 52V266H596" />
      <circle className="nsx-art-dot" cx="412" cy="166" r="13" />
      <circle className="nsx-art-ring" cx="412" cy="166" r="42" />
      <circle className="nsx-art-ring" cx="412" cy="166" r="72" />
      <path className="nsx-art-red-line" d="M506 118l50-38m-11 1 11-1-3 11" />
      <g className="nsx-art-candles">
        <path d="M104 208v54m-9-34h18v22h-18zM144 184v58m-9-42h18v25h-18zM184 194v66m-9-48h18v31h-18zM224 152v88m-9-62h18v41h-18z" />
      </g>
      <text className="nsx-art-text" x="48" y="40">
        STRUCTURE / NOT NOISE
      </text>
      <text className="nsx-art-text" x="444" y="182">
        CRITICAL POINT
      </text>
      <text className="nsx-art-text" x="48" y="296">
        t0
      </text>
      <text className="nsx-art-text" x="574" y="296">
        tn
      </text>
    </svg>
  );
}

function IndexArt() {
  return (
    <svg viewBox="0 0 640 320" aria-hidden="true">
      <ArtGrid id="nsx-grid-index" />
      <path className="nsx-art-ink" d="M48 48V272H592" />
      <g className="nsx-art-index-cards">
        <rect x="84" y="76" width="188" height="58" />
        <rect x="118" y="150" width="188" height="58" />
        <rect x="152" y="224" width="188" height="1" />
      </g>
      <path className="nsx-art-red" d="M84 105h188" />
      <path className="nsx-art-cyan" d="M118 179h188" />
      <path className="nsx-art-ink" d="M84 130h188" strokeDasharray="2 6" />
      <path className="nsx-art-red-line" d="M352 96c92 0 92 138 188 138" />
      <circle className="nsx-art-dot" cx="390" cy="126" r="5" />
      <circle className="nsx-art-dot" cx="460" cy="196" r="5" />
      <circle className="nsx-art-dot" cx="540" cy="226" r="5" />
      <text className="nsx-art-text" x="84" y="68">
        01 / INBOX
      </text>
      <text className="nsx-art-text" x="118" y="142">
        02 / LIBRARY
      </text>
      <text className="nsx-art-text" x="152" y="216">
        03 / VALIDATION
      </text>
      <text className="nsx-art-text" x="438" y="88">
        HUMAN REVIEW
      </text>
      <text className="nsx-art-text" x="438" y="306">
        AI PROPOSES · HUMANS CURATE
      </text>
    </svg>
  );
}

function ResearchArt() {
  return (
    <svg viewBox="0 0 640 320" aria-hidden="true">
      <ArtGrid id="nsx-grid-research" />
      <path className="nsx-art-ink" d="M48 54V270H592" />
      <path
        className="nsx-art-cyan"
        d="M64 206c48 0 48-92 96-92s48 138 96 138 48-196 96-196 48 170 96 170 48-84 96-84 48 52 96 52"
      />
      <path
        className="nsx-art-red"
        d="M64 246c56 0 56-58 112-58s56 84 112 84 56-118 112-118 56 96 112 96 56-44 112-44"
      />
      <circle className="nsx-art-dot" cx="256" cy="252" r="7" />
      <circle className="nsx-art-dot" cx="352" cy="52" r="7" />
      <circle className="nsx-art-ring" cx="352" cy="52" r="33" />
      <path className="nsx-art-ink" d="M352 52v-78M352 52h96" strokeDasharray="2 6" />
      <text className="nsx-art-text" x="64" y="292">
        HYPOTHESIS
      </text>
      <text className="nsx-art-text" x="300" y="36">
        EVIDENCE
      </text>
      <text className="nsx-art-text" x="512" y="292">
        OOS
      </text>
      <text className="nsx-art-text" x="64" y="44">
        ψ / OBSERVATION FIELD
      </text>
    </svg>
  );
}

function ComputeArt() {
  return (
    <svg viewBox="0 0 640 320" aria-hidden="true">
      <ArtGrid id="nsx-grid-compute" />
      <path className="nsx-art-ink" d="M48 48V272H592" />
      <path className="nsx-art-ink" d="M48 160h544" strokeDasharray="2 7" />
      <g className="nsx-art-nodes">
        <circle cx="112" cy="104" r="7" />
        <circle cx="176" cy="152" r="7" />
        <circle cx="240" cy="84" r="7" />
        <circle cx="112" cy="216" r="7" />
        <circle cx="188" cy="238" r="7" />
        <circle cx="264" cy="196" r="7" />
      </g>
      <path
        className="nsx-art-cyan"
        d="M112 104 176 152 240 84"
      />
      <path
        className="nsx-art-cyan"
        d="M112 216 188 238 264 196"
        strokeDasharray="3 7"
      />
      <path
        className="nsx-art-ink"
        d="M240 84c94 0 94 76 156 76M264 196c80 0 80-36 132-36"
      />
      <rect className="nsx-art-gate" x="396" y="118" width="86" height="84" />
      <path className="nsx-art-red" d="M439 118v84" />
      <path className="nsx-art-red-line" d="M482 160h74m-12-12 12 12-12 12" />
      <circle className="nsx-art-dot" cx="556" cy="160" r="8" />
      <text className="nsx-art-text" x="64" y="84">
        MATLAB LANE
      </text>
      <text className="nsx-art-text" x="64" y="296">
        GPU LANE
      </text>
      <text className="nsx-art-text" x="402" y="108">
        OOS GATE
      </text>
      <text className="nsx-art-text" x="518" y="140">
        ARTIFACT
      </text>
      <text className="nsx-art-text" x="402" y="232">
        GPU ACCELERATES — IT DOES NOT PROVE
      </text>
    </svg>
  );
}

function ExecutionArt() {
  return (
    <svg viewBox="0 0 640 320" aria-hidden="true">
      <ArtGrid id="nsx-grid-execution" />
      <path className="nsx-art-ink" d="M48 52V268H592" />
      <g className="nsx-art-target">
        <circle cx="320" cy="160" r="42" />
        <circle cx="320" cy="160" r="74" />
        <circle cx="320" cy="160" r="106" />
      </g>
      <path className="nsx-art-cyan" d="M320 54v52m0 108v52M214 160h52m108 0h52" />
      <path className="nsx-art-red-line" d="M320 96l62 62-62 62-62-62Z" />
      <circle className="nsx-art-dot" cx="320" cy="160" r="9" />
      <g className="nsx-art-ticks">
        <path d="M492 88v144M504 88v144M516 88v144M528 88v144M540 88v144M552 88v144M564 88v144" />
      </g>
      <text className="nsx-art-text" x="64" y="44">
        RISK GATE
      </text>
      <text className="nsx-art-text" x="492" y="72">
        AUDIT
      </text>
      <text className="nsx-art-text" x="64" y="296">
        NO BROWSER ORDER ENTRY
      </text>
      <text className="nsx-art-text" x="492" y="252">
        FAIL CLOSED
      </text>
    </svg>
  );
}

function EmptyArt() {
  return (
    <svg viewBox="0 0 640 320" aria-hidden="true">
      <ArtGrid id="nsx-grid-empty" />
      <path className="nsx-art-ink" d="M48 52V268H592" />
      <path className="nsx-art-red" d="M48 214h544" />
      <path className="nsx-art-ink" d="M48 268h544" strokeDasharray="2 7" />
      <circle className="nsx-art-dot" cx="320" cy="214" r="7" />
      <text className="nsx-art-text" x="48" y="44">
        NO VERIFIED HISTORY
      </text>
      <text className="nsx-art-text" x="48" y="296">
        EMPTY BY DESIGN — NOT A FLAT LINE
      </text>
      <text className="nsx-art-text" x="470" y="196">
        净值历史未接入
      </text>
    </svg>
  );
}

const ART: Record<ArtVariant, () => ReactNode> = {
  field: FieldArt,
  index: IndexArt,
  research: ResearchArt,
  compute: ComputeArt,
  execution: ExecutionArt,
  empty: EmptyArt,
};

export function AbstractPlate({
  variant,
  label,
  caption,
  className,
}: {
  variant: ArtVariant;
  label: string;
  caption: ReactNode;
  className?: string;
}) {
  const Art = ART[variant];
  return (
    <figure className={cn("nsx-plate", className)}>
      <div className="nsx-plate-meta">
        <span>{label}</span>
        <span>ABSTRACT / NOT DATA</span>
      </div>
      <div className="nsx-plate-canvas">
        <Art />
      </div>
      <figcaption className="nsx-plate-caption">
        <i aria-hidden="true" />
        <span>{caption}</span>
      </figcaption>
    </figure>
  );
}
