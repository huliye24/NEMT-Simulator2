"""
API Module - API 模块

提供 API 版本管理和路由功能。
"""

from nemt.api.versioning import (
    APICompatibility,
    APIVersion,
    BreakingChange,
    DeprecationInfo,
    FieldMapper,
    ResponseTransformer,
    VersionedEndpoint,
    VersioningStrategy,
    VersionRouter,
    add_deprecation_headers,
)

__all__ = [
    "APIVersion",
    "VersioningStrategy",
    "APICompatibility",
    "VersionRouter",
    "DeprecationInfo",
    "BreakingChange",
    "VersionedEndpoint",
    "ResponseTransformer",
    "FieldMapper",
    "add_deprecation_headers",
]
