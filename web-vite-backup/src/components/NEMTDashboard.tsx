/**
 * NEMT Dashboard Component
 * Real-time NEMT analysis visualization
 */

import React, { useState, useEffect, useCallback, useRef } from 'react';
import {
  NEMTPhase,
  NEMTSignalType,
  NEMTSignalDirection,
  NEMTState,
  NEMTTradingSignal,
  NEMTPipelineConfig,
  DEFAULT_NEMT_CONFIG
} from '../types/nemt';

interface NEMTDashboardProps {
  symbol?: string;
  marketService?: any;
}

// Phase colors
const PHASE_COLORS: Record<string, { bg: string; text: string; border: string }> = {
  PHASE_A_NOISE: { bg: '#fef3c7', text: '#92400e', border: '#f59e0b' },
  PHASE_B_VORTEX: { bg: '#dbeafe', text: '#1e40af', border: '#3b82f6' },
  PHASE_C_RESONANCE: { bg: '#d1fae5', text: '#065f46', border: '#10b981' },
  PHASE_D_TREND: { bg: '#ede9fe', text: '#5b21b6', border: '#8b5cf6' }
};

const PHASE_NAMES: Record<string, string> = {
  PHASE_A_NOISE: 'Noise',
  PHASE_B_VORTEX: 'Vortex',
  PHASE_C_RESONANCE: 'Resonance',
  PHASE_D_TREND: 'Trend'
};

// Mock NEMT Pipeline for frontend
class MockNEMTPipeline {
  private prices: number[] = [];
  private config: NEMTPipelineConfig;
  private state: NEMTState | null = null;
  private signals: NEMTTradingSignal[] = [];

  constructor(config: NEMTPipelineConfig = DEFAULT_NEMT_CONFIG) {
    this.config = config;
  }

  addPrice(price: number): NEMTTradingSignal[] {
    this.prices.push(price);
    if (this.prices.length > this.config.lookbackPeriods) {
      this.prices = this.prices.slice(-this.config.lookbackPeriods);
    }

    // Update state every updateInterval prices
    if (this.prices.length > 32 && this.prices.length % this.config.updateInterval === 0) {
      this.state = this.computeState(price);
      
      // Generate signals
      const newSignals = this.generateSignals();
      this.signals = [...this.signals, ...newSignals].slice(-20);
      return newSignals;
    }
    return [];
  }

  private computeState(price: number): NEMTState {
    // Simulate NEMT analysis
    const spectralWidth = Math.random() * 0.03;
    const coherence = Math.random();
    const entropy = Math.random();
    const resonancePeaks = Math.floor(Math.random() * 5);

    // Determine phase
    let phase: string;
    if (spectralWidth > 0.025) phase = NEMTPhase.PHASE_A_NOISE;
    else if (spectralWidth > 0.020) phase = NEMTPhase.PHASE_B_VORTEX;
    else if (spectralWidth > 0.015) phase = NEMTPhase.PHASE_C_RESONANCE;
    else phase = NEMTPhase.PHASE_D_TREND;

    const confidence = 0.5 + Math.random() * 0.5;

    return {
      phase,
      phaseConfidence: confidence,
      phaseDescription: `Spectral width: ${spectralWidth.toFixed(4)}`,
      spectralWidth,
      coherence,
      entropy,
      resonancePeaks,
      meanFrequency: Math.random() * 0.1,
      strategy: this.getStrategyForPhase(phase),
      recommendations: this.getRecommendationsForPhase(phase),
      price,
      timestamp: new Date().toISOString()
    };
  }

  private getStrategyForPhase(phase: string) {
    const strategies: Record<string, any> = {
      PHASE_A_NOISE: { name: 'Noise Phase', strategyText: 'Wait and observe', maxPosition: 0.1, leverageAllowed: 1, focus: 'Rest', avoid: 'Frequent trading' },
      PHASE_B_VORTEX: { name: 'Vortex Phase', strategyText: 'Range trading', maxPosition: 0.3, leverageAllowed: 2, focus: 'Support/Resistance', avoid: 'Breakout chasing' },
      PHASE_C_RESONANCE: { name: 'Resonance Phase', strategyText: 'Trend confirmation', maxPosition: 0.6, leverageAllowed: 3, focus: 'Direction', avoid: 'Counter-trend' },
      PHASE_D_TREND: { name: 'Trend Phase', strategyText: 'Hold trend', maxPosition: 1.0, leverageAllowed: 5, focus: 'Stop loss', avoid: 'Early exit' }
    };
    return strategies[phase] || strategies.PHASE_A_NOISE;
  }

  private getRecommendationsForPhase(phase: string) {
    const recs: Record<string, any> = {
      PHASE_A_NOISE: { position: 0.1, leverage: 1 },
      PHASE_B_VORTEX: { position: 0.3, leverage: 2 },
      PHASE_C_RESONANCE: { position: 0.6, leverage: 3 },
      PHASE_D_TREND: { position: 1.0, leverage: 5 }
    };
    return recs[phase] || recs.PHASE_A_NOISE;
  }

  private generateSignals(): NEMTTradingSignal[] {
    if (!this.state) return [];

    const signals: NEMTTradingSignal[] = [];
    const random = Math.random();

    if (random > 0.7) {
      signals.push({
        signalId: Math.random().toString(36).substr(2, 8),
        signalType: NEMTSignalType.VORTEX_BREAKOUT,
        direction: Math.random() > 0.5 ? NEMTSignalDirection.BULLISH : NEMTSignalDirection.BEARISH,
        confidence: 0.6 + Math.random() * 0.3,
        strength: 50 + Math.random() * 50,
        reason: 'Vortex breakout detected',
        price: this.state.price,
        phase: this.state.phase,
        metadata: { spectralWidth: this.state.spectralWidth },
        timestamp: new Date().toISOString()
      });
    }

    if (random > 0.8 && this.state.resonancePeaks > 2) {
      signals.push({
        signalId: Math.random().toString(36).substr(2, 8),
        signalType: NEMTSignalType.RESONANCE_TRIGGER,
        direction: NEMTSignalDirection.BULLISH,
        confidence: 0.7 + Math.random() * 0.2,
        strength: 60 + Math.random() * 40,
        reason: `Resonance trigger: ${this.state.resonancePeaks} peaks detected`,
        price: this.state.price,
        phase: this.state.phase,
        metadata: { peaks: this.state.resonancePeaks },
        timestamp: new Date().toISOString()
      });
    }

    return signals;
  }

  getState(): NEMTState | null {
    return this.state;
  }

  getSignals(count: number = 10): NEMTTradingSignal[] {
    return this.signals.slice(-count);
  }
}

export const NEMTDashboard: React.FC<NEMTDashboardProps> = ({ symbol: _symbol = 'BTCUSDT', marketService: _marketService }) => {
  const [pipeline] = useState(() => new MockNEMTPipeline(DEFAULT_NEMT_CONFIG));
  const [state, setState] = useState<NEMTState | null>(null);
  const [signals, setSignals] = useState<NEMTTradingSignal[]>([]);
  const [currentPrice, setCurrentPrice] = useState<number>(0);
  const [isRunning, setIsRunning] = useState<boolean>(false);
  const intervalRef = useRef<number | null>(null);

  // Start/stop simulation
  const toggleSimulation = useCallback(() => {
    if (isRunning) {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
      setIsRunning(false);
    } else {
      // Generate initial prices
      let basePrice = 67500;
      for (let i = 0; i < 150; i++) {
        const change = (Math.random() - 0.5) * 100;
        basePrice += change;
        pipeline.addPrice(basePrice);
      }
      setState(pipeline.getState());
      setSignals(pipeline.getSignals());

      // Start price updates
      intervalRef.current = setInterval(() => {
        const change = (Math.random() - 0.5) * 50;
        const newPrice = currentPrice + change || 67500 + (Math.random() - 0.5) * 200;
        setCurrentPrice(newPrice);
        
        const newSignals = pipeline.addPrice(newPrice);
        if (newSignals.length > 0) {
          setSignals(prev => [...prev, ...newSignals].slice(-20));
        }
        
        const currentState = pipeline.getState();
        if (currentState) {
          setState({ ...currentState, price: newPrice });
        }
      }, 1000);
      
      setIsRunning(true);
    }
  }, [isRunning, pipeline, currentPrice]);

  useEffect(() => {
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, []);

  const getPhaseColor = (phase: string) => {
    return PHASE_COLORS[phase] || PHASE_COLORS.PHASE_A_NOISE;
  };

  const formatPercent = (value: number) => {
    return (value * 100).toFixed(1) + '%';
  };

  return (
    <div style={{ padding: '20px', maxWidth: '1200px', margin: '0 auto' }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <div>
          <h2 style={{ margin: 0, color: '#1f2937' }}>NEMT Core Dashboard</h2>
          <p style={{ margin: '5px 0 0 0', color: '#6b7280', fontSize: '14px' }}>
            Non-Equilibrium Market Theory Analysis
          </p>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '15px' }}>
          <span style={{ fontSize: '24px', fontWeight: 'bold', color: '#10b981' }}>
            ${currentPrice.toFixed(2)}
          </span>
          <button
            onClick={toggleSimulation}
            style={{
              padding: '10px 20px',
              background: isRunning ? '#ef4444' : '#10b981',
              color: 'white',
              border: 'none',
              borderRadius: '8px',
              cursor: 'pointer',
              fontWeight: 'bold'
            }}
          >
            {isRunning ? 'Stop' : 'Start'}
          </button>
        </div>
      </div>

      {/* Phase Indicator */}
      {state && (
        <div
          style={{
            padding: '20px',
            borderRadius: '12px',
            marginBottom: '20px',
            background: getPhaseColor(state.phase).bg,
            border: `2px solid ${getPhaseColor(state.phase).border}`,
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '15px' }}>
            <div
              style={{
                width: '80px',
                height: '80px',
                borderRadius: '50%',
                background: getPhaseColor(state.phase).border,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: '32px',
                fontWeight: 'bold',
                color: 'white'
              }}
            >
              {state.phase === NEMTPhase.PHASE_A_NOISE ? 'A' :
               state.phase === NEMTPhase.PHASE_B_VORTEX ? 'B' :
               state.phase === NEMTPhase.PHASE_C_RESONANCE ? 'C' : 'D'}
            </div>
            <div>
              <h3 style={{ margin: 0, color: getPhaseColor(state.phase).text, fontSize: '24px' }}>
                {PHASE_NAMES[state.phase]}
              </h3>
              <p style={{ margin: '5px 0 0 0', color: getPhaseColor(state.phase).text, opacity: 0.8 }}>
                Confidence: {(state.phaseConfidence * 100).toFixed(1)}%
              </p>
              <p style={{ margin: '5px 0 0 0', color: getPhaseColor(state.phase).text, opacity: 0.8 }}>
                {state.phaseDescription}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Metrics Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '15px', marginBottom: '20px' }}>
        <MetricCard
          title="Spectral Width"
          value={state?.spectralWidth.toFixed(4) || '0.0000'}
          subtitle="Market coherence"
          color="#8b5cf6"
        />
        <MetricCard
          title="Coherence"
          value={formatPercent(state?.coherence || 0)}
          subtitle="Signal strength"
          color="#3b82f6"
        />
        <MetricCard
          title="Entropy"
          value={formatPercent(state?.entropy || 0)}
          subtitle="Chaos level"
          color="#f59e0b"
        />
        <MetricCard
          title="Resonance Peaks"
          value={state?.resonancePeaks.toString() || '0'}
          subtitle="Frequency peaks"
          color="#10b981"
        />
      </div>

      {/* Strategy Panel */}
      {state && (
        <div style={{ background: '#f9fafb', borderRadius: '12px', padding: '20px', marginBottom: '20px' }}>
          <h4 style={{ margin: '0 0 15px 0', color: '#374151' }}>Current Strategy</h4>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '15px' }}>
            <div>
              <p style={{ margin: 0, fontSize: '12px', color: '#6b7280' }}>Position</p>
              <p style={{ margin: '5px 0 0 0', fontSize: '20px', fontWeight: 'bold', color: '#1f2937' }}>
                {formatPercent(state.recommendations.position)}
              </p>
            </div>
            <div>
              <p style={{ margin: 0, fontSize: '12px', color: '#6b7280' }}>Max Leverage</p>
              <p style={{ margin: '5px 0 0 0', fontSize: '20px', fontWeight: 'bold', color: '#1f2937' }}>
                {state.recommendations.leverage}x
              </p>
            </div>
            <div>
              <p style={{ margin: 0, fontSize: '12px', color: '#6b7280' }}>Strategy</p>
              <p style={{ margin: '5px 0 0 0', fontSize: '14px', color: '#1f2937' }}>
                {state.strategy.strategyText}
              </p>
            </div>
          </div>
          <div style={{ marginTop: '15px', display: 'flex', gap: '20px' }}>
            <div style={{ flex: 1 }}>
              <p style={{ margin: 0, fontSize: '12px', color: '#10b981', fontWeight: 'bold' }}>Focus</p>
              <p style={{ margin: '5px 0 0 0', fontSize: '14px', color: '#374151' }}>{state.strategy.focus}</p>
            </div>
            <div style={{ flex: 1 }}>
              <p style={{ margin: 0, fontSize: '12px', color: '#ef4444', fontWeight: 'bold' }}>Avoid</p>
              <p style={{ margin: '5px 0 0 0', fontSize: '14px', color: '#374151' }}>{state.strategy.avoid}</p>
            </div>
          </div>
        </div>
      )}

      {/* Signals Panel */}
      <div style={{ background: '#f9fafb', borderRadius: '12px', padding: '20px' }}>
        <h4 style={{ margin: '0 0 15px 0', color: '#374151' }}>Recent Signals</h4>
        {signals.length === 0 ? (
          <p style={{ color: '#9ca3af', textAlign: 'center', padding: '20px' }}>
            No signals yet. Start simulation to generate signals.
          </p>
        ) : (
          <div style={{ maxHeight: '300px', overflowY: 'auto' }}>
            {signals.slice().reverse().map((signal, index) => (
              <SignalItem key={signal.signalId || index} signal={signal} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

// Metric Card Component
interface MetricCardProps {
  title: string;
  value: string;
  subtitle: string;
  color: string;
}

const MetricCard: React.FC<MetricCardProps> = ({ title, value, subtitle, color }) => (
  <div style={{
    background: 'white',
    borderRadius: '12px',
    padding: '15px',
    boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
    borderLeft: `4px solid ${color}`
  }}>
    <p style={{ margin: 0, fontSize: '12px', color: '#6b7280' }}>{title}</p>
    <p style={{ margin: '5px 0 0 0', fontSize: '24px', fontWeight: 'bold', color: '#1f2937' }}>{value}</p>
    <p style={{ margin: '5px 0 0 0', fontSize: '12px', color: '#9ca3af' }}>{subtitle}</p>
  </div>
);

// Signal Item Component
interface SignalItemProps {
  signal: NEMTTradingSignal;
}

const SignalItem: React.FC<SignalItemProps> = ({ signal }) => {
  const getDirectionColor = (dir: string) => {
    switch (dir) {
      case 'bullish': return '#10b981';
      case 'bearish': return '#ef4444';
      default: return '#6b7280';
    }
  };

  const getSignalIcon = (type: string) => {
    switch (type) {
      case 'vortex_breakout': return 'V';
      case 'resonance_trigger': return 'R';
      case 'trend_callback': return 'T';
      case 'phase_transition': return 'P';
      case 'noise_signal': return 'N';
      default: return '?';
    }
  };

  return (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      gap: '12px',
      padding: '12px',
      background: 'white',
      borderRadius: '8px',
      marginBottom: '8px',
      borderLeft: `3px solid ${getDirectionColor(signal.direction)}`
    }}>
      <div style={{
        width: '32px',
        height: '32px',
        borderRadius: '50%',
        background: getDirectionColor(signal.direction),
        color: 'white',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        fontWeight: 'bold',
        fontSize: '14px'
      }}>
        {getSignalIcon(signal.signalType)}
      </div>
      <div style={{ flex: 1 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span style={{ fontWeight: 'bold', color: '#374151' }}>
            {signal.signalType.replace('_', ' ')}
          </span>
          <span style={{ fontSize: '12px', color: '#9ca3af' }}>
            {new Date(signal.timestamp).toLocaleTimeString()}
          </span>
        </div>
        <p style={{ margin: '3px 0 0 0', fontSize: '13px', color: '#6b7280' }}>
          {signal.reason}
        </p>
        <div style={{ display: 'flex', gap: '15px', marginTop: '5px', fontSize: '12px' }}>
          <span>Confidence: {(signal.confidence * 100).toFixed(0)}%</span>
          <span>Strength: {signal.strength.toFixed(0)}</span>
          <span style={{ color: getDirectionColor(signal.direction), fontWeight: 'bold' }}>
            {signal.direction.toUpperCase()}
          </span>
        </div>
      </div>
    </div>
  );
};

export default NEMTDashboard;
