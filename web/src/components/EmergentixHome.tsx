"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import type { AIReport, MarketState, MarketSymbol, Portfolio } from "@/lib/types";

type Props = {
  state: MarketState;
  symbols: MarketSymbol[];
  portfolio: Portfolio;
  latestReport?: AIReport;
};
type Filter = "all" | "strong" | "observe";

const phaseName: Record<MarketSymbol["phase"], string> = {
  ACCUMULATION: "积累", MARKUP: "上行", DISTRIBUTION: "分配",
  MARKDOWN: "下行", RECOVERY: "恢复", UNKNOWN: "未知",
};
const navigation = [
  { href: "/", label: "总览", index: "01" },
  { href: "/market", label: "市场", index: "02" },
  { href: "/analysis", label: "研究报告", index: "03" },
  { href: "/simulation", label: "模拟验证", index: "04" },
  { href: "/journal", label: "研究日志", index: "05" },
];
const money = (n: number) => "$" + n.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });

function Brand() {
  return (
    <span className="inline-flex items-center gap-2 text-[20px] font-semibold tracking-[-0.055em]">
      <span className="flex h-8 w-8 items-center justify-center rounded-xl bg-[#17313B] text-xl font-bold text-[#36D5E1]">e</span>
      emergent<span className="-ml-2 text-[#08A6B8]">ix</span>
    </span>
  );
}

function Metric({ label, value, hint }: { label: string; value: string; hint: string }) {
  return (
    <div className="rounded-2xl border border-[#E4EBEF] bg-white p-4 sm:p-5">
      <p className="text-[10px] font-semibold uppercase tracking-[0.13em] text-[#8B9CA5]">{label}</p>
      <p className="mt-3 text-[27px] font-semibold tracking-[-0.05em] tabular-nums text-[#1D3642]">{value}</p>
      <p className="mt-1 text-[11px] text-[#8496A0]">{hint}</p>
    </div>
  );
}

/** Homepage uses historical fixtures from web/src/data, never live exchange prices. */
export default function EmergentixHome({ state, symbols, portfolio, latestReport }: Props) {
  const [filter, setFilter] = useState<Filter>("all");
  const [search, setSearch] = useState("");
  const [selected, setSelected] = useState<string | null>(null);
  const filtered = useMemo(() => symbols.filter((item) => {
    const queryMatch = item.symbol.toLowerCase().includes(search.trim().toLowerCase())
      || item.display.toLowerCase().includes(search.trim().toLowerCase());
    const bandMatch = filter === "all" || (filter === "strong" ? item.dci.value >= 65 : item.dci.value < 65);
    return queryMatch && bandMatch;
  }), [symbols, search, filter]);
  const selectedAsset = symbols.find((item) => item.symbol === selected) ?? filtered[0];
  const snapshot = state.asOf ? state.asOf.replace("T", " ").slice(0, 16) + " UTC" : "未提供";

  return (
    <div className="min-h-screen bg-[#F5F7F8] text-[#19313D]">
      <div className="mx-auto flex min-h-screen max-w-[1680px]">
        <aside className="hidden w-[230px] shrink-0 flex-col border-r border-[#E6ECEF] bg-white px-5 py-7 md:flex">
          <Link href="/" className="focus-visible:outline-2 focus-visible:outline-[#00ACC0]"><Brand /></Link>
          <p className="mb-10 ml-10 mt-1 text-[10px] tracking-[0.1em] text-[#8298A2]">MARKET INTELLIGENCE</p>
          <p className="mb-3 px-3 text-[10px] font-bold uppercase tracking-[0.16em] text-[#A1AEB5]">Workspace</p>
          <nav aria-label="主导航" className="space-y-1">
            {navigation.map((nav) => (
              <Link key={nav.href} href={nav.href} aria-current={nav.href === "/" ? "page" : undefined}
                className={"flex gap-3 rounded-xl px-3 py-3 text-[13px] font-semibold transition " +
                  (nav.href === "/" ? "bg-[#E8F8FA] text-[#087D8D]" : "text-[#72858F] hover:bg-[#F2F7F8]")}>
                <span className="font-mono text-[10px] opacity-60">{nav.index}</span>{nav.label}
              </Link>
            ))}
          </nav>
          <div className="mt-auto rounded-2xl bg-[#EFF8F9] p-4">
            <p className="text-xs font-semibold text-[#227482]">NEMT Research</p>
            <p className="mt-2 text-xs leading-5 text-[#7A929B]">非平衡市场理论、数学实验与策略验证是 Emergentix 的研究基础。</p>
          </div>
        </aside>
        <div className="min-w-0 flex-1">
          <header className="sticky top-0 z-20 flex h-[68px] items-center justify-between border-b border-[#E7EBEE] bg-white/95 px-5 backdrop-blur sm:px-8">
            <div className="md:hidden"><Brand /></div>
            <p className="hidden text-xs font-medium text-[#77909B] md:block">Workspace <span className="mx-2 text-[#C9D5DA]">/</span> Overview</p>
            <div className="flex items-center gap-2">
              <span className="rounded-full border border-[#EFDFBA] bg-[#FFF9E9] px-3 py-1.5 text-[10px] font-bold tracking-wider text-[#9E7526]">● DEMO DATA</span>
              <Link href="/trade" className="rounded-full border border-[#DEE9EC] px-3 py-1.5 text-xs font-semibold text-[#317A89] hover:bg-[#ECF8FA]">交易终端 ↗</Link>
            </div>
          </header>
          <main className="mx-auto max-w-[1440px] space-y-6 px-5 pb-24 pt-8 sm:px-8 lg:pt-10">
            <section className="flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
              <div>
                <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-[#079EAE]">EMERGENCE INTELLIGENCE</p>
                <h1 className="mt-3 max-w-3xl text-[29px] font-semibold leading-tight tracking-[-0.052em] sm:text-[38px]">
                  以涌现算法，<span className="text-[#0BA6B7]">探索市场机会。</span>
                </h1>
                <p className="mt-3 max-w-2xl text-[13px] leading-6 text-[#768B95]">
                  从市场结构识别，到策略研究与风险控制。通过可验证的数据观察市场，而非追逐噪声。
                </p>
              </div>
              <Link href="/analysis" className="inline-flex shrink-0 items-center justify-center rounded-xl bg-[#183441] px-5 py-3 text-xs font-semibold text-white hover:bg-[#2E5665]">
                进入研究工作台 <span className="ml-3">↗</span>
              </Link>
            </section>
            <div role="status" className="rounded-xl border border-[#DDE9ED] bg-[#EDF6F8] px-4 py-3 text-xs leading-5 text-[#5A7F8B]">
              <strong>数据声明：</strong>本页行情、信号和组合均为历史演示快照（{snapshot}），不是实时 Binance 报价、已验证盈利策略或真实账户数据。
            </div>
            <section aria-label="市场概览" className="grid grid-cols-2 gap-3 xl:grid-cols-4">
              <Metric label="Markets" value={String(state.trackedSymbols)} hint="演示跟踪市场" />
              <Metric label="Market regime" value={phaseName[state.phase]} hint="样例结构状态" />
              <Metric label="Average DCI" value={state.avgDci.toFixed(1)} hint="研究指标 / 100" />
              <Metric label="Signals to review" value={String(state.activeSignals)} hint="待验证候选，非下单信号" />
            </section>
            <div className="grid gap-5 xl:grid-cols-12">
              <section className="overflow-hidden rounded-2xl border border-[#E4EBEF] bg-white xl:col-span-8">
                <div className="flex flex-wrap items-center justify-between gap-2 border-b border-[#EAF0F2] px-5 py-5">
                  <div><h2 className="text-base font-semibold">Market watchlist</h2><p className="mt-1 text-xs text-[#8899A2]">市场结构观察 · 历史 DEMO 样本</p></div>
                  <Link href="/market" className="text-xs font-semibold text-[#079CAC] hover:underline">全部市场 ↗</Link>
                </div>
                <div className="flex flex-wrap items-center justify-between gap-2 border-b border-[#EDF1F3] px-5 py-3">
                  <div className="flex flex-wrap gap-1.5" aria-label="DCI 筛选">
                    {([["all", "全部"], ["strong", "DCI ≥ 65"], ["observe", "DCI < 65"]] as const).map(([key, label]) => (
                      <button key={key} type="button" onClick={() => { setFilter(key); setSelected(null); }} aria-pressed={filter === key}
                        className={"rounded-lg px-3 py-2 text-xs font-medium " + (filter === key ? "bg-[#E5F7F9] text-[#0A91A0]" : "text-[#8799A1] hover:bg-[#F3F7F8]")}>{label}</button>
                    ))}
                  </div>
                  <label className="sr-only" htmlFor="emergentix-search">搜索市场</label>
                  <input id="emergentix-search" value={search} onChange={(e) => setSearch(e.target.value)}
                    placeholder="搜索 BTC / ETH" className="w-full rounded-lg border border-[#E3EBEE] bg-white px-3 py-2 text-xs outline-none focus:border-[#08AABE] sm:w-40" />
                </div>
                <div className="overflow-x-auto">
                  <table className="min-w-[540px] w-full text-left text-xs">
                    <thead className="bg-[#F9FBFC] text-[10px] uppercase tracking-widest text-[#92A1A9]">
                      <tr><th scope="col" className="px-5 py-3">Asset</th><th scope="col" className="px-3 py-3">Sample price</th><th scope="col" className="px-3 py-3">24h change</th><th scope="col" className="px-3 py-3">DCI</th><th scope="col" className="px-4 py-3">Phase</th></tr>
                    </thead>
                    <tbody>
                      {filtered.map((s) => (
                        <tr key={s.symbol} className={"border-t border-[#EEF3F4] " + (selectedAsset?.symbol === s.symbol ? "bg-[#F0FAFB]" : "hover:bg-[#F7FAFB]")}>
                          <td className="px-5 py-3.5"><button onClick={() => setSelected(s.symbol)} aria-pressed={selectedAsset?.symbol === s.symbol} type="button" className="font-semibold hover:text-[#0097A8]">{s.display}</button></td>
                          <td className="px-3 py-3.5 font-medium tabular-nums">{money(s.price)}</td>
                          <td className={"px-3 py-3.5 font-semibold tabular-nums " + (s.change24h >= 0 ? "text-[#148F7C]" : "text-[#CB6863]")}>{s.change24h > 0 ? "+" : ""}{s.change24h.toFixed(2)}%</td>
                          <td className="px-3 py-3.5">
                            <span className="tabular-nums">{s.dci.value.toFixed(1)}</span>
                            <div className="mt-1 h-1 w-16 rounded-full bg-[#E5EEF1]"><div className="h-1 rounded-full bg-[#15B5C3]" style={{ width: Math.min(100, Math.max(0, s.dci.value)) + "%" }} /></div>
                          </td>
                          <td className="px-4 py-3.5 text-[#768C96]">{phaseName[s.phase]}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                  {filtered.length === 0 && <p role="status" className="p-8 text-center text-xs text-[#7D939D]">没有匹配的样例市场。</p>}
                </div>
                <div className="border-t border-[#E7EFF1] bg-[#F9FBFC] px-5 py-4 text-xs leading-6 text-[#6D8590]">
                  {selectedAsset ? (
                    <><span className="font-bold text-[#235667]">{selectedAsset.display} · {phaseName[selectedAsset.phase]}</span>
                    <span> — DCI {selectedAsset.dci.value.toFixed(1)}，模型置信度 {selectedAsset.confidence.toFixed(1)}%。仅供结构研究，需样本外验证。</span></>
                  ) : "选择一个交易对以查看演示研究摘要。"}
                </div>
              </section>
              <div className="space-y-5 xl:col-span-4">
                <section className="rounded-2xl border border-[#E4EBEF] bg-white p-5">
                  <div className="flex items-center justify-between gap-3"><h2 className="text-base font-semibold">Portfolio preview</h2><span className="rounded-md bg-[#FFF4E4] px-2 py-1 text-[10px] font-bold text-[#A47729]">SIMULATED</span></div>
                  <p className="mt-1 text-xs text-[#94A3AB]">研究样例组合 · 非实际交易资金</p>
                  <p className="mt-7 text-[30px] font-semibold tracking-[-0.055em] tabular-nums">{money(portfolio.equity)}</p>
                  <p className="mt-1 text-xs text-[#91A0A9]">模拟组合总权益</p>
                  <div className="mt-5 grid grid-cols-2 gap-3 border-t border-[#E9F0F2] pt-4 text-xs">
                    <div><p className="text-[#96A5AC]">模拟盈亏</p><p className="mt-2 text-base font-semibold tabular-nums text-[#148F7C]">{money(portfolio.pnl)}</p></div>
                    <div><p className="text-[#96A5AC]">持仓数量</p><p className="mt-2 text-base font-semibold tabular-nums">{portfolio.positions.length}</p></div>
                  </div>
                  <Link href="/simulation" className="mt-5 block rounded-xl border border-[#DDE9ED] py-2.5 text-center text-xs font-semibold text-[#178997] hover:bg-[#F1F9FA]">查看模拟验证 ↗</Link>
                </section>
                <section className="rounded-2xl border border-[#D6E9EC] bg-[#ECF7F8] p-5">
                  <h2 className="text-sm font-bold text-[#267383]">Safety by design</h2>
                  <p className="mt-3 text-xs leading-6 text-[#6B8993]">DEMO 与实盘隔离。未经验证的涌现结构不是可执行的交易策略。</p>
                  <div className="mt-4 flex items-center justify-between border-t border-[#D8EAED] pt-3 text-xs"><span className="text-[#668691]">LIVE Trading</span><strong className="text-[#14899B]">Disabled</strong></div>
                </section>
              </div>
            </div>
            <section className="flex flex-col justify-between gap-3 rounded-2xl border border-[#E4EBEF] bg-white p-5 lg:flex-row lg:items-center">
              <div>
                <p className="text-[10px] font-bold uppercase tracking-widest text-[#0DA5B4]">Research pipeline</p>
                <h2 className="mt-2 text-base font-semibold">从科学假设到可验证策略</h2>
                <p className="mt-2 max-w-2xl text-xs leading-6 text-[#81939B]">
                  {latestReport ? "示例研究报告：" + latestReport.title + "。" : "暂时没有可展示的研究报告。"}
                  所有研究结果均需独立验证。
                </p>
              </div>
              <Link href="/analysis" className="shrink-0 text-xs font-semibold text-[#098F9D] hover:underline">研究报告 ↗</Link>
            </section>
            <footer className="flex flex-wrap items-center justify-between gap-2 border-t border-[#DFE8EB] pt-5 text-[11px] text-[#93A3AB]">
              <span>Emergentix · Powered by NEMT Research</span>
              <span>历史样例数据 · LIVE 禁用 · 不构成投资建议</span>
            </footer>
          </main>
        </div>
      </div>
      <nav className="fixed bottom-0 left-0 right-0 z-30 flex items-center justify-around border-t border-[#E2EAED] bg-white/95 px-2 py-2 md:hidden" aria-label="移动端导航">
        {navigation.slice(0, 3).map((n) => <Link key={n.href} href={n.href} className={"rounded-lg px-3 py-2 text-xs font-semibold " + (n.href === "/" ? "bg-[#E7F8FA] text-[#098798]" : "text-[#7E939C]")}>{n.label}</Link>)}
        <Link href="/trade" className="px-3 py-2 text-xs font-semibold text-[#098798]">交易</Link>
      </nav>
    </div>
  );
}
