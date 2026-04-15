"""
NEMT 2026年比特币数据收集脚本
收集并保存为MATLAB兼容格式

使用方法:
    python collect_2026_data.py          # 收集所有周期
    python collect_2026_data.py --1h     # 仅收集1小时数据
    python collect_2026_data.py --list   # 查看已收集的数据
"""

import argparse
import os
import sys
import time
from datetime import datetime

import numpy as np
import pandas as pd

# 确保导入本地模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from binance_fetcher import BinanceFetcher


class NEMTDataCollector:
    """NEMT专用数据收集器"""
    
    # 数据分组定义
    DATA_GROUPS = {
        'short': {
            'intervals': ['5m', '15m'],
            'description': '短期分析数据'
        },
        'medium': {
            'intervals': ['1h', '4h', '1d'],
            'description': '中期分析数据（核心）'
        },
        'long': {
            'intervals': ['1w', '1M'],
            'description': '长期分析数据'
        },
        'all': {
            'intervals': ['5m', '15m', '1h', '4h', '1d', '1w', '1M'],
            'description': '全部数据'
        }
    }
    
    def __init__(self, output_dir: str = 'matlab_data/2026'):
        self.output_dir = output_dir
        self.fetcher = BinanceFetcher()
        os.makedirs(output_dir, exist_ok=True)
    
    def collect_interval(
        self, 
        interval: str, 
        start_date: str, 
        end_date: str,
        save_mat: bool = True
    ) -> pd.DataFrame:
        """
        收集单个周期的数据
        
        Args:
            interval: K线周期
            start_date: 开始日期
            end_date: 结束日期
            save_mat: 是否保存MATLAB格式
            
        Returns:
            DataFrame或None
        """
        print(f"\n正在获取 {interval} 数据...")
        
        try:
            df = self.fetcher.fetch_range(
                symbol='BTCUSDT',
                interval=interval,
                start_date=start_date,
                end_date=end_date
            )
            
            if df.empty:
                print(f"  获取失败，返回空数据")
                return None
            
            # 清理和整理数据
            clean_df = df[[
                'open_time', 'open', 'high', 'low', 'close', 
                'volume', 'quote_volume', 'trades',
                'taker_buy_base', 'taker_buy_quote'
            ]].copy()
            
            # 保存CSV
            csv_file = f"{self.output_dir}/BTC_{interval}_2026.csv"
            clean_df.to_csv(csv_file, index=False)
            print(f"  CSV已保存: {csv_file} ({len(clean_df)}条)")
            
            # 保存MATLAB格式
            if save_mat:
                try:
                    mat_file = f"{self.output_dir}/BTC_{interval}_2026.mat"
                    self._save_mat(clean_df, mat_file, interval)
                    print(f"  MAT已保存: {mat_file}")
                except ImportError:
                    print("  警告: scipy未安装，仅保存CSV")
            
            return clean_df
            
        except Exception as e:
            print(f"  错误: {e}")
            return None
    
    def _save_mat(
        self, 
        df: pd.DataFrame, 
        filepath: str, 
        interval: str
    ):
        """保存为MATLAB格式"""
        import scipy.io as sio
        
        mat_data = {
            # 基本OHLCV
            'timestamp': df['open_time'].values,
            'open': df['open'].values.astype(np.float64),
            'high': df['high'].values.astype(np.float64),
            'low': df['low'].values.astype(np.float64),
            'close': df['close'].values.astype(np.float64),
            'volume': df['volume'].values.astype(np.float64),
            
            # 扩展数据
            'quote_volume': df['quote_volume'].values.astype(np.float64),
            'trades': df['trades'].values.astype(np.float64),
            'taker_buy_base': df['taker_buy_base'].values.astype(np.float64),
            'taker_buy_quote': df['taker_buy_quote'].values.astype(np.float64),
            
            # 元数据
            'symbol': 'BTCUSDT',
            'interval': interval,
            'start_date': df['open_time'].min(),
            'end_date': df['open_time'].max()
        }
        
        sio.savemat(filepath, mat_data)
    
    def collect_group(
        self, 
        group: str, 
        start_date: str, 
        end_date: str
    ) -> dict:
        """
        收集一组数据
        
        Args:
            group: 'short', 'medium', 'long', 'all'
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            {interval: DataFrame} 字典
        """
        if group not in self.DATA_GROUPS:
            raise ValueError(f"未知分组: {group}")
        
        intervals = self.DATA_GROUPS[group]['intervals']
        print(f"\n收集分组 '{group}': {intervals}")
        
        results = {}
        
        for interval in intervals:
            df = self.collect_interval(interval, start_date, end_date)
            if df is not None:
                results[interval] = df
            
            time.sleep(0.5)  # 避免API限流
        
        return results
    
    def list_collected(self) -> list:
        """列出已收集的数据文件"""
        files = []
        
        for f in os.listdir(self.output_dir):
            if f.startswith('BTC_') and f.endswith('.csv'):
                interval = f.split('_')[1]
                filepath = os.path.join(self.output_dir, f)
                size = os.path.getsize(filepath)
                files.append({
                    'interval': interval,
                    'file': f,
                    'size': size,
                    'path': filepath
                })
        
        return sorted(files, key=lambda x: x['interval'])
    
    def validate_data(self, interval: str) -> dict:
        """验证已收集的数据"""
        csv_file = f"{self.output_dir}/BTC_{interval}_2026.csv"
        
        if not os.path.exists(csv_file):
            return {'valid': False, 'error': '文件不存在'}
        
        try:
            df = pd.read_csv(csv_file, parse_dates=['open_time'])
            
            issues = []
            
            # 检查缺失值
            if df.isnull().any().any():
                issues.append("存在缺失值")
            
            # 检查价格关系
            invalid_price = (df['close'] > df['high']) | (df['close'] < df['low'])
            if invalid_price.any():
                issues.append("收盘价超出范围")
            
            # 检查零值
            zero_volume = (df['volume'] <= 0).sum()
            if zero_volume > 0:
                issues.append(f"零成交量: {zero_volume}条")
            
            return {
                'valid': len(issues) == 0,
                'issues': issues,
                'rows': len(df),
                'date_range': (df['open_time'].min(), df['open_time'].max())
            }
            
        except Exception as e:
            return {'valid': False, 'error': str(e)}


def main():
    parser = argparse.ArgumentParser(
        description='NEMT 2026年BTC数据收集工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python collect_2026_data.py --all           # 收集全部数据
  python collect_2026_data.py --short         # 仅收集短期数据
  python collect_2026_data.py --1h            # 仅收集1小时数据
  python collect_2026_data.py --list           # 查看已收集数据
  python collect_2026_data.py --validate 1h  # 验证1h数据

分组说明:
  --short   5m, 15m - 短期波动分析
  --medium  1h, 4h, 1d - 中期策略分析（推荐）
  --long    1w, 1M - 长期趋势分析
  --all     所有周期
        """
    )
    
    # 分组参数
    parser.add_argument('--all', action='store_true', help='收集全部周期数据')
    parser.add_argument('--short', action='store_true', help='收集短期数据 (5m, 15m)')
    parser.add_argument('--medium', action='store_true', help='收集中期数据 (1h, 4h, 1d)')
    parser.add_argument('--long', action='store_true', help='收集长期数据 (1w, 1M)')
    
    # 单周期参数
    parser.add_argument('--1m', action='store_true', help='仅收集1分钟数据')
    parser.add_argument('--5m', action='store_true', help='仅收集5分钟数据')
    parser.add_argument('--15m', action='store_true', help='仅收集15分钟数据')
    parser.add_argument('--1h', action='store_true', help='仅收集1小时数据')
    parser.add_argument('--4h', action='store_true', help='仅收集4小时数据')
    parser.add_argument('--1d', action='store_true', help='仅收集日线数据')
    parser.add_argument('--1w', action='store_true', help='仅收集周线数据')
    parser.add_argument('--1M', action='store_true', help='仅收集月线数据')
    
    # 其他操作
    parser.add_argument('--list', action='store_true', help='列出已收集的数据')
    parser.add_argument('--validate', metavar='INTERVAL', help='验证指定周期数据')
    
    # 日期参数
    parser.add_argument('--start', default='2026-01-01', help='开始日期 (YYYY-MM-DD)')
    parser.add_argument('--end', default='2026-04-15', help='结束日期 (YYYY-MM-DD)')
    
    # 输出目录
    parser.add_argument('--output', default='matlab_data/2026', help='输出目录')
    
    args = parser.parse_args()
    
    collector = NEMTDataCollector(output_dir=args.output)
    
    # 列出已收集数据
    if args.list:
        print("\n已收集的数据文件:")
        print("-" * 50)
        files = collector.list_collected()
        
        if not files:
            print("暂无数据文件")
        else:
            for f in files:
                size_mb = f['size'] / 1024 / 1024
                print(f"  {f['interval']:4s}  {f['file']}  ({size_mb:.2f} MB)")
        
        print()
        return
    
    # 验证数据
    if args.validate:
        print(f"\n验证 {args.validate} 数据...")
        result = collector.validate_data(args.validate)
        
        if result['valid']:
            print("  ✓ 数据有效")
            print(f"  数据点数: {result['rows']}")
            print(f"  时间范围: {result['date_range'][0]} ~ {result['date_range'][1]}")
        else:
            print("  ✗ 数据无效")
            if 'issues' in result:
                for issue in result['issues']:
                    print(f"    - {issue}")
            else:
                print(f"    {result.get('error', '未知错误')}")
        return
    
    # 确定要收集的周期
    intervals_to_collect = []
    
    if args.all:
        intervals_to_collect = collector.DATA_GROUPS['all']['intervals']
    elif args.short:
        intervals_to_collect = collector.DATA_GROUPS['short']['intervals']
    elif args.medium:
        intervals_to_collect = collector.DATA_GROUPS['medium']['intervals']
    elif args.long:
        intervals_to_collect = collector.DATA_GROUPS['long']['intervals']
    else:
        # 检查单周期参数
        single_intervals = {
            '1m': args.__dict__.get('1m'),
            '5m': args.__dict__.get('5m'),
            '15m': args.__dict__.get('15m'),
            '1h': args.__dict__.get('1h'),
            '4h': args.__dict__.get('4h'),
            '1d': args.__dict__.get('1d'),
            '1w': args.__dict__.get('1w'),
            '1M': args.__dict__.get('1M'),
        }
        
        for interval, enabled in single_intervals.items():
            if enabled:
                intervals_to_collect.append(interval)
    
    if not intervals_to_collect:
        parser.print_help()
        print("\n提示: 使用 --medium 参数收集推荐的分析数据")
        return
    
    # 开始收集
    print("\n" + "=" * 60)
    print("NEMT 2026年BTC数据收集")
    print("=" * 60)
    print(f"时间范围: {args.start} ~ {args.end}")
    print(f"输出目录: {args.output}")
    print(f"收集周期: {intervals_to_collect}")
    
    results = {}
    
    for interval in intervals_to_collect:
        df = collector.collect_interval(interval, args.start, args.end)
        if df is not None:
            results[interval] = df
        time.sleep(0.5)
    
    # 生成摘要
    print("\n" + "=" * 60)
    print("收集完成摘要")
    print("=" * 60)
    
    summary_file = f"{args.output}/collection_summary.txt"
    
    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write(f"NEMT 2026年BTC数据收集摘要\n")
        f.write(f"收集时间: {datetime.now()}\n")
        f.write(f"数据范围: {args.start} ~ {args.end}\n")
        f.write("=" * 50 + "\n\n")
        
        for interval, df in results.items():
            f.write(f"[{interval}]\n")
            f.write(f"  数据点数: {len(df)}\n")
            f.write(f"  时间范围: {df['open_time'].min()} ~ {df['open_time'].max()}\n")
            f.write(f"  价格范围: {df['low'].min():.2f} ~ {df['high'].max():.2f}\n")
            f.write(f"  总成交量: {df['volume'].sum():,.0f}\n\n")
    
    print(f"\n摘要已保存: {summary_file}")
    print("\n下一步:")
    print("  1. 在MATLAB中运行: NEMT_Launcher")
    print("  2. 或在Python中运行: python main.py --demo")


if __name__ == "__main__":
    main()
