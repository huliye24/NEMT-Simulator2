"""
Test Examples - 测试示例

展示如何使用测试框架。
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))



class TestCapsuleExample:
    """Capsule 测试示例"""

    def test_capsule_init(self, test_env):
        """测试 Capsule 初始化"""
        from nemt.core.capsule import ModuleCapsule

        class TestCapsule(ModuleCapsule):
            def init(self):
                self._data = {"initialized": True}

            def exec(self):
                return {"data": self._data}

        capsule = TestCapsule("test")
        capsule.event_bus = test_env.event_bus
        capsule.config = test_env.config_center

        capsule.init()
        assert capsule.is_initialized

        result = capsule.exec()
        assert result["data"]["initialized"] is True

    def test_capsule_lifecycle(self, test_env):
        """测试 Capsule 生命周期"""
        from nemt.core.capsule import ModuleCapsule

        class LifecycleCapsule(ModuleCapsule):
            def init(self):
                self.lifecycle = ["init"]

            def exec(self):
                self.lifecycle.append("exec")
                return {"lifecycle": self.lifecycle}

        capsule = LifecycleCapsule("lifecycle")
        capsule.event_bus = test_env.event_bus
        capsule.config = test_env.config_center

        capsule.init()
        assert "init" in capsule.lifecycle

        capsule.exec()
        assert "exec" in capsule.lifecycle

        capsule.shutdown()


class TestEventBusExample:
    """EventBus 测试示例"""

    def test_event_subscribe_publish(self, mock_event_bus):
        """测试事件订阅和发布"""
        events_received = []

        def handler(event):
            events_received.append(event)

        mock_event_bus.subscribe("test.event", handler)
        mock_event_bus.publish("test.event", {"data": "hello"})

        assert len(events_received) == 1
        assert events_received[0]["data"] == "hello"

    def test_event_unsubscribe(self, mock_event_bus):
        """测试取消订阅"""
        call_count = [0]

        def handler(event):
            call_count[0] += 1

        mock_event_bus.subscribe("test.event", handler)
        mock_event_bus.publish("test.event", {})
        assert call_count[0] == 1

        mock_event_bus.unsubscribe("test.event", handler)
        mock_event_bus.publish("test.event", {})
        assert call_count[0] == 1  # 未增加


class TestConfigCenterExample:
    """ConfigCenter 测试示例"""

    def test_config_get_set(self, mock_config):
        """测试配置获取和设置"""
        mock_config.set("test.key", "value")
        assert mock_config.get("test.key") == "value"

    def test_config_watch(self, mock_config):
        """测试配置监听"""
        changes = []

        def on_change(key, old, new):
            changes.append({"key": key, "old": old, "new": new})

        mock_config.watch("test.key", on_change)
        mock_config.set("test.key", "new_value")

        assert len(changes) == 1
        assert changes[0]["new"] == "new_value"

    def test_config_history(self, mock_config):
        """测试配置历史"""
        mock_config.set("test.key", "v1")
        mock_config.set("test.key", "v2")
        mock_config.set("test.key", "v3")

        history = mock_config.get_history()
        assert len(history) == 3


class TestDIContainerExample:
    """DI Container 测试示例"""

    def test_container_register_resolve(self):
        """测试容器注册和解析"""
        from nemt.core.di import DIContainer

        container = DIContainer()

        class MyService:
            def __init__(self):
                self.value = "test"

        container.register(MyService)

        service = container.resolve(MyService)
        assert service.value == "test"

    def test_container_singleton(self):
        """测试单例模式"""
        from nemt.core.di import DIContainer, Lifetime

        container = DIContainer()

        class SingletonService:
            pass

        container.register(SingletonService, lifetime=Lifetime.SINGLETON)

        s1 = container.resolve(SingletonService)
        s2 = container.resolve(SingletonService)

        assert s1 is s2  # 同一个实例


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
