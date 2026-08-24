"""
分形迭代度量体系

量化每个层级的开发进度和质量。
"""

import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional


class PhaseStatus(Enum):
    """阶段状态"""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"


@dataclass
class PhaseMetrics:
    """单阶段度量"""

    phase: str
    status: PhaseStatus = PhaseStatus.PENDING
    start_time: datetime | None = None
    end_time: datetime | None = None
    duration_seconds: float = 0.0
    issues: list[str] = field(default_factory=list)
    artifacts: list[str] = field(default_factory=list)
    notes: str = ""

    @property
    def is_completed(self) -> bool:
        """是否完成"""
        return self.status == PhaseStatus.COMPLETED

    @property
    def is_blocked(self) -> bool:
        """是否阻塞"""
        return self.status == PhaseStatus.BLOCKED

    def start(self) -> None:
        """开始阶段"""
        self.status = PhaseStatus.IN_PROGRESS
        self.start_time = datetime.now()

    def complete(self, duration: float = None) -> None:
        """完成阶段"""
        self.status = PhaseStatus.COMPLETED
        self.end_time = datetime.now()
        if duration:
            self.duration_seconds = duration
        elif self.start_time:
            self.duration_seconds = (self.end_time - self.start_time).total_seconds()

    def block(self, reason: str) -> None:
        """阻塞阶段"""
        self.status = PhaseStatus.BLOCKED
        self.issues.append(reason)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "phase": self.phase,
            "status": self.status.value,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_seconds": self.duration_seconds,
            "issues": self.issues,
            "artifacts": self.artifacts,
            "notes": self.notes,
        }


@dataclass
class IterationMetrics:
    """
    迭代度量

    记录一次完整的五阶段迭代的度量数据。
    """

    iteration_id: str
    capsule_id: str
    layer: str
    timestamp: datetime = field(default_factory=datetime.now)
    version: str = "1.0.0"

    # 五阶段状态
    observe: PhaseMetrics = field(default_factory=lambda: PhaseMetrics("observe"))
    design: PhaseMetrics = field(default_factory=lambda: PhaseMetrics("design"))
    implement: PhaseMetrics = field(default_factory=lambda: PhaseMetrics("implement"))
    verify: PhaseMetrics = field(default_factory=lambda: PhaseMetrics("verify"))
    integrate: PhaseMetrics = field(default_factory=lambda: PhaseMetrics("integrate"))

    # 质量指标
    test_coverage: float = 0.0
    complexity: float = 0.0
    coupling: float = 0.0
    cohesion: float = 0.0

    # 总体评估
    quality_score: float = 0.0
    blockers: list[str] = field(default_factory=list)
    notes: str = ""

    @property
    def completion_rate(self) -> float:
        """完成率"""
        phases = [
            self.observe,
            self.design,
            self.implement,
            self.verify,
            self.integrate,
        ]
        completed = sum(1 for p in phases if p.is_completed)
        return completed / len(phases) * 100

    @property
    def total_duration(self) -> float:
        """总耗时（秒）"""
        phases = [
            self.observe,
            self.design,
            self.implement,
            self.verify,
            self.integrate,
        ]
        return sum(p.duration_seconds for p in phases)

    @property
    def is_blocked(self) -> bool:
        """是否有阻塞"""
        return any(p.is_blocked for p in self.get_all_phases())

    @property
    def all_completed(self) -> bool:
        """是否全部完成"""
        return all(p.is_completed for p in self.get_all_phases())

    def get_all_phases(self) -> list[PhaseMetrics]:
        """获取所有阶段"""
        return [self.observe, self.design, self.implement, self.verify, self.integrate]

    def get_phase(self, name: str) -> PhaseMetrics | None:
        """获取指定阶段"""
        phase_map = {
            "observe": self.observe,
            "design": self.design,
            "implement": self.implement,
            "verify": self.verify,
            "integrate": self.integrate,
        }
        return phase_map.get(name)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "iteration_id": self.iteration_id,
            "capsule_id": self.capsule_id,
            "layer": self.layer,
            "version": self.version,
            "timestamp": self.timestamp.isoformat(),
            "completion_rate": self.completion_rate,
            "total_duration_seconds": self.total_duration,
            "is_blocked": self.is_blocked,
            "phases": {
                "observe": self.observe.to_dict(),
                "design": self.design.to_dict(),
                "implement": self.implement.to_dict(),
                "verify": self.verify.to_dict(),
                "integrate": self.integrate.to_dict(),
            },
            "quality": {
                "test_coverage": self.test_coverage,
                "complexity": self.complexity,
                "coupling": self.coupling,
                "cohesion": self.cohesion,
                "score": self.quality_score,
            },
            "blockers": self.blockers,
            "notes": self.notes,
        }

    def to_json(self) -> str:
        """转换为 JSON 字符串"""
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False)


class FractalMetricsCollector:
    """
    分形度量收集器

    收集并分析分形迭代的度量数据。
    提供单例模式。
    """

    _instance: Optional["FractalMetricsCollector"] = None

    def __init__(self):
        self._iterations: list[IterationMetrics] = []
        self._current_iteration: IterationMetrics | None = None
        self._callbacks: dict[str, list[callable]] = {
            "on_iteration_start": [],
            "on_iteration_end": [],
            "on_phase_start": [],
            "on_phase_end": [],
            "on_block": [],
        }

    @classmethod
    def get_instance(cls) -> "FractalMetricsCollector":
        """获取单例实例"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def register_callback(self, event: str, callback: callable) -> None:
        """
        注册回调

        Args:
            event: 事件名
            callback: 回调函数
        """
        if event in self._callbacks:
            self._callbacks[event].append(callback)

    def _trigger_callbacks(self, event: str, *args, **kwargs) -> None:
        """触发回调"""
        for callback in self._callbacks.get(event, []):
            try:
                callback(*args, **kwargs)
            except Exception:
                pass

    def start_iteration(self, capsule_id: str, layer: str, version: str = "1.0.0") -> IterationMetrics:
        """
        开始新迭代

        Args:
            capsule_id: 胶囊 ID
            layer: 层级
            version: 版本号

        Returns:
            新创建的迭代度量
        """
        iteration_id = f"{capsule_id}_{layer}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self._current_iteration = IterationMetrics(
            iteration_id=iteration_id,
            capsule_id=capsule_id,
            layer=layer,
            version=version,
        )

        self._trigger_callbacks("on_iteration_start", self._current_iteration)
        return self._current_iteration

    def start_phase(self, phase: str) -> None:
        """
        开始阶段

        Args:
            phase: 阶段名 (observe, design, implement, verify, integrate)
        """
        if self._current_iteration is None:
            return

        phase_metrics = self._current_iteration.get_phase(phase)
        if phase_metrics:
            phase_metrics.start()
            self._trigger_callbacks("on_phase_start", phase, phase_metrics)

    def complete_phase(self, phase: str, duration: float = None, notes: str = "") -> None:
        """
        完成阶段

        Args:
            phase: 阶段名
            duration: 指定耗时
            notes: 备注
        """
        if self._current_iteration is None:
            return

        phase_metrics = self._current_iteration.get_phase(phase)
        if phase_metrics:
            phase_metrics.complete(duration)
            if notes:
                phase_metrics.notes = notes
            self._trigger_callbacks("on_phase_end", phase, phase_metrics)

    def block_phase(self, phase: str, reason: str) -> None:
        """
        阻塞阶段

        Args:
            phase: 阶段名
            reason: 阻塞原因
        """
        if self._current_iteration is None:
            return

        phase_metrics = self._current_iteration.get_phase(phase)
        if phase_metrics:
            phase_metrics.block(reason)
            self._current_iteration.blockers.append(f"{phase}: {reason}")
            self._trigger_callbacks("on_block", phase, reason)

    def end_iteration(self, quality_score: float = None, notes: str = "") -> IterationMetrics | None:
        """
        结束迭代

        Args:
            quality_score: 质量分数
            notes: 备注

        Returns:
            完成的迭代度量
        """
        if self._current_iteration is None:
            return None

        if quality_score is not None:
            self._current_iteration.quality_score = quality_score
        else:
            self._current_iteration.quality_score = self._calculate_quality_score()

        if notes:
            self._current_iteration.notes = notes

        self._iterations.append(self._current_iteration)
        result = self._current_iteration
        self._trigger_callbacks("on_iteration_end", result)
        self._current_iteration = None
        return result

    def _calculate_quality_score(self) -> float:
        """计算质量分数"""
        if self._current_iteration is None:
            return 0.0

        # 基于完成率
        completion_score = self._current_iteration.completion_rate

        # 基于时间分配
        ideal_times = {
            "observe": 15,
            "design": 25,
            "implement": 35,
            "verify": 15,
            "integrate": 10,
        }

        time_score = 100.0
        phases = ["observe", "design", "implement", "verify", "integrate"]

        for phase in phases:
            phase_metrics = self._current_iteration.get_phase(phase)
            if phase_metrics and phase_metrics.duration_seconds > 0:
                ideal = ideal_times[phase] * 60
                actual = phase_metrics.duration_seconds
                ratio = ideal / actual if actual >= ideal else actual / ideal
                time_score *= ratio

        time_score = min(100.0, max(0.0, time_score))

        # 综合评分
        return (completion_score + time_score) / 2

    def get_current_iteration(self) -> IterationMetrics | None:
        """获取当前迭代"""
        return self._current_iteration

    def get_iterations(self, capsule_id: str = None, layer: str = None) -> list[IterationMetrics]:
        """
        获取迭代列表

        Args:
            capsule_id: 可选，按胶囊 ID 过滤
            layer: 可选，按层级过滤

        Returns:
            过滤后的迭代列表
        """
        result = self._iterations

        if capsule_id:
            result = [i for i in result if i.capsule_id == capsule_id]

        if layer:
            result = [i for i in result if i.layer == layer]

        return result

    def get_summary(self) -> dict[str, Any]:
        """
        获取汇总统计

        Returns:
            汇总字典
        """
        if not self._iterations:
            return {
                "total_iterations": 0,
                "message": "No iterations recorded",
            }

        total_duration = sum(i.total_duration for i in self._iterations)
        avg_completion = sum(i.completion_rate for i in self._iterations) / len(self._iterations)
        avg_quality = sum(i.quality_score for i in self._iterations) / len(self._iterations)

        # 按层级分组
        by_layer: dict[str, dict[str, Any]] = {}
        for i in self._iterations:
            if i.layer not in by_layer:
                by_layer[i.layer] = {"count": 0, "iterations": []}
            by_layer[i.layer]["count"] += 1
            by_layer[i.layer]["iterations"].append(i.to_dict())

        layer_summary = {}
        for layer, data in by_layer.items():
            iterations = data["iterations"]
            layer_summary[layer] = {
                "count": data["count"],
                "avg_completion": sum(it["completion_rate"] for it in iterations) / len(iterations),
                "avg_quality": sum(it["quality"]["score"] for it in iterations) / len(iterations),
                "total_duration_minutes": sum(it["total_duration_seconds"] for it in iterations) / 60,
            }

        # 按胶囊分组
        by_capsule: dict[str, dict[str, Any]] = {}
        for i in self._iterations:
            if i.capsule_id not in by_capsule:
                by_capsule[i.capsule_id] = {"count": 0, "iterations": []}
            by_capsule[i.capsule_id]["count"] += 1
            by_capsule[i.capsule_id]["iterations"].append(i.to_dict())

        capsule_summary = {}
        for capsule_id, data in by_capsule.items():
            iterations = data["iterations"]
            capsule_summary[capsule_id] = {
                "count": data["count"],
                "avg_completion": sum(it["completion_rate"] for it in iterations) / len(iterations),
                "avg_quality": sum(it["quality"]["score"] for it in iterations) / len(iterations),
            }

        return {
            "total_iterations": len(self._iterations),
            "total_duration_minutes": total_duration / 60,
            "overall_completion_rate": avg_completion,
            "overall_quality_score": avg_quality,
            "by_layer": layer_summary,
            "by_capsule": capsule_summary,
            "latest_iteration": self._iterations[-1].to_dict() if self._iterations else None,
        }

    def export_json(self, filepath: str) -> None:
        """
        导出为 JSON 文件

        Args:
            filepath: 文件路径
        """
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self.get_summary(), f, indent=2, ensure_ascii=False)

    def reset(self) -> None:
        """重置所有数据"""
        self._iterations.clear()
        self._current_iteration = None
