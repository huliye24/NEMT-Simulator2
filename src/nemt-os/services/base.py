"""
NEMT Platform - 服务基类
"""

import asyncio
from abc import ABC, abstractmethod
from datetime import datetime

import redis.asyncio as aioredis
from aiohttp import web

from .common import ServiceConfig, ServiceInfo, ServiceStatus, get_logger
from .common.discovery import ServiceRegistry


class BaseService(ABC):
    """
    服务基类

    所有微服务都应继承此类
    """

    def __init__(self, service_name: str, port: int = 8000):
        self.config = ServiceConfig.from_env(service_name, port)
        self.logger = get_logger(service_name)
        self.status = ServiceStatus.STARTING
        self.started_at = datetime.now()
        self._redis: aioredis.Redis | None = None
        self._registry: ServiceRegistry | None = None
        self._app: web.Application | None = None
        self._runner: web.AppRunner | None = None
        self._pubsub: aioredis.client.PubSub | None = None
        self._subscribers: dict = {}
        self._loop: asyncio.AbstractEventLoop | None = None

    async def initialize(self):
        """初始化服务"""
        self.logger.info(f"初始化 {self.config.service_name}...")

        # 连接 Redis
        self._redis = aioredis.from_url(self.config.redis_url, encoding="utf-8", decode_responses=True)

        # 初始化注册表
        self._registry = ServiceRegistry(self.config)

        # 调用子类初始化
        await self.on_init()

        self.logger.info(f"{self.config.service_name} 初始化完成")

    async def start(self):
        """启动服务"""
        self.logger.info(f"启动 {self.config.service_name}...")

        # 注册服务
        service_info = ServiceInfo(
            service_name=self.config.service_name,
            host=self.config.host,
            port=self.config.port,
            status=ServiceStatus.HEALTHY,
            version="1.0.0",
            started_at=datetime.now(),
        )
        self._registry.register(service_info)

        # 创建 Web 应用
        self._app = web.Application()
        self._setup_routes()

        # 启动 HTTP 服务器
        self._runner = web.AppRunner(self._app)
        await self._runner.setup()
        site = web.TCPSite(self._runner, self.config.host, self.config.port)
        await site.start()

        self.status = ServiceStatus.HEALTHY
        self.logger.info(f"{self.config.service_name} 启动完成，监听 {self.config.port}")

        # 启动事件订阅
        asyncio.create_task(self._subscribe_events())

        # 调用子类启动
        await self.on_start()

    async def stop(self):
        """停止服务"""
        self.logger.info(f"停止 {self.config.service_name}...")

        self.status = ServiceStatus.STOPPING

        # 注销服务
        if self._registry:
            self._registry.unregister(self.config.service_name)

        # 调用子类停止
        await self.on_stop()

        # 关闭连接
        if self._pubsub:
            await self._pubsub.close()

        if self._redis:
            await self._redis.close()

        if self._runner:
            await self._runner.cleanup()

        self.logger.info(f"{self.config.service_name} 已停止")

    def _setup_routes(self):
        """设置路由"""
        self._app.router.add_get("/health", self._handle_health)
        self._app.router.add_get("/info", self._handle_info)

    async def _handle_health(self, request):
        """健康检查"""
        return web.json_response(
            {
                "status": self.status.value,
                "service": self.config.service_name,
                "timestamp": datetime.now().isoformat(),
            }
        )

    async def _handle_info(self, request):
        """服务信息"""
        return web.json_response(
            {
                "service": self.config.service_name,
                "version": "1.0.0",
                "started_at": self.started_at.isoformat() if self.started_at else None,
                "uptime_seconds": (datetime.now() - self.started_at).total_seconds() if self.started_at else 0,
            }
        )

    async def _subscribe_events(self):
        """订阅事件"""
        self._pubsub = self._redis.pubsub()

        for event_type in self._subscribers:
            await self._pubsub.subscribe(event_type)

        async for message in self._pubsub.listen():
            if message["type"] == "message":
                event_type = message["channel"]
                if event_type in self._subscribers:
                    handler = self._subscribers[event_type]
                    try:
                        import json

                        data = json.loads(message["data"])
                        asyncio.create_task(handler(data))
                    except Exception as e:
                        self.logger.error(f"事件处理失败: {e}")

    def subscribe(self, event_type: str, handler):
        """
        订阅事件

        Args:
            event_type: 事件类型
            handler: 处理函数
        """
        self._subscribers[event_type] = handler
        if self._pubsub:
            asyncio.create_task(self._pubsub.subscribe(event_type))

    async def publish(self, event_type: str, data: dict):
        """
        发布事件

        Args:
            event_type: 事件类型
            data: 事件数据
        """
        if self._redis:
            import json

            await self._redis.publish(event_type, json.dumps(data))

    async def run(self):
        """运行服务"""
        try:
            await self.initialize()
            await self.start()

            # 保持运行
            while self.status == ServiceStatus.HEALTHY:
                await asyncio.sleep(1)

        except Exception as e:
            self.logger.error(f"服务异常: {e}")
            raise
        finally:
            await self.stop()

    # 子类需要实现的方法
    @abstractmethod
    async def on_init(self):
        """初始化回调"""
        pass

    @abstractmethod
    async def on_start(self):
        """启动回调"""
        pass

    async def on_stop(self):
        """停止回调"""
        pass
