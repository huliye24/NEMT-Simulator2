"""
NEMT Platform - 服务发现
"""

import json
import time

import redis

from .config import ServiceConfig
from .logging import get_logger
from .types import ServiceInfo, ServiceStatus


class ServiceRegistry:
    """
    服务注册表

    使用 Redis 实现服务发现
    """

    KEY_PREFIX = "nemt:service:"
    LEASE_TTL = 30  # 服务注册过期时间（秒）

    def __init__(self, config: ServiceConfig):
        self.config = config
        self.redis = redis.Redis(
            host=config.redis_host,
            port=config.redis_port,
            db=config.redis_db,
            decode_responses=True,
        )
        self.logger = get_logger(f"ServiceRegistry:{config.service_name}")
        self._heartbeat_task = None

    def register(self, service_info: ServiceInfo) -> bool:
        """
        注册服务

        Args:
            service_info: 服务信息

        Returns:
            注册是否成功
        """
        try:
            key = f"{self.KEY_PREFIX}{service_info.service_name}"
            value = json.dumps(service_info.to_dict())

            # 使用 SETNX 确保只有一个实例注册
            if self.redis.setnx(key, value):
                # 设置过期时间
                self.redis.expire(key, self.LEASE_TTL * 2)
                self.logger.info(f"注册服务: {service_info.service_name}")
                return True

            # 如果已有注册，更新
            self.redis.set(key, value)
            self.redis.expire(key, self.LEASE_TTL * 2)
            self.logger.info(f"更新服务注册: {service_info.service_name}")
            return True

        except Exception as e:
            self.logger.error(f"注册服务失败: {e}")
            return False

    def unregister(self, service_name: str) -> bool:
        """
        注销服务

        Args:
            service_name: 服务名称

        Returns:
            注销是否成功
        """
        try:
            key = f"{self.KEY_PREFIX}{service_name}"
            self.redis.delete(key)
            self.logger.info(f"注销服务: {service_name}")
            return True
        except Exception as e:
            self.logger.error(f"注销服务失败: {e}")
            return False

    def get_service(self, service_name: str) -> ServiceInfo | None:
        """
        获取服务信息

        Args:
            service_name: 服务名称

        Returns:
            服务信息或 None
        """
        try:
            key = f"{self.KEY_PREFIX}{service_name}"
            value = self.redis.get(key)

            if value:
                data = json.loads(value)
                return ServiceInfo(**data)
            return None

        except Exception as e:
            self.logger.error(f"获取服务失败: {e}")
            return None

    def list_services(self) -> list[str]:
        """
        列出所有已注册的服务

        Returns:
            服务名称列表
        """
        try:
            pattern = f"{self.KEY_PREFIX}*"
            keys = self.redis.keys(pattern)
            return [k.replace(self.KEY_PREFIX, "") for k in keys]
        except Exception as e:
            self.logger.error(f"列出服务失败: {e}")
            return []

    def heartbeat(self, service_name: str) -> bool:
        """
        发送心跳（续约服务注册）

        Args:
            service_name: 服务名称

        Returns:
            是否成功
        """
        try:
            key = f"{self.KEY_PREFIX}{service_name}"
            if self.redis.exists(key):
                self.redis.expire(key, self.LEASE_TTL * 2)
                return True
            return False
        except Exception as e:
            self.logger.error(f"心跳失败: {e}")
            return False

    def close(self):
        """关闭连接"""
        self.redis.close()


class ServiceDiscovery:
    """
    服务发现客户端

    用于发现和连接其他服务
    """

    def __init__(self, config: ServiceConfig):
        self.config = config
        self.redis = redis.Redis(
            host=config.redis_host,
            port=config.redis_port,
            db=config.redis_db,
            decode_responses=True,
        )
        self.logger = get_logger(f"ServiceDiscovery:{config.service_name}")

    def find_service(self, service_name: str) -> ServiceInfo | None:
        """
        查找服务

        Args:
            service_name: 服务名称

        Returns:
            服务信息或 None
        """
        try:
            key = f"{ServiceRegistry.KEY_PREFIX}{service_name}"
            value = self.redis.get(key)

            if value:
                data = json.loads(value)
                return ServiceInfo(**data)
            return None

        except Exception as e:
            self.logger.error(f"查找服务失败: {e}")
            return None

    def find_services_by_tag(self, tag: str) -> list[ServiceInfo]:
        """
        按标签查找服务

        Args:
            tag: 服务标签

        Returns:
            匹配的服务列表
        """
        services = []
        try:
            pattern = f"{ServiceRegistry.KEY_PREFIX}*"
            keys = self.redis.keys(pattern)

            for key in keys:
                value = self.redis.get(key)
                if value:
                    data = json.loads(value)
                    if tag in data.get("metadata", {}).get("tags", []):
                        services.append(ServiceInfo(**data))

        except Exception as e:
            self.logger.error(f"标签查找失败: {e}")

        return services

    def wait_for_service(
        self, service_name: str, timeout: float = 30.0, check_interval: float = 1.0
    ) -> ServiceInfo | None:
        """
        等待服务上线

        Args:
            service_name: 服务名称
            timeout: 超时时间（秒）
            check_interval: 检查间隔（秒）

        Returns:
            服务信息或 None（超时）
        """
        start_time = time.time()

        while time.time() - start_time < timeout:
            service = self.find_service(service_name)
            if service and service.status == ServiceStatus.HEALTHY:
                return service

            time.sleep(check_interval)

        return None

    def close(self):
        """关闭连接"""
        self.redis.close()
