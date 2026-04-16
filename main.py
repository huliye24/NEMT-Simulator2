# Copyright 2026 NEMT Lab
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
NEMT Simulator V1
非平衡市场模拟器 (BTC实验版)

使用方法:
    python main.py              # 获取最新数据并运行
    python main.py --fetch      # 仅获取数据
    python main.py --demo       # 使用演示数据运行
"""

import argparse
import sys
import os
import numpy as np
from datetime import datetime

# 添加当前目录到Python路径
sys.path.insert(0, '.')

# 导入本地模块
from data_fetcher import fetch_btc_data, BinanceDataFetcher
from nemt_core import NEMTSimulator, NEMTParams
from visualizer import NEMTVisualizer
from experiments import (
    NoiseScanExperiment,
    NonlinearScanExperiment,
    ComparisonExperiment,
    run_all_experiments
)


def banner():
    """打印横幅"""
    print("=" * 70)
    print("""
    ██╗  ██╗██╗   ██╗███╗   ██╗ ██████╗ ███████╗██████╗
    ██║  ██║██║   ██║████╗  ██║██╔════╝ ██╔════╝██╔══██╗
    ███████║██║   ██║██╔██╗ ██║██║  ███╗█████╗  ██████╔╝
    ██╔══██║██║   ██║██║╚██╗██║██║   ██║██╔══╝  ██╔══██╗
    ██║  ██║╚██████╔╝██║ ╚████║╚██████╔╝███████╗██║  ██║
    ╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═══╝ ╚═════╝ ╚══════╝╚═╝  ╚═╝
    """)
    print("    Non-Equilibrium Market Theory Simulator V1")
    print("    非平衡市场模拟器 (BTC实验版)")
    print("=" * 70)
    print()


def load_data(csv_path: str = "btc_data.csv") -> np.ndarray:
    """加载CSV数据"""
    import pandas as pd
    df = pd.read_csv(csv_path)
    return df["close"].values


def run_basic_simulation(price_data: np.ndarray, params: NEMTParams = None):
    """运行基础模拟"""
    if params is None:
        params = NEMTParams()

    print("\n[1] 初始化模拟器...")
    sim = NEMTSimulator(params)

    print("[2] 初始化状态...")
    psi = sim.initialize_state(price_data)
    print(f"    数据点数: {len(psi)}")

    print("[3] 运行时间演化...")
    psi = sim.evolve(psi)
    print(f"    演化步数: {params.steps}")

    print("[4] 频谱分析...")
    freqs, spectrum = sim.spectral_analysis(psi)
    spec_width = sim.compute_spectral_width()
    resonance = sim.detect_resonance()

    print("\n" + "=" * 50)
    print("核心指标:")
    print(f"  谱宽 (Spectral Width): {spec_width:.6f}")
    print(f"  共振峰数量: {resonance['num_peaks']}")
    if len(resonance['peak_frequencies']) > 0:
        print(f"  共振频率: {resonance['peak_frequencies'][:5]}")
    print("=" * 50)

    return sim, {'freqs': freqs, 'spectrum': spectrum, 'psi': psi}


def generate_demo_data(n: int = 500) -> np.ndarray:
    """生成演示数据（模拟BTC价格波动）"""
    np.random.seed(42)
    t = np.linspace(0, 10, n)

    # 多频率成分（模拟市场周期）
    price = (
        2 * np.sin(0.5 * t) +
        1.5 * np.sin(1.3 * t + 0.3) +
        0.8 * np.sin(2.7 * t + 0.7) +
        0.3 * np.random.randn(n)  # 噪声
    )

    # 添加一些随机尖峰（模拟突发事件）
    spikes = np.random.choice(n, size=5, replace=False)
    price[spikes] += np.random.uniform(3, 5, 5) * np.sign(np.random.randn(5))

    return price


def main():
    banner()

    parser = argparse.ArgumentParser(description="NEMT Simulator V1")
    parser.add_argument('--fetch', action='store_true', help='仅获取数据')
    parser.add_argument('--demo', action='store_true', help='使用演示数据')
    parser.add_argument('--interval', type=str, default='1m', help='K线周期 (1m, 5m, 1h, 4h, 1d)')
    parser.add_argument('--limit', type=int, default=1000, help='数据条数')
    parser.add_argument('--output', type=str, default='output', help='输出目录')

    args = parser.parse_args()

    # 创建输出目录
    os.makedirs(args.output, exist_ok=True)

    # 获取数据
    if args.demo:
        print("使用演示数据...")
        price_data = generate_demo_data(1000)
    else:
        print(f"正在获取 BTCUSDT {args.interval} 数据...")
        df = fetch_btc_data(interval=args.interval, limit=args.limit,
                           csv_path="btc_data.csv", save_csv=True)

        if df.empty:
            print("获取数据失败，使用演示数据...")
            price_data = generate_demo_data(1000)
        else:
            price_data = df["close"].values

    if args.fetch:
        print("数据获取完成")
        return

    # 基础模拟
    print("\n" + "=" * 60)
    print("基础模拟")
    print("=" * 60)
    sim, analysis = run_basic_simulation(price_data)

    # 可视化
    print("\n生成可视化图表...")
    vis = NEMTVisualizer()

    # 1. 频谱图
    fig_spec = vis.plot_spectrum(analysis['spectrum'], analysis['freqs'])
    vis.save_figure(fig_spec, f"{args.output}/spectrum.png")

    # 2. 演化图
    if sim.psi_evolution is not None:
        fig_evo = vis.plot_evolution(sim.psi_evolution, dt=sim.params.dt)
        vis.save_figure(fig_evo, f"{args.output}/evolution.png")

    # 3. 共振分析
    resonance = sim.detect_resonance()
    fig_res = vis.plot_resonance_analysis(analysis['psi'], analysis['spectrum'],
                                         analysis['freqs'], resonance)
    vis.save_figure(fig_res, f"{args.output}/resonance.png")

    # 运行三个实验
    print("\n" + "=" * 60)
    print("运行三个核心实验")
    print("=" * 60)

    # 实验1: 噪声扫描
    exp1 = NoiseScanExperiment(price_data)
    results1 = exp1.run()
    exp1.analyze()
    exp1.visualize(args.output)

    # 实验2: 非线性扫描
    exp2 = NonlinearScanExperiment(price_data)
    results2 = exp2.run()
    exp2.analyze()
    exp2.visualize(args.output)

    # 实验3: 对比
    exp3 = ComparisonExperiment(price_data)
    result3, comparison = exp3.run()
    exp3.visualize(comparison, args.output)

    print("\n" + "=" * 60)
    print("所有模拟完成！")
    print(f"结果保存在: {args.output}/")
    print("=" * 60)

    # 保存结果摘要
    summary_file = f"{args.output}/summary.txt"
    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write("NEMT Simulator V1 结果摘要\n")
        f.write("=" * 50 + "\n")
        f.write(f"时间: {datetime.now()}\n")
        f.write(f"数据点数: {len(price_data)}\n\n")

        f.write("基础模拟:\n")
        f.write(f"  谱宽: {sim.compute_spectral_width():.6f}\n\n")

        f.write("噪声扫描实验:\n")
        for nl, r in zip(exp1.noise_levels, results1):
            f.write(f"  η={nl}: 谱宽={r.spectral_width:.6f}, 共振峰={r.resonance['num_peaks']}\n")

        f.write("\n非线性扫描实验:\n")
        for beta, r in zip(exp2.beta_values, results2):
            f.write(f"  β={beta}: 谱宽={r.spectral_width:.6f}, 共振峰={r.resonance['num_peaks']}\n")

    print(f"摘要已保存: {summary_file}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n用户中断")
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()
