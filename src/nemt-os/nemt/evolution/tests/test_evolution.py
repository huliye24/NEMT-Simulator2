"""
自演化系统测试套件

测试自演化系统的核心功能
"""

import os
import sys
import unittest

# 直接从当前目录导入，避免 nemt 包
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from evolution.base.meta_rule_engine import (
    ActionType,
    Comparator,
    ConditionNode,
    MetaRuleEngine,
    create_meta_rule,
)
from evolution.bootstrap.bootstrap import (
    BootstrapEngine,
    BootstrapPhase,
    BootstrapSeed,
)
from evolution.constraint.constraint import (
    BusinessConstraints,
    Constraint,
    ConstraintValidator,
    Severity,
)
from evolution.guider.guider import (
    EvolutionGuider,
    EvolutionState,
    GuiderRole,
    InterventionType,
)
from evolution.state_universe.state_universe import (
    EntityType,
    StateUniverse,
)


class TestMetaRuleEngine(unittest.TestCase):
    """测试元规则引擎"""

    def setUp(self):
        self.engine = MetaRuleEngine()

    def test_register_rule(self):
        """测试规则注册"""
        rule = create_meta_rule(
            name="test_rule",
            condition_field="state.value",
            condition_comparator=Comparator.GT,
            condition_value=10,
            action_type=ActionType.CALL,
            action_target="test_target",
            action_method="test_method",
            priority=50,
        )

        self.engine.register(rule)
        self.assertEqual(len(self.engine.get_rules()), 1)
        self.assertEqual(self.engine.get_rule(rule.id), rule)

    def test_rule_evaluation(self):
        """测试规则评估"""
        rule = create_meta_rule(
            name="high_value_alert",
            condition_field="state.cpu_usage",
            condition_comparator=Comparator.GT,
            condition_value=80,
            action_type=ActionType.EMIT,
            action_target="alert_manager",
            action_method="send",
            priority=80,
        )

        self.engine.register(rule)

        # 满足条件
        context1 = {"cpu_usage": 90}
        evaluations = self.engine.evaluate(context1)
        self.assertTrue(any(triggered for _, triggered in evaluations if triggered))

        # 不满足条件
        context2 = {"cpu_usage": 50}
        evaluations = self.engine.evaluate(context2)
        self.assertFalse(any(triggered for _, triggered in evaluations if triggered))

    def test_condition_node(self):
        """测试条件节点"""
        # 简单条件
        cond = ConditionNode.simple("value", Comparator.GT, 10)
        self.assertTrue(cond.evaluate({"value": 20}))
        self.assertFalse(cond.evaluate({"value": 5}))

        # AND 条件
        left = ConditionNode.simple("a", Comparator.GT, 5)
        right = ConditionNode.simple("b", Comparator.LT, 10)
        and_cond = ConditionNode.and_(left, right)

        self.assertTrue(and_cond.evaluate({"a": 10, "b": 5}))
        self.assertFalse(and_cond.evaluate({"a": 10, "b": 15}))


class TestStateUniverse(unittest.TestCase):
    """测试状态宇宙"""

    def setUp(self):
        self.universe = StateUniverse(name="test_universe")

    def test_create_entity(self):
        """测试创建实体"""
        entity = self.universe.create_entity(
            entity_type=EntityType.STRATEGY,
            name="test_strategy",
            properties={"param1": 10, "param2": "value"},
        )

        self.assertIsNotNone(entity)
        self.assertEqual(entity.name, "test_strategy")
        self.assertEqual(entity.type, EntityType.STRATEGY)

    def test_update_entity(self):
        """测试更新实体"""
        entity = self.universe.create_entity(
            entity_type=EntityType.ORDER,
            name="test_order",
            properties={"price": 100},
        )

        event = self.universe.update_entity(
            entity_id=entity.id,
            changes={"price": 110, "quantity": 10},
            cause="price_update",
        )

        self.assertIsNotNone(event)
        self.assertEqual(entity.get_property("price"), 110)
        self.assertEqual(entity.get_property("quantity"), 10)

    def test_snapshot_and_rollback(self):
        """测试快照和回滚"""
        entity = self.universe.create_entity(
            entity_type=EntityType.POSITION,
            name="test_position",
            properties={"size": 100},
        )

        # 创建快照
        snapshot = self.universe.snapshot(entity.id, description="initial")
        self.assertIsNotNone(snapshot)

        # 修改
        self.universe.update_entity(
            entity_id=entity.id,
            changes={"size": 200},
            cause="increase_size",
        )
        self.assertEqual(entity.get_property("size"), 200)

        # 回滚
        event = self.universe.rollback(entity.id, snapshot.id)
        self.assertIsNotNone(event)
        self.assertEqual(entity.get_property("size"), 100)


class TestConstraintValidator(unittest.TestCase):
    """测试约束验证器"""

    def setUp(self):
        self.validator = ConstraintValidator()

    def test_validate(self):
        """测试验证"""
        constraint = Constraint(
            id="test_constraint",
            name="range_check",
            validator=lambda x: 0 <= x <= 100,
            severity=Severity.HIGH,
        )

        self.validator.add_constraint(constraint)

        # 满足约束
        result = self.validator.validate(50)
        self.assertTrue(result.is_valid)

        # 不满足约束
        result = self.validator.validate(150)
        self.assertFalse(result.is_valid)
        self.assertEqual(len(result.violations), 1)

    def test_business_constraints(self):
        """测试业务约束工厂"""
        balance_constraint = BusinessConstraints.create_balance_positive()
        self.validator.add_constraint(balance_constraint)

        # 满足
        result = self.validator.validate({"balance": 1000})
        self.assertTrue(result.is_valid)

        # 不满足
        result = self.validator.validate({"balance": -100})
        self.assertFalse(result.is_valid)


class TestEvolutionGuider(unittest.TestCase):
    """测试演化引导器"""

    def setUp(self):
        self.guider = EvolutionGuider(role=GuiderRole.ARCHITECT)

    def test_add_direction(self):
        """测试添加方向"""
        direction = self.guider.add_direction(
            name="performance_improvement",
            vector={"performance": 1.0, "efficiency": 0.8},
            priority=80,
        )

        self.assertIsNotNone(direction)
        self.assertEqual(direction.name, "performance_improvement")

    def test_add_goal(self):
        """测试添加目标"""
        goal = self.guider.add_goal(
            name="reduce_latency",
            metric="avg_response_time",
            direction="decrease",
            target_value=50,
        )

        self.assertIsNotNone(goal)
        self.assertEqual(goal.metric, "avg_response_time")

    def test_intervention(self):
        """测试干预"""
        intervention = self.guider.intervene(
            InterventionType.STEER,
            reason="adjust direction",
            parameters={"factor": 1.5},
        )

        self.assertIsNotNone(intervention)
        self.assertEqual(intervention.type, InterventionType.STEER)

    def test_trajectory(self):
        """测试轨迹追踪"""
        trajectory = self.guider.start_trajectory(name="test_run")
        self.assertIsNotNone(trajectory)

        self.guider.record_step(
            step=1,
            state={"value": 10},
            metrics={"performance": 0.5},
            action="optimize",
            result="success",
        )

        self.guider.end_trajectory(EvolutionState.CONVERGED)
        self.assertEqual(trajectory.state, EvolutionState.CONVERGED)


class TestBootstrapEngine(unittest.TestCase):
    """测试自举引擎"""

    def test_create_seed(self):
        """测试创建种子"""
        seed = BootstrapSeed.get_default_seed()
        self.assertIsNotNone(seed)
        self.assertGreater(len(seed.meta_rules), 0)
        self.assertGreater(len(seed.constraints), 0)

    def test_bootstrap_init(self):
        """测试自举引擎初始化"""
        engine = BootstrapEngine()
        self.assertIsNotNone(engine)
        self.assertEqual(engine.phase, BootstrapPhase.INITIAL)
        self.assertEqual(engine.state.value, "idle")

    def test_load_seed(self):
        """测试加载种子"""
        engine = BootstrapEngine()
        result = engine._load_seed()
        self.assertTrue(result)
        self.assertGreater(len(engine.rule_engine.get_rules()), 0)


if __name__ == "__main__":
    unittest.main()
