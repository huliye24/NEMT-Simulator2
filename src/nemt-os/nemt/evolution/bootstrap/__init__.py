"""
L-Boot: 系统自举层模块
"""


def __getattr__(name):
    if name == "BootstrapEngine":
        from .bootstrap import BootstrapEngine

        return BootstrapEngine
    elif name == "BootstrapSeed":
        from .bootstrap import BootstrapSeed

        return BootstrapSeed
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
