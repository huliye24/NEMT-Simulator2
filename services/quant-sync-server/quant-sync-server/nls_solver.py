#!/usr/bin/env python3
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
Python NLS 求解器 - MATLAB 引擎的纯 Python Fallback
==================================================
当 MATLAB Engine 不可用时，使用 NumPy 实现等效的 NLS 方程求解

改进的非线性薛定谔方程 (NLS):
    i·∂ψ/∂t + α·∂²ψ/∂x² + β·|ψ|²·ψ = η(x,t)

其中:
    ψ (psi): 市场状态复振幅
    α (alpha): 扩散系数（市场流动性）
    β (beta): 非线性系数（情绪/杠杆/羊群效应）
    η (eta): 噪声（外部扰动/随机交易）
"""

import time
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime

import numpy as np
from numpy.fft import fft, fftshift


logger = logging.getLogger(__name__)


@dataclass
class NLSSolverResult:
    """NLS 求解结果"""
    success: bool = False
    error: str = ""

    # 原始数据
    close_prices: List[float] = field(default_factory=list)

    # NEMT 核心指标
    spectral_width: float = 0.0
    mean_frequency: float = 0.0
    resonance_peaks: List[Dict] = field(default_factory=list)

    # 频谱数据 (用于可视化)
    frequencies: List[float] = field(default_factory=list)
    spectrum: List[float] = field(default_factory=list)

    # 演化数据
    evolution_matrix: List[List[float]] = field(default_factory=list)

    # 统计
    stats: Dict[str, Any] = field(default_factory=dict)

    # 性能
    execution_time: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "error": self.error,
            "spectral_width": self.spectral_width,
            "mean_frequency": self.mean_frequency,
            "resonance_peaks": self.resonance_peaks,
            "frequencies": self.frequencies[:100] if self.frequencies else [],
            "spectrum": self.spectrum[:100] if self.spectrum else [],
            "evolution_matrix": self.evolution_matrix[:10] if self.evolution_matrix else [],
            "stats": self.stats,
            "execution_time": self.execution_time,
            "engine": self.stats.get("engine", "numpy"),
            "timestamp": self.timestamp,
        }


class NLSSolver:
    """
    纯 Python NLS 方程求解器
    当 MATLAB Engine 不可用时使用 NumPy 实现等效算法
    """

    def __init__(self):
        self.prices: Optional[np.ndarray] = None
        self.psi: Optional[np.ndarray] = None
        self.psi_evolution: List[np.ndarray] = []

    def solve(
        self,
        prices: List[float],
        alpha: float = 0.1,
        beta: float = 1.0,
        noise: float = 0.2,
        dt: float = 0.01,
        dx: float = 1.0,
        steps: int = 200,
        record_every: int = 5,
    ) -> NLSSolverResult:
        """
        求解 NLS 方程

        Args:
            prices: 价格序列
            alpha: 扩散系数
            beta: 非线性系数
            noise: 噪声水平
            dt: 时间步长
            dx: 空间步长
            steps: 演化步数
            record_every: 每隔多少步记录一次演化

        Returns:
            NLSSolverResult
        """
        result = NLSSolverResult()
        start_time = time.time()
        self.psi_evolution = []

        try:
            prices_arr = np.asarray(prices, dtype=np.float64)
            result.close_prices = prices_arr.tolist()

            if len(prices_arr) < 10:
                result.error = "价格数据太少，至少需要10个数据点"
                return result

            # 1. 归一化并初始化复振幅
            normalized = (prices_arr - np.mean(prices_arr)) / (np.std(prices_arr) + 1e-10)
            psi = normalized.astype(np.complex128)

            # 2. 时间演化
            n = len(psi)
            alpha_val = float(alpha)
            beta_val = float(beta)
            noise_val = float(noise)
            dt_val = float(dt)
            dx_val = float(dx)
            steps_val = int(steps)
            rec_every = int(record_every)

            for step in range(steps_val):
                # Laplacian: ∂²ψ/∂x² (centered finite difference)
                laplacian = np.zeros(n, dtype=np.complex128)
                laplacian[1:-1] = psi[:-2] - 2 * psi[1:-1] + psi[2:]
                laplacian[0] = psi[1] - 2 * psi[0]
                laplacian[-1] = psi[-2] - 2 * psi[-1]
                laplacian /= (dx_val ** 2)

                # Non-linear term: β·|ψ|²·ψ
                psi_abs = np.abs(psi)
                psi_abs = np.minimum(psi_abs, 10.0)  # 防止数值爆炸
                nonlinear = beta_val * (psi_abs ** 2) * psi

                # NLS dψ/dt
                dpsi = 1j * (alpha_val * laplacian + nonlinear)

                # 噪声扰动
                noise_term = noise_val * (
                    np.random.randn(n) + 1j * np.random.randn(n)
                ) / np.sqrt(2)

                # Euler 积分
                psi = psi + dt_val * (dpsi + noise_term)

                # 记录演化 (每隔 record_every 步)
                if step % rec_every == 0:
                    self.psi_evolution.append(np.abs(psi).copy())

            self.psi = psi

            # 3. 频谱分析
            spectrum_result = self._spectral_analysis(psi)
            result.spectral_width = spectrum_result["spectral_width"]
            result.mean_frequency = spectrum_result["mean_frequency"]
            result.resonance_peaks = spectrum_result["resonance_peaks"]
            result.frequencies = spectrum_result["frequencies"]
            result.spectrum = spectrum_result["spectrum"]

            # 4. 演化矩阵
            result.evolution_matrix = [arr.tolist() for arr in self.psi_evolution]

            # 5. 统计信息
            result.stats = {
                "data_points": len(prices_arr),
                "alpha": alpha_val,
                "beta": beta_val,
                "noise": noise_val,
                "steps": steps_val,
                "engine": "numpy",
            }

            result.success = True

        except Exception as e:
            result.error = str(e)
            logger.error(f"NLS 求解失败: {e}")

        finally:
            result.execution_time = time.time() - start_time

        return result

    def _spectral_analysis(self, psi: np.ndarray) -> Dict[str, Any]:
        """FFT 频谱分析"""
        n = len(psi)

        # FFT
        spectrum = fftshift(fft(psi))
        freqs = fftshift(np.fft.fftfreq(n))

        mid = n // 2
        freqs = freqs[mid:]
        spectrum = np.abs(spectrum[mid:])

        # 归一化
        spectrum = spectrum / (np.max(spectrum) + 1e-10)

        # 谱宽 (加权标准差)
        spectrum_power = spectrum ** 2
        total_power = np.sum(spectrum_power)

        if total_power > 1e-10:
            mean_freq = np.sum(freqs * spectrum_power) / total_power
            variance = np.sum((freqs - mean_freq) ** 2 * spectrum_power) / total_power
            spectral_width = float(np.sqrt(variance))
        else:
            mean_freq = 0.0
            spectral_width = 0.0

        # 共振峰检测
        threshold = np.mean(spectrum_power) * 2.0
        peak_indices = []

        for i in range(1, len(spectrum_power) - 1):
            if (spectrum_power[i] > spectrum_power[i - 1] and
                spectrum_power[i] > spectrum_power[i + 1] and
                spectrum_power[i] > threshold):
                peak_indices.append(i)

        resonance_peaks = []
        for idx in peak_indices[:10]:
            resonance_peaks.append({
                "frequency": float(freqs[idx]),
                "amplitude": float(spectrum[idx]),
            })

        return {
            "spectral_width": spectral_width,
            "mean_frequency": float(mean_freq),
            "resonance_peaks": resonance_peaks,
            "frequencies": freqs.tolist(),
            "spectrum": spectrum.tolist(),
        }

    def noise_scan(
        self,
        prices: List[float],
        noise_levels: List[float],
        alpha: float = 0.1,
        beta: float = 1.0,
        dt: float = 0.01,
        dx: float = 1.0,
        steps: int = 200,
    ) -> List[NLSSolverResult]:
        """噪声扫描实验"""
        results = []
        for noise in noise_levels:
            logger.info(f"  噪声扫描: η = {noise}")
            result = self.solve(prices, alpha, beta, noise, dt, dx, steps)
            results.append(result)
        return results

    def beta_scan(
        self,
        prices: List[float],
        beta_values: List[float],
        alpha: float = 0.1,
        noise: float = 0.2,
        dt: float = 0.01,
        dx: float = 1.0,
        steps: int = 200,
    ) -> List[NLSSolverResult]:
        """非线性系数扫描实验"""
        results = []
        for beta in beta_values:
            logger.info(f"  非线性扫描: β = {beta}")
            result = self.solve(prices, alpha, beta, noise, dt, dx, steps)
            results.append(result)
        return results


# 全局单例
_solver: Optional[NLSSolver] = None


def get_solver() -> NLSSolver:
    global _solver
    if _solver is None:
        _solver = NLSSolver()
    return _solver


def solve_nls(
    prices: List[float],
    params: Dict[str, Any] = None,
) -> Dict[str, Any]:
    """
    便捷函数: 求解 NLS 方程

    与 MatlabBridge.run_analysis() 相同的接口
    当 MATLAB 不可用时自动 fallback 到 NumPy
    """
    params = params or {}

    alpha = params.get("alpha", 0.1)
    beta = params.get("beta", 1.0)
    noise = params.get("noiseLevel", params.get("noise", 0.2))
    dt = params.get("dt", 0.01)
    dx = params.get("dx", 1.0)
    steps = params.get("steps", 200)

    solver = get_solver()
    result = solver.solve(
        prices=prices,
        alpha=alpha,
        beta=beta,
        noise=noise,
        dt=dt,
        dx=dx,
        steps=steps,
    )

    return result.to_dict()


# ============================================================================
# 单元测试
# ============================================================================
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    # 生成测试价格数据
    np.random.seed(42)
    t = np.linspace(0, 10, 500)
    prices = (
        50000
        + 2000 * np.sin(0.5 * t)
        + 1500 * np.sin(1.3 * t + 0.3)
        + 500 * np.sin(2.7 * t + 0.7)
        + 300 * np.random.randn(500)
    ).tolist()

    print("=" * 60)
    print("NLS Solver Fallback 测试")
    print("=" * 60)

    # 单次分析
    print("\n[1] 单次 NLS 求解...")
    solver = NLSSolver()
    result = solver.solve(prices, alpha=0.1, beta=1.0, noise=0.2, steps=200)
    print(f"    谱宽: {result.spectral_width:.6f}")
    print(f"    平均频率: {result.mean_frequency:.6f}")
    print(f"    共振峰数量: {len(result.resonance_peaks)}")
    print(f"    耗时: {result.execution_time:.2f}s")

    # 噪声扫描
    print("\n[2] 噪声扫描实验...")
    noise_results = solver.noise_scan(prices, [0.0, 0.1, 0.3, 0.5, 1.0], steps=200)
    for r in noise_results:
        print(f"    η={r.stats.get('noise', 0):.1f}: 谱宽={r.spectral_width:.6f}, 峰数={len(r.resonance_peaks)}")

    # 非线性扫描
    print("\n[3] 非线性扫描实验...")
    beta_results = solver.beta_scan(prices, [0.5, 1.0, 2.0, 5.0, 10.0], steps=200)
    for r in beta_results:
        print(f"    β={r.stats.get('beta', 0):.1f}: 谱宽={r.spectral_width:.6f}, 峰数={len(r.resonance_peaks)}")

    print("\n✅ NLS Solver 测试完成")
