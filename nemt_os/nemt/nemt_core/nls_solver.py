"""
NLS 方程求解器 (NLS Solver)
非线性薛定谔方程: i∂ψ/∂t + α∂²ψ/∂x² + β|ψ|²ψ = η
"""

import numpy as np
from dataclasses import dataclass
from typing import List, Tuple, Optional
from datetime import datetime


@dataclass
class NLSParams:
    """NLS 方程参数"""
    alpha: float = 0.5      # 扩散系数 (流动性指标)
    beta: float = 1.0       # 非线性强度 (情绪效应)
    noise_level: float = 0.1  # 噪声强度 (外部扰动)
    dt: float = 0.01        # 时间步长
    dx: float = 1.0          # 空间步长
    steps: int = 100        # 演化步数


class Complex:
    """复数类，用于 NLS 方程"""
    
    def __init__(self, re: float = 0.0, im: float = 0.0):
        self.re = re
        self.im = im
    
    @staticmethod
    def from_polar(r: float, theta: float) -> 'Complex':
        """从极坐标创建"""
        return Complex(r * np.cos(theta), r * np.sin(theta))
    
    def abs(self) -> float:
        """模"""
        return np.sqrt(self.re ** 2 + self.im ** 2)
    
    def abs2(self) -> float:
        """模平方"""
        return self.re ** 2 + self.im ** 2
    
    def conj(self) -> 'Complex':
        """共轭"""
        return Complex(self.re, -self.im)
    
    def __add__(self, other: 'Complex') -> 'Complex':
        return Complex(self.re + other.re, self.im + other.im)
    
    def __sub__(self, other) -> 'Complex':
        if isinstance(other, Complex):
            return Complex(self.re - other.re, self.im - other.im)
        # Handle scalar subtraction: scalar - Complex
        val = float(other) if not isinstance(other, float) else other
        return Complex(val - self.re, -self.im)
    
    def __rsub__(self, other) -> 'Complex':
        return self.__sub__(other)
    
    def __mul__(self, other) -> 'Complex':
        if isinstance(other, Complex):
            return Complex(
                self.re * other.re - self.im * other.im,
                self.re * other.im + self.im * other.re
            )
        # Handle int and float
        val = float(other) if not isinstance(other, float) else other
        return Complex(self.re * val, self.im * val)
    
    def __rmul__(self, scalar: float) -> 'Complex':
        val = float(scalar) if not isinstance(scalar, float) else scalar
        return Complex(self.re * val, self.im * val)
    
    def __repr__(self) -> str:
        return f"Complex({self.re:.4f}+{self.im:.4f}j)"


class NLSSolver:
    """
    NLS 方程求解器
    
    方程: i∂ψ/∂t + α∂²ψ/∂x² + β|ψ|²ψ = η
    
    其中:
    - ψ (psi): 市场状态复振幅
    - α (alpha): 扩散系数，流动性指标
    - β (beta): 非线性强度，情绪效应
    - η (eta): 噪声项，外部扰动
    """
    
    def __init__(self, params: NLSParams = None):
        self.params = params or NLSParams()
        self.psi: List[Complex] = []
        self.psi_history: List[np.ndarray] = []
        self.N: int = 0
    
    def initialize_state(self, price_data: np.ndarray) -> np.ndarray:
        """
        初始化市场状态（复振幅 ψ）
        
        Args:
            price_data: 原始价格数据
            
        Returns:
            归一化后的复振幅数组
        """
        n = len(price_data)
        
        # 归一化
        mean = np.mean(price_data)
        std = np.std(price_data)
        
        if std > 0:
            normalized = (price_data - mean) / std
        else:
            normalized = np.zeros(n)
        
        # 转为复数
        self.psi = [Complex(float(x), 0.0) for x in normalized]
        self.N = n
        self.psi_history = [self._psi_abs()]
        
        return normalized
    
    def _psi_abs(self) -> np.ndarray:
        """获取当前状态的振幅"""
        return np.array([p.abs() for p in self.psi])
    
    def _generate_noise(self, size: int) -> List[Complex]:
        """生成高斯噪声（使用 Box-Muller 变换）"""
        noise = []
        for _ in range(size):
            u1 = np.random.random()
            u2 = np.random.random()
            z1 = np.sqrt(-2 * np.log(u1 + 1e-10)) * np.cos(2 * np.pi * u2)
            z2 = np.sqrt(-2 * np.log(u1 + 1e-10)) * np.sin(2 * np.pi * u2)
            
            scale = self.params.noise_level * 0.5
            noise.append(Complex(scale * z1, scale * z2))
        
        return noise
    
    def _compute_laplacian(self, psi: List[Complex]) -> List[Complex]:
        """
        计算离散拉普拉斯算子 ∇²ψ
        
        使用中心差分: ∇²ψ ≈ (ψ_{i+1} - 2ψ_i + ψ_{i-1}) / dx²
        """
        laplacian = [Complex() for _ in range(self.N)]
        dx2 = self.params.dx * self.params.dx
        
        # Internal points
        for i in range(1, self.N - 1):
            term = psi[i - 1] - psi[i] * 2 + psi[i + 1]
            laplacian[i] = term * (1 / dx2)
        
        # Boundary conditions
        laplacian[0] = (psi[1] - psi[0]) * (1 / self.params.dx)
        laplacian[self.N - 1] = (psi[self.N - 2] - psi[self.N - 1]) * (1 / self.params.dx)
        
        return laplacian
    
    def evolve(self, psi: List[Complex] = None, steps: int = None) -> List[Complex]:
        """
        时间演化（核心算法）
        
        求解: dψ/dt = i(α∇²ψ + β|ψ|²ψ) + η
        
        Args:
            psi: 初始状态，None 时使用当前状态
            steps: 演化步数，None 时使用参数中的值
            
        Returns:
            演化后的状态
        """
        psi = psi if psi is not None else self.psi
        if not psi:
            raise ValueError("State not initialized. Call initialize_state first.")
        
        N = self.N
        steps = steps if steps is not None else self.params.steps
        alpha = self.params.alpha
        beta = self.params.beta
        dt = self.params.dt
        
        # 记录初始状态
        self.psi_history = [self._psi_abs()]
        
        # 工作副本
        state = [Complex(p.re, p.im) for p in psi]
        
        for t in range(steps):
            # 1. 计算拉普拉斯算子
            laplacian = self._compute_laplacian(state)
            
            # 2. 非线性项 |ψ|²ψ
            nonlinear = [p * p.abs2() * beta for p in state]
            
            # 3. dψ/dt = i(α∇²ψ + β|ψ|²ψ)
            dpsi = []
            for i in range(N):
                term = laplacian[i] * alpha + nonlinear[i]
                # i * term = (-term.im + term.re * i)
                dpsi.append(Complex(-term.im, term.re))
            
            # 4. 添加噪声
            noise = self._generate_noise(N)
            
            # 5. 更新状态（欧拉法）
            new_state = []
            for i in range(N):
                delta = dpsi[i] * dt + noise[i] * dt
                new_state.append(state[i] + delta)
            
            state = new_state
            
            # 记录振幅演化
            if t % 10 == 0:  # 每10步记录一次
                self.psi_history.append(self._psi_abs())
        
        self.psi = state
        return self.psi
    
    def get_spectral_analysis(self) -> Tuple[np.ndarray, np.ndarray]:
        """
        频谱分析
        
        Returns:
            (frequencies, spectrum_amplitude) 频率和幅度谱
        """
        if not self.psi:
            raise ValueError("State not initialized.")
        
        # 提取实部进行 FFT
        psi_real = np.array([p.re for p in self.psi])
        
        # 确保长度是2的幂次
        N = len(psi_real)
        next_pow2 = 2 ** int(np.ceil(np.log2(N)))
        if next_pow2 > N:
            psi_real = np.pad(psi_real, (0, next_pow2 - N), mode='constant')
        
        # FFT
        spectrum = np.fft.fft(psi_real)
        amplitudes = np.abs(spectrum)
        
        # 频率轴
        frequencies = np.fft.fftfreq(len(spectrum), d=self.params.dx)
        
        # fftshift: 将零频率移到中心
        frequencies = np.fft.fftshift(frequencies)
        amplitudes = np.fft.fftshift(amplitudes)
        
        return frequencies, amplitudes
    
    def compute_spectral_width(self, frequencies: np.ndarray = None, amplitudes: np.ndarray = None) -> float:
        """
        计算谱宽
        
        谱宽 = sqrt(Σ(f - f_mean)²·S(f) / ΣS(f))
        
        Returns:
            谱宽值（越小表示市场相干性越高）
        """
        if frequencies is None or amplitudes is None:
            frequencies, amplitudes = self.get_spectral_analysis()
        
        # 排除零频率附近的直流分量
        mask = np.abs(frequencies) > 0.01
        freqs = frequencies[mask]
        amps = amplitudes[mask]
        
        if len(amps) == 0 or np.sum(amps) < 1e-10:
            return 0.02
        
        # 计算加权均值频率
        total_power = np.sum(amps)
        mean_freq = np.sum(freqs * amps) / total_power
        
        # 计算方差
        variance = np.sum((freqs - mean_freq) ** 2 * amps) / total_power
        
        result = np.sqrt(variance)
        
        # 如果结果无效，返回默认值
        if np.isnan(result) or result == 0:
            return 0.02
        
        return float(result)
    
    def detect_resonance_peaks(self, frequencies: np.ndarray = None, amplitudes: np.ndarray = None) -> dict:
        """
        检测共振峰
        
        Returns:
            dict: {
                'peak_frequencies': [...],
                'peak_amplitudes': [...],
                'num_peaks': int
            }
        """
        if frequencies is None or amplitudes is None:
            frequencies, amplitudes = self.get_spectral_analysis()
        
        # 计算均值
        mean = np.mean(amplitudes)
        
        # 峰值检测
        peak_indices = []
        for i in range(1, len(amplitudes) - 1):
            if amplitudes[i] > amplitudes[i - 1] and amplitudes[i] > amplitudes[i + 1]:
                if amplitudes[i] > mean * 1.5:
                    peak_indices.append(i)
        
        return {
            'peak_frequencies': frequencies[peak_indices].tolist(),
            'peak_amplitudes': amplitudes[peak_indices].tolist(),
            'num_peaks': len(peak_indices)
        }
    
    def get_evolution_history(self) -> np.ndarray:
        """获取振幅演化历史"""
        return np.array(self.psi_history)
    
    def run_experiment(self, price_data: np.ndarray) -> dict:
        """
        运行完整实验
        
        Args:
            price_data: 价格数据
            
        Returns:
            实验结果字典
        """
        # 初始化
        normalized = self.initialize_state(price_data)
        
        # 演化
        psi_final = self.evolve()
        
        # 频谱分析
        frequencies, amplitudes = self.get_spectral_analysis()
        
        # 谱宽
        spectral_width = self.compute_spectral_width(frequencies, amplitudes)
        
        # 共振检测
        resonance = self.detect_resonance_peaks(frequencies, amplitudes)
        
        # 计算平均频率
        mean_freq = np.sum(frequencies * amplitudes) / np.sum(amplitudes) if np.sum(amplitudes) > 0 else 0
        
        return {
            'params': {
                'alpha': self.params.alpha,
                'beta': self.params.beta,
                'noise_level': self.params.noise_level,
                'dt': self.params.dt,
                'steps': self.params.steps
            },
            'spectral_width': spectral_width,
            'frequencies': frequencies,
            'amplitudes': amplitudes,
            'resonance': resonance,
            'mean_frequency': float(mean_freq),
            'evolution_history': self.get_evolution_history()
        }
