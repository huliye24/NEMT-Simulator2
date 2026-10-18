"use client";

import { FormEvent, useCallback, useEffect, useMemo, useState } from "react";
import { ApiError, riskReasonsFromError, tradeApi } from "@/lib/trade/api";
import {
  ageLabel,
  cn,
  fmtPrice,
  fmtQty,
  fmtUSDT,
  roundDown,
} from "@/lib/trade/format";
import { ORDER_STATUS_LABEL } from "@/lib/trade/order-status";
import type {
  Order,
  OrderKind,
  OrderPreview,
  OrderSide,
  Session,
} from "@/lib/trade/types";
import type { WorkspaceData } from "./workspace-shared";
import type { ToastKind } from "./workspace-shared";
import {
  Icon,
  ModeBadge,
  SectionHeader,
  SourceBadge,
  Spinner,
  StatusDot,
} from "./ui";

const FEE_RATE = 0.001;
const BTC_STEP_DECIMALS = 5;

interface TradeTabProps {
  session: Session;
  data: WorkspaceData;
  notify: (kind: ToastKind, message: string) => void;
  onOrdersChanged: () => Promise<void>;
}

interface PreviewErrorState {
  message: string;
  reasons: string[];
}

function newIdempotencyKey(): string {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
    return crypto.randomUUID();
  }
  return `idem-${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;
}

function sanitizeDecimal(value: string): string {
  const cleaned = value.replace(/[^0-9.]/g, "");
  const [whole, ...rest] = cleaned.split(".");
  return rest.length > 0 ? `${whole}.${rest.join("")}` : whole;
}

function balanceFor(data: WorkspaceData, asset: string): { free: number; locked: number } {
  const item = data.balances?.balances.find((entry) => entry.asset === asset);
  return { free: Number(item?.free ?? 0), locked: Number(item?.locked ?? 0) };
}

function apiQuantity(value: number): string {
  const rounded = roundDown(value, BTC_STEP_DECIMALS);
  return rounded.toFixed(BTC_STEP_DECIMALS);
}

export default function TradeTab({
  session,
  data,
  notify,
  onOrdersChanged,
}: TradeTabProps) {
  const { system, ticker, balances, orders, online, feedError } = data;
  const [side, setSide] = useState<OrderSide>("BUY");
  const [kind, setKind] = useState<OrderKind>("MARKET");
  const [amountMode, setAmountMode] = useState<"quote" | "base">("quote");
  const [amountInput, setAmountInput] = useState("");
  const [priceInput, setPriceInput] = useState("");
  const [previewing, setPreviewing] = useState(false);
  const [preview, setPreview] = useState<OrderPreview | null>(null);
  const [previewError, setPreviewError] = useState<PreviewErrorState | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [confirmChecked, setConfirmChecked] = useState(false);
  const [idempotencyKey, setIdempotencyKey] = useState<string | null>(null);
  const [lastResult, setLastResult] = useState<Order | null>(null);

  const usdt = balanceFor(data, "USDT");
  const btc = balanceFor(data, "BTC");
  const lastPrice = Number(ticker?.last_price ?? 0);
  const limitPrice = Number(priceInput);
  const referencePrice = kind === "LIMIT" ? limitPrice : lastPrice;
  const amount = Number(amountInput);
  const quantity =
    amountMode === "quote"
      ? referencePrice > 0
        ? amount / referencePrice
        : 0
      : amount;
  const normalizedQuantity = roundDown(quantity, BTC_STEP_DECIMALS);
  const estimatedNotional = normalizedQuantity * referencePrice;
  const estimatedFee = estimatedNotional * FEE_RATE;
  const paused = Boolean(system?.risk.pause_new_orders);
  const tradingEnabled = Boolean(system?.flags.trading_enabled);
  const accountStale = Boolean(balances?.stale);
  const marketStale = Boolean(ticker?.stale) || !online;

  useEffect(() => {
    if (!preview) return;
    const previous = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = previous;
    };
  }, [preview]);

  const disabledReason = useMemo(() => {
    if (!online) return "网络已断开，禁止提交交易写请求";
    if (!system) return "正在同步服务端状态…";
    if (!ticker || lastPrice <= 0) return "等待行情数据…";
    if (ticker.stale) return "行情已过期，等待恢复后再试";
    if (paused) return "管理员已暂停新订单";
    if (!tradingEnabled)
      return system.mode === "LIVE"
        ? "V0.1 不开放 LIVE 下单"
        : "当前环境未启用交易";
    if (accountStale) return "账户快照已过期，等待刷新";
    if (balances?.account_status === "NOT_CONFIGURED")
      return "账户未配置，无法下单";
    if (kind === "LIMIT" && (!Number.isFinite(limitPrice) || limitPrice <= 0))
      return "请输入有效的限价";
    if (!Number.isFinite(amount) || amount <= 0) return "请输入金额或数量";
    if (normalizedQuantity <= 0) return "数量低于 BTC 最小精度";
    if (estimatedNotional < Number(system.limits.min_order_notional))
      return `名义金额低于最小要求 ${system.limits.min_order_notional} USDT`;
    if (estimatedNotional > Number(system.limits.max_order_notional))
      return `名义金额超过单笔上限 ${system.limits.max_order_notional} USDT`;
    if (side === "BUY" && estimatedNotional + estimatedFee > usdt.free)
      return "USDT 可用余额不足（含估算手续费）";
    if (side === "SELL" && normalizedQuantity > btc.free)
      return "BTC 可用余额不足";
    return null;
  }, [
    online,
    system,
    ticker,
    lastPrice,
    paused,
    tradingEnabled,
    accountStale,
    balances?.account_status,
    kind,
    limitPrice,
    amount,
    normalizedQuantity,
    estimatedNotional,
    side,
    estimatedFee,
    usdt.free,
    btc.free,
  ]);

  const applyPercent = useCallback(
    (percent: number) => {
      const ratio = percent / 100;
      const price = referencePrice > 0 ? referencePrice : lastPrice;
      if (!price) return;
      if (amountMode === "quote") {
        if (side === "BUY") {
          const maxQuote = usdt.free / (1 + FEE_RATE);
          setAmountInput((maxQuote * ratio).toFixed(2));
        } else {
          setAmountInput((btc.free * price * ratio).toFixed(2));
        }
      } else if (side === "BUY") {
        const maxBase = usdt.free / (price * (1 + FEE_RATE));
        setAmountInput(
          roundDown(maxBase * ratio, BTC_STEP_DECIMALS).toFixed(BTC_STEP_DECIMALS)
        );
      } else {
        setAmountInput(
          roundDown(btc.free * ratio, BTC_STEP_DECIMALS).toFixed(BTC_STEP_DECIMALS)
        );
      }
    },
    [amountMode, referencePrice, lastPrice, side, usdt.free, btc.free]
  );

  async function handlePreview(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (disabledReason || previewing) return;
    setPreviewing(true);
    setPreviewError(null);
    setSubmitError(null);
    setLastResult(null);
    try {
      const next = await tradeApi.previewOrder(session.csrf_token, {
        symbol: "BTCUSDT",
        side,
        type: kind,
        quantity: apiQuantity(normalizedQuantity),
        price: kind === "LIMIT" ? String(limitPrice) : undefined,
        time_in_force: "GTC",
      });
      setPreview(next);
      setIdempotencyKey(newIdempotencyKey());
      setConfirmChecked(false);
    } catch (error) {
      setPreviewError({
        message:
          error instanceof ApiError ? error.message : "订单预览失败，请稍后重试",
        reasons: riskReasonsFromError(error),
      });
    } finally {
      setPreviewing(false);
    }
  }

  async function handleConfirm() {
    if (!preview || !idempotencyKey || submitting) return;
    setSubmitting(true);
    setSubmitError(null);
    try {
      const result = await tradeApi.createOrder(
        session.csrf_token,
        preview.preview_token,
        idempotencyKey
      );
      const order = result.order;
      setPreview(null);
      setConfirmChecked(false);
      setAmountInput("");
      setIdempotencyKey(null);
      setPreviewError(null);
      setLastResult(order);
      notify(
        order.status === "FILLED" ? "success" : "info",
        result.replayed
          ? "重复请求已安全去重，未产生新订单"
          : order.status === "FILLED"
            ? `${side === "BUY" ? "买入" : "卖出"} ${fmtQty(order.filled_qty)} BTC 已成交`
            : `订单已提交 · ${ORDER_STATUS_LABEL[order.status]}`
      );
      await onOrdersChanged();
    } catch (error) {
      const apiError = error instanceof ApiError ? error : null;
      const reasons = riskReasonsFromError(error);
      if (reasons.length > 0) {
        setPreviewError({
          message: apiError?.message ?? "订单未通过服务端风控",
          reasons,
        });
        setPreview(null);
        setConfirmChecked(false);
        setIdempotencyKey(null);
      } else {
        const message =
          apiError?.message ?? "提交结果未知，请刷新订单状态后确认";
        setSubmitError(message);
        if (apiError?.code === "network_error") {
          notify(
            "warning",
            "网络中断，订单结果未知。请勿反复提交；恢复后刷新订单状态。"
          );
          await onOrdersChanged();
        }
      }
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="space-y-4">
      <div>
        <div className="flex items-center gap-2">
          <h1 className="text-[17px] font-semibold text-slate-100">下单</h1>
          <span className={ticker?.source === "demo" ? "trade-chip trade-chip-amber" : "trade-chip trade-chip-cyan"}>
            <span className="trade-dot" />
            {ticker?.source === "demo" ? "SIM" : "BINANCE"}
          </span>
        </div>
        <p className="text-[10px] text-slate-500 mt-0.5">
          BTC/USDT · Spot · 预览后二次确认 · 服务端风控
        </p>
      </div>

      <div className="trade-card-flat px-3.5 py-2.5 flex items-center justify-between gap-3">
        <div className="flex items-center gap-2 min-w-0">
          <span className="w-7 h-7 rounded-lg bg-emerald-400/10 text-emerald-300 flex items-center justify-center text-[10px] font-bold flex-none">
            U
          </span>
          <div className="min-w-0">
            <p className="text-[9px] text-slate-600">可用 USDT</p>
            <p className="trade-number text-[12px] text-slate-200 truncate">
              {fmtUSDT(usdt.free)}
            </p>
          </div>
        </div>
        <div className="w-px h-7 bg-white/[0.07]" />
        <div className="flex items-center gap-2 min-w-0">
          <span className="w-7 h-7 rounded-lg bg-amber-400/10 text-amber-300 flex items-center justify-center text-[10px] font-bold flex-none">
            B
          </span>
          <div className="min-w-0">
            <p className="text-[9px] text-slate-600">可用 BTC</p>
            <p className="trade-number text-[12px] text-slate-200 truncate">
              {fmtQty(btc.free)}
            </p>
          </div>
        </div>
        <button
          type="button"
          onClick={() => {
            setAmountInput("");
            setPreviewError(null);
          }}
          className="text-[10px] text-slate-600 hover:text-slate-300 flex-none"
        >
          清空
        </button>
      </div>

      {paused || !tradingEnabled || marketStale || accountStale ? (
        <div className="rounded-xl border border-amber-300/20 bg-amber-300/[0.06] px-3.5 py-2.5">
          <div className="flex items-center gap-2 text-[11px] font-semibold text-amber-200">
            <Icon name="lock" size={13} />
            {paused
              ? "暂停新订单"
              : !tradingEnabled
                ? session.mode === "LIVE"
                  ? "LIVE 写入未开放"
                  : "交易未启用"
                : marketStale
                  ? "行情不可用"
                  : "账户快照过期"}
          </div>
          <p className="text-[10px] text-amber-100/45 mt-1">
            {paused
              ? system?.risk.pause_reason ?? "管理员已暂停新订单"
              : feedError ??
                "系统处于 fail-closed 状态，确认按钮与提交接口都会拒绝交易。"}
          </p>
        </div>
      ) : null}

      <form onSubmit={handlePreview} className="trade-card p-4 space-y-4">
        <div className="trade-seg">
          <button
            type="button"
            className={cn(
              "trade-seg-btn",
              side === "BUY" ? "trade-seg-btn-buy" : "hover:text-slate-300"
            )}
            onClick={() => {
              setSide("BUY");
              setPreviewError(null);
              setLastResult(null);
            }}
          >
            买入
          </button>
          <button
            type="button"
            className={cn(
              "trade-seg-btn",
              side === "SELL" ? "trade-seg-btn-sell" : "hover:text-slate-300"
            )}
            onClick={() => {
              setSide("SELL");
              setPreviewError(null);
              setLastResult(null);
            }}
          >
            卖出
          </button>
        </div>

        <div className="trade-seg">
          <button
            type="button"
            className={cn("trade-seg-btn", kind === "MARKET" && "trade-seg-btn-active")}
            onClick={() => setKind("MARKET")}
          >
            市价
          </button>
          <button
            type="button"
            className={cn("trade-seg-btn", kind === "LIMIT" && "trade-seg-btn-active")}
            onClick={() => {
              setKind("LIMIT");
              if (!priceInput && lastPrice > 0) setPriceInput(lastPrice.toFixed(2));
            }}
          >
            限价
          </button>
        </div>

        {kind === "LIMIT" ? (
          <label className="block">
            <div className="flex items-center justify-between mb-1.5">
              <span className="text-[11px] font-medium text-slate-400">限价</span>
              <button
                type="button"
                onClick={() => setPriceInput(lastPrice ? lastPrice.toFixed(2) : "")}
                className="text-[10px] font-semibold text-cyan-300/80"
              >
                使用最新价 {fmtPrice(lastPrice)}
              </button>
            </div>
            <div className="relative">
              <input
                className="trade-input trade-number !pr-14"
                inputMode="decimal"
                placeholder="0.00"
                value={priceInput}
                onChange={(event) => setPriceInput(sanitizeDecimal(event.target.value))}
              />
              <span className="absolute right-3.5 top-1/2 -translate-y-1/2 text-[11px] text-slate-600">
                USDT
              </span>
            </div>
          </label>
        ) : (
          <div className="flex items-center justify-between rounded-xl border border-white/[0.06] bg-black/20 px-3 py-2.5">
            <span className="text-[11px] text-slate-500">市价参考</span>
            <span className="trade-number text-[12px] text-slate-300">
              ≈ {fmtPrice(lastPrice)} USDT
            </span>
          </div>
        )}

        <div>
          <div className="flex items-center justify-between mb-1.5">
            <span className="text-[11px] font-medium text-slate-400">
              {amountMode === "quote" ? "金额" : "数量"}
            </span>
            <div className="flex rounded-lg border border-white/[0.07] bg-black/30 p-0.5">
              <button
                type="button"
                onClick={() => {
                  setAmountMode("quote");
                  setAmountInput("");
                }}
                className={cn(
                  "px-2 py-1 rounded-md text-[10px] font-semibold",
                  amountMode === "quote" ? "bg-white/[0.08] text-slate-200" : "text-slate-600"
                )}
              >
                USDT
              </button>
              <button
                type="button"
                onClick={() => {
                  setAmountMode("base");
                  setAmountInput("");
                }}
                className={cn(
                  "px-2 py-1 rounded-md text-[10px] font-semibold",
                  amountMode === "base" ? "bg-white/[0.08] text-slate-200" : "text-slate-600"
                )}
              >
                BTC
              </button>
            </div>
          </div>
          <div className="relative">
            <input
              className="trade-input trade-number !text-[22px] !font-semibold !pr-16"
              inputMode="decimal"
              placeholder={amountMode === "quote" ? "0.00" : "0.00000"}
              value={amountInput}
              onChange={(event) => {
                setAmountInput(sanitizeDecimal(event.target.value));
                setPreviewError(null);
                setLastResult(null);
              }}
              aria-label={amountMode === "quote" ? "金额（USDT）" : "数量（BTC）"}
            />
            <span className="absolute right-3.5 top-1/2 -translate-y-1/2 text-[11px] font-semibold text-slate-600">
              {amountMode === "quote" ? "USDT" : "BTC"}
            </span>
          </div>
          <div className="mt-2 grid grid-cols-4 gap-1.5">
            {[25, 50, 75, 100].map((percent) => (
              <button
                key={percent}
                type="button"
                onClick={() => applyPercent(percent)}
                className="trade-quick-btn"
              >
                {percent === 100 ? "最大" : `${percent}%`}
              </button>
            ))}
          </div>
          <div className="mt-2 flex items-center justify-between text-[10px] text-slate-600">
            <span>
              ≈ {fmtQty(normalizedQuantity)} BTC · {fmtUSDT(estimatedNotional)} USDT
            </span>
            <span>估算手续费 {fmtUSDT(estimatedFee)} USDT</span>
          </div>
        </div>

        <div className="rounded-xl border border-white/[0.06] bg-black/20 px-3.5 py-3 space-y-1.5">
          <div className="flex items-center justify-between text-[10px]">
            <span className="text-slate-600">参考价格</span>
            <span className="trade-number text-slate-400">{fmtPrice(referencePrice)} USDT</span>
          </div>
          <div className="flex items-center justify-between text-[10px]">
            <span className="text-slate-600">订单名义金额</span>
            <span className="trade-number text-slate-300">{fmtUSDT(estimatedNotional)} USDT</span>
          </div>
          <div className="flex items-center justify-between text-[10px]">
            <span className="text-slate-600">数量精度</span>
            <span className="trade-number text-slate-500">向下取整至 0.00001 BTC</span>
          </div>
        </div>

        {previewError ? (
          <div className="rounded-xl border border-rose-400/25 bg-rose-400/[0.06] px-3.5 py-3">
            <div className="flex items-center gap-2 text-[11px] font-semibold text-rose-200">
              <Icon name="warning" size={13} />
              {previewError.message}
            </div>
            {previewError.reasons.length > 0 ? (
              <ul className="mt-2 space-y-1 pl-4 list-disc text-[10px] leading-relaxed text-rose-200/65">
                {previewError.reasons.slice(0, 6).map((reason) => (
                  <li key={reason}>{reason}</li>
                ))}
              </ul>
            ) : null}
          </div>
        ) : null}

        {lastResult ? (
          <button
            type="button"
            onClick={() => setLastResult(null)}
            className="w-full rounded-xl border border-emerald-400/20 bg-emerald-400/[0.06] px-3.5 py-2.5 text-left"
          >
            <div className="flex items-center gap-2 text-[11px] font-semibold text-emerald-200">
              <Icon name="check" size={13} />
              上一笔：{ORDER_STATUS_LABEL[lastResult.status]}
              <span className="text-[9px] font-normal text-emerald-200/45 ml-auto">
                点击关闭
              </span>
            </div>
            <p className="trade-number text-[10px] text-emerald-100/45 mt-1">
              {lastResult.side === "BUY" ? "买入" : "卖出"} {fmtQty(lastResult.filled_qty)} BTC
              @ {lastResult.avg_fill_price ? fmtPrice(lastResult.avg_fill_price) : "限价挂单"} ·{" "}
              {lastResult.client_order_id}
            </p>
          </button>
        ) : null}

        <button
          type="submit"
          className={cn(
            "trade-btn w-full",
            side === "BUY" ? "trade-btn-buy" : "trade-btn-sell"
          )}
          disabled={Boolean(disabledReason) || previewing}
        >
          {previewing ? <Spinner size={16} /> : <Icon name="shield" size={16} />}
          {previewing ? "服务端预览中…" : "预览订单"}
        </button>
        {disabledReason ? (
          <p className="text-center text-[10px] text-amber-200/55">{disabledReason}</p>
        ) : (
          <p className="flex items-center justify-center gap-1.5 text-center text-[10px] text-slate-600">
            <Icon name="lock" size={10} />
            预览通过后仍需二次确认；服务端会重新校验风控与行情
          </p>
        )}
      </form>

      <section className="hidden">
        <SectionHeader
          title="风控与保护"
          hint="所有限制由服务端强制执行，前端无法覆盖"
        />
        <div className="trade-card-flat divide-y divide-white/[0.05]">
          <ProtectionRow
            icon="shield"
            title="服务端风控"
            body={`单笔 ≤ ${system?.limits.max_order_notional ?? "—"} USDT · 当日 ≤ ${system?.limits.max_daily_notional ?? "—"} USDT`}
            ok={Boolean(system)}
          />
          <ProtectionRow
            icon="lock"
            title="幂等下单"
            body="每次确认生成唯一 clientOrderId；网络中断不会盲目重复 POST"
            ok
          />
          <ProtectionRow
            icon="check"
            title="一次性确认"
            body="预览签发短期确认令牌，提交后立即作废"
            ok
          />
          <ProtectionRow
            icon="pause"
            title="紧急暂停"
            body={
              paused
                ? `已暂停：${system?.risk.pause_reason ?? "管理员操作"}`
                : "管理员可从设置页暂停全部新订单（不会平仓）"
            }
            ok={!paused}
          />
        </div>
      </section>

      {orders && orders.open_count > 0 ? (
        <p className="text-center text-[10px] text-slate-600">
          当前有 {orders.open_count} 笔未完成订单占用额度 ·{" "}
          {balances ? `账户更新 ${ageLabel(balances.fetched_at)}` : ""}
        </p>
      ) : null}

      {preview ? (
        <ConfirmSheet
          preview={preview}
          submitting={submitting}
          submitError={submitError}
          checked={confirmChecked}
          setChecked={setConfirmChecked}
          onClose={() => {
            if (!submitting) setPreview(null);
          }}
          onConfirm={() => void handleConfirm()}
        />
      ) : null}
    </div>
  );
}

function ProtectionRow({
  icon,
  title,
  body,
  ok,
}: {
  icon: "shield" | "lock" | "check" | "pause";
  title: string;
  body: string;
  ok: boolean;
}) {
  return (
    <div className="flex items-start gap-3 px-3.5 py-3">
      <div
        className={cn(
          "w-8 h-8 rounded-lg flex items-center justify-center flex-none border",
          ok
            ? "border-cyan-300/15 bg-cyan-400/[0.07] text-cyan-300"
            : "border-amber-300/20 bg-amber-400/[0.08] text-amber-300"
        )}
      >
        <Icon name={icon} size={14} />
      </div>
      <div className="min-w-0">
        <p className="text-[11px] font-semibold text-slate-300">{title}</p>
        <p className="text-[10px] leading-relaxed text-slate-500 mt-0.5">{body}</p>
      </div>
    </div>
  );
}

function ConfirmSheet({
  preview,
  submitting,
  submitError,
  checked,
  setChecked,
  onClose,
  onConfirm,
}: {
  preview: OrderPreview;
  submitting: boolean;
  submitError: string | null;
  checked: boolean;
  setChecked: (value: boolean) => void;
  onClose: () => void;
  onConfirm: () => void;
}) {
  const draft = preview.draft;
  const risk = preview.risk;
  const buy = draft.side === "BUY";
  const failedChecks = risk.checks.filter((check) => !check.passed);

  useEffect(() => {
    function onKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape" && !submitting) onClose();
    }
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [onClose, submitting]);

  return (
    <div
      className="trade-sheet-overlay"
      role="dialog"
      aria-modal="true"
      aria-label="订单确认"
      onClick={(event) => {
        if (event.target === event.currentTarget && !submitting) onClose();
      }}
    >
      <div className="trade-sheet">
        <div className="trade-sheet-handle" />
        <div className="flex items-start justify-between gap-3">
          <div>
            <div className="flex items-center gap-2">
              <span
                className={cn(
                  "trade-chip",
                  buy ? "trade-chip-cyan text-emerald-300 border-emerald-400/25 bg-emerald-400/10" : "trade-chip-danger"
                )}
              >
                {buy ? "BUY 买入" : "SELL 卖出"}
              </span>
              <span className="trade-chip">{draft.type}</span>
              <ModeBadge mode={preview.mode} />
            </div>
            <h2 className="text-[19px] font-semibold text-slate-100 mt-2.5">
              确认 {draft.symbol} {draft.type === "MARKET" ? "市价" : "限价"}
              {buy ? "买入" : "卖出"}
            </h2>
            <p className="text-[10px] text-slate-500 mt-1">
              服务端风控已通过 · 确认后不可修改
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            disabled={submitting}
            className="w-8 h-8 rounded-full border border-white/[0.08] flex items-center justify-center text-slate-500 disabled:opacity-40"
            aria-label="关闭"
          >
            <Icon name="close" size={14} />
          </button>
        </div>

        <div className="mt-5 rounded-2xl border border-white/[0.07] bg-black/25 p-4 space-y-2.5">
          <ConfirmRow label="数量" value={`${fmtQty(draft.quantity)} BTC`} strong />
          <ConfirmRow
            label={draft.type === "MARKET" ? "参考价格" : "限价"}
            value={`${fmtPrice(
              draft.type === "MARKET" ? draft.latest_price : draft.price
            )} USDT`}
          />
          <ConfirmRow
            label="预计名义金额"
            value={`${fmtUSDT(draft.estimated_notional)} USDT`}
            strong
          />
          <ConfirmRow
            label={`估算手续费（${draft.fee_asset}）`}
            value={`${fmtUSDT(draft.estimated_fee)} USDT`}
          />
          {draft.type === "MARKET" ? (
            <p className="text-[10px] leading-relaxed text-amber-200/55 pt-1 border-t border-white/[0.05]">
              市价单的最终成交价可能与预览参考价不同；实际成交以订单回报为准。
            </p>
          ) : null}
        </div>

        <div className="mt-3 grid grid-cols-2 gap-2">
          <div className="rounded-xl border border-white/[0.06] bg-black/20 px-3 py-2">
            <p className="text-[9px] text-slate-600">行情来源</p>
            <div className="mt-1">
              <SourceBadge source={preview.market_source} stale={false} />
            </div>
          </div>
          <div className="rounded-xl border border-white/[0.06] bg-black/20 px-3 py-2">
            <p className="text-[9px] text-slate-600">账户快照</p>
            <p className="trade-number text-[10px] text-slate-400 mt-1.5">
              {ageLabel(preview.account_fetched_at)}
              {preview.account_stale ? " · 已过期" : ""}
            </p>
          </div>
        </div>

        {preview.warnings.length > 0 ? (
          <div className="mt-3 rounded-xl border border-amber-300/20 bg-amber-300/[0.06] px-3.5 py-3">
            <div className="flex items-center gap-2 text-[10px] font-semibold text-amber-200">
              <Icon name="warning" size={12} />
              注意事项
            </div>
            <ul className="mt-1.5 space-y-1 pl-4 list-disc text-[10px] leading-relaxed text-amber-100/55">
              {preview.warnings.map((warning) => (
                <li key={warning}>{warning}</li>
              ))}
            </ul>
          </div>
        ) : null}

        <details className="mt-3 rounded-xl border border-white/[0.06] bg-black/15">
          <summary className="cursor-pointer list-none px-3.5 py-2.5 text-[10px] font-medium text-slate-400 flex items-center justify-between">
            <span className="flex items-center gap-1.5">
              <StatusDot tone={risk.approved ? "ok" : "bad"} />
              风控检查 {risk.checks.length} 项
              {failedChecks.length > 0 ? ` · ${failedChecks.length} 项未通过` : "全部通过"}
            </span>
            <Icon name="chevronRight" size={12} className="text-slate-600" />
          </summary>
          <div className="px-3.5 pb-3 space-y-1.5">
            {risk.checks.map((check) => (
              <div key={check.code} className="flex items-start gap-2">
                <span
                  className={cn(
                    "mt-[3px] w-1.5 h-1.5 rounded-full flex-none",
                    check.passed ? "bg-emerald-400/70" : "bg-rose-400"
                  )}
                />
                <div>
                  <p className="trade-number text-[9px] text-slate-500 uppercase">
                    {check.code}
                  </p>
                  <p className="text-[10px] leading-relaxed text-slate-500/80">
                    {check.message}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </details>

        {submitError ? (
          <div className="mt-3 rounded-xl border border-rose-400/25 bg-rose-400/[0.06] px-3.5 py-2.5 text-[11px] leading-relaxed text-rose-200">
            {submitError}
            <p className="text-[10px] text-rose-200/45 mt-1">
              若网络中断，请先关闭并在订单页核对状态；重复确认使用同一幂等键，不会重复下单。
            </p>
          </div>
        ) : null}

        <label className="mt-4 flex items-start gap-3 rounded-xl border border-white/[0.07] bg-white/[0.02] px-3.5 py-3 cursor-pointer">
          <input
            type="checkbox"
            checked={checked}
            onChange={(event) => setChecked(event.target.checked)}
            disabled={submitting}
            className="mt-0.5 h-4 w-4 accent-cyan-400"
          />
          <span className="text-[11px] leading-relaxed text-slate-400">
            我已核对订单信息，理解
            {preview.mode === "DEMO"
              ? "这是 DEMO 模拟订单，不涉及真实资金。"
              : "这是 TESTNET 订单，使用测试网资金；成交价与结果以交易所回报为准。"}
            提交后服务端将再次校验风控、余额与行情。
          </span>
        </label>

        <button
          type="button"
          onClick={onConfirm}
          disabled={!checked || submitting || !risk.approved}
          className={cn(
            "trade-btn w-full mt-3",
            buy ? "trade-btn-buy" : "trade-btn-sell"
          )}
        >
          {submitting ? <Spinner size={16} /> : <Icon name="shield" size={16} />}
          {submitting
            ? "提交中，请勿关闭…"
            : `确认提交${buy ? "买入" : "卖出"} · ${fmtUSDT(draft.estimated_notional)} USDT`}
        </button>
        <p className="text-center text-[9px] text-slate-600 mt-2">
          确认令牌 {preview.expires_at.slice(11, 19)} UTC 前有效 · 仅可使用一次
        </p>
      </div>
    </div>
  );
}

function ConfirmRow({
  label,
  value,
  strong,
}: {
  label: string;
  value: string;
  strong?: boolean;
}) {
  return (
    <div className="flex items-center justify-between gap-4">
      <span className="text-[11px] text-slate-500">{label}</span>
      <span
        className={cn(
          "trade-number text-right",
          strong ? "text-[14px] font-semibold text-slate-100" : "text-[12px] text-slate-300"
        )}
      >
        {value}
      </span>
    </div>
  );
}
