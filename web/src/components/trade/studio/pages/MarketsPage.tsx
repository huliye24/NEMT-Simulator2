"use client";

import { ageLabel, fmtPct, fmtPrice } from "@/lib/trade/format";
import {
  EditorialPage,
  EditorialLink,
  Masthead,
  PageFootnote,
  StatusTag,
} from "../editorial/Editorial";
import { StudioIcon } from "../icons";
import MarketPanel from "../market/MarketPanel";
import type { StudioPageProps } from "../types";

export default function MarketsPage({ data, navigate }: StudioPageProps) {
  const { ticker, system } = data;
  const market = system?.market;
  const sourceLabel =
    ticker?.source === "binance"
      ? "Binance Spot"
      : ticker?.source === "demo"
        ? "Demo feed"
        : "—";

  return (
    <EditorialPage className="nsx-markets">
      <Masthead
        compact
        kicker="MARKET OBSERVATORY / 05"
        title="市场行情"
        accent="Read the structure, not the noise."
        lead="BTC/USDT 现货行情、24H 统计、多周期 K 线与数据新鲜度。图表保持金融数据的准确性，不做装饰化处理。"
        issue={{ label: "SPOT", value: "05", note: "BTC / USDT" }}
        actions={
          <>
            <StatusTag tone={ticker?.stale ? "warn" : ticker ? "ok" : "muted"}>
              {ticker?.stale
                ? "Stale data"
                : ticker
                  ? "Live feed"
                  : "Awaiting feed"}
            </StatusTag>
            <button
              type="button"
              className="nsx-btn is-small"
              onClick={() => void data.refreshAll()}
              disabled={data.syncing || !data.online}
            >
              <StudioIcon name="refresh" size={12} />
              {data.syncing ? "同步中…" : "刷新"}
            </button>
          </>
        }
      />

      <div className="nsx-market-layout">
        <div className="nsx-market-main">
          <MarketPanel data={data} variant="expanded" />
        </div>

        <aside className="nsx-market-rail" aria-label="行情数据边界">
          <div className="nsx-rail-block">
            <div className="nsx-eyebrow-row">
              <span>01</span>
              DATA INTEGRITY
            </div>
            <h3>数据来源与新鲜度</h3>
            <p>
              价格与 K 线仅来自 NEMT Cloud 行情服务。所有图表数据是真实金融数据，不包含装饰线稿。
            </p>
            <dl className="nsx-rail-facts">
              <div>
                <dt>Source</dt>
                <dd>{sourceLabel}</dd>
              </div>
              <div>
                <dt>Last tick</dt>
                <dd>{ticker ? ageLabel(ticker.fetched_at) : "—"}</dd>
              </div>
              <div>
                <dt>Freshness</dt>
                <dd>
                  {market
                    ? market.status === "ok"
                      ? "正常"
                      : market.status === "stale"
                        ? "延迟"
                        : "不可用"
                    : ticker
                      ? ticker.stale
                        ? "延迟"
                        : "正常"
                      : "—"}
                </dd>
              </div>
              <div>
                <dt>24H change</dt>
                <dd>{ticker ? fmtPct(ticker.price_change_percent) : "—"}</dd>
              </div>
              <div>
                <dt>Last price</dt>
                <dd>{ticker ? fmtPrice(ticker.last_price) : "—"}</dd>
              </div>
            </dl>
          </div>

          <div className="nsx-rail-block">
            <p className="nsx-aside-title">CHART BOUNDARY</p>
            <h3>行情不是叙事</h3>
            <p>
              K 线区域保持金融图表的原貌，不使用涂鸦、标题遮挡或装饰曲线。艺术语言只出现在页面排版、分隔与状态说明中。
            </p>
          </div>

          <div className="nsx-rail-block">
            <p className="nsx-aside-title">NEXT ACTION</p>
            <h3>只读观察</h3>
            <p>
              行情本身不会触发订单。交易写入与策略执行由服务端限额、授权和独立风控约束。
            </p>
            <div style={{ marginTop: 12 }}>
              <EditorialLink onClick={() => navigate("execution")}>
                查看执行边界
              </EditorialLink>
            </div>
          </div>
        </aside>
      </div>

      <PageFootnote
        center="Market data is rendered as financial data. Editorial illustration never enters the chart."
      />
    </EditorialPage>
  );
}
