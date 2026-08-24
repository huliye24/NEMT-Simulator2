/**
 * Copyright 2026 NEMT Lab
 *
 * DeepSeek AI Trading Strategy
 * 借鉴 nautilus_AItrader 的 AI 交易策略
 *
 * 功能：
 * - AI 市场分析
 * - 技术指标计算
 * - 信号生成
 * - 仓位管理
 */

import { EventEmitter } from 'events';
import { DeepSeekAnalyzer, DeepSeekConfig, MarketContext, TradingSignal, TechnicalAnalysis, ConfidenceLevel } from '../client/deepseekClient';
import { SentimentDataFetcher, SentimentResult } from '../sentiment/sentimentFetcher';
import { calculateRSI, calculateMACD, calculateBollingerBands, calculateSMA } from '../../strategy/indicators/technicalIndicators';
import { logger } from '../../trader/engine/logger';

// ============================================
// 策略配置
// ============================================

export interface AIStrategyConfig {
  // 交易对
  symbol: string;
  interval: string;

  // 资金
  equity: number;
  leverage: number;

  // 仓位
  baseUsdtAmount: number;
  highConfidenceMultiplier: number;
  mediumConfidenceMultiplier: number;
  lowConfidenceMultiplier: number;
  maxPositionRatio: number;
  minTradeAmount: number;

  // 技术指标
  smaPeriods: number[];
  rsiPeriod: number;
  macdFast: number;
  macdSlow: number;
  bbPeriod: number;
  bbStd: number;

  // AI 配置
  deepseekApiKey?: string;
  deepseekModel?: string;
  useLocalAI?: boolean;

  // 情绪配置
  sentimentEnabled: boolean;
  sentimentLookbackHours: number;

  // 风险管理
  minConfidenceToTrade: ConfidenceLevel;
  allowReversals: boolean;
  rsiExtremeThresholdUpper: number;
  rsiExtremeThresholdLower: number;
  rsiExtremeMultiplier: number;

  // 止损止盈
  enableAutoSLTP: boolean;
  slBufferPct: number;
  tpHighConfidencePct: number;
  tpMediumConfidencePct: number;
  tpLowConfidencePct: number;
}

const DEFAULT_CONFIG: Partial<AIStrategyConfig> = {
  equity: 10000,
  leverage: 10,
  baseUsdtAmount: 100,
  highConfidenceMultiplier: 1.5,
  mediumConfidenceMultiplier: 1.0,
  lowConfidenceMultiplier: 0.5,
  maxPositionRatio: 0.1,
  minTradeAmount: 0.001,
  smaPeriods: [3, 7, 15],
  rsiPeriod: 14,
  macdFast: 12,
  macdSlow: 26,
  bbPeriod: 20,
  bbStd: 2,
  deepseekModel: 'deepseek-chat',
  useLocalAI: true,
  sentimentEnabled: true,
  sentimentLookbackHours: 4,
  minConfidenceToTrade: 'MEDIUM',
  allowReversals: true,
  rsiExtremeThresholdUpper: 75,
  rsiExtremeThresholdLower: 25,
  rsiExtremeMultiplier: 0.7,
  enableAutoSLTP: true,
  slBufferPct: 0.001,
  tpHighConfidencePct: 0.03,
  tpMediumConfidencePct: 0.02,
  tpLowConfidencePct: 0.01,
};

// ============================================
// K线数据
// ============================================

export interface KLine {
  time: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

// ============================================
// AI 交易策略
// ============================================

export class DeepSeekAIStrategy extends EventEmitter {
  private config: AIStrategyConfig;
  private analyzer: DeepSeekAnalyzer | null = null;
  private sentimentFetcher: SentimentDataFetcher;
  private klines: KLine[] = [];
  private currentPosition: {
    direction: 'long' | 'short' | 'none';
    size: number;
    entryPrice: number;
  } = { direction: 'none', size: 0, entryPrice: 0 };
  private running: boolean = false;
  private lastSignal: TradingSignal | null = null;
  private barCount: number = 0;

  constructor(config: AIStrategyConfig) {
    super();
    this.config = { ...DEFAULT_CONFIG, ...config } as AIStrategyConfig;
    this.sentimentFetcher = new SentimentDataFetcher({
      enabled: this.config.sentimentEnabled,
      lookbackHours: this.config.sentimentLookbackHours,
    });

    // 初始化 AI 分析器
    if (this.config.deepseekApiKey && !this.config.useLocalAI) {
      this.analyzer = new DeepSeekAnalyzer({
        apiKey: this.config.deepseekApiKey,
        model: this.config.deepseekModel,
      });
    }
  }

  // -----------------------------------------
  // 生命周期
  // -----------------------------------------

  /** 初始化 */
  initialize(): void {
    logger.info(`[AIStrategy] Initialized for ${this.config.symbol}`);
    this.emit('initialized');
  }

  /** 启动 */
  start(): void {
    this.running = true;
    logger.info(`[AIStrategy] Started`);
    this.emit('started');
  }

  /** 停止 */
  stop(): void {
    this.running = false;
    logger.info(`[AIStrategy] Stopped`);
    this.emit('stopped');
  }

  // -----------------------------------------
  // 数据处理
  // -----------------------------------------

  /**
   * 更新 K 线数据
   */
  updateBar(bar: KLine): void {
    this.klines.push(bar);

    // 保持最近 100 根
    if (this.klines.length > 100) {
      this.klines.shift();
    }

    this.barCount++;

    // 每 15 根 K 线分析一次
    if (this.barCount % 15 === 0 && this.running) {
      this.analyze();
    }
  }

  /**
   * 更新持仓
   */
  updatePosition(direction: 'long' | 'short' | 'none', size: number, entryPrice: number): void {
    this.currentPosition = { direction, size, entryPrice };
  }

  // -----------------------------------------
  // 分析
  // -----------------------------------------

  /**
   * 执行市场分析
   */
  async analyze(): Promise<TradingSignal | null> {
    if (this.klines.length < 50) {
      logger.debug(`[AIStrategy] Not enough data: ${this.klines.length}/50`);
      return null;
    }

    try {
      // 计算技术指标
      const technical = this.calculateTechnicalIndicators();

      // 获取情绪数据
      const sentiment = this.sentimentFetcher.isEnabled()
        ? await this.sentimentFetcher.fetch()
        : this.getDefaultSentiment();

      // 构建市场上下文
      const context: MarketContext = {
        symbol: this.config.symbol,
        current_price: this.klines[this.klines.length - 1].close,
        timestamp: Date.now(),
        klines: this.klines.slice(-10),
        technical,
        sentiment,
        position: this.currentPosition.direction !== 'none' ? {
          direction: this.currentPosition.direction,
          size: this.currentPosition.size,
          entry_price: this.currentPosition.entryPrice,
          unrealized_pnl: this.calculateUnrealizedPnL(),
        } : undefined,
      };

      // 生成信号
      let signal: TradingSignal;

      if (this.analyzer) {
        signal = await this.analyzer.analyze(context);
      } else {
        signal = this.generateLocalSignal(context);
      }

      // 应用风险管理
      signal = this.applyRiskManagement(signal);

      this.lastSignal = signal;

      logger.info(
        `[AIStrategy] Signal: ${signal.signal} (${signal.confidence}) @ ${context.current_price.toFixed(2)}`
      );

      // 发送信号事件
      this.emit('signal', signal);

      return signal;
    } catch (error) {
      logger.error(`[AIStrategy] Analysis failed:`, error);
      return null;
    }
  }

  /**
   * 计算技术指标
   */
  private calculateTechnicalIndicators(): TechnicalAnalysis {
    const closes = this.klines.map((k) => k.close);
    const highs = this.klines.map((k) => k.high);
    const lows = this.klines.map((k) => k.low);
    const volumes = this.klines.map((k) => k.volume);

    const lastIdx = closes.length - 1;

    // SMA
    const sma3 = calculateSMA(closes, 3)[lastIdx] || 0;
    const sma7 = calculateSMA(closes, 7)[lastIdx] || 0;
    const sma15 = calculateSMA(closes, 15)[lastIdx] || 0;

    // 趋势判断
    const price = closes[lastIdx];
    let smaAlignment: 'bullish' | 'bearish' | 'neutral' = 'neutral';
    let overallTrend: '上涨趋势' | '下跌趋势' | '盘整' = '盘整';

    if (price > sma3 && sma3 > sma7 && sma7 > sma15) {
      smaAlignment = 'bullish';
      overallTrend = '上涨趋势';
    } else if (price < sma3 && sma3 < sma7 && sma7 < sma15) {
      smaAlignment = 'bearish';
      overallTrend = '下跌趋势';
    }

    // RSI
    const rsi = calculateRSI(closes, this.config.rsiPeriod)[lastIdx] || 50;

    // MACD
    const macd = calculateMACD(closes, this.config.macdFast, this.config.macdSlow);

    // 布林带
    const bb = calculateBollingerBands(closes, this.config.bbPeriod, this.config.bbStd);
    const bbUpper = bb.upper[lastIdx] || price;
    const bbMiddle = bb.middle[lastIdx] || price;
    const bbLower = bb.lower[lastIdx] || price;
    const bbPosition = bbUpper !== bbLower ? (price - bbLower) / (bbUpper - bbLower) : 0.5;

    // 支撑阻力
    const support = this.findSupport(this.klines);
    const resistance = this.findResistance(this.klines);

    // 成交量
    const currentVolume = volumes[lastIdx] || 0;
    const volumeSMA = calculateSMA(volumes, 20)[lastIdx] || 1;
    const volumeRatio = volumeSMA > 0 ? currentVolume / volumeSMA : 1;

    return {
      trend: {
        sma_3: sma3,
        sma_7: sma7,
        sma_15: sma15,
        sma_alignment: smaAlignment,
        overall_trend: overallTrend,
      },
      momentum: {
        rsi,
        rsi_normalized: rsi / 100,
        macd: {
          value: macd.macd[lastIdx] || 0,
          signal: macd.signal[lastIdx] || 0,
          histogram: macd.histogram[lastIdx] || 0,
        },
      },
      volatility: {
        bb_upper: bbUpper,
        bb_middle: bbMiddle,
        bb_lower: bbLower,
        bb_position: bbPosition,
      },
      support_resistance: {
        support,
        resistance,
      },
      volume: {
        current: currentVolume,
        sma: volumeSMA,
        ratio: volumeRatio,
      },
    };
  }

  /**
   * 查找支撑位
   */
  private findSupport(klines: KLine[]): number {
    const lows = klines.slice(-20).map((k) => k.low);
    return Math.min(...lows);
  }

  /**
   * 查找阻力位
   */
  private findResistance(klines: KLine[]): number {
    const highs = klines.slice(-20).map((k) => k.high);
    return Math.max(...highs);
  }

  // -----------------------------------------
  // 信号生成
  // -----------------------------------------

  /**
   * 生成本地信号 (无 AI API)
   */
  private generateLocalSignal(context: MarketContext): TradingSignal {
    const { technical } = context;
    const price = context.current_price;

    let score = 0;
    const reasons: string[] = [];

    // 趋势
    if (technical.trend.sma_alignment === 'bullish') {
      score += 0.25;
      reasons.push('SMA多头排列');
    } else if (technical.trend.sma_alignment === 'bearish') {
      score -= 0.25;
      reasons.push('SMA空头排列');
    }

    // RSI
    const rsi = technical.momentum.rsi;
    if (rsi < 30) {
      score += 0.2;
      reasons.push(`RSI超卖(${rsi.toFixed(1)})`);
    } else if (rsi > 70) {
      score -= 0.2;
      reasons.push(`RSI超买(${rsi.toFixed(1)})`);
    }

    // MACD
    if (technical.momentum.macd.histogram > 0) {
      score += 0.2;
      reasons.push('MACD柱正值');
    } else {
      score -= 0.2;
      reasons.push('MACD柱负值');
    }

    // 布林带
    const bbPos = technical.volatility.bb_position;
    if (bbPos < 0.2) {
      score += 0.15;
      reasons.push('触及布林下轨');
    } else if (bbPos > 0.8) {
      score -= 0.15;
      reasons.push('触及布林上轨');
    }

    // 成交量
    if (technical.volume.ratio > 1.5) {
      score += 0.1;
      reasons.push('成交量放大');
    }

    // 情绪
    const fg = context.sentiment.fear_greed_index;
    if (fg < 30) {
      score += 0.1;
      reasons.push('市场极度恐惧');
    } else if (fg > 70) {
      score -= 0.1;
      reasons.push('市场极度贪婪');
    }

    // 确定信号
    let signal: 'BUY' | 'SELL' | 'HOLD' = 'HOLD';
    if (score > 0.3) signal = 'BUY';
    else if (score < -0.3) signal = 'SELL';

    // 置信度
    let confidence: ConfidenceLevel = 'MEDIUM';
    const absScore = Math.abs(score);
    if (absScore > 0.5) confidence = 'HIGH';
    else if (absScore < 0.2) confidence = 'LOW';

    // 计算止盈止损
    let stopLoss: number | undefined;
    let takeProfit: number | undefined;

    if (signal === 'BUY') {
      stopLoss = price * (1 - this.config.slBufferPct);
      takeProfit = price * (1 + this.getTpPct(confidence));
    } else if (signal === 'SELL') {
      stopLoss = price * (1 + this.config.slBufferPct);
      takeProfit = price * (1 - this.getTpPct(confidence));
    }

    return {
      signal_id: `signal_${Date.now()}`,
      signal,
      confidence,
      confidence_score: Math.min(1, absScore + 0.5),
      reasoning: reasons.join('; ') || '信号不明确',
      stop_loss: stopLoss,
      take_profit: takeProfit,
      position_size_ratio: this.calculatePositionSize(confidence, Math.abs(score)),
      timestamp: Date.now(),
      ai_model: 'local_rule_based',
    };
  }

  /**
   * 应用风险管理
   */
  private applyRiskManagement(signal: TradingSignal): TradingSignal {
    const { minConfidenceToTrade, allowReversals, rsiExtremeThresholdUpper, rsiExtremeThresholdLower, rsiExtremeMultiplier } = this.config;
    const { technical, position } = this.getLastContext();

    // 置信度过滤
    const confidenceOrder: Record<ConfidenceLevel, number> = { LOW: 0, MEDIUM: 1, HIGH: 2 };
    if (confidenceOrder[signal.confidence] < confidenceOrder[minConfidenceToTrade]) {
      signal.signal = 'HOLD';
      signal.reasoning += ` (置信度低于${minConfidenceToTrade})`;
    }

    // RSI 极端值调整
    const rsi = technical?.momentum.rsi || 50;
    if (rsi > rsiExtremeThresholdUpper || rsi < rsiExtremeThresholdLower) {
      signal.position_size_ratio = (signal.position_size_ratio || 0.1) * rsiExtremeMultiplier;
      signal.reasoning += ' (RSI极端值,降低仓位)';
    }

    // 持仓反转检查
    if (position && position.direction !== 'none' && signal.signal !== 'HOLD') {
      const positionSignal = position.direction === 'long' ? 'BUY' : 'SELL';
      if (signal.signal !== positionSignal && signal.confidence !== 'HIGH') {
        signal.signal = 'HOLD';
        signal.reasoning += ' (反转需高置信度)';
      }
    }

    return signal;
  }

  private getLastContext(): { technical?: TechnicalAnalysis; sentiment?: SentimentResult; position?: { direction: 'long' | 'short' | 'none' } } {
    return {
      technical: this.klines.length > 0 ? this.calculateTechnicalIndicators() : undefined,
      position: this.currentPosition,
    };
  }

  // -----------------------------------------
  // 仓位计算
  // -----------------------------------------

  /**
   * 计算仓位大小
   */
  calculatePositionSize(confidence: ConfidenceLevel, trendStrength: number): number {
    let size = this.config.baseUsdtAmount;

    switch (confidence) {
      case 'HIGH':
        size *= this.config.highConfidenceMultiplier;
        break;
      case 'MEDIUM':
        size *= this.config.mediumConfidenceMultiplier;
        break;
      case 'LOW':
        size *= this.config.lowConfidenceMultiplier;
        break;
    }

    // 趋势强度调整
    size *= Math.min(1.2, trendStrength + 0.8);

    // 最大仓位限制
    const maxSize = this.config.equity * this.config.maxPositionRatio;
    size = Math.min(size, maxSize);

    // 最小交易限制
    if (size < this.config.minTradeAmount * this.klines[this.klines.length - 1]?.close) {
      size = 0;
    }

    return size / this.config.equity;
  }

  /**
   * 计算未实现盈亏
   */
  private calculateUnrealizedPnL(): number {
    if (this.currentPosition.direction === 'none') return 0;

    const currentPrice = this.klines[this.klines.length - 1]?.close || 0;
    const entryPrice = this.currentPosition.entryPrice;

    if (this.currentPosition.direction === 'long') {
      return (currentPrice - entryPrice) / entryPrice * this.currentPosition.size;
    } else {
      return (entryPrice - currentPrice) / entryPrice * this.currentPosition.size;
    }
  }

  /**
   * 获取止盈百分比
   */
  private getTpPct(confidence: ConfidenceLevel): number {
    switch (confidence) {
      case 'HIGH':
        return this.config.tpHighConfidencePct;
      case 'MEDIUM':
        return this.config.tpMediumConfidencePct;
      case 'LOW':
        return this.config.tpLowConfidencePct;
    }
  }

  // -----------------------------------------
  // 状态查询
  // -----------------------------------------

  getConfig(): AIStrategyConfig {
    return { ...this.config };
  }

  getLastSignal(): TradingSignal | null {
    return this.lastSignal;
  }

  getPosition(): typeof this.currentPosition {
    return { ...this.currentPosition };
  }

  getKlines(): KLine[] {
    return [...this.klines];
  }

  isRunning(): boolean {
    return this.running;
  }
}
