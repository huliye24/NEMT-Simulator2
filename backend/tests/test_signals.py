"""NEMT signal engine tests.

The formulas must agree with the repository's reference implementation in
``src/web/strategy/nemt/nemtCalculator.ts``: ψ is an EMA of simple returns
scaled ×100, φ is annualised volatility, and S is normalised histogram entropy.
"""

from __future__ import annotations

import asyncio
import math
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from trade_app.config import AppMode, Settings
from trade_app.main import create_app
from trade_app.market import Kline, KlineSeries
from trade_app.signals import (
    NemtConfig,
    NemtSignalService,
    atr,
    compute_state,
    determine_phase,
    ema,
    price_entropy,
    strength,
)

DEMO_PASSWORDS = {"viewer": "nemt-viewer", "demo": "nemt-demo", "admin": "nemt-admin"}
CFG = NemtConfig()


def make_settings(tmp_path: Path, **overrides: Any) -> Settings:
    mode = overrides.pop("mode", AppMode.DEMO)
    defaults: dict[str, Any] = {
        "mode": mode,
        "database_path": tmp_path / "signal_test.sqlite3",
        "session_secret": "test-session-secret-" + "x" * 32,
        "market_source": "demo" if mode is AppMode.DEMO else "binance",
        "demo_passwords": DEMO_PASSWORDS,
        "confirmation_ttl_seconds": 90,
    }
    defaults.update(overrides)
    return Settings(**defaults)


def up_series(bars: int = 60, step: float = 0.01, start: float = 100.0) -> list[float]:
    return [start * (1 + step) ** index for index in range(bars)]


def down_series(bars: int = 60, step: float = 0.01, start: float = 100.0) -> list[float]:
    return [start * (1 - step) ** index for index in range(bars)]


# ---------------------------------------------------------------------------
# ψ / φ / S
# ---------------------------------------------------------------------------


def test_psi_is_ema_of_returns_times_100() -> None:
    closes = [100.0, 101.0, 101.0, 102.0, 102.0]
    returns = [0.01, 0.0, 1 / 101, 0.0]
    expected = ema(returns, 0.3) * 100
    state = compute_state(closes, CFG)
    assert state.psi == pytest.approx(expected, rel=1e-9)
    # a strengthening uptrend must produce a positive ψ
    assert state.psi > 0


def test_phi_is_annualised_volatility() -> None:
    closes = [100.0, 102.0, 99.0, 103.0, 98.0, 104.0]
    returns = [
        (closes[i] - closes[i - 1]) / closes[i - 1] for i in range(1, len(closes))
    ]
    mean = sum(returns) / len(returns)
    variance = sum((value - mean) ** 2 for value in returns) / len(returns)
    expected = math.sqrt(variance) * math.sqrt(24 * 365) * 100
    assert compute_state(closes, CFG).phi == pytest.approx(expected, rel=1e-9)
    # constant-percentage growth has zero return variance
    assert compute_state(up_series(), CFG).phi == pytest.approx(0.0, abs=1e-12)


def test_entropy_bounds_and_monotonicity() -> None:
    assert price_entropy([100.0] * 20) == 0.0  # no dispersion, no entropy
    trend = price_entropy(up_series(bars=60))
    assert 0.9 <= trend <= 1.0  # prices spread over every bin
    flat = price_entropy([100.0 + 0.001 * (index % 2) for index in range(60)])
    assert 0.0 < flat < 0.5


def test_phase_rules_match_reference_thresholds() -> None:
    # high entropy (S > 0.7)
    assert determine_phase(0.8, 0.9, CFG) == "critical_up"
    assert determine_phase(-0.8, 0.9, CFG) == "critical_down"
    assert determine_phase(0.1, 0.9, CFG) == "critical"
    # low entropy (S < 0.15)
    assert determine_phase(0.4, 0.05, CFG) == "stable"
    assert determine_phase(0.0, 0.05, CFG) == "decay"
    # middle entropy is "stable" and yields no new entry
    assert determine_phase(0.9, 0.4, CFG) == "stable"


def test_strength_is_bounded_percentage() -> None:
    assert strength(0.0, 0.0, CFG) == 0
    assert strength(5.0, 1.0, CFG) == 100
    # half the momentum threshold and half the entropy threshold -> mid score
    assert strength(0.25, 0.35, CFG) == 50


def test_uptrend_and_downtrend_phases() -> None:
    up = compute_state(up_series(), CFG)
    assert up.phase == "critical_up" and up.psi > CFG.critical_psi
    down = compute_state(down_series(), CFG)
    assert down.phase == "critical_down" and down.psi < -CFG.critical_psi
    # a linear ramp has decaying percentage returns: entropy is high but ψ < 0.5
    ramp = compute_state([100.0 + index for index in range(120)], CFG)
    assert ramp.phase == "critical"


def test_not_enough_data_fails_closed() -> None:
    from trade_app.errors import ApiException

    with pytest.raises(ApiException):
        compute_state([100.0, 101.0], CFG)


# ---------------------------------------------------------------------------
# ATR + signal cards
# ---------------------------------------------------------------------------


def to_klines(closes: list[float], spread: float = 0.004) -> tuple[Kline, ...]:
    items = []
    for index, close in enumerate(closes):
        payload = Decimal(f"{close:.8f}")
        band = Decimal(f"{close * spread:.8f}")
        items.append(
            Kline(
                open_time=index * 60_000,
                open_time_iso=f"2026-01-01T00:00:{index % 60:02d}+00:00",
                open=payload,
                high=payload + band,
                low=payload - band,
                close=payload,
                volume=Decimal("10"),
                close_time=index * 60_000 + 59_999,
                is_closed=True,
            )
        )
    return tuple(items)


def test_atr_uses_true_range() -> None:
    klines = to_klines(up_series(bars=20), spread=0.01)
    value = atr(klines, 14)
    assert value > 0
    # with a ±1% band the true range is about 2% of price
    assert 1.0 < value < 5.0


class StubKlineMarket:
    def __init__(self, closes: list[float]) -> None:
        self.closes = closes

    async def klines(self, symbol: str, interval: str, limit: int = 120) -> KlineSeries:  # noqa: ARG002
        items = to_klines(self.closes[-limit:])
        return KlineSeries(
            symbol=symbol,
            interval=interval,
            items=items,
            fetched_at="2026-01-01T00:00:00+00:00",
            source="binance",
            stale=False,
        )


def run(coro: Any) -> Any:
    return asyncio.run(coro)


def test_card_gives_long_with_risk_levels_on_uptrend(tmp_path: Path) -> None:
    settings = make_settings(tmp_path, paper_initial_equity=Decimal("20"))
    service = NemtSignalService(settings, StubKlineMarket(up_series(bars=60)))  # type: ignore[arg-type]
    card = run(service.card("BTCUSDT", "15m"))

    assert card.direction == "LONG"
    assert card.state.phase == "critical_up"
    assert card.strength > 0
    assert card.entry is not None and card.stop_loss is not None and card.take_profit is not None
    assert card.stop_loss < card.entry < card.take_profit
    assert 0.01 <= card.stop_pct <= 0.05

    # risk is 1% of a 20 USDT account, and size follows from the stop distance
    assert card.risk_usdt is not None and card.risk_usdt == pytest.approx(Decimal("0.2"))
    assert card.suggested_notional is not None
    assert card.suggested_notional >= settings.paper_min_notional
    # reward:risk must be 1:2
    risk = float(card.entry - card.stop_loss)
    reward = float(card.take_profit - card.entry)
    assert reward == pytest.approx(risk * 2, rel=1e-6)


def test_suggested_trade_fits_the_account(tmp_path: Path) -> None:
    """Regression: risk sizing must never suggest a position the cash cannot carry.

    A 1% stop on a 20 USDT account asks for a 20 USDT position; at 1x that leaves
    no room for the taker fee, so the card has to raise the leverage.
    """

    settings = make_settings(tmp_path, paper_initial_equity=Decimal("20"))
    service = NemtSignalService(settings, StubKlineMarket(up_series(bars=60)))  # type: ignore[arg-type]
    card = run(service.card("BTCUSDT", "15m"))
    assert card.suggested_notional is not None

    equity = Decimal("20")
    notional = card.suggested_notional
    leverage = card.suggested_leverage
    margin = notional / leverage
    fee = notional * settings.paper_taker_fee_perp
    assert margin + fee <= equity, f"{margin} + {fee} exceeds {equity}"
    assert leverage <= settings.paper_max_leverage


def test_card_gives_short_on_downtrend(tmp_path: Path) -> None:
    settings = make_settings(tmp_path)
    service = NemtSignalService(settings, StubKlineMarket(down_series(bars=60)))  # type: ignore[arg-type]
    card = run(service.card("ETHUSDT", "15m"))
    assert card.direction == "SHORT"
    assert card.stop_loss is not None and card.take_profit is not None
    assert card.take_profit < card.entry < card.stop_loss


def test_card_waits_when_entropy_is_middle(tmp_path: Path) -> None:
    settings = make_settings(tmp_path)
    choppy = [100.0 + 0.001 * (index % 2) for index in range(60)]
    service = NemtSignalService(settings, StubKlineMarket(choppy))  # type: ignore[arg-type]
    card = run(service.card("SOLUSDT", "15m"))
    assert card.direction in ("HOLD", "EXIT")
    assert card.entry is None  # no levels without a directional signal


# ---------------------------------------------------------------------------
# HTTP surface
# ---------------------------------------------------------------------------


def test_signal_route_returns_cards(tmp_path: Path) -> None:
    settings = make_settings(tmp_path)
    with TestClient(create_app(settings)) as client:
        assert client.post("/api/v1/auth/demo", json={"account": "demo"}).status_code == 200
        response = client.get("/api/v1/signals/nemt?interval=15m")
        assert response.status_code == 200, response.text
        body = response.json()
        assert body["count"] == len(settings.paper_symbols)
        assert body["thresholds"]["critical_entropy"] == "0.7"
        for card in body["cards"]:
            assert card["phase"] in ("stable", "critical", "critical_up", "critical_down", "decay")
            assert 0 <= card["strength"] <= 100
            assert card["action_label"]
            assert isinstance(card["reasons"], list) and card["reasons"]

        anon = client.get("/api/v1/signals/nemt", headers={"Cookie": ""})
        assert anon.status_code in (200, 401)
