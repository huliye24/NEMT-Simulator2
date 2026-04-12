"""
NEMT数据获取模块 - Python版
支持多交易对、多时间周期的Binance数据获取
"""

import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Optional, List, Dict
import time
import os


class BinanceFetcher:
    """Binance API数据获取器"""

    BASE_URL = "https://api.binance.com/api/v3"
    UBASE_URL = "https://api.binance.com"  # 备用

    SYMBOLS = {
        'BTC': 'BTCUSDT',
        'ETH': 'ETHUSDT',
        'SOL': 'SOLUSDT',
        'BNB': 'BNBUSDT',
        'XRP': 'XRPUSDT',
        'ADA': 'ADAUSDT',
        'DOGE': 'DOGEUSDT',
        'DOT': 'DOTUSDT',
        'MATIC': 'MATICUSDT',
        'LINK': 'LINKUSDT'
    }

    INTERVALS = {
        '1m': ('1m', 60 * 1000),
        '5m': ('5m', 5 * 60 * 1000),
        '15m': ('15m', 15 * 60 * 1000),
        '30m': ('30m', 30 * 60 * 1000),
        '1h': ('1h', 60 * 60 * 1000),
        '4h': ('4h', 4 * 60 * 60 * 1000),
        '1d': ('1d', 24 * 60 * 60 * 1000),
        '1w': ('1w', 7 * 24 * 60 * 60 * 1000)
    }

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) NEMT-Simulator/2.0'
        })

    def fetch_klines(
        self,
        symbol: str,
        interval: str,
        limit: int = 1000,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None
    ) -> pd.DataFrame:
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
                print(f"警告: {symbol} {interval} API返回空数据")
                return pd.DataFrame()

            df = pd.DataFrame(data, columns=[
                "open_time", "open", "high", "low", "close", "volume",
                "close_time", "quote_volume", "trades", "taker_buy_base",
                "taker_buy_quote", "ignore"
            ])

            numeric_cols = ["open", "high", "low", "close", "volume", "quote_volume"]
            for col in numeric_cols:
                df[col] = pd.to_numeric(df[col], errors='coerce')

            df["open_time"] = pd.to_datetime(df["open_time"], unit='ms')
            df["close_time"] = pd.to_datetime(df["close_time"], unit='ms')
            df["symbol"] = symbol

            return df

        except requests.exceptions.RequestException as e:
            print(f"网络错误: {e}")
            return pd.DataFrame()

    def fetch_range(
        self,
        symbol: str,
        interval: str,
        start_date: str = None,
        end_date: str = None,
        days: int = None
    ) -> pd.DataFrame:
        """按日期范围获取数据"""
        if days is not None:
            end_time = int(datetime.now().timestamp() * 1000)
            start_time = int((datetime.now() - timedelta(days=days)).timestamp() * 1000)
        else:
            if end_date is None:
                end_time = int(datetime.now().timestamp() * 1000)
            else:
                end_time = int(datetime.strptime(end_date, '%Y-%m-%d').timestamp() * 1000) + 86400*1000

            if start_date is None:
                start_time = int((datetime.now() - timedelta(days=30)).timestamp() * 1000)
            else:
                start_time = int(datetime.strptime(start_date, '%Y-%m-%d').timestamp() * 1000)

        all_data = []
        limit = 1000
        interval_ms = self.INTERVALS.get(interval, self.INTERVALS['1h'])[1]

        print(f"  日期范围: {datetime.fromtimestamp(start_time/1000).strftime('%Y-%m-%d')} ~ {datetime.fromtimestamp(end_time/1000).strftime('%Y-%m-%d')}")

        while start_time < end_time:
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
            time.sleep(0.2)

        if all_data:
            result = pd.concat(all_data, ignore_index=True)
            result = result.drop_duplicates(subset=['open_time'], keep='last')
            result = result.sort_values('open_time').reset_index(drop=True)
            return result

        return pd.DataFrame()

    def fetch_multiple(
        self,
        symbol: str,
        interval: str,
        days: int = 7
    ) -> pd.DataFrame:
        all_data = []
        end_time = int(datetime.now().timestamp() * 1000)
        start_time = int((datetime.now() - timedelta(days=days)).timestamp() * 1000)

        limit = 1000
        interval_ms = self.INTERVALS.get(interval, self.INTERVALS['1h'])[1]

        while start_time < end_time:
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
            time.sleep(0.2)

        if all_data:
            result = pd.concat(all_data, ignore_index=True)
            result = result.drop_duplicates(subset=['open_time'], keep='last')
            result = result.sort_values('open_time').reset_index(drop=True)
            return result

        return pd.DataFrame()

    def fetch_symbols(
        self,
        symbols: List[str],
        interval: str = '1h',
        days: int = 7
    ) -> Dict[str, pd.DataFrame]:
        results = {}

        for sym in symbols:
            if sym not in self.SYMBOLS:
                print(f"警告: 不支持的交易对 {sym}")
                continue

            full_symbol = self.SYMBOLS[sym]
            print(f"获取 {full_symbol} {interval} 数据...")

            df = self.fetch_multiple(full_symbol, interval, days)
            if not df.empty:
                results[sym] = df
                print(f"  获取到 {len(df)} 条数据")
            else:
                print(f"  获取失败")

            time.sleep(0.1)

        return results

    def save_to_csv(
        self,
        data: Dict[str, pd.DataFrame],
        output_dir: str = "data"
    ) -> Dict[str, str]:
        os.makedirs(output_dir, exist_ok=True)
        paths = {}

        for sym, df in data.items():
            if df.empty:
                continue

            filename = f"{output_dir}/{sym}_{df['open_time'].iloc[0].strftime('%Y%m%d')}_{len(df)}rows.csv"
            df.to_csv(filename, index=False)
            paths[sym] = filename
            print(f"已保存: {filename}")

        return paths

    def get_current_price(self, symbol: str) -> Optional[float]:
        """获取当前价格"""
        try:
            url = f"{self.BASE_URL}/ticker/price"
            response = self.session.get(
                url,
                params={"symbol": symbol.upper()},
                timeout=10
            )
            response.raise_for_status()
            return float(response.json()["price"])
        except:
            return None


def fetch_by_range(
    symbols: List[str] = None,
    interval: str = '1h',
    start_date: str = None,
    end_date: str = None,
    days: int = 30,
    output_dir: str = "matlab_data",
    export_mat: bool = True
) -> Dict[str, pd.DataFrame]:
    """
    按日期范围获取数据（主要用于研究）

    示例:
        # 获取2026年4月的数据
        fetch_by_range('BTC', '1h', '2026-04-01', '2026-04-30')

        # 获取最近7天
        fetch_by_range('BTC', '4h', days=7)
    """
    if symbols is None:
        symbols = ['BTC', 'ETH']
    if isinstance(symbols, str):
        symbols = [symbols]

    fetcher = BinanceFetcher()
    results = {}

    for sym in symbols:
        if sym not in fetcher.SYMBOLS:
            print(f"警告: 不支持的交易对 {sym}")
            continue

        full_symbol = fetcher.SYMBOLS[sym]
        print(f"\n获取 {full_symbol} {interval} 数据...")

        df = fetcher.fetch_range(full_symbol, interval, start_date, end_date, days)

        if not df.empty:
            results[sym] = df
            print(f"  成功: {len(df)} 条数据")

            os.makedirs(output_dir, exist_ok=True)
            
            # 导出CSV
            csv_filename = f"{output_dir}/{sym}_{interval}.csv"
            clean_df = df[['open_time', 'open', 'high', 'low', 'close', 'volume']].copy()
            clean_df.columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
            clean_df.to_csv(csv_filename, index=False)
            print(f"  导出CSV: {csv_filename}")
            
            # 导出MAT格式
            if export_mat:
                try:
                    mat_file = export_as_mat({sym: df}, sym, interval, output_dir)
                    if mat_file:
                        print(f"  导出MAT: {mat_file}")
                except Exception as e:
                    print(f"  MAT导出失败: {e}")
        else:
            print(f"  失败")

        time.sleep(0.1)

    return results


def fetch_multi_symbols(
    symbols: List[str] = None,
    intervals: List[str] = None,
    days: int = 30,
    output_dir: str = "data",
    save_csv: bool = True
) -> Dict[str, Dict[str, pd.DataFrame]]:
    """获取多个交易对、多个周期的数据"""
    if symbols is None:
        symbols = ['BTC', 'ETH', 'SOL']
    if intervals is None:
        intervals = ['15m', '1h', '4h']

    fetcher = BinanceFetcher()
    results = {}

    for interval in intervals:
        print(f"\n{'='*50}")
        print(f"获取 {interval} 周期数据")
        print(f"{'='*50}")

        interval_data = fetcher.fetch_symbols(symbols, interval, days)

        if save_csv and interval_data:
            subdir = f"{output_dir}/{interval}"
            fetcher.save_to_csv(interval_data, subdir)

        for sym, df in interval_data.items():
            if sym not in results:
                results[sym] = {}
            results[sym][interval] = df

    return results


def load_csv_data(filepath: str) -> pd.DataFrame:
    """加载CSV数据"""
    df = pd.read_csv(filepath)
    df["open_time"] = pd.to_datetime(df["open_time"])
    df["close_time"] = pd.to_datetime(df["close_time"])
    return df


def export_for_matlab(
    data: Dict[str, Dict[str, pd.DataFrame]],
    output_dir: str = "matlab_data"
) -> None:
    """导出数据为MATLAB兼容格式"""
    os.makedirs(output_dir, exist_ok=True)

    for symbol, intervals in data.items():
        for interval, df in intervals.items():
            if df.empty:
                continue

            clean_df = df[['open_time', 'open', 'high', 'low', 'close', 'volume']].copy()
            clean_df.columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume']

            filename = f"{output_dir}/{symbol}_{interval}.csv"
            clean_df.to_csv(filename, index=False)
            print(f"导出: {filename}")


def export_as_mat(
    data: Dict[str, pd.DataFrame],
    symbol: str,
    interval: str,
    output_dir: str = "matlab_data",
    mat_filename: str = None
) -> str:
    """
    导出为MATLAB .mat格式
    
    输出:
        - .mat 文件: MATLAB可直接 load()
        - .csv 文件: 备用/预览用
    
    MATLAB加载方式:
        data = load('BTC_1h.mat');
        timestamps = data.timestamp;  % datetime数组
        prices = data.close;         % 数值数组
    """
    try:
        import scipy.io as sio
    except ImportError:
        print("需要安装scipy: pip install scipy")
        return None
    
    os.makedirs(output_dir, exist_ok=True)
    
    if isinstance(data, dict):
        df = data.get(symbol, data.get(list(data.keys())[0]))
    else:
        df = data
    
    if df.empty:
        return None
    
    clean_df = df[['open_time', 'open', 'high', 'low', 'close', 'volume']].copy()
    clean_df.columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
    
    # 转换为datetime数组 (MATLAB会识别为datetime类型)
    timestamps = clean_df['timestamp'].values
    
    # 构建MATLAB兼容的结构
    mat_data = {
        'timestamp': timestamps,
        'open': clean_df['open'].values.astype(np.float64),
        'high': clean_df['high'].values.astype(np.float64),
        'low': clean_df['low'].values.astype(np.float64),
        'close': clean_df['close'].values.astype(np.float64),
        'volume': clean_df['volume'].values.astype(np.float64),
        'symbol': symbol,
        'interval': interval
    }
    
    if mat_filename is None:
        mat_filename = f"{output_dir}/{symbol}_{interval}.mat"
    else:
        mat_filename = os.path.join(output_dir, mat_filename)
    
    sio.savemat(mat_filename, mat_data)
    print(f"导出MAT格式: {mat_filename}")
    
    # 同时保存CSV备用
    csv_filename = f"{output_dir}/{symbol}_{interval}.csv"
    clean_df.to_csv(csv_filename, index=False)
    print(f"导出CSV: {csv_filename}")
    
    return mat_filename


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='NEMT数据获取工具')
    parser.add_argument('symbol', nargs='?', default='BTC', help='交易对 (默认: BTC)')
    parser.add_argument('-i', '--interval', default='1h', help='周期 (默认: 1h)')
    parser.add_argument('-s', '--start', default=None, help='开始日期 YYYY-MM-DD')
    parser.add_argument('-e', '--end', default=None, help='结束日期 YYYY-MM-DD')
    parser.add_argument('-d', '--days', type=int, default=None, help='天数 (会覆盖日期参数)')

    args = parser.parse_args()

    print(f"获取 {args.symbol} 数据...")
    print(f"周期: {args.interval}")

    data = fetch_by_range(
        symbols=[args.symbol],
        interval=args.interval,
        start_date=args.start,
        end_date=args.end,
        days=args.days
    )

    if data:
        print(f"\n数据已保存到 matlab_data 目录")
        print("在MATLAB中运行: NEMTAnalyzer.run()")
