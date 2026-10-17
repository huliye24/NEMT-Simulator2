"""统一 K 线数据契约 (Canonical)。

本模块是 NEMT 研究主链路的唯一数据入口契约。所有下游模块
(变量计算 / 事件检测 / 策略 / 回测) 只能消费这里定义的 CandleSeries，
不得再自行解析 CSV 或交易所原始返回。

设计约束:
    - 时间戳统一为 UTC 毫秒 epoch (int)
    - 严格按时间升序
    - 纯标准库实现，不依赖 numpy / pandas，保证 CPU 单机可跑且结果确定
"""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Sequence

# ---------------------------------------------------------------- 常量

TIMEFRAME_MS: Dict[str, int] = {
    "1m": 60_000,
    "3m": 180_000,
    "5m": 300_000,
    "15m": 900_000,
    "30m": 1_800_000,
    "1h": 3_600_000,
    "2h": 7_200_000,
    "4h": 14_400_000,
    "6h": 21_600_000,
    "12h": 43_200_000,
    "1d": 86_400_000,
}

# 一年按 365 天计，用于年化
BARS_PER_YEAR: Dict[str, float] = {
    "1m": 365 * 24 * 60,
    "5m": 365 * 24 * 12,
    "15m": 365 * 24 * 4,
    "1h": 365 * 24,
    "4h": 365 * 6,
    "1d": 365,
}


def timeframe_to_ms(timeframe: str) -> int:
    """把周期字符串转换为毫秒。未知周期直接报错，不做静默猜测。"""
    try:
        return TIMEFRAME_MS[timeframe]
    except KeyError:
        raise ValueError(
            f"未知周期 {timeframe!r}; 支持: {sorted(TIMEFRAME_MS)}"
        ) from None


def bars_per_year(timeframe: str) -> float:
    """返回该周期下一年的 K 线根数，用于年化收益与 Sharpe。"""
    if timeframe in BARS_PER_YEAR:
        return BARS_PER_YEAR[timeframe]
    ms = timeframe_to_ms(timeframe)
    return 365 * 24 * 3_600_000 / ms


# ---------------------------------------------------------------- 数据契约


@dataclass(frozen=True)
class Candle:
    """单根 K 线。timestamp 为 UTC 毫秒 epoch，代表该 K 线的开盘时间。"""

    timestamp: int
    open: float
    high: float
    low: float
    close: float
    volume: float
    symbol: str = "BTCUSDT"
    timeframe: str = "1h"

    def __post_init__(self) -> None:
        # frozen dataclass 无法在 __post_init__ 里赋值，只做校验
        if not isinstance(self.timestamp, int):
            raise TypeError(f"timestamp 必须是 int (UTC ms epoch), 收到 {type(self.timestamp)}")


@dataclass
class DataQualityReport:
    """数据质量报告。任何一项为 True 都意味着数据不可直接用于实验。"""

    total_rows: int = 0
    kept_rows: int = 0
    duplicate_timestamps: int = 0
    unsorted_input: bool = False
    missing_bars: int = 0
    missing_examples: List[int] = field(default_factory=list)
    non_positive_price: int = 0
    negative_volume: int = 0
    ohlc_violations: int = 0
    unclosed_last_bar_dropped: bool = False
    start_ms: Optional[int] = None
    end_ms: Optional[int] = None
    warnings: List[str] = field(default_factory=list)

    def is_clean(self) -> bool:
        """是否在严格意义下干净（允许丢弃未收盘最后一根）。"""
        return (
            self.duplicate_timestamps == 0
            and self.missing_bars == 0
            and self.non_positive_price == 0
            and self.negative_volume == 0
            and self.ohlc_violations == 0
            and not self.unsorted_input
        )

    def to_dict(self) -> dict:
        d = asdict(self)
        d["is_clean"] = self.is_clean()
        return d


@dataclass
class CandleSeries:
    """有序 K 线序列。构造后保证升序、去重。"""

    candles: List[Candle]
    symbol: str
    timeframe: str
    quality: DataQualityReport = field(default_factory=DataQualityReport)

    def __len__(self) -> int:
        return len(self.candles)

    def __getitem__(self, idx):
        return self.candles[idx]

    @property
    def timestamps(self) -> List[int]:
        return [c.timestamp for c in self.candles]

    @property
    def opens(self) -> List[float]:
        return [c.open for c in self.candles]

    @property
    def highs(self) -> List[float]:
        return [c.high for c in self.candles]

    @property
    def lows(self) -> List[float]:
        return [c.low for c in self.candles]

    @property
    def closes(self) -> List[float]:
        return [c.close for c in self.candles]

    @property
    def volumes(self) -> List[float]:
        return [c.volume for c in self.candles]

    def start_ms(self) -> Optional[int]:
        return self.candles[0].timestamp if self.candles else None

    def end_ms(self) -> Optional[int]:
        return self.candles[-1].timestamp if self.candles else None

    def slice(self, start_ms: Optional[int] = None, end_ms: Optional[int] = None) -> "CandleSeries":
        """按 [start_ms, end_ms) 左闭右开切分，保持契约不变。"""
        out = [c for c in self.candles
               if (start_ms is None or c.timestamp >= start_ms)
               and (end_ms is None or c.timestamp < end_ms)]
        return CandleSeries(candles=out, symbol=self.symbol, timeframe=self.timeframe,
                            quality=self.quality)

    def coverage_days(self) -> float:
        if len(self.candles) < 2:
            return 0.0
        return (self.candles[-1].timestamp - self.candles[0].timestamp) / 86_400_000.0

    def to_csv(self, path: str) -> None:
        """落盘为规范 CSV，供后续实验复现使用。"""
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["timestamp", "open", "high", "low", "close", "volume",
                        "symbol", "timeframe"])
            for c in self.candles:
                w.writerow([c.timestamp, repr(c.open), repr(c.high), repr(c.low),
                            repr(c.close), repr(c.volume), c.symbol, c.timeframe])

    @staticmethod
    def from_csv(path: str) -> "CandleSeries":
        return load_csv(path)


# ---------------------------------------------------------------- 校验


def _is_bad_price(c: Candle) -> bool:
    """价格必须为正且有限。"""
    vals = (c.open, c.high, c.low, c.close)
    for v in vals:
        if v != v or v in (float("inf"), float("-inf")):  # NaN / Inf
            return True
        if v <= 0:
            return True
    return False


def _is_ohlc_violation(c: Candle) -> bool:
    """high 必须 >= max(open, close)，low 必须 <= min(open, close)，且 low <= high。"""
    if c.high < max(c.open, c.close):
        return True
    if c.low > min(c.open, c.close):
        return True
    if c.low > c.high:
        return True
    return False


def validate_and_build(
    rows: Sequence[Candle],
    symbol: str,
    timeframe: str,
    drop_unclosed_last: bool = True,
    now_ms: Optional[int] = None,
) -> CandleSeries:
    """清洗并构建 CandleSeries。

    步骤:
        1. 丢弃非正价格 / 负成交量 / OHLC 关系违规的行
        2. 检查是否原本升序
        3. 按 timestamp 升序排序
        4. 按 timestamp 去重（保留首次出现）
        5. 检查缺失 K 线（按周期推断应有多少根）
        6. 可选：丢弃最后一根尚未收盘的 K 线

    drop_unclosed_last 是防未来数据泄漏的关键开关：
    交易所返回的最后一根 K 线往往是未定盘的，其 high/low/close 会继续变动，
    若被事件检测消费即构成前视偏差。
    """
    report = DataQualityReport(total_rows=len(rows))

    cleaned: List[Candle] = []
    for c in rows:
        if _is_bad_price(c):
            report.non_positive_price += 1
            continue
        if c.volume < 0:
            report.negative_volume += 1
            continue
        if _is_ohlc_violation(c):
            report.ohlc_violations += 1
            continue
        cleaned.append(c)

    if cleaned:
        ts = [c.timestamp for c in cleaned]
        report.unsorted_input = any(ts[i] > ts[i + 1] for i in range(len(ts) - 1))
        cleaned.sort(key=lambda c: c.timestamp)

    deduped: List[Candle] = []
    seen = set()
    for c in cleaned:
        if c.timestamp in seen:
            report.duplicate_timestamps += 1
            continue
        seen.add(c.timestamp)
        deduped.append(c)

    if drop_unclosed_last and deduped:
        tf_ms = timeframe_to_ms(timeframe)
        if now_ms is None:
            import time
            now_ms = int(time.time() * 1000)
        last = deduped[-1]
        if last.timestamp + tf_ms > now_ms:
            deduped = deduped[:-1]
            report.unclosed_last_bar_dropped = True
            report.warnings.append(
                f"丢弃未收盘最后一根 K 线 timestamp={last.timestamp} (防前视)"
            )

    if len(deduped) >= 2:
        tf_ms = timeframe_to_ms(timeframe)
        expected = (deduped[-1].timestamp - deduped[0].timestamp) // tf_ms + 1
        report.missing_bars = max(0, expected - len(deduped))
        if report.missing_bars > 0:
            # 给出最多 10 个缺失点示例
            present = {c.timestamp for c in deduped}
            t = deduped[0].timestamp
            ex: List[int] = []
            while t <= deduped[-1].timestamp and len(ex) < 10:
                if t not in present:
                    ex.append(t)
                t += tf_ms
            report.missing_examples = ex

    report.kept_rows = len(deduped)
    if deduped:
        report.start_ms = deduped[0].timestamp
        report.end_ms = deduped[-1].timestamp

    if report.missing_bars > 0:
        report.warnings.append(
            f"检测到 {report.missing_bars} 根缺失 K 线；实验将对缺失区间保持保守，不做插值填充"
        )
    if report.duplicate_timestamps > 0:
        report.warnings.append(f"丢弃 {report.duplicate_timestamps} 根重复时间戳 K 线")

    return CandleSeries(candles=deduped, symbol=symbol, timeframe=timeframe, quality=report)


# ---------------------------------------------------------------- 加载


def _to_float(x) -> float:
    if isinstance(x, (int, float)):
        return float(x)
    s = str(x).strip()
    if s == "" or s.lower() in ("nan", "null", "none"):
        return float("nan")
    return float(s)


def _coerce_timestamp(value, path: str) -> int:
    """把各种时间戳表示统一成 UTC 毫秒 epoch。

    接受:
        - int / float 的 epoch（自动判定秒级还是毫秒级）
        - ISO8601 字符串（含 'Z' 或带偏移），一律按 UTC 解释
    """
    if isinstance(value, (int, float)):
        v = int(value)
        # 小于 1e11 视为秒级 epoch（2001-09-09 之前阈值为 1e11 ms）
        if v < 100_000_000_000:
            return v * 1000
        return v

    s = str(value).strip()
    try:
        v = int(float(s))
        if v < 100_000_000_000:
            return v * 1000
        return v
    except ValueError:
        pass

    import datetime as _dt

    iso = s.replace("Z", "+00:00")
    try:
        d = _dt.datetime.fromisoformat(iso)
    except ValueError:
        raise ValueError(f"{path}: 无法解析时间戳 {value!r}") from None
    if d.tzinfo is None:
        d = d.replace(tzinfo=_dt.timezone.utc)
    return int(d.timestamp() * 1000)


def load_csv(
    path: str,
    symbol: Optional[str] = None,
    timeframe: Optional[str] = None,
) -> CandleSeries:
    """从 CSV 加载 K 线。

    兼容多种列名写法（本仓库历史 CSV 列名三套互不兼容）:
        timestamp / open_time / time / date
        open / o, high / h, low / l, close / c, volume / v
    """
    with open(path, "r", newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            raise ValueError(f"{path}: CSV 无表头")
        header = {h.strip().lower(): h for h in reader.fieldnames}

        def pick(*names: str) -> Optional[str]:
            for n in names:
                if n in header:
                    return header[n]
            return None

        col_ts = pick("timestamp", "open_time", "opentime", "time", "date", "datetime")
        col_o = pick("open", "o")
        col_h = pick("high", "h")
        col_l = pick("low", "l")
        col_c = pick("close", "c")
        col_v = pick("volume", "v", "vol")
        col_sym = pick("symbol")
        col_tf = pick("timeframe", "interval")

        if not all([col_ts, col_o, col_h, col_l, col_c, col_v]):
            raise ValueError(
                f"{path}: 缺少必要列。找到表头={list(reader.fieldnames)}；"
                f"需要 timestamp/open/high/low/close/volume"
            )

        rows: List[Candle] = []
        for raw in reader:
            try:
                ts = _coerce_timestamp(raw[col_ts], path)
                rows.append(Candle(
                    timestamp=ts,
                    open=_to_float(raw[col_o]),
                    high=_to_float(raw[col_h]),
                    low=_to_float(raw[col_l]),
                    close=_to_float(raw[col_c]),
                    volume=_to_float(raw[col_v]),
                    symbol=(raw[col_sym] if col_sym else "") or "",
                    timeframe=(raw[col_tf] if col_tf else "") or "",
                ))
            except (ValueError, TypeError):
                continue

    if not rows:
        raise ValueError(f"{path}: 未解析出任何有效 K 线")

    sym = symbol or next((c.symbol for c in rows if c.symbol), "") or "UNKNOWN"
    tf = timeframe or next((c.timeframe for c in rows if c.timeframe), "") or "1h"

    normalized = [
        Candle(c.timestamp, c.open, c.high, c.low, c.close, c.volume, sym, tf)
        for c in rows
    ]
    return validate_and_build(normalized, sym, tf)


def write_quality_report(report: DataQualityReport, path: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(report.to_dict(), f, indent=2, ensure_ascii=False)
