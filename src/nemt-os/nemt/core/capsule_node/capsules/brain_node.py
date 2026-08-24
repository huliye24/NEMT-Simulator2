"""
BrainNode - 决策大脑节点

基于 CapsuleNode 的决策大脑节点
"""

import threading
from datetime import datetime
from typing import Any

from nemt.core.capsule_node import (
    ConstraintSchema,
    FractalCapsuleNode,
    PortSchema,
)


class BrainNode(FractalCapsuleNode):
    """
    BrainNode - 决策大脑胶囊节点

    职责：
    - 接收信号和风险评估
    - 做最终交易决策
    - 协调各节点
    - 维护决策历史

    AI 可直接读取：
    - state: 当前状态
    - decisions: 决策历史
    - strategy_state: 策略状态
    """

    # ═══════════════════════════════════════════════════════════════════════════════
    # 节点身份
    # ═══════════════════════════════════════════════════════════════════════════════
    NODE_ID = "brain_node"
    NODE_NAME = "Decision Brain Node"
    NODE_VERSION = "1.0.0"

    # ═══════════════════════════════════════════════════════════════════════════════
    # 输入端口 Schema
    # ═══════════════════════════════════════════════════════════════════════════════
    INPUT_PORTS = [
        PortSchema(
            name="signal",
            data_type="object",
            required=True,
            description="Signal from signal_node",
            properties={
                "signal_id": {"type": "string"},
                "symbol": {"type": "string"},
                "direction": {"type": "string"},
                "confidence": {"type": "number"},
            },
            required_fields=["signal_id", "symbol", "direction"],
        ),
        PortSchema(
            name="risk_evaluation",
            data_type="object",
            required=True,
            description="Risk evaluation result",
            properties={
                "approved": {"type": "boolean"},
                "approved_size": {"type": "number"},
                "risk_score": {"type": "number"},
            },
            required_fields=["approved"],
        ),
        PortSchema(
            name="market_phase",
            data_type="string",
            required=False,
            description="Current market phase",
            enum_values=["UNKNOWN", "TREND_UP", "TREND_DOWN", "RANGE", "VOLATILE"],
        ),
    ]

    # ═══════════════════════════════════════════════════════════════════════════════
    # 输出端口 Schema
    # ═══════════════════════════════════════════════════════════════════════════════
    OUTPUT_PORTS = [
        PortSchema(
            name="decision",
            data_type="object",
            required=True,
            description="Final trading decision",
            properties={
                "decision_id": {"type": "string"},
                "action": {"type": "string", "enum": ["EXECUTE", "SKIP", "WAIT"]},
                "symbol": {"type": "string"},
                "direction": {"type": "string"},
                "size": {"type": "number"},
                "reason": {"type": "string"},
                "timestamp": {"type": "integer"},
            },
            required_fields=["decision_id", "action", "symbol"],
        ),
        PortSchema(
            name="strategy_state",
            data_type="object",
            required=True,
            description="Current strategy state",
            properties={
                "total_decisions": {"type": "integer"},
                "executions": {"type": "integer"},
                "skips": {"type": "integer"},
                "success_rate": {"type": "number"},
            },
        ),
    ]

    # ═══════════════════════════════════════════════════════════════════════════════
    # 约束 Schema
    # ═══════════════════════════════════════════════════════════════════════════════
    CONSTRAINTS = [
        ConstraintSchema(
            name="min_confidence_threshold",
            constraint_type="validation",
            value=0.65,
            description="Minimum combined confidence",
            min_value=0,
            max_value=1,
        ),
        ConstraintSchema(
            name="max_risk_score",
            constraint_type="validation",
            value=0.5,
            description="Maximum risk score to proceed",
            min_value=0,
            max_value=1,
        ),
        ConstraintSchema(
            name="consecutive_skips_limit",
            constraint_type="runtime",
            value=5,
            description="Max consecutive skips before forcing trade",
            min_value=1,
            max_value=20,
        ),
        ConstraintSchema(
            name="decision_cooldown_ms",
            constraint_type="runtime",
            value=1000,
            description="Minimum time between decisions for same symbol",
            min_value=100,
            max_value=60000,
        ),
    ]

    # ═══════════════════════════════════════════════════════════════════════════════
    # 初始化
    # ═══════════════════════════════════════════════════════════════════════════════

    def __init__(self, node_id: str = "brain_node"):
        super().__init__(node_id)

        # 决策状态
        self._decisions: list[dict] = []
        self._consecutive_skips: dict[str, int] = {}
        self._last_decision_time: dict[str, float] = {}
        self._lock = threading.Lock()

        # 统计
        self._total_decisions = 0
        self._executions = 0
        self._skips = 0

    # ═══════════════════════════════════════════════════════════════════════════════
    # 处理实现
    # ═══════════════════════════════════════════════════════════════════════════════

    def _process_impl(self, inputs: dict[str, Any]) -> dict[str, Any]:
        """
        决策处理

        Args:
            inputs = {
                "signal": {...},
                "risk_evaluation": {...},
                "market_phase": "RANGE"
            }

        Returns:
            {
                "decision": {...},
                "strategy_state": {...}
            }
        """
        signal = inputs.get("signal")
        risk_eval = inputs.get("risk_evaluation", {})
        market_phase = inputs.get("market_phase", "UNKNOWN")

        if not signal:
            raise ValueError("Missing required input: signal")

        symbol = signal["symbol"]
        decision_id = f"dec_{datetime.now().timestamp()}"

        # 检查冷却时间
        if self._is_in_cooldown(symbol):
            decision = {
                "decision_id": decision_id,
                "action": "WAIT",
                "symbol": symbol,
                "direction": signal.get("direction"),
                "size": 0,
                "reason": "Cooldown period",
                "timestamp": int(datetime.now().timestamp()),
            }
            return self._finalize_decision(decision, inputs)

        # 检查是否批准
        if not risk_eval.get("approved", False):
            self._consecutive_skips[symbol] = self._consecutive_skips.get(symbol, 0) + 1
            decision = {
                "decision_id": decision_id,
                "action": "SKIP",
                "symbol": symbol,
                "direction": signal.get("direction"),
                "size": 0,
                "reason": f"Risk rejected: {risk_eval.get('risk_rejection', {}).get('reason', 'Unknown')}",
                "timestamp": int(datetime.now().timestamp()),
            }
            return self._finalize_decision(decision, inputs)

        # 计算综合置信度
        signal_confidence = signal.get("confidence", 0)
        risk_score = risk_eval.get("risk_score", 1)
        combined_confidence = signal_confidence * (1 - risk_score)

        # 检查阈值
        min_confidence = self.get_config("min_confidence_threshold", 0.65)
        max_risk = self.get_config("max_risk_score", 0.5)

        if combined_confidence < min_confidence:
            self._consecutive_skips[symbol] = self._consecutive_skips.get(symbol, 0) + 1
            decision = {
                "decision_id": decision_id,
                "action": "SKIP",
                "symbol": symbol,
                "direction": signal.get("direction"),
                "size": 0,
                "reason": f"Combined confidence {combined_confidence:.2f} below threshold {min_confidence}",
                "timestamp": int(datetime.now().timestamp()),
            }
        elif risk_score > max_risk:
            self._consecutive_skips[symbol] = self._consecutive_skips.get(symbol, 0) + 1
            decision = {
                "decision_id": decision_id,
                "action": "SKIP",
                "symbol": symbol,
                "direction": signal.get("direction"),
                "size": 0,
                "reason": f"Risk score {risk_score:.2f} above threshold {max_risk}",
                "timestamp": int(datetime.now().timestamp()),
            }
        else:
            # 执行交易
            self._consecutive_skips[symbol] = 0
            approved_size = risk_eval.get("approved_size", 0)

            decision = {
                "decision_id": decision_id,
                "action": "EXECUTE",
                "symbol": symbol,
                "direction": signal.get("direction"),
                "size": approved_size,
                "entry_price": signal.get("entry_price"),
                "stop_loss": signal.get("stop_loss"),
                "take_profit": signal.get("take_profit"),
                "reason": f"Approved: confidence={combined_confidence:.2f}, risk={risk_score:.2f}",
                "timestamp": int(datetime.now().timestamp()),
            }

        return self._finalize_decision(decision, inputs)

    def _is_in_cooldown(self, symbol: str) -> bool:
        """检查是否在冷却期"""
        if symbol not in self._last_decision_time:
            return False

        import time

        cooldown_ms = self.get_config("decision_cooldown_ms", 1000)
        elapsed = (time.time() - self._last_decision_time[symbol]) * 1000

        return elapsed < cooldown_ms

    def _finalize_decision(self, decision: dict, inputs: dict) -> dict:
        """完成决策"""
        with self._lock:
            self._decisions.append(decision)
            self._total_decisions += 1

            if decision["action"] == "EXECUTE":
                self._executions += 1
            else:
                self._skips += 1

            import time

            self._last_decision_time[decision["symbol"]] = time.time()

            # 限制历史大小
            if len(self._decisions) > 1000:
                self._decisions = self._decisions[-500:]

        return {
            "decision": decision,
            "strategy_state": self._get_strategy_state(),
        }

    def _get_strategy_state(self) -> dict:
        """获取策略状态"""
        success_rate = self._executions / self._total_decisions if self._total_decisions > 0 else 0

        return {
            "total_decisions": self._total_decisions,
            "executions": self._executions,
            "skips": self._skips,
            "success_rate": round(success_rate, 4),
            "consecutive_skips": dict(self._consecutive_skips),
        }

    # ═══════════════════════════════════════════════════════════════════════════════
    # 五阶段实现
    # ═══════════════════════════════════════════════════════════════════════════════

    def _observe_phase_impl(self) -> dict[str, Any]:
        """观察阶段"""
        return {
            "node_id": self.NODE_ID,
            "phase": "observe",
            "timestamp": datetime.now().isoformat(),
            "inputs": {
                "signal": {"source": "signal_node"},
                "risk_evaluation": {"source": "risk_node"},
                "market_phase": {"source": "market_node"},
            },
            "outputs": {
                "decision": {"destination": "execution_node"},
                "strategy_state": {"destination": "monitor_node"},
            },
            "constraints": {
                "min_confidence_threshold": {"value": 0.65},
                "max_risk_score": {"value": 0.5},
            },
            "dependencies": ["signal_node", "risk_node", "market_node"],
            "risks": [
                {"type": "决策过慢", "mitigation": "冷却时间限制"},
                {"type": "过度交易", "mitigation": "高置信度阈值"},
            ],
        }

    def _design_phase_impl(self) -> dict[str, Any]:
        """设计阶段"""
        return {
            "node_id": self.NODE_ID,
            "phase": "design",
            "timestamp": datetime.now().isoformat(),
            "public_api": {
                "run(inputs)": "Make trading decision",
                "get_decisions(symbol)": "Get decisions for symbol",
                "get_strategy_state()": "Get current strategy state",
            },
            "internal_structure": {
                "_decisions": "List[Dict] - 决策历史",
                "_consecutive_skips": "Dict[str, int] - 连续跳过计数",
            },
            "event_contracts": {
                "publishes": ["brain.decision"],
                "subscribes": ["signal.generated", "risk.evaluated"],
            },
        }

    # ═══════════════════════════════════════════════════════════════════════════════
    # 公开 API
    # ═══════════════════════════════════════════════════════════════════════════════

    def get_decisions(self, symbol: str | None = None) -> list[dict]:
        """获取决策历史"""
        with self._lock:
            if symbol:
                return [d for d in self._decisions if d["symbol"] == symbol]
            return self._decisions.copy()

    def get_strategy_state(self) -> dict:
        """获取策略状态"""
        return self._get_strategy_state()
