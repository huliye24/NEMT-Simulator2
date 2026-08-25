"""
NEMT Engine Adapter
连接 FastAPI 与 NEMT Core Engine
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass

# 添加 NEMT OS 到路径
NEMT_OS_PATH = Path(__file__).parent.parent.parent / "nemt_os"
sys.path.insert(0, str(NEMT_OS_PATH))


@dataclass
class MarketState:
    """市场状态数据类"""
    symbol: str
    phase: str
    dci: float
    signal: str
    confidence: float
    price: float
    change24h: float


@dataclass
class AnalysisReport:
    """分析报告数据类"""
    symbol: str
    summary: str
    reasoning: List[str]
    recommendation: str
    confidence: float
    dci: float
    phase: str


class NEMTEngineAdapter:
    """NEMT Engine 适配器"""

    def __init__(self):
        self._engine_loaded = False
        self._mock_mode = True  # 暂时使用 Mock 模式
        self._load_engine()

    def _load_engine(self):
        """加载 NEMT Engine"""
        try:
            # 尝试导入 NEMT 模块
            from nemt.core.nls_solver import NLSSolver
            from nemt.core.phase_detector import PhaseDetector
            self.nls_solver = NLSSolver()
            self.phase_detector = PhaseDetector()
            self._engine_loaded = True
            self._mock_mode = False
            print("✅ NEMT Engine loaded successfully")
        except ImportError as e:
            print(f"⚠️  NEMT Engine not available: {e}")
            print("🔄 Running in MOCK mode")
            self._mock_mode = True

    def get_market_state(self, symbol: str = "BTCUSDT") -> MarketState:
        """获取市场状态"""
        if self._mock_mode:
            return self._get_mock_market_state(symbol)

        # 真实 NEMT Engine 调用
        # TODO: 实现真实的 NEMT 计算
        return self._get_mock_market_state(symbol)

    def _get_mock_market_state(self, symbol: str) -> MarketState:
        """Mock 市场状态"""
        import random

        phases = ["ACCUMULATION", "MARKUP", "DISTRIBUTION", "MARKDOWN"]
        signals = ["WAIT", "BUY", "SELL", "STRONG_BUY", "REDUCE"]

        # 根据 symbol 确定固定值（保持一致性）
        symbol_hash = sum(ord(c) for c in symbol) % 5
        phase = phases[symbol_hash % len(phases)]

        return MarketState(
            symbol=symbol,
            phase=phase,
            dci=round(50 + random.uniform(-20, 30), 2),
            signal=signals[symbol_hash % len(signals)],
            confidence=round(random.uniform(60, 90), 2),
            price=round(random.uniform(20000, 70000), 2),
            change24h=round(random.uniform(-5, 5), 2),
        )

    def get_analysis_report(self, symbol: str = "BTCUSDT") -> AnalysisReport:
        """获取分析报告"""
        if self._mock_mode:
            return self._get_mock_analysis_report(symbol)

        return self._get_mock_analysis_report(symbol)

    def _get_mock_analysis_report(self, symbol: str) -> AnalysisReport:
        """Mock 分析报告"""
        state = self._get_mock_market_state(symbol)

        phase_desc = {
            "ACCUMULATION": "积累阶段，等待突破",
            "MARKUP": "上涨阶段，趋势良好",
            "DISTRIBUTION": "派发阶段，注意风险",
            "MARKDOWN": "下跌阶段，保持谨慎",
        }

        return AnalysisReport(
            symbol=symbol,
            summary=f"{symbol} 当前处于 {state.phase} 阶段。DCI {state.dci} 显示{'强劲' if state.dci > 60 else '温和'}动能。",
            reasoning=[
                f"DCI {state.dci} 处于 {'HIGH' if state.dci > 60 else 'MEDIUM' if state.dci > 40 else 'LOW'} band",
                f"Phase {state.phase} 确认，{phase_desc.get(state.phase, '观望')}",
                "成交量与价格走势一致",
                "链上指标支持当前判断",
            ],
            recommendation=state.signal,
            confidence=state.confidence,
            dci=state.dci,
            phase=state.phase,
        )

    def get_simulation_signal(self, symbol: str = "BTCUSDT") -> Dict:
        """获取模拟交易信号"""
        state = self.get_market_state(symbol)

        return {
            "symbol": symbol,
            "signal": state.signal,
            "entry_price": state.price,
            "stop_loss": round(state.price * 0.95, 2),
            "take_profit": round(state.price * 1.1, 2),
            "confidence": state.confidence,
            "timestamp": "2026-08-25T10:00:00Z",
        }


# 全局适配器实例
adapter = NEMTEngineAdapter()
