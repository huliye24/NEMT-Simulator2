"""
NEMT 分形迭代集成测试

测试所有分形迭代组件的集成功能。
"""

import time

import pytest

from nemt.core.capsule import FractalCapsule
from nemt.core.layer_lock import LayerLockManager, LockStatus

# 导入分形框架
from nemt.core.metrics import FractalMetricsCollector, PhaseStatus
from nemt.core.view_switcher import ViewMode, ViewSwitcher


class TestCapsule(FractalCapsule):
    """测试用胶囊"""

    def __init__(self, capsule_id: str = "test"):
        super().__init__(capsule_id, version="1.0.0")
        self.initialized = False

    def init(self):
        self.initialized = True

    def exec(self):
        return {"status": "ok"}

    def shutdown(self):
        self.initialized = False

    def observe_phase(self):
        return {
            "capsule_id": self._capsule_id,
            "test_data": "observe",
        }

    def design_phase(self):
        return {
            "capsule_id": self._capsule_id,
            "test_data": "design",
        }

    def implement_phase(self):
        self.test_data = "implemented"

    def verify_phase(self):
        return {"passed": True}

    def integrate_phase(self):
        pass


class TestFractalMetrics:
    """测试度量收集器"""

    def test_start_iteration(self):
        collector = FractalMetricsCollector.get_instance()
        collector.reset()

        metrics = collector.start_iteration("test_capsule", "L1")

        assert metrics.capsule_id == "test_capsule"
        assert metrics.layer == "L1"
        assert metrics.completion_rate == 0.0

    def test_phase_lifecycle(self):
        collector = FractalMetricsCollector.get_instance()
        collector.reset()

        collector.start_iteration("test_capsule", "L1")
        collector.start_phase("observe")
        time.sleep(0.01)
        collector.complete_phase("observe")

        metrics = collector.get_current_iteration()
        assert metrics.observe.status == PhaseStatus.COMPLETED
        assert metrics.completion_rate == 20.0  # 1/5 phases

    def test_end_iteration(self):
        collector = FractalMetricsCollector.get_instance()
        collector.reset()

        collector.start_iteration("test_capsule", "L1")
        collector.start_phase("observe")
        collector.complete_phase("observe")
        result = collector.end_iteration()

        assert result is not None
        assert result.completion_rate == 20.0

    def test_summary(self):
        collector = FractalMetricsCollector.get_instance()
        collector.reset()

        collector.start_iteration("capsule1", "L1")
        collector.start_phase("observe")
        collector.complete_phase("observe")
        collector.end_iteration()

        collector.start_iteration("capsule2", "L1")
        collector.start_phase("observe")
        collector.complete_phase("observe")
        collector.end_iteration()

        summary = collector.get_summary()
        assert summary["total_iterations"] == 2


class TestViewSwitcher:
    """测试视角切换器"""

    def test_switch_to_macro(self):
        vs = ViewSwitcher()

        context = vs.macro_view()

        assert context.mode == ViewMode.MACRO
        assert context.layer == "L0"

    def test_switch_to_micro(self):
        vs = ViewSwitcher()

        context = vs.micro_view("test_capsule", "L2")

        assert context.mode == ViewMode.MICRO
        assert context.capsule_id == "test_capsule"
        assert context.layer == "L2"

    def test_switch_to_fractal(self):
        vs = ViewSwitcher()

        context = vs.fractal_view("test_capsule", "L1")

        assert context.mode == ViewMode.FRACTAL
        assert context.layer == "L1"

    def test_go_back(self):
        vs = ViewSwitcher()

        vs.macro_view()
        vs.micro_view("test")
        old_view = vs.go_back()

        assert old_view is not None
        assert old_view.mode == ViewMode.MACRO

    def test_snapshot(self):
        vs = ViewSwitcher()

        vs.macro_view()
        snapshot = vs.save_snapshot("backup", capsules=["c1", "c2"])

        assert snapshot is not None
        assert len(snapshot.capsules) == 2


class TestLayerLock:
    """测试层级锁定"""

    def test_register_contract(self):
        manager = LayerLockManager.get_instance()
        manager.reset()

        contract = manager.register_contract("L0", "test_module", "test_contract")

        assert contract.layer == "L0"
        assert contract.owner == "test_module"
        assert contract.status == LockStatus.UNLOCKED

    def test_freeze_layer(self):
        manager = LayerLockManager.get_instance()
        manager.reset()

        # L0 可以直接冻结
        result = manager.freeze_contract("L0", "system", "l0_main")
        assert result is True

    def test_dependency_order(self):
        manager = LayerLockManager.get_instance()
        manager.reset()

        # L1 需要 L0 先冻结
        assert manager.can_start_layer("L0") is True
        assert manager.can_start_layer("L1") is False  # L0 未冻结

        # 冻结 L0
        manager.freeze_contract("L0", "system", "l0_main")

        # 现在 L1 可以开始
        assert manager.can_start_layer("L1") is True

    def test_layer_status(self):
        manager = LayerLockManager.get_instance()
        manager.reset()

        manager.register_contract("L0", "system", "main")
        manager.freeze_contract("L0", "system", "main")

        status = manager.get_layer_status("L0")
        assert status["is_frozen"] is True


class TestFractalCapsule:
    """测试分形胶囊"""

    def test_capsule_creation(self):
        capsule = TestCapsule("test_capsule")

        assert capsule.capsule_id == "test_capsule"
        assert capsule.version == "1.0.0"
        assert capsule.layer == "L1"

    def test_run_iteration(self):
        capsule = TestCapsule("test_iteration")

        result = capsule.run_fractal_iteration()

        assert result["status"] == "success"
        assert "phases" in result
        assert "observe" in result["phases"]
        assert "design" in result["phases"]
        assert "implement" in result["phases"]
        assert "verify" in result["phases"]
        assert "integrate" in result["phases"]

    def test_iteration_count(self):
        capsule = TestCapsule()

        capsule.run_fractal_iteration()
        capsule.run_fractal_iteration()

        assert capsule.iteration_count == 2

    def test_get_summary(self):
        capsule = TestCapsule()

        capsule.run_fractal_iteration()
        summary = capsule.get_iteration_summary()

        assert "capsule_id" in summary
        assert "iteration_count" in summary
        assert summary["iteration_count"] == 1


class TestIntegration:
    """集成测试"""

    def test_full_workflow(self):
        # 1. 创建度量收集器
        collector = FractalMetricsCollector.get_instance()
        collector.reset()

        # 2. 创建胶囊
        capsule = TestCapsule("integration_test")

        # 3. 开始迭代
        collector.start_iteration("integration_test", "L1")

        # 4. 运行胶囊迭代
        capsule_result = capsule.run_fractal_iteration()
        assert capsule_result["status"] == "success"

        # 5. 结束迭代
        collector.end_iteration()

        # 6. 检查结果
        summary = collector.get_summary()
        assert summary["total_iterations"] == 1

    def test_view_and_lock_integration(self):
        # 视角切换
        vs = ViewSwitcher()
        vs.macro_view()

        # 层级锁定
        manager = LayerLockManager.get_instance()
        manager.reset()

        status = manager.get_layer_status("L0")
        assert status["layer"] == "L0"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
