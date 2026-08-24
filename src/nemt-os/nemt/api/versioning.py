"""
API Versioning - API 版本管理

提供 API 版本管理和向后兼容支持。
"""

import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from functools import wraps

__all__ = [
    "APIVersion",
    "VersioningStrategy",
    "APICompatibility",
    "VersionRouter",
    "DeprecationInfo",
]


class APIVersion(Enum):
    """API 版本"""

    V1 = "v1"
    V2 = "v2"
    V3 = "v3"


class VersioningStrategy(Enum):
    """版本控制策略"""

    HEADER = "header"  # X-API-Version header
    URL_PATH = "url_path"  # /api/v1/, /api/v2/
    QUERY_PARAM = "query"  # ?version=v1
    ACCEPT_HEADER = "accept"  # Accept: application/vnd.api+v1+json


class BreakingChange(Enum):
    """破坏性变更类型"""

    NONE = "none"
    FIELD_REMOVED = "field_removed"
    FIELD_RENAMED = "field_renamed"
    FIELD_TYPE_CHANGED = "field_type_changed"
    BEHAVIOR_CHANGED = "behavior_changed"
    REQUIRED_ADDED = "required_added"
    VALIDATION_STRICTER = "validation_stricter"


@dataclass
class DeprecationInfo:
    """废弃信息"""

    deprecated_since: str  # 废弃版本
    will_be_removed: str  # 将移除版本
    alternative: str  # 替代方案
    migration_guide: str  # 迁移指南


@dataclass
class APICompatibility:
    """API 兼容性信息"""

    version: APIVersion
    previous_version: APIVersion | None
    breaking_changes: list[BreakingChange] = field(default_factory=list)
    deprecated_fields: dict[str, DeprecationInfo] = field(default_factory=dict)
    new_fields: list[str] = field(default_factory=list)


@dataclass
class VersionedEndpoint:
    """版本化端点"""

    path: str
    method: str
    version: APIVersion
    handler: Callable
    deprecated: bool = False
    deprecation_info: DeprecationInfo = None
    compatibility: APICompatibility = None


class VersionRouter:
    """
    API 版本路由器

    示例:
    ```python
    router = VersionRouter(strategy=VersioningStrategy.URL_PATH)

    @router.route("/api/market", "GET", version=APIVersion.V1)
    def get_market_v1():
        pass

    @router.route("/api/market", "GET", version=APIVersion.V2)
    def get_market_v2():
        pass

    # 自动路由
    result = router.route_request("/api/market", "GET", headers={})
    ```
    """

    def __init__(self, strategy: VersioningStrategy = VersioningStrategy.URL_PATH):
        self.strategy = strategy
        self._endpoints: dict[tuple[str, str, APIVersion], VersionedEndpoint] = {}
        self._default_version = APIVersion.V1
        self._logger = logging.getLogger("VersionRouter")

    def route(
        self,
        path: str,
        method: str = "GET",
        version: APIVersion = None,
    ) -> Callable:
        """路由装饰器"""
        version = version or self._default_version

        def decorator(handler: Callable) -> Callable:
            endpoint = VersionedEndpoint(
                path=path,
                method=method,
                version=version,
                handler=handler,
            )
            self._endpoints[(path, method, version)] = endpoint

            @wraps(handler)
            def wrapper(*args, **kwargs):
                return handler(*args, **kwargs)

            return wrapper

        return decorator

    def deprecate(
        self,
        path: str,
        method: str,
        version: APIVersion,
        info: DeprecationInfo,
    ) -> None:
        """标记端点为废弃"""
        endpoint = self._endpoints.get((path, method, version))
        if endpoint:
            endpoint.deprecated = True
            endpoint.deprecation_info = info

    def route_request(
        self,
        path: str,
        method: str,
        headers: dict = None,
        query_params: dict = None,
    ) -> tuple[Callable | None, APIVersion, bool]:
        """
        路由请求到正确版本的处理程序

        Returns:
            (handler, version, is_deprecated)
        """
        headers = headers or {}
        query_params = query_params or {}

        # 获取请求版本
        request_version = self._get_version(headers, path, query_params)

        # 尝试精确匹配
        key = (path, method, request_version)
        if key in self._endpoints:
            endpoint = self._endpoints[key]
            return endpoint.handler, endpoint.version, endpoint.deprecated

        # 降级到默认版本
        if request_version != self._default_version:
            key = (path, method, self._default_version)
            if key in self._endpoints:
                endpoint = self._endpoints[key]
                self._logger.warning(f"版本 {request_version.value} 不可用，降级到 {self._default_version.value}")
                return endpoint.handler, endpoint.version, True

        return None, request_version, False

    def _get_version(
        self,
        headers: dict,
        path: str,
        query_params: dict,
    ) -> APIVersion:
        """根据策略获取版本"""
        if self.strategy == VersioningStrategy.HEADER:
            version_str = headers.get("X-API-Version", "v1")
            return APIVersion(version_str)

        elif self.strategy == VersioningStrategy.URL_PATH:
            parts = path.split("/")
            for part in parts:
                if part.startswith("v") and part[1:].isdigit():
                    return APIVersion(part)
            return self._default_version

        elif self.strategy == VersioningStrategy.QUERY_PARAM:
            version_str = query_params.get("version", "v1")
            return APIVersion(version_str)

        elif self.strategy == VersioningStrategy.ACCEPT_HEADER:
            accept = headers.get("Accept", "")
            if "v2" in accept:
                return APIVersion.V2
            elif "v3" in accept:
                return APIVersion.V3
            return self._default_version

        return self._default_version

    def get_versions(self, path: str, method: str) -> list[APIVersion]:
        """获取端点支持的所有版本"""
        versions = []
        for (p, m, v), _ in self._endpoints.items():
            if p == path and m == method:
                versions.append(v)
        return sorted(versions, key=lambda x: x.value)

    def get_deprecated_endpoints(self) -> list[VersionedEndpoint]:
        """获取所有废弃端点"""
        return [ep for ep in self._endpoints.values() if ep.deprecated]


class ResponseTransformer:
    """
    响应转换器

    处理 API 版本间的响应转换。

    示例:
    ```python
    transformer = ResponseTransformer()

    # 注册转换规则
    transformer.register(
        from_version=APIVersion.V1,
        to_version=APIVersion.V2,
        transform=lambda data: {
            **data,
            "new_field": data.pop("old_field"),
        }
    )

    # 转换响应
    transformed = transformer.transform(response, from_version=APIVersion.V1, to_version=APIVersion.V2)
    ```
    """

    def __init__(self):
        self._transforms: dict[tuple[APIVersion, APIVersion], Callable] = {}

    def register(
        self,
        from_version: APIVersion,
        to_version: APIVersion,
        transform: Callable[[dict], dict],
    ) -> None:
        """注册转换规则"""
        self._transforms[(from_version, to_version)] = transform

    def transform(
        self,
        data: dict,
        from_version: APIVersion,
        to_version: APIVersion,
    ) -> dict:
        """转换响应数据"""
        if from_version == to_version:
            return data

        key = (from_version, to_version)
        if key in self._transforms:
            return self._transforms[key](data)

        # 尝试链式转换
        # V1 -> V3 = V1 -> V2 -> V3
        for mid_version in APIVersion:
            if mid_version != from_version and mid_version != to_version:
                if (from_version, mid_version) in self._transforms and (mid_version, to_version) in self._transforms:
                    intermediate = self._transforms[(from_version, mid_version)](data)
                    return self._transforms[(mid_version, to_version)](intermediate)

        return data


# 字段映射器
class FieldMapper:
    """字段映射器"""

    def __init__(self):
        self._mappings: dict[tuple[APIVersion, APIVersion], dict[str, str]] = {}

    def register_mapping(
        self,
        from_version: APIVersion,
        to_version: APIVersion,
        mappings: dict[str, str],
    ) -> None:
        """注册字段映射"""
        self._mappings[(from_version, to_version)] = mappings

    def map_fields(
        self,
        data: dict,
        from_version: APIVersion,
        to_version: APIVersion,
    ) -> dict:
        """映射字段"""
        if from_version == to_version:
            return data

        key = (from_version, to_version)
        mappings = self._mappings.get(key, {})

        result = {}
        for field_name, value in data.items():
            new_name = mappings.get(field_name, field_name)
            result[new_name] = value

        return result


# 便捷函数
def add_deprecation_headers(
    response: dict,
    deprecated_since: str,
    will_be_removed: str,
    alternative: str = None,
) -> dict:
    """添加废弃响应头"""
    response["headers"] = response.get("headers", {})
    response["headers"]["Deprecation"] = f'date="{deprecated_since}"'
    response["headers"]["Sunset"] = will_be_removed
    if alternative:
        response["headers"]["Link"] = f'<{alternative}>; rel="deprecation"'
    return response
