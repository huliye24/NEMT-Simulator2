"""
NEMT 自演化系统核心模块

自演化系统分为五层:
- L-Base: 基础框架层
- L-State: 状态管理层
- L-Rule: 规则生成层
- L-Evolve: 自演化层
- L-Guide: 开发者引导者层
"""


def __getattr__(name):
    # 延迟导入避免循环依赖
    if name in ("MetaRule", "MetaRuleEngine", "RuleType"):
        from . import base

        return getattr(base, name)
    elif name in ("StateUniverse", "StateEntity", "EntityType"):
        from . import state_universe

        return getattr(state_universe, name)
    elif name in ("Constraint", "ConstraintValidator"):
        from . import constraint

        return getattr(constraint, name)
    elif name in ("EvolutionGuider", "EvolutionDirection"):
        from . import guider

        return getattr(guider, name)
    elif name in ("BootstrapEngine", "BootstrapSeed"):
        from . import bootstrap

        return getattr(bootstrap, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
