"""Account snapshots for DEMO and read-only exchange connectivity."""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from typing import Literal

from .binance_spot import BinanceError, BinanceSpotAdapter
from .config import AppMode, Settings
from .db import Database, iso


@dataclass(frozen=True)
class Balance:
    asset: str
    free: Decimal
    locked: Decimal

    @property
    def total(self) -> Decimal:
        return self.free + self.locked


@dataclass(frozen=True)
class AccountSnapshot:
    status: Literal["CONNECTED", "NOT_CONFIGURED", "DISCONNECTED", "ERROR"]
    connected: bool
    source: Literal["demo", "binance", "none"]
    fetched_at: str | None
    stale: bool
    note: str | None
    balances: tuple[Balance, ...]


class AccountService:
    def __init__(
        self,
        db: Database,
        settings: Settings,
        adapter: BinanceSpotAdapter | None,
    ):
        self.db = db
        self.settings = settings
        self.adapter = adapter
        self._cache: tuple[float, AccountSnapshot] | None = None
        self._lock = asyncio.Lock()

    async def snapshot(self, username: str) -> AccountSnapshot:
        if self.settings.mode is AppMode.DEMO:
            return self._demo_snapshot(username)
        return await self._exchange_snapshot()

    def _demo_snapshot(self, username: str) -> AccountSnapshot:
        rows = self.db.query_all(
            "SELECT asset, free, locked FROM demo_wallets WHERE username = ? ORDER BY asset",
            (username,),
        )
        balances = tuple(
            Balance(
                asset=str(row["asset"]),
                free=Decimal(str(row["free"])),
                locked=Decimal(str(row["locked"])),
            )
            for row in rows
        )
        return AccountSnapshot(
            status="CONNECTED",
            connected=True,
            source="demo",
            fetched_at=iso(),
            stale=False,
            note="DEMO 模拟账户，余额不代表真实资产",
            balances=balances,
        )

    async def _exchange_snapshot(self) -> AccountSnapshot:
        if self.adapter is None or not self.adapter.configured:
            return AccountSnapshot(
                status="NOT_CONFIGURED",
                connected=False,
                source="none",
                fetched_at=None,
                stale=True,
                note="未配置交易所只读/Testnet 凭据（仅可存在于服务端环境变量）",
                balances=(),
            )

        cached = self._cache
        if cached and time.monotonic() - cached[0] < 10:
            return cached[1]

        async with self._lock:
            cached = self._cache
            if cached and time.monotonic() - cached[0] < 10:
                return cached[1]
            try:
                account = await self.adapter.get_account()
                snapshot = AccountSnapshot(
                    status="CONNECTED",
                    connected=True,
                    source="binance",
                    fetched_at=account.fetched_at,
                    stale=False,
                    note=(
                        f"{self.settings.mode.value} 只读账户快照"
                        f"（canTrade={account.can_trade}）"
                    ),
                    balances=tuple(
                        Balance(asset=item.asset, free=item.free, locked=item.locked)
                        for item in account.balances
                    ),
                )
                self._cache = (time.monotonic(), snapshot)
                return snapshot
            except BinanceError as exc:
                previous = cached[1] if cached else None
                snapshot = AccountSnapshot(
                    status="ERROR",
                    connected=False,
                    source="binance",
                    fetched_at=previous.fetched_at if previous else None,
                    stale=True,
                    note=f"账户读取失败：{exc}",
                    balances=previous.balances if previous else (),
                )
                self._cache = (time.monotonic(), snapshot)
                return snapshot

    @staticmethod
    def age_seconds(fetched_at: str | None) -> float | None:
        if not fetched_at:
            return None
        try:
            fetched = datetime.fromisoformat(fetched_at)
        except ValueError:
            return None
        if fetched.tzinfo is None:
            fetched = fetched.replace(tzinfo=timezone.utc)
        return max(0.0, time.time() - fetched.timestamp())
