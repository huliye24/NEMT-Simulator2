"""
实验模块
包含三个核心实验
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field

from nemt_core import NEMTSimulator, NEMTParams
from visualizer import NEMTVisualizer


@dataclass
class ExperimentResult:
    """实验结果"""
    params: NEMTParams
    spectral_width: float
    spectrum: np.ndarray
    freqs: np.ndarray
    psi: np.ndarray
    evolution: Optional[np.ndarray] = None
    resonance: Optional[Dict] = None
    mean_frequency: float = 0.0


class NEMTExperiment:
    """NEMT实验基类"""

    def __init__(self, price_data: np.ndarray, name: str = "Experiment"):
        self.price_data = price_data
        self.name = name
        self.results: List[ExperimentResult] = []
        self.visualizer = NEMTVisualizer()

    def run_single(
        self,
        params: NEMTParams,
        save_evolution: bool = True
    ) -> ExperimentResult:
        """运行单次模拟"""
        sim = NEMTSimulator(params)
        psi = sim.initialize_state(self.price_data)
        psi = sim.evolve(psi)
        freqs, spectrum = sim.spectral_analysis(psi)
        spec_width = sim.compute_spectral_width()
        resonance = sim.detect_resonance()

        result = ExperimentResult(
            params=params,
            spectral_width=spec_width,
            spectrum=spectrum,
            freqs=freqs,
            psi=psi,
            evolution=sim.psi_evolution if save_evolution else None,
            resonance=resonance,
            mean_frequency=sim.mean_frequency
        )

        return result

    def run_batch(
        self,
        param_list: List[NEMTParams],
        show_progress: bool = True
    ) -> List[ExperimentResult]:
        """批量运行"""
        results = []
        for i, params in enumerate(param_list):
            if show_progress:
                print(f"[{i+1}/{len(param_list)}] 运行参数: α={params.alpha}, β={params.beta}, η={params.noise_level}")
            result = self.run_single(params)
            results.append(result)
            if show_progress:
                print(f"    谱宽: {result.spectral_width:.6f}, 共振峰: {result.resonance['num_peaks']}")
        return results


class NoiseScanExperiment(NEMTExperiment):
    """
    实验1：噪声扫描

    目的：研究噪声水平对市场结构的影响
    预期观察：
    - 低噪声：清晰的谱结构
    - 高噪声：谱宽突然放大（相变？）
    - 可能出现共振峰
    """

    def __init__(self, price_data: np.ndarray):
        super().__init__(price_data, "噪声扫描实验")
        self.noise_levels = [0, 0.1, 0.3, 0.5]

    def run(self) -> List[ExperimentResult]:
        """执行噪声扫描"""
        print("=" * 60)
        print("实验1：噪声扫描")
        print("目的：观察不同噪声水平下的谱结构响应")
        print("=" * 60)

        base_params = NEMTParams(alpha=0.1, beta=1.0, steps=200)

        param_list = [
            NEMTParams(alpha=p.alpha, beta=p.beta, noise_level=nl,
                      steps=200, dt=0.01)
            for nl in self.noise_levels
            for p in [base_params]
        ]

        # 只创建每个噪声水平一个参数
        param_list = [
            NEMTParams(alpha=0.1, beta=1.0, noise_level=nl, steps=200)
            for nl in self.noise_levels
        ]

        self.results = self.run_batch(param_list)

        return self.results

    def analyze(self) -> Dict:
        """分析结果"""
        print("\n" + "=" * 60)
        print("噪声扫描分析")
        print("=" * 60)

        summary = {
            'noise_levels': self.noise_levels,
            'spectral_widths': [r.spectral_width for r in self.results],
            'mean_frequencies': [r.mean_frequency for r in self.results],
            'resonance_counts': [r.resonance['num_peaks'] for r in self.results]
        }

        # 检测相变
        widths = summary['spectral_widths']
        if len(widths) >= 3:
            # 计算增长率
            growth_rates = np.diff(widths) / np.diff(self.noise_levels)
            max_growth_idx = np.argmax(growth_rates)
            print(f"\n最大增长率在: η = {self.noise_levels[max_growth_idx]} → {self.noise_levels[max_growth_idx+1]}")
            print(f"增长率: {growth_rates[max_growth_idx]:.4f}")

            # 检查是否出现突变
            if max_growth_idx > 0:
                print(f"警告: 在 η = {self.noise_levels[max_growth_idx+1]} 附近可能存在结构相变")

        print(f"\n共振峰统计:")
        for nl, count in zip(self.noise_levels, summary['resonance_counts']):
            print(f"  η = {nl}: {count} 个共振峰")

        return summary

    def visualize(self, output_dir: str = "output"):
        """可视化"""
        import os
        os.makedirs(output_dir, exist_ok=True)

        # 1. 噪声实验总图
        fig_data = [{
            'spectral_width': r.spectral_width,
            'spectrum': r.spectrum,
            'freqs': r.freqs,
            'evolution': r.evolution
        } for r in self.results]

        fig = self.visualizer.plot_noise_experiment(fig_data, self.noise_levels)
        self.visualizer.save_figure(fig, f"{output_dir}/noise_experiment.png")

        # 2. 每个噪声水平的详细图
        for nl, result in zip(self.noise_levels, self.results):
            fig_res = self.visualizer.plot_resonance_analysis(
                result.psi, result.spectrum, result.freqs, result.resonance
            )
            self.visualizer.save_figure(fig_res, f"{output_dir}/noise_{nl}_resonance.png")

        print(f"图表已保存至: {output_dir}/")


class NonlinearScanExperiment(NEMTExperiment):
    """
    实验2：非线性强度扫描

    目的：研究非线性效应（情绪/杠杆/羊群）对市场的影响
    预期观察：
    - β增大：可能出现孤子结构
    - β增大：局部价格聚集
    - 高β：谱峰分裂
    """

    def __init__(self, price_data: np.ndarray):
        super().__init__(price_data, "非线性扫描实验")
        self.beta_values = [0.1, 0.5, 1.0, 2.0]

    def run(self) -> List[ExperimentResult]:
        """执行非线性扫描"""
        print("=" * 60)
        print("实验2：非线性强度扫描")
        print("目的：观察不同非线性强度下的市场结构")
        print("=" * 60)

        param_list = [
            NEMTParams(alpha=0.1, beta=beta, noise_level=0.2, steps=200)
            for beta in self.beta_values
        ]

        self.results = self.run_batch(param_list)

        return self.results

    def analyze(self) -> Dict:
        """分析结果"""
        print("\n" + "=" * 60)
        print("非线性扫描分析")
        print("=" * 60)

        summary = {
            'beta_values': self.beta_values,
            'spectral_widths': [r.spectral_width for r in self.results],
            'resonance_counts': [r.resonance['num_peaks'] for r in self.results],
            'mean_frequencies': [r.mean_frequency for r in self.results]
        }

        # 分析非线性效应
        print(f"\n谱宽随β变化:")
        for beta, width in zip(self.beta_values, summary['spectral_widths']):
            print(f"  β = {beta:4.1f}: 谱宽 = {width:.6f}")

        # 检测孤子特征（谱峰数量变化）
        peak_changes = np.diff(summary['resonance_counts'])
        if any(peak_changes < 0):
            idx = np.where(peak_changes < 0)[0][0]
            print(f"\n警告: 在 β = {self.beta_values[idx]} → {self.beta_values[idx+1]} 出现谱峰分裂")
            print("这可能表明孤子结构形成")

        return summary

    def visualize(self, output_dir: str = "output"):
        """可视化"""
        import os
        os.makedirs(output_dir, exist_ok=True)

        fig_data = [{
            'spectral_width': r.spectral_width,
            'spectrum': r.spectrum,
            'freqs': r.freqs,
            'evolution': r.evolution,
            'psi': r.psi
        } for r in self.results]

        fig = self.visualizer.plot_nonlinear_experiment(fig_data, self.beta_values)
        self.visualizer.save_figure(fig, f"{output_dir}/nonlinear_experiment.png")

        print(f"图表已保存至: {output_dir}/")


class ComparisonExperiment(NEMTExperiment):
    """
    实验3：真实 vs 模拟对比

    目的：比较原始价格与模拟后的差异
    """

    def __init__(self, price_data: np.ndarray, params: Optional[NEMTParams] = None):
        super().__init__(price_data, "对比实验")
        self.params = params or NEMTParams()

    def run(self) -> Tuple[ExperimentResult, Dict]:
        """执行对比实验"""
        print("=" * 60)
        print("实验3：真实 vs 模拟对比")
        print("=" * 60)

        # 原始数据频谱
        from scipy.fft import fft
        original_psi = (self.price_data - np.mean(self.price_data)) / np.std(self.price_data)
        original_fft = fft(original_psi)
        freqs = np.fft.fftfreq(len(original_psi))

        # 模拟
        result = self.run_single(self.params)

        print(f"\n原始数据:")
        print(f"  数据点: {len(original_psi)}")
        print(f"  谱宽: N/A (原始数据)")

        print(f"\n模拟后:")
        print(f"  谱宽: {result.spectral_width:.6f}")
        print(f"  共振峰: {result.resonance['num_peaks']}")

        comparison = {
            'original_psi': original_psi,
            'original_spectrum': original_fft,
            'evolved_psi': result.psi,
            'evolved_spectrum': result.spectrum,
            'freqs': result.freqs,
            'result': result
        }

        return result, comparison

    def visualize(self, comparison: Dict, output_dir: str = "output"):
        """可视化"""
        import os
        os.makedirs(output_dir, exist_ok=True)

        fig = self.visualizer.plot_comparison(
            comparison['original_psi'],
            comparison['evolved_psi'],
            comparison['original_spectrum'],
            comparison['evolved_spectrum'],
            comparison['freqs']
        )
        self.visualizer.save_figure(fig, f"{output_dir}/comparison.png")

        print(f"图表已保存至: {output_dir}/")


def run_all_experiments(price_data: np.ndarray) -> Dict[str, ExperimentResult]:
    """
    运行所有实验

    Returns:
        包含所有实验结果的字典
    """
    results = {}

    # 实验1: 噪声扫描
    exp1 = NoiseScanExperiment(price_data)
    results['noise_scan'] = exp1.run()
    exp1.analyze()
    exp1.visualize()

    # 实验2: 非线性扫描
    exp2 = NonlinearScanExperiment(price_data)
    results['nonlinear_scan'] = exp2.run()
    exp2.analyze()
    exp2.visualize()

    # 实验3: 对比
    exp3 = ComparisonExperiment(price_data)
    result3, comparison = exp3.run()
    exp3.visualize(comparison)

    return results
