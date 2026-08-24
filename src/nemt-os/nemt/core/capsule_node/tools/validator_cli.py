"""
Schema 验证 CLI 工具

命令行工具，用于验证 CapsuleNode 的输入/输出是否符合 Schema
"""

import argparse
import json
import sys
from typing import Any


class ValidationError:
    """验证错误"""

    def __init__(self, field: str, message: str, value: Any = None):
        self.field = field
        self.message = message
        self.value = value

    def __str__(self) -> str:
        if self.value is not None:
            return f"  [{self.field}] {self.message} (got: {self.value})"
        return f"  [{self.field}] {self.message}"


class ValidationResult:
    """验证结果"""

    def __init__(self):
        self.errors: list[ValidationError] = []
        self.warnings: list[str] = []

    @property
    def valid(self) -> bool:
        return len(self.errors) == 0

    def add_error(self, field: str, message: str, value: Any = None):
        self.errors.append(ValidationError(field, message, value))

    def add_warning(self, message: str):
        self.warnings.append(message)

    def __str__(self) -> str:
        lines = []
        if self.errors:
            lines.append("ERRORS:")
            for e in self.errors:
                lines.append(str(e))
        if self.warnings:
            lines.append("WARNINGS:")
            for w in self.warnings:
                lines.append(f"  - {w}")
        if self.valid:
            lines.append("VALID")
        return "\n".join(lines)


class SchemaValidator:
    """
    Schema 验证器

    验证数据是否符合 Schema 定义。
    """

    def __init__(self, schema: dict):
        self.schema = schema

    def validate(self, data: dict, schema_type: str = "inputs") -> ValidationResult:
        """
        验证数据

        Args:
            data: 要验证的数据
            schema_type: "inputs" 或 "outputs"
        """
        result = ValidationResult()

        schema_fields = self.schema.get(schema_type, [])

        for field_schema in schema_fields:
            field_name = field_schema["name"]
            required = field_schema.get("required", False)

            # 检查必需字段
            if required and field_name not in data:
                result.add_error(field_name, "Required field missing")
                continue

            if field_name not in data:
                continue

            value = data[field_name]

            # 检查类型
            expected_type = field_schema.get("type", "any")
            if expected_type != "any":
                self._validate_type(field_name, value, expected_type, result)

            # 检查必需子字段
            required_fields = field_schema.get("required_fields", [])
            if isinstance(value, dict):
                for subfield in required_fields:
                    if subfield not in value:
                        result.add_error(f"{field_name}.{subfield}", "Required subfield missing")

            # 检查枚举
            enum_values = field_schema.get("enum")
            if enum_values and value not in enum_values:
                result.add_error(field_name, f"Value must be one of {enum_values}", value)

            # 检查约束
            constraints = field_schema.get("constraints", {})
            if isinstance(value, (int, float)):
                if "min" in constraints and value < constraints["min"]:
                    result.add_error(field_name, f"Value below minimum {constraints['min']}", value)
                if "max" in constraints and value > constraints["max"]:
                    result.add_error(field_name, f"Value above maximum {constraints['max']}", value)

        return result

    def _validate_type(self, field: str, value: Any, expected_type: str, result: ValidationResult):
        """验证类型"""
        type_checks = {
            "string": lambda v: isinstance(v, str),
            "integer": lambda v: isinstance(v, int) and not isinstance(v, bool),
            "number": lambda v: isinstance(v, (int, float)) and not isinstance(v, bool),
            "boolean": lambda v: isinstance(v, bool),
            "array": lambda v: isinstance(v, list),
            "object": lambda v: isinstance(v, dict),
        }

        check = type_checks.get(expected_type)
        if check and not check(value):
            result.add_error(field, f"Expected type {expected_type}", type(value).__name__)


def validate_json_file(filepath: str, schema: dict) -> ValidationResult:
    """验证 JSON 文件"""
    with open(filepath, encoding="utf-8") as f:
        data = json.load(f)

    validator = SchemaValidator(schema)
    return validator.validate(data)


def validate_json_string(json_str: str, schema: dict) -> ValidationResult:
    """验证 JSON 字符串"""
    data = json.loads(json_str)
    validator = SchemaValidator(schema)
    return validator.validate(data)


def create_sample_schema() -> dict:
    """创建示例 Schema"""
    return {
        "name": "sample_node",
        "version": "1.0.0",
        "inputs": [
            {
                "name": "raw_feed",
                "type": "object",
                "required": True,
                "description": "Raw market feed",
                "properties": {
                    "symbol": {"type": "string"},
                    "price": {"type": "number"},
                    "volume": {"type": "number"},
                    "timestamp": {"type": "integer"},
                },
                "required_fields": ["symbol", "price", "timestamp"],
            }
        ],
        "outputs": [
            {
                "name": "ohlcv",
                "type": "object",
                "required": True,
                "description": "OHLCV data",
                "properties": {
                    "symbol": {"type": "string"},
                    "open": {"type": "number"},
                    "high": {"type": "number"},
                    "low": {"type": "number"},
                    "close": {"type": "number"},
                    "volume": {"type": "number"},
                },
                "required_fields": ["symbol", "close"],
            }
        ],
        "constraints": [{"name": "max_latency_ms", "type": "runtime", "value": 1000, "description": "Maximum latency"}],
    }


def main():
    """CLI 主函数"""
    parser = argparse.ArgumentParser(
        description="CapsuleNode Schema Validator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # 验证 JSON 文件
  python validator_cli.py validate data.json --schema schema.yaml

  # 验证 JSON 字符串
  python validator_cli.py validate-json '{"raw_feed": {...}}'

  # 验证标准输入
  echo '{"raw_feed": {...}}' | python validator_cli.py validate-stdin
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # validate 命令
    validate_parser = subparsers.add_parser("validate", help="Validate JSON file against schema")
    validate_parser.add_argument("file", help="JSON file to validate")
    validate_parser.add_argument("--schema", "-s", required=True, help="Schema file (YAML)")

    # validate-json 命令
    json_parser = subparsers.add_parser("validate-json", help="Validate JSON string")
    json_parser.add_argument("json", help="JSON string to validate")
    json_parser.add_argument("--schema", "-s", required=True, help="Schema file (YAML)")

    # validate-stdin 命令
    stdin_parser = subparsers.add_parser("validate-stdin", help="Validate JSON from stdin")
    stdin_parser.add_argument("--schema", "-s", required=True, help="Schema file (YAML)")

    # sample-schema 命令
    sample_parser = subparsers.add_parser("sample-schema", help="Print sample schema")

    args = parser.parse_args()

    if args.command == "validate":
        # 验证文件
        import yaml

        with open(args.schema, encoding="utf-8") as f:
            schema = yaml.safe_load(f)

        result = validate_json_file(args.file, schema)
        print(result)
        sys.exit(0 if result.valid else 1)

    elif args.command == "validate-json":
        import yaml

        with open(args.schema, encoding="utf-8") as f:
            schema = yaml.safe_load(f)

        result = validate_json_string(args.json, schema)
        print(result)
        sys.exit(0 if result.valid else 1)

    elif args.command == "validate-stdin":
        import yaml

        with open(args.schema, encoding="utf-8") as f:
            schema = yaml.safe_load(f)

        json_str = sys.stdin.read()
        result = validate_json_string(json_str, schema)
        print(result)
        sys.exit(0 if result.valid else 1)

    elif args.command == "sample-schema":
        import yaml

        schema = create_sample_schema()
        print(yaml.dump(schema, allow_unicode=True))

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
