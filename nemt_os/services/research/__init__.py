"""NEMT 研究服务 (canonical research path)。

主链路:
    NEMT 理论命题
      → 可观测变量        (variables.py)
      → BTC/Binance 数据  (data_sources.py / candles.py)
      → 实验事件检测      (events.py)
      → 统计验证          (stats.py)
      → 策略信号          (strategies.py)
      → 可信回测          (backtest.py)
      → 样本外验证        (validation.py)
      → 实验报告          (report.py / cli.py)
      → 模拟盘候选策略

本包为 canonical 主路径。仓库内其它历史实现
(nemt_core.py / nemt_signals.py / enhanced_phase_detector.py / quant-mvp 等)
均标记为 non-canonical，详见 docs/NEMT_REFACTOR_AUDIT.md。
"""

__version__ = "0.1.0"

__all__ = [
    "candles",
    "data_sources",
]
