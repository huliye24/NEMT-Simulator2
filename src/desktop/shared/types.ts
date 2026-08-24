// NEMT Simulator - Shared Type Definitions
// Types used across Electron Main, Preload, and Renderer

export interface Strategy {
  id: string;
  name: string;
  author: string;
  type: StrategyType;
  code: string;
  sharpeRatio: number;
  maxDrawdown: number;
  totalTrades: number;
  winRate: number;
  status: StrategyStatus;
  createdAt: number;
  updatedAt: number;
}

export enum StrategyType {
  TREND_FOLLOWING = 'TREND_FOLLOWING',
  MEAN_REVERSION = 'MEAN_REVERSION',
  ARBITRAGE = 'ARBITRAGE',
  MARKET_MAKING = 'MARKET_MAKING',
  ML_BASED = 'ML_BASED',
}

export enum StrategyStatus {
  DRAFT = 'DRAFT',
  ACTIVE = 'ACTIVE',
  PAUSED = 'PAUSED',
  ARCHIVED = 'ARCHIVED',
}

export interface Capsule {
  id: string;
  name: string;
  version: string;
  author: string;
  type: CapsuleType;
  code: string;
  dependencies: string[];
  createdAt: number;
  updatedAt: number;
}

export enum CapsuleType {
  MARKET = 'MARKET',
  SIGNAL = 'SIGNAL',
  RISK = 'RISK',
  EXECUTION = 'EXECUTION',
  BRAIN = 'BRAIN',
  MONITOR = 'MONITOR',
}

export interface BacktestRequest {
  strategyId: string;
  dataSource: string;
  symbol: string;
  interval: string;
  startTime: number;
  endTime: number;
  initialCapital: number;
}

export interface BacktestResult {
  barIndex: number;
  equity: number;
  position: number;
  pnl: number;
  drawdown: number;
}

export interface MarketData {
  symbol: string;
  timestamp: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface TickerData {
  symbol: string;
  price: number;
  change: number;
  changePercent: number;
  volume: number;
  timestamp: number;
}

export interface PythonStatus {
  running: boolean;
  error?: string;
  code?: number;
  signal?: string;
}

export interface SystemStats {
  memory: number;
  cpu: number;
  platform: string;
}

export interface GatewayHealth {
  status: string;
  version: string;
  uptime: number;
  services: {
    gateway: boolean;
    collector: boolean;
    scheduler: boolean;
  };
}

// IPC Channel Names
export const IPC_CHANNELS = {
  // Gateway
  GATEWAY_HEALTH: 'gateway:health',
  GATEWAY_LIST_STRATEGIES: 'gateway:listStrategies',
  GATEWAY_GET_STRATEGY: 'gateway:getStrategy',
  GATEWAY_CREATE_STRATEGY: 'gateway:createStrategy',
  GATEWAY_UPDATE_STRATEGY: 'gateway:updateStrategy',
  GATEWAY_DELETE_STRATEGY: 'gateway:deleteStrategy',
  GATEWAY_LIST_CAPSULE: 'gateway:listCapsules',
  GATEWAY_REGISTER_CAPSULE: 'gateway:registerCapsule',
  GATEWAY_START_BACKTEST: 'gateway:startBacktest',
  GATEWAY_GET_BACKTEST: 'gateway:getBacktest',
  GATEWAY_GET_MARKET_DATA: 'gateway:getMarketData',

  // Python
  PYTHON_EXECUTE: 'python:execute',
  PYTHON_STATUS: 'python:status',
  PYTHON_LOG: 'python:log',
  PYTHON_ERROR: 'python:error',

  // Window
  WINDOW_MINIMIZE: 'window:minimize',
  WINDOW_MAXIMIZE: 'window:maximize',
  WINDOW_CLOSE: 'window:close',
  WINDOW_IS_MAXIMIZED: 'window:isMaximized',

  // App
  APP_GET_VERSION: 'app:getVersion',

  // File
  FILE_OPEN: 'file:open',
  FILE_SAVE: 'file:save',
  FILE_EXPORT: 'file:export',

  // WebSocket
  WS_CONNECT: 'ws:connect',
  WS_DISCONNECT: 'ws:disconnect',
  WS_SUBSCRIBE: 'ws:subscribe',
  WS_UNSUBSCRIBE: 'ws:unsubscribe',
  WS_TICKER: 'ws:ticker',

  // Menu Events
  MENU_NEW_SIMULATION: 'menu:newSimulation',
  MENU_SAVE: 'menu:save',
  MENU_RUN_SIMULATION: 'menu:runSimulation',
  MENU_STOP_SIMULATION: 'menu:stopSimulation',
  MENU_SETTINGS: 'menu:settings',
  MENU_THEORY_DOCS: 'menu:theoryDocs',
  MENU_API_DOCS: 'menu:apiDocs',
  MENU_EXPORT: 'menu:export',
  MENU_NOISE_SCAN: 'menu:noiseScan',
  MENU_NONLINEAR_ANALYSIS: 'menu:nonlinearAnalysis',
  MENU_FULL_PIPELINE: 'menu:fullPipeline',

  // Market
  MARKET_TICKER: 'market:ticker',
} as const;

// Service Ports
export const SERVICE_PORTS = {
  GATEWAY_HTTP: 8080,
  GATEWAY_GRPC: 9090,
  PYTHON_GRPC: 50051,
} as const;
