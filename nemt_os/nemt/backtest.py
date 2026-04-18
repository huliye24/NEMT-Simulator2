# -*- coding: utf-8 -*-
"""
NEMT Backtest Engine
Event-driven backtesting loop
"""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from pathlib import Path

from .market import MarketLayer, MarketState
from .data_layer import DataLayer
from .signal_layer import SignalLayer, Signal
from .strategy import Strategy, StrategyPool, create_default_pool, StrategyStatus
from .execution import ExecutionLayer, OrderSide
from .risk import RiskLayer, RiskMode
from .brain import BrainLayer, BrainController, AllocationMode
from .evolution import EvolutionLayer
from .dashboard import Dashboard
from .config.settings import NEMTConfig


class NEMTEngine:
    """
    NEMT 交易引擎

    核心功能：
    1. 事件驱动回测循环
    2. 各层协调
    3. 状态管理
    """

    def __init__(self, config: NEMTConfig = None):
        self.config = config or NEMTConfig()

        # 各层组件
        self.market: Optional[MarketLayer] = None
        self.data_layer: Optional[DataLayer] = None
        self.signal_layer: Optional[SignalLayer] = None
        self.strategy_pool: Optional[StrategyPool] = None
        self.execution: Optional[ExecutionLayer] = None
        self.risk: Optional[RiskLayer] = None
        self.brain: Optional[BrainLayer] = None
        self.brain_controller: Optional[BrainController] = None
        self.evolution: Optional[EvolutionLayer] = None
        self.dashboard: Optional[Dashboard] = None

        # 状态
        self.is_running: bool = False
        self.current_bar_idx: int = 0
        self.symbol: str = "BTC/USDT"

        # 当前仓位
        self.current_position: float = 0.0  # -1 to 1

        # 初始化
        self._init_components()

    def _init_components(self):
        """初始化所有组件"""
        # 创建策略池
        self.strategy_pool = create_default_pool()

        # 创建执行层
        self.execution = ExecutionLayer(
            initial_capital=self.config.backtest.initial_capital,
            slippage_bps=self.config.backtest.slippage_bps,
            commission_bps=self.config.backtest.commission_bps
        )

        # 创建风控层
        self.risk = RiskLayer(
            max_drawdown_pct=self.config.risk.max_drawdown_pct * 100,
            daily_loss_limit_pct=self.config.risk.daily_loss_limit_pct * 100,
            strategy_exposure_cap=self.config.risk.strategy_exposure_cap * 100,
            market_exposure_cap=self.config.risk.market_exposure_cap * 100,
            caution_threshold=self.config.risk.caution_threshold * 100,
            defense_threshold=self.config.risk.defense_threshold * 100,
            shutdown_threshold=self.config.risk.shutdown_threshold * 100
        )
        self.risk.set_initial_capital(self.config.backtest.initial_capital)

        # 创建大脑层
        self.brain = BrainLayer(
            strategy_pool=self.strategy_pool,
            allocation_mode=AllocationMode.EQUAL if self.config.strategy_weight.equal_weight else AllocationMode.SHARPE_WEIGHTED,
            lookback_days=self.config.strategy_weight.lookback_days
        )
        self.brain_controller = BrainController(self.brain, self.risk)

        # 创建进化层
        self.evolution = EvolutionLayer(
            strategy_pool=self.strategy_pool,
            eval_frequency=self.config.evolution.eval_frequency,
            keep_best=self.config.evolution.keep_best,
            min_score_threshold=self.config.evolution.min_score_threshold,
            mutation_rate=self.config.evolution.mutation_rate
        )

        # 创建信号层
        self.signal_layer = SignalLayer()

        # 创建控制台
        self.dashboard = Dashboard()

    def load_data(self, filepath: str, start_date: str = None, end_date: str = None):
        """加载数据"""
        # 创建市场层
        self.market = MarketLayer()
        self.market.load_data(filepath, start_date, end_date)

        # 创建数据层
        self.data_layer = DataLayer(self.market.data)

        print(f"\n{'='*60}")
        print("NEMT Quant Trading System Initialized")
        print(f"{'='*60}")
        print(f"Initial Capital: ${self.config.backtest.initial_capital:,.2f}")
        print(f"Strategies: {len(self.strategy_pool)}")
        print(f"Data Period: {len(self.market.data)} bars")
        print(f"{'='*60}\n")

    def run(self, verbose: bool = True) -> Dict:
        """
        运行回测

        Args:
            verbose: 是否输出详细信息

        Returns:
            回测结果
        """
        if self.data_layer is None:
            raise ValueError("请先加载数据")

        self.is_running = True
        self.data_layer.reset()

        print("\n开始回测...\n")

        # 主循环
        while self.is_running:
            # 获取当前K线
            bar = self.data_layer.get_current_bar()
            if bar is None:
                break

            # 处理当前bar
            self._process_bar(verbose)

            # 进化层tick
            self.evolution.tick()

            # 检查是否应该评估
            if self.evolution.should_evaluate():
                events = self.evolution.evaluate()
                if verbose and events:
                    for event in events:
                        print(f"  [EVOLVE] {event}")

            # 前进到下一个bar
            if not self.data_layer.advance():
                self.is_running = False

        # 回测结束
        return self._finalize()

    def _process_bar(self, verbose: bool = True):
        """处理单个K线"""
        bar = self.data_layer.get_current_bar()
        timestamp = self.data_layer.get_timestamp()

        # 获取数据
        closes = self.data_layer.get_close_prices(100)
        highs = self.data_layer.get_highs(100)
        lows = self.data_layer.get_lows(100)
        volumes = self.data_layer.get_volumes(100)

        if len(closes) < 50:
            return

        current_price = closes[-1]

        # === 1. 市场感知 ===
        market_state = self.market.detect_regime(lookback=20)

        # === 2. 信号生成 ===
        signals = self.signal_layer.generate_all_signals(
            closes, highs, lows, volumes, current_price, timestamp
        )

        # === 3. 策略生成信号 ===
        strategy_signals = []
        for strategy in self.strategy_pool.get_active_strategies():
            signal = strategy.generate_signal(closes, highs, lows, volumes)
            strategy_signals.append(signal)

            # 更新策略表现
            if self.current_position != 0:
                pnl = self.current_position * (current_price - closes[-2]) / closes[-2] * self.execution.get_position_value()
                strategy.update_performance(pnl)

        # === 4. 大脑决策 ===
        combined_signal, decisions = self.brain_controller.make_decision(
            strategy_signals,
            self.signal_layer.indicators_cache
        )

        # === 5. 风控检查 ===
        approved, reason = self.risk.check_order(
            proposed_position=abs(combined_signal),
            strategy_name="combined"
        )

        if not approved:
            combined_signal = 0

        # 应用风控仓位限制
        combined_signal *= self.risk.get_position_multiplier()

        # === 6. 执行交易 ===
        self._execute_signal(combined_signal, current_price, timestamp)

        # === 7. 更新状态 ===
        equity = self.execution.get_equity()
        self.risk.update_equity(equity)
        self.execution.update_prices({self.symbol: current_price})

        # === 8. 记录数据 ===
        self.dashboard.record_equity(equity, timestamp)

        # 记录策略表现
        for strategy in self.strategy_pool.strategies:
            pnl = strategy.metrics.total_pnl if strategy.metrics else 0
            self.dashboard.record_strategy_performance(strategy.name, pnl)

        # 更新控制台指标
        self.dashboard.update_metrics(
            total_pnl=self.execution.get_total_pnl(),
            total_trades=self.execution.total_trades,
            win_rate=self.execution.get_win_rate(),
            max_drawdown=self.risk.metrics.max_drawdown,
            profit_factor=self.execution.get_profit_factor()
        )

        # 更新系统状态
        self.dashboard.update_system_status(self.brain.get_state_report())

        # 打印进度
        if verbose and self.current_bar_idx % 50 == 0:
            self.dashboard.print_progress(
                self.current_bar_idx,
                len(self.data_layer),
                f"市场: {market_state.value}"
            )

        self.current_bar_idx += 1

    def _execute_signal(self, signal: float, price: float, timestamp: datetime):
        """
        执行信号

        Args:
            signal: 信号 (-1 to 1)
            price: 当前价格
            timestamp: 时间戳
        """
        # 信号阈值
        signal_threshold = 0.2

        # 当前目标仓位
        target_position = signal  # -1 to 1

        # 如果仓位变化超过阈值，执行交易
        if abs(target_position - self.current_position) > signal_threshold:
            if target_position > self.current_position:
                # 做多
                if self.current_position < 0:
                    # 先平空
                    self.execution.close_position(self.symbol, exit_price=price, timestamp=timestamp)

                # 开多
                position_value = self.execution.get_equity() * abs(target_position)
                quantity = position_value / price

                order = self.execution.create_order(
                    side=OrderSide.BUY,
                    symbol=self.symbol,
                    quantity=quantity,
                    price=price
                )
                self.execution.execute_order(order, price, timestamp)
                self.current_position = target_position

            elif target_position < self.current_position:
                # 做空或平仓
                if self.current_position > 0:
                    # 先平多
                    self.execution.close_position(self.symbol, exit_price=price, timestamp=timestamp)

                # 如果信号是做空
                if target_position < 0:
                    position_value = self.execution.get_equity() * abs(target_position)
                    quantity = position_value / price

                    order = self.execution.create_order(
                        side=OrderSide.SELL,
                        symbol=self.symbol,
                        quantity=quantity,
                        price=price
                    )
                    self.execution.execute_order(order, price, timestamp)

                self.current_position = target_position

        # 检查风控关机
        if self.risk.should_close_all() and self.current_position != 0:
            self.execution.close_position(self.symbol, exit_price=price, timestamp=timestamp)
            self.current_position = 0

    def _finalize(self) -> Dict:
        """回测结束，汇总结果"""
        print("\n\n回测完成!")

        # 关闭所有仓位
        if self.current_position != 0:
            bar = self.data_layer.get_current_bar()
            self.execution.close_position(self.symbol, exit_price=bar.close if bar else 0)

        # 汇总结果
        results = {
            'initial_capital': self.config.backtest.initial_capital,
            'final_equity': self.execution.get_equity(),
            'total_pnl': self.execution.get_total_pnl(),
            'return_pct': self.execution.get_return_percent(),
            'max_drawdown': self.risk.metrics.max_drawdown,
            'sharpe_ratio': self.dashboard.metrics.sharpe_ratio,
            'total_trades': self.execution.total_trades,
            'win_rate': self.execution.get_win_rate(),
            'profit_factor': self.execution.get_profit_factor(),
            'bars': self.current_bar_idx,
            'strategies': len(self.strategy_pool),
            'evolution_report': self.evolution.get_evolution_report()
        }

        # 打印汇总
        self.dashboard.print_summary()

        # 保存结果
        self.dashboard.save_results()
        self.dashboard.save_report()

        # 绘制图表
        self.dashboard.plot_equity_curve()
        self.dashboard.plot_strategy_comparison()

        return results


def run_backtest(
    data_path: str,
    initial_capital: float = 10000,
    start_date: str = None,
    end_date: str = None,
    config_path: str = None
) -> Dict:
    """
    运行回测的便捷函数

    Args:
        data_path: 数据文件路径
        initial_capital: 初始资金
        start_date: 开始日期
        end_date: 结束日期
        config_path: 配置文件路径

    Returns:
        回测结果
    """
    # 加载配置
    if config_path and Path(config_path).exists():
        config = NEMTConfig.from_yaml(config_path)
    else:
        config = NEMTConfig()
        config.backtest.initial_capital = initial_capital

    # 创建引擎
    engine = NEMTEngine(config)

    # 加载数据
    engine.load_data(data_path, start_date, end_date)

    # 运行回测
    return engine.run(verbose=True)


if __name__ == "__main__":
    # 默认回测
    results = run_backtest(
        data_path="matlab_data/BTC_1h.csv",
        initial_capital=10000
    )

    print("\n最终结果:")
    for key, value in results.items():
        print(f"  {key}: {value}")
