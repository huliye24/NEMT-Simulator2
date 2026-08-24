"""
Container Module - 容器化模块

提供进程隔离、IPC 通信等容器化能力。
"""

from nemt.container.ipc import (
    IPCBus,
    IPCBusType,
    IPCMessage,
    RPCClient,
    RPCServer,
)
from nemt.container.process_capsule import (
    ProcessCapsule,
    ProcessCapsuleManager,
    ProcessConfig,
    ProcessInfo,
    ProcessState,
)
from nemt.container.process_manager import (
    ProcessInfo as ProcessInfoData,
)
from nemt.container.process_manager import (
    ProcessManager,
)
from nemt.container.process_manager import (
    ProcessState as PMState,
)

__all__ = [
    # 进程胶囊
    "ProcessCapsule",
    "ProcessConfig",
    "ProcessState",
    "ProcessInfo",
    "ProcessCapsuleManager",
    # IPC
    "IPCMessage",
    "IPCBus",
    "IPCBusType",
    "RPCClient",
    "RPCServer",
    # 进程管理器
    "ProcessManager",
    "PMState",
    "ProcessInfoData",
]
