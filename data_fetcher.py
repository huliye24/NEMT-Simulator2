"""
数据获取模块
从Binance获取BTC历史数据
"""

import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Optional
import time


class BinanceDataFetcher:
    """Binance API数据获取器"""

    BASE_URL = "https://api.binance.com/api/v3"

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) NEMT-Simulator/1.0'
        })

    def fetch_klines(
        self,
        symbol: str = "BTCUSDT",
        interval: str = "1m",
        limit: int = 1000,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None
    ) -> pd.DataFrame:
        """
        获取K线数据

        Args:
            symbol: 交易对符号
            interval: K线周期 (1m, 5m, 15m, 1h, 4h, 1d, 1w)
            limit: 数据条数 (1-1000)
            start_time: 开始时间戳(毫秒)
            end_time: 结束时间戳(毫秒)

        Returns:
            DataFrame包含OHLCV数据
        """
        params = {
            "symbol": symbol.upper(),
            "interval": interval,
            "limit": limit
        }

        if start_time:
            params["startTime"] = start_time
        if end_time:
            params["endTime"] = end_time

        url = f"{self.BASE_URL}/klines"

        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            if not data:
                print("警告: API返回空数据")
                return pd.DataFrame()

            # 构建DataFrame
            df = pd.DataFrame(data, columns=[
                "open_time", "open", "high", "low", "close", "volume",
                "close_time", "quote_volume", "trades", "taker_buy_base",
                "taker_buy_quote", "ignore"
            ])

            # 类型转换
            numeric_cols = ["open", "high", "low", "close", "volume", "quote_volume"]
            for col in numeric_cols:
                df[col] = pd.to_numeric(df[col], errors='coerce')

            df["open_time"] = pd.to_datetime(df["open_time"], unit='ms')
            df["close_time"] = pd.to_datetime(df["close_time"], unit='ms')

            return df

        except requests.exceptions.RequestException as e:
            print(f"网络错误: {e}")
            return pd.DataFrame()

    def fetch_multiple_klines(
        self,
        symbol: str = "BTCUSDT",
        interval: str = "1m",
        days: int = 7
    ) -> pd.DataFrame:
        """
        获取多天数据（自动分页）

        Args:
            symbol: 交易对
            interval: K线周期
            days: 获取的天数

        Returns:
            合并后的DataFrame
        """
        all_data = []
        end_time = int(datetime.now().timestamp() * 1000)
        start_time = int((datetime.now() - timedelta(days=days)).timestamp() * 1000)

        limit = 1000  # API单次最大1000条

        while start_time < end_time:
            # 根据interval估算需要多少条
            interval_ms = self._interval_to_ms(interval)
            fetch_until = min(start_time + limit * interval_ms, end_time)

            df = self.fetch_klines(
                symbol=symbol,
                interval=interval,
                start_time=start_time,
                end_time=fetch_until
            )

            if df.empty:
                break

            all_data.append(df)
            start_time = int(df["close_time"].iloc[-1].timestamp() * 1000) + interval_ms

            time.sleep(0.2)  # 避免API限流

        if all_data:
            return pd.concat(all_data, ignore_index=True).drop_duplicates()
        return pd.DataFrame()

    @staticmethod
    def _interval_to_ms(interval: str) -> int:
        """将interval转换为毫秒"""
        mapping = {
            "1m": 60 * 1000,
            "5m": 5 * 60 * 1000,
            "15m": 15 * 60 * 1000,
            "1h": 60 * 60 * 1000,
            "4h": 4 * 60 * 60 * 1000,
            "1d": 24 * 60 * 60 * 1000,
            "1w": 7 * 24 * 60 * 60 * 1000
        }
        return mapping.get(interval, 60 * 1000)

    def get_price(self, symbol: str = "BTCUSDT") -> Optional[float]:
        """获取当前价格"""
        try:
            url = f"{self.BASE_URL}/ticker/price"
            response = self.session.get(url, params={"symbol": symbol.upper()}, timeout=10)
            response.raise_for_status()
            return float(response.json()["price"])
        except:
            return None


def fetch_btc_data(
    interval: str = "1m",
    limit: int = 1000,
    save_csv: bool = True,
    csv_path: str = "btc_data.csv"
) -> pd.DataFrame:
    """
    便捷函数：获取BTC数据并保存

    Args:
        interval: K线周期
        limit: 数据条数
        save_csv: 是否保存CSV
        csv_path: CSV保存路径

    Returns:
        价格数据DataFrame
    """
    fetcher = BinanceDataFetcher()

    print(f"正在从Binance获取 BTCUSDT {interval} 数据...")
    df = fetcher.fetch_klines(symbol="BTCUSDT", interval=interval, limit=limit)

    if not df.empty:
        print(f"获取到 {len(df)} 条数据")
        print(f"时间范围: {df['open_time'].iloc[0]} ~ {df['close_time'].iloc[-1]}")

        if save_csv:
            df.to_csv(csv_path, index=False)
            print(f"数据已保存至: {csv_path}")

        return df
    else:
        print("获取数据失败")
        return pd.DataFrame()


# 演示用测试函数
if __name__ == "__main__":
    # 测试数据获取
    df = fetch_btc_data(interval="1m", limit=100)
    if not df.empty:
        print("\n数据预览:")
        print(df[['open_time', 'close', 'volume']].head())
