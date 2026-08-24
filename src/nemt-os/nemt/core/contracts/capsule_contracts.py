"""
L1 模块级接口契约

所有胶囊必须遵循此契约，确保层级间的有序递进。
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class CapsuleMetadata:
    """
    胶囊元数据

    用于描述胶囊的基本信息，便于管理和追踪。
    """

    capsule_id: str
    version: str = "1.0.0"
    layer: str = "L1"
    dependencies: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    description: str = ""

    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "capsule_id": self.capsule_id,
            "version": self.version,
            "layer": self.layer,
            "dependencies": self.dependencies,
            "created_at": self.created_at.isoformat(),
            "description": self.description,
        }


class ICapsuleContract(ABC):
    """
    L1 模块级接口契约

    所有胶囊必须实现此契约。
    自相似性体现在：生命周期方法与 L0 Engine 一致。

    五阶段方法：
    - observe(): 观察阶段 - 理解输入、需求、上下文
    - design(): 设计阶段 - 设计接口、定义骨架
    - implement(): 实现阶段 - 填充核心逻辑
    - verify(): 验证阶段 - 测试验证
    - integrate(): 集成阶段 - 与上下游对接
    """

    @property
    @abstractmethod
    def metadata(self) -> CapsuleMetadata:
        """获取胶囊元数据"""
        pass

    # ========================================
    # 五阶段方法
    # ========================================

    @abstractmethod
    def observe(self) -> dict[str, Any]:
        """
        【看】观察阶段

        理解输入、需求、上下文。

        Returns:
            观察报告字典，包含：
            - inputs: 输入数据定义
            - outputs: 输出数据定义
            - constraints: 约束条件
            - risks: 风险识别
            - dependencies: 依赖关系
        """
        pass

    @abstractmethod
    def design(self) -> dict[str, Any]:
        """
        【画】设计阶段

        设计接口、定义骨架。

        Returns:
            设计文档字典，包含：
            - public_api: 公开接口定义
            - input_schema: 输入模式
            - output_schema: 输出模式
            - internal_structure: 内部结构
            - event_contracts: 事件契约
        """
        pass

    @abstractmethod
    def implement(self) -> None:
        """
        【填】实现阶段

        填充核心逻辑。子类应在此实现具体功能。
        """
        pass

    @abstractmethod
    def verify(self) -> dict[str, Any]:
        """
        【验】验证阶段

        测试验证。

        Returns:
            验证结果字典，包含：
            - checks: 检查项列表
            - test_results: 测试结果
            - coverage: 覆盖率
        """
        pass

    @abstractmethod
    def integrate(self, upstream: Any = None, downstream: Any = None) -> None:
        """
        【连】集成阶段

        与上下游对接。

        Args:
            upstream: 上游模块
            downstream: 下游模块
        """
        pass

    # ========================================
    # 标准生命周期（与 L0 自相似）
    # ========================================

    @abstractmethod
    def init(self) -> None:
        """
        初始化

        订阅事件、设置初始状态。
        """
        pass

    @abstractmethod
    def exec(self) -> dict[str, Any]:
        """
        执行主要逻辑

        Returns:
            执行结果
        """
        pass

    @abstractmethod
    def shutdown(self) -> None:
        """
        关闭

        清理资源、取消订阅。
        """
        pass

    # ========================================
    # 分形迭代支持
    # ========================================

    def run_fractal_iteration(self) -> dict[str, Any]:
        """
        执行完整的五阶段迭代

        Returns:
            迭代结果字典
        """
        result = {
            "metadata": self.metadata.to_dict(),
            "phases": {},
            "status": "success",
        }

        try:
            # 看
            result["phases"]["observe"] = self.observe()

            # 画
            result["phases"]["design"] = self.design()

            # 填
            self.implement()
            result["phases"]["implement"] = {"status": "completed"}

            # 验
            result["phases"]["verify"] = self.verify()

            # 连
            self.integrate()
            result["phases"]["integrate"] = {"status": "completed"}

        except Exception as e:
            result["status"] = "failed"
            result["error"] = str(e)

        return result
