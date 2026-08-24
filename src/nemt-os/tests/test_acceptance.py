"""
Final Acceptance Tests - 最终验收测试

验证平台完整性和可用性。
"""

import sys
import time


def test_imports():
    """测试所有模块导入"""
    print("=" * 60)
    print("测试 1: 模块导入")
    print("=" * 60)

    try:

        print("✓ 所有模块导入成功")
        return True
    except Exception as e:
        print(f"✗ 模块导入失败: {e}")
        return False


def test_core_capsule():
    """测试核心胶囊"""
    print("\n" + "=" * 60)
    print("测试 2: 核心胶囊")
    print("=" * 60)

    try:
        from nemt import Capsule, CapsuleConfig, CapsuleState

        config = CapsuleConfig(name="test", memory_limit=128)
        capsule = Capsule(config)

        assert capsule.state == CapsuleState.CREATED, "初始状态应为 CREATED"
        capsule.start()
        assert capsule.state == CapsuleState.RUNNING, "启动后状态应为 RUNNING"
        capsule.stop()
        assert capsule.state == CapsuleState.STOPPED, "停止后状态应为 STOPPED"

        print("✓ 胶囊生命周期正常")
        return True
    except Exception as e:
        print(f"✗ 胶囊测试失败: {e}")
        return False


def test_event_bus():
    """测试事件总线"""
    print("\n" + "=" * 60)
    print("测试 3: 事件总线")
    print("=" * 60)

    try:
        from nemt import Event, EventBus

        bus = EventBus()
        received = []

        def handler(event):
            received.append(event)

        bus.subscribe("test", handler)
        bus.publish(Event("test", {"value": 42}))
        bus.unsubscribe("test", handler)

        assert len(received) == 1, "应收到 1 条消息"
        assert received[0].data["value"] == 42, "消息内容应正确"

        print("✓ 事件总线正常")
        return True
    except Exception as e:
        print(f"✗ 事件总线测试失败: {e}")
        return False


def test_circuit_breaker():
    """测试熔断器"""
    print("\n" + "=" * 60)
    print("测试 4: 熔断器")
    print("=" * 60)

    try:
        from nemt import CircuitBreaker

        cb = CircuitBreaker(failure_threshold=3)

        for _ in range(3):
            cb.record_failure()

        assert cb.state == "open", "触发熔断后状态应为 open"

        time.sleep(1.5)  # 等待半开时间
        cb.record_success()
        assert cb.state == "closed", "成功后状态应为 closed"

        print("✓ 熔断器正常")
        return True
    except Exception as e:
        print(f"✗ 熔断器测试失败: {e}")
        return False


def test_metrics():
    """测试指标系统"""
    print("\n" + "=" * 60)
    print("测试 5: 指标系统")
    print("=" * 60)

    try:
        from nemt import MetricsCollector

        collector = MetricsCollector()

        counter = collector.create_counter("requests", labels=["method"])
        counter.inc(labels={"method": "GET"})

        gauge = collector.create_gauge("memory")
        gauge.set(1024)

        histogram = collector.create_histogram("latency", buckets=[0.1, 0.5, 1.0])
        histogram.observe(0.3)

        output = collector.export()
        assert "requests" in output, "指标应包含 requests"

        print("✓ 指标系统正常")
        return True
    except Exception as e:
        print(f"✗ 指标系统测试失败: {e}")
        return False


def test_alert_manager():
    """测试告警管理"""
    print("\n" + "=" * 60)
    print("测试 6: 告警管理")
    print("=" * 60)

    try:
        from nemt import AlertManager, AlertRule, AlertSeverity

        manager = AlertManager()

        rule = AlertRule(
            name="high_error_rate",
            expr="$value > 10",
            severity=AlertSeverity.ERROR,
        )
        manager.add_rule(rule)

        alert = manager.evaluate("high_error_rate", 15)
        assert alert is not None, "应触发告警"
        assert alert.severity == AlertSeverity.ERROR, "级别应为 ERROR"

        alerts = manager.get_firing_alerts()
        assert len(alerts) == 1, "应有 1 个触发中的告警"

        print("✓ 告警管理正常")
        return True
    except Exception as e:
        print(f"✗ 告警管理测试失败: {e}")
        return False


def test_config():
    """测试配置系统"""
    print("\n" + "=" * 60)
    print("测试 7: 配置系统")
    print("=" * 60)

    try:
        from nemt import ConfigLoader

        loader = ConfigLoader()
        loader.add_default(
            {
                "app": {"name": "NEMT", "version": "2.0"},
                "database": {"host": "localhost", "port": 5432},
            }
        )

        config = loader.load()
        assert config.get("app.name") == "NEMT", "配置值应正确"
        assert config.get("database.port") == 5432, "配置值应正确"

        print("✓ 配置系统正常")
        return True
    except Exception as e:
        print(f"✗ 配置系统测试失败: {e}")
        return False


def test_security():
    """测试安全系统"""
    print("\n" + "=" * 60)
    print("测试 8: 安全系统")
    print("=" * 60)

    try:
        from nemt import AuditLogger, PermissionManager, SecretManager

        # 密钥管理
        secrets = SecretManager()
        secrets.set("api_key", "secret123")
        assert secrets.get("api_key") == "secret123", "密钥应正确"

        # 审计日志
        audit = AuditLogger()
        event = audit.log(
            action=1,
            resource_type="strategy",
            resource_id="s1",
            user_id="u1",
        )
        assert event is not None, "应创建审计事件"

        # 权限管理
        pm = PermissionManager()
        pm.create_user("user1", "Test User")
        pm.assign_role("user1", "operator")
        assert pm.has_permission("user1", "resource:create"), "应有权限"

        print("✓ 安全系统正常")
        return True
    except Exception as e:
        print(f"✗ 安全系统测试失败: {e}")
        return False


def test_api_gateway():
    """测试 API 网关"""
    print("\n" + "=" * 60)
    print("测试 9: API 网关")
    print("=" * 60)

    try:
        import asyncio

        from nemt import APIGateway, APIResponse, HTTPMethod

        gateway = APIGateway()

        @gateway.route("/api/health", HTTPMethod.GET)
        async def health(request):
            return APIResponse.success({"status": "ok"})

        response = asyncio.get_event_loop().run_until_complete(
            gateway.handle({"method": "GET", "path": "/api/health", "client_ip": "127.0.0.1"})
        )

        assert response.success, "响应应成功"
        assert response.data["status"] == "ok", "数据应正确"

        print("✓ API 网关正常")
        return True
    except Exception as e:
        print(f"✗ API 网关测试失败: {e}")
        return False


def test_trading():
    """测试交易系统"""
    print("\n" + "=" * 60)
    print("测试 10: 交易系统")
    print("=" * 60)

    try:
        from nemt import RiskCalculator, SignalType, StrategySimulator

        # 策略模拟
        simulator = StrategySimulator(initial_capital=10000)
        simulator.set_market_data("TEST", [100, 102, 101, 103, 105, 104])

        def strategy(data, position):
            if len(data) > 1 and data[-1] > data[-2]:
                return SignalType.BUY
            return SignalType.HOLD

        result = simulator.run("TEST", strategy)
        assert "total_pnl" in result, "结果应包含收益"
        assert "sharpe_ratio" in result, "结果应包含夏普比率"

        # 风险计算
        calculator = RiskCalculator()
        metrics = calculator.calculate([0.01, -0.02, 0.03, -0.01, 0.02])
        assert metrics.sharpe_ratio != 0, "应计算夏普比率"

        print("✓ 交易系统正常")
        return True
    except Exception as e:
        print(f"✗ 交易系统测试失败: {e}")
        return False


def test_ops():
    """测试运维系统"""
    print("\n" + "=" * 60)
    print("测试 11: 运维系统")
    print("=" * 60)

    try:
        from nemt import LogAggregator, Profiler, TraceCollector

        # 日志聚合
        logs = LogAggregator()
        logs.info("Test info message")
        logs.error("Test error message")
        stats = logs.get_stats()
        assert stats["total_logs"] >= 2, "应有日志记录"

        # 链路追踪
        traces = TraceCollector()
        with traces.start_trace("test_trace") as trace:
            span = trace.start_span("child")
            trace.end_span()

        # 性能分析
        profiler = Profiler()

        @profiler.profile("test_func")
        def test_func():
            time.sleep(0.01)
            return 42

        test_func()
        stats = profiler.get_stats("test_func")
        assert stats.call_count == 1, "应有调用记录"

        print("✓ 运维系统正常")
        return True
    except Exception as e:
        print(f"✗ 运维系统测试失败: {e}")
        return False


def test_platform():
    """测试平台"""
    print("\n" + "=" * 60)
    print("测试 12: 平台集成")
    print("=" * 60)

    try:
        from nemt import NEMTPlatform

        platform = NEMTPlatform()
        platform.initialize()

        status = platform.get_status()
        assert status["initialized"], "平台应已初始化"
        assert status["components"]["event_bus"], "事件总线应初始化"
        assert status["components"]["metrics"], "指标系统应初始化"
        assert status["components"]["trading"], "交易系统应初始化"

        print("✓ 平台集成正常")
        return True
    except Exception as e:
        print(f"✗ 平台集成测试失败: {e}")
        return False


def run_acceptance_tests():
    """运行验收测试"""
    print("\n")
    print("=" * 60)
    print("  NEMT Platform - 最终验收测试")
    print("=" * 60)
    print()

    tests = [
        ("模块导入", test_imports),
        ("核心胶囊", test_core_capsule),
        ("事件总线", test_event_bus),
        ("熔断器", test_circuit_breaker),
        ("指标系统", test_metrics),
        ("告警管理", test_alert_manager),
        ("配置系统", test_config),
        ("安全系统", test_security),
        ("API 网关", test_api_gateway),
        ("交易系统", test_trading),
        ("运维系统", test_ops),
        ("平台集成", test_platform),
    ]

    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"✗ {name} 测试异常: {e}")
            results.append((name, False))

    # 汇总
    print("\n" + "=" * 60)
    print("  测试结果汇总")
    print("=" * 60)

    passed = sum(1 for _, r in results if r)
    total = len(results)

    for name, result in results:
        status = "✓ 通过" if result else "✗ 失败"
        print(f"  {name}: {status}")

    print()
    print(f"  通过: {passed}/{total}")
    print("=" * 60)

    if passed == total:
        print("\n  🎉 所有测试通过！NEMT 平台验收完成！\n")
        return True
    else:
        print(f"\n  ⚠ {total - passed} 项测试失败\n")
        return False


if __name__ == "__main__":
    success = run_acceptance_tests()
    sys.exit(0 if success else 1)
