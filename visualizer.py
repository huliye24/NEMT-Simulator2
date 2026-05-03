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
可视化模块
生成NEMT分析图表
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
import matplotlib
matplotlib.use('Agg')  # 非交互式后端
from typing import Optional, Tuple, List
from scipy.fft import fftfreq

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False


class NEMTVisualizer:
    """NEMT可视化器"""

    def __init__(self, figsize: Tuple[int, int] = (14, 10)):
        self.figsize = figsize
        self.fig = None

    def plot_spectrum(
        self,
        spectrum: np.ndarray,
        freqs: np.ndarray,
        title: str = "频谱结构",
        highlight_resonance: bool = True
    ) -> plt.Figure:
        """
        绘制频谱图

        Args:
            spectrum: 频谱振幅
            freqs: 频率轴
            title: 图表标题
            highlight_resonance: 是否高亮共振峰

        Returns:
            matplotlib Figure对象
        """
        fig, ax = plt.subplots(figsize=(12, 5))

        ax.plot(freqs, np.abs(spectrum), 'b-', linewidth=1.5, label='频谱振幅')
        ax.fill_between(freqs, np.abs(spectrum), alpha=0.3)

        if highlight_resonance:
            # 标记主要峰值
            power = np.abs(spectrum) ** 2
            threshold = np.mean(power) * 2
            peaks = np.where(power > threshold)[0]

            if len(peaks) > 0:
                ax.scatter(freqs[peaks], np.abs(spectrum[peaks]),
                          c='red', s=50, zorder=5, label='共振峰')

        ax.set_xlabel('频率', fontsize=12)
        ax.set_ylabel('振幅', fontsize=12)
        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.legend()
        ax.grid(True, alpha=0.3)

        plt.tight_layout()
        return fig

    def plot_evolution(
        self,
        psi_evolution: np.ndarray,
        dt: float = 0.01,
        title: str = "市场波动演化（NEMT）"
    ) -> plt.Figure:
        """
        绘制时空演化图（核心图表）

        Args:
            psi_evolution: 演化矩阵 (N, steps)
            dt: 时间步长
            title: 标题

        Returns:
            matplotlib Figure对象
        """
        fig, ax = plt.subplots(figsize=(14, 8))

        # 绘制热力图
        extent = [0, psi_evolution.shape[1] * dt, 0, psi_evolution.shape[0]]
        im = ax.imshow(psi_evolution, aspect='auto', cmap='viridis',
                       extent=extent, origin='lower')

        ax.set_xlabel('时间 (t)', fontsize=12)
        ax.set_ylabel('空间索引 (价格位置)', fontsize=12)
        ax.set_title(title, fontsize=14, fontweight='bold')

        cbar = plt.colorbar(im, ax=ax)
        cbar.set_label('|ψ| 振幅', fontsize=11)

        plt.tight_layout()
        return fig

    def plot_comparison(
        self,
        original_price: np.ndarray,
        evolved_psi: np.ndarray,
        original_spectrum: np.ndarray,
        evolved_spectrum: np.ndarray,
        freqs: np.ndarray
    ) -> plt.Figure:
        """
        原始 vs 模拟对比图

        Args:
            original_price: 原始价格
            evolved_psi: 演化后状态
            original_spectrum: 原始频谱
            evolved_spectrum: 演化后频谱
            freqs: 频率轴

        Returns:
            matplotlib Figure对象
        """
        fig = plt.figure(figsize=(16, 12))
        gs = GridSpec(3, 2, figure=fig, hspace=0.3, wspace=0.25)

        # 获取有效的频谱长度
        n = min(len(freqs), len(evolved_spectrum))

        # 1. 原始价格时序
        ax1 = fig.add_subplot(gs[0, 0])
        ax1.plot(original_price, 'b-', linewidth=0.8, alpha=0.8)
        ax1.set_title('原始价格序列', fontsize=12)
        ax1.set_xlabel('索引')
        ax1.set_ylabel('价格（归一化）')
        ax1.grid(True, alpha=0.3)

        # 2. 演化后振幅
        ax2 = fig.add_subplot(gs[0, 1])
        ax2.plot(np.abs(evolved_psi), 'r-', linewidth=0.8, alpha=0.8)
        ax2.set_title('演化后|ψ|分布', fontsize=12)
        ax2.set_xlabel('索引')
        ax2.set_ylabel('振幅')
        ax2.grid(True, alpha=0.3)

        # 3. 原始频谱（取正半轴）
        ax3 = fig.add_subplot(gs[1, 0])
        orig_spec_abs = np.abs(original_spectrum[:n])
        ax3.plot(freqs[:n], orig_spec_abs, 'b-', linewidth=1.2)
        ax3.set_title('原始价格频谱', fontsize=12)
        ax3.set_xlabel('频率')
        ax3.set_ylabel('振幅')
        ax3.grid(True, alpha=0.3)

        # 4. 演化后频谱
        ax4 = fig.add_subplot(gs[1, 1])
        ax4.plot(freqs[:n], np.abs(evolved_spectrum[:n]), 'r-', linewidth=1.2)
        ax4.set_title('演化后频谱', fontsize=12)
        ax4.set_xlabel('频率')
        ax4.set_ylabel('振幅')
        ax4.grid(True, alpha=0.3)

        # 5. 频谱对比
        ax5 = fig.add_subplot(gs[2, :])
        ax5.plot(freqs[:n], orig_spec_abs, 'b-',
                linewidth=1.5, alpha=0.7, label='原始')
        ax5.plot(freqs[:n], np.abs(evolved_spectrum[:n]), 'r-',
                linewidth=1.5, alpha=0.7, label='演化后')
        ax5.set_title('频谱对比', fontsize=12)
        ax5.set_xlabel('频率')
        ax5.set_ylabel('振幅')
        ax5.legend()
        ax5.grid(True, alpha=0.3)

        fig.suptitle('NEMT模拟对比分析', fontsize=16, fontweight='bold', y=0.98)

        return fig

    def plot_noise_experiment(
        self,
        results: List[dict],
        noise_levels: List[float]
    ) -> plt.Figure:
        """
        噪声扫描实验结果

        Args:
            results: 每种噪声水平的结果
            noise_levels: 噪声水平列表

        Returns:
            matplotlib Figure对象
        """
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))

        # 提取数据
        spectral_widths = [r['spectral_width'] for r in results]
        spectra = [r['spectrum'] for r in results]
        freqs = results[0]['freqs']

        # 1. 谱宽 vs 噪声水平
        ax1 = axes[0, 0]
        ax1.plot(noise_levels, spectral_widths, 'bo-', linewidth=2, markersize=8)
        ax1.set_xlabel('噪声水平')
        ax1.set_ylabel('谱宽')
        ax1.set_title('谱宽随噪声变化', fontsize=12)
        ax1.grid(True, alpha=0.3)

        # 2. 频谱叠加
        ax2 = axes[0, 1]
        colors = plt.cm.viridis(np.linspace(0, 1, len(noise_levels)))
        for i, (sp, nl, c) in enumerate(zip(spectra, noise_levels, colors)):
            ax2.plot(freqs, np.abs(sp), color=c, linewidth=1.5,
                    label=f'η={nl}', alpha=0.8)
        ax2.set_xlabel('频率')
        ax2.set_ylabel('振幅')
        ax2.set_title('不同噪声水平下的频谱', fontsize=12)
        ax2.legend()
        ax2.grid(True, alpha=0.3)

        # 3. 各演化图
        for idx, (r, nl) in enumerate(zip(results[:2], noise_levels[:2])):
            if 'evolution' in r and idx < 2:
                ax = axes[1, idx]
                evo = r['evolution']
                im = ax.imshow(evo, aspect='auto', cmap='plasma')
                ax.set_title(f'演化图 η={nl}', fontsize=11)
                ax.set_xlabel('时间')
                ax.set_ylabel('空间')
                plt.colorbar(im, ax=ax)

        fig.suptitle('噪声扫描实验', fontsize=16, fontweight='bold')
        plt.tight_layout()

        return fig

    def plot_nonlinear_experiment(
        self,
        results: List[dict],
        beta_values: List[float]
    ) -> plt.Figure:
        """
        非线性扫描实验结果

        Args:
            results: 每种β值的结果
            beta_values: β值列表

        Returns:
            matplotlib Figure对象
        """
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))

        spectral_widths = [r['spectral_width'] for r in results]
        spectra = [r['spectrum'] for r in results]
        freqs = results[0]['freqs']

        # 1. 谱宽 vs β
        ax1 = axes[0, 0]
        ax1.plot(beta_values, spectral_widths, 'ro-', linewidth=2, markersize=8)
        ax1.set_xlabel('β (非线性强度)')
        ax1.set_ylabel('谱宽')
        ax1.set_title('谱宽随非线性强度变化', fontsize=12)
        ax1.grid(True, alpha=0.3)

        # 2. 频谱对比
        ax2 = axes[0, 1]
        colors = plt.cm.plasma(np.linspace(0, 1, len(beta_values)))
        for sp, bv, c in zip(spectra, beta_values, colors):
            ax2.plot(freqs, np.abs(sp), color=c, linewidth=1.5,
                    label=f'β={bv}', alpha=0.8)
        ax2.set_xlabel('频率')
        ax2.set_ylabel('振幅')
        ax2.set_title('不同非线性强度下的频谱', fontsize=12)
        ax2.legend()
        ax2.grid(True, alpha=0.3)

        # 3. 振幅分布直方图
        ax3 = axes[1, 0]
        for r, bv, c in zip(results[:3], beta_values[:3], colors[:3]):
            ax3.hist(np.abs(r['psi']), bins=30, alpha=0.5, color=c, label=f'β={bv}')
        ax3.set_xlabel('|ψ|')
        ax3.set_ylabel('频数')
        ax3.set_title('振幅分布', fontsize=12)
        ax3.legend()
        ax3.grid(True, alpha=0.3)

        # 4. 最后两种β的演化图
        for idx, (r, bv) in enumerate(zip(results[-2:], beta_values[-2:])):
            ax = axes[1, idx]
            if 'evolution' in r:
                evo = r['evolution']
                im = ax.imshow(evo, aspect='auto', cmap='magma')
                ax.set_title(f'演化图 β={bv}', fontsize=11)
                ax.set_xlabel('时间')
                ax.set_ylabel('空间')
                plt.colorbar(im, ax=ax)

        fig.suptitle('非线性扫描实验', fontsize=16, fontweight='bold')
        plt.tight_layout()

        return fig

    def plot_resonance_analysis(
        self,
        psi: np.ndarray,
        spectrum: np.ndarray,
        freqs: np.ndarray,
        resonance_info: dict
    ) -> plt.Figure:
        """
        共振分析图

        Args:
            psi: 复振幅
            spectrum: 频谱
            freqs: 频率轴
            resonance_info: 共振信息

        Returns:
            matplotlib Figure对象
        """
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))

        # 1. 振幅时间序列
        ax1 = axes[0, 0]
        ax1.plot(np.abs(psi), 'g-', linewidth=0.8)
        ax1.set_title('|ψ(t)| 振幅演化', fontsize=12)
        ax1.set_xlabel('索引')
        ax1.set_ylabel('振幅')
        ax1.grid(True, alpha=0.3)

        # 2. 相位
        ax2 = axes[0, 1]
        ax2.plot(np.angle(psi), 'purple', linewidth=0.5, alpha=0.7)
        ax2.set_title('相位 arg(ψ)', fontsize=12)
        ax2.set_xlabel('索引')
        ax2.set_ylabel('相位 (rad)')
        ax2.grid(True, alpha=0.3)

        # 3. 频谱（标记共振峰）
        ax3 = axes[1, 0]
        ax3.plot(freqs, np.abs(spectrum), 'b-', linewidth=1.2)
        peak_freqs = resonance_info.get('peak_frequencies', [])
        peak_amps = resonance_info.get('peak_amplitudes', [])
        if len(peak_freqs) > 0:
            ax3.scatter(peak_freqs, np.abs(peak_amps), c='red', s=100,
                       marker='v', zorder=5, label=f'共振峰 ({len(peak_freqs)}个)')
        ax3.set_title('频谱与共振峰', fontsize=12)
        ax3.set_xlabel('频率')
        ax3.set_ylabel('振幅')
        ax3.legend()
        ax3.grid(True, alpha=0.3)

        # 4. 功率谱
        ax4 = axes[1, 1]
        power = np.abs(spectrum) ** 2
        ax4.semilogy(freqs, power, 'r-', linewidth=1.2)
        ax4.set_title('功率谱 (对数坐标)', fontsize=12)
        ax4.set_xlabel('频率')
        ax4.set_ylabel('功率')
        ax4.grid(True, alpha=0.3)

        fig.suptitle('共振分析', fontsize=16, fontweight='bold')
        plt.tight_layout()

        return fig

    def save_figure(self, fig: plt.Figure, filename: str, dpi: int = 150):
        """保存图表"""
        fig.savefig(filename, dpi=dpi, bbox_inches='tight')
        print(f"图表已保存: {filename}")
        plt.close(fig)
