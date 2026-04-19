"""
谱分析器 (Spectral Analyzer)
对 NLS 演化结果进行频谱分析
"""

import numpy as np
from typing import List, Tuple, Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class SpectralMetrics:
    """谱分析指标"""
    spectral_width: float
    mean_frequency: float
    dominant_frequency: float
    peak_count: int
    peak_frequencies: List[float]
    peak_amplitudes: List[float]
    coherence: float  # 相干性 0-1
    entropy: float  # 谱熵


class SpectralAnalyzer:
    """
    谱分析器
    
    功能：
    1. FFT 频谱计算
    2. 谱宽计算
    3. 共振峰检测
    4. 相干性分析
    5. 谱熵计算
    """
    
    def __init__(self, sample_rate: float = 1.0):
        """
        Args:
            sample_rate: 采样率
        """
        self.sample_rate = sample_rate
    
    def compute_fft(self, signal: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        计算 FFT
        
        Args:
            signal: 输入信号
            
        Returns:
            (frequencies, amplitudes) 频率和幅度
        """
        n = len(signal)
        
        # 补零到2的幂次
        next_pow2 = 2 ** int(np.ceil(np.log2(n)))
        if next_pow2 > n:
            signal = np.pad(signal, (0, next_pow2 - n), mode='constant')
        
        # FFT
        spectrum = np.fft.fft(signal)
        amplitudes = np.abs(spectrum)
        
        # 频率轴
        frequencies = np.fft.fftfreq(len(spectrum), d=1.0 / self.sample_rate)
        
        # 只取正频率部分
        pos_mask = frequencies >= 0
        frequencies = frequencies[pos_mask]
        amplitudes = amplitudes[pos_mask]
        
        # 归一化
        if np.max(amplitudes) > 0:
            amplitudes = amplitudes / np.max(amplitudes)
        
        return frequencies, amplitudes
    
    def compute_spectral_width(
        self,
        frequencies: np.ndarray,
        amplitudes: np.ndarray
    ) -> float:
        """
        计算谱宽
        
        使用加权标准差
        """
        if len(amplitudes) == 0 or np.sum(amplitudes) < 1e-10:
            return 0.0
        
        # 排除直流分量
        mask = frequencies > 0.001
        freqs = frequencies[mask]
        amps = amplitudes[mask]
        
        if len(amps) == 0:
            return 0.0
        
        # 总功率
        total_power = np.sum(amps ** 2)
        if total_power < 1e-10:
            return 0.0
        
        # 加权平均频率
        mean_freq = np.sum(freqs * amps ** 2) / total_power
        
        # 加权方差
        variance = np.sum((freqs - mean_freq) ** 2 * amps ** 2) / total_power
        
        return float(np.sqrt(variance))
    
    def find_peaks(
        self,
        frequencies: np.ndarray,
        amplitudes: np.ndarray,
        threshold: float = 0.3
    ) -> Tuple[List[float], List[float]]:
        """
        寻找谱峰
        
        Args:
            frequencies: 频率
            amplitudes: 幅度
            threshold: 峰值阈值（相对于最大值）
            
        Returns:
            (peak_frequencies, peak_amplitudes)
        """
        threshold_value = threshold * np.max(amplitudes)
        
        peaks_freq = []
        peaks_amp = []
        
        for i in range(1, len(amplitudes) - 1):
            # 局部最大值
            if amplitudes[i] > amplitudes[i - 1] and amplitudes[i] > amplitudes[i + 1]:
                # 高于阈值
                if amplitudes[i] > threshold_value:
                    peaks_freq.append(float(frequencies[i]))
                    peaks_amp.append(float(amplitudes[i]))
        
        return peaks_freq, peaks_amp
    
    def compute_coherence(
        self,
        frequencies: np.ndarray,
        amplitudes: np.ndarray
    ) -> float:
        """
        计算相干性
        
        基于频谱的集中程度
        """
        if len(amplitudes) == 0:
            return 0.0
        
        # 使用前几个主要频率分量的功率占比
        total_power = np.sum(amplitudes ** 2)
        if total_power < 1e-10:
            return 0.0
        
        # 排序幅度
        sorted_amps = np.sort(amplitudes)[::-1]
        n_top = min(5, len(sorted_amps))
        top_power = np.sum(sorted_amps[:n_top] ** 2)
        
        coherence = top_power / total_power
        
        return float(np.clip(coherence, 0, 1))
    
    def compute_entropy(
        self,
        frequencies: np.ndarray,
        amplitudes: np.ndarray
    ) -> float:
        """
        计算谱熵
        
        熵越高表示频谱越均匀（噪声特征）
        熵越低表示频谱越集中（相干特征）
        """
        if len(amplitudes) == 0:
            return 0.0
        
        # 归一化为概率分布
        total = np.sum(amplitudes) + 1e-10
        p = amplitudes / total
        
        # 计算熵
        entropy = -np.sum(p * np.log2(p + 1e-10))
        
        # 归一化
        max_entropy = np.log2(len(amplitudes) + 1)
        normalized_entropy = entropy / max_entropy if max_entropy > 0 else 0
        
        return float(normalized_entropy)
    
    def analyze(
        self,
        signal: np.ndarray,
        frequencies: np.ndarray = None,
        amplitudes: np.ndarray = None
    ) -> SpectralMetrics:
        """
        完整谱分析
        
        Args:
            signal: 输入信号
            frequencies: 可选，预计算的频率
            amplitudes: 可选，预计算的幅度
            
        Returns:
            SpectralMetrics: 谱分析指标
        """
        # 计算 FFT
        if frequencies is None or amplitudes is None:
            frequencies, amplitudes = self.compute_fft(signal)
        
        # 谱宽
        spectral_width = self.compute_spectral_width(frequencies, amplitudes)
        
        # 平均频率
        if np.sum(amplitudes) > 0:
            mean_frequency = np.sum(frequencies * amplitudes) / np.sum(amplitudes)
        else:
            mean_frequency = 0.0
        
        # 主频率
        dominant_idx = np.argmax(amplitudes)
        dominant_frequency = float(frequencies[dominant_idx]) if len(frequencies) > 0 else 0.0
        
        # 峰值
        peak_freqs, peak_amps = self.find_peaks(frequencies, amplitudes)
        
        # 相干性
        coherence = self.compute_coherence(frequencies, amplitudes)
        
        # 谱熵
        entropy = self.compute_entropy(frequencies, amplitudes)
        
        return SpectralMetrics(
            spectral_width=spectral_width,
            mean_frequency=mean_frequency,
            dominant_frequency=dominant_frequency,
            peak_count=len(peak_freqs),
            peak_frequencies=peak_freqs,
            peak_amplitudes=peak_amps,
            coherence=coherence,
            entropy=entropy
        )
    
    def analyze_from_psi(self, psi: List) -> SpectralMetrics:
        """
        从复振幅序列分析
        
        Args:
            psi: 复振幅列表
            
        Returns:
            SpectralMetrics
        """
        # 提取振幅
        amplitudes = np.array([abs(p) if hasattr(p, 'abs') else abs(complex(p)) for p in psi])
        
        return self.analyze(amplitudes)
