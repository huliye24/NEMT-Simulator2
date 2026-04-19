"""
NEMT Core Module
Non-Equilibrium Market Theory Core Implementation
"""

from .nls_solver import NLSSolver, NLSParams
from .phase_detector import PhaseDetector, MarketPhase, PhaseResult, PhaseStrategy, PHASE_STRATEGIES
from .spectral_analyzer import SpectralAnalyzer, SpectralMetrics
from .signal_generator import SignalGenerator, TradingSignal, SignalType, SignalDirection
from .emt_pipeline import NEMTPipeline, MultiSymbolPipeline

__all__ = [
    # NLS Solver
    'NLSSolver',
    'NLSParams',
    # Phase Detection
    'PhaseDetector',
    'MarketPhase',
    'PhaseResult',
    'PhaseStrategy',
    'PHASE_STRATEGIES',
    # Spectral Analysis
    'SpectralAnalyzer',
    'SpectralMetrics',
    # Signal Generation
    'SignalGenerator',
    'TradingSignal',
    'SignalType',
    'SignalDirection',
    # Pipeline
    'NEMTPipeline',
    'MultiSymbolPipeline'
]
