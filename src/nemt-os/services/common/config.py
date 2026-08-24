"""
NEMT Platform - 服务配置
"""

import os
from dataclasses import dataclass


@dataclass
class ServiceConfig:
    """服务配置"""

    service_name: str
    host: str = "0.0.0.0"
    port: int = 8000
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    log_level: str = "INFO"
    environment: str = "development"

    @classmethod
    def from_env(cls, service_name: str, default_port: int = 8000) -> "ServiceConfig":
        """从环境变量加载配置"""
        return cls(
            service_name=service_name,
            host=os.getenv("SERVICE_HOST", "0.0.0.0"),
            port=int(os.getenv("SERVICE_PORT", str(default_port))),
            redis_host=os.getenv("REDIS_HOST", "localhost"),
            redis_port=int(os.getenv("REDIS_PORT", "6379")),
            redis_db=int(os.getenv("REDIS_DB", "0")),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            environment=os.getenv("ENVIRONMENT", "development"),
        )

    @property
    def redis_url(self) -> str:
        """Redis 连接 URL"""
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"

    @property
    def service_url(self) -> str:
        """服务 URL"""
        return f"http://{self.host}:{self.port}"


# 默认端口分配
SERVICE_PORTS = {
    "market": 8001,
    "signal": 8002,
    "risk": 8003,
    "execution": 8004,
    "brain": 8005,
}


def get_config(service_name: str) -> ServiceConfig:
    """获取服务配置"""
    default_port = SERVICE_PORTS.get(service_name, 8000)
    return ServiceConfig.from_env(service_name, default_port)
