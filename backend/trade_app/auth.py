"""Password authentication, opaque server-side sessions and RBAC."""

from __future__ import annotations

import time
from collections import defaultdict, deque
from dataclasses import dataclass

from .config import Settings
from .db import Database, iso, iso_after, parse_iso, utc_now
from .security import (
    constant_time_equals,
    new_token,
    token_hash,
    verify_password,
)

ROLE_RANK = {"viewer": 1, "trader": 2, "admin": 3}
LOGIN_WINDOW_SECONDS = 60
LOGIN_MAX_ATTEMPTS = 5


@dataclass(frozen=True)
class AuthUser:
    username: str
    roles: tuple[str, ...]

    def has_role(self, required: str) -> bool:
        required_rank = ROLE_RANK.get(required, 999)
        return any(ROLE_RANK.get(role, 0) >= required_rank for role in self.roles)


@dataclass(frozen=True)
class SessionContext:
    user: AuthUser
    token: str
    csrf_token: str
    expires_at: str


class AuthService:
    def __init__(self, db: Database, settings: Settings):
        self.db = db
        self.settings = settings
        self._attempts: dict[str, deque[float]] = defaultdict(deque)

    def _rate_limit_key(self, username: str, client_ip: str) -> str:
        return f"{client_ip}:{username.lower()}"

    def _check_rate_limit(self, key: str) -> None:
        now = time.monotonic()
        attempts = self._attempts[key]
        while attempts and now - attempts[0] > LOGIN_WINDOW_SECONDS:
            attempts.popleft()
        if len(attempts) >= LOGIN_MAX_ATTEMPTS:
            raise PermissionError("Too many login attempts. Try again later.")

    def _record_failure(self, key: str) -> None:
        self._attempts[key].append(time.monotonic())

    def _clear_failures(self, key: str) -> None:
        self._attempts.pop(key, None)

    def _load_user(self, username: str) -> tuple[AuthUser, str] | None:
        row = self.db.query_one(
            "SELECT username, password_hash, roles, enabled FROM users WHERE username = ?",
            (username,),
        )
        if row is None or not bool(row["enabled"]):
            return None
        roles = tuple(role for role in str(row["roles"]).split(",") if role)
        return AuthUser(username=str(row["username"]), roles=roles), str(row["password_hash"])

    def login(
        self,
        username: str,
        password: str,
        *,
        client_ip: str,
        request_id: str | None = None,
    ) -> SessionContext:
        username = username.strip()
        key = self._rate_limit_key(username, client_ip)
        try:
            self._check_rate_limit(key)
        except PermissionError:
            with self.db.tx() as conn:
                self.db.log_audit(
                    conn,
                    action="auth.login.rate_limited",
                    mode=self.settings.mode.value,
                    actor=username,
                    request_id=request_id,
                )
            raise

        loaded = self._load_user(username)
        valid = loaded is not None and verify_password(password, loaded[1])
        if not valid or loaded is None:
            self._record_failure(key)
            with self.db.tx() as conn:
                self.db.log_audit(
                    conn,
                    action="auth.login.failure",
                    mode=self.settings.mode.value,
                    actor=username,
                    request_id=request_id,
                )
            raise ValueError("Invalid username or password")

        self._clear_failures(key)
        session = self._create_session(loaded[0], request_id=request_id)
        with self.db.tx() as conn:
            self.db.log_audit(
                conn,
                action="auth.login.success",
                mode=self.settings.mode.value,
                actor=loaded[0].username,
                request_id=request_id,
            )
        return session

    def demo_login(
        self,
        account: str,
        *,
        request_id: str | None = None,
    ) -> SessionContext:
        """Local DEMO convenience. Never available outside DEMO mode."""

        if not self.settings.is_demo:
            raise PermissionError("Demo login is only available in DEMO mode")
        username = account if account in {"viewer", "demo", "admin"} else "demo"
        loaded = self._load_user(username)
        if loaded is None:
            raise ValueError("Demo account is not seeded")
        session = self._create_session(loaded[0], request_id=request_id)
        with self.db.tx() as conn:
            self.db.log_audit(
                conn,
                action="auth.demo_login",
                mode=self.settings.mode.value,
                actor=loaded[0].username,
                request_id=request_id,
            )
        return session

    def _create_session(
        self, user: AuthUser, *, request_id: str | None = None
    ) -> SessionContext:
        token = new_token()
        csrf = new_token()
        expires_at = iso_after(self.settings.session_ttl_seconds)
        now = iso()
        with self.db.tx() as conn:
            # Opportunistic cleanup keeps the table bounded without a worker.
            conn.execute("DELETE FROM sessions WHERE expires_at < ?", (now,))
            conn.execute(
                "INSERT INTO sessions(token_hash, username, csrf_token, created_at,"
                " expires_at, last_seen_at) VALUES (?, ?, ?, ?, ?, ?)",
                (token_hash(token), user.username, csrf, now, expires_at, now),
            )
        return SessionContext(
            user=user,
            token=token,
            csrf_token=csrf,
            expires_at=expires_at,
        )

    def authenticate(self, token: str | None) -> SessionContext | None:
        if not token:
            return None
        row = self.db.query_one(
            "SELECT s.token_hash, s.username, s.csrf_token, s.expires_at,"
            " s.last_seen_at, u.roles, u.enabled"
            " FROM sessions s JOIN users u ON u.username = s.username"
            " WHERE s.token_hash = ?",
            (token_hash(token),),
        )
        if row is None or not bool(row["enabled"]):
            return None
        expires_at = parse_iso(str(row["expires_at"]))
        if expires_at is None or expires_at <= utc_now():
            with self.db.tx() as conn:
                conn.execute("DELETE FROM sessions WHERE token_hash = ?", (token_hash(token),))
            return None

        roles = tuple(role for role in str(row["roles"]).split(",") if role)
        user = AuthUser(username=str(row["username"]), roles=roles)
        last_seen = parse_iso(str(row["last_seen_at"]))
        if last_seen is None or (utc_now() - last_seen).total_seconds() > 60:
            with self.db.tx() as conn:
                conn.execute(
                    "UPDATE sessions SET last_seen_at = ? WHERE token_hash = ?",
                    (iso(), token_hash(token)),
                )
        return SessionContext(
            user=user,
            token=token,
            csrf_token=str(row["csrf_token"]),
            expires_at=str(row["expires_at"]),
        )

    def logout(self, session: SessionContext, *, request_id: str | None = None) -> None:
        with self.db.tx() as conn:
            conn.execute(
                "DELETE FROM sessions WHERE token_hash = ?", (token_hash(session.token),)
            )
            self.db.log_audit(
                conn,
                action="auth.logout",
                mode=self.settings.mode.value,
                actor=session.user.username,
                request_id=request_id,
            )

    @staticmethod
    def verify_csrf(expected: str, provided: str | None) -> bool:
        return bool(provided) and constant_time_equals(expected, provided or "")
