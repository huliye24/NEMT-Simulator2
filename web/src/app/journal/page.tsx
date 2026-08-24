import { Card } from "@/components/Card";
import { getJournal } from "@/lib/api";
import { classNames } from "@/lib/format";
import type { Sentiment } from "@/lib/types";


const MOOD_TONE: Record<Sentiment, string> = {
  BULLISH: "text-emerald-300 bg-emerald-500/10 ring-emerald-500/30",
  BEARISH: "text-rose-300 bg-rose-500/10 ring-rose-500/30",
  NEUTRAL: "text-slate-300 bg-slate-500/10 ring-slate-500/30",
  CAUTIOUS: "text-amber-300 bg-amber-500/10 ring-amber-500/30",
};

export default async function JournalPage() {
  const entries = await getJournal();

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      <header>
        <div className="text-[11px] uppercase tracking-wider text-amber-400 mb-1">Journal</div>
        <h1 className="text-2xl font-bold text-slate-100">Trading Journal</h1>
        <p className="text-sm text-slate-400 mt-1">
          Daily notes from the desk and the council. Searchable, taggable, honest.
        </p>
      </header>

      <div className="space-y-4">
        {entries.map((entry) => (
          <Card
            key={entry.id}
            title={
              <div className="flex items-center gap-2">
                <span className="nemt-mono text-amber-300 text-[12px]">{entry.date}</span>
                <span className="text-slate-500">·</span>
                <span className="text-slate-100">{entry.title}</span>
              </div>
            }
            rightSlot={
              <span
                className={classNames("nemt-phase-chip ring-1", MOOD_TONE[entry.mood])}
              >
                {entry.mood}
              </span>
            }
          >
            <p className="text-sm text-slate-300 leading-relaxed whitespace-pre-line">
              {entry.body}
            </p>
            <div className="mt-4 flex flex-wrap gap-1.5">
              {entry.tags.map((tag) => (
                <span
                  key={tag}
                  className="text-[10px] uppercase tracking-wider px-2 py-0.5 rounded bg-nemt-bg-elevated text-slate-400 ring-1 ring-amber-500/10"
                >
                  #{tag}
                </span>
              ))}
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}
