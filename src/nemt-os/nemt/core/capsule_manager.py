"""
CapsuleManager - 胶囊管理器

统一管理所有胶囊的生命周期:
- 注册胶囊
- 启动/停止胶囊
- 管理依赖注入
"""

import logging
import time
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from nemt.core.capsule import ModuleCapsule
    from nemt.core.config_center import ConfigCenter
    from nemt.core.event_bus import EventBus

__all__ = ["CapsuleManager"]


class CapsuleManager:
    """
    胶囊管理器

    负责:
    - 胶囊注册
    - 依赖注入 (EventBus, ConfigCenter)
    - 生命周期管理
    - 启动顺序控制
    """

    def __init__(self, event_bus: "EventBus", config: "ConfigCenter"):
        """
        初始化管理器

        Args:
            event_bus: 事件总线
            config: 配置中心
        """
        self._event_bus = event_bus
        self._config = config
        self._capsules: dict[str, "ModuleCapsule"] = {}
        self._logger = logging.getLogger("CapsuleManager")
        self._is_running = False

    def register(self, capsule: "ModuleCapsule") -> None:
        """
        注册胶囊

        Args:
            capsule: 要注册的胶囊实例
        """
        capsule_id = capsule.capsule_id

        if capsule_id in self._capsules:
            self._logger.warning(f"胶囊 {capsule_id} 已存在，将被替换")

        # 依赖注入
        capsule.event_bus = self._event_bus
        capsule.config = self._config

        self._capsules[capsule_id] = capsule
        self._logger.info(f"注册胶囊: {capsule_id}")

    def unregister(self, capsule_id: str) -> None:
        """
        注销胶囊

        Args:
            capsule_id: 胶囊 ID
        """
        if capsule_id in self._capsules:
            capsule = self._capsules[capsule_id]
            if capsule.is_running:
                capsule.shutdown()
            del self._capsules[capsule_id]
            self._logger.info(f"注销胶囊: {capsule_id}")

    def get_capsule(self, capsule_id: str) -> Optional["ModuleCapsule"]:
        """
        获取胶囊

        Args:
            capsule_id: 胶囊 ID

        Returns:
            胶囊实例，不存在则返回 None
        """
        return self._capsules.get(capsule_id)

    def start_all(self) -> None:
        """
        启动所有胶囊

        启动顺序:
        1. 所有胶囊 init() - 订阅事件
        2. 发布 system.ready 事件
        3. 所有胶囊 start() - 开始执行

        注意: 单个胶囊初始化失败不阻断其他胶囊，
              失败信息发布到 system.capsule_init_failed 事件。
        """
        self._logger.info(f"启动所有胶囊 (共 {len(self._capsules)} 个)...")

        failed_capsules = {}

        # Phase 1: 所有胶囊订阅
        for capsule_id, capsule in self._capsules.items():
            try:
                capsule.init()
                capsule._initialized = True
                self._logger.debug(f"胶囊 {capsule_id} 初始化完成")
            except Exception as e:
                capsule._initialized = False
                failed_capsules[capsule_id] = str(e)
                self._logger.error(f"胶囊 {capsule_id} 初始化失败: {e}")

        # 发布初始化失败事件（如果有）
        if failed_capsules:
            self._event_bus.publish("system.capsule_init_failed", {"failed": failed_capsules})
            self._logger.warning(f"有 {len(failed_capsules)} 个胶囊初始化失败")

        # Phase 2: 发布就绪事件
        self._event_bus.publish(
            "system.ready",
            {
                "capsules": list(self._capsules.keys()),
                "failed_count": len(failed_capsules),
            },
        )
        self._logger.debug("系统就绪事件已发布")

        # Phase 3: 所有胶囊开始执行
        for capsule_id, capsule in self._capsules.items():
            try:
                if hasattr(capsule, "start"):
                    capsule.start()
                capsule._running = True
            except Exception as e:
                capsule._running = False
                self._logger.error(f"胶囊 {capsule_id} 启动失败: {e}")

        self._is_running = True
        self._logger.info("所有胶囊启动完成")

    def stop_all(self, timeout: float = 10.0) -> None:
        """
        停止所有胶囊

        Args:
            timeout: 单个胶囊超时时间

        注意: 单个胶囊关闭失败不阻断其他胶囊。
        """
        self._logger.info(f"停止所有胶囊 (共 {len(self._capsules)} 个)...")

        for capsule_id, capsule in self._capsules.items():
            start = time.time()
            try:
                capsule.shutdown()
                capsule._running = False  # 显式设置
                elapsed = time.time() - start
                self._logger.debug(f"胶囊 {capsule_id} 已关闭 ({elapsed:.3f}s)")
            except Exception as e:
                elapsed = time.time() - start
                self._logger.error(f"胶囊 {capsule_id} 关闭失败 ({elapsed:.3f}s): {e}")

        # 发布关闭事件
        self._event_bus.publish("system.shutdown", {"capsules": list(self._capsules.keys())})

        self._is_running = False
        self._logger.info("所有胶囊已停止")

    @property
    def capsules(self) -> dict[str, "ModuleCapsule"]:
        """获取所有胶囊"""
        return self._capsules

    @property
    def capsule_ids(self) -> list:
        """获取所有胶囊 ID"""
        return list(self._capsules.keys())

    def __len__(self) -> int:
        return len(self._capsules)

    def __repr__(self) -> str:
        return f"CapsuleManager(capsules={len(self._capsules)})"
