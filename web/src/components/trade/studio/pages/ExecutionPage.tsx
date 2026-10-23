"use client";

import { useCallback, useEffect, useState } from "react";
import type { StudioPageProps } from "../types";
import PositionDetail from "../execution/PositionDetail";
import { legSummary, signed, type Leg, type LegSide, type Market, type Strategy } from "@/lib/studio/demoPortfolio";
import { ApiError, tradeApi } from "@/lib/trade/api";
import { fmtTime } from "@/lib/trade/format";
import type { StrategyBoard } from "@/lib/trade/types";
import styles from "./ExecutionPage.module.css";

const MARKET_LABEL: Record<Market, string> = { PERPETUAL: "合约", SPOT: "现货", HEDGE: "对冲" };
const SIDE_LABEL: Record<LegSide, string> = { LONG: "做多", SHORT: "做空", NEUTRAL: "中性" };
const POLL_MS = 5_000;

/**
 * The execution page renders the *auto trader's* book, not a fixture: the
 * backend evaluates NEMT signals and opens/closes paper positions on its own.
 * 「暂停」 is a real kill switch for that loop, and 「日志」 shows its journal.
 */
export default function ExecutionPage({ session, notify }: StudioPageProps) {
  const [board, setBoard] = useState<StrategyBoard | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [selected, setSelected] = useState("BTC/USDT");
  const [logFor, setLogFor] = useState<string | null>(null);
  const [query, setQuery] = useState("");
  const [collapsed, setCollapsed] = useState<string[]>([]);
  const [busy, setBusy] = useState(false);
  const [detail, setDetail] = useState<{ leg: Leg; strategy: Strategy } | null>(null);

  const load = useCallback(async () => {
    try {
      const next = await tradeApi.getStrategyBoard();
      setBoard(next);
      setError(null);
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : "策略看板不可用");
    }
  }, []);

  useEffect(() => {
    void load();
    const timer = window.setInterval(() => {
      if (!document.hidden) void load();
    }, POLL_MS);
    return () => window.clearInterval(timer);
  }, [load]);

  async function toggleAutoTrade() {
    if (!board || busy) return;
    const next = !board.auto_trade.enabled;
    setBusy(true);
    try {
      await tradeApi.setAutoTrade(session.csrf_token, next);
      notify(
        "success",
        next ? "策略已启动：服务端将按 NEMT 信号自动开平仓" : "策略已暂停：不再自动开仓"
      );
      await load();
    } catch (caught) {
      notify("error", caught instanceof ApiError ? caught.message : "切换失败");
    } finally {
      setBusy(false);
    }
  }

  function toggleCollapse(id: string) {
    setCollapsed((current) => (current.includes(id) ? current.filter((item) => item !== id) : [...current, id]));
  }

  const strategies: Strategy[] = board
    ? [
        {
          id: board.strategy.id,
          name: board.strategy.name,
          code: board.strategy.code,
          version: board.strategy.version,
          timeframe: board.strategy.timeframe,
          state: board.strategy.state,
          signal: board.strategy.signal,
          risk: board.strategy.risk,
          legs: board.strategy.legs as unknown as Leg[],
        },
      ]
    : [];

  const keyword = query.trim().toLowerCase();
  const groups = strategies
    .map((strategy) => {
      if (!keyword) return strategy;
      const metaHit = [strategy.name, strategy.code, strategy.version, strategy.timeframe]
        .join(" ")
        .toLowerCase()
        .includes(keyword);
      if (metaHit) return strategy;
      const legs = strategy.legs.filter((leg) =>
        [leg.symbol, leg.market, leg.side, MARKET_LABEL[leg.market], SIDE_LABEL[leg.side], `${leg.leverage}倍杠杆`]
          .join(" ")
          .toLowerCase()
          .includes(keyword)
      );
      return { ...strategy, legs };
    })
    .filter((strategy) => strategy.legs.length > 0);
  const totalLegs = groups.reduce((count, strategy) => count + strategy.legs.length, 0);
  const autoTrade = board?.auto_trade;
  const events = board?.events ?? [];

  const emptyText = !board
    ? error ?? "正在读取策略看板…"
    : query
      ? `没有匹配「${query}」的持仓或策略`
      : autoTrade?.enabled
        ? "策略运行中 · 当前无持仓，等待 NEMT 临界信号（H>0.7 且 |ψ|>0.5%）"
        : "策略已暂停 · 点击下方「启动」恢复自动开仓";

  return <div className={styles.page}>
    <section className={styles.book}>
      <div className={styles.positionHeader}>
        <span>策略</span><span>持仓</span><span>价格</span><span>未实现盈亏</span><span>保证金率</span><span>详情</span>
        <label className={styles.searchBox}>
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M10.4 3.4c3.7-.9 7.2 1.3 8.1 5 .9 3.6-1.2 7.2-4.8 8.1-3.7.9-7.2-1.2-8.2-4.8-.9-3.6 1.2-7.4 4.9-8.3Z" stroke="currentColor" strokeWidth="2.6" strokeLinecap="round"/><path d="M17.1 15.6l4.6 5.1" stroke="currentColor" strokeWidth="3.4" strokeLinecap="round"/><path d="M3.6 20.2l4.6-1.1" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" opacity=".5"/></svg>
          <input value={query} onChange={(event) => setQuery(event.target.value)} aria-label="搜索持仓"/>
        </label>
      </div>

      {totalLegs === 0 ? <p className={styles.emptyRow}>{emptyText}</p> : null}

      {groups.map((strategy) => {
        const total = strategy.legs.reduce((sum, leg) => sum + legSummary(leg).unrealized, 0);
        const isCollapsed = !keyword && collapsed.includes(strategy.id);
        return <article className={styles.group} key={strategy.id} data-collapsed={isCollapsed ? "yes" : "no"}>
          <header
            className={styles.groupHead}
            role="button"
            tabIndex={0}
            aria-expanded={!isCollapsed}
            onClick={() => toggleCollapse(strategy.id)}
            onKeyDown={(event) => {
              if (event.key === "Enter" || event.key === " ") {
                event.preventDefault();
                toggleCollapse(strategy.id);
              }
            }}
          >
            <span className={styles.groupChevron} title={isCollapsed ? "展开策略" : "收起策略"} aria-hidden="true"><svg width="11" height="11" viewBox="0 0 24 24" fill="none"><path d={isCollapsed ? "M9 5l7 7-7 7" : "M5 9l7 7 7-7"} stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"/></svg></span>
            <div className={styles.groupIdentity}>
              <div className={styles.groupTitle}>
                <span className={strategy.state === "运行中" ? styles.live : styles.hold}><i />{strategy.state}</span>
                <strong>{strategy.name}</strong>
                <small>{strategy.code} · {strategy.version} · {strategy.timeframe} · Risk {strategy.risk}</small>
              </div>
              <em>{strategy.signal}</em>
            </div>
            <div className={styles.groupStats}>
              <span>{strategy.legs.length > 1 ? `组合 · ${strategy.legs.length} 个持仓` : "单币策略"}</span>
              <strong className={total >= 0 ? styles.goodText : styles.badText}>{signed(total)} USDT</strong>
            </div>
            <div className={styles.strategyActions} onClick={(event) => event.stopPropagation()}>
              <button onClick={() => notify("info", `${strategy.name} 参数：${strategy.timeframe} 周期，单笔风险 ${strategy.risk}`)}>编辑</button>
              <button
                disabled={busy}
                className={strategy.state === "运行中" ? styles.pause : styles.start}
                onClick={() => void toggleAutoTrade()}
              >
                {strategy.state === "运行中" ? "暂停" : "启动"}
              </button>
              <button className={logFor === strategy.id ? styles.logOn : ""} onClick={() => setLogFor((current) => (current === strategy.id ? null : strategy.id))}>日志</button>
            </div>
          </header>

          {isCollapsed ? null : strategy.legs.map((leg) => {
            const s = legSummary(leg);
            return <div key={leg.symbol} className={`${styles.leg} ${selected === leg.symbol ? styles.selected : ""}`} onClick={() => setSelected(leg.symbol)}>
              <div className={styles.instrument}>
                <span>{MARKET_LABEL[leg.market]} · {leg.leverage} 倍杠杆 · {s.lots.length} 批次</span>
                <strong>{leg.symbol}</strong>
                <b className={leg.side === "SHORT" ? styles.short : leg.side === "NEUTRAL" ? styles.neutral : styles.long}>{SIDE_LABEL[leg.side]}</b>
              </div>
              <div className={styles.value}><strong>{s.qty.toFixed(3)} {leg.unit}</strong></div>
              <div className={styles.priceCell}>
                <span><em>AVG</em><b>{s.avgCost.toFixed(2)}</b></span>
                <span><em>MARK</em><b>{leg.mark}</b><small className={styles.dev}>{s.priceChangePct >= 0 ? "▲" : "▼"} {signed(s.priceChangePct)}%</small></span>
              </div>
              <div className={styles.value}>
                <strong className={s.unrealized >= 0 ? styles.goodText : styles.badText}>{signed(s.unrealized)} USDT</strong>
                <small>{s.realized !== 0 ? `已实现 ${signed(s.realized)}` : "无已实现"}</small>
              </div>
              <div className={styles.value}><strong>{leg.margin}</strong></div>
              <div className={styles.legAction}>
                <button type="button" onClick={(event) => { event.stopPropagation(); setDetail({ leg, strategy }); }}>详情</button>
              </div>
            </div>;
          })}

          {!isCollapsed && logFor === strategy.id ? (
            <ol className={styles.logList}>
              {events.length === 0 ? <li>暂无策略事件</li> : events.slice(0, 12).map((event) => (
                <li key={event.id}>{fmtTime(event.ts)} · {event.symbol ?? "—"} {event.action} · {event.reason}</li>
              ))}
            </ol>
          ) : null}
        </article>;
      })}
    </section>

    {detail ? <PositionDetail
      leg={detail.leg}
      strategy={{ name: detail.strategy.name, code: detail.strategy.code }}
      interval={detail.strategy.timeframe}
      onClose={() => setDetail(null)}
    /> : null}
  </div>;
}
