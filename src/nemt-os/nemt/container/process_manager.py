"""
ProcessManager - 进程管理器

管理 Capsule 进程的完整生命周期。
"""

import logging
import os
import subprocess
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

import psutil

__all__ = [
    "ProcessState",
    "ProcessInfo",
    "ProcessManager",
]


class ProcessState(Enum):
    """进程状态"""

    PENDING = "pending"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    FAILED = "failed"
    RESTARTING = "restarting"


@dataclass
class ProcessInfo:
    """进程信息"""

    pid: int
    name: str
    state: ProcessState
    start_time: float
    restart_count: int = 0
    last_restart: float = 0
    cpu_percent: float = 0
    memory_mb: float = 0
    metadata: dict[str, Any] = field(default_factory=dict)


class ProcessManager:
    """
    进程管理器

    示例:
    ```python
    manager = ProcessManager()

    # 启动进程
    pid = manager.start("my_process", ["python", "main.py"])

    # 获取状态
    info = manager.get_info(pid)
    print(f"State: {info.state}")

    # 停止进程
    manager.stop(pid)

    # 重启进程
    manager.restart(pid)
    ```
    """

    def __init__(
        self,
        max_restart: int = 3,
        restart_window: float = 60.0,
        health_check_interval: float = 10.0,
    ):
        self.max_restart = max_restart
        self.restart_window = restart_window
        self.health_check_interval = health_check_interval

        self._processes: dict[int, dict[str, Any]] = {}
        self._lock = threading.RLock()
        self._logger = logging.getLogger("ProcessManager")

        # 启动健康检查线程
        self._running = True
        self._health_thread = threading.Thread(target=self._health_check_loop, daemon=True)
        self._health_thread.start()

    def start(
        self,
        name: str,
        command: list[str],
        env: dict[str, str] = None,
        cwd: str = None,
        on_exit: Callable = None,
    ) -> int:
        """启动进程"""
        with self._lock:
            # 准备环境
            process_env = os.environ.copy()
            if env:
                process_env.update(env)

            try:
                # 启动进程
                process = subprocess.Popen(
                    command,
                    env=process_env,
                    cwd=cwd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    stdin=subprocess.DEVNULL,
                )

                # 记录进程信息
                self._processes[process.pid] = {
                    "name": name,
                    "process": process,
                    "state": ProcessState.RUNNING,
                    "start_time": time.time(),
                    "restart_count": 0,
                    "last_restart": 0,
                    "on_exit": on_exit,
                }

                self._logger.info(f"启动进程: {name} (PID: {process.pid})")
                return process.pid

            except Exception as e:
                self._logger.error(f"启动进程失败: {name}: {e}")
                raise

    def stop(self, pid: int, timeout: float = 10.0) -> bool:
        """停止进程"""
        with self._lock:
            if pid not in self._processes:
                return False

            info = self._processes[pid]
            info["state"] = ProcessState.STOPPING
            process = info["process"]

        try:
            # 发送 SIGTERM
            process.terminate()

            # 等待进程退出
            try:
                process.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                # 强制杀死
                process.kill()
                process.wait()

            with self._lock:
                self._processes[pid]["state"] = ProcessState.STOPPED
                del self._processes[pid]

            self._logger.info(f"停止进程: PID {pid}")
            return True

        except Exception as e:
            self._logger.error(f"停止进程失败: PID {pid}: {e}")
            return False

    def restart(self, pid: int) -> bool:
        """重启进程"""
        with self._lock:
            if pid not in self._processes:
                return False

            info = self._processes[pid]
            name = info["name"]
            info["state"] = ProcessState.RESTARTING

        # 停止进程
        if not self.stop(pid):
            return False

        # 重启计数
        with self._lock:
            if pid in self._processes:
                info = self._processes[pid]
            else:
                return False

        info["restart_count"] += 1
        info["last_restart"] = time.time()

        self._logger.info(f"重启进程: {name} (重启次数: {info['restart_count']})")
        return True

    def get_info(self, pid: int) -> ProcessInfo | None:
        """获取进程信息"""
        with self._lock:
            if pid not in self._processes:
                return None

            info = self._processes[pid]
            process = info["process"]

            # 获取系统进程信息
            try:
                proc = psutil.Process(pid)
                cpu_percent = proc.cpu_percent(interval=0.1)
                memory_info = proc.memory_info()
                memory_mb = memory_info.rss / 1024 / 1024
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                cpu_percent = 0
                memory_mb = 0

            return ProcessInfo(
                pid=pid,
                name=info["name"],
                state=info["state"],
                start_time=info["start_time"],
                restart_count=info["restart_count"],
                last_restart=info["last_restart"],
                cpu_percent=cpu_percent,
                memory_mb=memory_mb,
            )

    def list_processes(self) -> list[ProcessInfo]:
        """列出所有进程"""
        with self._lock:
            pids = list(self._processes.keys())

        return [self.get_info(pid) for pid in pids if self.get_info(pid)]

    def stop_all(self, timeout: float = 10.0) -> int:
        """停止所有进程"""
        with self._lock:
            pids = list(self._processes.keys())

        count = 0
        for pid in pids:
            if self.stop(pid, timeout):
                count += 1

        return count

    def _health_check_loop(self) -> None:
        """健康检查循环"""
        while self._running:
            try:
                self._check_processes()
            except Exception as e:
                self._logger.error(f"健康检查异常: {e}")

            time.sleep(self.health_check_interval)

    def _check_processes(self) -> None:
        """检查进程状态"""
        with self._lock:
            pids = list(self._processes.keys())

        for pid in pids:
            try:
                # 检查进程是否存活
                proc = psutil.Process(pid)
                if not proc.is_running():
                    self._handle_process_exit(pid)
            except psutil.NoSuchProcess:
                self._handle_process_exit(pid)

    def _handle_process_exit(self, pid: int) -> None:
        """处理进程退出"""
        with self._lock:
            if pid not in self._processes:
                return

            info = self._processes[pid]
            name = info["name"]
            restart_count = info["restart_count"]

        # 检查是否需要重启
        if restart_count < self.max_restart:
            # 检查重启窗口
            now = time.time()
            if now - info["last_restart"] < self.restart_window or info["last_restart"] == 0:
                self._logger.warning(f"进程退出，准备重启: {name}")
                self.restart(pid)
            else:
                self._logger.error(f"进程退出次数过多，停止重启: {name}")
                with self._lock:
                    self._processes[pid]["state"] = ProcessState.FAILED
        else:
            self._logger.error(f"超过最大重启次数: {name}")
            with self._lock:
                self._processes[pid]["state"] = ProcessState.FAILED

        # 调用退出回调
        with self._lock:
            if pid in self._processes:
                on_exit = info.get("on_exit")
                if on_exit:
                    try:
                        on_exit(pid, info["state"])
                    except Exception as e:
                        self._logger.error(f"退出回调异常: {e}")

    def shutdown(self) -> None:
        """关闭管理器"""
        self._running = False
        self.stop_all()
        self._logger.info("进程管理器已关闭")
