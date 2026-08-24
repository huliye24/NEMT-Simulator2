"""
自演化系统测试

测试自演化系统的核心功能:
- 元规则引擎
- 状态宇宙
- 约束系统
- 演化引导器
- 自举引擎
"""

import os
import sys
import unittest

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 直接导入，避免通过 nemt 包导入有问题的模块
from nemt.evolution.base.meta_rule_engine import (
    ActionType,
    Comparator,
    ConditionNode,
    MetaRuleEngine,
    create_meta_rule,
)
from nemt.evolution.bootstrap.bootstrap import (
    BootstrapEngine,
    BootstrapPhase,
    BootstrapSeed,
)
from nemt.evolution.constraint.constraint import (
    BusinessConstraints,
    Constraint,
    ConstraintValidator,
    Severity,
)
from nemt.evolution.guider.guider import (
    EvolutionGuider,
    EvolutionState,
    GuiderRole,
    InterventionType,
)
from nemt.evolution.state_universe.state_universe import (
    EntityType,
    RelationType,
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
        triggered = any(triggered for _, triggered in evaluations if triggered)
        self.assertTrue(triggered)

        # 不满足条件
        context2 = {"cpu_usage": 50}
        evaluations = self.engine.evaluate(context2)
        triggered = any(triggered for _, triggered in evaluations if not triggered)
        self.assertTrue(not any(triggered for _, triggered in evaluations if triggered))

    def test_rule_priority(self):
        """测试规则优先级"""
        rule1 = create_meta_rule(
            name="low_priority",
            condition_field="state.test",
            condition_comparator=Comparator.EQ,
            condition_value=True,
            action_type=ActionType.CALL,
            action_target="t",
            action_method="m",
            priority=10,
        )

        rule2 = create_meta_rule(
            name="high_priority",
            condition_field="state.test",
            condition_comparator=Comparator.EQ,
            condition_value=True,
            action_type=ActionType.CALL,
            action_target="t",
            action_method="m",
            priority=90,
        )

        self.engine.register(rule1)
        self.engine.register(rule2)

        rules = self.engine.get_rules()
        self.assertEqual(rules[0].priority, 90)
        self.assertEqual(rules[1].priority, 10)

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

        # OR 条件
        or_cond = ConditionNode.or_(left, right)
        self.assertTrue(or_cond.evaluate({"a": 3, "b": 5}))
        self.assertFalse(or_cond.evaluate({"a": 3, "b": 15}))


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

    def test_get_entity(self):
        """测试获取实体"""
        entity = self.universe.create_entity(
            entity_type=EntityType.SIGNAL,
            name="test_signal",
        )

        retrieved = self.universe.get_entity(entity.id)
        self.assertEqual(retrieved.id, entity.id)

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

    def test_relations(self):
        """测试关系"""
        entity1 = self.universe.create_entity(
            entity_type=EntityType.STRATEGY,
            name="strategy1",
        )

        entity2 = self.universe.create_entity(
            entity_type=EntityType.SIGNAL,
            name="signal1",
        )

        relation = self.universe.relate(
            source_id=entity1.id,
            target_id=entity2.id,
            relation_type=RelationType.GENERATES,
        )

        self.assertIsNotNone(relation)
        relations = self.universe.get_relations(source_id=entity1.id)
        self.assertEqual(len(relations), 1)


class TestConstraintValidator(unittest.TestCase):
    """测试约束验证器"""

    def setUp(self):
        self.validator = ConstraintValidator()

    def test_add_constraint(self):
        """测试添加约束"""
        constraint = Constraint(
            id="test_constraint",
            name="positive_balance",
            validator=lambda x: x >= 0,
            severity=Severity.CRITICAL,
        )

        self.validator.add_constraint(constraint)
        self.assertEqual(len(self.validator.get_constraints()), 1)

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

    def test_add_boundary(self):
        """测试添加边界"""
        boundary = self.guider.add_boundary(
            name="max_cpu_usage",
            condition="cpu_usage < 99",
            action="warn",
        )

        self.assertIsNotNone(boundary)
        self.assertEqual(boundary.name, "max_cpu_usage")

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
