"""
TenantContext - 多租户上下文

提供多租户隔离和上下文传播能力。
"""

import logging
import threading
from contextvars import ContextVar
from typing import Any

__all__ = [
    "TenantContext",
    "TenantInfo",
    "TenantManager",
]


class TenantInfo:
    """租户信息"""

    def __init__(
        self,
        tenant_id: str,
        name: str,
        plan: str = "basic",
        quota: dict[str, Any] = None,
        metadata: dict[str, Any] = None,
    ):
        self.tenant_id = tenant_id
        self.name = name
        self.plan = plan
        self.quota = quota or {}
        self.metadata = metadata or {}

    def get_quota(self, resource: str) -> int | None:
        """获取资源配额"""
        return self.quota.get(resource)

    def to_dict(self) -> dict:
        return {
            "tenant_id": self.tenant_id,
            "name": self.name,
            "plan": self.plan,
            "quota": self.quota,
            "metadata": self.metadata,
        }


class TenantContext:
    """
    租户上下文

    示例:
    ```python
    # 设置当前租户
    TenantContext.set(tenant_id="tenant-123")

    # 在代码中获取当前租户
    tenant_id = TenantContext.get().tenant_id

    # 使用上下文管理器
    with TenantContext(tenant_id="tenant-456"):
        # 这里使用 tenant-456
        pass
    ```
    """

    _context: ContextVar[TenantInfo | None] = ContextVar("tenant_context", default=None)

    @classmethod
    def set(cls, tenant_info: TenantInfo) -> None:
        """设置当前租户"""
        cls._context.set(tenant_info)

    @classmethod
    def get(cls) -> TenantInfo | None:
        """获取当前租户"""
        return cls._context.get()

    @classmethod
    def get_tenant_id(cls) -> str | None:
        """获取当前租户 ID"""
        info = cls.get()
        return info.tenant_id if info else None

    @classmethod
    def clear(cls) -> None:
        """清除租户上下文"""
        cls._context.set(None)

    @classmethod
    def __enter__(cls):
        return cls

    @classmethod
    def __exit__(cls, exc_type, exc_val, exc_tb):
        cls.clear()


class TenantManager:
    """
    租户管理器

    示例:
    ```python
    manager = TenantManager()

    # 创建租户
    manager.create_tenant("tenant-1", "Company A", plan="pro")

    # 获取租户
    tenant = manager.get_tenant("tenant-1")

    # 切换租户上下文
    with manager.set_context("tenant-1"):
        # 这里使用 tenant-1
        pass
    ```
    """

    def __init__(self):
        self._tenants: dict[str, TenantInfo] = {}
        self._lock = threading.RLock()
        self._logger = logging.getLogger("TenantManager")

    def create_tenant(
        self,
        tenant_id: str,
        name: str,
        plan: str = "basic",
        quota: dict[str, Any] = None,
        metadata: dict[str, Any] = None,
    ) -> TenantInfo:
        """创建租户"""
        with self._lock:
            if tenant_id in self._tenants:
                raise ValueError(f"租户已存在: {tenant_id}")

            tenant = TenantInfo(
                tenant_id=tenant_id,
                name=name,
                plan=plan,
                quota=quota,
                metadata=metadata,
            )
            self._tenants[tenant_id] = tenant
            self._logger.info(f"创建租户: {name} ({tenant_id})")
            return tenant

    def get_tenant(self, tenant_id: str) -> TenantInfo | None:
        """获取租户"""
        return self._tenants.get(tenant_id)

    def update_tenant(self, tenant_id: str, **kwargs) -> bool:
        """更新租户"""
        tenant = self._tenants.get(tenant_id)
        if not tenant:
            return False

        for key, value in kwargs.items():
            if hasattr(tenant, key):
                setattr(tenant, key, value)
        return True

    def delete_tenant(self, tenant_id: str) -> bool:
        """删除租户"""
        with self._lock:
            if tenant_id in self._tenants:
                del self._tenants[tenant_id]
                return True
            return False

    def list_tenants(self, plan: str = None) -> list:
        """列出租户"""
        tenants = list(self._tenants.values())
        if plan:
            tenants = [t for t in tenants if t.plan == plan]
        return tenants

    def set_context(self, tenant_id: str):
        """设置租户上下文（返回上下文管理器）"""
        tenant = self.get_tenant(tenant_id)
        if not tenant:
            raise ValueError(f"租户不存在: {tenant_id}")
        return TenantContextManager(tenant)

    def check_quota(self, tenant_id: str, resource: str, current_usage: int) -> bool:
        """检查配额"""
        tenant = self.get_tenant(tenant_id)
        if not tenant:
            return False

        quota = tenant.get_quota(resource)
        if quota is None:
            return True  # 无配额限制

        return current_usage < quota


class TenantContextManager:
    """租户上下文管理器"""

    def __init__(self, tenant: TenantInfo):
        self._tenant = tenant
        self._previous: TenantInfo | None = None

    def __enter__(self):
        self._previous = TenantContext.get()
        TenantContext.set(self._tenant)
        return self._tenant

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._previous is None:
            TenantContext.clear()
        else:
            TenantContext.set(self._previous)


# 全局实例
_tenant_manager: TenantManager | None = None


def get_tenant_manager() -> TenantManager:
    """获取全局租户管理器"""
    global _tenant_manager
    if _tenant_manager is None:
        _tenant_manager = TenantManager()
    return _tenant_manager
