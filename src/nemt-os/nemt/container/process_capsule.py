"""
Process Capsule - 进程胶囊

提供胶囊的进程级隔离能力。
"""

import logging
import os
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from multiprocessing import Pipe, Process, Queue
from typing import Any

__all__ = [
    "ProcessCapsule",
    "ProcessState",
    "ProcessConfig",
    "ProcessCapsuleManager",
]


class ProcessState(Enum):
    """进程状态"""

    CREATED = "created"
    INITIALIZING = "initializing"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"


@dataclass
class ProcessConfig:
    """进程配置"""

    name: str
    target: Callable
    args: tuple = ()
    kwargs: dict = field(default_factory=dict)
    # 资源限制
    max_memory_mb: int | None = None  # 内存限制 (MB)
    max_cpu_percent: int | None = None  # CPU 限制 (%)
    # 进程池配置
    use_process_pool: bool = False
    pool_size: int = 4
    # 超时配置
    startup_timeout: float = 30.0  # 启动超时
    shutdown_timeout: float = 10.0  # 关闭超时
    # 进程间通信
    enable_ipc: bool = True  # 启用进程间通信
    # 环境变量
    env: dict[str, str] = field(default_factory=dict)


@dataclass
class ProcessInfo:
    """进程信息"""

    pid: int
    name: str
    state: ProcessState
    started_at: float
    cpu_percent: float = 0.0
    memory_mb: float = 0.0
    message_count: int = 0


class ProcessCapsule:
    """
    进程胶囊

    将 Capsule 包装为独立进程运行。

    示例:
    ```python
    config = ProcessConfig(
        name="my_process",
        target=my_capsule_exec,
        args=(capsule_id,),
    )

    capsule = ProcessCapsule(config)
    capsule.start()
    capsule.send_message({"type": "ping"})
    capsule.stop()
    ```
    """

    def __init__(self, config: ProcessConfig):
        self.config = config
        self._process: Process | None = None
        self._state = ProcessState.CREATED
        self._start_time: float | None = None
        self._logger = logging.getLogger(f"Process.{config.name}")

        # 进程间通信
        self._send_queue: Queue | None = None
        self._recv_queue: Queue | None = None
        self._command_pipe: Pipe | None = None
        self._result_pipe: Pipe | None = None

        # 消息处理
        self._message_handlers: dict[str, Callable] = {}
        self._recv_thread: threading.Thread | None = None
        self._running = False

    @property
    def pid(self) -> int | None:
        """进程 ID"""
        if self._process:
            return self._process.pid
        return None

    @property
    def state(self) -> ProcessState:
        """进程状态"""
        return self._state

    @property
    def is_alive(self) -> bool:
        """进程是否存活"""
        return self._process is not None and self._process.is_alive()

    def start(self) -> bool:
        """
        启动进程

        Returns:
            是否启动成功
        """
        if self._state != ProcessState.CREATED:
            return False

        try:
            self._state = ProcessState.INITIALIZING

            # 创建通信队列
            if self.config.enable_ipc:
                self._send_queue = Queue()
                self._recv_queue = Queue()
                recv_conn, send_conn = Pipe()
                self._command_pipe = send_conn
                self._result_pipe = recv_conn

            # 设置环境变量
            env = os.environ.copy()
            env.update(self.config.env)
            env["NEMT_PROCESS_NAME"] = self.config.name

            # 创建进程
            self._process = Process(
                target=self._run_target,
                name=self.config.name,
                args=(self.config.args, self.config.kwargs),
            )

            self._process.start()
            self._start_time = time.time()
            self._state = ProcessState.RUNNING

            # 启动消息接收线程
            if self.config.enable_ipc:
                self._running = True
                self._recv_thread = threading.Thread(target=self._recv_messages, daemon=True)
                self._recv_thread.start()

            self._logger.info(f"进程 {self.config.name} 启动成功 (PID: {self.pid})")
            return True

        except Exception as e:
            self._state = ProcessState.ERROR
            self._logger.error(f"进程启动失败: {e}")
            return False

    def _run_target(self, args: tuple, kwargs: dict) -> None:
        """进程目标函数"""
        try:
            # 子进程入口
            if self.config.enable_ipc:
                # 设置信号处理
                import signal

                signal.signal(signal.SIGTERM, self._handle_signal)
                signal.signal(signal.SIGINT, self._handle_signal)

            # 执行目标函数
            self.config.target(*args, **kwargs)

        except Exception as e:
            self._logger.error(f"进程执行错误: {e}")

    def _handle_signal(self, signum, frame) -> None:
        """处理信号"""
        self._logger.info(f"收到信号 {signum}，准备关闭")
        self._running = False

    def _recv_messages(self) -> None:
        """接收消息（子进程内）"""
        while self._running:
            try:
                if self._recv_queue and not self._recv_queue.empty():
                    message = self._recv_queue.get(timeout=0.1)
                    self._handle_message(message)
            except Exception:
                pass

    def _handle_message(self, message: dict[str, Any]) -> None:
        """处理消息"""
        msg_type = message.get("type")
        if msg_type in self._message_handlers:
            handler = self._message_handlers[msg_type]
            try:
                handler(message)
            except Exception as e:
                self._logger.error(f"消息处理错误: {e}")

    def send_message(self, message: dict[str, Any]) -> bool:
        """
        发送消息到进程

        Args:
            message: 消息字典

        Returns:
            是否发送成功
        """
        if not self.is_alive or not self._send_queue:
            return False

        try:
            self._send_queue.put(message)
            return True
        except Exception:
            return False

    def register_handler(self, message_type: str, handler: Callable) -> None:
        """注册消息处理器"""
        self._message_handlers[message_type] = handler

    def stop(self, timeout: float = None) -> bool:
        """
        停止进程

        Args:
            timeout: 超时时间

        Returns:
            是否成功停止
        """
        timeout = timeout or self.config.shutdown_timeout

        if self._state == ProcessState.STOPPED:
            return True

        self._state = ProcessState.STOPPING
        self._running = False

        try:
            if self._process and self._process.is_alive():
                # 发送停止信号
                self._process.terminate()
                self._process.join(timeout=timeout)

                if self._process.is_alive():
                    self._logger.warning("进程未响应，强制终止")
                    self._process.kill()
                    self._process.join(timeout=5)

            self._state = ProcessState.STOPPED
            self._logger.info(f"进程 {self.config.name} 已停止")
            return True

        except Exception as e:
            self._logger.error(f"停止进程失败: {e}")
            self._state = ProcessState.ERROR
            return False

    def get_info(self) -> ProcessInfo:
        """获取进程信息"""
        return ProcessInfo(
            pid=self.pid or 0,
            name=self.config.name,
            state=self._state,
            started_at=self._start_time or time.time(),
        )

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()


class ProcessCapsuleManager:
    """
    进程胶囊管理器

    管理多个进程胶囊。
    """

    def __init__(self):
        self._capsules: dict[str, ProcessCapsule] = {}
        self._logger = logging.getLogger("ProcessManager")

    def add(self, name: str, capsule: ProcessCapsule) -> None:
        """添加胶囊"""
        self._capsules[name] = capsule

    def remove(self, name: str) -> bool:
        """移除胶囊"""
        if name in self._capsules:
            capsule = self._capsules[name]
            capsule.stop()
            del self._capsules[name]
            return True
        return False

    def get(self, name: str) -> ProcessCapsule | None:
        """获取胶囊"""
        return self._capsules.get(name)

    def start_all(self) -> int:
        """启动所有胶囊"""
        count = 0
        for capsule in self._capsules.values():
            if capsule.start():
                count += 1
        return count

    def stop_all(self, timeout: float = None) -> int:
        """停止所有胶囊"""
        count = 0
        for capsule in self._capsules.values():
            if capsule.stop(timeout):
                count += 1
        return count

    def get_all_info(self) -> list[ProcessInfo]:
        """获取所有胶囊信息"""
        return [capsule.get_info() for capsule in self._capsules.values()]

    def __len__(self) -> int:
        return len(self._capsules)

    def __contains__(self, name: str) -> bool:
        return name in self._capsules
