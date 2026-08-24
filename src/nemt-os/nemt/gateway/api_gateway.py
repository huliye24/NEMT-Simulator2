"""
APIGateway - API 网关核心

提供路由、限流、认证、缓存等 API 网关能力。
"""

import asyncio
import hashlib
import json
import logging
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from functools import wraps
from typing import Any

__all__ = [
    "APIResponse",
    "APIError",
    "HTTPMethod",
    "Route",
    "APIGateway",
]


class HTTPMethod(Enum):
    """HTTP 方法"""

    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"
    OPTIONS = "OPTIONS"
    HEAD = "HEAD"


@dataclass
class APIResponse:
    """
    API 统一响应格式

    示例:
    ```python
    # 成功响应
    return APIResponse.success({"user": "data"})

    # 错误响应
    return APIResponse.error("Invalid input", code=400)

    # 分页响应
    return APIResponse.paginate(items, total=100, page=1, size=10)
    ```
    """

    success: bool
    data: Any = None
    error: str = ""
    code: int = 200
    message: str = ""
    timestamp: float = field(default_factory=time.time)
    request_id: str = ""

    @classmethod
    def success(cls, data: Any = None, message: str = "Success") -> "APIResponse":
        return cls(success=True, data=data, message=message, code=200)

    @classmethod
    def error(
        cls,
        message: str,
        code: int = 500,
        error: str = None,
    ) -> "APIResponse":
        return cls(
            success=False,
            error=error or message,
            message=message,
            code=code,
        )

    @classmethod
    def paginate(
        cls,
        items: list,
        total: int,
        page: int = 1,
        size: int = 20,
        message: str = "Success",
    ) -> "APIResponse":
        return cls(
            success=True,
            data={
                "items": items,
                "pagination": {
                    "total": total,
                    "page": page,
                    "size": size,
                    "pages": (total + size - 1) // size,
                },
            },
            message=message,
            code=200,
        )

    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "data": self.data,
            "error": self.error,
            "code": self.code,
            "message": self.message,
            "timestamp": self.timestamp,
            "request_id": self.request_id,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False)

    def __iter__(self):
        return iter(self.to_dict().items())


class APIError(Exception):
    """API 错误异常"""

    def __init__(
        self,
        message: str,
        code: int = 500,
        details: dict = None,
    ):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(message)


@dataclass
class Route:
    """路由定义"""

    path: str
    method: HTTPMethod
    handler: Callable
    middleware: list[Callable] = field(default_factory=list)
    auth_required: bool = False
    rate_limit: int = 0  # 每分钟请求数，0 表示不限
    cache_ttl: int = 0  # 缓存秒数，0 表示不缓存
    description: str = ""


class APIRateLimiter:
    """
    API 限流器

    示例:
    ```python
    limiter = APIRateLimiter(default_rate=100)

    # 按 IP 限流
    if not limiter.allow(client_ip):
        return 429 Too Many Requests

    # 按用户限流
    if not limiter.allow(user_id, key_type="user"):
        return 429
    ```
    """

    def __init__(self, default_rate: int = 100, window: float = 60.0):
        self.default_rate = default_rate
        self.window = window
        self._requests: dict[str, list[float]] = {}
        self._limits: dict[str, int] = {}
        self._lock = asyncio.Lock()

    async def allow(self, key: str, rate: int = None) -> bool:
        """检查是否允许请求"""
        rate = rate or self.default_rate
        now = time.time()

        async with self._lock:
            if key not in self._requests:
                self._requests[key] = []

            # 清理过期记录
            self._requests[key] = [t for t in self._requests[key] if now - t < self.window]

            # 检查是否超限
            if len(self._requests[key]) >= rate:
                return False

            # 记录请求
            self._requests[key].append(now)
            return True

    def set_limit(self, key: str, rate: int) -> None:
        """设置特定键的限流"""
        self._limits[key] = rate

    def get_remaining(self, key: str) -> int:
        """获取剩余请求数"""
        rate = self._limits.get(key, self.default_rate)
        count = len(self._requests.get(key, []))
        return max(0, rate - count)


class APICache:
    """
    API 缓存

    示例:
    ```python
    cache = APICache(default_ttl=300)

    # 尝试获取缓存
    cached = await cache.get("key")
    if cached:
        return cached

    # 设置缓存
    await cache.set("key", data, ttl=60)
    ```
    """

    def __init__(self, default_ttl: int = 300):
        self.default_ttl = default_ttl
        self._cache: dict[str, dict] = {}
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> Any | None:
        """获取缓存"""
        async with self._lock:
            if key not in self._cache:
                return None

            entry = self._cache[key]
            if time.time() > entry["expires_at"]:
                del self._cache[key]
                return None

            entry["hits"] += 1
            return entry["value"]

    async def set(self, key: str, value: Any, ttl: int = None) -> None:
        """设置缓存"""
        ttl = ttl or self.default_ttl
        async with self._lock:
            self._cache[key] = {
                "value": value,
                "expires_at": time.time() + ttl,
                "created_at": time.time(),
                "hits": 0,
            }

    async def delete(self, key: str) -> bool:
        """删除缓存"""
        async with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False

    async def clear(self) -> None:
        """清空缓存"""
        async with self._lock:
            self._cache.clear()

    def _generate_key(self, path: str, params: dict) -> str:
        """生成缓存键"""
        key_data = f"{path}:{json.dumps(params, sort_keys=True)}"
        return hashlib.md5(key_data.encode()).hexdigest()


class APIGateway:
    """
    API 网关

    示例:
    ```python
    gateway = APIGateway()

    # 注册路由
    @gateway.route("/users", HTTPMethod.GET)
    async def get_users(request):
        return APIResponse.success([...])

    @gateway.route("/users", HTTPMethod.POST)
    async def create_user(request):
        return APIResponse.success(user)

    # 添加中间件
    @gateway.middleware
    async def auth_middleware(request, handler):
        if not request.auth:
            return APIResponse.error("Unauthorized", code=401)
        return await handler(request)

    # 处理请求
    response = await gateway.handle(request)
    ```
    """

    def __init__(
        self,
        default_rate: int = 100,
        default_cache_ttl: int = 60,
    ):
        self._routes: dict[str, Route] = {}
        self._middleware: list[Callable] = []
        self._rate_limiter = APIRateLimiter(default_rate=default_rate)
        self._cache = APICache(default_ttl=default_cache_ttl)
        self._logger = logging.getLogger("APIGateway")

    def route(
        self,
        path: str,
        method: HTTPMethod = HTTPMethod.GET,
        auth_required: bool = False,
        rate_limit: int = 0,
        cache_ttl: int = 0,
        description: str = "",
    ) -> Callable:
        """装饰器：注册路由"""

        def decorator(func: Callable) -> Callable:
            route = Route(
                path=path,
                method=method,
                handler=func,
                auth_required=auth_required,
                rate_limit=rate_limit,
                cache_ttl=cache_ttl,
                description=description,
            )
            self._routes[f"{method.value}:{path}"] = route

            @wraps(func)
            async def wrapper(*args, **kwargs):
                return await func(*args, **kwargs)

            return wrapper

        return decorator

    def middleware(self, func: Callable) -> Callable:
        """装饰器：添加中间件"""
        self._middleware.append(func)
        return func

    async def handle(self, request: dict) -> APIResponse:
        """处理请求"""
        method = request.get("method", "GET")
        path = request.get("path", "/")
        client_ip = request.get("client_ip", "unknown")
        request_id = request.get("request_id", "")

        route_key = f"{method}:{path}"
        route = self._routes.get(route_key)

        if not route:
            return APIResponse.error(
                message="Not Found",
                code=404,
            )

        # 限流检查
        if route.rate_limit > 0:
            if not await self._rate_limiter.allow(client_ip, route.rate_limit):
                return APIResponse.error(
                    message="Rate limit exceeded",
                    code=429,
                )

        # 缓存检查 (GET 请求)
        if method == "GET" and route.cache_ttl > 0:
            cache_key = self._cache._generate_key(path, request.get("params", {}))
            cached = await self._cache.get(cache_key)
            if cached:
                response = APIResponse.success(cached)
                response.request_id = request_id
                return response

        # 执行中间件
        async def handler(req):
            return await route.handler(req)

        for mw in self._middleware:
            handler = lambda req, h=handler: mw(req, h)

        try:
            result = await handler(request)

            # 缓存结果
            if method == "GET" and route.cache_ttl > 0 and result.success:
                await self._cache.set(cache_key, result.data, route.cache_ttl)

            result.request_id = request_id
            return result

        except APIError as e:
            return APIResponse.error(
                message=e.message,
                code=e.code,
                error=str(e),
            )
        except Exception as e:
            self._logger.error(f"处理请求异常: {e}")
            return APIResponse.error(
                message="Internal server error",
                code=500,
                error=str(e),
            )

    def list_routes(self) -> list[dict]:
        """列出所有路由"""
        return [
            {
                "path": r.path,
                "method": r.method.value,
                "auth_required": r.auth_required,
                "rate_limit": r.rate_limit,
                "description": r.description,
            }
            for r in self._routes.values()
        ]
