"""
NEMT Pipeline - Connect market data to NEMT Core
"""

import numpy as np
from typing import List, Optional, Dict, Any
from datetime import datetime

from .nls_solver import NLSSolver, NLSParams
from .phase_detector import PhaseDetector, MarketPhase
from .spectral_analyzer import SpectralAnalyzer
from .signal_generator import SignalGenerator, TradingSignal


class NEMTPipeline:
    """
    NEMT Processing Pipeline
    
    From market data to trading signals:
    1. Receive market data (KLines)
    2. Run NLS experiment
    3. Detect market phase
    4. Execute spectral analysis
    5. Generate trading signals
    """
    
    def __init__(
        self,
        nls_params: NLSParams = None,
        lookback_periods: int = 128,
        update_interval: int = 10
    ):
        self.nls_params = nls_params or NLSParams(steps=50)
        self.lookback_periods = lookback_periods
        self.update_interval = update_interval
        
        self.nls_solver = NLSSolver(nls_params)
        self.phase_detector = PhaseDetector()
        self.spectral_analyzer = SpectralAnalyzer()
        self.signal_generator = SignalGenerator()
        
        self.price_history: List[float] = []
        self.kline_history: List[Dict] = []
        self.current_phase = None
        self.prev_phase = None
        self.last_update_count = 0
        self._cached_result: Optional[Dict[str, Any]] = None
    
    def add_kline(self, kline: Dict[str, Any]) -> Optional[List[TradingSignal]]:
        """Add new K-line data"""
        if 'close' in kline:
            price = kline['close']
        elif 'price' in kline:
            price = kline['price']
        else:
            return None
        
        self.price_history.append(price)
        self.kline_history.append(kline)
        
        if len(self.price_history) > self.lookback_periods:
            self.price_history = self.price_history[-self.lookback_periods:]
            self.kline_history = self.kline_history[-self.lookback_periods:]
        
        self.last_update_count += 1
        
        if self.last_update_count >= self.update_interval and len(self.price_history) >= 32:
            signals = self._run_analysis()
            self.last_update_count = 0
            return signals
        
        return None
    
    def add_price(self, price: float, timestamp: datetime = None) -> Optional[List[TradingSignal]]:
        """Add price data"""
        kline = {
            'timestamp': timestamp or datetime.now(),
            'close': price,
            'price': price
        }
        return self.add_kline(kline)
    
    def _run_analysis(self) -> List[TradingSignal]:
        """Run complete analysis"""
        if len(self.price_history) < 32:
            return []
        
        self.prev_phase = self.current_phase
        
        price_array = np.array(self.price_history[-self.lookback_periods:])
        nls_result = self.nls_solver.run_experiment(price_array)
        
        phase_result = self.phase_detector.detect(
            spectral_width=nls_result['spectral_width'],
            resonance_peaks=nls_result['resonance']['num_peaks']
        )
        self.current_phase = phase_result.phase.value
        
        spectral_metrics = self.spectral_analyzer.analyze(
            signal=price_array,
            frequencies=nls_result.get('frequencies'),
            amplitudes=nls_result.get('amplitudes')
        )
        
        price = self.price_history[-1]
        prev_price = self.price_history[-2] if len(self.price_history) > 1 else price
        trend_price = np.mean(self.price_history[-20:]) if len(self.price_history) >= 20 else price
        
        signals = self.signal_generator.generate_all_signals(
            phase=self.current_phase,
            prev_phase=self.prev_phase or self.current_phase,
            spectral_width=nls_result['spectral_width'],
            coherence=spectral_metrics.coherence,
            resonance_peaks=nls_result['resonance']['num_peaks'],
            price=price,
            prev_price=prev_price,
            trend_price=trend_price,
            confidence=phase_result.confidence
        )
        
        self._cached_result = {
            'nls_result': nls_result,
            'phase_result': phase_result,
            'spectral_metrics': spectral_metrics,
            'signals': signals,
            'price': price,
            'timestamp': datetime.now()
        }
        
        return signals
    
    def get_current_state(self) -> Dict[str, Any]:
        """Get current market state"""
        if self._cached_result is None and len(self.price_history) >= 32:
            self._run_analysis()
        
        if self._cached_result is None:
            return {
                'phase': 'UNKNOWN',
                'phase_confidence': 0.0,
                'spectral_width': 0.0,
                'coherence': 0.0,
                'resonance_peaks': 0,
                'strategy': None,
                'recommendations': {}
            }
        
        phase_result = self._cached_result['phase_result']
        spectral_metrics = self._cached_result['spectral_metrics']
        strategy = self.phase_detector.get_phase_strategy(phase_result.phase)
        
        return {
            'phase': self.current_phase,
            'phase_confidence': phase_result.confidence,
            'phase_description': phase_result.description,
            'spectral_width': self._cached_result['nls_result']['spectral_width'],
            'coherence': spectral_metrics.coherence,
            'entropy': spectral_metrics.entropy,
            'resonance_peaks': self._cached_result['nls_result']['resonance']['num_peaks'],
            'mean_frequency': self._cached_result['nls_result']['mean_frequency'],
            'strategy': {
                'name': strategy.name,
                'strategy_text': strategy.strategy_text,
                'max_position': strategy.max_position,
                'leverage_allowed': strategy.leverage_allowed,
                'focus': strategy.focus_text,
                'avoid': strategy.avoid_text
            },
            'recommendations': {
                'position': self.phase_detector.get_recommended_position(phase_result.phase),
                'leverage': self.phase_detector.get_recommended_leverage(phase_result.phase)
            },
            'price': self._cached_result['price'],
            'timestamp': self._cached_result['timestamp']
        }
    
    def get_latest_signals(self, n: int = 10) -> List[TradingSignal]:
        """Get recent signals"""
        return self.signal_generator.get_latest_signals(n)
    
    def get_evolution_history(self) -> np.ndarray:
        """Get NLS evolution history"""
        return self.nls_solver.get_evolution_history()
    
    def reset(self):
        """Reset pipeline state"""
        self.price_history = []
        self.kline_history = []
        self.current_phase = None
        self.prev_phase = None
        self.last_update_count = 0
        self._cached_result = None
    
    def set_nls_params(self, **kwargs):
        """Update NLS parameters"""
        for key, value in kwargs.items():
            if hasattr(self.nls_params, key):
                setattr(self.nls_params, key, value)
        self.nls_solver = NLSSolver(self.nls_params)
        self._cached_result = None


class MultiSymbolPipeline:
    """Multi-symbol NEMT Pipeline"""
    
    def __init__(self, nls_params: NLSParams = None):
        self.nls_params = nls_params or NLSParams(steps=50)
        self.pipelines: Dict[str, NEMTPipeline] = {}
        self.subscribed_symbols: List[str] = []
    
    def add_symbol(self, symbol: str, lookback: int = 128) -> NEMTPipeline:
        """Add trading symbol"""
        pipeline = NEMTPipeline(
            nls_params=self.nls_params,
            lookback_periods=lookback
        )
        self.pipelines[symbol] = pipeline
        if symbol not in self.subscribed_symbols:
            self.subscribed_symbols.append(symbol)
        return pipeline
    
    def get_pipeline(self, symbol: str) -> Optional[NEMTPipeline]:
        """Get pipeline for symbol"""
        return self.pipelines.get(symbol)
    
    def add_price(self, symbol: str, price: float, timestamp: datetime = None) -> Optional[List[TradingSignal]]:
        """Add price for symbol"""
        if symbol not in self.pipelines:
            self.add_symbol(symbol)
        return self.pipelines[symbol].add_price(price, timestamp)
    
    def get_state(self, symbol: str) -> Dict[str, Any]:
        """Get state for symbol"""
        pipeline = self.pipelines.get(symbol)
        if pipeline:
            return pipeline.get_current_state()
        return {}
    
    def get_all_states(self) -> Dict[str, Dict[str, Any]]:
        """Get all symbol states"""
        return {
            symbol: pipeline.get_current_state()
            for symbol, pipeline in self.pipelines.items()
        }
    
    def remove_symbol(self, symbol: str):
        """Remove symbol"""
        if symbol in self.pipelines:
            del self.pipelines[symbol]
        if symbol in self.subscribed_symbols:
            self.subscribed_symbols.remove(symbol)
