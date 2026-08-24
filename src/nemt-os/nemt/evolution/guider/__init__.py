"""
L-Guide: 开发者引导者层模块
"""


def __getattr__(name):
    if name == "EvolutionGuider":
        from .guider import EvolutionGuider

        return EvolutionGuider
    elif name == "EvolutionDirection":
        from .guider import EvolutionDirection

        return EvolutionDirection
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
