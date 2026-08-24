#!/usr/bin/env python
"""
自演化系统测试套件

直接在 evolution 目录下运行
"""
import os
import sys

# 确保当前目录在路径中
sys.path.insert(0, os.path.dirname(__file__))

print("=" * 60)
print("NEMT Self-Evolution System Test Suite")
print("=" * 60)

# 按依赖顺序导入
print("\n[Loading Modules...]")

# 基础模块
from base.meta_rule_engine import (
    ActionType,
    Comparator,
    ConditionNode,
    MetaRuleEngine,
    create_meta_rule,
)

print("  - base.meta_rule_engine: OK")

from state_universe.state_universe import (
    EntityType,
    RelationType,
    StateUniverse,
)

print("  - state_universe.state_universe: OK")

from constraint.constraint import (
    BusinessConstraints,
    Constraint,
    ConstraintValidator,
    Severity,
)

print("  - constraint.constraint: OK")

from observer.observer import (
    AlertLevel,
    AnomalyDetector,
    MetricType,
    StateObserver,
)

print("  - observer.observer: OK")

from self_repair.self_repair import (
    FaultType,
    SelfRepairEngine,
)

print("  - self_repair.self_repair: OK")

from self_optimize.self_optimize import (
    SelfOptimizeEngine,
)

print("  - self_optimize.self_optimize: OK")

from guider.guider import (
    EvolutionGuider,
    EvolutionState,
    GuiderRole,
    InterventionType,
)

print("  - guider.guider: OK")

from bootstrap.bootstrap import (
    BootstrapEngine,
    BootstrapSeed,
)

print("  - bootstrap.bootstrap: OK")

print("\n[Running Tests...]")

# ============================================================
# Test 1: MetaRuleEngine
# ============================================================
print("\n[Test 1] MetaRuleEngine")
try:
    engine = MetaRuleEngine()

    # 创建规则 - 使用扁平字段名
    rule = create_meta_rule(
        name="cpu_alert",
        condition_field="cpu_usage",
        condition_comparator=Comparator.GT,
        condition_value=80,
        action_type=ActionType.EMIT,
        action_target="alert",
        action_method="send",
        priority=90,
    )
    engine.register(rule)
    assert len(engine.get_rules()) == 1
    print("    [PASS] Rule registration")

    # 条件评估
    result = engine.evaluate({"cpu_usage": 90})
    assert any(triggered for _, triggered in result if triggered)
    print("    [PASS] Condition evaluation (triggered)")

    result = engine.evaluate({"cpu_usage": 50})
    assert not any(triggered for _, triggered in result if triggered)
    print("    [PASS] Condition evaluation (not triggered)")

    # 条件节点
    cond = ConditionNode.and_(
        ConditionNode.simple("a", Comparator.GT, 5),
        ConditionNode.simple("b", Comparator.LT, 10),
    )
    assert cond.evaluate({"a": 8, "b": 7})
    assert not cond.evaluate({"a": 8, "b": 15})
    print("    [PASS] Condition node (AND)")

    cond = ConditionNode.or_(
        ConditionNode.simple("a", Comparator.GT, 5),
        ConditionNode.simple("b", Comparator.LT, 10),
    )
    assert cond.evaluate({"a": 3, "b": 5})
    assert not cond.evaluate({"a": 3, "b": 15})
    print("    [PASS] Condition node (OR)")

except Exception as e:
    print(f"    [FAIL] {e}")
    raise

# ============================================================
# Test 2: StateUniverse
# ============================================================
print("\n[Test 2] StateUniverse")
try:
    universe = StateUniverse(name="test")

    # 创建实体
    entity = universe.create_entity(
        entity_type=EntityType.STRATEGY,
        name="test_strategy",
        properties={"param1": 10, "param2": "value"},
    )
    assert entity.name == "test_strategy"
    assert entity.type == EntityType.STRATEGY
    print("    [PASS] Entity creation")

    # 更新实体
    event = universe.update_entity(
        entity_id=entity.id,
        changes={"param1": 20},
        cause="test",
    )
    assert entity.get_property("param1") == 20
    print("    [PASS] Entity update")

    # 快照和回滚
    snapshot = universe.snapshot(entity.id, description="before")
    assert snapshot is not None
    universe.update_entity(entity.id, {"param1": 30})
    assert entity.get_property("param1") == 30
    universe.rollback(entity.id, snapshot.id)
    assert entity.get_property("param1") == 20
    print("    [PASS] Snapshot and rollback")

    # 关系
    entity2 = universe.create_entity(EntityType.SIGNAL, "signal1")
    relation = universe.relate(entity.id, entity2.id, RelationType.GENERATES)
    assert relation is not None
    relations = universe.get_relations(source_id=entity.id)
    assert len(relations) == 1
    print("    [PASS] Entity relations")

except Exception as e:
    print(f"    [FAIL] {e}")
    raise

# ============================================================
# Test 3: ConstraintValidator
# ============================================================
print("\n[Test 3] ConstraintValidator")
try:
    validator = ConstraintValidator()

    # 余额非负约束
    constraint = BusinessConstraints.create_balance_positive()
    validator.add_constraint(constraint)

    result = validator.validate({"balance": 1000})
    assert result.is_valid
    print("    [PASS] Positive balance (valid)")

    result = validator.validate({"balance": -100})
    assert not result.is_valid
    assert len(result.violations) == 1
    print("    [PASS] Negative balance (invalid)")

    # 自定义范围约束 - 单独验证
    range_constraint = Constraint(
        id="range",
        name="range_check",
        validator=lambda x: isinstance(x, (int, float)) and 0 <= x <= 100,
        severity=Severity.HIGH,
    )
    range_validator = ConstraintValidator()
    range_validator.add_constraint(range_constraint)

    result = range_validator.validate(50)
    assert result.is_valid, f"Expected valid but got: {result.violations}"
    result = range_validator.validate(150)
    assert not result.is_valid, "Expected invalid for value > 100"
    print("    [PASS] Custom range constraint")

except Exception as e:
    print(f"    [FAIL] {e}")
    raise

# ============================================================
# Test 4: StateObserver
# ============================================================
print("\n[Test 4] StateObserver")
try:
    observer = StateObserver(name="test")

    # 注册指标
    observer.register_metric("cpu", "CPU Usage", MetricType.GAUGE, unit="%")
    observer.register_metric("mem", "Memory Usage", MetricType.GAUGE, unit="%")
    print("    [PASS] Metric registration")

    # 记录值
    observer.record("cpu", 50)
    observer.record("cpu", 80)
    observer.record("cpu", 90)
    metric = observer.get_metric("cpu")
    assert metric.value == 90
    print("    [PASS] Metric recording")

    # 异常检测
    detector = AnomalyDetector()
    detector.add_threshold_rule("cpu", 85, "gt", AlertLevel.WARNING)

    alert = detector.detect_threshold("cpu", 90)
    assert alert is not None
    assert alert.level == AlertLevel.WARNING
    print("    [PASS] Anomaly detection")

    # Z-score 检测
    values = [10, 12, 11, 13, 12, 50, 11, 12]  # 50 是明显异常值
    anomalies = detector.detect_zscore(values, threshold=2.0)
    assert len(anomalies) > 0, f"Expected anomalies but got: {anomalies}"
    print("    [PASS] Z-score anomaly detection")

except Exception as e:
    print(f"    [FAIL] {e}")
    raise

# ============================================================
# Test 5: SelfRepairEngine
# ============================================================
print("\n[Test 5] SelfRepairEngine")
try:
    engine = SelfRepairEngine()

    # 报告故障
    fault = engine.report_fault(
        fault_type=FaultType.CRASH,
        description="Component crashed",
        severity="high",
        entity_id="component_1",
    )
    assert fault.id is not None
    assert fault.fault_type == FaultType.CRASH
    print("    [PASS] Fault reporting")

    # 创建修复计划
    plan = engine.create_repair_plan(fault.id)
    assert plan is not None
    assert len(plan.actions) > 0
    print("    [PASS] Repair plan creation")

    # 模拟执行
    engine._repair_executors["restart"] = lambda a: {"success": True}
    result = engine.execute_repair(plan.id)
    assert result == True
    print("    [PASS] Repair execution")

except Exception as e:
    print(f"    [FAIL] {e}")
    raise

# ============================================================
# Test 6: SelfOptimizeEngine
# ============================================================
print("\n[Test 6] SelfOptimizeEngine")
try:
    engine = SelfOptimizeEngine()

    # 设置阈值
    engine.add_metric_threshold("latency", 100, 500)
    print("    [PASS] Threshold setting")

    # 检测瓶颈
    bottleneck = engine.check_metric("latency", 600, "api")
    assert bottleneck is not None
    assert bottleneck.severity == "critical"
    print("    [PASS] Bottleneck detection")

    # 创建优化计划
    plan = engine.create_optimize_plan(bottleneck.id)
    assert plan is not None
    print("    [PASS] Optimization plan creation")

except Exception as e:
    print(f"    [FAIL] {e}")
    raise

# ============================================================
# Test 7: EvolutionGuider
# ============================================================
print("\n[Test 7] EvolutionGuider")
try:
    guider = EvolutionGuider(role=GuiderRole.ARCHITECT)

    # 添加方向
    direction = guider.add_direction(
        name="performance",
        vector={"speed": 1.0, "efficiency": 0.8},
        priority=80,
    )
    assert direction.name == "performance"
    print("    [PASS] Direction creation")

    # 添加目标
    goal = guider.add_goal(
        name="reduce_latency",
        metric="latency",
        direction="decrease",
        target_value=50,
    )
    assert goal.target_value == 50
    print("    [PASS] Goal creation")

    # 添加边界
    boundary = guider.add_boundary(
        name="max_cpu",
        condition="cpu < 99",
        action="warn",
    )
    assert boundary.name == "max_cpu"
    print("    [PASS] Boundary creation")

    # 干预
    intervention = guider.intervene(
        InterventionType.ACCELERATE,
        reason="speed up",
        parameters={"factor": 2},
    )
    assert intervention.type == InterventionType.ACCELERATE
    print("    [PASS] Intervention")

    # 轨迹
    trajectory = guider.start_trajectory(name="test_run")
    guider.record_step(1, {"value": 10}, {"perf": 0.5}, result="success")
    guider.end_trajectory(EvolutionState.CONVERGED)
    assert trajectory.state == EvolutionState.CONVERGED
    print("    [PASS] Trajectory tracking")

except Exception as e:
    print(f"    [FAIL] {e}")
    raise

# ============================================================
# Test 8: BootstrapEngine
# ============================================================
print("\n[Test 8] BootstrapEngine")
try:
    seed = BootstrapSeed.get_default_seed()
    assert len(seed.meta_rules) >= 4
    assert len(seed.constraints) >= 3
    print(f"    [PASS] Default seed (rules={len(seed.meta_rules)}, constraints={len(seed.constraints)})")

    engine = BootstrapEngine(seed=seed)

    # 加载种子
    result = engine._load_seed()
    assert result == True
    assert len(engine.rule_engine.get_rules()) >= 4
    print(f"    [PASS] Seed loading (rules={len(engine.rule_engine.get_rules())})")

    # 验证种子
    result = engine._validate_seed()
    assert result == True
    print("    [PASS] Seed validation")

    # 初始化组件
    result = engine._initialize_components()
    assert result == True
    print("    [PASS] Component initialization")

except Exception as e:
    print(f"    [FAIL] {e}")
    raise

# ============================================================
# Summary
# ============================================================
print("\n" + "=" * 60)
print("ALL TESTS PASSED!")
print("=" * 60)
print("\nTested Modules:")
print("  - MetaRuleEngine (元规则引擎)")
print("  - StateUniverse (状态宇宙)")
print("  - ConstraintValidator (约束验证器)")
print("  - StateObserver (状态观测器)")
print("  - SelfRepairEngine (自修复引擎)")
print("  - SelfOptimizeEngine (自优化引擎)")
print("  - EvolutionGuider (演化引导器)")
print("  - BootstrapEngine (自举引擎)")
print()
