"""
Value Objects - 共享值对象模块

定义跨上下文使用的值对象：
- Money: 金额
- Percentage: 百分比
- TimeRange: 时间范围
- PriceRange: 价格范围

版本: v1.0.0
更新: 2026-04-27
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from decimal import ROUND_HALF_UP, Decimal
from typing import Any


@dataclass(frozen=True)
class Money:
    """
    金额值对象

    表示带币种的金额，使用 Decimal 避免浮点精度问题。
    不可变对象。
    """

    amount: Decimal
    currency: str = "USDT"

    def __post_init__(self):
        if not isinstance(self.amount, Decimal):
            object.__setattr__(self, "amount", Decimal(str(self.amount)))

    @classmethod
    def from_float(cls, amount: float, currency: str = "USDT") -> Money:
        return cls(amount=Decimal(str(amount)), currency=currency)

    @classmethod
    def from_int(cls, amount: int, currency: str = "USDT") -> Money:
        return cls(amount=Decimal(amount), currency=currency)

    @classmethod
    def zero(cls, currency: str = "USDT") -> Money:
        return cls(amount=Decimal("0"), currency=currency)

    def __add__(self, other: Money) -> Money:
        if self.currency != other.currency:
            raise ValueError(f"Cannot add {self.currency} and {other.currency}")
        return Money(amount=self.amount + other.amount, currency=self.currency)

    def __sub__(self, other: Money) -> Money:
        if self.currency != other.currency:
            raise ValueError(f"Cannot subtract {self.currency} and {other.currency}")
        return Money(amount=self.amount - other.amount, currency=self.currency)

    def __mul__(self, factor: float) -> Money:
        return Money(amount=self.amount * Decimal(str(factor)), currency=self.currency)

    def __truediv__(self, other: Money | float) -> Money | float:
        if isinstance(other, Money):
            if self.currency != other.currency:
                raise ValueError(f"Cannot divide {self.currency} and {other.currency}")
            return float(self.amount / other.amount)
        return Money(amount=self.amount / Decimal(str(other)), currency=self.currency)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Money):
            return False
        return self.amount == other.amount and self.currency == other.currency

    def __lt__(self, other: Money) -> bool:
        if self.currency != other.currency:
            raise ValueError(f"Cannot compare {self.currency} and {other.currency}")
        return self.amount < other.amount

    def __le__(self, other: Money) -> bool:
        return self == other or self < other

    def __gt__(self, other: Money) -> bool:
        return not self <= other

    def __ge__(self, other: Money) -> bool:
        return not self < other

    def round(self, decimals: int = 8) -> Money:
        """四舍五入到指定小数位"""
        quantize_str = "0." + "0" * decimals
        return Money(amount=self.amount.quantize(Decimal(quantize_str), rounding=ROUND_HALF_UP), currency=self.currency)

    def to_float(self) -> float:
        return float(self.amount)

    def to_dict(self) -> dict[str, Any]:
        return {
            "amount": str(self.amount),
            "currency": self.currency,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Money:
        return cls(
            amount=Decimal(str(data.get("amount", 0))),
            currency=data.get("currency", "USDT"),
        )

    def __repr__(self) -> str:
        return f"Money({self.amount} {self.currency})"


@dataclass(frozen=True)
class Percentage:
    """
    百分比值对象

    表示百分比值，支持加减乘除运算。
    不可变对象。
    """

    value: Decimal  # 存储为小数形式 (0.05 表示 5%)

    def __post_init__(self):
        if not isinstance(self.value, Decimal):
            object.__setattr__(self, "value", Decimal(str(self.value)))

    @classmethod
    def from_percent(cls, percent: float) -> Percentage:
        return cls(value=Decimal(str(percent)) / Decimal("100"))

    @classmethod
    def from_basis_points(cls, bps: int) -> Percentage:
        """从基点创建 (100 bps = 1%)"""
        return cls(value=Decimal(str(bps)) / Decimal("10000"))

    @property
    def percent(self) -> float:
        """转换为百分比数值"""
        return float(self.value * Decimal("100"))

    @property
    def basis_points(self) -> int:
        """转换为基点"""
        return int(self.value * Decimal("10000"))

    def __add__(self, other: Percentage) -> Percentage:
        return Percentage(value=self.value + other.value)

    def __sub__(self, other: Percentage) -> Percentage:
        return Percentage(value=self.value - other.value)

    def __mul__(self, factor: float | Decimal) -> Percentage:
        return Percentage(value=self.value * Decimal(str(factor)))

    def __truediv__(self, other: Percentage | float) -> Percentage | float:
        if isinstance(other, Percentage):
            return float(self.value / other.value)
        return Percentage(value=self.value / Decimal(str(other)))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Percentage):
            return False
        return self.value == other.value

    def __lt__(self, other: Percentage) -> bool:
        return self.value < other.value

    def __le__(self, other: Percentage) -> bool:
        return self.value <= other.value

    def __gt__(self, other: Percentage) -> bool:
        return self.value > other.value

    def __ge__(self, other: Percentage) -> bool:
        return self.value >= other.value

    def to_float(self) -> float:
        return float(self.value)

    def to_dict(self) -> dict[str, Any]:
        return {
            "value": str(self.value),
            "percent": self.percent,
            "basis_points": self.basis_points,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Percentage:
        if "percent" in data:
            return cls.from_percent(data["percent"])
        return cls(value=Decimal(str(data.get("value", 0))))

    def __repr__(self) -> str:
        return f"Percentage({self.percent}%)"


@dataclass(frozen=True)
class TimeRange:
    """
    时间范围值对象

    表示一个时间区间。
    不可变对象。
    """

    start: datetime
    end: datetime

    def __post_init__(self):
        if self.start > self.end:
            raise ValueError("start must be <= end")

    @property
    def duration(self) -> timedelta:
        """时间范围长度"""
        return self.end - self.start

    @property
    def duration_seconds(self) -> float:
        """时间范围秒数"""
        return self.duration.total_seconds()

    @property
    def duration_hours(self) -> float:
        """时间范围小时数"""
        return self.duration_seconds / 3600

    def contains(self, dt: datetime) -> bool:
        """判断时间是否在范围内"""
        return self.start <= dt <= self.end

    def overlaps(self, other: TimeRange) -> bool:
        """判断两个时间范围是否重叠"""
        return self.start < other.end and self.end > other.start

    def union(self, other: TimeRange) -> TimeRange:
        """与另一个时间范围合并"""
        return TimeRange(start=min(self.start, other.start), end=max(self.end, other.end))

    def intersection(self, other: TimeRange) -> TimeRange | None:
        """与另一个时间范围交集"""
        if not self.overlaps(other):
            return None
        return TimeRange(start=max(self.start, other.start), end=min(self.end, other.end))

    def to_dict(self) -> dict[str, Any]:
        return {
            "start": self.start.isoformat(),
            "end": self.end.isoformat(),
            "duration_seconds": self.duration_seconds,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TimeRange:
        start = data.get("start")
        if isinstance(start, str):
            start = datetime.fromisoformat(start)
        end = data.get("end")
        if isinstance(end, str):
            end = datetime.fromisoformat(end)
        return cls(start=start, end=end)

    def __repr__(self) -> str:
        return f"TimeRange({self.start} to {self.end})"


@dataclass(frozen=True)
class PriceRange:
    """
    价格范围值对象

    表示一个价格区间。
    不可变对象。
    """

    low: float
    high: float

    def __post_init__(self):
        if self.low > self.high:
            raise ValueError("low must be <= high")
        if self.low < 0 or self.high < 0:
            raise ValueError("prices must be non-negative")

    @property
    def midpoint(self) -> float:
        """价格区间中点"""
        return (self.low + self.high) / 2

    @property
    def width(self) -> float:
        """价格区间宽度"""
        return self.high - self.low

    @property
    def width_percent(self) -> float:
        """价格区间宽度百分比"""
        return self.width / self.low if self.low > 0 else 0

    def contains(self, price: float) -> bool:
        """判断价格是否在范围内"""
        return self.low <= price <= self.high

    def is_within(self, percent: float) -> bool:
        """判断价格是否在区间宽度的百分比内"""
        return self.width_percent <= percent

    def expand(self, factor: float) -> PriceRange:
        """按因子扩展区间"""
        midpoint = self.midpoint
        half_width = (self.width / 2) * factor
        return PriceRange(low=max(0, midpoint - half_width), high=midpoint + half_width)

    def to_dict(self) -> dict[str, Any]:
        return {
            "low": self.low,
            "high": self.high,
            "midpoint": self.midpoint,
            "width": self.width,
            "width_percent": self.width_percent,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PriceRange:
        return cls(low=float(data["low"]), high=float(data["high"]))

    def __repr__(self) -> str:
        return f"PriceRange({self.low} to {self.high})"


# =============================================================================
# Serialization Utilities
# =============================================================================


def serialize_entity(entity: Any) -> dict[str, Any]:
    """
    通用实体序列化

    Args:
        entity: 实体对象

    Returns:
        字典表示
    """
    if hasattr(entity, "to_dict"):
        return entity.to_dict()
    elif hasattr(entity, "__dict__"):
        return {k: serialize_entity(v) for k, v in entity.__dict__.items() if not k.startswith("_")}
    else:
        return entity


def deserialize_entity(data: dict[str, Any], entity_class: type) -> Any:
    """
    通用实体反序列化

    Args:
        data: 字典数据
        entity_class: 实体类

    Returns:
        实体对象
    """
    if hasattr(entity_class, "from_dict"):
        return entity_class.from_dict(data)
    else:
        return entity_class(**data)


# =============================================================================
# Entity Versioning
# =============================================================================


@dataclass
class VersionInfo:
    """实体版本信息"""

    version: int = 1
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    created_by: str = ""
    updated_by: str = ""

    def increment(self, updated_by: str = "") -> VersionInfo:
        """递增版本号"""
        return VersionInfo(
            version=self.version + 1,
            created_at=self.created_at,
            updated_at=datetime.now(),
            created_by=self.created_by,
            updated_by=updated_by,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "created_by": self.created_by,
            "updated_by": self.updated_by,
        }
