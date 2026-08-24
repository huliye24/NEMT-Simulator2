"""
TraceCollector - 链路追踪系统

提供分布式追踪能力。
"""

import logging
import threading
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

__all__ = [
    "SpanStatus",
    "Span",
    "Trace",
    "TraceCollector",
]


class SpanStatus(Enum):
    """Span 状态"""

    OK = "ok"
    ERROR = "error"
    CANCELLED = "cancelled"


@dataclass
class Span:
    """追踪 Span"""

    span_id: str
    trace_id: str
    name: str
    start_time: float
    end_time: float = 0
    duration_ms: float = 0
    status: SpanStatus = SpanStatus.OK
    parent_span_id: str = ""
    service_name: str = ""
    operation_name: str = ""
    tags: dict[str, str] = field(default_factory=dict)
    logs: list[dict] = field(default_factory=list)
    children: list[str] = field(default_factory=list)  # 子 span IDs

    def finish(self, status: SpanStatus = SpanStatus.OK) -> None:
        """结束 Span"""
        self.end_time = time.time()
        self.duration_ms = (self.end_time - self.start_time) * 1000
        self.status = status

    def tag(self, key: str, value: str) -> "Span":
        """添加标签"""
        self.tags[key] = str(value)
        return self

    def log_event(self, message: str, **attrs) -> "Span":
        """记录事件"""
        self.logs.append(
            {
                "timestamp": time.time(),
                "message": message,
                "attrs": attrs,
            }
        )
        return self

    def to_dict(self) -> dict:
        return {
            "span_id": self.span_id,
            "trace_id": self.trace_id,
            "name": self.name,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration_ms": self.duration_ms,
            "status": self.status.value,
            "parent_span_id": self.parent_span_id,
            "service_name": self.service_name,
            "operation_name": self.operation_name,
            "tags": self.tags,
            "logs": self.logs,
            "children": self.children,
        }


@dataclass
class Trace:
    """追踪上下文"""

    trace_id: str
    start_time: float
    end_time: float = 0
    duration_ms: float = 0
    spans: list[Span] = field(default_factory=list)
    root_span_id: str = ""
    metadata: dict = field(default_factory=dict)

    def finish(self) -> None:
        """结束追踪"""
        self.end_time = time.time()
        self.duration_ms = (self.end_time - self.start_time) * 1000
        for span in self.spans:
            if span.end_time == 0:
                span.finish()

    def to_dict(self) -> dict:
        return {
            "trace_id": self.trace_id,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration_ms": self.duration_ms,
            "spans": [s.to_dict() for s in self.spans],
            "root_span_id": self.root_span_id,
            "metadata": self.metadata,
        }


class TraceCollector:
    """
    链路追踪收集器

    示例:
    ```python
    collector = TraceCollector()

    # 开始追踪
    trace = collector.start_trace("process_order")
    span = trace.start_span("validate_input")

    # ... 执行操作 ...

    span.finish()
    trace.finish()

    # 获取追踪
    trace_data = collector.get_trace(trace.trace_id)
    ```
    """

    def __init__(self, max_traces: int = 10000):
        self.max_traces = max_traces
        self._traces: dict[str, Trace] = {}
        self._spans: dict[str, Span] = {}
        self._lock = threading.RLock()
        self._logger = logging.getLogger("TraceCollector")

    def start_trace(
        self,
        name: str,
        service_name: str = "",
        metadata: dict = None,
    ) -> "TraceContext":
        """开始追踪"""
        trace_id = str(uuid.uuid4())
        root_span_id = str(uuid.uuid4())

        start_time = time.time()

        trace = Trace(
            trace_id=trace_id,
            start_time=start_time,
            root_span_id=root_span_id,
            metadata=metadata or {},
        )

        root_span = Span(
            span_id=root_span_id,
            trace_id=trace_id,
            name=name,
            start_time=start_time,
            service_name=service_name,
            operation_name=name,
        )

        with self._lock:
            self._traces[trace_id] = trace
            self._spans[span_id] = root_span
            trace.spans.append(root_span)

            if len(self._traces) > self.max_traces:
                self._cleanup_old_traces()

        return TraceContext(self, trace, root_span)

    def start_span(
        self,
        name: str,
        trace_id: str,
        parent_span_id: str = "",
        service_name: str = "",
    ) -> Span:
        """开始 Span"""
        span_id = str(uuid.uuid4())
        start_time = time.time()

        span = Span(
            span_id=span_id,
            trace_id=trace_id,
            name=name,
            start_time=start_time,
            parent_span_id=parent_span_id,
            service_name=service_name,
            operation_name=name,
        )

        with self._lock:
            self._spans[span_id] = span

            # 添加到父 span 的子列表
            if parent_span_id and parent_span_id in self._spans:
                self._spans[parent_span_id].children.append(span_id)

            # 添加到 trace
            if trace_id in self._traces:
                self._traces[trace_id].spans.append(span)

        return span

    def finish_span(self, span_id: str, status: SpanStatus = SpanStatus.OK) -> None:
        """结束 Span"""
        with self._lock:
            if span_id in self._spans:
                self._spans[span_id].finish(status)

    def finish_trace(self, trace_id: str) -> Trace | None:
        """结束追踪"""
        with self._lock:
            if trace_id in self._traces:
                trace = self._traces[trace_id]
                trace.finish()
                return trace
        return None

    def get_trace(self, trace_id: str) -> Trace | None:
        """获取追踪"""
        return self._traces.get(trace_id)

    def get_span(self, span_id: str) -> Span | None:
        """获取 Span"""
        return self._spans.get(span_id)

    def query_traces(
        self,
        start_time: float = 0,
        end_time: float = 0,
        service_name: str = "",
        limit: int = 100,
    ) -> list[Trace]:
        """查询追踪"""
        with self._lock:
            traces = list(self._traces.values())

        if start_time > 0:
            traces = [t for t in traces if t.start_time >= start_time]
        if end_time > 0:
            traces = [t for t in traces if t.start_time <= end_time]
        if service_name:
            traces = [t for t in traces if any(s.service_name == service_name for s in t.spans)]

        traces.sort(key=lambda t: t.start_time, reverse=True)
        return traces[:limit]

    def get_trace_tree(self, trace_id: str) -> dict | None:
        """获取追踪树"""
        trace = self.get_trace(trace_id)
        if not trace:
            return None

        # 构建树
        span_map = {s.span_id: s for s in trace.spans}

        def build_tree(span_id: str) -> dict:
            span = span_map.get(span_id)
            if not span:
                return {}

            return {
                "span_id": span.span_id,
                "name": span.name,
                "duration_ms": span.duration_ms,
                "service_name": span.service_name,
                "status": span.status.value,
                "children": [build_tree(child_id) for child_id in span.children if child_id in span_map],
            }

        return build_tree(trace.root_span_id)

    def get_stats(self) -> dict[str, Any]:
        """获取统计"""
        with self._lock:
            total_traces = len(self._traces)
            total_spans = len(self._spans)

            # 计算平均持续时间
            durations = [t.duration_ms for t in self._traces.values() if t.duration_ms > 0]
            avg_duration = sum(durations) / len(durations) if durations else 0

            return {
                "total_traces": total_traces,
                "total_spans": total_spans,
                "avg_duration_ms": avg_duration,
            }

    def _cleanup_old_traces(self) -> None:
        """清理旧追踪"""
        # 删除最老的追踪
        sorted_traces = sorted(self._traces.items(), key=lambda x: x[1].start_time)
        for trace_id, trace in sorted_traces[: len(self._traces) - self.max_traces]:
            del self._traces[trace_id]
            for span in trace.spans:
                if span.span_id in self._spans:
                    del self._spans[span.span_id]


class TraceContext:
    """追踪上下文"""

    def __init__(self, collector: TraceCollector, trace: Trace, root_span: Span):
        self._collector = collector
        self._trace = trace
        self._root_span = root_span
        self._current_span = root_span
        self._spans: list[Span] = [root_span]

    def start_span(self, name: str, service_name: str = "") -> Span:
        """开始子 Span"""
        span = self._collector.start_span(
            name=name,
            trace_id=self._trace.trace_id,
            parent_span_id=self._current_span.span_id,
            service_name=service_name,
        )
        self._current_span = span
        self._spans.append(span)
        return span

    def end_span(self, status: SpanStatus = SpanStatus.OK) -> None:
        """结束当前 Span"""
        self._collector.finish_span(self._current_span.span_id, status)
        if self._spans:
            self._spans.pop()
        if self._spans:
            self._current_span = self._spans[-1]

    def finish(self) -> Trace:
        """结束追踪"""
        for span in self._spans:
            if span.end_time == 0:
                self._collector.finish_span(span.span_id)
        return self._collector.finish_trace(self._trace.trace_id)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self._current_span.status = SpanStatus.ERROR
            self._current_span.log_event(str(exc_val))
        self.finish()


# 全局实例
_trace_collector: TraceCollector | None = None


def get_trace_collector() -> TraceCollector:
    """获取全局追踪收集器"""
    global _trace_collector
    if _trace_collector is None:
        _trace_collector = TraceCollector()
    return _trace_collector
