"""
L-Evolve: 自演化层模块
"""


def __getattr__(name):
    if name == "SelfRepairEngine":
        from .self_repair import SelfRepairEngine

        return SelfRepairEngine
    elif name == "Fault":
        from .self_repair import Fault

        return Fault
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
