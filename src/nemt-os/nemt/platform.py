"""
NEMT Platform - 主入口

提供统一的平台初始化和运行接口。
"""

import logging

# 版本信息
__version__ = "2.0.0"
__author__ = "NEMT Team"

# 导入所有核心模块
from nemt import (
    AlertManager,
    APIGateway,
    AuditLogger,
    ConfigLoader,
    EventBus,
    HealthCheckRegistry,
    LogAggregator,
    MetricsCollector,
    OrderExecutor,
    PermissionManager,
    Profiler,
    RiskCalculator,
    SecretManager,
    StrategyMarket,
    StrategySimulator,
    TraceCollector,
    WorkflowEngine,
)


class NEMTPlatform:
    """
    NEMT 平台主类

    示例:
    ```python
    platform = NEMTPlatform()

    # 初始化
    platform.initialize()

    # 启动
    platform.start()

    # 运行策略
    platform.run_strategy(strategy)

    # 停止
    platform.shutdown()
    ```
    """

    def __init__(self, config: dict = None):
        self.config = config or {}
        self._initialized = False
        self._running = False

        # 核心组件
        self.capsule_manager = None
        self.event_bus = None
        self.metrics = None
        self.alerts = None
        self.health = None
        self.config_loader = None
        self.secrets = None
        self.audit = None
        self.permissions = None
        self.api_gateway = None
        self.market = None
        self.logs = None
        self.traces = None
        self.profiler = None
        self.workflows = None
        self.simulator = None
        self.executor = None
        self.risk = None

        # 配置日志
        self._setup_logging()

    def _setup_logging(self) -> None:
        """配置日志"""
        level = self.config.get("log_level", "INFO")
        logging.basicConfig(
            level=getattr(logging, level),
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )
        self._logger = logging.getLogger("NEMTPlatform")

    def initialize(self) -> "NEMTPlatform":
        """初始化平台"""
        if self._initialized:
            return self

        self._logger.info("初始化 NEMT 平台...")

        # 初始化核心组件
        self.event_bus = EventBus()
        self.metrics = MetricsCollector()
        self.alerts = AlertManager()
        self.health = HealthCheckRegistry()
        self.config_loader = ConfigLoader()
        self.secrets = SecretManager()
        self.audit = AuditLogger()
        self.permissions = PermissionManager()
        self.api_gateway = APIGateway()
        self.market = StrategyMarket()
        self.logs = LogAggregator()
        self.traces = TraceCollector()
        self.profiler = Profiler()
        self.workflows = WorkflowEngine()
        self.simulator = StrategySimulator()
        self.executor = OrderExecutor()
        self.risk = RiskCalculator()

        # 加载配置
        config_file = self.config.get("config_file")
        if config_file:
            self.config_loader.add_file(config_file)
            self.config_loader.load()

        self._initialized = True
        self._logger.info("NEMT 平台初始化完成")

        return self

    def start(self) -> "NEMTPlatform":
        """启动平台"""
        if not self._initialized:
            self.initialize()

        if self._running:
            return self

        self._logger.info("启动 NEMT 平台...")
        self._running = True

        return self

    def stop(self) -> "NEMTPlatform":
        """停止平台"""
        if not self._running:
            return self

        self._logger.info("停止 NEMT 平台...")
        self._running = False

        return self

    def shutdown(self) -> None:
        """关闭平台"""
        self._logger.info("关闭 NEMT 平台...")
        self.stop()
        self._logger.info("NEMT 平台已关闭")

    def get_status(self) -> dict:
        """获取平台状态"""
        return {
            "version": __version__,
            "initialized": self._initialized,
            "running": self._running,
            "components": {
                "event_bus": self.event_bus is not None,
                "metrics": self.metrics is not None,
                "alerts": self.alerts is not None,
                "health": self.health is not None,
                "config": self.config_loader is not None,
                "secrets": self.secrets is not None,
                "audit": self.audit is not None,
                "permissions": self.permissions is not None,
                "api_gateway": self.api_gateway is not None,
                "market": self.market is not None,
                "logs": self.logs is not None,
                "traces": self.traces is not None,
                "profiler": self.profiler is not None,
                "workflows": self.workflows is not None,
                "simulator": self.simulator is not None,
                "executor": self.executor is not None,
                "risk": self.risk is not None,
            },
        }


# 全局平台实例
_platform: NEMTPlatform | None = None


def get_platform() -> NEMTPlatform:
    """获取全局平台实例"""
    global _platform
    if _platform is None:
        _platform = NEMTPlatform()
    return _platform


def create_platform(config: dict = None) -> NEMTPlatform:
    """创建新平台实例"""
    return NEMTPlatform(config)


# CLI 入口
def main():
    """CLI 主入口"""
    import argparse

    parser = argparse.ArgumentParser(description="NEMT Platform")
    parser.add_argument("--version", action="version", version=f"NEMT {__version__}")
    parser.add_argument("--config", help="配置文件路径")
    parser.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"])

    args = parser.parse_args()

    # 创建平台
    platform = NEMTPlatform(
        {
            "config_file": args.config,
            "log_level": args.log_level,
        }
    )

    # 初始化并启动
    platform.initialize().start()

    print(f"NEMT Platform {__version__} 启动成功")
    print("按 Ctrl+C 停止...")

    try:
        import time

        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        platform.shutdown()
        print("\nNEMT Platform 已停止")


if __name__ == "__main__":
    main()
