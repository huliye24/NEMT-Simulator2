"""
IntegrationTests - 集成测试

验证各模块间的协作能力。
"""

import time
import unittest

# 导入所有模块
from nemt import (
    AlertManager,
    AlertRule,
    AlertSeverity,
    APIGateway,
    APIResponse,
    AuditLogger,
    Capsule,
    CapsuleConfig,
    CapsuleState,
    CircuitBreaker,
    ConfigLoader,
    DIContainer,
    Event,
    EventBus,
    FeatureFlagManager,
    HealthCheckRegistry,
    HTTPMethod,
    LambdaHealthCheck,
    LogAggregator,
    MetricsCollector,
    OrderExecutor,
    PermissionManager,
    Profiler,
    RetryPolicy,
    RiskCalculator,
    SecretManager,
    SignalType,
    StrategyCategory,
    StrategyMarket,
    StrategySimulator,
    Task,
    TaskStatus,
    TaskType,
    TraceCollector,
    WorkflowEngine,
)


class TestCoreModules(unittest.TestCase):
    """核心模块测试"""

    def test_capsule_lifecycle(self):
        """胶囊生命周期测试"""
        config = CapsuleConfig(name="test_capsule", memory_limit=256)
        capsule = Capsule(config)

        self.assertEqual(capsule.state, CapsuleState.CREATED)
        capsule.start()
        self.assertEqual(capsule.state, CapsuleState.RUNNING)
        capsule.stop()
        self.assertEqual(capsule.state, CapsuleState.STOPPED)

    def test_event_bus(self):
        """事件总线测试"""
        bus = EventBus()
        received = []

        def handler(event):
            received.append(event)

        bus.subscribe("test_event", handler)
        bus.publish(Event("test_event", {"data": "test"}))
        bus.unsubscribe("test_event", handler)

        self.assertEqual(len(received), 1)
        self.assertEqual(received[0].data["data"], "test")

    def test_di_container(self):
        """依赖注入容器测试"""
        container = DIContainer()

        container.register("service", lambda: {"name": "test_service"})
        service = container.get("service")

        self.assertEqual(service["name"], "test_service")


class TestIsolationModules(unittest.TestCase):
    """隔离模块测试"""

    def test_circuit_breaker(self):
        """熔断器测试"""
        cb = CircuitBreaker(failure_threshold=3)

        # 触发熔断
        for _ in range(3):
            cb.record_failure()

        self.assertEqual(cb.state, "open")

        # 等待恢复
        time.sleep(1)
        cb.record_success()
        self.assertEqual(cb.state, "closed")

    def test_retry_policy(self):
        """重试策略测试"""
        retry = RetryPolicy(max_attempts=3, base_delay=0.1)

        attempts = []

        def failing_func():
            attempts.append(1)
            if len(attempts) < 3:
                raise ValueError("fail")
            return "success"

        result = retry.execute(failing_func)
        self.assertEqual(result, "success")
        self.assertEqual(len(attempts), 3)


class TestMonitoringModules(unittest.TestCase):
    """监控模块测试"""

    def test_metrics_collector(self):
        """指标收集器测试"""
        collector = MetricsCollector()

        counter = collector.create_counter("requests", labels=["method"])
        counter.inc(labels={"method": "GET"})

        metrics_output = collector.export()
        self.assertIn("requests", metrics_output)

    def test_alert_manager(self):
        """告警管理器测试"""
        manager = AlertManager()

        rule = AlertRule(
            name="high_cpu",
            expr="$value > 80",
            severity=AlertSeverity.WARNING,
        )
        manager.add_rule(rule)

        alert = manager.evaluate("high_cpu", 90)
        self.assertIsNotNone(alert)
        self.assertEqual(alert.status.value, "firing")

    def test_health_check(self):
        """健康检查测试"""
        registry = HealthCheckRegistry()

        check = LambdaHealthCheck("test_check", lambda: True)
        registry.register(check)


class TestConfigModules(unittest.TestCase):
    """配置模块测试"""

    def test_config_loader(self):
        """配置加载器测试"""
        loader = ConfigLoader()
        loader.add_default({"debug": True, "port": 8080})

        config = loader.load()
        self.assertEqual(config.get("debug"), True)
        self.assertEqual(config.get("port"), 8080)

    def test_feature_flag(self):
        """特性开关测试"""
        manager = FeatureFlagManager()

        manager.add_flag(
            type(
                "Flag",
                (),
                {
                    "name": "new_feature",
                    "flag_type": 2,  # BOOLEAN
                    "enabled": True,
                    "description": "",
                    "default_value": True,
                    "percentage": 100.0,
                    "target_users": [],
                    "excluded_users": [],
                    "start_time": 0,
                    "end_time": 0,
                    "stages": [],
                    "tags": [],
                    "metadata": {},
                    "created_at": time.time(),
                    "updated_at": time.time(),
                },
            )()
        )

        self.assertTrue(manager.is_enabled("new_feature"))


class TestSecurityModules(unittest.TestCase):
    """安全模块测试"""

    def test_secret_manager(self):
        """密钥管理器测试"""
        manager = SecretManager()

        manager.set("api_key", "secret123")
        value = manager.get("api_key")

        self.assertEqual(value, "secret123")
        self.assertTrue(manager.exists("api_key"))

        manager.delete("api_key")
        self.assertFalse(manager.exists("api_key"))

    def test_audit_logger(self):
        """审计日志测试"""
        logger = AuditLogger()

        logger.log(
            action=1,  # CREATE
            resource_type="strategy",
            resource_id="s1",
            user_id="u1",
            details={"name": "Test"},
        )

        events = logger.query(limit=10)
        self.assertEqual(len(events), 1)

    def test_permission_manager(self):
        """权限管理器测试"""
        pm = PermissionManager()

        pm.create_user("user1", "User One")
        pm.assign_role("user1", "operator")

        has_perm = pm.has_permission("user1", "resource:create")
        self.assertTrue(has_perm)


class TestGatewayModules(unittest.TestCase):
    """网关模块测试"""

    def test_api_gateway(self):
        """API 网关测试"""
        gateway = APIGateway()

        @gateway.route("/test", HTTPMethod.GET)
        async def test_handler(request):
            return APIResponse.success({"message": "ok"})

        response = gateway.handle({"method": "GET", "path": "/test"})
        self.assertTrue(response.success)


class TestMarketModules(unittest.TestCase):
    """市场模块测试"""

    def test_strategy_market(self):
        """策略市场测试"""
        market = StrategyMarket()

        listing = market.publish_strategy(
            strategy_id="s1",
            author_id="a1",
            author_name="Author",
            name="Test Strategy",
            description="A test strategy",
            category=StrategyCategory.TREND,
            price=0,
        )

        self.assertIsNotNone(listing)
        self.assertEqual(listing.name, "Test Strategy")

        results = market.search(query="test")
        self.assertEqual(len(results), 1)


class TestOpsModules(unittest.TestCase):
    """运维模块测试"""

    def test_log_aggregator(self):
        """日志聚合器测试"""
        aggregator = LogAggregator()

        aggregator.info("Test message", source="test")
        aggregator.error("Error message", source="test")

        logs = aggregator.query(
            type(
                "Query",
                (),
                {
                    "start_time": 0,
                    "end_time": 0,
                    "levels": None,
                    "sources": None,
                    "capsule_id": "",
                    "trace_id": "",
                    "keywords": None,
                    "limit": 100,
                    "offset": 0,
                    "sort_order": "desc",
                },
            )()
        )

        self.assertEqual(len(logs), 2)

    def test_trace_collector(self):
        """链路追踪测试"""
        collector = TraceCollector()

        with collector.start_trace("test_operation") as trace:
            span = trace.start_span("child_span")
            trace.end_span()

        trace_data = collector.get_trace(trace._trace.trace_id)
        self.assertIsNotNone(trace_data)

    def test_profiler(self):
        """性能分析器测试"""
        profiler = Profiler()

        @profiler.profile("test_func")
        def test_func():
            time.sleep(0.01)
            return 42

        result = test_func()
        self.assertEqual(result, 42)

        stats = profiler.get_stats("test_func")
        self.assertIsNotNone(stats)
        self.assertEqual(stats.call_count, 1)

    def test_workflow_engine(self):
        """工作流引擎测试"""
        engine = WorkflowEngine()

        task = Task(
            task_id="task1",
            name="Test Task",
            task_type=TaskType.ACTION,
        )

        self.assertEqual(task.status, TaskStatus.PENDING)


class TestTradingModules(unittest.TestCase):
    """交易模块测试"""

    def test_strategy_simulator(self):
        """策略模拟器测试"""
        simulator = StrategySimulator(initial_capital=10000)

        prices = [100, 102, 101, 103, 105, 104]
        simulator.set_market_data("TEST", prices)

        def strategy(data, position):
            if data[-1] > data[-2]:
                return SignalType.BUY
            return SignalType.HOLD

        result = simulator.run("TEST", strategy)

        self.assertIn("total_pnl", result)
        self.assertIn("sharpe_ratio", result)

    def test_order_executor(self):
        """订单执行器测试"""
        executor = OrderExecutor()

        order_id = executor.submit_order(
            symbol="AAPL",
            side="buy",
            quantity=100,
            target_price=150,
        )

        plan = executor.get_plan(order_id)
        self.assertIsNotNone(plan)
        self.assertEqual(plan.symbol, "AAPL")

    def test_risk_calculator(self):
        """风险计算器测试"""
        calculator = RiskCalculator()

        returns = [0.01, -0.02, 0.03, -0.01, 0.02, 0.015]
        metrics = calculator.calculate(returns, portfolio_value=100000)

        self.assertGreater(metrics.sharpe_ratio, 0)
        self.assertLess(metrics.max_drawdown, 1)


def run_integration_tests():
    """运行集成测试"""
    # 创建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # 添加所有测试
    suite.addTests(loader.loadTestsFromTestCase(TestCoreModules))
    suite.addTests(loader.loadTestsFromTestCase(TestIsolationModules))
    suite.addTests(loader.loadTestsFromTestCase(TestMonitoringModules))
    suite.addTests(loader.loadTestsFromTestCase(TestConfigModules))
    suite.addTests(loader.loadTestsFromTestCase(TestSecurityModules))
    suite.addTests(loader.loadTestsFromTestCase(TestGatewayModules))
    suite.addTests(loader.loadTestsFromTestCase(TestMarketModules))
    suite.addTests(loader.loadTestsFromTestCase(TestOpsModules))
    suite.addTests(loader.loadTestsFromTestCase(TestTradingModules))

    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_integration_tests()
    exit(0 if success else 1)
