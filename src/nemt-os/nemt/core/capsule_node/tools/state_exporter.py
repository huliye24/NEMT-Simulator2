"""
状态导出工具

导出 CapsuleNode 的状态为各种格式 (JSON, YAML, Markdown)
"""

import json
from datetime import datetime
from typing import Any

import yaml


class StateExporter:
    """
    状态导出器

    将 CapsuleNode 的状态导出为各种格式。

    使用方法:

    ```python
    from capsules import MarketNode
    from tools.state_exporter import StateExporter

    node = MarketNode()
    node.init()

    exporter = StateExporter()

    # 导出为 JSON
    json_str = exporter.to_json(node)

    # 导出为 YAML
    yaml_str = exporter.to_yaml(node)

    # 导出为 Markdown
    md_str = exporter.to_markdown(node)

    # 导出到文件
    exporter.save(node, "market_state.json")
    ```
    """

    def __init__(self, indent: int = 2):
        self.indent = indent

    def to_dict(self, node) -> dict[str, Any]:
        """
        导出为字典

        Args:
            node: CapsuleNode 实例

        Returns:
            状态字典
        """
        state = {
            "node": {
                "id": node.node_id,
                "name": getattr(node, "NODE_NAME", ""),
                "version": getattr(node, "NODE_VERSION", ""),
            },
            "state": {
                "capsule_state": (
                    node.capsule_state.value if hasattr(node.capsule_state, "value") else str(node.capsule_state)
                ),
                "phase": node.state.phase.value if hasattr(node.state, "phase") else "",
            },
            "schemas": {
                "inputs": self._ports_to_list(node.INPUT_PORTS),
                "outputs": self._ports_to_list(node.OUTPUT_PORTS),
                "constraints": self._constraints_to_list(node.CONSTRAINTS),
            },
            "metrics": node.metrics if hasattr(node, "metrics") else {},
            "exported_at": datetime.now().isoformat(),
        }

        return state

    def _ports_to_list(self, ports: list) -> list[dict]:
        """转换端口列表"""
        result = []
        for port in ports:
            port_dict = {
                "name": port.name,
                "type": port.data_type,
                "required": port.required,
                "description": getattr(port, "description", ""),
            }

            if hasattr(port, "required_fields") and port.required_fields:
                port_dict["required_fields"] = port.required_fields

            if hasattr(port, "enum_values") and port.enum_values:
                port_dict["enum"] = port.enum_values

            result.append(port_dict)

        return result

    def _constraints_to_list(self, constraints: list) -> list[dict]:
        """转换约束列表"""
        result = []
        for c in constraints:
            c_dict = {
                "name": c.name,
                "type": c.constraint_type,
                "value": c.value,
                "description": getattr(c, "description", ""),
            }

            if hasattr(c, "min_value") and c.min_value is not None:
                c_dict["min"] = c.min_value

            if hasattr(c, "max_value") and c.max_value is not None:
                c_dict["max"] = c.max_value

            result.append(c_dict)

        return result

    def to_json(self, node, pretty: bool = True) -> str:
        """
        导出为 JSON 字符串

        Args:
            node: CapsuleNode 实例
            pretty: 是否格式化输出

        Returns:
            JSON 字符串
        """
        state = self.to_dict(node)
        if pretty:
            return json.dumps(state, indent=self.indent, ensure_ascii=False, default=str)
        return json.dumps(state, ensure_ascii=False, default=str)

    def to_yaml(self, node) -> str:
        """
        导出为 YAML 字符串

        Args:
            node: CapsuleNode 实例

        Returns:
            YAML 字符串
        """
        state = self.to_dict(node)
        return yaml.dump(state, allow_unicode=True, sort_keys=False, default_flow_style=False)

    def to_markdown(self, node, include_metrics: bool = True) -> str:
        """
        导出为 Markdown 表格

        Args:
            node: CapsuleNode 实例
            include_metrics: 是否包含指标

        Returns:
            Markdown 字符串
        """
        state = self.to_dict(node)

        lines = []

        # 标题
        lines.append(f"# {state['node']['name']}")
        lines.append("")
        lines.append(f"**ID**: `{state['node']['id']}` | **Version**: `{state['node']['version']}`")
        lines.append("")

        # 状态
        lines.append("## Status")
        lines.append("")
        lines.append(f"- **Capsule State**: `{state['state']['capsule_state']}`")
        lines.append(f"- **Phase**: `{state['state']['phase']}`")
        lines.append(f"- **Exported**: {state['exported_at']}")
        lines.append("")

        # 输入端口
        lines.append("## Input Ports")
        lines.append("")
        if state["schemas"]["inputs"]:
            lines.append("| Name | Type | Required | Description |")
            lines.append("|------|------|----------|-------------|")
            for port in state["schemas"]["inputs"]:
                req = "Yes" if port.get("required") else "No"
                fields = ", ".join(port.get("required_fields", []))
                desc = port.get("description", "")[:50]
                lines.append(f"| `{port['name']}` | {port['type']} | {req} | {desc} |")
        else:
            lines.append("*No input ports defined*")
        lines.append("")

        # 输出端口
        lines.append("## Output Ports")
        lines.append("")
        if state["schemas"]["outputs"]:
            lines.append("| Name | Type | Required | Description |")
            lines.append("|------|------|----------|-------------|")
            for port in state["schemas"]["outputs"]:
                req = "Yes" if port.get("required") else "No"
                enum = f"enum: {port.get('enum', [])}" if port.get("enum") else ""
                desc = port.get("description", "")[:30]
                lines.append(f"| `{port['name']}` | {port['type']} | {req} | {desc} {enum} |")
        else:
            lines.append("*No output ports defined*")
        lines.append("")

        # 约束
        lines.append("## Constraints")
        lines.append("")
        if state["schemas"]["constraints"]:
            lines.append("| Name | Type | Value | Description |")
            lines.append("|------|------|-------|-------------|")
            for c in state["schemas"]["constraints"]:
                lines.append(f"| `{c['name']}` | {c['type']} | {c['value']} | {c.get('description', '')} |")
        else:
            lines.append("*No constraints defined*")
        lines.append("")

        # 指标
        if include_metrics and state.get("metrics"):
            lines.append("## Metrics")
            lines.append("")
            lines.append("| Metric | Value |")
            lines.append("|--------|-------|")
            for k, v in state["metrics"].items():
                lines.append(f"| {k} | {v} |")
            lines.append("")

        return "\n".join(lines)

    def save(self, node, filepath: str, format: str | None = None) -> None:
        """
        保存到文件

        Args:
            node: CapsuleNode 实例
            filepath: 文件路径
            format: 格式 ("json", "yaml", "md")，如果为 None 则根据扩展名判断
        """
        if format is None:
            ext = filepath.split(".")[-1].lower()
            format = ext if ext in ["json", "yaml", "yml", "md", "markdown"] else "json"

        if format == "json":
            content = self.to_json(node)
        elif format in ["yaml", "yml"]:
            content = self.to_yaml(node)
        elif format in ["md", "markdown"]:
            content = self.to_markdown(node)
        else:
            raise ValueError(f"Unsupported format: {format}")

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)


def export_all_nodes(nodes: list, output_dir: str = "exports") -> None:
    """
    导出所有节点状态

    Args:
        nodes: CapsuleNode 实例列表
        output_dir: 输出目录
    """
    import os

    os.makedirs(output_dir, exist_ok=True)

    exporter = StateExporter()

    for node in nodes:
        name = node.node_id
        filepath = f"{output_dir}/{name}.md"
        exporter.save(node, filepath, format="md")
        print(f"Exported: {filepath}")


if __name__ == "__main__":
    # 示例用法
    import os
    import sys

    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

    from capsules import BrainNode, ExecutionNode, MarketNode, RiskNode, SignalNode

    # 创建节点
    nodes = [
        MarketNode(),
        SignalNode(),
        RiskNode(),
        BrainNode(),
        ExecutionNode(),
    ]

    # 初始化
    for node in nodes:
        node.init()

    # 导出
    exporter = StateExporter()

    for node in nodes:
        print(f"\n{'='*60}")
        print(f"Node: {node.node_id}")
        print(f"{'='*60}")

        # JSON
        json_str = exporter.to_json(node)
        print(f"\nJSON (first 500 chars):\n{json_str[:500]}...")

        # Markdown
        md_str = exporter.to_markdown(node)
        print(f"\nMarkdown:\n{md_str[:500]}...")
