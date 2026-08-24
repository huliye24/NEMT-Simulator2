"""
Log Analyzer - 日志分析器

提供日志分析和统计功能:
- 日志级别统计
- 错误聚合
- 性能日志分析
- 异常模式检测

参考: Notion 暗物质框架 第一章「日志即宇宙背景辐射」
"""

import json
import re
import threading
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

# ============================================================================
# 日志统计
# ============================================================================


@dataclass
class LogStats:
    """日志统计"""

    total_count: int = 0
    by_level: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    by_module: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    by_capsule: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    error_count: int = 0
    warning_count: int = 0
    first_timestamp: datetime | None = None
    last_timestamp: datetime | None = None

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "total_count": self.total_count,
            "by_level": dict(self.by_level),
            "by_module": dict(self.by_module),
            "by_capsule": dict(self.by_capsule),
            "error_count": self.error_count,
            "warning_count": self.warning_count,
            "first_timestamp": self.first_timestamp.isoformat() if self.first_timestamp else None,
            "last_timestamp": self.last_timestamp.isoformat() if self.last_timestamp else None,
        }


@dataclass
class ErrorSummary:
    """错误汇总"""

    error_code: str
    message: str
    count: int = 0
    first_occurrence: datetime | None = None
    last_occurrence: datetime | None = None
    samples: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "error_code": self.error_code,
            "message": self.message,
            "count": self.count,
            "first_occurrence": self.first_occurrence.isoformat() if self.first_occurrence else None,
            "last_occurrence": self.last_occurrence.isoformat() if self.last_occurrence else None,
            "samples": self.samples[:5],  # 最多 5 个样本
        }


# ============================================================================
# 日志分析器
# ============================================================================


class LogAnalyzer:
    """
    日志分析器

    提供日志分析和统计功能。

    Usage:
        analyzer = LogAnalyzer()

        # 分析日志文件
        stats = analyzer.analyze_file("app.log")

        # 分析内存中的日志
        for line in log_lines:
            analyzer.process_line(line)

        stats = analyzer.get_stats()
        errors = analyzer.get_error_summary()
    """

    def __init__(self):
        """初始化分析器"""
        self._stats = LogStats()
        self._error_map: dict[str, ErrorSummary] = {}
        self._lock = threading.Lock()

    def reset(self) -> None:
        """重置分析器"""
        with self._lock:
            self._stats = LogStats()
            self._error_map.clear()

    def process_line(self, line: str) -> dict[str, Any] | None:
        """
        处理单行日志

        Args:
            line: 日志行

        Returns:
            解析后的日志字典，或 None（解析失败）
        """
        try:
            # 尝试 JSON 解析
            log_entry = json.loads(line)
            self._process_entry(log_entry)
            return log_entry
        except json.JSONDecodeError:
            # 尝试普通文本解析
            return self._process_text_line(line)

        return None

    def _process_entry(self, entry: dict[str, Any]) -> None:
        """处理解析后的日志条目"""
        with self._lock:
            self._stats.total_count += 1

            # 级别统计
            level = entry.get("level", "UNKNOWN")
            self._stats.by_level[level] += 1

            # 模块统计
            module = entry.get("module", "unknown")
            self._stats.by_module[module] += 1

            # 胶囊统计
            capsule_id = entry.get("capsule_id")
            if capsule_id:
                self._stats.by_capsule[capsule_id] += 1

            # 错误/警告计数
            if level in ("ERROR", "CRITICAL"):
                self._stats.error_count += 1
                self._update_error(entry)
            elif level == "WARNING":
                self._stats.warning_count += 1

            # 时间戳
            timestamp_str = entry.get("timestamp")
            if timestamp_str:
                try:
                    timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
                    if self._stats.first_timestamp is None or timestamp < self._stats.first_timestamp:
                        self._stats.first_timestamp = timestamp
                    if self._stats.last_timestamp is None or timestamp > self._stats.last_timestamp:
                        self._stats.last_timestamp = timestamp
                except (ValueError, TypeError):
                    pass

    def _process_text_line(self, line: str) -> dict[str, Any] | None:
        """处理普通文本日志行"""
        # 简单的文本解析（适配标准日志格式）
        pattern = r"(\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}[.\d]*).*?\[?(\w+)\]?\s+(.*)"
        match = re.match(pattern, line)
        if not match:
            return None

        timestamp_str, level, message = match.groups()
        try:
            timestamp = datetime.fromisoformat(timestamp_str)
        except ValueError:
            timestamp = datetime.now()

        entry = {
            "timestamp": timestamp.isoformat(),
            "level": level.upper(),
            "message": message.strip(),
        }

        self._process_entry(entry)
        return entry

    def _update_error(self, entry: dict[str, Any]) -> None:
        """更新错误统计"""
        error_code = entry.get("error_code", "UNKNOWN")
        message = entry.get("message", "")

        # 创建错误键
        error_key = f"{error_code}:{message[:50]}"

        if error_key not in self._error_map:
            self._error_map[error_key] = ErrorSummary(
                error_code=error_code,
                message=message[:100],
            )

        error_summary = self._error_map[error_key]
        error_summary.count += 1

        # 时间戳
        timestamp_str = entry.get("timestamp")
        if timestamp_str:
            try:
                timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
                if error_summary.first_occurrence is None:
                    error_summary.first_occurrence = timestamp
                error_summary.last_occurrence = timestamp
            except (ValueError, TypeError):
                pass

        # 保存样本
        if len(error_summary.samples) < 5:
            sample = {
                "timestamp": timestamp_str,
                "message": message,
                "context": {k: v for k, v in entry.items() if k in ("capsule_id", "symbol", "bar_index")},
            }
            error_summary.samples.append(json.dumps(sample))

    def analyze_file(self, file_path: str, max_lines: int | None = None) -> LogStats:
        """
        分析日志文件

        Args:
            file_path: 日志文件路径
            max_lines: 最大处理行数（可选）

        Returns:
            日志统计
        """
        self.reset()

        with open(file_path, encoding="utf-8") as f:
            lines_read = 0
            for line in f:
                if line.strip():
                    self.process_line(line)
                lines_read += 1
                if max_lines and lines_read >= max_lines:
                    break

        return self.get_stats()

    def get_stats(self) -> LogStats:
        """获取统计结果"""
        with self._lock:
            return self._stats

    def get_error_summary(self, min_count: int = 1) -> list[ErrorSummary]:
        """
        获取错误汇总

        Args:
            min_count: 最小错误次数

        Returns:
            错误汇总列表（按次数降序）
        """
        with self._lock:
            errors = [e for e in self._error_map.values() if e.count >= min_count]
            return sorted(errors, key=lambda e: e.count, reverse=True)

    def get_top_errors(self, n: int = 10) -> list[ErrorSummary]:
        """
        获取 Top N 错误

        Args:
            n: 返回数量

        Returns:
            错误汇总列表
        """
        return self.get_error_summary()[:n]

    def generate_report(self) -> str:
        """
        生成分析报告

        Returns:
            报告字符串
        """
        stats = self.get_stats()
        errors = self.get_top_errors(10)

        lines = [
            "=" * 60,
            "日志分析报告",
            "=" * 60,
            "",
            f"总日志数: {stats.total_count}",
            f"错误数: {stats.error_count}",
            f"警告数: {stats.warning_count}",
            "",
            "按级别分布:",
        ]

        for level, count in sorted(stats.by_level.items()):
            pct = (count / stats.total_count * 100) if stats.total_count > 0 else 0
            lines.append(f"  {level}: {count} ({pct:.1f}%)")

        lines.append("")
        lines.append("Top 10 错误:")

        if errors:
            for i, error in enumerate(errors, 1):
                lines.append(f"  {i}. [{error.error_code}] {error.message[:50]} (x{error.count})")
        else:
            lines.append("  无错误记录")

        lines.append("")
        lines.append("=" * 60)

        return "\n".join(lines)


# ============================================================================
# 便捷函数
# ============================================================================


def quick_analyze(file_path: str, max_lines: int | None = None) -> LogStats:
    """
    快速分析日志文件

    Args:
        file_path: 日志文件路径
        max_lines: 最大处理行数

    Returns:
        日志统计
    """
    analyzer = LogAnalyzer()
    return analyzer.analyze_file(file_path, max_lines)


def quick_report(file_path: str) -> str:
    """
    快速生成分析报告

    Args:
        file_path: 日志文件路径

    Returns:
        报告字符串
    """
    analyzer = LogAnalyzer()
    analyzer.analyze_file(file_path)
    return analyzer.generate_report()
