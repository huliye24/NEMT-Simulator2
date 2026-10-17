"use client";

import { useCallback, useEffect, useRef, useState, useSyncExternalStore } from "react";
import { ApiError, tradeApi } from "@/lib/trade/api";
import type {
  Balances,
  OrdersResponse,
  Session,
  SystemStatus,
  Ticker,
} from "@/lib/trade/types";

export interface TradingData {
  system: SystemStatus | null;
  ticker: Ticker | null;
  balances: Balances | null;
  orders: OrdersResponse | null;
  online: boolean;
  syncing: boolean;
  feedError: string | null;
  coreError: string | null;
  lastTickAt: number | null;
  refreshAll: () => Promise<void>;
  refreshOrders: () => Promise<void>;
}

const TICKER_INTERVAL_MS = 5_000;
const CORE_INTERVAL_MS = 15_000;

function subscribeOnline(callback: () => void): () => void {
  window.addEventListener("online", callback);
  window.addEventListener("offline", callback);
  return () => {
    window.removeEventListener("online", callback);
    window.removeEventListener("offline", callback);
  };
}

function getOnlineSnapshot(): boolean {
  return typeof navigator === "undefined" ? true : navigator.onLine;
}

function getServerOnlineSnapshot(): boolean {
  return true;
}

export function useTradingData(
  session: Session,
  onAuthLost: () => void
): TradingData {
  const [system, setSystem] = useState<SystemStatus | null>(null);
  const [ticker, setTicker] = useState<Ticker | null>(null);
  const [balances, setBalances] = useState<Balances | null>(null);
  const [orders, setOrders] = useState<OrdersResponse | null>(null);
  const online = useSyncExternalStore(
    subscribeOnline,
    getOnlineSnapshot,
    getServerOnlineSnapshot
  );
  const [syncing, setSyncing] = useState(false);
  const [feedError, setFeedError] = useState<string | null>(null);
  const [coreError, setCoreError] = useState<string | null>(null);
  const [lastTickAt, setLastTickAt] = useState<number | null>(null);
  const authLostRef = useRef(onAuthLost);

  useEffect(() => {
    authLostRef.current = onAuthLost;
  }, [onAuthLost]);

  const handleError = useCallback((error: unknown, scope: "feed" | "core") => {
    if (error instanceof ApiError && error.status === 401) {
      authLostRef.current();
      return;
    }
    const message =
      error instanceof Error ? error.message : "NEMT 服务端请求失败，请稍后重试";
    if (scope === "feed") setFeedError(message);
    else setCoreError(message);
  }, []);

  const refreshOrders = useCallback(async () => {
    try {
      const next = await tradeApi.listOrders(undefined, 100);
      setOrders(next);
    } catch (error) {
      handleError(error, "core");
    }
  }, [handleError]);

  const refreshAll = useCallback(async () => {
    setSyncing(true);
    const results = await Promise.allSettled([
      tradeApi.getTicker(),
      tradeApi.getSystemStatus(),
      tradeApi.getBalances(),
      tradeApi.listOrders(undefined, 100),
    ]);
    const [tickerResult, systemResult, balancesResult, ordersResult] = results;
    if (tickerResult.status === "fulfilled") {
      setTicker(tickerResult.value);
      setFeedError(null);
      setLastTickAt(Date.now());
    } else {
      handleError(tickerResult.reason, "feed");
    }
    if (systemResult.status === "fulfilled") setSystem(systemResult.value);
    else handleError(systemResult.reason, "core");
    if (balancesResult.status === "fulfilled") setBalances(balancesResult.value);
    else handleError(balancesResult.reason, "core");
    if (ordersResult.status === "fulfilled") setOrders(ordersResult.value);
    else handleError(ordersResult.reason, "core");
    if (results.every((item) => item.status === "fulfilled")) setCoreError(null);
    setSyncing(false);
  }, [handleError]);

  useEffect(() => {
    let cancelled = false;
    let tickerBusy = false;
    let coreBusy = false;

    async function pollTicker() {
      if (tickerBusy || document.hidden) return;
      tickerBusy = true;
      try {
        const next = await tradeApi.getTicker();
        if (cancelled) return;
        setTicker(next);
        setFeedError(null);
        setLastTickAt(Date.now());
      } catch (error) {
        if (cancelled) return;
        handleError(error, "feed");
      } finally {
        tickerBusy = false;
      }
    }

    async function pollCore() {
      if (coreBusy || document.hidden) return;
      coreBusy = true;
      try {
        const [nextSystem, nextBalances, nextOrders] = await Promise.all([
          tradeApi.getSystemStatus(),
          tradeApi.getBalances(),
          tradeApi.listOrders(undefined, 100),
        ]);
        if (cancelled) return;
        setSystem(nextSystem);
        setBalances(nextBalances);
        setOrders(nextOrders);
        setCoreError(null);
      } catch (error) {
        if (cancelled) return;
        handleError(error, "core");
      } finally {
        coreBusy = false;
      }
    }

    function onConnectivityRestored() {
      void pollTicker();
      void pollCore();
    }

    function onVisibility() {
      if (!document.hidden) {
        void pollTicker();
        void pollCore();
      }
    }

    void pollTicker();
    void pollCore();
    const tickerTimer = window.setInterval(pollTicker, TICKER_INTERVAL_MS);
    const coreTimer = window.setInterval(pollCore, CORE_INTERVAL_MS);
    window.addEventListener("online", onConnectivityRestored);
    document.addEventListener("visibilitychange", onVisibility);

    return () => {
      cancelled = true;
      window.clearInterval(tickerTimer);
      window.clearInterval(coreTimer);
      window.removeEventListener("online", onConnectivityRestored);
      document.removeEventListener("visibilitychange", onVisibility);
    };
  }, [session, handleError]);

  return {
    system,
    ticker,
    balances,
    orders,
    online,
    syncing,
    feedError,
    coreError,
    lastTickAt,
    refreshAll,
    refreshOrders,
  };
}
