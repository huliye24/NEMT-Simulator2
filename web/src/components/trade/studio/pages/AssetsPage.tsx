"use client";

import { ageLabel, fmtPrice, fmtQty, fmtUSDT } from "@/lib/trade/format";
import { findAsset, accountEquity } from "../account/AccountSummary";
import { EmptyState, PageHeader, Skeleton, StatusDot } from "../common";
import { StudioIcon } from "../icons";
import type { StudioPageProps } from "../types";

export default function AssetsPage({ data, navigate }: StudioPageProps) {
  const { balances, ticker } = data;
  const usdt = findAsset(data, "USDT");
  const btc = findAsset(data, "BTC");
  const lastPrice = Number(ticker?.last_price ?? 0);
  const equity = accountEquity(data);
  const assets = balances?.balances ?? [];
  const connected = Boolean(balances?.connected);

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
    <div className="ns-page">
      <PageHeader
        eyebrow="ACCOUNT / ASSETS"
        title="资产"
        description="现货账户资产与估值。所有余额来自 NEMT Cloud 账户快照，不在此界面缓存交易所密钥。"
        actions={
          <button
            type="button"
            className="ns-btn ns-btn-outline ns-btn-sm"
            onClick={() => void data.refreshAll()}
            disabled={data.syncing || !data.online}
          >
            <StudioIcon name="refresh" size={14} />
            {data.syncing ? "同步中…" : "刷新快照"}
          </button>
        }
      />

      <div className="ns-asset-summary-grid">
        <div className="ns-asset-summary ns-asset-summary-primary">
          <span className="ns-asset-summary-label">总资产估值</span>
          {balances ? (
            <strong className="ns-asset-summary-value">
              {fmtUSDT(equity)}
              <em>USDT</em>
            </strong>
          ) : (
            <Skeleton className="ns-skeleton-equity" />
          )}
          <span className="ns-asset-summary-note">
            现货账户 · 按最新 BTC 参考价折算
          </span>
        </div>
        <div className="ns-asset-summary">
          <span className="ns-asset-summary-label">
            <span className="ns-asset-token ns-asset-token-usdt">U</span>
            可用 USDT
          </span>
          <strong className="ns-asset-summary-value ns-number">
            {balances ? fmtUSDT(usdt.free) : "—"}
          </strong>
          <span className="ns-asset-summary-note">
            冻结 {balances ? fmtUSDT(usdt.locked) : "—"} USDT
          </span>
        </div>
        <div className="ns-asset-summary">
          <span className="ns-asset-summary-label">
            <span className="ns-asset-token ns-asset-token-btc">₿</span>
            可用 BTC
          </span>
          <strong className="ns-asset-summary-value ns-number">
            {balances ? fmtQty(btc.free) : "—"}
          </strong>
          <span className="ns-asset-summary-note">
            ≈ {fmtUSDT(btc.free * lastPrice)} USDT
          </span>
        </div>
      </div>

      <div className="ns-assets-layout">
        <section className="ns-card ns-balances-card" aria-label="资产余额明细">
          <div className="ns-balances-head">
            <div>
              <h2 className="ns-card-title">资产余额</h2>
              <p className="ns-card-hint">
                {balances?.source === "demo"
                  ? "DEMO 模拟账本"
                  : balances?.source === "binance"
                    ? "Binance 只读账户"
                    : "等待账户连接"}
              </p>
            </div>
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
          </div>

          {!balances ? (
            !data.coreError ? (
              <div className="ns-balances-skeleton">
                <Skeleton className="ns-skeleton-row" />
                <Skeleton className="ns-skeleton-row" />
              </div>
            ) : (
              <EmptyState
                icon="warning"
                title="账户快照暂不可用"
                body={data.coreError}
                action={
                  <button type="button" className="ns-btn ns-btn-outline ns-btn-sm" onClick={() => void data.refreshAll()}>
                    重新获取
                  </button>
                }
              />
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
                          <span className={`ns-asset-token ns-asset-token-${asset.asset.toLowerCase()}`}>
                            {asset.asset === "BTC" ? "₿" : asset.asset.slice(0, 1)}
                          </span>
                          <span>
                            <strong>{asset.asset}</strong>
                            <em>{asset.asset === "USDT" ? "Tether" : asset.asset === "BTC" ? "Bitcoin" : "Asset"}</em>
                          </span>
                        </span>
                      </td>
                      <td className="is-numeric ns-number">{formatAmount(asset.asset, asset.free)}</td>
                      <td className="is-numeric ns-number ns-muted-cell">{formatAmount(asset.asset, asset.locked)}</td>
                      <td className="is-numeric ns-number">{formatAmount(asset.asset, asset.total)}</td>
                      <td className="is-numeric ns-number ns-muted-cell">
                        {valuation(asset.asset, asset.total)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              <div className="ns-balance-mobile-list">
                {assets.map((asset) => (
                  <article className="ns-balance-mobile-row" key={`${asset.asset}-mobile`}>
                    <span className="ns-asset-name">
                      <span className={`ns-asset-token ns-asset-token-${asset.asset.toLowerCase()}`}>
                        {asset.asset === "BTC" ? "₿" : asset.asset.slice(0, 1)}
                      </span>
                      <span>
                        <strong>{asset.asset}</strong>
                        <em>{valuation(asset.asset, asset.total)}</em>
                      </span>
                    </span>
                    <span className="ns-balance-mobile-values">
                      <strong className="ns-number">{formatAmount(asset.asset, asset.total)}</strong>
                      <em className="ns-number">可用 {formatAmount(asset.asset, asset.free)}</em>
                    </span>
                  </article>
                ))}
              </div>
            </div>
          )}

          {balances ? (
            <div className="ns-balances-foot">
              <span>快照 {ageLabel(balances.fetched_at)}更新</span>
              <span>{balances.note ?? "账户快照仅用于只读展示与风控校验。"}</span>
            </div>
          ) : null}
        </section>

        <aside className="ns-asset-side">
          <section className="ns-card">
            <div className="ns-side-card-head">
              <h2 className="ns-card-title">账户状态</h2>
              <StudioIcon name="shield" size={16} />
            </div>
            <dl className="ns-detail-list">
              <div>
                <dt>交易环境</dt>
                <dd>{balances?.mode ?? data.system?.mode ?? "—"}</dd>
              </div>
              <div>
                <dt>账本来源</dt>
                <dd>{balances?.source === "demo" ? "DEMO 模拟账本" : balances?.source ?? "—"}</dd>
              </div>
              <div>
                <dt>账户连接</dt>
                <dd>{balances?.connected ? "只读已连接" : balances?.account_status ?? "—"}</dd>
              </div>
              <div>
                <dt>BTC 参考价</dt>
                <dd className="ns-number">{fmtPrice(ticker?.last_price)} USDT</dd>
              </div>
              <div>
                <dt>数据新鲜度</dt>
                <dd>{balances?.stale ? "延迟" : "正常"}</dd>
              </div>
            </dl>
          </section>

          <section className="ns-card ns-asset-note-card">
            <span className="ns-note-icon">
              <StudioIcon name="info" size={17} />
            </span>
            <div>
              <h2 className="ns-card-title">估值口径</h2>
              <p>
                当前账户为现货账户，不计算合约未实现盈亏。总资产估值 =
                USDT 总额 + BTC 总额 × 最新参考价，仅用于界面展示，不代表可提取资金。
              </p>
            </div>
          </section>

          <button type="button" className="ns-btn ns-btn-outline ns-btn-block" onClick={() => navigate("execution")}>
            查看订单与成交
            <StudioIcon name="arrowUpRight" size={14} />
          </button>
        </aside>
      </div>
    </div>
  );
}
