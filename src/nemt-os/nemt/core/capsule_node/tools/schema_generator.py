"""
Schema 生成器工具

自动从 CapsuleNode 类生成 Schema YAML 文件
"""

from typing import Any

import yaml


class SchemaGenerator:
    """
    Schema 生成器

    从 CapsuleNode 类自动生成 Schema YAML 文件。

    使用方法:

    ```python
    from capsules import MarketNode

    generator = SchemaGenerator()
    schema = generator.generate_from_node(MarketNode)

    # 保存为 YAML
    generator.save_schema(schema, "market_schema.yaml")

    # 或者直接打印
    print(generator.to_yaml(schema))
    ```
    """

    def __init__(self):
        self._type_map = {
            "str": "string",
            "int": "integer",
            "float": "number",
            "bool": "boolean",
            "list": "array",
            "dict": "object",
        }

    def generate_from_node(self, node_class: type) -> dict[str, Any]:
        """
        从节点类生成 Schema

        Args:
            node_class: CapsuleNode 子类

        Returns:
            Schema 字典
        """
        schema = {
            "name": getattr(node_class, "NODE_ID", node_class.__name__),
            "version": getattr(node_class, "NODE_VERSION", "1.0.0"),
            "description": self._get_docstring(node_class),
            "inputs": [],
            "outputs": [],
            "constraints": [],
        }

        # 收集输入端口
        for port in getattr(node_class, "INPUT_PORTS", []):
            schema["inputs"].append(self._port_to_dict(port))

        # 收集输出端口
        for port in getattr(node_class, "OUTPUT_PORTS", []):
            schema["outputs"].append(self._port_to_dict(port))

        # 收集约束
        for constraint in getattr(node_class, "CONSTRAINTS", []):
            schema["constraints"].append(self._constraint_to_dict(constraint))

        return schema

    def _get_docstring(self, cls: type) -> str:
        """获取类的文档字符串"""
        doc = cls.__doc__
        if doc:
            return doc.strip().split("\n")[0]
        return ""

    def _port_to_dict(self, port) -> dict[str, Any]:
        """将 PortSchema 转换为字典"""
        result = {
            "name": port.name,
            "type": port.data_type,
            "required": port.required,
            "description": getattr(port, "description", ""),
        }

        if hasattr(port, "properties") and port.properties:
            result["properties"] = port.properties

        if hasattr(port, "required_fields") and port.required_fields:
            result["required_fields"] = port.required_fields

        if hasattr(port, "enum_values") and port.enum_values:
            result["enum"] = port.enum_values

        if hasattr(port, "constraints") and port.constraints:
            result["constraints"] = port.constraints

        return result

    def _constraint_to_dict(self, constraint) -> dict[str, Any]:
        """将 ConstraintSchema 转换为字典"""
        result = {
            "name": constraint.name,
            "type": constraint.constraint_type,
            "value": constraint.value,
            "description": getattr(constraint, "description", ""),
        }

        if hasattr(constraint, "min_value") and constraint.min_value is not None:
            result["min"] = constraint.min_value

        if hasattr(constraint, "max_value") and constraint.max_value is not None:
            result["max"] = constraint.max_value

        return result

    def to_yaml(self, schema: dict) -> str:
        """转换为 YAML 格式"""
        return yaml.dump(schema, allow_unicode=True, sort_keys=False, default_flow_style=False)

    def save_schema(self, schema: dict, filepath: str) -> None:
        """保存 Schema 到文件"""
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(self.to_yaml(schema))

    def generate_all(self, node_classes: list[type], output_dir: str = "schemas") -> dict[str, dict]:
        """为所有节点类生成 Schema"""
        results = {}

        for node_class in node_classes:
            name = getattr(node_class, "NODE_ID", node_class.__name__)
            schema = self.generate_from_node(node_class)
            results[name] = schema

            # 保存文件
            filepath = f"{output_dir}/{name}.yaml"
            self.save_schema(schema, filepath)

        return results


def generate_node_schemas():
    """为所有节点生成 Schema 文件"""
    # 导入节点类
    import os
    import sys

    sys.path.insert(0, os.path.dirname(__file__))

    from capsules import BrainNode, ExecutionNode, MarketNode, RiskNode, SignalNode

    generator = SchemaGenerator()
    nodes = [MarketNode, SignalNode, RiskNode, BrainNode, ExecutionNode]

    schemas = generator.generate_all(nodes, output_dir="schemas")

    print("Generated schemas:")
    for name, schema in schemas.items():
        print(f"  - {name}: {len(schema['inputs'])} inputs, {len(schema['outputs'])} outputs")

    return schemas


if __name__ == "__main__":
    generate_node_schemas()
