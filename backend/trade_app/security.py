"""Small, dependency-free security helpers.

Only opaque session tokens and password hashes are persisted. API keys,
passwords and raw tokens are never written to audit logs.
"""

from __future__ import annotations

import hashlib
import hmac
import secrets
from typing import Any

PBKDF2_ITERATIONS = 260_000
SESSION_TOKEN_BYTES = 32


def hash_password(password: str, *, salt: bytes | None = None) -> str:
    salt = salt or secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS
    )
    return f"pbkdf2_sha256${PBKDF2_ITERATIONS}${salt.hex()}${digest.hex()}"


def verify_password(password: str, encoded: str) -> bool:
    try:
        algorithm, iterations, salt_hex, digest_hex = encoded.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        expected = bytes.fromhex(digest_hex)
        actual = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), bytes.fromhex(salt_hex), int(iterations)
        )
    except (ValueError, TypeError):
        return False
    return hmac.compare_digest(actual, expected)


def new_token() -> str:
    return secrets.token_urlsafe(SESSION_TOKEN_BYTES)


def token_hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def constant_time_equals(left: str, right: str) -> bool:
    return hmac.compare_digest(left.encode("utf-8"), right.encode("utf-8"))


def new_order_id() -> str:
    return f"ord_{secrets.token_hex(10)}"


def client_order_id_for(username: str, idempotency_key: str) -> str:
    """Stable venue id so a retried request cannot create a second order."""

    material = f"{username}:{idempotency_key}".encode("utf-8")
    return "nemt_" + hashlib.sha256(material).hexdigest()[:28]


_REDACT_KEYS = {
    "password",
    "secret",
    "api_key",
    "apikey",
    "signature",
    "token",
    "authorization",
    "cookie",
    "session",
    "csrf",
    "confirmation_token",
}


def redact(value: Any) -> Any:
    """Recursively redact credential-like fields before persistence/logging."""

    if isinstance(value, dict):
        redacted: dict[str, Any] = {}
        for key, item in value.items():
            if any(part in key.lower() for part in _REDACT_KEYS):
                redacted[key] = "[REDACTED]"
            else:
                redacted[key] = redact(item)
        return redacted
    if isinstance(value, (list, tuple)):
        return [redact(item) for item in value]
    return value
