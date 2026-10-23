"""Auto trader tests: signal in, paper position out, journalled, no human click.

Every test uses a stub signal service and fixed prices, so the decisions are
deterministic and no network is touched.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from trade_app.auto_trader import AutoTrader
from trade_app.config import AppMode, Settings
from trade_app.db import Database, iso
from trade_app.main import create_app
from trade_app.market import Ticker
from trade_app.paper import LONG, PERP, SHORT, PaperService
from trade_app.signals import NemtState, SignalCard

DEMO_PASSWORDS = {"viewer": "nemt-viewer", "demo": "nemt-demo", "admin": "nemt-admin"}
PRICES = {"BTCUSDT": "80000", "ETHUSDT": "3000", "SOLUSDT": "150"}


def make_settings(tmp_path: Path, **overrides: Any) -> Settings:
    mode = overrides.pop("mode", AppMode.DEMO)
    defaults: dict[str, Any] = {
        "mode": mode,
        "database_path": tmp_path / "auto_trade.sqlite3",
        "session_secret": "test-session-secret-" + "x" * 32,
        "market_source": "demo" if mode is AppMode.DEMO else "binance",
        "demo_passwords": DEMO_PASSWORDS,
        "confirmation_ttl_seconds": 90,
        "paper_symbols": ("BTCUSDT",),
        "auto_trade_username": "demo",
        "auto_trade_max_positions": 3,
        "auto_trade_cooldown_minutes": 15,
    }
    defaults.update(overrides)
    return Settings(**defaults)


class StubMarket:
    def __init__(self, prices: dict[str, str] | None = None) -> None:
        self.prices = {key: Decimal(value) for key, value in (prices or PRICES).items()}

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
        return Decimal("0.0001")


def make_card(
    symbol: str,
    phase: str,
    direction: str,
    *,
    psi: float = 0.8,
    entropy: float = 0.9,
    stop: str | None = "78400",
    take: str | None = "83200",
    notional: str = "10",
    leverage: int = 2,
) -> SignalCard:
    state = NemtState(
        psi=psi,
        phi=20.0,
        entropy=entropy,
        phase=phase,  # type: ignore[arg-type]
        wave_amplitude=0.05,
        wave_frequency=0.1,
    )
    return SignalCard(
        symbol=symbol,
        interval="15m",
        mark_price=Decimal("80000"),
        state=state,
        direction=direction,  # type: ignore[arg-type]
        strength=80,
        reasons=["test"],
        entry=Decimal("80000"),
        stop_loss=Decimal(stop) if stop else None,
        take_profit=Decimal(take) if take else None,
        stop_pct=0.02,
        risk_usdt=Decimal("0.2"),
        suggested_notional=Decimal(notional),
        suggested_leverage=leverage,
        action_label="test",
    )


class StubSignals:
    def __init__(self, cards: dict[str, SignalCard]) -> None:
        self.cards = cards

    def set(self, cards: dict[str, SignalCard]) -> None:
        self.cards = cards

    async def card(self, symbol: str, interval: str = "15m", *, equity: Any = None) -> SignalCard:  # noqa: ARG002
        return self.cards[symbol]

    async def board(self, symbols: Any, interval: str = "15m", *, equity: Any = None) -> list[SignalCard]:  # noqa: ARG002
        return [self.cards[symbol] for symbol in symbols if symbol in self.cards]


def run(coro: Any) -> Any:
    return asyncio.run(coro)


def build(tmp_path: Path, signals: StubSignals, **overrides: Any):
    settings = make_settings(tmp_path, **overrides)
    db = Database(settings.database_path)
    db.initialize(settings)
    market = StubMarket()
    paper = PaperService(db, settings, market)
    return AutoTrader(db, settings, paper, signals), paper, market, db


WAIT_CARD = make_card("BTCUSDT", "critical", "WAIT", psi=0.1)


# ---------------------------------------------------------------------------
# Entries
# ---------------------------------------------------------------------------


def test_opens_long_on_critical_up(tmp_path: Path) -> None:
    signals = StubSignals({"BTCUSDT": make_card("BTCUSDT", "critical_up", "LONG")})
    trader, paper, _market, _db = build(tmp_path, signals)

    decisions = run(trader.run_once())

    assert decisions == [{"symbol": "BTCUSDT", "action": "OPEN_LONG"}]
    positions = run(paper.positions("demo"))
    assert len(positions) == 1
    assert positions[0]["side"] == LONG
    assert positions[0]["market"] == PERP

    events = trader.events()
    assert events[0]["action"] == "OPEN"
    assert "critical_up" in events[0]["reason"]


def test_opens_short_on_critical_down(tmp_path: Path) -> None:
    signals = StubSignals({"BTCUSDT": make_card("BTCUSDT", "critical_down", "SHORT", psi=-0.8)})
    trader, paper, _market, _db = build(tmp_path, signals)

    assert run(trader.run_once()) == [{"symbol": "BTCUSDT", "action": "OPEN_SHORT"}]
    assert run(paper.positions("demo"))[0]["side"] == SHORT


def test_no_position_when_waiting(tmp_path: Path) -> None:
    signals = StubSignals({"BTCUSDT": WAIT_CARD})
    trader, paper, _market, _db = build(tmp_path, signals)

    assert run(trader.run_once()) == []
    assert run(paper.positions("demo")) == []


def test_kill_switch_stops_everything(tmp_path: Path) -> None:
    signals = StubSignals({"BTCUSDT": make_card("BTCUSDT", "critical_up", "LONG")})
    trader, paper, _market, _db = build(tmp_path, signals)

    assert trader.set_enabled(False, actor="tester") is False
    assert run(trader.run_once()) == []
    assert run(paper.positions("demo")) == []
    assert trader.board is not None

    assert trader.set_enabled(True, actor="tester") is True
    assert run(trader.run_once()) == [{"symbol": "BTCUSDT", "action": "OPEN_LONG"}]


def test_pause_keeps_protective_exits_alive(tmp_path: Path) -> None:
    """A paused desk must still honour the stops on positions it already holds."""

    signals = StubSignals(
        {"BTCUSDT": make_card("BTCUSDT", "critical_up", "LONG", stop="78400", take="83200")}
    )
    trader, paper, market, _db = build(tmp_path, signals)
    run(trader.run_once())
    assert len(run(paper.positions("demo"))) == 1

    trader.set_enabled(False, actor="tester")
    market.move("BTCUSDT", "77000")  # stop breached while paused

    decisions = run(trader.run_once())

    assert decisions == [{"symbol": "BTCUSDT", "action": "CLOSE_止损"}]
    assert run(paper.positions("demo")) == []


# ---------------------------------------------------------------------------
# Exits
# ---------------------------------------------------------------------------


def test_closes_on_decay(tmp_path: Path) -> None:
    signals = StubSignals({"BTCUSDT": make_card("BTCUSDT", "critical_up", "LONG")})
    trader, paper, _market, _db = build(tmp_path, signals)
    run(trader.run_once())

    signals.set({"BTCUSDT": make_card("BTCUSDT", "decay", "EXIT", psi=0.05, entropy=0.05)})
    assert run(trader.run_once()) == [{"symbol": "BTCUSDT", "action": "CLOSE"}]
    assert run(paper.positions("demo")) == []
    assert any("decay" in event["reason"] for event in trader.events())


def test_closes_and_then_flips_on_reversal(tmp_path: Path) -> None:
    signals = StubSignals({"BTCUSDT": make_card("BTCUSDT", "critical_up", "LONG")})
    trader, paper, _market, _db = build(tmp_path, signals)
    run(trader.run_once())

    signals.set({"BTCUSDT": make_card("BTCUSDT", "critical_down", "SHORT", psi=-0.9)})
    assert run(trader.run_once()) == [{"symbol": "BTCUSDT", "action": "CLOSE"}]
    assert run(paper.positions("demo")) == []

    # A later pass (after the cooldown window) opens the opposite side.
    with trader.db.tx(immediate=True) as conn:
        conn.execute(
            "UPDATE auto_trade_state SET last_action_at = ? WHERE symbol = ?",
            (iso(datetime.now(timezone.utc) - timedelta(hours=1)), "BTCUSDT"),
        )
    assert run(trader.run_once()) == [{"symbol": "BTCUSDT", "action": "OPEN_SHORT"}]


def test_stop_loss_closes_position(tmp_path: Path) -> None:
    signals = StubSignals(
        {"BTCUSDT": make_card("BTCUSDT", "critical_up", "LONG", stop="78400", take="83200")}
    )
    trader, paper, market, _db = build(tmp_path, signals)
    run(trader.run_once())

    market.move("BTCUSDT", "78000")  # below the stop
    decisions = run(trader.run_once())

    assert decisions == [{"symbol": "BTCUSDT", "action": "CLOSE_止损"}]
    assert run(paper.positions("demo")) == []
    assert any("止损" in event["reason"] for event in trader.events())


def test_take_profit_closes_position(tmp_path: Path) -> None:
    signals = StubSignals(
        {"BTCUSDT": make_card("BTCUSDT", "critical_up", "LONG", stop="78400", take="83200")}
    )
    trader, paper, market, _db = build(tmp_path, signals)
    run(trader.run_once())

    market.move("BTCUSDT", "84000")  # above the target
    assert run(trader.run_once()) == [{"symbol": "BTCUSDT", "action": "CLOSE_止盈"}]
    assert run(paper.positions("demo")) == []


# ---------------------------------------------------------------------------
# Rails
# ---------------------------------------------------------------------------


def test_cooldown_blocks_immediate_reentry(tmp_path: Path) -> None:
    signals = StubSignals({"BTCUSDT": make_card("BTCUSDT", "critical_up", "LONG")})
    trader, paper, _market, _db = build(tmp_path, signals, auto_trade_cooldown_minutes=60)
    run(trader.run_once())

    position = run(paper.positions("demo"))[0]
    run(paper.close_position("demo", position["id"], fraction=Decimal("1")))

    assert run(trader.run_once()) == []
    assert run(paper.positions("demo")) == []
    assert any(event["action"] == "SKIP" and "冷却" in event["reason"] for event in trader.events())


def test_position_cap_is_enforced(tmp_path: Path) -> None:
    signals = StubSignals(
        {
            "BTCUSDT": make_card("BTCUSDT", "critical_up", "LONG", notional="5"),
            "ETHUSDT": make_card("ETHUSDT", "critical_up", "LONG", notional="5"),
            "SOLUSDT": make_card("SOLUSDT", "critical_up", "LONG", notional="5"),
        }
    )
    trader, paper, _market, _db = build(
        tmp_path,
        signals,
        paper_symbols=("BTCUSDT", "ETHUSDT", "SOLUSDT"),
        auto_trade_max_positions=1,
    )

    decisions = run(trader.run_once())

    assert len(decisions) == 1
    assert len(run(paper.positions("demo"))) == 1
    assert any("上限" in event["reason"] for event in trader.events())


def test_notional_is_capped_to_a_per_symbol_slot(tmp_path: Path) -> None:
    """A 40 USDT signal on a 20 USDT account must not eat the whole book."""

    signals = StubSignals(
        {"BTCUSDT": make_card("BTCUSDT", "critical_up", "LONG", notional="40", leverage=1)}
    )
    trader, paper, _market, _db = build(
        tmp_path,
        signals,
        auto_trade_max_positions=2,
        paper_initial_equity=Decimal("20"),
    )

    decisions = run(trader.run_once())

    assert decisions == [{"symbol": "BTCUSDT", "action": "OPEN_LONG"}]
    position = run(paper.positions("demo"))[0]
    # 20 * 0.95 / 2 slots = 9.5 USDT, not the 40 the card asked for
    assert abs(Decimal(position["notional"]) - Decimal("9.5")) < Decimal("0.2")


def test_insufficient_cash_is_skipped_not_crashed(tmp_path: Path) -> None:
    """A 5 USDT account cannot fund even the minimum order; skip, don't crash."""

    signals = StubSignals(
        {"BTCUSDT": make_card("BTCUSDT", "critical_up", "LONG", notional="10", leverage=1)}
    )
    trader, paper, _market, _db = build(
        tmp_path, signals, paper_initial_equity=Decimal("5")
    )

    assert run(trader.run_once()) == []
    assert run(paper.positions("demo")) == []
    assert any(event["action"] == "SKIP" and "开仓被拒" in event["reason"] for event in trader.events())


# ---------------------------------------------------------------------------
# Board contract (what the execution page renders)
# ---------------------------------------------------------------------------


def test_board_matches_the_ui_contract(tmp_path: Path) -> None:
    signals = StubSignals({"BTCUSDT": make_card("BTCUSDT", "critical_up", "LONG")})
    trader, _paper, _market, _db = build(tmp_path, signals)
    run(trader.run_once())

    board = run(trader.board("demo"))
    strategy = board["strategy"]

    assert strategy["state"] == "运行中"
    assert strategy["timeframe"] == "15m"
    assert strategy["risk"] == "1%"
    assert "BTC" in strategy["signal"]

    leg = strategy["legs"][0]
    assert leg["symbol"] == "BTC/USDT"
    assert leg["market"] == "PERPETUAL"
    assert leg["side"] == LONG
    assert leg["leverage"] == 2
    assert leg["unit"] == "BTC"
    assert leg["fills"][0]["action"] == "OPEN"
    assert leg["fills"][0]["at"] > 1_600_000_000_000  # epoch millis
    assert Decimal(leg["mark"]) > 0

    assert board["auto_trade"]["enabled"] is True
    assert Decimal(board["account"]["equity"]) > 0
    assert board["events"][0]["action"] == "OPEN"


def test_board_shows_paused_state_after_toggle(tmp_path: Path) -> None:
    signals = StubSignals({"BTCUSDT": WAIT_CARD})
    trader, _paper, _market, _db = build(tmp_path, signals)
    trader.set_enabled(False, actor="tester")
    board = run(trader.board("demo"))
    assert board["strategy"]["state"] == "已暂停"
    assert board["auto_trade"]["enabled"] is False


# ---------------------------------------------------------------------------
# HTTP surface
# ---------------------------------------------------------------------------


def csrf(token: str) -> dict[str, str]:
    return {"X-CSRF-Token": token}


def test_strategy_routes(tmp_path: Path) -> None:
    settings = make_settings(tmp_path)
    with TestClient(create_app(settings)) as client:
        login = client.post("/api/v1/auth/demo", json={"account": "demo"})
        assert login.status_code == 200, login.text
        token = login.json()["csrf_token"]

        board = client.get("/api/v1/strategy/board")
        assert board.status_code == 200, board.text
        payload = board.json()
        assert payload["strategy"]["id"] == "nemt"
        assert isinstance(payload["strategy"]["legs"], list)
        assert payload["auto_trade"]["username"] == "demo"
        assert isinstance(payload["events"], list)

        paused = client.post(
            "/api/v1/strategy/auto-trade", headers=csrf(token), json={"enabled": False}
        )
        assert paused.status_code == 200, paused.text
        assert paused.json()["enabled"] is False
        assert client.get("/api/v1/strategy/board").json()["auto_trade"]["enabled"] is False

        resumed = client.post(
            "/api/v1/strategy/auto-trade", headers=csrf(token), json={"enabled": True}
        )
        assert resumed.json()["enabled"] is True

        manual = client.post("/api/v1/strategy/run-once", headers=csrf(token))
        assert manual.status_code == 200, manual.text
        assert manual.json()["count"] >= 0

        # writes need CSRF
        blocked = client.post("/api/v1/strategy/auto-trade", json={"enabled": False})
        assert blocked.status_code in (401, 403)
