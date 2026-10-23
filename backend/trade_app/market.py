"""Public Binance market data with an explicit DEMO fallback.

Important parsing rules (issue #8):
- 24h ticker: ``c`` is the latest price and ``p`` is the 24h price change.
- Kline events carry OHLCV as strings inside the nested ``k`` object.
- REST klines are arrays, not event objects.
- Every response exposes its source and freshness so the UI never pretends
  that simulated data is a live exchange feed.
"""

from __future__ import annotations

import asyncio
import dataclasses
import math
import os
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Any

import httpx

from .config import AppMode, Settings

ALLOWED_INTERVALS = {"1m", "5m", "15m", "1h", "4h", "1d"}
KLINE_INTERVAL_MS = {
    "1m": 60_000,
    "5m": 300_000,
    "15m": 900_000,
    "1h": 3_600_000,
    "4h": 14_400_000,
    "1d": 86_400_000,
}


class MarketUnavailable(RuntimeError):
    """Raised when no safe price can be produced for an order path."""


@dataclass(frozen=True)
class Ticker:
    symbol: str
    last_price: Decimal
    price_change: Decimal
    price_change_percent: Decimal
    high_price: Decimal
    low_price: Decimal
    volume: Decimal
    quote_volume: Decimal
    event_time: str | None
    fetched_at: str
    source: str
    stale: bool


@dataclass(frozen=True)
class Kline:
    open_time: int
    open_time_iso: str
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal
    close_time: int
    is_closed: bool


@dataclass(frozen=True)
class KlineSeries:
    symbol: str
    interval: str
    items: tuple[Kline, ...]
    fetched_at: str
    source: str
    stale: bool


@dataclass(frozen=True)
class SymbolRules:
    symbol: str
    base_asset: str
    quote_asset: str
    tick_size: Decimal
    step_size: Decimal
    min_qty: Decimal
    max_qty: Decimal
    min_notional: Decimal
    source: str


def _iso_from_ms(value: Any) -> str | None:
    try:
        return datetime.fromtimestamp(int(value) / 1000, tz=timezone.utc).isoformat(
            timespec="seconds"
        )
    except (TypeError, ValueError, OSError):
        return None


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _dec(value: Any) -> Decimal:
    return Decimal(str(value))


def parse_ticker(
    payload: dict[str, Any],
    symbol: str,
    *,
    fetched_at: str | None = None,
    stale: bool = False,
    source: str = "binance",
) -> Ticker:
    """Parse Binance's raw 24h ticker without swapping ``c`` and ``p``."""

    return Ticker(
        symbol=str(payload.get("symbol") or symbol).upper(),
        last_price=_dec(payload["lastPrice"] if "lastPrice" in payload else payload["c"]),
        price_change=_dec(payload["priceChange"] if "priceChange" in payload else payload["p"]),
        price_change_percent=_dec(
            payload["priceChangePercent"] if "priceChangePercent" in payload else payload["P"]
        ),
        high_price=_dec(payload["highPrice"] if "highPrice" in payload else payload["h"]),
        low_price=_dec(payload["lowPrice"] if "lowPrice" in payload else payload["l"]),
        volume=_dec(payload["volume"] if "volume" in payload else payload["v"]),
        quote_volume=_dec(
            payload["quoteVolume"] if "quoteVolume" in payload else payload["q"]
        ),
        event_time=_iso_from_ms(payload.get("closeTime", payload.get("E"))),
        fetched_at=fetched_at or _now_iso(),
        source=source,
        stale=stale,
    )


def parse_kline(values: list[Any], interval: str) -> Kline:
    """Parse one REST kline array. Binance returns all numbers as strings."""

    if not isinstance(values, list) or len(values) < 7:
        raise ValueError("Malformed kline payload")
    close_time = int(values[6])
    now_ms = int(time.time() * 1000)
    return Kline(
        open_time=int(values[0]),
        open_time_iso=_iso_from_ms(values[0]) or "",
        open=_dec(values[1]),
        high=_dec(values[2]),
        low=_dec(values[3]),
        close=_dec(values[4]),
        volume=_dec(values[5]),
        close_time=close_time,
        is_closed=close_time < now_ms,
    )


def parse_kline_event(payload: dict[str, Any]) -> Kline:
    """Parse a raw or combined Binance ``@kline`` WebSocket event.

    Raw:      {"e":"kline","k":{"t":...,"o":"...","x":true,...}}
    Combined: {"stream":"btcusdt@kline_1m","data":{"e":"kline","k":{...}}}
    """

    event = payload.get("data", payload)
    if not isinstance(event, dict) or not isinstance(event.get("k"), dict):
        raise ValueError("Malformed kline event")
    k = event["k"]
    return Kline(
        open_time=int(k["t"]),
        open_time_iso=_iso_from_ms(k["t"]) or "",
        open=_dec(k["o"]),
        high=_dec(k["h"]),
        low=_dec(k["l"]),
        close=_dec(k["c"]),
        volume=_dec(k["v"]),
        close_time=int(k["T"]),
        is_closed=bool(k.get("x", False)),
    )


def parse_exchange_rules(payload: dict[str, Any], symbol: str) -> SymbolRules:
    symbols = payload.get("symbols") or []
    match = next((item for item in symbols if item.get("symbol") == symbol), None)
    if match is None:
        raise ValueError(f"Symbol {symbol} missing from exchangeInfo")
    tick_size = Decimal("0.01")
    step_size = Decimal("0.00001")
    min_qty = Decimal("0.00001")
    max_qty = Decimal("9000")
    min_notional = Decimal("5")
    for item in match.get("filters", []):
        filter_type = item.get("filterType")
        if filter_type == "PRICE_FILTER":
            tick_size = _dec(item.get("tickSize", tick_size))
        elif filter_type == "LOT_SIZE":
            step_size = _dec(item.get("stepSize", step_size))
            min_qty = _dec(item.get("minQty", min_qty))
            max_qty = _dec(item.get("maxQty", max_qty))
        elif filter_type in {"MIN_NOTIONAL", "NOTIONAL"}:
            min_notional = _dec(item.get("minNotional", min_notional))
    return SymbolRules(
        symbol=symbol,
        base_asset=str(match.get("baseAsset", "BTC")),
        quote_asset=str(match.get("quoteAsset", "USDT")),
        tick_size=tick_size,
        step_size=step_size,
        min_qty=min_qty,
        max_qty=max_qty,
        min_notional=min_notional,
        source="binance",
    )


def demo_symbol_rules(symbol: str = "BTCUSDT") -> SymbolRules:
    return SymbolRules(
        symbol=symbol,
        base_asset="BTC",
        quote_asset="USDT",
        tick_size=Decimal("0.01"),
        step_size=Decimal("0.00001"),
        min_qty=Decimal("0.00001"),
        max_qty=Decimal("9000"),
        min_notional=Decimal("5"),
        source="demo",
    )


def _demo_price(now: float) -> tuple[Decimal, Decimal, Decimal, Decimal]:
    minute = now / 60.0
    base = 118_000 + 3800 * math.sin(minute / 37.0) + 700 * math.sin(minute / 7.3)
    base += 35 * math.sin(now / 4.0)
    percent = 1.8 * math.sin(minute / 53.0) + 0.4 * math.sin(minute / 3.0)
    open_24h = base / (1 + percent / 100)
    change = base - open_24h
    return (
        Decimal(f"{base:.2f}"),
        Decimal(f"{change:.2f}"),
        Decimal(f"{percent:.2f}"),
        Decimal(f"{open_24h:.2f}"),
    )


def demo_ticker(
    symbol: str = "BTCUSDT", *, now: float | None = None
) -> Ticker:
    now = now or time.time()
    last, change, percent, open_24h = _demo_price(now)
    high = max(last, open_24h) * Decimal("1.012")
    low = min(last, open_24h) * Decimal("0.988")
    volume = Decimal(f"{18_500 + 2600 * math.sin(now / 900):.3f}")
    quote_volume = volume * last
    event_iso = datetime.fromtimestamp(now, tz=timezone.utc).isoformat(
        timespec="seconds"
    )
    return Ticker(
        symbol=symbol,
        last_price=last,
        price_change=change,
        price_change_percent=percent,
        high_price=high.quantize(Decimal("0.01")),
        low_price=low.quantize(Decimal("0.01")),
        volume=volume,
        quote_volume=quote_volume.quantize(Decimal("0.01")),
        event_time=event_iso,
        fetched_at=_now_iso(),
        source="demo",
        stale=False,
    )


def demo_klines(symbol: str, interval: str, limit: int, *, now: float | None = None) -> list[Kline]:
    now = now or time.time()
    step_ms = KLINE_INTERVAL_MS[interval]
    current_bucket = int(now * 1000) // step_ms * step_ms
    items: list[Kline] = []
    for index in range(limit):
        open_time_ms = current_bucket - (limit - 1 - index) * step_ms
        phase = open_time_ms / step_ms
        center = 118_000 + 3800 * math.sin(phase / 37.0) + 700 * math.sin(phase / 7.3)
        wobble = 420 * math.sin(phase / 2.7) + 160 * math.sin(phase / 0.9)
        open_price = Decimal(f"{center + wobble:.2f}")
        close_price = Decimal(f"{center + wobble * 0.55 + 45 * math.sin(phase / 5.1):.2f}")
        high_price = max(open_price, close_price) * Decimal("1.0018")
        low_price = min(open_price, close_price) * Decimal("0.9982")
        volume = Decimal(f"{120 + 55 * abs(math.sin(phase / 3.3)):.4f}")
        close_time_ms = open_time_ms + step_ms - 1
        items.append(
            Kline(
                open_time=open_time_ms,
                open_time_iso=_iso_from_ms(open_time_ms) or "",
                open=open_price,
                high=high_price.quantize(Decimal("0.01")),
                low=low_price.quantize(Decimal("0.01")),
                close=close_price,
                volume=volume,
                close_time=close_time_ms,
                is_closed=close_time_ms < int(now * 1000),
            )
        )
    return items


class MarketService:
    def __init__(self, settings: Settings):
        self.settings = settings
        self._client: httpx.AsyncClient | None = None
        self._ticker_cache: dict[str, tuple[float, Ticker]] = {}
        self._kline_cache: dict[tuple[str, str, int], tuple[float, KlineSeries]] = {}
        self._rules_cache: dict[str, tuple[float, SymbolRules]] = {}
        self._funding_cache: dict[str, tuple[float, Decimal]] = {}
        self._locks: dict[str, asyncio.Lock] = {}
        self._market_base = (
            "https://testnet.binance.vision"
            if settings.mode is AppMode.TESTNET
            else os.environ.get("NEMT_BINANCE_MARKET_URL", "https://api.binance.com").rstrip("/")
        )
        self._futures_base = (
            "https://testnet.binancefuture.com"
            if settings.mode is AppMode.TESTNET
            else "https://fapi.binance.com"
        )

    def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(6.0, connect=4.0),
                headers={"User-Agent": "NEMT-App/0.1"},
            )
        return self._client

    async def close(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    def _lock(self, key: str) -> asyncio.Lock:
        if key not in self._locks:
            self._locks[key] = asyncio.Lock()
        return self._locks[key]

    def _ensure_allowed(self, symbol: str) -> str:
        normalized = symbol.strip().upper()
        if normalized not in self.settings.market_symbols:
            raise MarketUnavailable(f"Symbol {normalized} is not allowed")
        return normalized

    async def funding_rate(self, symbol: str) -> Decimal:
        """Current perpetual funding rate (8h), from the public futures venue.

        Paper trading only; never used to sign an order. Falls back to a small
        positive rate when the futures endpoint is unreachable so a paper
        position still accrues something instead of silently ignoring funding.
        """

        symbol = self._ensure_allowed(symbol)
        now = time.monotonic()
        cached = self._funding_cache.get(symbol)
        if cached and now - cached[0] < 300:
            return cached[1]
        if self.settings.market_source == "demo":
            return self._remember_funding(symbol, Decimal("0.0001"))
        try:
            response = await self._get_client().get(
                f"{self._futures_base}/fapi/v1/premiumIndex",
                params={"symbol": symbol},
            )
            response.raise_for_status()
            rate = Decimal(str(response.json().get("lastFundingRate", "0.0001")))
        except (httpx.HTTPError, ValueError, KeyError, InvalidOperation):
            rate = Decimal("0.0001")
        return self._remember_funding(symbol, rate)

    def _remember_funding(self, symbol: str, rate: Decimal) -> Decimal:
        self._funding_cache[symbol] = (time.monotonic(), rate)
        return rate

    async def ticker(self, symbol: str) -> Ticker:
        symbol = self._ensure_allowed(symbol)
        if self.settings.market_source == "demo":
            return demo_ticker(symbol)

        now = time.monotonic()
        cached = self._ticker_cache.get(symbol)
        if cached and now - cached[0] < 3:
            age = time.time() - self._fetched_epoch(cached[1])
            return self._mark_stale(cached[1], age > self.settings.market_stale_seconds)

        async with self._lock(f"ticker:{symbol}"):
            cached = self._ticker_cache.get(symbol)
            now = time.monotonic()
            if cached and now - cached[0] < 3:
                return cached[1]
            try:
                response = await self._get_client().get(
                    f"{self._market_base}/api/v3/ticker/24hr",
                    params={"symbol": symbol},
                )
                response.raise_for_status()
                parsed = parse_ticker(response.json(), symbol)
                self._ticker_cache[symbol] = (time.monotonic(), parsed)
                return parsed
            except (httpx.HTTPError, ValueError, KeyError):
                if cached is not None:
                    age = time.time() - self._fetched_epoch(cached[1])
                    return self._mark_stale(cached[1], age > self.settings.market_stale_seconds)
                if self.settings.mode is AppMode.DEMO:
                    fallback = demo_ticker(symbol)
                    self._ticker_cache[symbol] = (time.monotonic(), fallback)
                    return fallback
                raise MarketUnavailable("Market feed unavailable")

    @staticmethod
    def _fetched_epoch(ticker: Ticker) -> float:
        try:
            return datetime.fromisoformat(ticker.fetched_at).timestamp()
        except ValueError:
            return 0.0

    @staticmethod
    def _mark_stale(ticker: Ticker, stale: bool) -> Ticker:
        if ticker.stale == stale:
            return ticker
        return dataclasses.replace(ticker, stale=stale)

    async def klines(self, symbol: str, interval: str, limit: int = 80) -> KlineSeries:
        symbol = self._ensure_allowed(symbol)
        if interval not in ALLOWED_INTERVALS:
            raise MarketUnavailable(f"Unsupported interval {interval}")
        limit = max(10, min(int(limit), 200))

        if self.settings.market_source == "demo":
            now_iso = _now_iso()
            return KlineSeries(
                symbol=symbol,
                interval=interval,
                items=tuple(demo_klines(symbol, interval, limit)),
                fetched_at=now_iso,
                source="demo",
                stale=False,
            )

        key = (symbol, interval, limit)
        now = time.monotonic()
        cached = self._kline_cache.get(key)
        if cached and now - cached[0] < 10:
            return cached[1]

        async with self._lock(f"klines:{symbol}:{interval}:{limit}"):
            cached = self._kline_cache.get(key)
            if cached and time.monotonic() - cached[0] < 10:
                return cached[1]
            try:
                response = await self._get_client().get(
                    f"{self._market_base}/api/v3/klines",
                    params={"symbol": symbol, "interval": interval, "limit": limit},
                )
                response.raise_for_status()
                raw = response.json()
                if not isinstance(raw, list) or not raw:
                    raise ValueError("Empty kline response")
                items = tuple(parse_kline(item, interval) for item in raw)
                series = KlineSeries(
                    symbol=symbol,
                    interval=interval,
                    items=items,
                    fetched_at=_now_iso(),
                    source="binance",
                    stale=False,
                )
                self._kline_cache[key] = (time.monotonic(), series)
                return series
            except (httpx.HTTPError, ValueError, KeyError, TypeError):
                if cached is not None:
                    series = cached[1]
                    return KlineSeries(
                        symbol=series.symbol,
                        interval=series.interval,
                        items=series.items,
                        fetched_at=series.fetched_at,
                        source=series.source,
                        stale=True,
                    )
                if self.settings.mode is AppMode.DEMO:
                    return KlineSeries(
                        symbol=symbol,
                        interval=interval,
                        items=tuple(demo_klines(symbol, interval, limit)),
                        fetched_at=_now_iso(),
                        source="demo",
                        stale=False,
                    )
                raise MarketUnavailable("Candle feed unavailable")

    async def symbol_rules(self, symbol: str) -> SymbolRules:
        symbol = self._ensure_allowed(symbol)
        cached = self._rules_cache.get(symbol)
        if cached and time.monotonic() - cached[0] < 3600:
            return cached[1]

        try:
            response = await self._get_client().get(
                f"{self._market_base}/api/v3/exchangeInfo",
                params={"symbol": symbol},
            )
            response.raise_for_status()
            rules = parse_exchange_rules(response.json(), symbol)
            self._rules_cache[symbol] = (time.monotonic(), rules)
            return rules
        except (httpx.HTTPError, ValueError, KeyError):
            if self.settings.mode is not AppMode.DEMO:
                # Never silently trade with local precision guesses outside
                # DEMO. The order flow fails closed instead.
                raise MarketUnavailable("Exchange symbol filters unavailable")
            rules = demo_symbol_rules(symbol)
            self._rules_cache[symbol] = (time.monotonic(), rules)
            return rules

    async def feed_health(self) -> dict[str, object]:
        """Freshness summary for /system/status; never raises."""

        try:
            ticker = await self.ticker(self.settings.allowed_symbols[0])
            age_seconds: float | None = None
            try:
                age_seconds = max(
                    0.0,
                    time.time() - datetime.fromisoformat(ticker.fetched_at).timestamp(),
                )
            except ValueError:
                age_seconds = None
            return {
                "status": "stale" if ticker.stale else "ok",
                "source": ticker.source,
                "last_price": str(ticker.last_price),
                "fetched_at": ticker.fetched_at,
                "age_seconds": round(age_seconds, 1) if age_seconds is not None else None,
                "stale": ticker.stale,
            }
        except MarketUnavailable:
            return {
                "status": "unavailable",
                "source": None,
                "last_price": None,
                "fetched_at": None,
                "age_seconds": None,
                "stale": True,
            }
