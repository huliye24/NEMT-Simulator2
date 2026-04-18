"""
NEMT 控制台 (Dashboard)
可视化控制台，实时监控、性能展示、系统健康状态
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass
class PerformanceMetrics:
    """性能指标"""
    total_pnl: float = 0.0
    total_return: float = 0.0
    sharpe_ratio: float = 0.0
    max_drawdown: float = 0.0
    win_rate: float = 0.0
    profit_factor: float = 0.0
    total_trades: int = 0


class Dashboard:
    """
    控制台

    核心功能：
    1. 实时指标展示
    2. Equity Curve 绘制
    3. 策略表现表格
    4. 系统健康状态
    """

    def __init__(self):
        self.equity_curve: List[float] = []
        self.equity_timestamps: List[datetime] = []
        self.daily_returns: List[float] = []
        self.strategy_performances: Dict[str, List[float]] = {}
        self.system_status: Dict = {}

        # 性能指标
        self.metrics = PerformanceMetrics()

        # 输出目录
        self.output_dir = Path("output")
        self.output_dir.mkdir(exist_ok=True)

    def record_equity(self, equity: float, timestamp: datetime = None):
        """记录权益"""
        self.equity_curve.append(equity)
        self.equity_timestamps.append(timestamp or datetime.now())

    def record_daily_return(self, return_pct: float):
        """记录日收益率"""
        self.daily_returns.append(return_pct)

    def record_strategy_performance(self, strategy_name: str, pnl: float):
        """记录策略表现"""
        if strategy_name not in self.strategy_performances:
            self.strategy_performances[strategy_name] = []
        self.strategy_performances[strategy_name].append(pnl)

    def update_metrics(
        self,
        total_pnl: float,
        total_trades: int,
        win_rate: float,
        max_drawdown: float,
        profit_factor: float
    ):
        """更新性能指标"""
        self.metrics.total_pnl = total_pnl
        self.metrics.total_trades = total_trades
        self.metrics.win_rate = win_rate
        self.metrics.max_drawdown = max_drawdown
        self.metrics.profit_factor = profit_factor

        # 计算夏普比率
        if len(self.daily_returns) >= 2:
            returns_arr = np.array(self.daily_returns)
            if np.std(returns_arr) > 0:
                self.metrics.sharpe_ratio = np.mean(returns_arr) / np.std(returns_arr) * np.sqrt(252)

        # 计算总收益
        if len(self.equity_curve) >= 2:
            self.metrics.total_return = (self.equity_curve[-1] - self.equity_curve[0]) / self.equity_curve[0] * 100

    def update_system_status(self, status: Dict):
        """更新系统状态"""
        self.system_status = status

    def print_summary(self):
        """打印汇总信息"""
        print("\n" + "=" * 60)
        print("                    NEMT Performance Summary")
        print("=" * 60)

        print(f"\n[STAT] Total PnL: ${self.metrics.total_pnl:,.2f}")
        print(f"[STAT] Total Return: {self.metrics.total_return:.2f}%")
        print(f"[STAT] Max Drawdown: {self.metrics.max_drawdown:.2f}%")
        print(f"[STAT] Sharpe Ratio: {self.metrics.sharpe_ratio:.2f}")
        print(f"[STAT] Win Rate: {self.metrics.win_rate:.1f}%")
        print(f"[STAT] Profit Factor: {self.metrics.profit_factor:.2f}")
        print(f"[STAT] Total Trades: {self.metrics.total_trades}")

        print("\n" + "-" * 60)
        print("                    Strategy Performance")
        print("-" * 60)

        for name, pnl_list in self.strategy_performances.items():
            total = sum(pnl_list)
            count = len(pnl_list)
            avg = total / count if count > 0 else 0
            print(f"  {name:20s}: ${total:>10,.2f} ({count} trades, avg: ${avg:,.2f})")

        if self.system_status:
            print("\n" + "-" * 60)
            print("                    System Status")
            print("-" * 60)
            print(f"  Market State: {self.system_status.get('market_state', 'N/A')}")
            print(f"  Risk Mode: {self.system_status.get('risk_mode', 'N/A')}")
            print(f"  Active Strategies: {self.system_status.get('active_strategies', 0)}")

        print("\n" + "=" * 60)

    def print_progress(self, current: int, total: int, extra_info: str = ""):
        """打印进度"""
        pct = current / total * 100 if total > 0 else 0
        bar_len = 30
        filled = int(bar_len * current / total) if total > 0 else 0
        bar = "█" * filled + "░" * (bar_len - filled)

        equity = self.equity_curve[-1] if self.equity_curve else 0
        pnl = self.metrics.total_pnl

        info = f" | {extra_info}" if extra_info else ""
        print(f"\r[{bar}] {pct:5.1f}% | Equity: ${equity:,.0f} | PnL: ${pnl:,.0f}{info}", end='', flush=True)

    def save_results(self, filename: str = None):
        """保存结果"""
        if filename is None:
            filename = f"nemt_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # 保存Equity Curve
        if self.equity_curve:
            df = pd.DataFrame({
                'timestamp': self.equity_timestamps,
                'equity': self.equity_curve
            })
            equity_file = self.output_dir / f"{filename}_equity.csv"
            df.to_csv(equity_file, index=False)
            print(f"\n[OK] Equity curve saved: {equity_file}")

        # 保存策略表现
        if self.strategy_performances:
            # 填充列表到相同长度
            max_len = max(len(v) for v in self.strategy_performances.values()) if self.strategy_performances else 0
            padded_data = {k: v + [0] * (max_len - len(v)) for k, v in self.strategy_performances.items()}
            perf_df = pd.DataFrame(padded_data)
            perf_file = self.output_dir / f"{filename}_strategies.csv"
            perf_df.to_csv(perf_file, index=False)
            print(f"[OK] Strategy performance saved: {perf_file}")

    def plot_equity_curve(self, filename: str = None):
        """绘制权益曲线"""
        try:
            import matplotlib.pyplot as plt
            import matplotlib.dates as mdates

            if len(self.equity_curve) < 2:
                print("[WARN] Not enough data to plot")
                return

            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))

            # 权益曲线
            ax1.plot(self.equity_timestamps, self.equity_curve, 'b-', linewidth=1.5)
            ax1.fill_between(self.equity_timestamps, self.equity_curve, alpha=0.3)
            ax1.set_title('NEMT Equity Curve', fontsize=14, fontweight='bold')
            ax1.set_ylabel('Equity ($)')
            ax1.grid(True, alpha=0.3)
            ax1.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
            ax1.xaxis.set_major_locator(mdates.AutoDateLocator())

            # 回撤曲线
            equity_series = pd.Series(self.equity_curve)
            running_max = equity_series.expanding().max()
            drawdown = (equity_series - running_max) / running_max * 100

            ax2.fill_between(self.equity_timestamps, drawdown, 0, color='red', alpha=0.5)
            ax2.set_title('Drawdown', fontsize=12)
            ax2.set_ylabel('Drawdown (%)')
            ax2.set_xlabel('Date')
            ax2.grid(True, alpha=0.3)
            ax2.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
            ax2.xaxis.set_major_locator(mdates.AutoDateLocator())

            plt.tight_layout()

            if filename is None:
                filename = f"equity_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"

            filepath = self.output_dir / filename
            plt.savefig(filepath, dpi=150, bbox_inches='tight')
            print(f"✓ 权益曲线已保存: {filepath}")
            plt.close()

        except ImportError:
            print("[WARN] matplotlib is required for plotting")

    def plot_strategy_comparison(self, filename: str = None):
        """绘制策略对比图"""
        try:
            import matplotlib.pyplot as plt

            if not self.strategy_performances:
                return

            fig, ax = plt.subplots(figsize=(12, 6))

            for name, pnl_list in self.strategy_performances.items():
                cumulative = np.cumsum(pnl_list)
                ax.plot(cumulative, label=name, linewidth=1.5)

            ax.set_title('Strategy Performance Comparison', fontsize=14, fontweight='bold')
            ax.set_xlabel('Trade Number')
            ax.set_ylabel('Cumulative PnL ($)')
            ax.legend()
            ax.grid(True, alpha=0.3)

            if filename is None:
                filename = f"strategies_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"

            filepath = self.output_dir / filename
            plt.savefig(filepath, dpi=150, bbox_inches='tight')
            print(f"[OK] Strategy comparison chart saved: {filepath}")
            plt.close()

        except ImportError:
            print("[WARN] matplotlib is required for plotting")

    def generate_report(self) -> str:
        """生成报告"""
        report = []
        report.append("=" * 60)
        report.append("NEMT Quant Trading System - Backtest Report")
        report.append("=" * 60)
        report.append(f"\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Data Period: {len(self.equity_curve)} bars")

        report.append("\n" + "-" * 60)
        report.append("Performance Metrics")
        report.append("-" * 60)
        report.append(f"Total PnL: ${self.metrics.total_pnl:,.2f}")
        report.append(f"Total Return: {self.metrics.total_return:.2f}%")
        report.append(f"Max Drawdown: {self.metrics.max_drawdown:.2f}%")
        report.append(f"Sharpe Ratio: {self.metrics.sharpe_ratio:.2f}")
        report.append(f"Win Rate: {self.metrics.win_rate:.1f}%")
        report.append(f"Profit Factor: {self.metrics.profit_factor:.2f}")
        report.append(f"Total Trades: {self.metrics.total_trades}")

        if self.system_status:
            report.append("\n" + "-" * 60)
            report.append("System Status")
            report.append("-" * 60)
            report.append(f"Market State: {self.system_status.get('market_state', 'N/A')}")
            report.append(f"Risk Mode: {self.system_status.get('risk_mode', 'N/A')}")
            report.append(f"Active Strategies: {self.system_status.get('active_strategies', 0)}")

        report.append("\n" + "=" * 60)

        return "\n".join(report)

    def save_report(self, filename: str = None):
        """保存报告"""
        if filename is None:
            filename = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"

        filepath = self.output_dir / filename
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(self.generate_report())

        print(f"[OK] Report saved: {filepath}")

    def reset(self):
        """重置控制台"""
        self.equity_curve = []
        self.equity_timestamps = []
        self.daily_returns = []
        self.strategy_performances = {}
        self.system_status = {}
        self.metrics = PerformanceMetrics()
