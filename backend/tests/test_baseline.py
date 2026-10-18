"""Baseline safety and health checks for the NEMT App V0.1.

These tests are intentionally dependency-light and never use exchange keys.
They are part of the engineering-baseline acceptance gate (#6).
"""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from trade_app.config import AppMode, ConfigError, Settings, load_settings
from trade_app.main import create_app


def test_live_order_path_stays_disabled(tmp_path: Path) -> None:
    live = load_settings(
        {
            "NEMT_APP_MODE": "LIVE",
            "NEMT_SESSION_SECRET": "x" * 48,
            "NEMT_COOKIE_SECURE": "true",
            "NEMT_LIVE_TRADING_ENABLED": "true",
            "NEMT_DATABASE_PATH": str(tmp_path / "live.sqlite3"),
        }
    )

    assert live.mode is AppMode.LIVE
    assert live.trading_enabled is False
    assert live.live_trading_available is False


def test_unknown_mode_fails_closed() -> None:
    with pytest.raises(ConfigError):
        load_settings({"NEMT_APP_MODE": "PROD"})


def test_demo_health_and_readiness(tmp_path: Path) -> None:
    settings = Settings(
        mode=AppMode.DEMO,
        database_path=tmp_path / "baseline.sqlite3",
        session_secret="test-session-secret-" + "x" * 32,
        market_source="demo",
        demo_passwords={"demo": "nemt-demo"},
    )
    app = create_app(settings)

    with TestClient(app) as client:
        health = client.get("/api/v1/health")
        assert health.status_code == 200
        assert health.json()["status"] == "ok"
        assert health.json()["mode"] == "DEMO"

        ready = client.get("/api/v1/health/ready")
        assert ready.status_code == 200
        assert ready.json()["status"] == "ready"
        assert ready.json()["database"] == "ok"
