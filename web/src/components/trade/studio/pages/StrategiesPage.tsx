"use client";

import Image from "next/image";
import { useMemo, useState } from "react";
import strategyPoster from "../assets/emergentix-strategy-poster-v1.png";
import type { StudioPageProps } from "../types";
import styles from "./StrategiesPage.module.css";

type ViewMode = "library" | "verified" | "selected";
type StrategyKind = "趋势" | "均值回归" | "NEMT" | "套利" | "AI";

interface StrategyItem {
  id: string; name: string; code: string; kind: StrategyKind; market: string; period: string;
  backtest: number; sharpe: number; drawdown: number; winRate: number;
  live?: number; liveDays?: number; risk: "低" | "中" | "高"; selected?: boolean;
}

const STRATEGIES: StrategyItem[] = [
  { id: "nemt-m", name: "NEMT Momentum", code: "EMG-01", kind: "NEMT", market: "BTC/USDT", period: "15m", backtest: 38.2, sharpe: 2.14, drawdown: 9.8, winRate: 58.4, live: 8.7, liveDays: 42, risk: "中", selected: true },
  { id: "mean", name: "Mean Revert 21", code: "MR-21", kind: "均值回归", market: "BTC/USDT", period: "1h", backtest: 24.6, sharpe: 1.82, drawdown: 7.1, winRate: 62.3, live: 5.2, liveDays: 68, risk: "低" },
  { id: "break", name: "Breakout Atlas", code: "BO-07", kind: "趋势", market: "ETH/USDT", period: "4h", backtest: 41.8, sharpe: 1.76, drawdown: 14.6, winRate: 53.1, live: 11.4, liveDays: 31, risk: "高" },
  { id: "phase", name: "Phase Transition", code: "NLS-12", kind: "NEMT", market: "BTC/USDT", period: "5m", backtest: 29.4, sharpe: 2.36, drawdown: 8.4, winRate: 57.8, risk: "中" },
  { id: "basis", name: "Basis Neutral", code: "ARB-04", kind: "套利", market: "多资产", period: "1h", backtest: 18.9, sharpe: 2.72, drawdown: 4.2, winRate: 71.5, live: 3.9, liveDays: 96, risk: "低" },
  { id: "alpha", name: "Alpha Ensemble", code: "AI-08", kind: "AI", market: "BTC/ETH", period: "15m", backtest: 34.1, sharpe: 1.94, drawdown: 11.3, winRate: 56.9, risk: "中" },
];

const VIEWS: Array<{ id: ViewMode; label: string; sub: string }> = [
  { id: "library", label: "历史策略库", sub: "BACKTESTED" },
  { id: "verified", label: "实测榜", sub: "LIVE PROVEN" },
  { id: "selected", label: "我的组合", sub: "SELECTED" },
];

export default function StrategiesPage(_props: StudioPageProps) {
  const [view, setView] = useState<ViewMode>("library");
  const [query, setQuery] = useState("");
  const [kind, setKind] = useState<"全部" | StrategyKind>("全部");
  const [activeId, setActiveId] = useState(STRATEGIES[0].id);
  const [selectedIds, setSelectedIds] = useState<string[]>(STRATEGIES.filter((item) => item.selected).map((item) => item.id));

  const items = useMemo(() => STRATEGIES.filter((item) => {
    if (view === "verified" && item.live === undefined) return false;
    if (view === "selected" && !selectedIds.includes(item.id)) return false;
    if (kind !== "全部" && item.kind !== kind) return false;
    return `${item.name}${item.market}${item.code}`.toLowerCase().includes(query.toLowerCase());
  }), [view, query, kind, selectedIds]);
  const active = STRATEGIES.find((item) => item.id === activeId) ?? STRATEGIES[0];

  function toggleSelection(id: string): void {
    setSelectedIds((current) => current.includes(id) ? current.filter((item) => item !== id) : [...current, id]);
  }

  return (
    <div className={styles.page}>
      <div className={styles.left}>
        <nav className={styles.viewTabs} aria-label="策略库视图">
          {VIEWS.map((item, index) => <button type="button" key={item.id} className={view === item.id ? styles.activeView : ""} onClick={() => setView(item.id)}><b>0{index + 1}</b><strong>{item.label}</strong><small>{item.sub}</small></button>)}
        </nav>

        <main className={styles.library}>
          <div className={styles.toolbar}>
            <label className={styles.search}><span>⌕</span><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="搜索策略 / 市场 / 编号" /></label>
            <div className={styles.kinds}>{(["全部", "趋势", "均值回归", "NEMT", "套利", "AI"] as const).map((item) => <button type="button" key={item} className={kind === item ? styles.activeKind : ""} onClick={() => setKind(item)}>{item}</button>)}</div>
            <span className={styles.count}>{items.length.toString().padStart(2, "0")} STRATEGIES</span>
          </div>

          <div className={styles.tableHead}><span>策略 / 市场</span><span>回测表现</span><span>实测表现</span><span>风险</span><span>选择</span></div>
          <div className={styles.rows}>
            {items.map((item, index) => {
              const isSelected = selectedIds.includes(item.id);
              return <article key={item.id} className={`${styles.row} ${active.id === item.id ? styles.activeRow : ""}`} onClick={() => setActiveId(item.id)}>
                <div className={styles.identity}><em>{(index + 1).toString().padStart(2, "0")}</em><div><strong>{item.name}</strong><span>{item.code} · {item.kind} · {item.market} · {item.period}</span></div></div>
                <div className={styles.metrics}><strong>+{item.backtest}%</strong><span>SHARPE {item.sharpe.toFixed(2)} · DD {item.drawdown}%</span></div>
                <div className={styles.metrics}>{item.live !== undefined ? <><strong className={styles.live}>+{item.live}%</strong><span>{item.liveDays} DAYS · WR {item.winRate}%</span></> : <><strong className={styles.pending}>待实测</strong><span>BACKTEST ONLY</span></>}</div>
                <span className={`${styles.risk} ${styles[`risk${item.risk}`]}`}>{item.risk}</span>
                <button type="button" className={`${styles.selectButton} ${isSelected ? styles.chosen : ""}`} onClick={(event) => { event.stopPropagation(); toggleSelection(item.id); }}>{isSelected ? "已选择 ✓" : "选择 +"}</button>
              </article>;
            })}
          </div>
        </main>
      </div>

      <aside className={styles.inspector} aria-label="Emergentix 策略测试海报">
        <div className={styles.poster}><Image src={strategyPoster} alt="Emergentix 策略测试研究员海报" fill priority sizes="(max-width: 900px) 100vw, 47vw" /></div>
      </aside>
    </div>
  );
}
