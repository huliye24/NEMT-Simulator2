"""
Dashboard - 运维仪表盘

提供运维监控、数据可视化能力。
"""

import json
import logging
import time
from dataclasses import dataclass, field
from typing import Any

__all__ = [
    "Widget",
    "WidgetType",
    "Dashboard",
    "DashboardRenderer",
]


class WidgetType(Enum):
    """组件类型"""

    COUNTER = "counter"  # 计数器
    LINE_CHART = "line_chart"  # 折线图
    BAR_CHART = "bar_chart"  # 柱状图
    GAUGE = "gauge"  # 仪表盘
    TABLE = "table"  # 表格
    LOG_VIEWER = "log_viewer"  # 日志查看器
    ALERT_LIST = "alert_list"  # 告警列表
    STATUS = "status"  # 状态指示




@dataclass
class Widget:
    """仪表盘组件"""

    widget_id: str
    name: str
    widget_type: WidgetType
    data_source: str  # 数据源名称
    config: dict = field(default_factory=dict)
    position: dict = field(default_factory=lambda: {"x": 0, "y": 0, "w": 1, "h": 1})
    refresh_interval: int = 30  # 秒


class Dashboard:
    """
    运维仪表盘

    示例:
    ```python
    dashboard = Dashboard()

    # 添加组件
    dashboard.add_widget(Widget(
        widget_id="cpu_usage",
        name="CPU 使用率",
        widget_type=WidgetType.GAUGE,
        data_source="metrics",
        config={"metric": "system.cpu.usage"},
    ))

    # 渲染
    html = dashboard.render()
    ```
    """

    def __init__(self, name: str = "NEMT Dashboard"):
        self.name = name
        self._widgets: dict[str, Widget] = {}
        self._data_sources: dict[str, Any] = {}
        self._logger = logging.getLogger("Dashboard")

    def add_widget(self, widget: Widget) -> None:
        """添加组件"""
        self._widgets[widget.widget_id] = widget

    def remove_widget(self, widget_id: str) -> bool:
        """移除组件"""
        if widget_id in self._widgets:
            del self._widgets[widget_id]
            return True
        return False

    def get_widget(self, widget_id: str) -> Widget | None:
        """获取组件"""
        return self._widgets.get(widget_id)

    def register_data_source(self, name: str, source: Any) -> None:
        """注册数据源"""
        self._data_sources[name] = source

    def get_data(self, widget: Widget) -> Any:
        """获取组件数据"""
        source = self._data_sources.get(widget.data_source)
        if not source:
            return None

        config = widget.config
        if widget.widget_type == WidgetType.COUNTER:
            return self._get_counter_data(source, config)
        elif widget.widget_type == WidgetType.LINE_CHART:
            return self._get_line_chart_data(source, config)
        elif widget.widget_type == WidgetType.GAUGE:
            return self._get_gauge_data(source, config)
        elif widget.widget_type == WidgetType.TABLE:
            return self._get_table_data(source, config)
        elif widget.widget_type == WidgetType.LOG_VIEWER:
            return self._get_log_data(source, config)
        elif widget.widget_type == WidgetType.ALERT_LIST:
            return self._get_alert_data(source, config)

        return None

    def _get_counter_data(self, source: Any, config: dict) -> dict:
        """计数器数据"""
        metric = config.get("metric", "")
        return {"value": 0, "label": config.get("label", metric)}

    def _get_line_chart_data(self, source: Any, config: dict) -> dict:
        """折线图数据"""
        return {
            "labels": ["10:00", "11:00", "12:00", "13:00", "14:00"],
            "datasets": [
                {
                    "label": config.get("metric", "Value"),
                    "data": [65, 59, 80, 81, 56],
                }
            ],
        }

    def _get_gauge_data(self, source: Any, config: dict) -> dict:
        """仪表盘数据"""
        return {"value": 65, "min": 0, "max": 100, "label": config.get("label", "")}

    def _get_table_data(self, source: Any, config: dict) -> dict:
        """表格数据"""
        return {
            "columns": ["名称", "状态", "更新时间"],
            "rows": [
                ["Capsule-1", "Running", "10:30:00"],
                ["Capsule-2", "Running", "10:29:55"],
            ],
        }

    def _get_log_data(self, source: Any, config: dict) -> dict:
        """日志数据"""
        return {
            "logs": [
                {"timestamp": time.time(), "level": "INFO", "message": "System started"},
            ],
            "total": 1,
        }

    def _get_alert_data(self, source: Any, config: dict) -> dict:
        """告警数据"""
        return {
            "alerts": [
                {"name": "High CPU", "severity": "warning", "time": "10:25:00"},
            ],
            "total": 1,
        }

    def render(self) -> dict:
        """渲染仪表盘"""
        widgets = []
        for widget in self._widgets.values():
            widgets.append(
                {
                    "widget_id": widget.widget_id,
                    "name": widget.name,
                    "type": widget.widget_type.value,
                    "position": widget.position,
                    "refresh_interval": widget.refresh_interval,
                    "data": self.get_data(widget),
                }
            )

        return {
            "name": self.name,
            "widgets": widgets,
            "generated_at": time.time(),
        }

    def render_html(self) -> str:
        """渲染 HTML"""
        data = self.render()

        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>{data['name']}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
        .dashboard {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 20px; }}
        .widget {{ background: white; border-radius: 8px; padding: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .widget h3 {{ margin-top: 0; color: #333; }}
        .counter {{ font-size: 48px; font-weight: bold; color: #2196F3; }}
        .gauge {{ width: 100%; height: 200px; display: flex; align-items: center; justify-content: center; }}
        .table {{ width: 100%; border-collapse: collapse; }}
        .table th, .table td {{ padding: 8px; text-align: left; border-bottom: 1px solid #ddd; }}
        .logs {{ max-height: 300px; overflow-y: auto; font-family: monospace; font-size: 12px; }}
        .log-entry {{ padding: 4px; border-bottom: 1px solid #eee; }}
        .alert {{ padding: 10px; margin: 5px 0; border-radius: 4px; }}
        .alert.warning {{ background: #fff3cd; }}
        .alert.error {{ background: #f8d7da; }}
    </style>
</head>
<body>
    <h1>{data['name']}</h1>
    <div class="dashboard">
"""

        for w in data["widgets"]:
            html += '<div class="widget">'
            html += f'<h3>{w["name"]}</h3>'

            if w["type"] == "counter":
                value = w["data"].get("value", 0) if w["data"] else 0
                html += f'<div class="counter">{value}</div>'

            elif w["type"] == "gauge":
                value = w["data"].get("value", 0) if w["data"] else 0
                html += f'<div class="gauge"><div class="counter">{value}%</div></div>'

            elif w["type"] == "table" and w["data"]:
                html += '<table class="table"><thead><tr>'
                for col in w["data"].get("columns", []):
                    html += f"<th>{col}</th>"
                html += "</tr></thead><tbody>"
                for row in w["data"].get("rows", []):
                    html += "<tr>"
                    for cell in row:
                        html += f"<td>{cell}</td>"
                    html += "</tr>"
                html += "</tbody></table>"

            elif w["type"] == "log_viewer" and w["data"]:
                html += '<div class="logs">'
                for log in w["data"].get("logs", []):
                    html += f'<div class="log-entry">[{log["level"]}] {log["message"]}</div>'
                html += "</div>"

            elif w["type"] == "alert_list" and w["data"]:
                for alert in w["data"].get("alerts", []):
                    html += f'<div class="alert {alert["severity"]}">{alert["name"]}</div>'

            html += "</div>"

        html += """
    </div>
    <script>
        // 自动刷新
        setTimeout(() => location.reload(), 60000);
    </script>
</body>
</html>
"""
        return html


class DashboardRenderer:
    """仪表盘渲染器"""

    @staticmethod
    def render_json(dashboard: Dashboard) -> str:
        """渲染为 JSON"""
        return json.dumps(dashboard.render(), indent=2)

    @staticmethod
    def render_html(dashboard: Dashboard) -> str:
        """渲染为 HTML"""
        return dashboard.render_html()
