"""
NEMT Quant OS 主入口
Next Evolution Market Trading System
"""

import argparse
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from nemt.backtest import run_backtest
from nemt.config.settings import create_default_config


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="NEMT Quant OS - 量化交易系统")

    parser.add_argument(
        "--data",
        type=str,
        default="matlab_data/BTC_1h.csv",
        help="数据文件路径"
    )

    parser.add_argument(
        "--capital",
        type=float,
        default=10000.0,
        help="初始资金"
    )

    parser.add_argument(
        "--start",
        type=str,
        default=None,
        help="开始日期 (YYYY-MM-DD)"
    )

    parser.add_argument(
        "--end",
        type=str,
        default=None,
        help="结束日期 (YYYY-MM-DD)"
    )

    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="配置文件路径"
    )

    parser.add_argument(
        "--init-config",
        action="store_true",
        help="创建默认配置文件"
    )

    args = parser.parse_args()

    # 初始化配置
    if args.init_config:
        config_path = "config/config.yaml"
        create_default_config(config_path)
        print(f"默认配置已创建: {config_path}")
        return

    # 运行回测
    print("\n" + "=" * 60)
    print("NEMT Quant OS - 量化交易系统")
    print("=" * 60)

    try:
        results = run_backtest(
            data_path=args.data,
            initial_capital=args.capital,
            start_date=args.start,
            end_date=args.end,
            config_path=args.config
        )

        print("\n" + "=" * 60)
        print("最终结果汇总")
        print("=" * 60)
        print(f"初始资金:    ${results['initial_capital']:,.2f}")
        print(f"最终权益:    ${results['final_equity']:,.2f}")
        print(f"总盈亏:      ${results['total_pnl']:,.2f}")
        print(f"收益率:      {results['return_pct']:.2f}%")
        print(f"最大回撤:    {results['max_drawdown']:.2f}%")
        print(f"夏普比率:    {results['sharpe_ratio']:.2f}")
        print(f"胜率:        {results['win_rate']:.1f}%")
        print(f"盈亏比:      {results['profit_factor']:.2f}")
        print(f"总交易次数:  {results['total_trades']}")
        print("=" * 60)

    except FileNotFoundError as e:
        print(f"\n错误: 数据文件未找到 - {e}")
        print(f"请确保数据文件存在: {args.data}")
        sys.exit(1)
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
