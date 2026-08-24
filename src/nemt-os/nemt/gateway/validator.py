"""
RequestValidator - 请求验证器

提供请求参数验证、数据验证能力。
"""

import logging
import re
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

__all__ = [
    "ValidationError",
    "ValidationRule",
    "Validator",
    "RequestValidator",
]


class ValidationError(Exception):
    """验证错误"""

    def __init__(self, message: str, field: str = None):
        self.message = message
        self.field = field
        super().__init__(message)


@dataclass
class ValidationRule:
    """验证规则"""

    name: str
    message: str
    validator: Callable[[Any], bool]


class Validator:
    """
    验证器

    示例:
    ```python
    validator = Validator()

    # 添加规则
    validator.add("email", [Validators.required, Validators.email])
    validator.add("age", [Validators.required, Validators.min(18)])

    # 验证数据
    try:
        validator.validate({"email": "test@example.com", "age": 25})
    except ValidationError as e:
        print(f"验证失败: {e.message}")
    ```
    """

    def __init__(self):
        self._rules: dict[str, list[Callable]] = {}
        self._messages: dict[str, str] = {}

    def add(self, field: str, rules: list[Callable], message: str = None) -> "Validator":
        """添加字段验证规则"""
        self._rules[field] = rules
        if message:
            self._messages[field] = message
        return self

    def validate(self, data: dict) -> dict:
        """验证数据"""
        errors = {}

        for field, rules in self._rules.items():
            value = data.get(field)

            for rule in rules:
                try:
                    result = rule(value, data)
                    if result is False:
                        errors[field] = self._messages.get(field, f"Validation failed for {field}")
                        break
                    elif isinstance(result, str):
                        errors[field] = result
                        break
                except ValidationError as e:
                    errors[field] = e.message
                    break

        if errors:
            raise ValidationError("Validation failed", errors)

        return data

    def is_valid(self, data: dict) -> bool:
        """检查数据是否有效"""
        try:
            self.validate(data)
            return True
        except ValidationError:
            return False


class Validators:
    """常用验证器"""

    @staticmethod
    def required(message: str = "Field is required") -> Callable:
        """必填验证"""

        def validate(value, data):
            if value is None or value == "":
                raise ValidationError(message)
            return True

        return validate

    @staticmethod
    def email(message: str = "Invalid email format") -> Callable:
        """邮箱验证"""
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        compiled = re.compile(pattern)

        def validate(value, data):
            if value and not compiled.match(value):
                raise ValidationError(message)
            return True

        return validate

    @staticmethod
    def min(min_value: int | float, message: str = None) -> Callable:
        """最小值验证"""

        def validate(value, data):
            if value is not None and value < min_value:
                msg = message or f"Value must be at least {min_value}"
                raise ValidationError(msg)
            return True

        return validate

    @staticmethod
    def max(max_value: int | float, message: str = None) -> Callable:
        """最大值验证"""

        def validate(value, data):
            if value is not None and value > max_value:
                msg = message or f"Value must be at most {max_value}"
                raise ValidationError(msg)
            return True

        return validate

    @staticmethod
    def min_length(min_len: int, message: str = None) -> Callable:
        """最小长度验证"""

        def validate(value, data):
            if value and len(str(value)) < min_len:
                msg = message or f"Length must be at least {min_len}"
                raise ValidationError(msg)
            return True

        return validate

    @staticmethod
    def max_length(max_len: int, message: str = None) -> Callable:
        """最大长度验证"""

        def validate(value, data):
            if value and len(str(value)) > max_len:
                msg = message or f"Length must be at most {max_len}"
                raise ValidationError(msg)
            return True

        return validate

    @staticmethod
    def pattern(pattern: str, message: str = "Invalid format") -> Callable:
        """正则验证"""
        compiled = re.compile(pattern)

        def validate(value, data):
            if value and not compiled.match(str(value)):
                raise ValidationError(message)
            return True

        return validate

    @staticmethod
    def choices(choices: list[Any], message: str = None) -> Callable:
        """选项验证"""

        def validate(value, data):
            if value and value not in choices:
                msg = message or f"Value must be one of {choices}"
                raise ValidationError(msg)
            return True

        return validate

    @staticmethod
    def type(expected_type: type, message: str = None) -> Callable:
        """类型验证"""

        def validate(value, data):
            if value is not None and not isinstance(value, expected_type):
                msg = message or f"Expected type {expected_type.__name__}"
                raise ValidationError(msg)
            return True

        return validate

    @staticmethod
    def url(message: str = "Invalid URL format") -> Callable:
        """URL 验证"""
        pattern = r"^https?://[^\s/$.?#].[^\s]*$"
        compiled = re.compile(pattern, re.IGNORECASE)

        def validate(value, data):
            if value and not compiled.match(str(value)):
                raise ValidationError(message)
            return True

        return validate

    @staticmethod
    def uuid(message: str = "Invalid UUID format") -> Callable:
        """UUID 验证"""
        pattern = r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
        compiled = re.compile(pattern, re.IGNORECASE)

        def validate(value, data):
            if value and not compiled.match(str(value)):
                raise ValidationError(message)
            return True

        return validate

    @staticmethod
    def custom(validator: Callable[[Any], bool], message: str = "Validation failed") -> Callable:
        """自定义验证"""

        def validate(value, data):
            if not validator(value):
                raise ValidationError(message)
            return True

        return validate


class RequestValidator:
    """
    请求验证器

    示例:
    ```python
    validator = RequestValidator()

    # 定义验证规则
    validator.add_rule("create_user", {
        "username": [Validators.required, Validators.min_length(3)],
        "email": [Validators.required, Validators.email],
        "age": [Validators.min(18), Validators.max(120)],
    })

    # 验证请求
    errors = validator.validate_request("create_user", request_data)
    if errors:
        return APIResponse.error("Validation failed", code=400, error=errors)
    ```
    """

    def __init__(self):
        self._rule_sets: dict[str, dict[str, list[Callable]]] = {}
        self._logger = logging.getLogger("RequestValidator")

    def add_rule(self, name: str, rules: dict[str, list[Callable]]) -> None:
        """添加规则集"""
        self._rule_sets[name] = rules

    def validate_request(self, rule_name: str, data: dict) -> dict[str, str]:
        """验证请求"""
        if rule_name not in self._rule_sets:
            self._logger.warning(f"未知规则集: {rule_name}")
            return {}

        rules = self._rule_sets[rule_name]
        errors = {}

        for field, field_rules in rules.items():
            value = data.get(field)

            for rule in field_rules:
                try:
                    result = rule(value, data)
                    if result is False:
                        errors[field] = f"Validation failed for {field}"
                        break
                    elif isinstance(result, str):
                        errors[field] = result
                        break
                except ValidationError as e:
                    errors[field] = e.message
                    break

        return errors

    def is_valid(self, rule_name: str, data: dict) -> bool:
        """检查请求是否有效"""
        return len(self.validate_request(rule_name, data)) == 0
