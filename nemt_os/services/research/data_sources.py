"""数据源适配层 (Canonical)。

提供两种取数方式，二者产出完全相同的 CandleSeries 契约:
    1. CSV  —— 本地缓存 / 手工数据，实验可复现的首选
    2. Binance 公共行情 REST —— 仅用公开端点，不需要任何 API Key / 私钥

纪律:
    - 研究链路**绝不**读取任何私钥、绝不调用任何下单端点
    - 下载的数据必须落盘缓存，保证同一实验可重复执行得到同一结果
    - 所有网络失败都要抛出可理解的错误，不做静默降级（静默降级会污染实验结果）
"""

from __future__ import annotations

import csv
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Optional

from .candles import (
    Candle,
    CandleSeries,
    TIMEFRAME_MS,
    load_csv,
    validate_and_build,
)

BINANCE_PUBLIC_BASE = "https://api.binance.com"
KLINES_ENDPOINT = "/api/v3/klines"
KLINES_LIMIT = 1000  # Binance 单次上限


class DataSourceError(RuntimeError):
    """取数失败。携带可理解的上下文，便于 CLI 直接呈现给用户。"""


# ---------------------------------------------------------------- Binance 公共行情


def _http_get_json(url: str, timeout: int = 20, retries: int = 3) -> list:
    last_err: Optional[Exception] = None
    for attempt in range(1, retries + 1):
        try:
            req = urllib.request.Request(
                url, headers={"User-Agent": "nemt-research/0.1 (public market data)"}
            )
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                if resp.status != 200:
                    raise DataSourceError(f"HTTP {resp.status} from {url}")
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            last_err = e
            if e.code in (400, 401, 403):
                # 参数或权限问题，重试无意义
                raise DataSourceError(f"HTTP {e.code} {e.reason} — 请求被拒绝: {url}") from e
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as e:
            last_err = e
        if attempt < retries:
            time.sleep(0.5 * attempt)
    raise DataSourceError(
        f"取数失败（已重试 {retries} 次）: {url}; 最后错误: {last_err!r}"
    )


def fetch_binance_klines(
    symbol: str = "BTCUSDT",
    timeframe: str = "1h",
    start_ms: Optional[int] = None,
    end_ms: Optional[int] = None,
    base_url: str = BINANCE_PUBLIC_BASE,
) -> list:
    """分页拉取 Binance 公共 K 线，返回原始 list（每项是 Binance 的数组格式）。

    只访问 /api/v3/klines，该端点为公开只读，无需 API Key。
    """
    if timeframe not in TIMEFRAME_MS:
        raise DataSourceError(f"Binance 不支持周期 {timeframe!r}")

    if start_ms is None:
        start_ms = 0
    if end_ms is None:
        end_ms = int(time.time() * 1000)

    out: list = []
    cursor = start_ms
    tf_ms = TIMEFRAME_MS[timeframe]

    while cursor < end_ms:
        params = urllib.parse.urlencode({
            "symbol": symbol.upper(),
            "interval": timeframe,
            "startTime": cursor,
            "endTime": end_ms,
            "limit": KLINES_LIMIT,
        })
        url = f"{base_url}{KLINES_ENDPOINT}?{params}"
        batch = _http_get_json(url)
        if not isinstance(batch, list) or not batch:
            break
        out.extend(batch)
        last_open = int(batch[-1][0])
        if len(batch) < KLINES_LIMIT:
            break
        nxt = last_open + tf_ms
        if nxt <= cursor:  # 防止死循环
            break
        cursor = nxt

    return out


def _parse_binance_rows(raw: list, symbol: str, timeframe: str) -> list:
    """Binance klines 数组 -> Candle。

    Binance 返回字段:
        [open_time, open, high, low, close, volume, close_time,
         quote_asset_volume, num_trades, taker_buy_base, taker_buy_quote, ignore]
    """
    candles: list = []
    for r in raw:
        try:
            candles.append(Candle(
                timestamp=int(r[0]),
                open=float(r[1]),
                high=float(r[2]),
                low=float(r[3]),
                close=float(r[4]),
                volume=float(r[5]),
                symbol=symbol.upper(),
                timeframe=timeframe,
            ))
        except (ValueError, TypeError, IndexError):
            continue
    return candles


def load_binance(
    symbol: str = "BTCUSDT",
    timeframe: str = "1h",
    start_ms: Optional[int] = None,
    end_ms: Optional[int] = None,
) -> CandleSeries:
    """直接拉取并构建 CandleSeries（不落盘）。"""
    raw = fetch_binance_klines(symbol, timeframe, start_ms, end_ms)
    if not raw:
        raise DataSourceError(
            f"Binance 未返回任何 K 线: symbol={symbol} timeframe={timeframe} "
            f"start={start_ms} end={end_ms}"
        )
    rows = _parse_binance_rows(raw, symbol, timeframe)
    return validate_and_build(rows, symbol.upper(), timeframe)


# ---------------------------------------------------------------- 缓存


def cache_path_for(cache_dir: str, symbol: str, timeframe: str) -> str:
    os.makedirs(cache_dir, exist_ok=True)
    return os.path.join(cache_dir, f"{symbol.upper()}_{timeframe}.csv")


def load_or_download(
    symbol: str = "BTCUSDT",
    timeframe: str = "1h",
    start_ms: Optional[int] = None,
    end_ms: Optional[int] = None,
    cache_dir: str = "data/cache",
    use_cache: bool = True,
    refresh: bool = False,
) -> CandleSeries:
    """优先读缓存；不存在或要求刷新时才联网下载，并写回缓存。

    这样保证：同一份数据可以被反复复现，研究不依赖网络的即时可用性。
    """
    path = cache_path_for(cache_dir, symbol, timeframe)

    if use_cache and not refresh and os.path.exists(path):
        series = load_csv(path, symbol=symbol, timeframe=timeframe)
        if start_ms is not None:
            series = series.slice(start_ms=start_ms)
        if end_ms is not None:
            series = series.slice(end_ms=end_ms)
        return series

    series = load_binance(symbol, timeframe, start_ms, end_ms)
    if use_cache:
        series.to_csv(path)
    return series


def merge_into_cache(series: CandleSeries, cache_dir: str = "data/cache") -> str:
    """把一段数据并入已有缓存（按 timestamp 去重后整体重写）。"""
    path = cache_path_for(cache_dir, series.symbol, series.timeframe)
    merged = {c.timestamp: c for c in series.candles}

    if os.path.exists(path):
        try:
            existing = load_csv(path, symbol=series.symbol, timeframe=series.timeframe)
            for c in existing.candles:
                merged.setdefault(c.timestamp, c)
        except Exception:
            # 缓存损坏不应阻断合并，直接用新数据覆盖
            pass

    rows = [merged[t] for t in sorted(merged)]
    rebuilt = validate_and_build(rows, series.symbol, series.timeframe)
    rebuilt.to_csv(path)
    return path


# ---------------------------------------------------------------- 合成数据（仅用于测试）


def make_synthetic_series(
    n: int = 500,
    symbol: str = "SYNTH",
    timeframe: str = "1h",
    start_ms: int = 1_600_000_000_000,
    seed: int = 42,
) -> CandleSeries:
    """生成确定性合成 K 线，仅供单元测试与冒烟使用。

    **严禁**用它得出任何关于 NEMT 理论有效性的结论——它是人工构造的。
    """
    import random

    rng = random.Random(seed)
    tf_ms = TIMEFRAME_MS[timeframe]
    rows: list = []
    price = 30000.0
    for i in range(n):
        drift = rng.gauss(0.0, 0.004)
        price = max(1.0, price * (1.0 + drift))
        o = price
        c = max(1.0, price * (1.0 + rng.gauss(0.0, 0.003)))
        h = max(o, c) * (1.0 + abs(rng.gauss(0.0, 0.002)))
        l = min(o, c) * (1.0 - abs(rng.gauss(0.0, 0.002)))
        v = abs(rng.gauss(1000.0, 200.0))
        rows.append(Candle(
            timestamp=start_ms + i * tf_ms,
            open=o, high=h, low=l, close=c, volume=v,
            symbol=symbol, timeframe=timeframe,
        ))
    return validate_and_build(rows, symbol, timeframe, drop_unclosed_last=False)
