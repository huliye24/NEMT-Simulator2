"""
L-Evolve: 自演化层模块
"""


def __getattr__(name):
    if name == "SelfOptimizeEngine":
        from .self_optimize import SelfOptimizeEngine

        return SelfOptimizeEngine
    elif name == "Bottleneck":
        from .self_optimize import Bottleneck

        return Bottleneck
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
