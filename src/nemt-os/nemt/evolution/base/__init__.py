"""
L-Base: 基础框架层模块
"""


# 延迟导入避免循环依赖
def __getattr__(name):
    if name == "MetaRule":
        from .meta_rule_engine import MetaRule

        return MetaRule
    elif name == "MetaRuleEngine":
        from .meta_rule_engine import MetaRuleEngine

        return MetaRuleEngine
    elif name == "RuleType":
        from .meta_rule_engine import RuleType

        return RuleType
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
