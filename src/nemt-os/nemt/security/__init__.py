"""
Security Module - 安全模块

提供密钥管理、审计日志、权限管理和多租户能力。
"""

from nemt.security.audit import (
    AuditAction,
    AuditEvent,
    AuditLogger,
    get_audit_logger,
)
from nemt.security.permission import (
    Permission,
    PermissionManager,
    Role,
    User,
    get_permission_manager,
)
from nemt.security.secret_manager import (
    SecretManager,
    SecretScope,
    get_secret_manager,
)
from nemt.security.tenant import (
    TenantContext,
    TenantInfo,
    TenantManager,
    get_tenant_manager,
)

__all__ = [
    # 密钥管理
    "SecretManager",
    "SecretScope",
    "get_secret_manager",
    # 审计日志
    "AuditEvent",
    "AuditAction",
    "AuditLogger",
    "get_audit_logger",
    # 权限管理
    "Permission",
    "Role",
    "User",
    "PermissionManager",
    "get_permission_manager",
    # 多租户
    "TenantInfo",
    "TenantContext",
    "TenantManager",
    "get_tenant_manager",
]
