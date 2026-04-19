#!/usr/bin/env python3
"""
本地数据获取器
"""

import sys
import logging
from typing import Optional
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

try:
    import pandas as pd
    import requests
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False


def fetch_btc_data(
    interval: str = "1m",
    limit: int = 500,
    save_csv: bool = False,
    output_dir: str = None
) -> Optional["pd.DataFrame"]:
    """
    从 Binance 获取 BTC 数据

    Args:
        interval: K线间隔 (1m, 5m, 15m, 1h, 4h, 1d)
        limit: 数据条数
        save_csv: 是否保存 CSV
        output_dir: 输出目录

    Returns:
        DataFrame 或 None
    """
    if not PANDAS_AVAILABLE:
        logger.warning("pandas 未安装，无法获取数据")
        return None

    try:
        url = "https://api.binance.com/api/v3/klines"
        params = {
            "symbol": "BTCUSDT",
            "interval": interval,
            "limit": limit,
        }
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        df = pd.DataFrame(data, columns=[
            "open_time", "open", "high", "low", "close", "volume",
            "close_time", "quote_asset_volume", "num_trades",
            "taker_buy_base", "taker_buy_quote", "ignore"
        ])

        df["open_time"] = pd.to_datetime(df["open_time"], unit="ms")
        for col in ["open", "high", "low", "close", "volume"]:
            df[col] = pd.to_numeric(df[col])

        if save_csv:
            out_dir = Path(output_dir) if output_dir else Path(__file__).parent.parent / "data"
            out_dir.mkdir(parents=True, exist_ok=True)
            fname = out_dir / f"BTCUSDT_{interval}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            df.to_csv(fname, index=False)
            logger.info(f"数据已保存: {fname}")

        return df

    except Exception as e:
        logger.error(f"获取 Binance 数据失败: {e}")
        return None


def load_csv_data(
    symbol: str = "BTCUSDT",
    interval: str = "1m",
    data_dir: str = None,
    limit: int = None
) -> Optional["pd.DataFrame"]:
    """从本地 CSV 加载数据"""
    if not PANDAS_AVAILABLE:
        return None

    if data_dir is None:
        data_dir = Path(__file__).parent.parent / "data"
    else:
        data_dir = Path(data_dir)

    pattern = f"{symbol}_{interval}"
    candidates = sorted(data_dir.glob(f"{pattern}*.csv"))

    if not candidates:
        return None

    latest = candidates[-1]
    df = pd.read_csv(latest)

    if limit:
        df = df.tail(limit)

    return df
