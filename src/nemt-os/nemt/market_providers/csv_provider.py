"""
CSV 文件市场数据提供者 (CSV File Market Provider)
支持本地CSV文件 + 文件监视实时更新
"""

import os
import csv
import time
import threading
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any, Callable
from dataclasses import dataclass

from .base import BaseMarketProvider, MarketData, KLine


@dataclass
class CSVConfig:
    """CSV配置文件"""

    filepath: str
    timestamp_col: str = "timestamp"
    open_col: str = "open"
    high_col: str = "high"
    low_col: str = "low"
    close_col: str = "close"
    volume_col: str = "volume"
    symbol_col: Optional[str] = None  # 可选，如CSV中有symbol列
    default_symbol: str = "DEFAULT"
    datetime_format: Optional[str] = None  # 如 "%Y-%m-%d %H:%M:%S"


class CSVFileProvider(BaseMarketProvider):
    """
    CSV 文件市场数据提供者

    功能:
    - 加载历史CSV数据
    - 支持多种CSV格式
    - 文件监视自动更新
    - 实时增量读取

    CSV格式要求:
    - 必须包含: timestamp/open/high/low/close/volume (或自定义列名)
    - timestamp 支持: Unix时间戳, ISO格式日期, 自定义格式
    """

    def __init__(
        self,
        name: str = "CSVProvider",
        config: Optional[CSVConfig] = None,
        auto_watch: bool = False,
        watch_interval: float = 1.0,
    ):
        """
        Args:
            name: 提供者名称
            config: CSV配置
            auto_watch: 是否自动监视文件变化
            watch_interval: 文件检查间隔(秒)
        """
        super().__init__(name)
        self._config = config
        self._auto_watch = auto_watch
        self._watch_interval = watch_interval

        # 数据存储
        self._klines: List[KLine] = []
        self._ticker_data: Optional[MarketData] = None

        # 文件监视
        self._watch_thread: Optional[threading.Thread] = None
        self._watch_running = False
        self._last_file_mtime: Optional[float] = None
        self._last_file_size: int = 0
        self._last_read_line: int = 0

        # 回调
        self._on_new_bar: Optional[Callable[[KLine], None]] = None

    def connect(self) -> bool:
        """
        连接CSV数据源

        Returns:
            bool: 连接是否成功
        """
        if self._config is None:
            print(f"[{self.name}] No CSV config provided")
            return False

        if not os.path.exists(self._config.filepath):
            print(f"[{self.name}] File not found: {self._config.filepath}")
            return False

        self._is_connected = True

        # 加载初始数据
        self._load_csv()

        # 启动文件监视
        if self._auto_watch:
            self._start_watching()

        print(f"[{self.name}] Connected to {self._config.filepath}")
        print(f"[{self.name}] Loaded {len(self._klines)} klines")

        return True

    def disconnect(self) -> None:
        """断开CSV数据源"""
        self._stop_watching()
        self._is_connected = False
        self._klines.clear()
        print(f"[{self.name}] Disconnected")

    def _load_csv(self) -> int:
        """
        加载CSV文件

        Returns:
            加载的数据条数
        """
        if self._config is None:
            return 0

        filepath = self._config.filepath

        # 获取文件信息
        stat = os.stat(filepath)
        self._last_file_mtime = stat.st_mtime
        self._last_file_size = stat.st_size

        # 清空旧数据
        self._klines.clear()

        klines = []
        line_count = 0

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)

                for row in reader:
                    kline = self._parse_row(row)
                    if kline:
                        klines.append(kline)
                    line_count += 1

                self._last_read_line = line_count

        except Exception as e:
            print(f"[{self.name}] Error loading CSV: {e}")
            return 0

        self._klines = klines
        return len(klines)

    def _parse_row(self, row: Dict[str, str]) -> Optional[KLine]:
        """解析CSV行"""
        if self._config is None:
            return None

        cfg = self._config

        try:
            # 解析时间戳
            ts_str = row.get(cfg.timestamp_col, "")
            timestamp = self._parse_timestamp(ts_str)

            # 解析价格数据
            open_price = float(row.get(cfg.open_col, 0))
            high_price = float(row.get(cfg.high_col, 0))
            low_price = float(row.get(cfg.low_col, 0))
            close_price = float(row.get(cfg.close_col, 0))
            volume = float(row.get(cfg.volume_col, 0))

            # 解析交易对
            symbol = row.get(cfg.symbol_col, cfg.default_symbol) if cfg.symbol_col else cfg.default_symbol

            return KLine(
                timestamp=timestamp,
                open=open_price,
                high=high_price,
                low=low_price,
                close=close_price,
                volume=volume,
                symbol=symbol,
                interval="1h",  # CSV不包含周期信息，使用默认值
            )

        except (ValueError, KeyError) as e:
            return None

    def _parse_timestamp(self, ts_str: str) -> datetime:
        """解析时间戳字符串"""
        if self._config is None:
            return datetime.now()

        cfg = self._config

        # 尝试多种格式
        # 1. Unix时间戳 (整数或浮点数)
        try:
            if ts_str.replace(".", "").isdigit():
                ts = float(ts_str)
                if ts > 1e12:  # 毫秒
                    ts /= 1000
                return datetime.fromtimestamp(ts)
        except (ValueError, OSError):
            pass

        # 2. ISO格式
        try:
            return datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
        except ValueError:
            pass

        # 3. 自定义格式
        if cfg.datetime_format:
            try:
                return datetime.strptime(ts_str, cfg.datetime_format)
            except ValueError:
                pass

        # 4. 常见格式尝试
        common_formats = [
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d %H:%M:%S.%f",
            "%Y-%m-%d",
            "%Y/%m/%d %H:%M:%S",
            "%d/%m/%Y %H:%M:%S",
            "%m/%d/%Y %H:%M:%S",
        ]

        for fmt in common_formats:
            try:
                return datetime.strptime(ts_str, fmt)
            except ValueError:
                continue

        return datetime.now()

    def _start_watching(self) -> None:
        """启动文件监视"""
        if self._watch_thread and self._watch_thread.is_alive():
            return

        self._watch_running = True

        def watch_loop():
            while self._watch_running:
                try:
                    self._check_file_changes()
                except Exception as e:
                    pass
                time.sleep(self._watch_interval)

        self._watch_thread = threading.Thread(target=watch_loop, daemon=True)
        self._watch_thread.start()

        print(f"[{self.name}] File watching started")

    def _stop_watching(self) -> None:
        """停止文件监视"""
        self._watch_running = False

        if self._watch_thread and self._watch_thread.is_alive():
            self._watch_thread.join(timeout=2)

    def _check_file_changes(self) -> None:
        """检查文件变化"""
        if self._config is None:
            return

        filepath = self._config.filepath

        if not os.path.exists(filepath):
            return

        stat = os.stat(filepath)

        # 检查文件大小或修改时间变化
        if stat.st_size != self._last_file_size or stat.st_mtime != self._last_file_mtime:
            self._read_new_lines()

            self._last_file_mtime = stat.st_mtime
            self._last_file_size = stat.st_size

    def _read_new_lines(self) -> None:
        """读取新增的行"""
        if self._config is None:
            return

        filepath = self._config.filepath
        new_klines = []

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)

                # 跳到上次读取的位置
                for _ in range(self._last_read_line):
                    next(reader, None)

                current_line = self._last_read_line

                for row in reader:
                    kline = self._parse_row(row)
                    if kline:
                        new_klines.append(kline)
                    current_line += 1

                self._last_read_line = current_line

        except Exception as e:
            print(f"[{self.name}] Error reading new lines: {e}")
            return

        # 添加新数据
        if new_klines:
            self._klines.extend(new_klines)

            # 触发回调
            for kline in new_klines:
                self._notify_subscribers(kline.symbol, kline)

                if self._on_new_bar:
                    self._on_new_bar(kline)

            print(f"[{self.name}] Added {len(new_klines)} new klines")

    def get_latest(self, symbol: Optional[str] = None, interval: str = "1h") -> Optional[KLine]:
        """
        获取最新K线

        Args:
            symbol: 交易对 (忽略，使用CSV中的数据)
            interval: K线周期

        Returns:
            最新K线
        """
        if not self._is_connected or not self._klines:
            return None

        return self._klines[-1]

    def get_history(
        self,
        symbol: Optional[str] = None,
        interval: str = "1h",
        limit: int = 100,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> List[KLine]:
        """
        获取历史K线

        Args:
            symbol: 交易对 (忽略，使用CSV中的数据)
            interval: K线周期
            limit: 获取数量上限
            start_time: 开始时间
            end_time: 结束时间

        Returns:
            K线数据列表
        """
        if not self._is_connected:
            return []

        klines = self._klines.copy()

        # 按时间过滤
        if start_time:
            klines = [k for k in klines if k.timestamp >= start_time]
        if end_time:
            klines = [k for k in klines if k.timestamp <= end_time]

        # 限制数量
        if limit > 0 and len(klines) > limit:
            klines = klines[-limit:]

        return klines

    def get_ticker(self, symbol: Optional[str] = None) -> Optional[MarketData]:
        """
        获取最新行情

        Args:
            symbol: 交易对

        Returns:
            市场数据
        """
        if not self._is_connected or not self._klines:
            return None

        latest = self._klines[-1]

        if self._ticker_data is None:
            self._ticker_data = MarketData(
                symbol=latest.symbol,
                price=latest.close,
                bid=latest.close * 0.9999,
                ask=latest.close * 1.0001,
                volume=latest.volume,
                timestamp=latest.timestamp,
            )
        else:
            # 更新
            self._ticker_data.price = latest.close
            self._ticker_data.timestamp = latest.timestamp
            self._ticker_data.bid = latest.close * 0.9999
            self._ticker_data.ask = latest.close * 1.0001

        return self._ticker_data

    def reload(self) -> int:
        """
        重新加载CSV文件

        Returns:
            加载的数据条数
        """
        self._last_read_line = 0
        return self._load_csv()

    def set_on_new_bar(self, callback: Callable[[KLine], None]) -> None:
        """设置新K线回调"""
        self._on_new_bar = callback

    def get_dataframe(self):
        """获取Pandas DataFrame"""
        import pandas as pd

        if not self._klines:
            return pd.DataFrame()

        df = pd.DataFrame([k.to_dict() for k in self._klines])
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        return df

    def save_to_csv(self, filepath: str) -> bool:
        """
        保存数据到CSV

        Args:
            filepath: 保存路径

        Returns:
            是否成功
        """
        if not self._klines:
            return False

        try:
            import pandas as pd

            df = self.get_dataframe()
            df.to_csv(filepath, index=False)
            print(f"[{self.name}] Saved {len(self._klines)} klines to {filepath}")
            return True
        except Exception as e:
            print(f"[{self.name}] Save failed: {e}")
            return False

    def get_status(self) -> Dict[str, Any]:
        """获取提供者状态"""
        status = super().get_status()
        status.update(
            {
                "filepath": self._config.filepath if self._config else None,
                "kline_count": len(self._klines),
                "watching": self._watch_running,
                "last_line": self._last_read_line,
            }
        )
        return status


# 便捷函数
def load_csv_data(
    filepath: str,
    timestamp_col: str = "timestamp",
    open_col: str = "open",
    high_col: str = "high",
    low_col: str = "low",
    close_col: str = "close",
    volume_col: str = "volume",
    symbol: str = "DEFAULT",
    datetime_format: Optional[str] = None,
) -> List[KLine]:
    """
    便捷函数：加载CSV数据

    Args:
        filepath: CSV文件路径
        其他列名配置...

    Returns:
        K线数据列表
    """
    config = CSVConfig(
        filepath=filepath,
        timestamp_col=timestamp_col,
        open_col=open_col,
        high_col=high_col,
        low_col=low_col,
        close_col=close_col,
        volume_col=volume_col,
        default_symbol=symbol,
        datetime_format=datetime_format,
    )

    provider = CSVFileProvider(config=config)
    provider.connect()
    klines = provider.get_history()
    provider.disconnect()

    return klines


def create_csv_provider(
    filepath: str, symbol: str = "DEFAULT", auto_watch: bool = False, datetime_format: Optional[str] = None
) -> CSVFileProvider:
    """
    便捷函数：创建CSV提供者

    Args:
        filepath: CSV文件路径
        symbol: 交易对名称
        auto_watch: 是否监视文件变化
        datetime_format: 日期时间格式

    Returns:
        CSVFileProvider 实例
    """
    config = CSVConfig(filepath=filepath, default_symbol=symbol, datetime_format=datetime_format)

    provider = CSVFileProvider(config=config, auto_watch=auto_watch)

    return provider
