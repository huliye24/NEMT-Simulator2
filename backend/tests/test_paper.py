"""Paper trading engine tests.

These run fully offline: a stub market service supplies fixed prices, so every
number below is arithmetic we can check by hand.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from trade_app.config import AppMode, Settings
from trade_app.db import Database, iso
from trade_app.errors import ApiException
from trade_app.main import create_app
from trade_app.market import Ticker
from trade_app.paper import PERP, SPOT, PaperService, funding_boundaries

DEMO_PASSWORDS = {
    "viewer": "nemt-viewer",
    "demo": "nemt-demo",
    "admin": "nemt-admin",
}


def make_settings(tmp_path: Path, **overrides: Any) -> Settings:
    mode = overrides.pop("mode", AppMode.DEMO)
    defaults: dict[str, Any] = {
        "mode": mode,
        "database_path": tmp_path / "paper_test.sqlite3",
        "session_secret": "test-session-secret-" + "x" * 32,
        "market_source": "demo" if mode is AppMode.DEMO else "binance",
        "demo_passwords": DEMO_PASSWORDS,
        "confirmation_ttl_seconds": 90,
    }
    defaults.update(overrides)
    return Settings(**defaults)


class StubMarket:
    """Deterministic quotes; ``prices`` is mutated by tests to move the market."""

    def __init__(self, prices: dict[str, str], funding: str = "0.0001") -> None:
        self.prices = {symbol: Decimal(value) for symbol, value in prices.items()}
        self.funding = Decimal(funding)

    def move(self, symbol: str, price: str) -> None:
        self.prices[symbol] = Decimal(price)

    async def ticker(self, symbol: str) -> Ticker:
        price = self.prices[symbol]
        return Ticker(
            symbol=symbol,
            last_price=price,
            price_change=Decimal("0"),
            price_change_percent=Decimal("0"),
            high_price=price,
            low_price=price,
            volume=Decimal("1"),
            quote_volume=price,
            event_time=None,
            fetched_at=iso(),
            source="binance",
            stale=False,
        )

    async def funding_rate(self, symbol: str) -> Decimal:  # noqa: ARG002
        return self.funding


PRICES = {"BTCUSDT": "80000", "ETHUSDT": "3000", "SOLUSDT": "150"}


@pytest.fixture()
def market() -> StubMarket:
    return StubMarket(PRICES)


@pytest.fixture()
def paper(tmp_path: Path, market: StubMarket) -> PaperService:
    # Pinned to 20 USDT so the hand-computed margins below stay readable;
    # the shipped default is 2000 (see test_default_paper_equity_is_2000).
    settings = make_settings(tmp_path, paper_initial_equity=Decimal("20"))
    db = Database(settings.database_path)
    db.initialize(settings)
    return PaperService(db, settings, market)  # type: ignore[arg-type]


def asyncio_run(coro: Any) -> Any:
    import asyncio

    return asyncio.run(coro)


# ---------------------------------------------------------------------------
# Account bootstrap
# ---------------------------------------------------------------------------


def test_paper_account_starts_with_configured_equity(paper: PaperService) -> None:
    state = asyncio_run(paper.account("demo"))
    assert state["initial_equity"] == Decimal("20")
    assert state["cash"] == Decimal("20")
    assert state["equity"] == Decimal("20")
    assert state["open_positions"] == 0
    assert state["mode"] == "PAPER"


def test_default_paper_equity_is_2000(tmp_path: Path) -> None:
    """The shipped default is 2000 USDT so several symbols can hold positions."""

    settings = make_settings(tmp_path)
    assert settings.paper_initial_equity == Decimal("2000")


def test_paper_reset_restores_starting_equity(
    paper: PaperService, market: StubMarket
) -> None:
    asyncio_run(
        paper.open_position(
            "demo",
            symbol="BTCUSDT",
            market=PERP,
            side="LONG",
            notional=Decimal("10"),
            leverage=2,
        )
    )
    assert len(asyncio_run(paper.positions("demo"))) == 1
    state = asyncio_run(paper.reset("demo"))
    assert state["equity"] == Decimal("20")
    assert state["open_positions"] == 0
    assert asyncio_run(paper.positions("demo")) == []


# ---------------------------------------------------------------------------
# Perpetual: isolated margin, P&L, close
# ---------------------------------------------------------------------------


def test_paper_perp_isolated_margin_and_pnl(
    paper: PaperService, market: StubMarket
) -> None:
    opened = asyncio_run(
        paper.open_position(
            "demo",
            symbol="BTCUSDT",
            market=PERP,
            side="LONG",
            notional=Decimal("20"),
            leverage=5,
        )
    )
    assert opened["market"] == PERP
    assert opened["side"] == "LONG"
    assert opened["leverage"] == 5

    # 5x means one fifth of the notional is locked as margin, not all of it.
    margin = opened["margin"]
    assert abs(margin - Decimal("4")) < Decimal("0.01")
    # Filling long means paying up through the slippage.
    assert opened["entry_price"] > Decimal("80000")

    state = asyncio_run(paper.account("demo"))
    # Opening moves money from cash into margin; only the fee is really spent.
    assert state["cash"] < Decimal("16.1")
    assert abs(state["equity"] - (Decimal("20") - state["fees"])) < Decimal("0.01")

    # Mark up 1%: the P&L must be amplified by the position size, not the margin.
    market.move("BTCUSDT", "80800")
    positions = asyncio_run(paper.positions("demo"))
    assert len(positions) == 1
    live = positions[0]
    assert live["unrealized"] > 0
    assert live["mark_price"] == Decimal("80800")
    assert live["liquidation_price"] is not None
    assert live["liquidation_price"] < live["entry_price"]

    closed = asyncio_run(paper.close_position("demo", opened["id"], fraction=Decimal("1")))
    assert closed["closed"] is True
    assert closed["gross_pnl"] > 0

    after = asyncio_run(paper.account("demo"))
    assert after["open_positions"] == 0
    assert after["cash"] > Decimal("20")
    assert after["realized"] == closed["gross_pnl"]
    # Equity equals cash once nothing is open, and it matches initial + gross - fees.
    assert abs(after["equity"] - after["cash"]) < Decimal("0.00000001")
    expected = Decimal("20") + closed["gross_pnl"] - after["fees"] - after["funding"]
    assert abs(after["equity"] - expected) < Decimal("0.01")


def test_paper_short_profits_when_price_falls(
    paper: PaperService, market: StubMarket
) -> None:
    opened = asyncio_run(
        paper.open_position(
            "demo",
            symbol="ETHUSDT",
            market=PERP,
            side="SHORT",
            notional=Decimal("20"),
            leverage=3,
        )
    )
    # A short fills below the mark.
    assert opened["entry_price"] < Decimal("3000")
    market.move("ETHUSDT", "2900")
    live = asyncio_run(paper.positions("demo"))[0]
    assert live["unrealized"] > 0
    assert live["liquidation_price"] > live["entry_price"]


def test_paper_liquidation_closes_position_at_liq_price(
    paper: PaperService, market: StubMarket
) -> None:
    opened = asyncio_run(
        paper.open_position(
            "demo",
            symbol="BTCUSDT",
            market=PERP,
            side="LONG",
            notional=Decimal("20"),
            leverage=10,
        )
    )
    liquidation = opened["liquidation_price"]
    assert liquidation is not None

    # Push the mark below the liquidation price: isolated margin is lost.
    market.move("BTCUSDT", str(Decimal(liquidation) - Decimal("500")))
    positions = asyncio_run(paper.positions("demo"))
    assert positions == []

    state = asyncio_run(paper.account("demo"))
    assert state["open_positions"] == 0
    # A 10x isolated long that gets liquidated loses about its margin (~2 USDT).
    assert Decimal("17.5") < state["equity"] < Decimal("20")

    fills = paper.fills("demo")
    assert any(fill["action"] == "LIQUIDATE" for fill in fills)


# ---------------------------------------------------------------------------
# Spot
# ---------------------------------------------------------------------------


def test_paper_spot_buy_holds_asset_and_keeps_equity_identity(
    paper: PaperService, market: StubMarket
) -> None:
    opened = asyncio_run(
        paper.open_position(
            "demo",
            symbol="BTCUSDT",
            market=SPOT,
            side="LONG",
            notional=Decimal("10"),
        )
    )
    assert opened["margin"] == Decimal("0")
    assert opened["liquidation_price"] is None

    state = asyncio_run(paper.account("demo"))
    assert state["spot_value"] > 0
    # Cash left over plus the position value, minus the fee, is the equity.
    assert abs(state["equity"] - (Decimal("20") - state["fees"])) < Decimal("0.01")

    market.move("BTCUSDT", "88000")
    live = asyncio_run(paper.positions("demo"))[0]
    assert live["unrealized"] > 0

    asyncio_run(paper.close_position("demo", opened["id"]))
    after = asyncio_run(paper.account("demo"))
    assert after["open_positions"] == 0
    assert after["cash"] > Decimal("20")


def test_paper_spot_rejects_short(paper: PaperService) -> None:
    with pytest.raises(ApiException) as excinfo:
        asyncio_run(
            paper.open_position(
                "demo",
                symbol="BTCUSDT",
                market=SPOT,
                side="SHORT",
                notional=Decimal("10"),
            )
        )
    assert excinfo.value.code == "paper_spot_long_only"


# ---------------------------------------------------------------------------
# Guards
# ---------------------------------------------------------------------------


def test_paper_rejects_bad_leverage_symbol_and_size(paper: PaperService) -> None:
    with pytest.raises(ApiException) as lev:
        asyncio_run(
            paper.open_position(
                "demo",
                symbol="BTCUSDT",
                market=PERP,
                side="LONG",
                notional=Decimal("20"),
                leverage=11,
            )
        )
    assert lev.value.code == "paper_leverage_invalid"

    with pytest.raises(ApiException) as symbol:
        asyncio_run(
            paper.open_position(
                "demo",
                symbol="DOGEUSDT",
                market=PERP,
                side="LONG",
                notional=Decimal("20"),
            )
        )
    assert symbol.value.code == "paper_symbol_not_allowed"

    with pytest.raises(ApiException) as size:
        asyncio_run(
            paper.open_position(
                "demo",
                symbol="BTCUSDT",
                market=PERP,
                side="LONG",
                notional=Decimal("1"),
            )
        )
    assert size.value.code == "paper_notional_too_small"


def test_paper_rejects_order_beyond_cash(paper: PaperService) -> None:
    """20 USDT of cash cannot carry 40 USDT of spot notional."""

    with pytest.raises(ApiException) as excinfo:
        asyncio_run(
            paper.open_position(
                "demo",
                symbol="BTCUSDT",
                market=SPOT,
                side="LONG",
                notional=Decimal("40"),
            )
        )
    assert excinfo.value.code == "paper_insufficient_funds"


# ---------------------------------------------------------------------------
# Funding
# ---------------------------------------------------------------------------


def test_funding_boundaries_follow_utc_grid() -> None:
    since = datetime(2026, 1, 1, 7, 0, tzinfo=timezone.utc)
    now = datetime(2026, 1, 1, 20, 0, tzinfo=timezone.utc)
    boundaries = funding_boundaries(since, now, 8)
    assert [item.hour for item in boundaries] == [8, 16]


def test_paper_funding_accrues_on_perp(
    paper: PaperService, market: StubMarket
) -> None:
    opened = asyncio_run(
        paper.open_position(
            "demo",
            symbol="BTCUSDT",
            market=PERP,
            side="LONG",
            notional=Decimal("20"),
            leverage=5,
        )
    )
    # Pretend the position has been open across a funding window.
    with paper.db.tx(immediate=True) as conn:
        conn.execute(
            "UPDATE paper_positions SET last_funding_at = ? WHERE id = ?",
            (iso(datetime.now(timezone.utc) - timedelta(hours=9)), opened["id"]),
        )

    asyncio_run(paper.positions("demo"))
    state = asyncio_run(paper.account("demo"))
    # Longs pay when the rate is positive.
    assert state["funding"] > 0
    assert state["cash"] < Decimal("20")


# ---------------------------------------------------------------------------
# HTTP surface (DEMO mode, demo quotes, no network)
# ---------------------------------------------------------------------------


def csrf(token: str) -> dict[str, str]:
    return {"X-CSRF-Token": token}


def demo_session(client: TestClient) -> str:
    response = client.post("/api/v1/auth/demo", json={"account": "demo"})
    assert response.status_code == 200, response.text
    return response.json()["csrf_token"]


def test_paper_routes_roundtrip(tmp_path: Path) -> None:
    settings = make_settings(tmp_path)
    with TestClient(create_app(settings)) as client:
        token = demo_session(client)

        account = client.get("/api/v1/paper/account")
        assert account.status_code == 200, account.text
        assert Decimal(account.json()["initial_equity"]) == settings.paper_initial_equity

        opened = client.post(
            "/api/v1/paper/positions",
            headers=csrf(token),
            json={
                "symbol": "BTCUSDT",
                "market": "PERP",
                "side": "LONG",
                "notional": "10",
                "leverage": 3,
                "strategy": "NEMT",
            },
        )
        assert opened.status_code == 200, opened.text
        body = opened.json()
        assert len(body["positions"]) == 1
        position_id = body["positions"][0]["id"]

        closed = client.post(
            f"/api/v1/paper/positions/{position_id}/close",
            headers=csrf(token),
            json={"fraction": "1"},
        )
        assert closed.status_code == 200, closed.text
        assert closed.json()["closed"] is True

        fills = client.get("/api/v1/paper/fills").json()
        assert fills["count"] >= 2
        equity = client.get("/api/v1/paper/equity").json()
        assert equity["count"] >= 1

        # Writes need CSRF: without the header the request must be rejected.
        blocked = client.post(
            "/api/v1/paper/positions",
            json={
                "symbol": "BTCUSDT",
                "market": "PERP",
                "side": "LONG",
                "notional": "10",
            },
        )
        assert blocked.status_code in (401, 403)
