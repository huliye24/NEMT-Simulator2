"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { tradeApi } from "@/lib/trade/api";
import type { Kline } from "@/lib/trade/types";
import { Spinner } from "../common";
import { StudioIcon } from "../icons";
import { ACTION_LABEL, annotateFills, summarize, type Fill } from "@/lib/studio/positionMath";
import styles from "./PositionDetail.module.css";

interface LegView {
  symbol: string;
  market: "PERPETUAL" | "SPOT" | "HEDGE";
  side: "LONG" | "SHORT" | "NEUTRAL";
  leverage: number;
  unit: string;
  mark: string;
  margin: string;
  fills: Fill[];
}

const MARKET_LABEL: Record<string, string> = { PERPETUAL: "合约", SPOT: "现货", HEDGE: "对冲" };
const SIDE_LABEL: Record<string, string> = { LONG: "做多", SHORT: "做空", NEUTRAL: "中性" };
const INTERVALS = ["5m", "15m", "1h", "4h", "1d"] as const;
const POLL_MS = 10_000;

function toNumber(value: string): number {
  return Number(value.replace(/[^0-9.-]/g, ""));
}
function signed(value: number, digits = 2): string {
  return `${value > 0 ? "+" : ""}${value.toFixed(digits)}`;
}
function clock(ts: number): string {
  return new Date(ts).toLocaleString("zh-CN", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

/* 网络不可用时用确定性随机游走兜底 */
function fallbackCandles(symbol: string, base: number, count = 300): Kline[] {
  let seed = 0;
  for (let i = 0; i < symbol.length; i += 1) seed = (seed * 31 + symbol.charCodeAt(i)) % 9973;
  let price = base * 0.99;
  const now = Date.now();
  return Array.from({ length: count }, (_, index) => {
    seed = (seed * 1103515245 + 12345) % 2147483648;
    const drift = (seed / 2147483648 - 0.5) * base * 0.0016;
    const open = price;
    const close = Math.max(base * 0.95, Math.min(base * 1.05, open + drift));
    const high = Math.max(open, close) + base * 0.0006;
    const low = Math.min(open, close) - base * 0.0006;
    price = close;
    const time = now - (count - index) * 15 * 60 * 1000;
    return {
      open_time: time,
      open_time_iso: new Date(time).toISOString(),
      open: open.toFixed(2),
      high: high.toFixed(2),
      low: low.toFixed(2),
      close: close.toFixed(2),
      volume: String(100 + (seed % 400)),
      close_time: time + 15 * 60 * 1000,
      is_closed: true,
    };
  });
}

export default function PositionDetail({
  leg,
  strategy,
  interval: initialInterval,
  onClose,
}: {
  leg: LegView;
  strategy: { name: string; code: string };
  interval: string;
  onClose: () => void;
}) {
  const [interval, setIntervalKey] = useState(initialInterval);
  const [candles, setCandles] = useState<Kline[] | null>(null);
  const [source, setSource] = useState<"live" | "offline">("live");
  const [updatedAt, setUpdatedAt] = useState<number | null>(null);

  const mark = toNumber(leg.mark);
  const summary = useMemo(() => summarize(leg.fills, mark, leg.side), [leg.fills, mark, leg.side]);
  const rows = useMemo(() => annotateFills(leg.fills, leg.side).slice().reverse(), [leg.fills, leg.side]);

  /* 实时 K 线：挂载后立刻拉一次，之后每 10s 刷新 */
  useEffect(() => {
    let cancelled = false;
    let timer = 0;
    const base = summary.avgCost || mark || 100;

    async function load() {
      try {
        const result = await tradeApi.getKlines(leg.symbol, interval, 300);
        if (cancelled) return;
        if (result.items.length) {
          setCandles(result.items);
          setSource("live");
        } else {
          setCandles((prev) => prev ?? fallbackCandles(leg.symbol, base));
          setSource("offline");
        }
      } catch {
        if (cancelled) return;
        setCandles((prev) => prev ?? fallbackCandles(leg.symbol, base));
        setSource("offline");
      }
      if (!cancelled) setUpdatedAt(Date.now());
    }

    void load();
    timer = window.setInterval(load, POLL_MS);
    return () => {
      cancelled = true;
      window.clearInterval(timer);
    };
  }, [leg.symbol, interval, summary.avgCost, mark]);

  useEffect(() => {
    function onKey(event: KeyboardEvent) {
      if (event.key === "Escape") onClose();
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  const totalPnl = summary.realized + summary.unrealized;

  return (
    <div className={styles.backdrop} role="presentation">
      <aside className={styles.panel} role="dialog" aria-label={`${leg.symbol} 持仓详情`}>
        <header className={styles.head}>
          <div>
            <div className={styles.titleRow}>
              <strong>{leg.symbol}</strong>
              <span className={styles.side} data-side={leg.side}>{SIDE_LABEL[leg.side]}</span>
              <span className={styles.tag}>{MARKET_LABEL[leg.market]}</span>
              <span className={styles.tag}>{leg.leverage} 倍杠杆</span>
              <span className={styles.tag}>{leg.fills.length} 笔成交</span>
            </div>
            <small>{strategy.name} · {strategy.code} · 均价来自剩余 {summary.lots.length} 个批次</small>
          </div>
          <button type="button" className={styles.close} onClick={onClose} aria-label="关闭详情">
            <StudioIcon name="close" size={14} />
          </button>
        </header>

        <div className={styles.stats}>
          <Stat label="持仓" value={`${summary.qty.toFixed(3)} ${leg.unit}`} />
          <Stat label="均价" value={summary.avgCost.toFixed(2)} note={`${summary.lots.length} 个批次`} />
          <Stat label="标记" value={leg.mark} note={`${signed(summary.priceChangePct)}%`} />
          <Stat label="未实现" value={`${signed(summary.unrealized)} USDT`} tone={summary.unrealized >= 0 ? "good" : "bad"} />
          <Stat label="已实现" value={`${signed(summary.realized)} USDT`} tone={summary.realized >= 0 ? "good" : "bad"} note={`手续费 ${summary.fees.toFixed(2)}`} />
          <Stat label="合计盈亏" value={`${signed(totalPnl)} USDT`} tone={totalPnl >= 0 ? "good" : "bad"} note={`保证金率 ${leg.margin}`} />
        </div>

        <section className={styles.chartCard}>
          <div className={styles.chartHead}>
            <div className={styles.chartTitle}>
              <strong>价格走势 · 分批成交点位</strong>
              <span className={styles.chartHintText}>滚轮缩放 · 拖拽平移 · 悬停查看</span>
            </div>
            <div className={styles.chartTools}>
              <div className={styles.intervals}>
                {INTERVALS.map((item) => (
                  <button
                    key={item}
                    type="button"
                    className={interval === item ? styles.intervalOn : ""}
                    onClick={() => setIntervalKey(item)}
                  >
                    {item}
                  </button>
                ))}
              </div>
              <span className={styles.liveDot} data-live={source === "live" ? "yes" : "no"} />
              <span className={styles.liveText}>
                {source === "live" ? "实时" : "离线模拟"}
                {updatedAt ? ` · ${new Date(updatedAt).toLocaleTimeString("zh-CN", { hour12: false })}` : ""}
              </span>
            </div>
          </div>
          {candles ? (
            <CandleChart candles={candles} fills={leg.fills} avg={summary.avgCost} mark={mark} side={leg.side} unit={leg.unit} />
          ) : (
            <div className={styles.chartLoading}>
              <Spinner size={14} /> 正在载入 K 线…
            </div>
          )}
        </section>

        <section className={styles.lotsCard}>
          <div className={styles.chartHead}>
            <strong>持仓批次（先进先出）</strong>
            <span>剩余 {summary.lots.length} 批</span>
          </div>
          <div className={styles.lots}>
            {summary.lots.length === 0 ? <p className={styles.lotsEmpty}>已无持仓</p> : summary.lots.map((lot, index) => (
              <div className={styles.lot} key={`${lot.at}-${index}`}>
                <em>#{index + 1}</em>
                <strong>{lot.qty.toFixed(3)} {leg.unit}</strong>
                <span>@ {lot.price.toFixed(2)}</span>
                <small>{clock(lot.at)}</small>
              </div>
            ))}
          </div>
        </section>

        <section className={styles.ledgerCard}>
          <div className={styles.chartHead}>
            <strong>成交流水</strong>
            <span>按时间倒序 · 共 {rows.length} 笔</span>
          </div>
          <table className={styles.table}>
            <thead>
              <tr><th>时间</th><th>动作</th><th>数量</th><th>价格</th><th>手续费</th><th>成交后持仓</th><th>已实现</th></tr>
            </thead>
            <tbody>
              {rows.map((row) => (
                <tr key={`${row.at}-${row.action}-${row.qty}`}>
                  <td>{clock(row.at)}</td>
                  <td>
                    <b className={row.action === "REDUCE" || row.action === "CLOSE" ? styles.actionOut : styles.actionIn}>
                      {ACTION_LABEL[row.action]}
                    </b>
                  </td>
                  <td>{row.qty.toFixed(3)} {leg.unit}</td>
                  <td>{row.price.toFixed(2)}</td>
                  <td>{row.fee.toFixed(2)}</td>
                  <td>{row.qtyAfter.toFixed(3)}</td>
                  <td className={row.realized === 0 ? styles.muted : row.realized >= 0 ? styles.ok : styles.bad}>
                    {row.realized === 0 ? "—" : `${signed(row.realized)} USDT`}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      </aside>
    </div>
  );
}

function Stat({ label, value, note, tone }: { label: string; value: string; note?: string; tone?: "good" | "bad" }) {
  return (
    <div className={styles.stat}>
      <span>{label}</span>
      <strong className={tone === "good" ? styles.good : tone === "bad" ? styles.bad : ""}>{value}</strong>
      {note ? <small>{note}</small> : null}
    </div>
  );
}

const W = 1500;
const H = 470;
const LEFT = 10;
const RIGHT = 78;
const PAD_TOP = 16;
const AXIS_H = 22;
const VOL_H = 84;
const GAP = 10;
const PLOT_W = W - LEFT - RIGHT;
const PRICE_BOTTOM = H - AXIS_H - VOL_H - GAP;
const VOL_TOP = PRICE_BOTTOM + GAP;
const VOL_BOTTOM = VOL_TOP + VOL_H;

function fmtVolume(value: number): string {
  if (value >= 1_000_000) return `${(value / 1_000_000).toFixed(1)}M`;
  if (value >= 1000) return `${(value / 1000).toFixed(1)}K`;
  return value.toFixed(0);
}

interface AxisTag {
  key: string;
  price: number;
  color: string;
  text: string;
}

function CandleChart({
  candles,
  fills,
  avg,
  mark,
  side,
  unit,
}: {
  candles: Kline[];
  fills: Fill[];
  avg: number;
  mark: number;
  side: string;
  unit: string;
}) {
  const [count, setCount] = useState(90);
  const [offset, setOffset] = useState(0);
  const [hover, setHover] = useState<{ index: number; x: number; y: number } | null>(null);
  const [dragging, setDragging] = useState(false);
  const dragRef = useRef<{ x: number; offset: number } | null>(null);

  const total = candles.length;
  const visibleCount = Math.max(12, Math.min(count, total));
  const end = Math.max(visibleCount, total - offset);
  const start = end - visibleCount;
  const visible = candles.slice(start, end);
  const accent = side === "SHORT" ? "#df5148" : "#109d83";

  const geometry = useMemo(() => {
    const highs = visible.map((c) => Number(c.high));
    const lows = visible.map((c) => Number(c.low));
    const max = Math.max(...highs, avg, mark);
    const min = Math.min(...lows, avg, mark);
    const span = max - min || 1;
    const cw = PLOT_W / visible.length;
    const volMax = Math.max(1, ...visible.map((c) => Number(c.volume)));
    const y = (price: number) => PAD_TOP + ((max - price) / span) * (PRICE_BOTTOM - PAD_TOP);
    const priceAt = (py: number) => max - ((py - PAD_TOP) / (PRICE_BOTTOM - PAD_TOP)) * span;
    const x = (index: number) => LEFT + (index + 0.5) * cw;
    return { max, min, span, cw, y, priceAt, x, volMax };
  }, [visible, avg, mark]);

  const { max, min, cw, y, priceAt, x, volMax } = geometry;

  const clampOffset = useCallback(
    (next: number) => Math.max(0, Math.min(total - visibleCount, next)),
    [total, visibleCount]
  );

  function onWheel(event: React.WheelEvent<HTMLDivElement>) {
    event.preventDefault();
    const rect = event.currentTarget.getBoundingClientRect();
    const ratio = Math.min(1, Math.max(0, (event.clientX - rect.left) / rect.width));
    const anchor = start + ratio * visibleCount;
    const factor = event.deltaY > 0 ? 1.16 : 0.86;
    const nextCount = Math.max(12, Math.min(total, Math.round(visibleCount * factor)));
    const nextStart = anchor - ratio * nextCount;
    setCount(nextCount);
    setOffset(clampOffset(total - (nextStart + nextCount)));
  }

  function onPointerDown(event: React.PointerEvent<HTMLDivElement>) {
    dragRef.current = { x: event.clientX, offset };
    setDragging(true);
    event.currentTarget.setPointerCapture(event.pointerId);
  }

  function onPointerMove(event: React.PointerEvent<HTMLDivElement>) {
    const rect = event.currentTarget.getBoundingClientRect();
    const scale = W / rect.width;
    const localX = (event.clientX - rect.left) * scale;
    const localY = (event.clientY - rect.top) * (H / rect.height);
    const index = Math.floor((localX - LEFT) / cw);
    setHover(
      index >= 0 && index < visible.length && localY < PRICE_BOTTOM
        ? { index, x: localX, y: Math.max(PAD_TOP, Math.min(PRICE_BOTTOM, localY)) }
        : null
    );

    const drag = dragRef.current;
    if (!drag) return;
    const dx = (event.clientX - drag.x) * scale;
    if (Math.abs(dx) < 1.5) return;
    setOffset(clampOffset(drag.offset + Math.round(dx / cw)));
  }

  function onPointerUp() {
    dragRef.current = null;
    setDragging(false);
  }

  const last = visible[visible.length - 1];
  const lastPrice = last ? Number(last.close) : mark;
  const lastUp = last ? Number(last.close) >= Number(last.open) : true;

  const rawTags: AxisTag[] = [
    { key: "last", price: lastPrice, color: lastUp ? "#109d83" : "#df5148", text: lastPrice.toFixed(2) },
    { key: "avg", price: avg, color: accent, text: `AVG ${avg.toFixed(2)}` },
    { key: "mark", price: mark, color: "#4f5a63", text: `MARK ${mark.toFixed(2)}` },
  ];
  if (hover) {
    rawTags.push({ key: "cursor", price: priceAt(hover.y), color: "#171b20", text: priceAt(hover.y).toFixed(2) });
  }
  const placed = rawTags
    .map((tag) => ({ ...tag, ty: y(tag.price) }))
    .sort((a, b) => a.ty - b.ty)
    .reduce<Array<AxisTag & { ty: number }>>((acc, tag) => {
      const prev = acc[acc.length - 1];
      const ty = prev ? Math.max(tag.ty, prev.ty + 19) : tag.ty;
      acc.push({ ...tag, ty: Math.min(ty, PRICE_BOTTOM - 9) });
      return acc;
    }, []);

  const hovered = hover ? visible[hover.index] : null;
  const hoverPct = hovered
    ? ((Number(hovered.close) - Number(hovered.open)) / Number(hovered.open)) * 100
    : 0;

  return (
    <div
      className={styles.chartWrap}
      data-dragging={dragging ? "yes" : "no"}
      onWheel={onWheel}
      onPointerDown={onPointerDown}
      onPointerMove={onPointerMove}
      onPointerUp={onPointerUp}
      onPointerLeave={() => {
        setHover(null);
        dragRef.current = null;
        setDragging(false);
      }}
    >
      <svg className={styles.chart} viewBox={`0 0 ${W} ${H}`} preserveAspectRatio="xMidYMid meet" role="img" aria-label="可交互 K 线图">
        {/* 价格网格 + 右侧价格刻度 */}
        {[max, (max + min) / 2, min].map((price) => (
          <g key={price}>
            <line x1={LEFT} x2={W - RIGHT} y1={y(price)} y2={y(price)} className={styles.gridLine} />
            <text x={W - RIGHT + 8} y={y(price) + 4} className={styles.axisText}>{price.toFixed(2)}</text>
          </g>
        ))}

        {/* 蜡烛 */}
        {visible.map((candle, index) => {
          const open = Number(candle.open);
          const close = Number(candle.close);
          const high = Number(candle.high);
          const low = Number(candle.low);
          const up = close >= open;
          const cx = x(index);
          const top = y(Math.max(open, close));
          const bottom = y(Math.min(open, close));
          return (
            <g key={candle.open_time} className={up ? styles.up : styles.down}>
              <line x1={cx} x2={cx} y1={y(high)} y2={y(low)} className={styles.wick} />
              <rect x={cx - Math.max(1.5, cw * 0.32)} y={top} width={Math.max(3, cw * 0.64)} height={Math.max(1.5, bottom - top)} className={styles.body} />
            </g>
          );
        })}

        {/* 成交量 */}
        <line x1={LEFT} x2={W - RIGHT} y1={VOL_TOP - GAP / 2} y2={VOL_TOP - GAP / 2} stroke="#d8d4cc" />
        {visible.map((candle, index) => {
          const up = Number(candle.close) >= Number(candle.open);
          const height = (Number(candle.volume) / volMax) * (VOL_H - 6);
          return (
            <rect
              key={`v-${candle.open_time}`}
              x={x(index) - Math.max(1.5, cw * 0.32)}
              y={VOL_BOTTOM - height}
              width={Math.max(3, cw * 0.64)}
              height={Math.max(1, height)}
              className={up ? styles.volUp : styles.volDown}
            />
          );
        })}
        <text x={W - RIGHT + 8} y={VOL_TOP + 10} className={styles.axisText}>{fmtVolume(volMax)}</text>
        <text x={LEFT + 2} y={VOL_TOP - 6} className={styles.volLabel}>VOL {unit}</text>

        {/* 均价 / 标记 */}
        <line x1={LEFT} x2={W - RIGHT} y1={y(avg)} y2={y(avg)} stroke={accent} strokeWidth="1.3" strokeDasharray="6 4" />
        <line x1={LEFT} x2={W - RIGHT} y1={y(mark)} y2={y(mark)} stroke="#4f5a63" strokeWidth="1" strokeDasharray="2 5" />

        {/* 分批成交点位 */}
        {fills.map((fill, index) => {
          const candleIndex = candles.findIndex((candle) => candle.open_time >= fill.at);
          const local = candleIndex - start;
          if (local < 0 || local >= visible.length) return null;
          const fx = x(local);
          const fy = y(fill.price);
          const isOpen = fill.action === "OPEN" || fill.action === "ADD";
          const color = isOpen ? accent : "#b07a12";
          const tip = (
            <title>{`${ACTION_LABEL[fill.action]} · ${fill.qty} ${unit} @ ${fill.price.toFixed(2)} · ${clock(fill.at)}`}</title>
          );
          return isOpen ? (
            <polygon key={`${fill.at}-${index}`} points={`${fx},${fy - 8} ${fx - 6},${fy + 4} ${fx + 6},${fy + 4}`} fill={color} opacity="0.95">{tip}</polygon>
          ) : (
            <polygon key={`${fill.at}-${index}`} points={`${fx},${fy + 8} ${fx - 6},${fy - 4} ${fx + 6},${fy - 4}`} fill="none" stroke={color} strokeWidth="1.6">{tip}</polygon>
          );
        })}

        {/* 最新价水平线 */}
        <line x1={LEFT} x2={W - RIGHT} y1={y(lastPrice)} y2={y(lastPrice)} stroke={lastUp ? "#109d83" : "#df5148"} strokeWidth="1" opacity="0.55" strokeDasharray="4 4" />

        {/* 十字光标 */}
        {hover ? (
          <>
            <line x1={hover.x} x2={hover.x} y1={PAD_TOP} y2={VOL_BOTTOM} stroke="#171b20" strokeWidth="1" strokeDasharray="3 3" opacity="0.4" />
            <line x1={LEFT} x2={W - RIGHT} y1={hover.y} y2={hover.y} stroke="#171b20" strokeWidth="1" strokeDasharray="3 3" opacity="0.22" />
          </>
        ) : null}

        {/* 时间轴 */}
        <line x1={LEFT} x2={W - RIGHT} y1={VOL_BOTTOM} y2={VOL_BOTTOM} stroke="#d8d4cc" />
        {[0, Math.floor(visible.length / 2), visible.length - 1].map((index) => {
          if (!visible[index]) return null;
          return (
            <text key={index} x={x(index)} y={H - 6} textAnchor="middle" className={styles.axisText}>
              {new Date(visible[index].open_time).toLocaleTimeString("zh-CN", { hour: "2-digit", minute: "2-digit" })}
            </text>
          );
        })}

        {/* 右侧价格标签（最新价 / AVG / MARK / 光标） */}
        {placed.map((tag) => (
          <g key={tag.key}>
            <rect x={W - RIGHT + 1} y={tag.ty - 9} width={RIGHT - 2} height={18} fill={tag.color} opacity={tag.key === "last" ? 1 : 0.92} />
            <text x={W - RIGHT / 2} y={tag.ty + 4} textAnchor="middle" className={styles.axisTag}>{tag.text}</text>
          </g>
        ))}
      </svg>

      {hovered ? (
        <div className={styles.tooltip} style={{ left: `${(hover!.x / W) * 100}%`, top: 8 }}>
          <strong>{new Date(hovered.open_time).toLocaleString("zh-CN", { month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit" })}</strong>
          <span>开 {Number(hovered.open).toFixed(2)}　高 {Number(hovered.high).toFixed(2)}</span>
          <span>低 {Number(hovered.low).toFixed(2)}　收 {Number(hovered.close).toFixed(2)}</span>
          <span>量 {fmtVolume(Number(hovered.volume))} {unit}　<span className={hoverPct >= 0 ? styles.good : styles.bad}>{signed(hoverPct)}%</span></span>
        </div>
      ) : null}
    </div>
  );
}
