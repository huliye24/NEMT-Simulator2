"""
NLS Equation Solver
Nonlinear Schrodinger Equation: i*psi_t + alpha*psi_xx + beta*|psi|^2*psi = eta
"""

import numpy as np
from dataclasses import dataclass
from typing import List, Tuple


@dataclass
class NLSParams:
    """NLS equation parameters"""
    alpha: float = 0.5
    beta: float = 1.0
    noise_level: float = 0.1
    dt: float = 0.01
    dx: float = 1.0
    steps: int = 100


class Complex:
    """Complex number class"""
    
    def __init__(self, re: float = 0.0, im: float = 0.0):
        self.re = re
        self.im = im
    
    def abs(self) -> float:
        return np.sqrt(self.re ** 2 + self.im ** 2)
    
    def abs2(self) -> float:
        return self.re ** 2 + self.im ** 2
    
    def __add__(self, other: 'Complex') -> 'Complex':
        return Complex(self.re + other.re, self.im + other.im)
    
    def __sub__(self, other: 'Complex') -> 'Complex':
        return Complex(self.re - other.re, self.im - other.im)
    
    def __mul__(self, other) -> 'Complex':
        if isinstance(other, (int, float)):
            return Complex(self.re * other, self.im * other)
        return Complex(
            self.re * other.re - self.im * other.im,
            self.re * other.im + self.im * other.re
        )
    
    def __rmul__(self, scalar: float) -> 'Complex':
        return Complex(self.re * scalar, self.im * scalar)
    
    def __repr__(self) -> str:
        return f"Complex({self.re:.4f}+{self.im:.4f}j)"


class NLSSolver:
    """NLS Equation Solver"""
    
    def __init__(self, params: NLSParams = None):
        self.params = params or NLSParams()
        self.psi: List[Complex] = []
        self.psi_history: List[np.ndarray] = []
        self.N: int = 0
    
    def initialize_state(self, price_data: np.ndarray) -> np.ndarray:
        """Initialize market state"""
        n = len(price_data)
        
        mean = np.mean(price_data)
        std = np.std(price_data)
        
        if std > 0:
            normalized = (price_data - mean) / std
        else:
            normalized = np.zeros(n)
        
        self.psi = [Complex(float(x), 0.0) for x in normalized]
        self.N = n
        self.psi_history = [self._psi_abs()]
        
        return normalized
    
    def _psi_abs(self) -> np.ndarray:
        """Get current amplitude"""
        return np.array([p.abs() for p in self.psi])
    
    def _generate_noise(self, size: int) -> List[Complex]:
        """Generate Gaussian noise"""
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
        """Compute discrete Laplacian"""
        laplacian = [Complex() for _ in range(self.N)]
        dx2 = self.params.dx * self.params.dx
        
        for i in range(1, self.N - 1):
            laplacian[i] = (psi[i - 1] - Complex(2, 0) * psi[i] + psi[i + 1]) * (1 / dx2)
        
        laplacian[0] = (psi[1] - psi[0]) * (1 / self.params.dx)
        laplacian[self.N - 1] = (psi[self.N - 2] - psi[self.N - 1]) * (1 / self.params.dx)
        
        return laplacian
    
    def evolve(self, psi: List[Complex] = None, steps: int = None) -> List[Complex]:
        """Time evolution"""
        psi = psi if psi is not None else self.psi
        if not psi:
            raise ValueError("State not initialized")
        
        N = self.N
        steps = steps if steps is not None else self.params.steps
        alpha = self.params.alpha
        beta = self.params.beta
        dt = self.params.dt
        
        self.psi_history = [self._psi_abs()]
        state = [Complex(p.re, p.im) for p in psi]
        
        for t in range(steps):
            laplacian = self._compute_laplacian(state)
            nonlinear = [p * p.abs2() * beta for p in state]
            
            dpsi = []
            for i in range(N):
                term = laplacian[i] * alpha + nonlinear[i]
                dpsi.append(Complex(-term.im, term.re))
            
            noise = self._generate_noise(N)
            
            state = [state[i] + dpsi[i] * dt + noise[i] * dt for i in range(N)]
            
            if t % 10 == 0:
                self.psi_history.append(self._psi_abs())
        
        self.psi = state
        return self.psi
    
    def get_spectral_analysis(self) -> Tuple[np.ndarray, np.ndarray]:
        """Spectral analysis"""
        if not self.psi:
            raise ValueError("State not initialized")
        
        psi_real = np.array([p.re for p in self.psi])
        
        N = len(psi_real)
        next_pow2 = 2 ** int(np.ceil(np.log2(N)))
        if next_pow2 > N:
            psi_real = np.pad(psi_real, (0, next_pow2 - N), mode='constant')
        
        spectrum = np.fft.fft(psi_real)
        amplitudes = np.abs(spectrum)
        
        frequencies = np.fft.fftfreq(len(spectrum), d=self.params.dx)
        frequencies = np.fft.fftshift(frequencies)
        amplitudes = np.fft.fftshift(amplitudes)
        
        return frequencies, amplitudes
    
    def compute_spectral_width(self, frequencies: np.ndarray = None, amplitudes: np.ndarray = None) -> float:
        """Compute spectral width"""
        if frequencies is None or amplitudes is None:
            frequencies, amplitudes = self.get_spectral_analysis()
        
        mask = np.abs(frequencies) > 0.01
        freqs = frequencies[mask]
        amps = amplitudes[mask]
        
        if len(amps) == 0 or np.sum(amps) < 1e-10:
            return 0.02
        
        total_power = np.sum(amps)
        mean_freq = np.sum(freqs * amps) / total_power
        
        variance = np.sum((freqs - mean_freq) ** 2 * amps) / total_power
        
        result = np.sqrt(variance)
        
        if np.isnan(result) or result == 0:
            return 0.02
        
        return float(result)
    
    def detect_resonance_peaks(self, frequencies: np.ndarray = None, amplitudes: np.ndarray = None) -> dict:
        """Detect resonance peaks"""
        if frequencies is None or amplitudes is None:
            frequencies, amplitudes = self.get_spectral_analysis()
        
        mean = np.mean(amplitudes)
        
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
        """Get amplitude evolution history"""
        return np.array(self.psi_history)
    
    def run_experiment(self, price_data: np.ndarray) -> dict:
        """Run complete experiment"""
        normalized = self.initialize_state(price_data)
        psi_final = self.evolve()
        frequencies, amplitudes = self.get_spectral_analysis()
        spectral_width = self.compute_spectral_width(frequencies, amplitudes)
        resonance = self.detect_resonance_peaks(frequencies, amplitudes)
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
