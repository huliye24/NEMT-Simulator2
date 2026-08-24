"""
NEMTEngine - NEMT 核心引擎

整合所有胶囊，统一管理回测流程。
"""

from typing import Dict, List, Any, Optional
import time as time_module

from nemt.core.config_center import ConfigCenter
from nemt.core.event_bus import EventBus
from nemt.core.capsule_manager import CapsuleManager
from nemt.core.capsule import ModuleCapsule
from nemt.core.market_capsule import MarketCapsule
from nemt.core.signal_capsule import SignalCapsule
from nemt.core.risk_capsule import RiskCapsule
from nemt.core.execution_capsule import ExecutionCapsule
from nemt.core.dashboard_capsule import DashboardCapsule
from nemt.core.brain_capsule import BrainCapsule
from nemt.core.monitor_capsule import MonitorCapsule
from nemt.core.phase_capsule import PhaseStateMachineCapsule
from nemt.core.position_capsule import PositionCapsule

__all__ = ["NEMTEngine", "create_engine"]


class NEMTEngine:
    """
    NEMT 核心引擎

    整合所有胶囊，提供统一的回测接口。

    示例:
    ```python
    engine = NEMTEngine()
    engine.setup()
    engine.load_data('BTC', test_data)
    results = engine.run()
    print(engine.generate_report(results))
    ```
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        初始化引擎

        Args:
            config_path: 配置文件路径
        """
        # 核心组件
        self.config = ConfigCenter()
        self.event_bus = EventBus()
        self.manager = CapsuleManager(self.event_bus, self.config)

        # 胶囊引用
        self._capsules: Dict[str, ModuleCapsule] = {}

        # 运行时状态
        self._is_running = False
        self._is_paused = False
        self._start_time: Optional[float] = None
        self._bar_count = 0

        # 加载配置
        if config_path:
            self.config.load(config_path)

    def setup(self) -> "NEMTEngine":
        """
        设置引擎 (链式调用)

        Returns:
            self
        """
        # 注册所有胶囊
        self._register_all_capsules()
        return self

    def _register_all_capsules(self) -> None:
        """注册所有胶囊"""
        # 市场胶囊
        market = MarketCapsule()
        self.register_capsule(market)

        # 信号胶囊
        signal = SignalCapsule()
        self.register_capsule(signal)

        # 风控胶囊
        risk = RiskCapsule()
        self.register_capsule(risk)

        # 执行胶囊
        execution = ExecutionCapsule()
        self.register_capsule(execution)

        # 仪表板胶囊
        dashboard = DashboardCapsule()
        self.register_capsule(dashboard)

        # 策略大脑胶囊
        brain = BrainCapsule()
        self.register_capsule(brain)

        # 监控胶囊
        monitor = MonitorCapsule()
        self.register_capsule(monitor)

        # 阶段状态机胶囊
        phase = PhaseStateMachineCapsule()
        self.register_capsule(phase)

        # 仓位管理胶囊
        position = PositionCapsule()
        self.register_capsule(position)

    def register_capsule(self, capsule: ModuleCapsule) -> "NEMTEngine":
        """
        注册胶囊 (链式调用)

        Args:
            capsule: 胶囊实例

        Returns:
            self
        """
        self._capsules[capsule.capsule_id] = capsule
        self.manager.register(capsule)
        return self

    def get_capsule(self, capsule_id: str) -> Optional[ModuleCapsule]:
        """
        获取胶囊

        Args:
            capsule_id: 胶囊 ID

        Returns:
            胶囊实例
        """
        return self._capsules.get(capsule_id)

    def load_data(self, symbol: str, data: List[Dict[str, Any]]) -> "NEMTEngine":
        """
        加载数据 (链式调用)

        Args:
            symbol: 交易品种
            data: K线数据

        Returns:
            self
        """
        market = self.get_capsule("market")
        if market:
            market.load_data(symbol, data)
        return self

    def run(self) -> Dict[str, Any]:
        """
        运行回测

        Returns:
            回测结果
        """
        # 启动胶囊
        self.manager.start_all()
        self._is_running = True
        self._start_time = time_module.time()

        # 获取市场胶囊
        market = self.get_capsule("market")
        if market:
            market.start_backtest()

        # 主循环
        try:
            while self._is_running and market:
                # 处理暂停
                while self._is_paused and self._is_running:
                    time_module.sleep(0.01)

                # 获取下一个 bar
                if not market.next_bar():
                    break

                self._bar_count += 1

                # 每 100 个 bar 输出进度
                if self._bar_count % 100 == 0:
                    print(f"进度: {self._bar_count} bars")

        except KeyboardInterrupt:
            print("收到中断信号")
        finally:
            self._shutdown()

        # 收集结果
        results = self._collect_results()

        return results

    def pause(self) -> None:
        """暂停回测"""
        self._is_paused = True

    def resume(self) -> None:
        """继续回测"""
        self._is_paused = False

    def stop(self) -> None:
        """停止回测"""
        self._is_running = False

    def _shutdown(self) -> None:
        """关闭引擎"""
        market = self.get_capsule("market")
        if market:
            market.stop_backtest()

        self.manager.stop_all()
        self._is_running = False

        elapsed = time_module.time() - self._start_time if self._start_time else 0
        print(f"运行时长: {elapsed:.2f}s, 处理 bars: {self._bar_count}")

    def _collect_results(self) -> Dict[str, Any]:
        """收集回测结果"""
        results = {
            "bars": self._bar_count,
            "elapsed": time_module.time() - self._start_time if self._start_time else 0,
            "capsules": {},
        }

        for capsule_id, capsule in self._capsules.items():
            try:
                results["capsules"][capsule_id] = capsule.exec()
            except Exception as e:
                results["capsules"][capsule_id] = {"error": str(e)}

        return results

    def generate_report(self, results: Optional[Dict[str, Any]] = None) -> str:
        """
        生成文本报告

        Args:
            results: 回测结果，默认使用最新结果

        Returns:
            报告文本
        """
        if results is None:
            results = self._collect_results()

        lines = []
        lines.append("=" * 60)
        lines.append("NEMT 回测报告")
        lines.append("=" * 60)
        lines.append(f"K线数量: {results.get('bars', 0)}")
        lines.append(f"运行时长: {results.get('elapsed', 0):.2f}s")
        lines.append("")

        # Dashboard 数据
        dashboard = results.get("capsules", {}).get("dashboard", {})
        if dashboard:
            lines.append("【交易统计】")
            lines.append(f"  当前权益: {dashboard.get('current_equity', 0):.2f}")
            lines.append(f"  总收益率: {dashboard.get('total_return', 0):.2%}")
            lines.append(f"  交易次数: {dashboard.get('trade_count', 0)}")
            lines.append(f"  胜率: {dashboard.get('win_rate', 0):.2%}")
            lines.append(f"  最大回撤: {dashboard.get('max_drawdown', 0):.2%}")
            lines.append("")

        # Signal 数据
        signal = results.get("capsules", {}).get("signal", {})
        if signal:
            lines.append("【信号统计】")
            signals = signal.get("signals", {})
            for sig_type, count in signals.items():
                lines.append(f"  {sig_type}: {count}")
            lines.append("")

        lines.append("=" * 60)

        return "\n".join(lines)

    def __enter__(self) -> "NEMTEngine":
        """上下文管理器入口"""
        return self.setup()

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """上下文管理器出口"""
        if self._is_running:
            self._shutdown()


def create_engine(config_path: Optional[str] = None) -> NEMTEngine:
    """
    创建引擎的便捷函数

    Args:
        config_path: 配置文件路径

    Returns:
        配置好的引擎
    """
    return NEMTEngine(config_path).setup()
