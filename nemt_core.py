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

# NEMT Simulator V1 - 非平衡市场模拟器
# Non-Equilibrium Market Theory Simulator (BTC实验版)
#
# 核心数学模型：改进的NLS（非线性薛定谔方程）
# i∂ψ/∂t + α∂²ψ/∂x² + β|ψ|²ψ = η(x,t)
#
# 作者：NEMT Lab
# 日期：2026-04-12

"""
NEMT核心模拟器模块

数学模型说明：
- ψ (psi): 市场状态复振幅（价格的波动形态）
- α (alpha): 扩散系数（市场流动性指标）
- β (beta): 非线性系数（情绪/杠杆/羊群效应强度）
- η (eta): 噪声项（外部扰动/随机交易）
"""

import numpy as np
from scipy.fft import fft, ifft, fftfreq
from dataclasses import dataclass
from typing import Optional, Tuple
import warnings


@dataclass
class NEMTParams:
    """NEMT模型参数"""
    alpha: float = 0.1       # 扩散系数
    beta: float = 1.0       # 非线性强度
    noise_level: float = 0.2  # 噪声水平
    dt: float = 0.01        # 时间步长
    dx: float = 1.0         # 空间步长
    steps: int = 200         # 演化步数


class NEMTSimulator:
    """非平衡市场理论模拟器"""

    def __init__(self, params: Optional[NEMTParams] = None):
        self.params = params or NEMTParams()
        self.psi_history = []
        self.spectrum = None
        self.spectral_width = None

    def initialize_state(self, price_data: np.ndarray) -> np.ndarray:
        """
        初始化市场状态（复振幅ψ）

        Args:
            price_data: 原始价格序列

        Returns:
            归一化后的复振幅
        """
        # 归一化处理
        normalized = (price_data - np.mean(price_data)) / np.std(price_data)

        # 转换为复振幅（虚部为0）
        psi = normalized + 1j * np.zeros_like(normalized)

        self.psi = psi
        self.N = len(psi)

        return psi

    def _compute_laplacian(self, psi: np.ndarray) -> np.ndarray:
        """
        计算离散拉普拉斯算子（二阶空间导数）

        使用二阶中心差分格式
        """
        # 首尾使用一阶差分
        laplacian = np.zeros_like(psi, dtype=complex)
        laplacian[1:-1] = psi[:-2] - 2*psi[1:-1] + psi[2:]
        laplacian[0] = psi[1] - 2*psi[0]
        laplacian[-1] = psi[-2] - 2*psi[-1]

        return laplacian / (self.params.dx ** 2)

    def _generate_noise(self, size: int) -> np.ndarray:
        """生成高斯噪声"""
        return self.params.noise_level * np.random.randn(size) * \
               (1 + 1j * np.random.randn(size)) / np.sqrt(2)

    def evolve(self, psi: np.ndarray, steps: Optional[int] = None) -> np.ndarray:
        """
        时间演化（核心算法）

        NLS方程离散格式：
        dψ/dt = i(α∇²ψ + β|ψ|²ψ) + η

        Args:
            psi: 初始复振幅
            steps: 演化步数

        Returns:
            演化后的复振幅
        """
        psi = psi.copy()
        steps = steps or self.params.steps
        self.psi_history = [np.abs(psi)]

        alpha = self.params.alpha
        beta = self.params.beta
        dt = self.params.dt

        for t in range(steps):
            # 1. 计算拉普拉斯算子
            laplacian = self._compute_laplacian(psi)

            # 2. 非线性项 |ψ|²ψ (限制幅度避免溢出)
            psi_abs = np.abs(psi)
            psi_abs = np.clip(psi_abs, 0, 10)  # 限制幅度
            nonlinear = beta * (psi_abs ** 2) * psi

            # 3. NLS更新（使用欧拉法）
            dpsi = 1j * (alpha * laplacian + nonlinear)

            # 4. 添加噪声
            noise = self._generate_noise(len(psi))

            # 5. 更新状态
            psi = psi + dt * (dpsi + noise)

            # 记录振幅演化
            self.psi_history.append(np.abs(psi))

        self.psi_final = psi
        self.psi_evolution = np.array(self.psi_history).T

        return psi

    def spectral_analysis(self, psi: Optional[np.ndarray] = None) -> Tuple[np.ndarray, np.ndarray]:
        """
        频谱分析

        Args:
            psi: 复振幅（默认使用最终状态）

        Returns:
            (频率, 振幅谱)
        """
        psi_to_use = psi if psi is not None else self.psi_final

        # FFT变换
        spectrum = fft(psi_to_use)

        # 频率轴
        N = len(psi_to_use)
        freqs = fftfreq(N, self.params.dx)

        # 取正半轴
        positive_mask = freqs >= 0
        freqs_positive = freqs[positive_mask]
        spectrum_positive = np.abs(spectrum[positive_mask])

        self.spectrum = spectrum_positive
        self.freqs = freqs_positive

        return freqs_positive, spectrum_positive

    def compute_spectral_width(self) -> float:
        """
        计算谱宽（核心指标）

        谱宽 = sqrt(Σ(f - f_mean)²·S(f) / ΣS(f))

        Returns:
            谱宽值
        """
        if self.spectrum is None:
            self.spectral_analysis()

        spectrum_power = np.abs(self.spectrum) ** 2
        freqs = self.freqs

        # 计算加权均值
        total_power = np.sum(spectrum_power)
        if total_power < 1e-10:
            warnings.warn("谱功率过低，可能存在数值问题")
            return 0.0

        mean_freq = np.sum(freqs * spectrum_power) / total_power

        # 计算方差
        variance = np.sum((freqs - mean_freq) ** 2 * spectrum_power) / total_power
        spectral_width = np.sqrt(variance)

        self.spectral_width = spectral_width
        self.mean_frequency = mean_freq

        return spectral_width

    def compute_autocorrelation(self, psi: Optional[np.ndarray] = None) -> np.ndarray:
        """
        计算自相关函数

        用于识别周期性结构
        """
        psi_to_use = psi if psi is not None else self.psi_final
        return np.correlate(np.abs(psi_to_use), np.abs(psi_to_use), mode='full')

    def detect_resonance(self) -> dict:
        """
        检测共振峰

        Returns:
            包含共振信息的字典
        """
        if self.spectrum is None:
            self.spectral_analysis()

        spectrum_power = np.abs(self.spectrum) ** 2
        peak_indices = []

        # 简单峰值检测
        for i in range(1, len(spectrum_power) - 1):
            if spectrum_power[i] > spectrum_power[i-1] and \
               spectrum_power[i] > spectrum_power[i+1]:
                if spectrum_power[i] > np.mean(spectrum_power) * 2:
                    peak_indices.append(i)

        return {
            'peak_frequencies': self.freqs[peak_indices],
            'peak_amplitudes': np.abs(self.spectrum[peak_indices]),
            'num_peaks': len(peak_indices)
        }
