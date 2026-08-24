"""
SecretManager - 密钥管理

提供密钥的安全存储、访问控制和应用。
"""

import base64
import hashlib
import hmac
import logging
import os
import secrets
import threading

__all__ = [
    "SecretManager",
    "SecretScope",
]


class SecretScope(Enum):
    """密钥作用域"""

    GLOBAL = "global"
    ENVIRONMENT = "environment"
    TENANT = "tenant"
    USER = "user"


class SecretManager:
    """
    密钥管理器

    示例:
    ```python
    manager = SecretManager()

    # 存储密钥
    manager.set("api_key", "secret123", scope=SecretScope.GLOBAL)

    # 获取密钥
    api_key = manager.get("api_key")

    # 使用密钥
    signed = manager.sign("data")
    verified = manager.verify("data", signed)
    ```
    """

    def __init__(self, master_key: str = None):
        self._secrets: dict[str, dict] = {}
        self._master_key = master_key or os.environ.get("NEMT_MASTER_KEY", secrets.token_hex(32))
        self._lock = threading.RLock()
        self._logger = logging.getLogger("SecretManager")

    def set(self, key: str, value: str, scope: SecretScope = SecretScope.GLOBAL, metadata: dict = None) -> None:
        """存储密钥"""
        with self._lock:
            encrypted_value = self._encrypt(value)
            self._secrets[key] = {
                "value": encrypted_value,
                "scope": scope,
                "metadata": metadata or {},
            }
            self._logger.info(f"密钥已存储: {key} [{scope.value}]")

    def get(self, key: str, scope: SecretScope = None) -> str | None:
        """获取密钥"""
        with self._lock:
            entry = self._secrets.get(key)
            if entry is None:
                return None

            if scope and entry["scope"] != scope:
                return None

            return self._decrypt(entry["value"])

    def delete(self, key: str) -> bool:
        """删除密钥"""
        with self._lock:
            if key in self._secrets:
                del self._secrets[key]
                self._logger.info(f"密钥已删除: {key}")
                return True
            return False

    def list_keys(self, scope: SecretScope = None) -> list[str]:
        """列出密钥名称"""
        with self._lock:
            if scope:
                return [k for k, v in self._secrets.items() if v["scope"] == scope]
            return list(self._secrets.keys())

    def exists(self, key: str) -> bool:
        """检查密钥是否存在"""
        return key in self._secrets

    def sign(self, data: str) -> str:
        """签名数据"""
        key_bytes = self._master_key.encode()
        data_bytes = data.encode()
        signature = hmac.new(key_bytes, data_bytes, hashlib.sha256).digest()
        return base64.b64encode(signature).decode()

    def verify(self, data: str, signature: str) -> bool:
        """验证签名"""
        expected = self.sign(data)
        return hmac.compare_digest(expected, signature)

    def _encrypt(self, value: str) -> str:
        """加密值（简化实现，实际应使用更强的加密）"""
        key_bytes = self._master_key.encode()
        value_bytes = value.encode()
        encrypted = bytearray()
        for i, b in enumerate(value_bytes):
            encrypted.append(b ^ key_bytes[i % len(key_bytes)])
        return base64.b64encode(bytes(encrypted)).decode()

    def _decrypt(self, encrypted: str) -> str:
        """解密值"""
        key_bytes = self._master_key.encode()
        encrypted_bytes = base64.b64decode(encrypted)
        decrypted = bytearray()
        for i, b in enumerate(encrypted_bytes):
            decrypted.append(b ^ key_bytes[i % len(key_bytes)])
        return bytes(decrypted).decode()




# 全局实例
_secret_manager: SecretManager | None = None


def get_secret_manager() -> SecretManager:
    """获取全局密钥管理器"""
    global _secret_manager
    if _secret_manager is None:
        _secret_manager = SecretManager()
    return _secret_manager
