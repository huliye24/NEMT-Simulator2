"""
L-State: 状态管理层模块
"""


def __getattr__(name):
    if name == "StateUniverse":
        from .state_universe import StateUniverse

        return StateUniverse
    elif name == "StateEntity":
        from .state_universe import StateEntity

        return StateEntity
    elif name == "EntityType":
        from .state_universe import EntityType

        return EntityType
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
