"""
PermissionManager - 权限管理

提供基于角色的访问控制 (RBAC) 能力。
"""

import logging
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum

__all__ = [
    "Permission",
    "Role",
    "User",
    "PermissionManager",
]


class Permission(Enum):
    """权限枚举"""

    # 资源权限
    RESOURCE_CREATE = "resource:create"
    RESOURCE_READ = "resource:read"
    RESOURCE_UPDATE = "resource:update"
    RESOURCE_DELETE = "resource:delete"

    # 策略权限
    STRATEGY_CREATE = "strategy:create"
    STRATEGY_EDIT = "strategy:edit"
    STRATEGY_DELETE = "strategy:delete"
    STRATEGY_EXECUTE = "strategy:execute"

    # 用户权限
    USER_CREATE = "user:create"
    USER_MANAGE = "user:manage"
    USER_DELETE = "user:delete"

    # 管理员权限
    ADMIN_ALL = "admin:all"
    ADMIN_CONFIG = "admin:config"
    ADMIN_AUDIT = "admin:audit"


@dataclass
class Role:
    """角色"""

    role_id: str
    name: str
    description: str = ""
    permissions: set[str] = field(default_factory=set)
    parent_role: str = None  # 继承的角色
    created_at: float = field(default_factory=time.time)

    def has_permission(self, permission: str) -> bool:
        """检查权限"""
        if permission in self.permissions:
            return True
        if self.parent_role:
            # 委托给角色管理器检查父角色
            return False
        return False


@dataclass
class User:
    """用户"""

    user_id: str
    username: str
    email: str = ""
    roles: set[str] = field(default_factory=set)
    direct_permissions: set[str] = field(default_factory=set)
    is_active: bool = True
    metadata: dict = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)


class PermissionManager:
    """
    权限管理器

    示例:
    ```python
    pm = PermissionManager()

    # 创建角色
    pm.create_role("admin", "Administrator", {
        Permission.ADMIN_ALL,
        Permission.USER_MANAGE,
    })

    pm.create_role("trader", "Trader", {
        Permission.STRATEGY_READ,
        Permission.STRATEGY_EXECUTE,
    })

    # 创建用户
    pm.create_user("user1", "trader")

    # 检查权限
    if pm.has_permission("user1", Permission.STRATEGY_EXECUTE):
        execute_strategy()
    ```
    """

    def __init__(self):
        self._roles: dict[str, Role] = {}
        self._users: dict[str, User] = {}
        self._lock = threading.RLock()
        self._logger = logging.getLogger("PermissionManager")

        # 创建默认角色
        self._init_default_roles()

    def _init_default_roles(self) -> None:
        """初始化默认角色"""
        # 超级管理员
        self.create_role(
            "super_admin",
            "Super Administrator",
            {p.value for p in Permission},
            description="Full system access",
        )

        # 管理员
        self.create_role(
            "admin",
            "Administrator",
            {
                Permission.ADMIN_CONFIG.value,
                Permission.ADMIN_AUDIT.value,
                Permission.USER_CREATE.value,
                Permission.USER_MANAGE.value,
                Permission.RESOURCE_CREATE.value,
                Permission.RESOURCE_READ.value,
                Permission.RESOURCE_UPDATE.value,
                Permission.RESOURCE_DELETE.value,
            },
            description="System administration",
        )

        # 操作员
        self.create_role(
            "operator",
            "Operator",
            {
                Permission.RESOURCE_CREATE.value,
                Permission.RESOURCE_READ.value,
                Permission.RESOURCE_UPDATE.value,
            },
            description="Regular operations",
        )

        # 只读用户
        self.create_role(
            "readonly",
            "Read Only",
            {Permission.RESOURCE_READ.value},
            description="Read only access",
        )

    def create_role(
        self,
        role_id: str,
        name: str,
        permissions: set[str] = None,
        parent_role: str = None,
        description: str = "",
    ) -> Role:
        """创建角色"""
        with self._lock:
            role = Role(
                role_id=role_id,
                name=name,
                description=description,
                permissions=permissions or set(),
                parent_role=parent_role,
            )
            self._roles[role_id] = role
            self._logger.info(f"创建角色: {name}")
            return role

    def get_role(self, role_id: str) -> Role | None:
        """获取角色"""
        return self._roles.get(role_id)

    def delete_role(self, role_id: str) -> bool:
        """删除角色"""
        with self._lock:
            if role_id in self._roles:
                del self._roles[role_id]
                return True
            return False

    def add_permission_to_role(self, role_id: str, permission: str) -> bool:
        """添加权限到角色"""
        role = self.get_role(role_id)
        if role:
            role.permissions.add(permission)
            return True
        return False

    def remove_permission_from_role(self, role_id: str, permission: str) -> bool:
        """从角色移除权限"""
        role = self.get_role(role_id)
        if role and permission in role.permissions:
            role.permissions.remove(permission)
            return True
        return False

    def create_user(
        self,
        user_id: str,
        username: str,
        email: str = "",
        roles: set[str] = None,
    ) -> User:
        """创建用户"""
        with self._lock:
            user = User(
                user_id=user_id,
                username=username,
                email=email,
                roles=roles or set(),
            )
            self._users[user_id] = user
            self._logger.info(f"创建用户: {username}")
            return user

    def get_user(self, user_id: str) -> User | None:
        """获取用户"""
        return self._users.get(user_id)

    def delete_user(self, user_id: str) -> bool:
        """删除用户"""
        with self._lock:
            if user_id in self._users:
                del self._users[user_id]
                return True
            return False

    def assign_role(self, user_id: str, role_id: str) -> bool:
        """分配角色给用户"""
        user = self.get_user(user_id)
        role = self.get_role(role_id)
        if user and role:
            user.roles.add(role_id)
            return True
        return False

    def revoke_role(self, user_id: str, role_id: str) -> bool:
        """撤销用户角色"""
        user = self.get_user(user_id)
        if user and role_id in user.roles:
            user.roles.remove(role_id)
            return True
        return False

    def grant_permission(self, user_id: str, permission: str) -> bool:
        """直接授权"""
        user = self.get_user(user_id)
        if user:
            user.direct_permissions.add(permission)
            return True
        return False

    def revoke_permission(self, user_id: str, permission: str) -> bool:
        """直接撤销权限"""
        user = self.get_user(user_id)
        if user and permission in user.direct_permissions:
            user.direct_permissions.remove(permission)
            return True
        return False

    def has_permission(self, user_id: str, permission: str) -> bool:
        """检查用户权限"""
        user = self.get_user(user_id)
        if not user:
            return False

        if not user.is_active:
            return False

        # 检查直接权限
        if permission in user.direct_permissions:
            return True

        # 检查角色权限
        for role_id in user.roles:
            role = self.get_role(role_id)
            if role and permission in role.permissions:
                return True

            # 检查父角色
            if role and role.parent_role:
                parent = self.get_role(role.parent_role)
                if parent and permission in parent.permissions:
                    return True

        return False

    def get_user_permissions(self, user_id: str) -> set[str]:
        """获取用户所有权限"""
        user = self.get_user(user_id)
        if not user:
            return set()

        permissions = set(user.direct_permissions)

        for role_id in user.roles:
            role = self.get_role(role_id)
            if role:
                permissions.update(role.permissions)

        return permissions

    def check_permission(self, permission: str) -> Callable:
        """装饰器：权限检查"""

        def decorator(func: Callable) -> Callable:
            def wrapper(user_id: str, *args, **kwargs):
                if self.has_permission(user_id, permission):
                    return func(user_id, *args, **kwargs)
                else:
                    raise PermissionError(f"Permission denied: {permission}")

            return wrapper

        return decorator


# 全局实例
_permission_manager: PermissionManager | None = None


def get_permission_manager() -> PermissionManager:
    """获取全局权限管理器"""
    global _permission_manager
    if _permission_manager is None:
        _permission_manager = PermissionManager()
    return _permission_manager
