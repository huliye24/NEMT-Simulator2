"""
ModuleCapsule - 模块胶囊基类

提供所有胶囊的基类，支持:
|- 标准化生命周期 (init, exec, shutdown)
|- 事件订阅管理
|- 配置访问
|- 状态管理
|- 健康检查
|- 指标采集
|- 错误处理（暗物质框架集成）
|- 分形迭代（五阶段：看画填验连）
|- ICapsule 接口实现
"""

import logging
import time
from abc import ABC, abstractmethod
from collections.abc import Callable
from contextlib import contextmanager
from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from nemt.core.config_center import ConfigCenter
    from nemt.core.event_bus import EventBus
    from nemt.core.interfaces import CapsuleState, HealthStatus

from nemt.core.interfaces import CapsuleState, HealthStatus

__all__ = ["ModuleCapsule", "FractalCapsule", "BaseCapsule"]


class BaseCapsule(ABC):
    """
    胶囊基类 - 实现 ICapsule 接口

    提供所有业务胶囊的通用功能。
    """

    def __init__(self, capsule_id: str):
        self._capsule_id = capsule_id
        self._logger = logging.getLogger(f"Capsule.{capsule_id}")
        self._state = CapsuleState.CREATED
        self._created_at = time.time()
        self._initialized_at: float | None = None
        self._started_at: float | None = None
        self._stopped_at: float | None = None
        self._last_error: Exception | None = None

        # 依赖注入 (由 CapsuleManager 设置)
        self._event_bus: "EventBus" | None = None
        self._config: "ConfigCenter" | None = None

        # 错误处理（延迟导入避免循环依赖）
        self._error_handler = None

        # 指标
        self._metrics: dict[str, Any] = {
            "exec_count": 0,
            "error_count": 0,
            "total_exec_time": 0.0,
        }

    # ========================================================================
    # ICapsule 接口实现
    # ========================================================================

    @property
    def capsule_id(self) -> str:
        """胶囊 ID"""
        return self._capsule_id

    @property
    def state(self) -> CapsuleState:
        """当前状态"""
        return self._state

    @property
    def is_initialized(self) -> bool:
        """是否已初始化"""
        return self._state in (CapsuleState.INITIALIZED, CapsuleState.STARTING, CapsuleState.RUNNING)

    @property
    def is_running(self) -> bool:
        """是否正在运行"""
        return self._state == CapsuleState.RUNNING

    @abstractmethod
    def init(self) -> None:
        """初始化胶囊"""
        pass

    @abstractmethod
    def exec(self) -> dict[str, Any]:
        """执行主要逻辑"""
        pass

    def shutdown(self) -> None:
        """关闭胶囊"""
        self._state = CapsuleState.STOPPING
        self._stopped_at = time.time()
        self._logger.info(f"{self._capsule_id} 已关闭")
        self._state = CapsuleState.STOPPED

    def start(self) -> None:
        """启动胶囊"""
        if self._state != CapsuleState.INITIALIZED:
            raise RuntimeError(f"胶囊 {self._capsule_id} 必须先初始化才能启动")
        self._state = CapsuleState.STARTING
        self._started_at = time.time()
        self._logger.info(f"{self._capsule_id} 已启动")
        self._state = CapsuleState.RUNNING

    def get_health(self) -> HealthStatus:
        """获取健康状态"""
        if self._state == CapsuleState.ERROR:
            return HealthStatus.UNHEALTHY
        if self._state in (CapsuleState.STOPPED, CapsuleState.CREATED):
            return HealthStatus.UNKNOWN
        if self._error_count > 0:
            return HealthStatus.DEGRADED
        return HealthStatus.HEALTHY

    def get_health_details(self) -> dict[str, Any]:
        """获取健康详情"""
        return {
            "capsule_id": self._capsule_id,
            "state": self._state.value,
            "health": self.get_health().value,
            "uptime": self._get_uptime(),
            "error_count": self._error_count,
            "exec_count": self._metrics.get("exec_count", 0),
        }

    def get_metrics(self) -> dict[str, Any]:
        """获取指标数据"""
        metrics = self._metrics.copy()
        metrics["avg_exec_time"] = (
            metrics["total_exec_time"] / metrics["exec_count"] if metrics["exec_count"] > 0 else 0
        )
        metrics["uptime"] = self._get_uptime()
        return metrics

    def reset_metrics(self) -> None:
        """重置指标"""
        self._metrics = {
            "exec_count": 0,
            "error_count": 0,
            "total_exec_time": 0.0,
        }

    # ========================================================================
    # 辅助属性
    # ========================================================================

    @property
    def event_bus(self) -> Optional["EventBus"]:
        """事件总线"""
        return self._event_bus

    @event_bus.setter
    def event_bus(self, bus: "EventBus"):
        """设置事件总线"""
        self._event_bus = bus

    @property
    def config(self) -> Optional["ConfigCenter"]:
        """配置中心"""
        return self._config

    @config.setter
    def config(self, cfg: "ConfigCenter"):
        """设置配置中心"""
        self._config = cfg

    @property
    def _error_count(self) -> int:
        """错误计数"""
        return self._metrics.get("error_count", 0)

    # ========================================================================
    # 生命周期辅助方法
    # ========================================================================

    def _transition_state(self, new_state: CapsuleState) -> None:
        """状态转换"""
        old_state = self._state
        self._state = new_state
        self._logger.debug(f"{self._capsule_id}: {old_state.value} -> {new_state.value}")

        if new_state == CapsuleState.ERROR:
            self._logger.error(f"{self._capsule_id} 进入错误状态")

    def _check_initialized(self) -> None:
        """检查是否已初始化"""
        if not self.is_initialized:
            raise RuntimeError(f"胶囊 {self._capsule_id} 尚未初始化，请先调用 init()")

    def _check_event_bus(self) -> None:
        """检查事件总线是否可用"""
        if self._event_bus is None:
            raise RuntimeError(f"胶囊 {self._capsule_id} 未设置事件总线")

    def _get_uptime(self) -> float:
        """获取运行时长（秒）"""
        if self._started_at is None:
            return 0.0
        end = self._stopped_at or time.time()
        return end - self._started_at

    # ========================================================================
    # 事件订阅便捷方法
    # ========================================================================

    def subscribe(self, event_type: str, handler: Callable) -> None:
        """订阅事件"""
        self._check_event_bus()
        self._event_bus.subscribe(event_type, handler)
        self._logger.debug(f"订阅事件: {event_type}")

    def unsubscribe(self, event_type: str, handler: Callable) -> None:
        """取消订阅"""
        self._check_event_bus()
        self._event_bus.unsubscribe(event_type, handler)
        self._logger.debug(f"取消订阅: {event_type}")

    def publish(self, event_type: str, data: Any = None) -> None:
        """发布事件"""
        self._check_event_bus()
        self._event_bus.publish(event_type, data)

    # ========================================================================
    # 配置便捷方法
    # ========================================================================

    def get_config(self, key: str, default: Any = None) -> Any:
        """获取配置"""
        if self._config is None:
            return default
        return self._config.get(key, default)

    def set_config(self, key: str, value: Any) -> None:
        """设置配置"""
        if self._config is not None:
            self._config.set(key, value)

    # ========================================================================
    # 执行辅助方法
    # ========================================================================

    def _record_exec(self, exec_time: float) -> None:
        """记录执行"""
        self._metrics["exec_count"] += 1
        self._metrics["total_exec_time"] += exec_time

    def _record_error(self, error: Exception, details: dict[str, Any] | None = None) -> None:
        """记录错误"""
        self._metrics["error_count"] += 1
        self._last_error = error
        self._transition_state(CapsuleState.ERROR)

        handler = self._get_error_handler()
        if handler is None:
            self._logger.error(f"Unhandled error: {type(error).__name__}: {error}")
            return

        try:
            from nemt.core.dark_matter.error_types import ErrorContext

            context = ErrorContext(
                error=error,
                source=self._capsule_id,
                details=details or {},
            )
            handler.handle(error, context)
        except Exception as e:
            self._logger.error(f"Failed to record error: {e}")

    def _try_exec(self, func: Callable, *args, default: Any = None, **kwargs) -> dict[str, Any]:
        """安全执行函数"""
        try:
            start = time.time()
            result = func(*args, **kwargs)
            self._record_exec(time.time() - start)
            return {"success": True, "result": result}
        except Exception as e:
            self._record_error(e, {"function": func.__name__})
            return {"success": False, "error": e}

    # ========================================================================
    # 错误处理
    # ========================================================================

    def _get_error_handler(self):
        """获取错误处理器（延迟初始化）"""
        if self._error_handler is None:
            try:
                from nemt.core.dark_matter.error_handler import ErrorHandler

                self._error_handler = ErrorHandler.get_instance()
            except ImportError:
                return None
        return self._error_handler

    @contextmanager
    def capsule_error_context(self):
        """胶囊级错误上下文管理器"""
        handler = self._get_error_handler()
        if handler:
            with handler.error_context(self._capsule_id):
                yield
        else:
            yield

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(id='{self._capsule_id}', state={self._state.value})"


# ========================================================================
# 兼容性别名
# ========================================================================

ModuleCapsule = BaseCapsule


# ========================================================================
# 分形迭代胶囊基类
# ========================================================================


class FractalCapsule(BaseCapsule):
    """
    分形迭代胶囊基类

    继承自 BaseCapsule，并添加五阶段迭代支持。
    """

    def __init__(self, capsule_id: str, version: str = "1.0.0"):
        super().__init__(capsule_id)

        self._version = version
        self._layer = "L1"

        # 五阶段产物
        self._observe_report: dict[str, Any] | None = None
        self._design_contract: dict[str, Any] | None = None
        self._verify_result: dict[str, Any] | None = None

        # 迭代计数器
        self._iteration_count = 0
        self._phase_timings: dict[str, float] = {}

    @property
    def version(self) -> str:
        """版本号"""
        return self._version

    @property
    def layer(self) -> str:
        """所属层级"""
        return self._layer

    @property
    def iteration_count(self) -> int:
        """迭代次数"""
        return self._iteration_count

    @property
    def observe_report(self) -> dict[str, Any] | None:
        """观察报告"""
        return self._observe_report

    @property
    def design_contract(self) -> dict[str, Any] | None:
        """设计契约"""
        return self._design_contract

    # 五阶段方法
    def observe_phase(self) -> dict[str, Any]:
        """【看】观察阶段"""
        return {
            "capsule_id": self._capsule_id,
            "class": self.__class__.__name__,
            "version": self._version,
            "layer": self._layer,
            "timestamp": datetime.now().isoformat(),
        }

    def design_phase(self) -> dict[str, Any]:
        """【画】设计阶段"""
        return {
            "capsule_id": self._capsule_id,
            "layer": self._layer,
            "public_methods": self._get_public_methods(),
            "dependencies": self._get_dependencies(),
            "timestamp": datetime.now().isoformat(),
        }

    def implement_phase(self) -> None:
        """【填】实现阶段"""
        pass

    def verify_phase(self) -> dict[str, Any]:
        """【验】验证阶段"""
        return {
            "capsule_id": self._capsule_id,
            "initialized": self.is_initialized,
            "ready": self.is_initialized,
            "timestamp": datetime.now().isoformat(),
        }

    def integrate_phase(self) -> None:
        """【连】集成阶段"""
        self._logger.info(f"{self._capsule_id} 集成完成")

    def run_fractal_iteration(self) -> dict[str, Any]:
        """执行完整的五阶段迭代"""
        self._iteration_count += 1
        iteration_start = datetime.now()

        result = {
            "iteration": self._iteration_count,
            "capsule_id": self._capsule_id,
            "version": self._version,
            "layer": self._layer,
            "start_time": iteration_start.isoformat(),
            "phases": {},
            "status": "success",
        }

        try:
            phase_start = datetime.now()
            self._observe_report = self.observe_phase()
            result["phases"]["observe"] = {
                "report": self._observe_report,
                "duration_ms": (datetime.now() - phase_start).total_seconds() * 1000,
            }

            phase_start = datetime.now()
            self._design_contract = self.design_phase()
            result["phases"]["design"] = {
                "contract": self._design_contract,
                "duration_ms": (datetime.now() - phase_start).total_seconds() * 1000,
            }

            phase_start = datetime.now()
            self.implement_phase()
            result["phases"]["implement"] = {
                "status": "completed",
                "duration_ms": (datetime.now() - phase_start).total_seconds() * 1000,
            }

            phase_start = datetime.now()
            self._verify_result = self.verify_phase()
            result["phases"]["verify"] = {
                "result": self._verify_result,
                "duration_ms": (datetime.now() - phase_start).total_seconds() * 1000,
            }

            phase_start = datetime.now()
            self.integrate_phase()
            result["phases"]["integrate"] = {
                "status": "completed",
                "duration_ms": (datetime.now() - phase_start).total_seconds() * 1000,
            }

            result["end_time"] = datetime.now().isoformat()
            result["total_duration_ms"] = (datetime.now() - iteration_start).total_seconds() * 1000

        except Exception as e:
            result["status"] = "failed"
            result["error"] = str(e)
            result["error_type"] = type(e).__name__
            self._logger.error(f"迭代失败: {e}")
            self._record_error(e)

        return result

    def get_iteration_summary(self) -> dict[str, Any]:
        """获取迭代摘要"""
        return {
            "capsule_id": self._capsule_id,
            "iteration_count": self._iteration_count,
            "last_observe": self._observe_report,
            "last_design": self._design_contract,
            "last_verify": self._verify_result,
        }

    def _get_public_methods(self) -> list[str]:
        """获取公开方法列表"""
        return [name for name in dir(self) if not name.startswith("_") and callable(getattr(self, name))]

    def _get_dependencies(self) -> list[str]:
        """获取依赖列表"""
        return []
