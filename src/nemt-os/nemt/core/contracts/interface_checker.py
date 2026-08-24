"""
Interface Compatibility Checker - 接口兼容性检查器

检测接口变更是否破坏向后兼容性。

版本: v1.0.0
更新: 2026-04-27
"""

from __future__ import annotations

import inspect
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


class BreakingChangeType:
    """破坏性变更类型"""

    METHOD_REMOVED = "method_removed"
    PARAMETER_REMOVED = "parameter_removed"
    PARAMETER_TYPE_CHANGED = "parameter_type_changed"
    RETURN_TYPE_CHANGED = "return_type_changed"
    EXCEPTION_ADDED = "exception_added"
    REQUIRED_PARAMETER_ADDED = "required_parameter_added"


@dataclass
class InterfaceChange:
    """接口变更"""

    file_path: str
    class_name: str
    method_name: str
    change_type: str
    severity: str  # breaking, warning, info
    description: str
    old_signature: str = ""
    new_signature: str = ""


@dataclass
class CompatibilityReport:
    """兼容性报告"""

    old_version: str
    new_version: str
    timestamp: datetime = field(default_factory=datetime.now)

    breaking_changes: list[InterfaceChange] = field(default_factory=list)
    warnings: list[InterfaceChange] = field(default_factory=list)
    info: list[InterfaceChange] = field(default_factory=list)

    @property
    def is_compatible(self) -> bool:
        return len(self.breaking_changes) == 0

    def add_breaking_change(self, change: InterfaceChange) -> None:
        self.breaking_changes.append(change)

    def add_warning(self, change: InterfaceChange) -> None:
        self.warnings.append(change)

    def add_info(self, change: InterfaceChange) -> None:
        self.info.append(change)


class InterfaceExtractor:
    """接口提取器"""

    @staticmethod
    def extract_class_interface(cls: type) -> dict[str, dict]:
        """提取类的接口定义"""
        interface = {}

        for name, method in inspect.getmembers(cls, predicate=inspect.isfunction):
            # 跳过私有方法
            if name.startswith("_") and not name.startswith("__"):
                continue

            sig = inspect.signature(method)
            interface[name] = {
                "signature": str(sig),
                "parameters": [
                    {
                        "name": p.name,
                        "default": p.default if p.default != inspect.Parameter.empty else None,
                        "kind": str(p.kind),
                    }
                    for p in sig.parameters.values()
                ],
                "return_annotation": (
                    str(sig.return_annotation) if sig.return_annotation != inspect.Signature.empty else None
                ),
            }

        return interface


class CompatibilityChecker:
    """兼容性检查器"""

    def __init__(self):
        self.extractor = InterfaceExtractor()

    def check_class_compatibility(
        self,
        old_class: type,
        new_class: type,
        file_path: str = "",
        old_version: str = "1.0",
        new_version: str = "1.1",
    ) -> CompatibilityReport:
        """
        检查类接口兼容性

        Args:
            old_class: 旧版本类
            new_class: 新版本类
            file_path: 文件路径
            old_version: 旧版本号
            new_version: 新版本号

        Returns:
            兼容性报告
        """
        old_interface = self.extractor.extract_class_interface(old_class)
        new_interface = self.extractor.extract_class_interface(new_class)

        report = CompatibilityReport(
            old_version=old_version,
            new_version=new_version,
        )

        # 检查方法移除
        for method_name, old_sig in old_interface.items():
            if method_name not in new_interface:
                report.add_breaking_change(
                    InterfaceChange(
                        file_path=file_path,
                        class_name=old_class.__name__,
                        method_name=method_name,
                        change_type=BreakingChangeType.METHOD_REMOVED,
                        severity="breaking",
                        description=f"Method '{method_name}' was removed",
                        old_signature=old_sig["signature"],
                    )
                )

        # 检查参数变更
        for method_name, new_sig in new_interface.items():
            if method_name not in old_interface:
                # 新方法，不需要检查
                continue

            old_sig = old_interface[method_name]
            self._check_parameters(report, file_path, old_class.__name__, method_name, old_sig, new_sig)

        # 检查新增必需参数
        for method_name, new_sig in new_interface.items():
            if method_name not in old_interface:
                continue

            old_sig = old_interface[method_name]
            self._check_new_required_params(report, file_path, old_class.__name__, method_name, old_sig, new_sig)

        return report

    def _check_parameters(
        self,
        report: CompatibilityReport,
        file_path: str,
        class_name: str,
        method_name: str,
        old_sig: dict,
        new_sig: dict,
    ) -> None:
        """检查参数变更"""
        old_params = {p["name"]: p for p in old_sig["parameters"]}
        new_params = {p["name"]: p for p in new_sig["parameters"]}

        # 检查移除的参数
        for param_name, old_param in old_params.items():
            if param_name not in new_params:
                # 检查是否有默认值
                if old_param["default"] is None:
                    report.add_breaking_change(
                        InterfaceChange(
                            file_path=file_path,
                            class_name=class_name,
                            method_name=method_name,
                            change_type=BreakingChangeType.PARAMETER_REMOVED,
                            severity="breaking",
                            description=f"Required parameter '{param_name}' was removed",
                            old_signature=old_sig["signature"],
                            new_signature=new_sig["signature"],
                        )
                    )
                else:
                    report.add_warning(
                        InterfaceChange(
                            file_path=file_path,
                            class_name=class_name,
                            method_name=method_name,
                            change_type=BreakingChangeType.PARAMETER_REMOVED,
                            severity="warning",
                            description=f"Optional parameter '{param_name}' was removed",
                            old_signature=old_sig["signature"],
                            new_signature=new_sig["signature"],
                        )
                    )

    def _check_new_required_params(
        self,
        report: CompatibilityReport,
        file_path: str,
        class_name: str,
        method_name: str,
        old_sig: dict,
        new_sig: dict,
    ) -> None:
        """检查新增必需参数"""
        old_params = {p["name"]: p for p in old_sig["parameters"]}
        new_params = {p["name"]: p for p in new_sig["parameters"]}

        for param_name, new_param in new_params.items():
            if param_name not in old_params:
                # 新参数，检查是否必需
                if new_param["default"] is None:
                    # 检查是否在参数列表末尾（位置参数会有兼容性问题）
                    param_names = [p["name"] for p in new_sig["parameters"]]
                    if param_names.index(param_name) < len(old_params):
                        report.add_breaking_change(
                            InterfaceChange(
                                file_path=file_path,
                                class_name=class_name,
                                method_name=method_name,
                                change_type=BreakingChangeType.REQUIRED_PARAMETER_ADDED,
                                severity="breaking",
                                description=f"Required parameter '{param_name}' was added in non-terminal position",
                                old_signature=old_sig["signature"],
                                new_signature=new_sig["signature"],
                            )
                        )


# =============================================================================
# Usage Examples
# =============================================================================


def check_api_compatibility(old_api: Any, new_api: Any) -> CompatibilityReport:
    """
    检查 API 兼容性

    Args:
        old_api: 旧版本 API 类
        new_api: 新版本 API 类

    Returns:
        兼容性报告
    """
    checker = CompatibilityChecker()
    return checker.check_class_compatibility(old_api, new_api)


def generate_compatibility_report(
    reports: list[CompatibilityReport],
) -> dict[str, Any]:
    """
    生成兼容性汇总报告

    Args:
        reports: 兼容性报告列表

    Returns:
        汇总报告
    """
    total_breaking = sum(len(r.breaking_changes) for r in reports)
    total_warnings = sum(len(r.warnings) for r in reports)
    compatible_count = sum(1 for r in reports if r.is_compatible)

    return {
        "total_checks": len(reports),
        "compatible": compatible_count,
        "incompatible": len(reports) - compatible_count,
        "total_breaking_changes": total_breaking,
        "total_warnings": total_warnings,
        "breaking_changes_summary": _summarize_changes(reports),
    }


def _summarize_changes(reports: list[CompatibilityReport]) -> dict[str, int]:
    """汇总变更类型"""
    summary: dict[str, int] = {}
    for report in reports:
        for change in report.breaking_changes:
            change_type = change.change_type
            summary[change_type] = summary.get(change_type, 0) + 1
    return summary
