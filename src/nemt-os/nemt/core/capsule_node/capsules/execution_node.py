"""
ExecutionNode - 订单执行节点

基于 CapsuleNode 的订单执行节点
"""

from typing import Any, Dict, List, Optional
from datetime import datetime
import threading
import uuid

from nemt.core.capsule_node import (
    CapsuleNode,
    FractalCapsuleNode,
    PortSchema,
    ConstraintSchema,
    NodePhase,
)


class ExecutionNode(FractalCapsuleNode):
    """
    ExecutionNode - 订单执行胶囊节点

    职责：
    - 接收决策
    - 创建和发送订单
    - 跟踪订单状态
    - 管理持仓
    - 提供投资组合状态

    AI 可直接读取：
    - state: 当前状态
    - orders: 订单列表
    - positions: 持仓列表
    - portfolio: 投资组合
    """

    # ═══════════════════════════════════════════════════════════════════════════════
    # 节点身份
    # ═══════════════════════════════════════════════════════════════════════════════
    NODE_ID = "execution_node"
    NODE_NAME = "Order Execution Node"
    NODE_VERSION = "1.0.0"

    # ═══════════════════════════════════════════════════════════════════════════════
    # 输入端口 Schema
    # ═══════════════════════════════════════════════════════════════════════════════
    INPUT_PORTS = [
        PortSchema(
            name="decision",
            data_type="object",
            required=True,
            description="Trading decision from brain_node",
            properties={
                "decision_id": {"type": "string"},
                "action": {"type": "string", "enum": ["EXECUTE", "SKIP", "WAIT"]},
                "symbol": {"type": "string"},
                "direction": {"type": "string"},
                "size": {"type": "number"},
                "entry_price": {"type": "number"},
                "stop_loss": {"type": "number"},
                "take_profit": {"type": "number"},
            },
            required_fields=["decision_id", "action", "symbol"],
        ),
    ]

    # ═══════════════════════════════════════════════════════════════════════════════
    # 输出端口 Schema
    # ═══════════════════════════════════════════════════════════════════════════════
    OUTPUT_PORTS = [
        PortSchema(
            name="order",
            data_type="object",
            required=False,
            description="Order to send to exchange",
            properties={
                "order_id": {"type": "string"},
                "symbol": {"type": "string"},
                "direction": {"type": "string"},
                "order_type": {"type": "string", "enum": ["MARKET", "LIMIT", "STOP"]},
                "size": {"type": "number"},
                "price": {"type": "number"},
                "stop_loss": {"type": "number"},
                "take_profit": {"type": "number"},
                "status": {"type": "string", "enum": ["PENDING", "FILLED", "PARTIAL", "CANCELLED", "REJECTED"]},
                "timestamp": {"type": "integer"},
            },
            required_fields=["order_id", "symbol", "direction", "size"],
        ),
        PortSchema(
            name="fill",
            data_type="object",
            required=False,
            description="Order fill event",
            properties={
                "order_id": {"type": "string"},
                "fill_id": {"type": "string"},
                "symbol": {"type": "string"},
                "size": {"type": "number"},
                "fill_price": {"type": "number"},
                "fees": {"type": "number"},
                "timestamp": {"type": "integer"},
            },
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
        ),
    ]

    # ═══════════════════════════════════════════════════════════════════════════════
    # 约束 Schema
    # ═══════════════════════════════════════════════════════════════════════════════
    CONSTRAINTS = [
        ConstraintSchema(
            name="initial_balance",
            constraint_type="immutable",
            value=100000,
            description="Initial account balance",
        ),
        ConstraintSchema(
            name="min_order_size",
            constraint_type="runtime",
            value=10,
            description="Minimum order size",
            min_value=0,
        ),
        ConstraintSchema(
            name="max_orders_per_minute",
            constraint_type="runtime",
            value=10,
            description="Rate limit for orders",
            min_value=1,
            max_value=60,
        ),
        ConstraintSchema(
            name="order_fee_rate",
            constraint_type="immutable",
            value=0.001,
            description="Trading fee rate (0.1%)",
            min_value=0,
            max_value=1,
        ),
        ConstraintSchema(
            name="slippage_rate",
            constraint_type="runtime",
            value=0.0005,
            description="Expected slippage rate (0.05%)",
        ),
    ]

    # ═══════════════════════════════════════════════════════════════════════════════
    # 初始化
    # ═══════════════════════════════════════════════════════════════════════════════

    def __init__(self, node_id: str = "execution_node"):
        super().__init__(node_id)

        # 内部状态
        self._orders: Dict[str, Dict] = {}
        self._fills: List[Dict] = []
        self._positions: Dict[str, Dict] = {}
        self._portfolio: Dict[str, Any] = {
            "total_value": 100000,
            "available_balance": 100000,
            "positions": [],
            "daily_pnl": 0,
            "drawdown": 0,
        }
        self._peak_value = 100000
        self._order_history: List[Dict] = []
        self._lock = threading.Lock()

    # ═══════════════════════════════════════════════════════════════════════════════
    # 处理实现
    # ═══════════════════════════════════════════════════════════════════════════════

    def _process_impl(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        订单执行处理

        Args:
            inputs = {
                "decision": {...}
            }

        Returns:
            {
                "order": {...},      # 如果创建订单
                "fill": {...},       # 如果成交
                "portfolio": {...}   # 投资组合状态
            }
        """
        decision = inputs.get("decision")

        if not decision:
            raise ValueError("Missing required input: decision")

        # 如果不是执行决策，直接返回当前投资组合
        if decision.get("action") != "EXECUTE":
            return {
                "order": None,
                "fill": None,
                "portfolio": self._get_portfolio(),
            }

        # 创建订单
        order = self._create_order(decision)

        # 模拟成交
        fill = self._simulate_fill(order)

        return {
            "order": order,
            "fill": fill,
            "portfolio": self._get_portfolio(),
        }

    def _create_order(self, decision: Dict) -> Dict:
        """创建订单"""
        order_id = f"ord_{uuid.uuid4().hex[:12]}"

        order = {
            "order_id": order_id,
            "decision_id": decision.get("decision_id"),
            "symbol": decision["symbol"],
            "direction": decision["direction"],
            "order_type": "MARKET",
            "size": decision["size"],
            "price": decision.get("entry_price"),
            "stop_loss": decision.get("stop_loss"),
            "take_profit": decision.get("take_profit"),
            "status": "PENDING",
            "created_at": int(datetime.now().timestamp()),
            "timestamp": int(datetime.now().timestamp()),
        }

        with self._lock:
            self._orders[order_id] = order
            self._order_history.append(order)

        return order

    def _simulate_fill(self, order: Dict) -> Optional[Dict]:
        """模拟订单成交"""
        # 模拟滑点
        slippage_rate = self.get_config("slippage_rate", 0.0005)
        price = order["price"]

        if order["direction"] == "LONG":
            fill_price = price * (1 + slippage_rate)
        else:
            fill_price = price * (1 - slippage_rate)

        # 计算手续费
        fee_rate = self.get_config("order_fee_rate", 0.001)
        fees = order["size"] * fill_price * fee_rate

        # 创建成交记录
        fill = {
            "order_id": order["order_id"],
            "fill_id": f"fill_{uuid.uuid4().hex[:12]}",
            "symbol": order["symbol"],
            "direction": order["direction"],
            "size": order["size"],
            "fill_price": fill_price,
            "fees": fees,
            "timestamp": int(datetime.now().timestamp()),
        }

        # 更新持仓
        self._update_position(fill)

        # 更新订单状态
        order["status"] = "FILLED"

        with self._lock:
            self._fills.append(fill)

        return fill

    def _update_position(self, fill: Dict) -> None:
        """更新持仓"""
        with self._lock:
            symbol = fill["symbol"]

            if symbol not in self._positions:
                self._positions[symbol] = {
                    "symbol": symbol,
                    "direction": fill["direction"],
                    "size": 0,
                    "entry_price": 0,
                    "current_price": fill["fill_price"],
                    "pnl": 0,
                }

            pos = self._positions[symbol]

            # 更新持仓
            if fill["direction"] == "LONG":
                # 开多或加仓
                total_cost = pos["size"] * pos["entry_price"] + fill["size"] * fill["fill_price"]
                pos["size"] += fill["size"]
                pos["entry_price"] = total_cost / pos["size"] if pos["size"] > 0 else 0
            elif fill["direction"] == "SHORT":
                # 开空或加仓
                pos["size"] -= fill["size"]  # 空头持仓为负
                pos["entry_price"] = fill["fill_price"]

            pos["current_price"] = fill["fill_price"]

            # 更新投资组合
            self._portfolio["available_balance"] -= fill["size"] * fill["fill_price"] + fill["fees"]

            # 同步持仓列表
            self._portfolio["positions"] = [
                {k: v for k, v in p.items() if k != "_lock"}
                for p in [self._positions[s] for s in self._positions]
                if isinstance(p, dict)
            ]

    def _get_portfolio(self) -> Dict:
        """获取投资组合"""
        with self._lock:
            # 计算总价值
            positions_value = sum(
                abs(p["size"]) * p["current_price"]
                for p in self._positions.values()
            )

            total_value = self._portfolio["available_balance"] + positions_value

            # 更新峰值和回撤
            if total_value > self._peak_value:
                self._peak_value = total_value

            drawdown = (self._peak_value - total_value) / self._peak_value if self._peak_value > 0 else 0

            # 计算每日盈亏 (简化版)
            daily_pnl = total_value - 100000  # 相对于初始值

            return {
                "total_value": round(total_value, 2),
                "available_balance": round(self._portfolio["available_balance"], 2),
                "positions": list(self._positions.values()),
                "daily_pnl": round(daily_pnl, 2),
                "drawdown": round(drawdown, 4),
            }

    # ═══════════════════════════════════════════════════════════════════════════════
    # 五阶段实现
    # ═══════════════════════════════════════════════════════════════════════════════

    def _observe_phase_impl(self) -> Dict[str, Any]:
        """观察阶段"""
        return {
            "node_id": self.NODE_ID,
            "phase": "observe",
            "timestamp": datetime.now().timestamp(),
            "inputs": {
                "decision": {"source": "brain_node"},
            },
            "outputs": {
                "order": {"destination": "exchange"},
                "fill": {"destination": "risk_node", "monitor_node"},
                "portfolio": {"destination": "risk_node", "brain_node"},
            },
            "constraints": {
                "initial_balance": {"value": 100000},
                "min_order_size": {"value": 10},
                "order_fee_rate": {"value": 0.001},
            },
            "dependencies": ["brain_node"],
            "risks": [
                {"type": "滑点", "mitigation": "限价单"},
                {"type": "资金不足", "mitigation": "余额检查"},
            ],
        }

    def _design_phase_impl(self) -> Dict[str, Any]:
        """设计阶段"""
        return {
            "node_id": self.NODE_ID,
            "phase": "design",
            "timestamp": datetime.now().isoformat(),
            "public_api": {
                "run(inputs)": "Execute order",
                "get_portfolio()": "Get current portfolio",
                "get_orders()": "Get all orders",
                "get_positions()": "Get all positions",
            },
            "internal_structure": {
                "_orders": "Dict[str, Dict] - 订单缓存",
                "_fills": "List[Dict] - 成交记录",
                "_positions": "Dict[str, Dict] - 持仓",
                "_portfolio": "Dict - 投资组合",
            },
            "event_contracts": {
                "publishes": ["execution.order", "execution.fill"],
                "subscribes": ["brain.decision"],
            },
        }

    # ═══════════════════════════════════════════════════════════════════════════════
    # 公开 API
    # ═══════════════════════════════════════════════════════════════════════════════

    def get_portfolio(self) -> Dict:
        """获取投资组合"""
        return self._get_portfolio()

    def get_orders(self, status: Optional[str] = None) -> List[Dict]:
        """获取订单列表"""
        with self._lock:
            if status:
                return [o for o in self._orders.values() if o["status"] == status]
            return list(self._orders.values())

    def get_fills(self) -> List[Dict]:
        """获取成交记录"""
        with self._lock:
            return self._fills.copy()

    def get_positions(self) -> Dict[str, Dict]:
        """获取持仓"""
        with self._lock:
            return self._positions.copy()

    def reset_portfolio(self) -> None:
        """重置投资组合"""
        with self._lock:
            initial = self.get_config("initial_balance", 100000)
            self._portfolio = {
                "total_value": initial,
                "available_balance": initial,
                "positions": [],
                "daily_pnl": 0,
                "drawdown": 0,
            }
            self._peak_value = initial
            self._orders.clear()
            self._fills.clear()
            self._positions.clear()
