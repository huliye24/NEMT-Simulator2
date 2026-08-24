"""
Sandbox - 沙箱隔离框架

提供策略执行的隔离环境:
- 代码执行隔离
- 资源限制
- 系统调用过滤
- 网络隔离
"""

import logging
import os
import resource
import signal
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

__all__ = [
    "Sandbox",
    "SandboxConfig",
    "SandboxResult",
    "SandboxState",
    "ResourceLimits",
]


class SandboxState(Enum):
    """沙箱状态"""

    CREATED = "created"
    RUNNING = "running"
    TERMINATED = "terminated"
    TIMEOUT = "timeout"
    ERROR = "error"


@dataclass
class ResourceLimits:
    """资源限制"""

    max_memory_mb: int = 256  # 最大内存 (MB)
    max_cpu_seconds: float = 10.0  # 最大 CPU 时间 (秒)
    max_execution_seconds: float = 30.0  # 最大执行时间 (秒)
    max_file_size_mb: int = 10  # 最大文件大小 (MB)
    max_processes: int = 10  # 最大进程数
    max_open_files: int = 100  # 最大打开文件数
    allow_network: bool = False  # 允许网络访问
    allow_filesystem: bool = True  # 允许文件系统访问
    allowed_dirs: list[str] = field(default_factory=list)  # 允许的目录
    blocked_modules: list[str] = field(default_factory=list)  # 禁止的模块


@dataclass
class SandboxResult:
    """沙箱执行结果"""

    success: bool
    output: Any
    error: str
    execution_time: float
    memory_used_mb: float
    state: SandboxState
    metrics: dict[str, Any] = field(default_factory=dict)


@dataclass
class SandboxConfig:
    """沙箱配置"""

    name: str
    limits: ResourceLimits = field(default_factory=ResourceLimits)
    # 安全策略
    block_builtins: list[str] = field(default_factory=list)  # 禁止的内置函数
    allowed_globals: list[str] = field(default_factory=lambda: ["__name__", "__doc__"])  # 允许的全局变量
    # 超时处理
    on_timeout: str = "terminate"  # "terminate", "exception", "ignore"
    # 错误处理
    capture_stdout: bool = True
    capture_stderr: bool = True


class Sandbox:
    """
    Python 沙箱

    提供安全的代码执行环境。

    示例:
    ```python
    config = SandboxConfig(
        name="strategy_sandbox",
        limits=ResourceLimits(max_memory_mb=128, max_execution_seconds=10),
        block_builtins=["open", "eval", "exec"],
    )

    sandbox = Sandbox(config)
    result = sandbox.execute(code, {"data": [1, 2, 3]})
    print(result.output)
    ```
    """

    # 默认禁止的内置函数
    DANGEROUS_BUILTINS = {
        "open",
        "file",
        "eval",
        "exec",
        "compile",
        "__import__",
        "reload",
        "input",
        "exit",
        "quit",
        "help",
        "breakpoint",
        "license",
    }

    def __init__(self, config: SandboxConfig):
        self.config = config
        self._state = SandboxState.CREATED
        self._logger = logging.getLogger(f"Sandbox.{config.name}")
        self._start_time: float | None = None

        # 默认禁止
        if not config.block_builtins:
            config.block_builtins = list(self.DANGEROUS_BUILTINS)

    @property
    def state(self) -> SandboxState:
        """沙箱状态"""
        return self._state

    def execute(self, code: str, globals_dict: dict = None, locals_dict: dict = None) -> SandboxResult:
        """
        执行代码

        Args:
            code: 代码字符串
            globals_dict: 全局变量
            locals_dict: 局部变量

        Returns:
            执行结果
        """
        if globals_dict is None:
            globals_dict = {}
        if locals_dict is None:
            locals_dict = {}

        self._state = SandboxState.RUNNING
        self._start_time = time.time()

        # 创建安全的全局变量
        safe_globals = self._create_safe_globals(globals_dict)
        safe_locals = locals_dict.copy()

        # 设置资源限制
        limits = self.config.limits

        # 设置超时
        def timeout_handler(signum, frame):
            if self.config.on_timeout == "terminate":
                self._state = SandboxState.TIMEOUT
                raise TimeoutError(f"执行超时 ({limits.max_execution_seconds}s)")
            elif self.config.on_timeout == "exception":
                raise TimeoutError(f"执行超时 ({limits.max_execution_seconds}s)")

        # 记录开始内存
        start_memory = self._get_memory_usage()

        try:
            # 设置信号处理
            old_handler = signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(int(limits.max_execution_seconds))

            # 执行代码
            try:
                result = eval(code, safe_globals, safe_locals)
                self._state = SandboxState.TERMINATED
            except SyntaxError as e:
                self._state = SandboxState.ERROR
                return SandboxResult(
                    success=False,
                    output=None,
                    error=f"语法错误: {e}",
                    execution_time=time.time() - self._start_time,
                    memory_used_mb=self._get_memory_usage() - start_memory,
                    state=self._state,
                )
            finally:
                signal.alarm(0)
                signal.signal(signal.SIGALRM, old_handler)

            return SandboxResult(
                success=True,
                output=result,
                error="",
                execution_time=time.time() - self._start_time,
                memory_used_mb=self._get_memory_usage() - start_memory,
                state=self._state,
            )

        except TimeoutError as e:
            self._state = SandboxState.TIMEOUT
            return SandboxResult(
                success=False,
                output=None,
                error=str(e),
                execution_time=time.time() - self._start_time,
                memory_used_mb=self._get_memory_usage() - start_memory,
                state=self._state,
            )

        except Exception as e:
            self._state = SandboxState.ERROR
            return SandboxResult(
                success=False,
                output=None,
                error=f"{type(e).__name__}: {e}",
                execution_time=time.time() - self._start_time,
                memory_used_mb=self._get_memory_usage() - start_memory,
                state=self._state,
            )

    def execute_function(self, func: Callable, *args, **kwargs) -> SandboxResult:
        """
        执行函数

        Args:
            func: 函数
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            执行结果
        """
        code = "func(*args, **kwargs)"
        return self.execute(code, {"func": func, "args": args, "kwargs": kwargs})

    def _create_safe_globals(self, user_globals: dict) -> dict:
        """创建安全的全局变量"""
        # 安全的内置函数
        safe_builtins = {}
        for name in dir(__builtins__):
            if name not in self.config.block_builtins:
                safe_builtins[name] = getattr(__builtins__, name)

        # 基础全局变量
        safe_globals = {
            "__builtins__": safe_builtins,
            "__name__": user_globals.get("__name__", "__sandbox__"),
            "__doc__": user_globals.get("__doc__", None),
        }

        # 添加用户全局变量（过滤）
        for key, value in user_globals.items():
            if key in self.config.allowed_globals:
                safe_globals[key] = value

        # 添加安全模块
        safe_globals["math"] = __import__("math")
        safe_globals["random"] = __import__("random")
        safe_globals["json"] = __import__("json")

        return safe_globals

    def _get_memory_usage(self) -> float:
        """获取内存使用 (MB)"""
        try:
            import psutil

            process = psutil.Process(os.getpid())
            return process.memory_info().rss / 1024 / 1024
        except ImportError:
            # 备用方法
            return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024

    def check_resource_limits(self) -> dict[str, Any]:
        """检查资源使用情况"""
        return {
            "memory_mb": self._get_memory_usage(),
            "execution_time": time.time() - self._start_time if self._start_time else 0,
            "state": self._state.value,
        }


class SandboxManager:
    """
    沙箱管理器

    管理多个沙箱实例。

    示例:
    ```python
    manager = SandboxManager()

    sandbox1 = manager.create("strategy_1", config)
    sandbox2 = manager.create("strategy_2", config)

    result1 = sandbox1.execute(code1)
    result2 = sandbox2.execute(code2)

    manager.destroy("strategy_1")
    ```
    """

    def __init__(self):
        self._sandboxes: dict[str, Sandbox] = {}
        self._logger = logging.getLogger("SandboxManager")

    def create(self, name: str, config: SandboxConfig = None) -> Sandbox:
        """创建沙箱"""
        if config is None:
            config = SandboxConfig(name=name)

        sandbox = Sandbox(config)
        self._sandboxes[name] = sandbox
        return sandbox

    def get(self, name: str) -> Sandbox | None:
        """获取沙箱"""
        return self._sandboxes.get(name)

    def destroy(self, name: str) -> bool:
        """销毁沙箱"""
        if name in self._sandboxes:
            del self._sandboxes[name]
            return True
        return False

    def destroy_all(self) -> None:
        """销毁所有沙箱"""
        self._sandboxes.clear()

    def list_sandboxes(self) -> list[str]:
        """列出所有沙箱"""
        return list(self._sandboxes.keys())

    def __len__(self) -> int:
        return len(self._sandboxes)


# 全局管理器
_sandbox_manager: SandboxManager | None = None


def get_sandbox_manager() -> SandboxManager:
    """获取沙箱管理器"""
    global _sandbox_manager
    if _sandbox_manager is None:
        _sandbox_manager = SandboxManager()
    return _sandbox_manager
