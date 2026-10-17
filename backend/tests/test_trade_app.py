from __future__ import annotations

import asyncio
from decimal import Decimal
from pathlib import Path
from typing import Any

import httpx
import pytest
from fastapi.testclient import TestClient

from trade_app.binance_spot import BinanceError, BinanceSpotAdapter
from trade_app.config import AppMode, ConfigError, Settings, load_settings
from trade_app.main import create_app
from trade_app.market import (
    MarketService,
    MarketUnavailable,
    parse_exchange_rules,
    parse_kline,
    parse_kline_event,
    parse_ticker,
)

DEMO_PASSWORDS = {
    "viewer": "nemt-viewer",
    "demo": "nemt-demo",
    "admin": "nemt-admin",
}


def make_settings(tmp_path: Path, **overrides: Any) -> Settings:
    mode = overrides.pop("mode", AppMode.DEMO)
    defaults: dict[str, Any] = {
        "mode": mode,
        "database_path": tmp_path / "nemt_test.sqlite3",
        "session_secret": "test-session-secret-" + "x" * 32,
        "market_source": "demo" if mode is AppMode.DEMO else "binance",
        "demo_passwords": DEMO_PASSWORDS,
        "confirmation_ttl_seconds": 90,
    }
    defaults.update(overrides)
    return Settings(**defaults)


@pytest.fixture()
def settings(tmp_path: Path) -> Settings:
    return make_settings(tmp_path)


@pytest.fixture()
def app(settings: Settings):
    return create_app(settings)


@pytest.fixture()
def client(app):
    with TestClient(app) as test_client:
        yield test_client


def demo_login(client: TestClient, account: str = "demo") -> str:
    response = client.post("/api/v1/auth/demo", json={"account": account})
    assert response.status_code == 200, response.text
    return response.json()["csrf_token"]


def csrf(csrf_token: str) -> dict[str, str]:
    return {"X-CSRF-Token": csrf_token}


def preview_market_buy(client: TestClient, csrf_token: str, quantity: str = "0.0005"):
    return client.post(
        "/api/v1/orders/preview",
        json={
            "symbol": "BTCUSDT",
            "side": "BUY",
            "type": "MARKET",
            "quantity": quantity,
        },
        headers=csrf(csrf_token),
    )


def balances_by_asset(client: TestClient) -> dict[str, dict[str, str]]:
    response = client.get("/api/v1/account/balances")
    assert response.status_code == 200
    return {item["asset"]: item for item in response.json()["balances"]}


# ---------------------------------------------------------------------------
# Authentication / RBAC / CSRF
# ---------------------------------------------------------------------------


def test_login_session_and_logout(client: TestClient):
    response = client.post(
        "/api/v1/auth/login", json={"username": "demo", "password": "nemt-demo"}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["authenticated"] is True
    assert body["user"]["username"] == "demo"
    assert "trader" in body["user"]["roles"]
    assert body["csrf_token"]
    assert "nemt-demo" not in response.text

    me = client.get("/api/v1/auth/me")
    assert me.status_code == 200
    assert me.json()["user"]["roles"] == body["user"]["roles"]

    missing_csrf = client.post("/api/v1/auth/logout")
    assert missing_csrf.status_code == 403
    assert missing_csrf.json()["error"]["code"] == "csrf_invalid"

    logged_out = client.post(
        "/api/v1/auth/logout", headers=csrf(body["csrf_token"])
    )
    assert logged_out.status_code == 200
    assert client.get("/api/v1/auth/me").status_code == 401


def test_invalid_credentials_and_unknown_fields(client: TestClient):
    response = client.post(
        "/api/v1/auth/login", json={"username": "demo", "password": "wrong"}
    )
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "invalid_credentials"

    malformed = client.post(
        "/api/v1/auth/login",
        json={"username": "demo", "password": "nemt-demo", "admin": True},
    )
    assert malformed.status_code == 422
    assert "nemt-demo" not in malformed.text


def test_market_requires_auth_and_session(client: TestClient):
    assert client.get("/api/v1/market/ticker").status_code == 401
    token = demo_login(client)
    assert token
    ticker = client.get("/api/v1/market/ticker")
    assert ticker.status_code == 200
    body = ticker.json()
    assert body["symbol"] == "BTCUSDT"
    assert Decimal(body["last_price"]) > 0
    assert body["source"] == "demo"
    assert body["stale"] is False

    klines = client.get(
        "/api/v1/market/klines", params={"interval": "1m", "limit": 30}
    )
    assert klines.status_code == 200
    payload = klines.json()
    assert len(payload["items"]) == 30
    assert payload["source"] == "demo"
    assert all(Decimal(item["close"]) > 0 for item in payload["items"])


def test_rbac_viewer_cannot_trade_and_csrf_is_required(client: TestClient):
    viewer_token = demo_login(client, "viewer")
    forbidden = preview_market_buy(client, viewer_token)
    assert forbidden.status_code == 403
    assert forbidden.json()["error"]["code"] == "forbidden"

    trader_token = demo_login(client, "demo")
    no_csrf = client.post(
        "/api/v1/orders/preview",
        json={"symbol": "BTCUSDT", "side": "BUY", "type": "MARKET", "quantity": "0.0005"},
    )
    assert no_csrf.status_code == 403
    assert no_csrf.json()["error"]["code"] == "csrf_invalid"

    valid = preview_market_buy(client, trader_token)
    assert valid.status_code == 200, valid.text


# ---------------------------------------------------------------------------
# Parsing and environment isolation
# ---------------------------------------------------------------------------


def test_parser_uses_latest_price_not_price_change():
    raw = {
        "symbol": "BTCUSDT",
        "priceChange": "500.00",
        "priceChangePercent": "1.20",
        "lastPrice": "68000.10",
        "highPrice": "70000.00",
        "lowPrice": "65000.00",
        "volume": "1234.5",
        "quoteVolume": "80000000",
        "closeTime": 1710000000000,
    }
    ticker = parse_ticker(raw, "BTCUSDT")
    assert ticker.last_price == Decimal("68000.10")
    assert ticker.price_change == Decimal("500.00")
    assert ticker.price_change_percent == Decimal("1.20")

    rest_kline = parse_kline(
        [1710000000000, "67000", "68000", "66000", "67500.5", "12.3", 1710000059999],
        "1m",
    )
    assert rest_kline.close == Decimal("67500.5")
    assert rest_kline.volume == Decimal("12.3")
    assert rest_kline.is_closed is True

    raw_event = {
        "e": "kline",
        "k": {
            "t": 1710000000000,
            "T": 1710000059999,
            "o": "67000",
            "h": "68000",
            "l": "66000",
            "c": "67500",
            "v": "12.3",
            "x": True,
        },
    }
    combined_event = {"stream": "btcusdt@kline_1m", "data": raw_event}
    for event in (raw_event, combined_event):
        parsed = parse_kline_event(event)
        assert parsed.open == Decimal("67000")
        assert parsed.close == Decimal("67500")
        assert parsed.is_closed is True


def test_exchange_rules_fail_closed_outside_demo(tmp_path: Path):
    async def scenario() -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            raise httpx.ConnectError("simulated offline", request=request)

        testnet_settings = make_settings(
            tmp_path,
            mode=AppMode.TESTNET,
            market_source="binance",
        )
        service = MarketService(testnet_settings)
        client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        service._client = client
        try:
            with pytest.raises(MarketUnavailable):
                await service.symbol_rules("BTCUSDT")
        finally:
            await client.aclose()
            await service.close()

        demo_settings = make_settings(tmp_path, mode=AppMode.DEMO, market_source="binance")
        demo_service = MarketService(demo_settings)
        demo_client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        demo_service._client = demo_client
        try:
            rules = await demo_service.symbol_rules("BTCUSDT")
            assert rules.source == "demo"
        finally:
            await demo_client.aclose()
            await demo_service.close()

    asyncio.run(scenario())


def test_exchange_rules_parse_filters():
    payload = {
        "symbols": [
            {
                "symbol": "BTCUSDT",
                "baseAsset": "BTC",
                "quoteAsset": "USDT",
                "filters": [
                    {"filterType": "PRICE_FILTER", "tickSize": "0.10"},
                    {"filterType": "LOT_SIZE", "stepSize": "0.00100000", "minQty": "0.001", "maxQty": "100"},
                    {"filterType": "MIN_NOTIONAL", "minNotional": "10"},
                ],
            }
        ]
    }
    rules = parse_exchange_rules(payload, "BTCUSDT")
    assert rules.tick_size == Decimal("0.10")
    assert rules.step_size == Decimal("0.001")
    assert rules.min_notional == Decimal("10")


def test_testnet_operator_login_and_demo_endpoint_disabled(tmp_path: Path):
    test_settings = make_settings(
        tmp_path,
        mode=AppMode.TESTNET,
        market_source="demo",  # isolated auth test; no venue calls
        allow_testnet_trading=False,
        operator_users={"ops": ("testnet-password-123", ("viewer", "trader", "admin"))},
    )
    app = create_app(test_settings)
    with TestClient(app) as client:
        login = client.post(
            "/api/v1/auth/login",
            json={"username": "ops", "password": "testnet-password-123"},
        )
        assert login.status_code == 200, login.text
        body = login.json()
        assert body["mode"] == "TESTNET"
        assert set(body["user"]["roles"]) == {"viewer", "trader", "admin"}

        demo = client.post("/api/v1/auth/demo", json={"account": "demo"})
        assert demo.status_code == 404
        assert demo.json()["error"]["code"] == "not_available"

        balances = client.get("/api/v1/account/balances").json()
        assert balances["account_status"] == "NOT_CONFIGURED"
        assert balances["connected"] is False
        assert balances["balances"] == []


def test_testnet_operator_credentials_load_from_env(tmp_path: Path):
    loaded = load_settings(
        {
            "NEMT_APP_MODE": "TESTNET",
            "NEMT_MARKET_SOURCE": "binance",
            "NEMT_SESSION_SECRET": "x" * 48,
            "NEMT_DATABASE_PATH": str(tmp_path / "ops.sqlite3"),
            "NEMT_TESTNET_TRADER_PASSWORD": "testnet-password-123",
            "NEMT_TESTNET_ADMIN_PASSWORD": "testnet-admin-pass-123",
        }
    )
    assert set(loaded.operator_users) == {"trader", "admin"}
    assert loaded.operator_users["trader"][1] == ("viewer", "trader")
    assert "viewer" in loaded.operator_users["admin"][1]

    with pytest.raises(ConfigError):
        load_settings(
            {
                "NEMT_APP_MODE": "TESTNET",
                "NEMT_MARKET_SOURCE": "binance",
                "NEMT_SESSION_SECRET": "x" * 48,
                "NEMT_TESTNET_TRADER_PASSWORD": "short",
            }
        )


def test_environment_isolation_fails_closed(tmp_path: Path):
    with pytest.raises(ConfigError):
        load_settings({"NEMT_APP_MODE": "PROD"})
    with pytest.raises(ConfigError):
        load_settings({"NEMT_APP_MODE": "TESTNET", "NEMT_MARKET_SOURCE": "binance"})
    with pytest.raises(ConfigError):
        load_settings({"NEMT_APP_MODE": "TESTNET", "NEMT_MARKET_SOURCE": "demo"})

    testnet = load_settings(
        {
            "NEMT_APP_MODE": "TESTNET",
            "NEMT_MARKET_SOURCE": "binance",
            "NEMT_SESSION_SECRET": "x" * 48,
            "NEMT_ALLOW_TESTNET_TRADING": "true",
            "NEMT_BINANCE_API_KEY": "",
            "NEMT_BINANCE_API_SECRET": "",
            "NEMT_DATABASE_PATH": str(tmp_path / "testnet.sqlite3"),
        }
    )
    assert testnet.trading_enabled is False

    live = load_settings(
        {
            "NEMT_APP_MODE": "LIVE",
            "NEMT_SESSION_SECRET": "x" * 48,
            "NEMT_COOKIE_SECURE": "true",
            "NEMT_LIVE_TRADING_ENABLED": "true",
            "NEMT_DATABASE_PATH": str(tmp_path / "live.sqlite3"),
        }
    )
    assert live.trading_enabled is False
    assert live.live_trading_available is False


# ---------------------------------------------------------------------------
# Demo order lifecycle, idempotency and risk
# ---------------------------------------------------------------------------


def test_market_order_fills_once_and_is_idempotent(client: TestClient):
    token = demo_login(client)
    before = balances_by_asset(client)

    preview = preview_market_buy(client, token)
    assert preview.status_code == 200, preview.text
    body = preview.json()
    assert body["risk"]["approved"] is True
    assert body["draft"]["normalized"] is False or body["draft"]["quantity"]
    preview_token = body["preview_token"]

    created = client.post(
        "/api/v1/orders",
        json={"confirmation_token": preview_token, "idempotency_key": "idem-market-0001"},
        headers=csrf(token),
    )
    assert created.status_code == 201, created.text
    order = created.json()["order"]
    assert order["status"] == "FILLED"
    assert order["type"] == "MARKET"
    assert order["client_order_id"].startswith("nemt_")
    assert Decimal(order["filled_qty"]) == Decimal("0.0005")
    assert len(order["fills"]) == 1
    assert Decimal(order["fee"]) > 0

    replay = client.post(
        "/api/v1/orders",
        json={"confirmation_token": preview_token, "idempotency_key": "idem-market-0001"},
        headers=csrf(token),
    )
    assert replay.status_code == 200
    assert replay.json()["replayed"] is True
    assert replay.json()["order"]["id"] == order["id"]

    after = balances_by_asset(client)
    assert Decimal(after["BTC"]["free"]) == Decimal(before["BTC"]["free"]) + Decimal("0.0005")
    assert Decimal(after["USDT"]["free"]) < Decimal(before["USDT"]["free"])

    listed = client.get("/api/v1/orders").json()
    assert listed["count"] == 1
    assert listed["open_count"] == 0


def test_preview_rejects_oversized_order_with_reasons(client: TestClient):
    token = demo_login(client)
    response = preview_market_buy(client, token, quantity="0.01")
    assert response.status_code == 422
    error = response.json()["error"]
    assert error["code"] == "risk_rejected"
    reasons = " ".join(error["details"]["risk"]["reasons"])
    assert "max_notional" in reasons
    assert client.get("/api/v1/orders").json()["count"] == 0


def test_pause_between_preview_and_confirm_fails_closed(app, client: TestClient):
    trader_token = demo_login(client)
    preview = preview_market_buy(client, trader_token)
    assert preview.status_code == 200
    preview_token = preview.json()["preview_token"]

    with TestClient(app) as admin_client:
        admin_token = demo_login(admin_client, "admin")
        paused = admin_client.post(
            "/api/v1/admin/pause-new-orders",
            json={"reason": "operator drill"},
            headers=csrf(admin_token),
        )
        assert paused.status_code == 200
        assert paused.json()["pause_new_orders"] is True

        blocked = client.post(
            "/api/v1/orders",
            json={"confirmation_token": preview_token, "idempotency_key": "idem-paused-01"},
            headers=csrf(trader_token),
        )
        assert blocked.status_code == 422
        error = blocked.json()["error"]
        assert error["code"] == "risk_rejected"
        assert any("kill_switch" in reason for reason in error["details"]["risk"]["reasons"])

        orders = client.get("/api/v1/orders").json()["orders"]
        assert orders[0]["status"] == "REJECTED"

        resumed = admin_client.post(
            "/api/v1/admin/resume-new-orders",
            json={"reason": "drill complete"},
            headers=csrf(admin_token),
        )
        assert resumed.status_code == 200
        assert resumed.json()["pause_new_orders"] is False


def test_pause_survives_restart(settings: Settings):
    app_one = create_app(settings)
    with TestClient(app_one) as admin_client:
        token = demo_login(admin_client, "admin")
        response = admin_client.post(
            "/api/v1/admin/pause-new-orders",
            json={"reason": "persistence test"},
            headers=csrf(token),
        )
        assert response.status_code == 200

    app_two = create_app(settings)
    with TestClient(app_two) as client:
        token = demo_login(client)
        blocked = preview_market_buy(client, token)
        assert blocked.status_code == 422
        assert any(
            "kill_switch" in reason
            for reason in blocked.json()["error"]["details"]["risk"]["reasons"]
        )


def test_limit_order_reserves_then_cancel_releases(client: TestClient):
    token = demo_login(client)
    before = balances_by_asset(client)
    preview = client.post(
        "/api/v1/orders/preview",
        json={
            "symbol": "BTCUSDT",
            "side": "BUY",
            "type": "LIMIT",
            "quantity": "0.0002",
            "price": "60000.009",
        },
        headers=csrf(token),
    )
    assert preview.status_code == 200, preview.text
    preview_body = preview.json()
    assert preview_body["draft"]["normalized"] is True
    assert Decimal(preview_body["draft"]["price"]) == Decimal("60000.00")

    created = client.post(
        "/api/v1/orders",
        json={
            "confirmation_token": preview_body["preview_token"],
            "idempotency_key": "idem-limit-0001",
        },
        headers=csrf(token),
    )
    assert created.status_code == 201, created.text
    order = created.json()["order"]
    assert order["status"] == "NEW"

    during = balances_by_asset(client)
    assert Decimal(during["USDT"]["locked"]) > 0
    assert Decimal(during["USDT"]["free"]) < Decimal(before["USDT"]["free"])

    canceled = client.post(
        f"/api/v1/orders/{order['id']}/cancel", headers=csrf(token)
    )
    assert canceled.status_code == 200, canceled.text
    assert canceled.json()["status"] == "CANCELED"

    after = balances_by_asset(client)
    assert Decimal(after["USDT"]["locked"]) == Decimal("0")
    assert Decimal(after["USDT"]["free"]) == Decimal(before["USDT"]["free"])


def test_admin_bulk_cancel_does_not_claim_positions_closed(app, client: TestClient):
    token = demo_login(client)
    preview = client.post(
        "/api/v1/orders/preview",
        json={
            "symbol": "BTCUSDT",
            "side": "BUY",
            "type": "LIMIT",
            "quantity": "0.0002",
            "price": "50000",
        },
        headers=csrf(token),
    )
    assert preview.status_code == 200
    client.post(
        "/api/v1/orders",
        json={
            "confirmation_token": preview.json()["preview_token"],
            "idempotency_key": "idem-bulk-cancel-01",
        },
        headers=csrf(token),
    )

    with TestClient(app) as admin_client:
        admin_token = demo_login(admin_client, "admin")
        no_confirm = admin_client.post(
            "/api/v1/admin/cancel-open-orders",
            json={"confirm": False, "reason": "no confirmation"},
            headers=csrf(admin_token),
        )
        assert no_confirm.status_code == 422

        result = admin_client.post(
            "/api/v1/admin/cancel-open-orders",
            json={"confirm": True, "reason": "operator drill"},
            headers=csrf(admin_token),
        )
        assert result.status_code == 200
        assert result.json()["canceled"] == 1
        assert "已成交仓位" in result.json()["message"]

        events = admin_client.get("/api/v1/audit/events").json()["events"]
        actions = {event["action"] for event in events}
        assert "admin.cancel_open_orders" in actions
        assert "order.canceled" in actions


def test_audit_redacts_credentials_and_supports_request_id(client: TestClient):
    token = demo_login(client)
    client.get("/api/v1/market/ticker", headers={"X-Request-ID": "req_test_0001"})
    preview_market_buy(client, token)

    with TestClient(client.app) as admin_client:
        admin_token = demo_login(admin_client, "admin")
        events = admin_client.get("/api/v1/audit/events", params={"limit": 200}).json()
    serialized = str(events)
    assert "nemt-demo" not in serialized
    assert "nemt-admin" not in serialized
    assert "auth.login" not in serialized or "password" not in serialized
    assert any(event["action"] == "order.preview" for event in events["events"])


def test_system_status_distinguishes_five_states(client: TestClient):
    demo_login(client)
    response = client.get("/api/v1/system/status")
    assert response.status_code == 200
    body = response.json()
    assert body["mode"] == "DEMO"
    assert body["flags"]["server_ok"] is True
    assert body["flags"]["authenticated"] is True
    assert body["flags"]["market_fresh"] is True
    assert body["flags"]["account_connected"] is True
    assert body["flags"]["trading_enabled"] is True
    assert body["live_trading_available"] is False
    assert body["risk"]["pause_new_orders"] is False


# ---------------------------------------------------------------------------
# Binance adapter (mock transport, no network, no real credentials)
# ---------------------------------------------------------------------------


def test_binance_adapter_signs_requests_and_parses_account(tmp_path: Path):
    captured: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api/v3/time":
            return httpx.Response(200, json={"serverTime": 1_700_000_000_000})
        if request.url.path == "/api/v3/account":
            captured["api_key"] = request.headers.get("X-MBX-APIKEY")
            captured["account_query"] = request.url.query.decode()
            return httpx.Response(
                200,
                json={
                    "canTrade": False,
                    "canWithdraw": False,
                    "accountType": "SPOT",
                    "permissions": ["SPOT"],
                    "balances": [
                        {"asset": "BTC", "free": "0.01", "locked": "0.001"},
                        {"asset": "USDT", "free": "500", "locked": "0"},
                    ],
                },
            )
        if request.url.path == "/api/v3/order":
            captured["order_query"] = request.url.query.decode()
            return httpx.Response(
                200,
                json={
                    "orderId": 12345,
                    "clientOrderId": "nemt_test",
                    "symbol": "BTCUSDT",
                    "side": "BUY",
                    "type": "MARKET",
                    "status": "FILLED",
                    "price": "0",
                    "origQty": "0.001",
                    "executedQty": "0.001",
                    "cummulativeQuoteQty": "100.5",
                    "fills": [
                        {
                            "price": "100500",
                            "qty": "0.001",
                            "commission": "0.000001",
                            "commissionAsset": "BTC",
                            "tradeId": 99,
                        }
                    ],
                },
            )
        return httpx.Response(404, json={"code": -1, "msg": "not found"})

    async def scenario() -> None:
        client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        test_settings = make_settings(
            tmp_path,
            mode=AppMode.TESTNET,
            market_source="binance",
            allow_testnet_trading=True,
            binance_api_key="PUBLIC-TEST-KEY",
            binance_api_secret="SERVER-ONLY-SECRET",
        )
        adapter = BinanceSpotAdapter(test_settings, client=client)
        account = await adapter.get_account()
        assert account.can_trade is False
        assert account.can_withdraw is False
        assert any(item.asset == "BTC" and item.free == Decimal("0.01") for item in account.balances)

        query = captured["account_query"]
        assert "signature=" in query
        assert "timestamp=" in query
        assert "recvWindow=5000" in query
        assert "SERVER-ONLY-SECRET" not in query
        assert captured["api_key"] == "PUBLIC-TEST-KEY"

        result = await adapter.create_order(
            symbol="BTCUSDT",
            side="BUY",
            order_type="MARKET",
            quantity=Decimal("0.001"),
            price=None,
            client_order_id="nemt_test",
        )
        assert result.status == "FILLED"
        assert result.executed_qty == Decimal("0.001")
        assert "newClientOrderId=nemt_test" in captured["order_query"]
        assert "SERVER-ONLY-SECRET" not in captured["order_query"]
        await adapter.close()

    asyncio.run(scenario())


def test_binance_adapter_does_not_claim_unknown_outcome(tmp_path: Path):
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api/v3/time":
            return httpx.Response(200, json={"serverTime": 1_700_000_000_000})
        raise httpx.ReadTimeout("simulated timeout", request=request)

    async def scenario() -> None:
        client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        test_settings = make_settings(
            tmp_path,
            mode=AppMode.TESTNET,
            market_source="binance",
            allow_testnet_trading=True,
            binance_api_key="KEY",
            binance_api_secret="SECRET",
        )
        adapter = BinanceSpotAdapter(test_settings, client=client)
        with pytest.raises(BinanceError) as error:
            await adapter.create_order(
                symbol="BTCUSDT",
                side="BUY",
                order_type="MARKET",
                quantity=Decimal("0.001"),
                price=None,
                client_order_id="nemt_test_timeout",
            )
        assert error.value.unknown_outcome is True
        await adapter.close()

    asyncio.run(scenario())
