"""Administrative controls: global pause, bulk cancel and audit read."""

from __future__ import annotations

import json
from typing import Any

from .config import Settings
from .db import Database, iso
from .errors import ApiException
from .orders import OPEN_STATUSES, OrderService
from .risk import RiskService


class AdminService:
    def __init__(
        self,
        db: Database,
        settings: Settings,
        risk: RiskService,
        orders: OrderService,
    ):
        self.db = db
        self.settings = settings
        self.risk = risk
        self.orders = orders

    def _set_flags(
        self,
        *,
        actor: str,
        paused: bool,
        reason: str,
        request_id: str,
        action: str,
    ) -> dict[str, object]:
        now = iso()
        values = {
            "pause_new_orders": "1" if paused else "0",
            "pause_reason": reason,
            "pause_updated_at": now,
            "pause_updated_by": actor,
        }
        with self.db.tx(immediate=True) as conn:
            for key, value in values.items():
                conn.execute(
                    "INSERT INTO system_flags(key, value, updated_at, updated_by)"
                    " VALUES (?, ?, ?, ?)"
                    " ON CONFLICT(key) DO UPDATE SET value = excluded.value,"
                    " updated_at = excluded.updated_at, updated_by = excluded.updated_by",
                    (key, value, now, actor),
                )
            self.db.log_audit(
                conn,
                action=action,
                mode=self.settings.mode.value,
                actor=actor,
                request_id=request_id,
                entity_type="system_flag",
                entity_id="pause_new_orders",
                detail={"paused": paused, "reason": reason},
            )
        return self.risk.flag_state()

    def pause(self, *, actor: str, reason: str, request_id: str) -> dict[str, object]:
        if not reason.strip():
            raise ApiException(422, "reason_required", "暂停新订单必须填写原因")
        return self._set_flags(
            actor=actor,
            paused=True,
            reason=reason.strip(),
            request_id=request_id,
            action="admin.pause_new_orders",
        )

    def resume(self, *, actor: str, reason: str, request_id: str) -> dict[str, object]:
        if not reason.strip():
            raise ApiException(422, "reason_required", "恢复新订单必须填写原因")
        return self._set_flags(
            actor=actor,
            paused=False,
            reason=reason.strip(),
            request_id=request_id,
            action="admin.resume_new_orders",
        )

    async def cancel_open_orders(
        self,
        *,
        actor: str,
        confirm: bool,
        reason: str,
        request_id: str,
    ) -> dict[str, Any]:
        if not confirm:
            raise ApiException(
                422,
                "confirmation_required",
                "撤单是不可逆操作，请在请求中明确 confirm=true",
            )
        rows = self.db.query_all(
            "SELECT id, username FROM orders WHERE mode = ? AND status IN (?, ?, ?)"
            " ORDER BY created_at",
            (self.settings.mode.value, *OPEN_STATUSES),
        )
        canceled = 0
        failed: list[dict[str, str]] = []
        for row in rows:
            try:
                await self.orders.cancel(
                    username=str(row["username"]),
                    order_id=str(row["id"]),
                    request_id=request_id,
                )
                canceled += 1
            except ApiException as exc:
                failed.append(
                    {"order_id": str(row["id"]), "code": exc.code, "message": exc.message}
                )
        with self.db.tx() as conn:
            self.db.log_audit(
                conn,
                action="admin.cancel_open_orders",
                mode=self.settings.mode.value,
                actor=actor,
                request_id=request_id,
                detail={
                    "confirm": confirm,
                    "reason": reason,
                    "canceled": canceled,
                    "failed": failed,
                    "scope": "open orders only; filled positions unchanged",
                },
            )
        return {
            "ok": not failed,
            "canceled": canceled,
            "failed": failed,
            "message": (
                f"已撤销 {canceled} 笔未成交订单；已成交仓位不会被自动平掉"
                if not failed
                else f"已撤销 {canceled} 笔，{len(failed)} 笔失败，请逐笔核对"
            ),
        }

    def audit_events(self, limit: int = 100) -> list[dict[str, Any]]:
        limit = max(1, min(limit, 500))
        rows = self.db.query_all(
            "SELECT id, ts, actor, action, mode, request_id, entity_type, entity_id,"
            " detail_json FROM audit_events ORDER BY id DESC LIMIT ?",
            (limit,),
        )
        events: list[dict[str, Any]] = []
        for row in rows:
            try:
                detail = json.loads(str(row["detail_json"]))
            except ValueError:
                detail = {}
            events.append(
                {
                    "id": int(row["id"]),
                    "ts": str(row["ts"]),
                    "actor": row["actor"],
                    "action": str(row["action"]),
                    "mode": str(row["mode"]),
                    "request_id": row["request_id"],
                    "entity_type": row["entity_type"],
                    "entity_id": row["entity_id"],
                    "detail": detail,
                }
            )
        return events
