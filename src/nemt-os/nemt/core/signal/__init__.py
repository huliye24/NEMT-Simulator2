"""
信号模块

导出所有信号相关的类和函数。
"""

from .signal_capsule import SignalCapsule, SignalType, TradingSignal

__all__ = ["SignalCapsule", "TradingSignal", "SignalType"]
