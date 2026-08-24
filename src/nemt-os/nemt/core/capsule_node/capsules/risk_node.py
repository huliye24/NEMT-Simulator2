"""
RiskNode - 风险管理节点

基于 CapsuleNode 的风险管理节点
"""

import threading
from datetime import datetime
from typing import Any

from nemt.core.capsule_node import (
    ConstraintSchema,
    FractalCapsuleNode,
    PortSchema,
)


class RiskNode(FractalCapsuleNode):
    """
    RiskNode - 风险管理胶囊节点

    职责：
    - 接收交易信号
    - 计算风险指标
    - 应用风险规则
    - 输出过滤后的信号或拒绝理由

    AI 可直接读取：
    - state: 当前状态
    - portfolio: 投资组合状态
    - risk_metrics: 风险指标
    """

    # ═══════════════════════════════════════════════════════════════════════════════
    # 节点身份
    # ═══════════════════════════════════════════════════════════════════════════════
    NODE_ID = "risk_node"
    NODE_NAME = "Risk Management Node"
    NODE_VERSION = "1.0.0"

    # ═══════════════════════════════════════════════════════════════════════════════
    # 输入端口 Schema
    # ═══════════════════════════════════════════════════════════════════════════════
    INPUT_PORTS = [
        PortSchema(
            name="signal",
            data_type="object",
            required=True,
            description="Trading signal to evaluate",
            properties={
                "signal_id": {"type": "string"},
                "symbol": {"type": "string"},
                "direction": {"type": "string", "enum": ["LONG", "SHORT", "NEUTRAL"]},
                "confidence": {"type": "number"},
                "entry_price": {"type": "number"},
                "stop_loss": {"type": "number"},
                "take_profit": {"type": "number"},
            },
            required_fields=["signal_id", "symbol", "direction"],
        ),
        PortSchema(
            name="portfolio",
            data_type="object",
            required=True,
            description="Current portfolio state",
            properties={
                "total_value": {"type": "number"},
                "available_balance": {"type": "number"},
                "positions": {"type": "array"},
                "daily_pnl": {"type": "number"},
                "drawdown": {"type": "number"},
            },
            required_fields=["total_value", "available_balance"],
        ),
    ]

    # ═══════════════════════════════════════════════════════════════════════════════
    # 输出端口 Schema
    # ═══════════════════════════════════════════════════════════════════════════════
    OUTPUT_PORTS = [
        PortSchema(
            name="risk_approved_signal",
            data_type="object",
            required=False,
            description="Risk-approved signal (if passed all checks)",
            properties={
                "signal_id": {"type": "string"},
                "symbol": {"type": "string"},
                "direction": {"type": "string"},
                "approved_size": {"type": "number"},
                "risk_score": {"type": "number"},
                "timestamp": {"type": "integer"},
            },
            required_fields=["signal_id", "symbol", "direction", "approved_size"],
        ),
        PortSchema(
            name="risk_rejection",
            data_type="object",
            required=False,
            description="Rejection reason (if failed any check)",
            properties={
                "signal_id": {"type": "string"},
                "reason": {"type": "string"},
                "rejected_at": {"type": "integer"},
            },
            required_fields=["signal_id", "reason"],
        ),
        PortSchema(
            name="risk_metrics",
            data_type="object",
            required=True,
            description="Current risk metrics",
            properties={
                "portfolio_risk": {"type": "number"},
                "max_drawdown": {"type": "number"},
                "daily_loss_limit": {"type": "number"},
                "exposure_limit": {"type": "number"},
                "risk_score": {"type": "number"},
            },
        ),
    ]

    # ═══════════════════════════════════════════════════════════════════════════════
    # 约束 Schema
    # ═══════════════════════════════════════════════════════════════════════════════
    CONSTRAINTS = [
        ConstraintSchema(
            name="max_portfolio_risk",
            constraint_type="immutable",
            value=0.1,
            description="Maximum portfolio risk (10%)",
            min_value=0,
            max_value=1,
        ),
        ConstraintSchema(
            name="max_drawdown",
            constraint_type="immutable",
            value=0.15,
            description="Maximum drawdown (15%)",
            min_value=0,
            max_value=1,
        ),
        ConstraintSchema(
            name="daily_loss_limit",
            constraint_type="runtime",
            value=0.03,
            description="Daily loss limit (3%)",
            min_value=0,
            max_value=1,
        ),
        ConstraintSchema(
            name="max_exposure_per_symbol",
            constraint_type="immutable",
            value=0.2,
            description="Max exposure per symbol (20%)",
            min_value=0,
            max_value=1,
        ),
        ConstraintSchema(
            name="max_position_size",
            constraint_type="runtime",
            value=0.1,
            description="Maximum position size (10%)",
            min_value=0,
            max_value=1,
        ),
        ConstraintSchema(
            name="min_confidence",
            constraint_type="validation",
            value=0.5,
            description="Minimum signal confidence",
            min_value=0,
            max_value=1,
        ),
    ]

    # ═══════════════════════════════════════════════════════════════════════════════
    # 初始化
    # ═══════════════════════════════════════════════════════════════════════════════

    def __init__(self, node_id: str = "risk_node"):
        super().__init__(node_id)

        # 内部状态
        self._portfolio: dict[str, Any] = {
            "total_value": 100000,
            "available_balance": 100000,
            "positions": [],
            "daily_pnl": 0,
            "drawdown": 0,
        }
        self._risk_history: list[dict] = []
        self._lock = threading.Lock()

    # ═══════════════════════════════════════════════════════════════════════════════
    # 处理实现
    # ═══════════════════════════════════════════════════════════════════════════════

    def _process_impl(self, inputs: dict[str, Any]) -> dict[str, Any]:
        """
        风险管理处理

        Args:
            inputs = {
                "signal": {...},
                "portfolio": {...}
            }

        Returns:
            {
                "risk_approved_signal": {...},  # 如果通过
                "risk_rejection": {...},        # 如果拒绝
                "risk_metrics": {...}
            }
        """
        signal = inputs.get("signal")
        portfolio = inputs.get("portfolio", self._portfolio)

        if not signal:
            raise ValueError("Missing required input: signal")

        # 更新投资组合
        self._portfolio = portfolio

        # 执行风险检查
        rejection = self._check_risk(signal)

        if rejection:
            # 信号被拒绝
            return {
                "risk_approved_signal": None,
                "risk_rejection": rejection,
                "risk_metrics": self._get_risk_metrics(),
            }
        else:
            # 信号通过，计算批准的头寸大小
            approved_size = self._calculate_position_size(signal)
            risk_score = self._calculate_risk_score(signal)

            approved_signal = {
                "signal_id": signal["signal_id"],
                "symbol": signal["symbol"],
                "direction": signal["direction"],
                "approved_size": approved_size,
                "risk_score": risk_score,
                "timestamp": int(datetime.now().timestamp()),
            }

            return {
                "risk_approved_signal": approved_signal,
                "risk_rejection": None,
                "risk_metrics": self._get_risk_metrics(),
            }

    def _check_risk(self, signal: dict) -> dict | None:
        """
        执行风险检查

        Returns:
            None 如果通过，否则返回拒绝原因
        """
        # 1. 检查置信度
        min_confidence = self.get_config("min_confidence", 0.5)
        if signal.get("confidence", 0) < min_confidence:
            return {
                "signal_id": signal["signal_id"],
                "reason": f"Confidence {signal.get('confidence')} below minimum {min_confidence}",
                "rejected_at": int(datetime.now().timestamp()),
            }

        # 2. 检查每日亏损限制
        daily_loss_limit = self.get_config("daily_loss_limit", 0.03)
        daily_pnl_pct = abs(self._portfolio.get("daily_pnl", 0)) / self._portfolio.get("total_value", 1)
        if daily_pnl_pct > daily_loss_limit:
            return {
                "signal_id": signal["signal_id"],
                "reason": f"Daily loss {daily_pnl_pct:.2%} exceeds limit {daily_loss_limit:.2%}",
                "rejected_at": int(datetime.now().timestamp()),
            }

        # 3. 检查最大回撤
        max_drawdown = self.get_config("max_drawdown", 0.15)
        current_drawdown = self._portfolio.get("drawdown", 0)
        if current_drawdown > max_drawdown:
            return {
                "signal_id": signal["signal_id"],
                "reason": f"Drawdown {current_drawdown:.2%} exceeds maximum {max_drawdown:.2%}",
                "rejected_at": int(datetime.now().timestamp()),
            }

        # 4. 检查可用余额
        max_position = self.get_config("max_position_size", 0.1)
        total_value = self._portfolio.get("total_value", 100000)
        max_order_value = total_value * max_position
        available = self._portfolio.get("available_balance", 0)

        if available < max_order_value * 0.5:  # 预留一半
            return {
                "signal_id": signal["signal_id"],
                "reason": f"Insufficient balance: {available} < {max_order_value * 0.5}",
                "rejected_at": int(datetime.now().timestamp()),
            }

        # 5. 检查符号暴露
        max_exposure = self.get_config("max_exposure_per_symbol", 0.2)
        symbol = signal["symbol"]
        positions = self._portfolio.get("positions", [])
        symbol_exposure = (
            sum((p.get("size", 0) * p.get("entry_price", 0)) for p in positions if p.get("symbol") == symbol)
            / total_value
        )

        if symbol_exposure >= max_exposure:
            return {
                "signal_id": signal["signal_id"],
                "reason": f"Symbol exposure {symbol_exposure:.2%} exceeds limit {max_exposure:.2%}",
                "rejected_at": int(datetime.now().timestamp()),
            }

        return None  # 通过所有检查

    def _calculate_position_size(self, signal: dict) -> float:
        """计算批准的头寸大小"""
        max_position = self.get_config("max_position_size", 0.1)
        total_value = self._portfolio.get("total_value", 100000)
        confidence = signal.get("confidence", 0.5)

        # 基于置信度调整
        base_size = total_value * max_position
        adjusted_size = base_size * confidence

        # 确保不超过可用余额
        available = self._portfolio.get("available_balance", total_value)
        return min(adjusted_size, available * 0.9)  # 最多使用90%的可用余额

    def _calculate_risk_score(self, signal: dict) -> float:
        """计算风险评分"""
        confidence = signal.get("confidence", 0.5)
        daily_pnl_pct = abs(self._portfolio.get("daily_pnl", 0)) / self._portfolio.get("total_value", 1)
        drawdown = self._portfolio.get("drawdown", 0)

        # 综合风险评分 (0-1，越低越好)
        risk_score = (
            (1 - confidence) * 0.4 + daily_pnl_pct * 0.3 + drawdown * 0.3  # 置信度权重  # 当日亏损权重  # 回撤权重
        )

        return round(risk_score, 4)

    def _get_risk_metrics(self) -> dict:
        """获取风险指标"""
        total_value = self._portfolio.get("total_value", 100000)
        daily_pnl = self._portfolio.get("daily_pnl", 0)
        drawdown = self._portfolio.get("drawdown", 0)

        return {
            "portfolio_risk": abs(daily_pnl) / total_value,
            "max_drawdown": drawdown,
            "daily_loss_limit": self.get_config("daily_loss_limit", 0.03),
            "exposure_limit": self.get_config("max_exposure_per_symbol", 0.2),
            "risk_score": self._calculate_risk_score({"confidence": 0.5}),
            "available_balance": self._portfolio.get("available_balance", 0),
            "total_value": total_value,
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
                "signal": {"type": "object", "source": "signal_node"},
                "portfolio": {"type": "object", "source": "execution_node"},
            },
            "outputs": {
                "risk_approved_signal": {"type": "object", "destination": "execution_node"},
                "risk_rejection": {"type": "object", "destination": "brain_node"},
                "risk_metrics": {"type": "object", "destination": "monitor_node"},
            },
            "constraints": {
                "max_portfolio_risk": {"value": 0.1},
                "max_drawdown": {"value": 0.15},
                "daily_loss_limit": {"value": 0.03},
            },
            "dependencies": ["signal_node", "execution_node"],
            "risks": [
                {"type": "超额风险", "mitigation": "头寸限制"},
                {"type": "连环亏损", "mitigation": "每日亏损限制"},
            ],
        }

    def _design_phase_impl(self) -> dict[str, Any]:
        """设计阶段"""
        return {
            "node_id": self.NODE_ID,
            "phase": "design",
            "timestamp": datetime.now().isoformat(),
            "public_api": {
                "run(inputs)": "Evaluate signal risk",
                "get_risk_metrics()": "Get current risk metrics",
                "update_portfolio(portfolio)": "Update portfolio state",
            },
            "internal_structure": {
                "_portfolio": "Dict - 投资组合状态",
                "_risk_history": "List - 风险检查历史",
            },
            "event_contracts": {
                "publishes": ["risk.approved", "risk.rejected"],
                "subscribes": ["signal.generated", "execution.update"],
            },
        }

    # ═══════════════════════════════════════════════════════════════════════════════
    # 公开 API
    # ═══════════════════════════════════════════════════════════════════════════════

    def update_portfolio(self, portfolio: dict) -> None:
        """更新投资组合状态"""
        with self._lock:
            self._portfolio = portfolio

    def get_portfolio(self) -> dict:
        """获取投资组合状态"""
        return self._portfolio.copy()

    def get_risk_metrics(self) -> dict:
        """获取风险指标"""
        return self._get_risk_metrics()
