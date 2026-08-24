"""
L-Rule: 规则生成层模块
"""


def __getattr__(name):
    if name == "ConstraintValidator":
        from .constraint import ConstraintValidator

        return ConstraintValidator
    elif name == "Constraint":
        from .constraint import Constraint

        return Constraint
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
