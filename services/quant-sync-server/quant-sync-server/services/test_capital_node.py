"""
CapitalNode 单元测试
====================

运行方式:
    cd quant-sync-server
    python -c "import sys; sys.path.insert(0, '.'); exec(open('services/test_capital_node.py').read())"
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.stdout.reconfigure(encoding='utf-8')

from services.capital_node import (
    CapitalNode,
    EqualWeightCapitalManager,
    PhaseDrivenCapitalManager,
    RiskAdjustedCapitalManager,
    MarketPhase,
    Order,
    FinalOrder,
    AllocationResult,
)


class TestOrder(unittest.TestCase):
    """Order 数据类测试"""

    def test_order_creation(self):
        order = Order(
            strategy_id="test-1",
            symbol="BTCUSDT",
            direction=1,
            quantity=0.1,
            stop_loss=65000,
            take_profit=70000,
        )
        self.assertEqual(order.strategy_id, "test-1")
        self.assertEqual(order.direction, 1)

    def test_order_with_metadata(self):
        order = Order(
            strategy_id="test-2",
            symbol="ETHUSDT",
            direction=-1,
            quantity=1.0,
            stop_loss=3000,
            take_profit=3500,
            metadata={"risk_score": 0.75}
        )
        self.assertEqual(order.metadata["risk_score"], 0.75)


class TestFinalOrder(unittest.TestCase):
    """FinalOrder 数据类测试"""

    def test_final_order_to_dict(self):
        order = Order(
            strategy_id="test-1",
            symbol="BTCUSDT",
            direction=1,
            quantity=0.1,
            stop_loss=65000,
            take_profit=70000,
        )
        final = FinalOrder(
            order=order,
            allocated_capital=30000,
            weight=0.5,
            position_ratio=0.3,
            risk_amount=600,
        )
        d = final.to_dict()
        self.assertEqual(d["strategy_id"], "test-1")
        self.assertEqual(d["allocated_capital"], 30000)
        self.assertEqual(d["weight"], 0.5)


class TestEqualWeightCapitalManager(unittest.TestCase):
    """等权重分配器测试"""

    def test_allocate_single_order(self):
        manager = EqualWeightCapitalManager(reserve_ratio=0.10)
        orders = [Order("s1", "BTCUSDT", 1, 0.1, 65000, 70000)]
        result = manager.allocate(orders, 100000, MarketPhase.PHASE_A_NOISE)

        self.assertEqual(len(result.allocations), 1)
        self.assertEqual(result.reserved_capital, 10000)
        self.assertEqual(result.allocated_capital, 90000)

    def test_allocate_multiple_orders(self):
        manager = EqualWeightCapitalManager(reserve_ratio=0.10)
        orders = [
            Order("s1", "BTCUSDT", 1, 0.1, 65000, 70000),
            Order("s2", "ETHUSDT", 1, 1.0, 3000, 3500),
        ]
        result = manager.allocate(orders, 100000, MarketPhase.PHASE_A_NOISE)

        self.assertEqual(len(result.allocations), 2)
        self.assertEqual(result.allocations[0].allocated_capital,
                        result.allocations[1].allocated_capital)

    def test_allocate_empty_orders(self):
        manager = EqualWeightCapitalManager()
        result = manager.allocate([], 100000, MarketPhase.PHASE_A_NOISE)

        self.assertEqual(len(result.allocations), 0)
        self.assertEqual(result.allocated_capital, 0)


class TestPhaseDrivenCapitalManager(unittest.TestCase):
    """相位驱动分配器测试"""

    def test_phase_a_max_position(self):
        manager = PhaseDrivenCapitalManager()
        orders = [Order("s1", "BTCUSDT", 1, 0.1, 65000, 70000)]
        result = manager.allocate(orders, 100000, MarketPhase.PHASE_A_NOISE)

        self.assertEqual(result.allocations[0].metadata["max_position"], 0.20)

    def test_phase_d_max_position(self):
        manager = PhaseDrivenCapitalManager()
        orders = [Order("s1", "BTCUSDT", 1, 0.1, 65000, 70000)]
        result = manager.allocate(orders, 100000, MarketPhase.PHASE_D_TREND)

        self.assertEqual(result.allocations[0].metadata["max_position"], 1.00)
        self.assertEqual(result.allocations[0].metadata["phase"], "phase_d")


class TestRiskAdjustedCapitalManager(unittest.TestCase):
    """风险调整分配器测试"""

    def test_risk_weight_distribution(self):
        manager = RiskAdjustedCapitalManager()
        orders = [
            Order("s1", "BTCUSDT", 1, 0.1, 65000, 70000,
                  metadata={"risk_score": 0.8}),
            Order("s2", "ETHUSDT", 1, 1.0, 3000, 3500,
                  metadata={"risk_score": 0.2}),
        ]
        result = manager.allocate(orders, 100000, MarketPhase.PHASE_A_NOISE)

        s1_capital = result.allocations[0].allocated_capital
        s2_capital = result.allocations[1].allocated_capital
        self.assertGreater(s1_capital, s2_capital)

    def test_weight_limits(self):
        manager = RiskAdjustedCapitalManager(min_weight=0.1, max_weight=0.5)
        orders = [
            Order("s1", "BTCUSDT", 1, 0.1, 65000, 70000,
                  metadata={"risk_score": 0.5}),
            Order("s2", "ETHUSDT", 1, 1.0, 3000, 3500,
                  metadata={"risk_score": 0.5}),
        ]
        result = manager.allocate(orders, 100000, MarketPhase.PHASE_A_NOISE)

        for alloc in result.allocations:
            self.assertGreaterEqual(alloc.weight, 0.1)
            self.assertLessEqual(alloc.weight, 0.5)


class TestCapitalNode(unittest.TestCase):
    """资金节点测试"""

    def test_initialization(self):
        node = CapitalNode(initial_capital=100000, mode="equal")
        self.assertEqual(node.current_capital, 100000)
        self.assertEqual(node.initial_capital, 100000)

    def test_set_phase(self):
        node = CapitalNode()
        node.set_phase(MarketPhase.PHASE_B_VORTEX)
        self.assertEqual(node.current_phase, MarketPhase.PHASE_B_VORTEX)

    def test_set_capital(self):
        node = CapitalNode()
        node.set_capital(80000)
        self.assertEqual(node.current_capital, 80000)

    def test_allocate_orders(self):
        node = CapitalNode(initial_capital=100000, mode="equal")
        orders = [Order("s1", "BTCUSDT", 1, 0.1, 65000, 70000)]
        result = node.allocate(orders)
        self.assertEqual(len(result.allocations), 1)

    def test_switch_mode(self):
        node = CapitalNode(mode="equal")
        success = node.set_mode("risk")
        self.assertTrue(success)
        self.assertEqual(node.manager.get_name(), "RiskAdjusted")

    def test_invalid_mode(self):
        node = CapitalNode(mode="equal")
        success = node.set_mode("invalid_mode")
        self.assertFalse(success)

    def test_get_status(self):
        node = CapitalNode(initial_capital=100000, mode="phase")
        status = node.get_status()
        self.assertEqual(status["name"], "CapitalNode")
        self.assertEqual(status["current_capital"], 100000)
        self.assertEqual(status["manager"], "PhaseDriven")

    def test_health_check(self):
        node = CapitalNode()
        health = node.health_check()
        self.assertEqual(health["status"], "healthy")
        self.assertEqual(health["capital_node"], "running")


class TestAllocationResult(unittest.TestCase):
    """分配结果测试"""

    def test_to_dict(self):
        order = Order("s1", "BTCUSDT", 1, 0.1, 65000, 70000)
        final = FinalOrder(order, 50000, 1.0, 0.5, 1000)
        result = AllocationResult(
            allocations=[final],
            total_capital=100000,
            allocated_capital=50000,
            reserved_capital=10000,
            reserve_ratio=0.10,
            timestamp="2026-04-19T10:00:00",
            reasoning="Test allocation"
        )
        d = result.to_dict()
        self.assertEqual(d["total_capital"], 100000)
        self.assertEqual(len(d["allocations"]), 1)


if __name__ == "__main__":
    unittest.main()
