"""Minimal Binance Spot REST adapter (read-only + Testnet order support).

Security boundaries:
- credentials exist only on the server;
- nothing in this module logs the secret, signature or auth headers;
- POST /order is never retried automatically. If the outcome is unknown the
  caller must query by ``clientOrderId`` before taking any further action.
"""

from __future__ import annotations

import asyncio
import hashlib
import hmac
import time
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from typing import Any
from urllib.parse import urlencode

import httpx

from .config import AppMode, Settings
from .security import redact

TESTNET_BASE_URL = "https://testnet.binance.vision"
LIVE_BASE_URL = "https://api.binance.com"


class BinanceError(RuntimeError):
    def __init__(
        self,
        message: str,
        *,
        http_status: int | None = None,
        code: int | None = None,
        unknown_outcome: bool = False,
        retry_after: float | None = None,
    ):
        super().__init__(message)
        self.http_status = http_status
        self.code = code
        self.unknown_outcome = unknown_outcome
        self.retry_after = retry_after


@dataclass(frozen=True)
class BinanceBalance:
    asset: str
    free: Decimal
    locked: Decimal


@dataclass(frozen=True)
class BinanceAccount:
    balances: tuple[BinanceBalance, ...]
    can_trade: bool
    can_withdraw: bool
    account_type: str
    permissions: tuple[str, ...]
    fetched_at: str


@dataclass(frozen=True)
class BinanceOrderResult:
    exchange_order_id: str
    client_order_id: str
    symbol: str
    side: str
    order_type: str
    status: str
    price: Decimal
    orig_qty: Decimal
    executed_qty: Decimal
    cummulative_quote_qty: Decimal
    fills: tuple[dict[str, Any], ...] = field(default_factory=tuple)
    updated_at: str | None = None
    raw: dict[str, Any] = field(default_factory=dict, repr=False)


def _to_decimal(value: Any, default: str = "0") -> Decimal:
    try:
        return Decimal(str(value if value is not None else default))
    except (InvalidOperation, ValueError):
        return Decimal(default)


def _now_iso() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class BinanceSpotAdapter:
    """Server-side adapter. Instantiate only with a key present."""

    def __init__(
        self,
        settings: Settings,
        *,
        client: httpx.AsyncClient | None = None,
        base_url: str | None = None,
    ):
        self.settings = settings
        self.api_key = settings.binance_api_key or ""
        self.api_secret = settings.binance_api_secret or ""
        self.base_url = (
            base_url
            or (TESTNET_BASE_URL if settings.mode is AppMode.TESTNET else LIVE_BASE_URL)
        ).rstrip("/")
        self._owns_client = client is None
        self._client = client or httpx.AsyncClient(
            timeout=httpx.Timeout(8.0, connect=5.0),
            headers={"User-Agent": "NEMT-App/0.1"},
        )
        self._time_offset_ms = 0
        self._time_synced = False
        self._lock = asyncio.Lock()

    @property
    def configured(self) -> bool:
        return bool(self.api_key and self.api_secret)

    @property
    def writes_allowed(self) -> bool:
        """Only TESTNET orders are reachable in V0.1."""

        return (
            self.settings.mode is AppMode.TESTNET
            and self.settings.allow_testnet_trading
            and self.configured
        )

    async def close(self) -> None:
        if self._owns_client:
            await self._client.aclose()

    async def _sync_time(self) -> None:
        if self._time_synced:
            return
        async with self._lock:
            if self._time_synced:
                return
            try:
                response = await self._client.get(f"{self.base_url}/api/v3/time")
                response.raise_for_status()
                server_ms = int(response.json()["serverTime"])
                self._time_offset_ms = server_ms - int(time.time() * 1000)
                self._time_synced = True
            except (httpx.HTTPError, KeyError, ValueError) as exc:
                raise BinanceError("Unable to synchronise exchange time") from exc

    def _sign_query(self, params: dict[str, Any]) -> str:
        query = urlencode(params, doseq=True)
        signature = hmac.new(
            self.api_secret.encode("utf-8"),
            query.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        return f"{query}&signature={signature}"

    async def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        signed: bool = False,
        retry_read: bool = True,
        timeout_unknown_outcome: bool = False,
    ) -> Any:
        if not self.configured:
            raise BinanceError("Binance credentials are not configured")
        if signed:
            await self._sync_time()

        query_params = dict(params or {})
        if signed:
            query_params["timestamp"] = int(time.time() * 1000) + self._time_offset_ms
            query_params["recvWindow"] = self.settings.binance_recv_window_ms

        attempts = 2 if retry_read and method.upper() == "GET" else 1
        last_error: Exception | None = None
        for attempt in range(attempts):
            try:
                if signed:
                    query_string = self._sign_query(query_params)
                    response = await self._client.request(
                        method,
                        f"{self.base_url}{path}?{query_string}",
                        headers={"X-MBX-APIKEY": self.api_key},
                    )
                else:
                    response = await self._client.request(
                        method,
                        f"{self.base_url}{path}",
                        params=query_params,
                        headers={"X-MBX-APIKEY": self.api_key} if self.api_key else {},
                    )

                if response.status_code == 429 or response.status_code == 418:
                    retry_after = None
                    try:
                        retry_after = float(response.headers.get("Retry-After", ""))
                    except ValueError:
                        pass
                    raise BinanceError(
                        "Exchange rate limit reached",
                        http_status=response.status_code,
                        retry_after=retry_after,
                    )
                if response.status_code >= 500:
                    raise BinanceError(
                        "Exchange server error",
                        http_status=response.status_code,
                    )
                if response.status_code >= 400:
                    code = None
                    message = "Exchange rejected the request"
                    try:
                        payload = response.json()
                        code = int(payload.get("code")) if payload.get("code") is not None else None
                        message = str(payload.get("msg") or message)
                    except (ValueError, TypeError):
                        pass
                    raise BinanceError(
                        message,
                        http_status=response.status_code,
                        code=code,
                    )
                return response.json()
            except (httpx.TimeoutException, httpx.NetworkError) as exc:
                last_error = exc
                if attempt + 1 >= attempts:
                    raise BinanceError(
                        "Exchange connection failed",
                        unknown_outcome=timeout_unknown_outcome,
                    ) from exc
                await asyncio.sleep(0.4 * (attempt + 1))
            except BinanceError as exc:
                last_error = exc
                if exc.http_status in {429, 418, 500, 502, 503, 504} and attempt + 1 < attempts:
                    delay = exc.retry_after or min(2 ** attempt * 0.5, 3)
                    await asyncio.sleep(min(delay, 5))
                    continue
                raise
        raise BinanceError("Exchange request failed") from last_error

    async def get_account(self) -> BinanceAccount:
        payload = await self._request(
            "GET",
            "/api/v3/account",
            signed=True,
            retry_read=True,
        )
        balances: list[BinanceBalance] = []
        for item in payload.get("balances", []):
            free = _to_decimal(item.get("free"))
            locked = _to_decimal(item.get("locked"))
            if free == 0 and locked == 0:
                continue
            balances.append(
                BinanceBalance(
                    asset=str(item.get("asset")),
                    free=free,
                    locked=locked,
                )
            )
        permissions = payload.get("permissions")
        if not isinstance(permissions, list):
            single = payload.get("permission")
            permissions = [str(single)] if single else []
        return BinanceAccount(
            balances=tuple(balances),
            can_trade=bool(payload.get("canTrade", False)),
            can_withdraw=bool(payload.get("canWithdraw", False)),
            account_type=str(payload.get("accountType", "UNKNOWN")),
            permissions=tuple(str(item) for item in permissions),
            fetched_at=_now_iso(),
        )

    async def create_order(
        self,
        *,
        symbol: str,
        side: str,
        order_type: str,
        quantity: Decimal,
        price: Decimal | None,
        client_order_id: str,
        time_in_force: str = "GTC",
    ) -> BinanceOrderResult:
        if not self.writes_allowed:
            raise BinanceError("Testnet order writes are disabled")
        params: dict[str, Any] = {
            "symbol": symbol,
            "side": side,
            "type": order_type,
            "newClientOrderId": client_order_id,
            "quantity": format(quantity, "f"),
            "newOrderRespType": "FULL",
        }
        if order_type == "LIMIT":
            if price is None:
                raise BinanceError("LIMIT order requires a price")
            params["price"] = format(price, "f")
            params["timeInForce"] = time_in_force or "GTC"
        payload = await self._request(
            "POST",
            "/api/v3/order",
            params=params,
            signed=True,
            retry_read=False,
            timeout_unknown_outcome=True,
        )
        return self._order_result(payload)

    async def get_order(
        self,
        *,
        symbol: str,
        client_order_id: str,
    ) -> BinanceOrderResult:
        payload = await self._request(
            "GET",
            "/api/v3/order",
            params={"symbol": symbol, "origClientOrderId": client_order_id},
            signed=True,
            retry_read=True,
        )
        return self._order_result(payload)

    async def cancel_order(
        self,
        *,
        symbol: str,
        client_order_id: str,
    ) -> BinanceOrderResult:
        if not self.writes_allowed:
            raise BinanceError("Testnet order writes are disabled")
        payload = await self._request(
            "DELETE",
            "/api/v3/order",
            params={"symbol": symbol, "origClientOrderId": client_order_id},
            signed=True,
            retry_read=False,
            timeout_unknown_outcome=True,
        )
        return self._order_result(payload)

    @staticmethod
    def _order_result(payload: dict[str, Any]) -> BinanceOrderResult:
        fills_raw = payload.get("fills") or []
        fills = tuple(redact(item) if isinstance(item, dict) else item for item in fills_raw)
        return BinanceOrderResult(
            exchange_order_id=str(payload.get("orderId", "")),
            client_order_id=str(payload.get("clientOrderId", "")),
            symbol=str(payload.get("symbol", "")),
            side=str(payload.get("side", "")),
            order_type=str(payload.get("type", "")),
            status=str(payload.get("status", "UNKNOWN")).upper(),
            price=_to_decimal(payload.get("price")),
            orig_qty=_to_decimal(payload.get("origQty")),
            executed_qty=_to_decimal(payload.get("executedQty")),
            cummulative_quote_qty=_to_decimal(payload.get("cummulativeQuoteQty")),
            fills=fills,
            updated_at=None,
            raw=payload,
        )
