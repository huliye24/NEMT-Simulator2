#!/usr/bin/env python3
"""
US Stock Data Fetcher - 美股数据下载脚本

从Yahoo Finance爬取美股历史数据并保存为CSV格式

Usage:
    python scripts/fetch_us_stocks.py --symbols AAPL MSFT GOOGL --days 365
    python scripts/fetch_us_stocks.py --all-popular --days 1825
    python scripts/fetch_us_stocks.py --symbol-file symbols.txt --output ./data
"""

import argparse
import logging
import sys
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
import time

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from backtest.data.loaders.us_stock_loader import USStockLoader

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


@dataclass
class FetchResult:
    """下载结果"""
    symbol: str
    success: bool
    record_count: int
    start_date: str
    end_date: str
    file_path: str
    error: Optional[str] = None
    duration_ms: float = 0.0


@dataclass
class Metadata:
    """数据元信息"""
    fetch_time: str
    total_symbols: int
    success_count: int
    failed_count: int
    results: List[Dict]
    stock_info: Dict[str, Dict]


class USStockFetcher:
    """美股数据下载器"""

    # 默认股票池
    DEFAULT_SYMBOLS = [
        # 科技巨头
        "AAPL", "MSFT", "GOOGL", "AMZN", "META", "NVDA", "TSLA",
        # 金融
        "JPM", "BAC", "WFC", "GS", "MS",
        # 消费
        "WMT", "PG", "KO", "PEP", "COST",
        # 医疗
        "JNJ", "UNH", "PFE", "ABBV", "LLY",
        # 工业
        "BA", "CAT", "GE", "HON",
        # 能源
        "XOM", "CVX", "COP",
        # 指数ETF
        "SPY", "QQQ", "IWM", "DIA",
        # 热门中概股
        "BABA", "JD", "PDD", "BIDU",
    ]

    def __init__(
        self,
        output_dir: str = "./data/us_stocks/daily",
        days: int = 1825,  # 5年数据
        timeframe: str = "1d",
        rate_limit: float = 2.0,
    ):
        """
        初始化下载器

        Args:
            output_dir: 输出目录
            days: 历史数据天数
            timeframe: 时间周期
            rate_limit: API速率限制
        """
        self.output_dir = Path(output_dir)
        self.days = days
        self.timeframe = timeframe
        self.loader = USStockLoader(rate_limit=rate_limit)

        # 计算日期范围
        self.end_date = datetime.now()
        self.start_date = self.end_date - timedelta(days=days)

    def fetch_single(
        self,
        symbol: str,
        show_progress: bool = True,
    ) -> FetchResult:
        """
        下载单只股票数据

        Args:
            symbol: 股票代码
            show_progress: 是否显示进度

        Returns:
            FetchResult
        """
        start_time = time.time()

        try:
            # 获取数据
            result = self.loader.load(
                symbol=symbol,
                timeframe=self.timeframe,
                start_date=self.start_date,
                end_date=self.end_date,
            )

            if not result.success:
                return FetchResult(
                    symbol=symbol,
                    success=False,
                    record_count=0,
                    start_date=self.start_date.strftime("%Y-%m-%d"),
                    end_date=self.end_date.strftime("%Y-%m-%d"),
                    file_path="",
                    error=result.error,
                    duration_ms=(time.time() - start_time) * 1000,
                )

            # 保存到CSV
            self.output_dir.mkdir(parents=True, exist_ok=True)
            file_path = self.output_dir / f"{symbol}_daily.csv"
            self._save_to_csv(result.data.data, file_path)

            if show_progress:
                logger.info(f"[OK] {symbol}: {result.record_count} records -> {file_path}")

            return FetchResult(
                symbol=symbol,
                success=True,
                record_count=result.record_count,
                start_date=self.start_date.strftime("%Y-%m-%d"),
                end_date=self.end_date.strftime("%Y-%m-%d"),
                file_path=str(file_path),
                duration_ms=(time.time() - start_time) * 1000,
            )

        except Exception as e:
            logger.error(f"[FAIL] {symbol}: {e}")
            return FetchResult(
                symbol=symbol,
                success=False,
                record_count=0,
                start_date=self.start_date.strftime("%Y-%m-%d"),
                end_date=self.end_date.strftime("%Y-%m-%d"),
                file_path="",
                error=str(e),
                duration_ms=(time.time() - start_time) * 1000,
            )

    def fetch_batch(
        self,
        symbols: List[str],
        show_progress: bool = True,
    ) -> List[FetchResult]:
        """
        批量下载

        Args:
            symbols: 股票代码列表
            show_progress: 是否显示进度

        Returns:
            下载结果列表
        """
        results = []
        total = len(symbols)

        logger.info(f"Starting batch fetch: {total} symbols")
        logger.info(f"Date range: {self.start_date.date()} to {self.end_date.date()}")
        logger.info(f"Output directory: {self.output_dir}")
        logger.info("-" * 60)

        for idx, symbol in enumerate(symbols, 1):
            if show_progress:
                print(f"[{idx}/{total}] ", end="", flush=True)

            result = self.fetch_single(symbol, show_progress=False)
            results.append(result)

            # 速率限制
            if idx < total:
                time.sleep(0.5)

        return results

    def fetch_all_popular(self, show_progress: bool = True) -> List[FetchResult]:
        """下载所有推荐股票"""
        return self.fetch_batch(self.DEFAULT_SYMBOLS, show_progress)

    def _save_to_csv(self, data: List, file_path: Path):
        """保存数据到CSV"""
        import pandas as pd

        records = []
        for ohlcv in data:
            records.append({
                'timestamp': ohlcv.timestamp.strftime('%Y-%m-%d'),
                'symbol': ohlcv.symbol,
                'open': ohlcv.open,
                'high': ohlcv.high,
                'low': ohlcv.low,
                'close': ohlcv.close,
                'volume': ohlcv.volume,
                'quote_volume': ohlcv.quote_volume,
                'source': ohlcv.source,
            })

        df = pd.DataFrame(records)
        df.to_csv(file_path, index=False)

    def generate_metadata(self, results: List[FetchResult]) -> Metadata:
        """生成元数据"""
        # 获取股票信息
        stock_info = {}
        for result in results:
            if result.success:
                info = self.loader.get_info(result.symbol)
                stock_info[result.symbol] = info
                time.sleep(0.3)  # 避免限流

        return Metadata(
            fetch_time=datetime.now().isoformat(),
            total_symbols=len(results),
            success_count=sum(1 for r in results if r.success),
            failed_count=sum(1 for r in results if not r.success),
            results=[asdict(r) for r in results],
            stock_info=stock_info,
        )

    def save_metadata(self, metadata: Metadata, output_path: Optional[Path] = None):
        """保存元数据"""
        if output_path is None:
            output_path = self.output_dir / "metadata.json"

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(asdict(metadata), f, indent=2, ensure_ascii=False)

        logger.info(f"Metadata saved to: {output_path}")

    def print_summary(self, results: List[FetchResult]):
        """打印摘要"""
        success = [r for r in results if r.success]
        failed = [r for r in results if not r.success]

        total_records = sum(r.record_count for r in success)
        total_time = sum(r.duration_ms for r in results)

        print("\n" + "=" * 60)
        print("FETCH SUMMARY")
        print("=" * 60)
        print(f"Total symbols: {len(results)}")
        print(f"Success: {len(success)}")
        print(f"Failed: {len(failed)}")
        print(f"Total records: {total_records:,}")
        print(f"Total time: {total_time/1000:.1f}s")
        print("=" * 60)

        if failed:
            print("\nFailed symbols:")
            for r in failed:
                print(f"  - {r.symbol}: {r.error}")


def load_symbols_from_file(file_path: str) -> List[str]:
    """从文件加载股票代码"""
    with open(file_path, 'r') as f:
        return [line.strip() for line in f if line.strip() and not line.startswith('#')]


def main():
    parser = argparse.ArgumentParser(
        description='US Stock Data Fetcher - 从Yahoo Finance下载美股历史数据',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # 下载单只股票
  python fetch_us_stocks.py --symbols AAPL

  # 下载多只股票
  python fetch_us_stocks.py --symbols AAPL MSFT GOOGL

  # 下载所有推荐股票
  python fetch_us_stocks.py --all-popular

  # 指定日期范围
  python fetch_us_stocks.py --symbols AAPL --days 3650 --start 2015-01-01

  # 从文件加载股票列表
  python fetch_us_stocks.py --symbol-file symbols.txt --output ./data
        """
    )

    # 基本参数
    parser.add_argument('--symbols', nargs='+', help='股票代码列表')
    parser.add_argument('--symbol-file', type=str, help='股票代码文件路径')
    parser.add_argument('--all-popular', action='store_true', help='下载所有推荐股票')

    # 时间和输出
    parser.add_argument('--days', type=int, default=1825, help='历史数据天数 (默认: 1825 = 5年)')
    parser.add_argument('--start', type=str, help='开始日期 (YYYY-MM-DD)')
    parser.add_argument('--end', type=str, help='结束日期 (YYYY-MM-DD)')
    parser.add_argument('--timeframe', type=str, default='1d', choices=['1d', '1w', '1M'],
                        help='时间周期 (默认: 1d)')
    parser.add_argument('--output', type=str, default='./data/us_stocks/daily',
                        help='输出目录 (默认: ./data/us_stocks/daily)')

    # 其他选项
    parser.add_argument('--rate-limit', type=float, default=2.0,
                        help='API速率限制 (请求/秒, 默认: 2.0)')
    parser.add_argument('--quiet', action='store_true', help='静默模式')
    parser.add_argument('--save-metadata', action='store_true', help='保存元数据')

    args = parser.parse_args()

    # 确定要下载的股票
    symbols = []
    if args.symbols:
        symbols = args.symbols
    elif args.symbol_file:
        symbols = load_symbols_from_file(args.symbol_file)
    elif args.all_popular:
        symbols = USStockFetcher.DEFAULT_SYMBOLS
    else:
        parser.print_help()
        print("\nError: 必须指定 --symbols, --symbol-file 或 --all-popular")
        sys.exit(1)

    logger.setLevel(logging.WARNING if args.quiet else logging.INFO)

    # 创建下载器
    fetcher = USStockFetcher(
        output_dir=args.output,
        days=args.days,
        timeframe=args.timeframe,
        rate_limit=args.rate_limit,
    )

    # 自定义日期范围
    if args.start:
        from datetime import datetime
        fetcher.start_date = datetime.strptime(args.start, '%Y-%m-%d')
    if args.end:
        from datetime import datetime
        fetcher.end_date = datetime.strptime(args.end, '%Y-%m-%d')

    # 下载数据
    results = fetcher.fetch_batch(symbols, show_progress=not args.quiet)

    # 打印摘要
    fetcher.print_summary(results)

    # 保存元数据
    if args.save_metadata:
        metadata = fetcher.generate_metadata(results)
        fetcher.save_metadata(metadata)


if __name__ == '__main__':
    main()
