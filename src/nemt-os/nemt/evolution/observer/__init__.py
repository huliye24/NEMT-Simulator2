"""
L-State: 状态管理层模块
"""


def __getattr__(name):
    if name == "StateObserver":
        from .observer import StateObserver

        return StateObserver
    elif name == "AnomalyDetector":
        from .observer import AnomalyDetector

        return AnomalyDetector
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
