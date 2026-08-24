"""
Coverage Analyzer - 覆盖率分析器

分析业务需求的代码实现覆盖率。

版本: v1.0.0
更新: 2026-04-27
"""

from __future__ import annotations

import ast
import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class CoverageReport:
    """覆盖率报告"""

    requirement_id: str
    requirement_title: str

    # 代码覆盖
    covered_files: list[str] = field(default_factory=list)
    total_files: int = 0
    code_coverage_percent: float = 0.0

    # 功能覆盖
    covered_functions: list[str] = field(default_factory=list)
    total_functions: int = 0
    function_coverage_percent: float = 0.0

    # 测试覆盖
    covered_tests: list[str] = field(default_factory=list)
    total_tests: int = 0
    test_coverage_percent: float = 0.0

    # 元数据
    analyzed_at: datetime = field(default_factory=datetime.now)
    gaps: list[str] = field(default_factory=list)


class CoverageAnalyzer:
    """覆盖率分析器"""

    def __init__(self, root_dir: str):
        self.root_dir = root_dir
        self._file_cache: dict[str, list[str]] = {}  # file -> functions

    def analyze_requirement(
        self,
        requirement_id: str,
        requirement_title: str,
        related_files: list[str],
    ) -> CoverageReport:
        """
        分析需求的覆盖情况

        Args:
            requirement_id: 需求 ID
            requirement_title: 需求标题
            related_files: 关联的文件列表

        Returns:
            覆盖率报告
        """
        report = CoverageReport(
            requirement_id=requirement_id,
            requirement_title=requirement_title,
        )

        # 分析文件覆盖
        all_functions = []
        covered_files = []

        for file_path in related_files:
            full_path = os.path.join(self.root_dir, file_path)
            if os.path.exists(full_path):
                covered_files.append(file_path)
                functions = self._extract_functions(full_path)
                all_functions.extend(functions)
                report.covered_functions.extend(functions)

        report.covered_files = covered_files
        report.total_files = len(related_files)
        report.code_coverage_percent = len(covered_files) / len(related_files) if related_files else 0

        # 分析函数覆盖
        report.total_functions = len(all_functions)
        report.function_coverage_percent = (
            len(report.covered_functions) / report.total_functions if report.total_functions else 0
        )

        # 识别缺口
        report.gaps = self._identify_gaps(requirement_title, report.covered_functions)

        return report

    def _extract_functions(self, file_path: str) -> list[str]:
        """从文件中提取函数"""
        if file_path in self._file_cache:
            return self._file_cache[file_path]

        try:
            with open(file_path, encoding="utf-8") as f:
                tree = ast.parse(f.read())

            functions = []
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    functions.append(f"{os.path.basename(file_path)}:{node.name}")

            self._file_cache[file_path] = functions
            return functions

        except Exception:
            return []

    def _identify_gaps(
        self,
        requirement_title: str,
        covered_functions: list[str],
    ) -> list[str]:
        """识别覆盖缺口"""
        gaps = []

        # 检查是否缺少关键方法
        title_lower = requirement_title.lower()

        if "market" in title_lower:
            required = ["subscribe", "get_price", "get_klines"]
            for method in required:
                if not any(method in f for f in covered_functions):
                    gaps.append(f"Missing required method: {method}")

        elif "signal" in title_lower:
            required = ["generate_signal", "calculate_indicators"]
            for method in required:
                if not any(method in f for f in covered_functions):
                    gaps.append(f"Missing required method: {method}")

        elif "risk" in title_lower:
            required = ["check_signal", "get_risk_metrics"]
            for method in required:
                if not any(method in f for f in covered_functions):
                    gaps.append(f"Missing required method: {method}")

        return gaps

    def generate_coverage_summary(
        self,
        reports: list[CoverageReport],
    ) -> dict[str, Any]:
        """
        生成覆盖率汇总

        Args:
            reports: 覆盖率报告列表

        Returns:
            汇总数据
        """
        total_requirements = len(reports)
        covered_requirements = sum(1 for r in reports if r.code_coverage_percent > 0)
        fully_covered = sum(1 for r in reports if r.code_coverage_percent == 1.0)

        total_files = sum(r.total_files for r in reports)
        covered_files = sum(len(r.covered_files) for r in reports)

        total_functions = sum(r.total_functions for r in reports)
        covered_functions = sum(len(r.covered_functions) for r in reports)

        all_gaps = []
        for r in reports:
            all_gaps.extend(r.gaps)

        return {
            "total_requirements": total_requirements,
            "covered_requirements": covered_requirements,
            "fully_covered_requirements": fully_covered,
            "requirement_coverage": covered_requirements / total_requirements if total_requirements else 0,
            "total_files": total_files,
            "covered_files": covered_files,
            "file_coverage": covered_files / total_files if total_files else 0,
            "total_functions": total_functions,
            "covered_functions": covered_functions,
            "function_coverage": covered_functions / total_functions if total_functions else 0,
            "total_gaps": len(all_gaps),
            "unique_gaps": list(set(all_gaps)),
            "gap_summary": {g: sum(1 for r in reports if g in r.gaps) for g in set(all_gaps)},
        }
