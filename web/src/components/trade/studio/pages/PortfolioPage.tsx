"use client";

import { ageLabel, fmtQty, fmtUSDT } from "@/lib/trade/format";
import { accountEquity, findAsset } from "../account/AccountSummary";
import { EmptyState, Skeleton, StatusDot } from "../common";
import {
  EditorialPage,
  Masthead,
  PageFootnote,
  StatusTag,
} from "../editorial/Editorial";
import { AbstractPlate } from "../editorial/AbstractPlate";
import { StudioIcon } from "../icons";
import type { StudioPageProps } from "../types";

export default function PortfolioPage({ data }: StudioPageProps) {
  const { balances, ticker } = data;
  const usdt = findAsset(data, "USDT");
  const btc = findAsset(data, "BTC");
  const lastPrice = Number(ticker?.last_price ?? 0);
  const equity = accountEquity(data);
  const assets = balances?.balances ?? [];
  const connected = Boolean(balances?.connected);

  const btcValue = btc.total * lastPrice;
  const usdtValue = usdt.total;
  const allocationTotal = usdtValue + btcValue;
  const btcShare = allocationTotal > 0 ? (btcValue / allocationTotal) * 100 : 0;
  const usdtShare = allocationTotal > 0 ? (usdtValue / allocationTotal) * 100 : 0;
  const btcPriceMissing = btc.total > 0 && lastPrice <= 0;

  function formatAmount(asset: string, value: string | null | undefined): string {
    if (!balances) return "—";
    return asset === "USDT" ? fmtUSDT(value) : fmtQty(value);
  }

  function valuation(asset: string, total: string): string {
    const value = Number(total);
    if (!Number.isFinite(value)) return "—";
    if (asset === "USDT") return `${fmtUSDT(value)} USDT`;
    if (asset === "BTC" && lastPrice > 0) return `≈ ${fmtUSDT(value * lastPrice)} USDT`;
    return "—";
  }

  return (
    <EditorialPage className="nsx-portfolio">
      <Masthead
        compact
        kicker="ACCOUNT / PORTFOLIO · 06"
        title="资产组合"
        accent="Exposure, measured honestly."
        lead="现货资产、配置与已知敞口。未接入的收益与回撤指标保持缺失状态；界面不会估算不存在的历史净值。"
        issue={{ label: "SPOT ACCOUNT", value: "06", note: "USDT VALUATION" }}
        actions={
          <>
            <StatusTag tone={connected ? "ok" : "muted"}>
              {connected ? "Account connected" : "Snapshot waiting"}
            </StatusTag>
            <button
              type="button"
              className="nsx-btn is-small"
              onClick={() => void data.refreshAll()}
              disabled={data.syncing || !data.online}
            >
              <StudioIcon name="refresh" size={12} />
              {data.syncing ? "同步中…" : "刷新快照"}
            </button>
          </>
        }
      />

      <section className="nsx-portfolio-hero" aria-label="Capital position">
        <div className="nsx-portfolio-equity">
          <div className="nsx-eyebrow-row">
            <span>01</span>
            CAPITAL POSITION
          </div>
          <p className="nsx-equity-label">TOTAL EQUITY / USDT</p>
          <div className="nsx-equity">
            {balances ? fmtUSDT(equity) : <span>读取中…</span>}
            {balances ? <span>USDT</span> : null}
          </div>
          <p className="nsx-freshness">
            <StatusDot
              tone={balances ? (connected ? "ok" : "bad") : "muted"}
              pulse={connected}
            />
            {balances
              ? `账户快照 · ${ageLabel(balances.fetched_at)}更新`
              : "正在读取账户快照"}
          </p>
          <p className="nsx-note" style={{ marginTop: 18, maxWidth: 560 }}>
            <strong>Realized PnL · Unrealized PnL · Drawdown — 尚无数据。</strong>{" "}
            需要成交成本基础、持仓成本与服务端净值历史。界面不以 0、估算值或装饰曲线代替缺失。
          </p>
        </div>

        <div className="nsx-portfolio-numbers">
          <div className="nsx-portfolio-number">
            <span>Available / 可用</span>
            <strong>{balances ? fmtUSDT(usdt.free) : "—"}</strong>
            <p>USDT</p>
          </div>
          <div className="nsx-portfolio-number">
            <span>BTC exposure / 敞口</span>
            <strong>
              {balances ? (btcPriceMissing ? "—" : fmtUSDT(btcValue)) : "—"}
            </strong>
            <p>
              {balances
                ? btcPriceMissing
                  ? "行情缺失，暂无法估值"
                  : `USDT · ${fmtQty(btc.total)} BTC · 占组合 ${btcShare.toFixed(1)}%`
                : "等待账户快照"}
            </p>
          </div>
          <div className="nsx-portfolio-number">
            <span>Snapshot source</span>
            <strong>
              {balances?.source === "demo"
                ? "DEMO ledger"
                : balances?.source === "binance"
                  ? "Binance"
                  : balances?.source ?? "—"}
            </strong>
            <p>只读账户快照</p>
          </div>
          <div className="nsx-portfolio-number">
            <span>Snapshot age</span>
            <strong>
              {balances?.fetched_at ? ageLabel(balances.fetched_at) : "—"}
            </strong>
            <p>{connected ? "账户已连接" : "等待连接"}</p>
          </div>
        </div>
      </section>

      <div className="nsx-portfolio-sections">
        <section className="nsx-portfolio-block" aria-label="Equity history">
          <div className="nsx-block-head">
            <div>
              <div className="nsx-eyebrow-row">
                <span>02</span>
                EQUITY CURVE
              </div>
              <h2>净值曲线</h2>
            </div>
            <StatusTag tone="muted">No history</StatusTag>
          </div>
          <div style={{ marginTop: 16 }}>
            <AbstractPlate
              variant="empty"
              label="EQUITY CURVE"
              caption="尚未接入净值历史 · 空白是真实状态，不是一条 0 收益曲线"
            />
          </div>
          <p className="nsx-note" style={{ marginTop: 10 }}>
            当前只有单一账户快照。历史快照接入后才会显示净值、收益与回撤；不会虚构历史表现。
          </p>
        </section>

        <section className="nsx-portfolio-block" aria-label="Asset allocation">
          <div className="nsx-block-head">
            <div>
              <div className="nsx-eyebrow-row">
                <span>03</span>
                ASSET ALLOCATION
              </div>
              <h2>资产配置</h2>
            </div>
            <StatusTag tone="muted">Spot</StatusTag>
          </div>

          <div style={{ marginTop: 18 }}>
            {!balances ? (
              <div className="ns-pf-allocation-loading">
                <Skeleton className="ns-skeleton-row" />
                <Skeleton className="ns-skeleton-row" />
              </div>
            ) : allocationTotal <= 0 ? (
              <EmptyState
                compact
                icon="assets"
                title="暂无资产配置"
                body="账户中没有可估值的资产。"
              />
            ) : (
              <>
                <div className="ns-allocation-bar" aria-hidden="true">
                  {btcShare > 0 ? (
                    <span
                      className="ns-allocation-segment is-btc"
                      style={{ width: `${btcShare}%` }}
                    />
                  ) : null}
                  {usdtShare > 0 ? (
                    <span
                      className="ns-allocation-segment is-usdt"
                      style={{ width: `${usdtShare}%` }}
                    />
                  ) : null}
                </div>
                <ul className="ns-allocation-list">
                  <li>
                    <span className="ns-allocation-name">
                      <span className="ns-asset-token ns-asset-token-btc">₿</span>
                      BTC
                    </span>
                    <span className="ns-allocation-values">
                      <strong className="ns-number">{btcShare.toFixed(1)}%</strong>
                      <em>{fmtUSDT(btcValue)} USDT</em>
                    </span>
                  </li>
                  <li>
                    <span className="ns-allocation-name">
                      <span className="ns-asset-token ns-asset-token-usdt">U</span>
                      USDT
                    </span>
                    <span className="ns-allocation-values">
                      <strong className="ns-number">{usdtShare.toFixed(1)}%</strong>
                      <em>{fmtUSDT(usdtValue)} USDT</em>
                    </span>
                  </li>
                </ul>
                {btcPriceMissing ? (
                  <p className="ns-pf-note">
                    行情缺失：BTC 暂按 0 估值，配置比例不完整。
                  </p>
                ) : (
                  <p className="ns-pf-allocation-note">
                    配置基于当前账户快照与最新 BTC
                    参考价，不含未接入的衍生品或策略仓位。
                  </p>
                )}
              </>
            )}
          </div>
        </section>
      </div>

      <section className="ns-pf-balances" aria-label="资产余额明细">
        <div className="ns-pf-balances-head">
          <div>
            <div className="nsx-eyebrow-row">
              <span>04</span>
              BALANCES
            </div>
            <h2>资产余额</h2>
            <p>
              {balances?.source === "demo"
                ? "DEMO 模拟账本"
                : balances?.source === "binance"
                  ? "Binance 只读账户"
                  : "等待账户连接"}
            </p>
          </div>
          <div className="ns-pf-balances-state">
            <span className="ns-data-source-pill">
              <StatusDot
                tone={!balances ? "muted" : connected ? "ok" : "bad"}
                pulse={connected}
              />
              {!balances
                ? "加载中"
                : balances.account_status === "CONNECTED"
                  ? "已连接"
                  : balances.account_status}
            </span>
            <span className="ns-muted-value">
              {balances?.fetched_at
                ? `快照 ${ageLabel(balances.fetched_at)}更新`
                : "—"}
            </span>
          </div>
        </div>

        {!balances ? (
          data.coreError ? (
            <EmptyState
              icon="warning"
              title="账户快照暂不可用"
              body={data.coreError}
              action={
                <button
                  type="button"
                  className="ns-btn ns-btn-outline ns-btn-sm"
                  onClick={() => void data.refreshAll()}
                >
                  重新获取
                </button>
              }
            />
          ) : (
            <div className="ns-balances-skeleton">
              <Skeleton className="ns-skeleton-row" />
              <Skeleton className="ns-skeleton-row" />
            </div>
          )
        ) : assets.length === 0 ? (
          <EmptyState
            icon="assets"
            title="账户中没有可用资产"
            body="连接账户或向模拟账本注入资金后，余额会显示在这里。"
          />
        ) : (
          <div className="ns-table-scroll">
            <table className="ns-data-table ns-balances-table">
              <thead>
                <tr>
                  <th>资产</th>
                  <th className="is-numeric">可用</th>
                  <th className="is-numeric">冻结</th>
                  <th className="is-numeric">总额</th>
                  <th className="is-numeric">参考估值</th>
                </tr>
              </thead>
              <tbody>
                {assets.map((asset) => (
                  <tr key={asset.asset}>
                    <td>
                      <span className="ns-asset-name">
                        <span
                          className={`ns-asset-token ns-asset-token-${asset.asset.toLowerCase()}`}
                        >
                          {asset.asset === "BTC" ? "₿" : asset.asset.slice(0, 1)}
                        </span>
                        <span>
                          <strong>{asset.asset}</strong>
                          <em>
                            {asset.asset === "USDT"
                              ? "Tether"
                              : asset.asset === "BTC"
                                ? "Bitcoin"
                                : "Asset"}
                          </em>
                        </span>
                      </span>
                    </td>
                    <td className="is-numeric ns-number">
                      {formatAmount(asset.asset, asset.free)}
                    </td>
                    <td className="is-numeric ns-number ns-muted-cell">
                      {formatAmount(asset.asset, asset.locked)}
                    </td>
                    <td className="is-numeric ns-number">
                      {formatAmount(asset.asset, asset.total)}
                    </td>
                    <td className="is-numeric ns-number ns-muted-cell">
                      {valuation(asset.asset, asset.total)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            <div className="ns-balance-mobile-list">
              {assets.map((asset) => (
                <article
                  className="ns-balance-mobile-row"
                  key={`${asset.asset}-mobile`}
                >
                  <span className="ns-asset-name">
                    <span
                      className={`ns-asset-token ns-asset-token-${asset.asset.toLowerCase()}`}
                    >
                      {asset.asset === "BTC" ? "₿" : asset.asset.slice(0, 1)}
                    </span>
                    <span>
                      <strong>{asset.asset}</strong>
                      <em>{valuation(asset.asset, asset.total)}</em>
                    </span>
                  </span>
                  <span className="ns-balance-mobile-values">
                    <strong className="ns-number">
                      {formatAmount(asset.asset, asset.total)}
                    </strong>
                    <em className="ns-number">
                      可用 {formatAmount(asset.asset, asset.free)}
                    </em>
                  </span>
                </article>
              ))}
            </div>
          </div>
        )}

        <p className="ns-pf-balances-note">
          总资产估值 = USDT 总额 + BTC 总额 × 最新参考价。仅用于界面展示，不代表可提取资金。
          {balances?.note ? ` ${balances.note}` : ""}
        </p>
      </section>

      <PageFootnote
        center="Portfolio numbers are derived from the current account snapshot. Missing history stays missing."
      />
    </EditorialPage>
  );
}
