/**
 * Copyright 2026 NEMT Lab
 *
 * Strategy Integration
 *
 * Re-exports all strategy module utilities for convenient importing
 */

// Re-export from backtest module
export {
  BacktestEngineCore,
  runBacktest,
  type EngineConfig,
  type EngineState,
  type BacktestResult,
  type DataFrame,
  type Trade,
  type BacktestProgressCallback,
} from '../backtest/engineCore';

// Also export BacktestEngine as an alias for BacktestEngineCore
export { BacktestEngineCore as BacktestEngine } from '../backtest/engineCore';

// Re-export from interfaces
export type {
  IStrategy,
  NEMTStrategy,
  StrategyConfig,
  DataProvider,
  Trade as StrategyTrade,
} from '../interfaces/IStrategy';

// Re-export from templates
export {
  createNEMTStrategy,
  createRSIStrategy,
  createMACDStrategy,
} from '../templates/strategyTemplates';

// Re-export from indicators
export {
  calculateAllIndicators,
  calculateRSI,
  calculateMACD,
  calculateSMA,
  calculateEMA,
  calculateBollingerBands,
  calculateATR,
} from '../indicators/technicalIndicators';

// Re-export from exchange
export {
  BinanceAdapter,
  BinanceDataProvider,
} from '../exchange/binanceAdapter';

// Re-export from nemt calculator
export {
  NEMTStateCalculator,
} from '../nemt/nemtCalculator';

// Re-export from types
export {
  createDataFrame,
  dataFrameToKlines,
  type DataFrame,
  type KlineData,
} from '../types/kline';
