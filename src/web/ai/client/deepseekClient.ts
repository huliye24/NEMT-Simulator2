/**
 * Copyright 2026 NEMT Lab
 *
 * DeepSeek AI Client
 * 借鉴 nautilus_AItrader deepseek_client.py
 *
 * 功能：
 * - AI 市场分析
 * - 交易信号生成
 * - 技术指标 + 情绪数据综合分析
 */

import { logger } from '../../trader/engine/logger';

// ============================================
// 类型定义
// ============================================

export interface TechnicalAnalysis {
  trend: {
    sma_3: number;
    sma_7: number;
    sma_15: number;
    sma_alignment: 'bullish' | 'bearish' | 'neutral';
    overall_trend: '上涨趋势' | '下跌趋势' | '盘整';
  };
  momentum: {
    rsi: number;
    rsi_normalized: number;
    macd: {
      value: number;
      signal: number;
      histogram: number;
    };
  };
  volatility: {
    bb_upper: number;
    bb_middle: number;
    bb_lower: number;
    bb_position: number;
  };
  support_resistance: {
    support: number;
    resistance: number;
  };
  volume: {
    current: number;
    sma: number;
    ratio: number;
  };
}

export interface SentimentData {
  fear_greed_index: number;
  sentiment_label: '极度恐惧' | '恐惧' | '中性' | '贪婪' | '极度贪婪';
  social_volume: number;
  trend: 'positive' | 'negative' | 'neutral';
}

export interface MarketContext {
  symbol: string;
  current_price: number;
  timestamp: number;
  klines: Array<{
    open: number;
    high: number;
    low: number;
    close: number;
    volume: number;
    time: number;
  }>;
  technical: TechnicalAnalysis;
  sentiment: SentimentData;
  position?: {
    direction: 'long' | 'short' | 'none';
    size: number;
    entry_price: number;
    unrealized_pnl: number;
  };
}

export type ConfidenceLevel = 'HIGH' | 'MEDIUM' | 'LOW';

export interface TradingSignal {
  signal_id: string;
  signal: 'BUY' | 'SELL' | 'HOLD';
  confidence: ConfidenceLevel;
  confidence_score: number;
  reasoning: string;
  target_price?: number;
  stop_loss?: number;
  take_profit?: number;
  position_size_ratio?: number;
  timestamp: number;
  ai_model: string;
}

// ============================================
// DeepSeek AI 分析器
// ============================================

export interface DeepSeekConfig {
  apiKey: string;
  model?: string;
  temperature?: number;
  maxRetries?: number;
  baseUrl?: string;
}

export class DeepSeekAnalyzer {
  private apiKey: string;
  private model: string;
  private temperature: number;
  private maxRetries: number;
  private baseUrl: string;

  private signalHistory: TradingSignal[] = [];

  constructor(config: DeepSeekConfig) {
    this.apiKey = config.apiKey;
    this.model = config.model || 'deepseek-chat';
    this.temperature = config.temperature || 0.1;
    this.maxRetries = config.maxRetries || 2;
    this.baseUrl = config.baseUrl || 'https://api.deepseek.com';
  }

  // -----------------------------------------
  // 生成交易信号
  // -----------------------------------------

  /**
   * 分析市场并生成交易信号
   */
  async analyze(marketContext: MarketContext): Promise<TradingSignal> {
    const prompt = this.buildPrompt(marketContext);
    const signal = await this.callAPI(prompt, marketContext);

    // 保存历史
    this.signalHistory.push(signal);
    if (this.signalHistory.length > 100) {
      this.signalHistory.shift();
    }

    return signal;
  }

  /**
   * 同步分析 (用于回测)
   */
  analyzeSync(marketContext: MarketContext): TradingSignal {
    const prompt = this.buildPrompt(marketContext);
    return this.generateLocalSignal(prompt, marketContext);
  }

  /**
   * 获取信号历史
   */
  getSignalHistory(): TradingSignal[] {
    return this.signalHistory;
  }

  // -----------------------------------------
  // 构建 Prompt
  // -----------------------------------------

  private buildPrompt(context: MarketContext): string {
    const { technical, sentiment, position, current_price } = context;

    const klinesStr = context.klines
      .slice(-10)
      .map(
        (k, i) =>
          `K${i + 1}: O=${k.open.toFixed(2)} H=${k.high.toFixed(2)} L=${k.low.toFixed(2)} C=${k.close.toFixed(2)} V=${k.volume.toFixed(2)}`
      )
      .join('\n');

    const positionStr = position
      ? `当前持仓: ${position.direction} ${position.size} @ ${position.entry_price.toFixed(2)}, 未实现盈亏: ${position.unrealized_pnl.toFixed(2)}`
      : '当前无持仓';

    const prompt = `
# 市场分析请求

## 当前市场状态
- 交易对: ${context.symbol}
- 当前价格: ${current_price.toFixed(2)}
- 时间: ${new Date(context.timestamp).toISOString()}

## 最近10根K线
${klinesStr}

## 技术分析
- 趋势:
  - SMA(3): ${technical.trend.sma_3.toFixed(2)}
  - SMA(7): ${technical.trend.sma_7.toFixed(2)}
  - SMA(15): ${technical.trend.sma_15.toFixed(2)}
  - 趋势判断: ${technical.trend.overall_trend}
  - SMA排列: ${technical.trend.sma_alignment}

- 动量:
  - RSI(14): ${technical.momentum.rsi.toFixed(2)}
  - MACD: ${technical.momentum.macd.value.toFixed(2)}
  - MACD Signal: ${technical.momentum.macd.signal.toFixed(2)}
  - MACD Histogram: ${technical.momentum.macd.histogram.toFixed(2)}

- 波动率 (布林带20,2σ):
  - 上轨: ${technical.volatility.bb_upper.toFixed(2)}
  - 中轨: ${technical.volatility.bb_middle.toFixed(2)}
  - 下轨: ${technical.volatility.bb_lower.toFixed(2)}
  - 位置: ${(technical.volatility.bb_position * 100).toFixed(1)}%

- 支撑/阻力:
  - 支撑位: ${technical.support_resistance.support.toFixed(2)}
  - 阻力位: ${technical.support_resistance.resistance.toFixed(2)}

- 成交量:
  - 当前: ${technical.volume.current.toFixed(2)}
  - MA: ${technical.volume.sma.toFixed(2)}
  - 比率: ${technical.volume.ratio.toFixed(2)}

## 情绪数据
- 恐惧贪婪指数: ${sentiment.fear_greed_index}/100 (${sentiment.sentiment_label})
- 社交量: ${sentiment.social_volume}
- 趋势: ${sentiment.trend}

## 持仓状态
${positionStr}

## 任务
基于以上数据,生成交易信号。请输出JSON格式:
{
  "signal": "BUY|SELL|HOLD",
  "confidence": "HIGH|MEDIUM|LOW",
  "confidence_score": 0-1,
  "reasoning": "分析理由(中文)",
  "target_price": 目标价格(可选),
  "stop_loss": 止损价格(可选),
  "take_profit": 止盈价格(可选),
  "position_size_ratio": 仓位比例0-1(可选)
}

只输出JSON,不要其他内容。
`.trim();

    return prompt;
  }

  // -----------------------------------------
  // API 调用
  // -----------------------------------------

  private async callAPI(
    prompt: string,
    context: MarketContext
  ): Promise<TradingSignal> {
    let lastError: Error | null = null;

    for (let attempt = 0; attempt < this.maxRetries; attempt++) {
      try {
        return await this.executeRequest(prompt, context);
      } catch (error) {
        lastError = error as Error;
        logger.warning(`DeepSeek API attempt ${attempt + 1} failed: ${lastError.message}`);
        await this.delay(1000 * (attempt + 1));
      }
    }

    logger.error(`DeepSeek API failed after ${this.maxRetries} attempts`);
    return this.generateFallbackSignal(context, lastError?.message);
  }

  private async executeRequest(
    prompt: string,
    context: MarketContext
  ): Promise<TradingSignal> {
    const response = await fetch(`${this.baseUrl}/chat/completions`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${this.apiKey}`,
      },
      body: JSON.stringify({
        model: this.model,
        messages: [
          {
            role: 'system',
            content:
              '你是一个专业的加密货币交易分析师。基于技术指标和市场情绪,生成交易信号。',
          },
          { role: 'user', content: prompt },
        ],
        temperature: this.temperature,
        max_tokens: 500,
      }),
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }

    const data = await response.json();
    const content = data.choices?.[0]?.message?.content || '{}';

    return this.parseSignal(content, context);
  }

  // -----------------------------------------
  // 信号解析
  // -----------------------------------------

  private parseSignal(
    content: string,
    context: MarketContext
  ): TradingSignal {
    try {
      // 尝试提取 JSON
      const jsonMatch = content.match(/\{[\s\S]*\}/);
      if (!jsonMatch) {
        return this.generateFallbackSignal(context, 'No JSON found');
      }

      const parsed = JSON.parse(jsonMatch[0]);

      return {
        signal_id: `signal_${Date.now()}`,
        signal: this.normalizeSignal(parsed.signal),
        confidence: this.normalizeConfidence(parsed.confidence),
        confidence_score: Math.min(1, Math.max(0, parseFloat(parsed.confidence_score) || 0.5)),
        reasoning: parsed.reasoning || 'No reasoning provided',
        target_price: parsed.target_price
          ? parseFloat(parsed.target_price)
          : undefined,
        stop_loss: parsed.stop_loss ? parseFloat(parsed.stop_loss) : undefined,
        take_profit: parsed.take_profit ? parseFloat(parsed.take_profit) : undefined,
        position_size_ratio: parsed.position_size_ratio
          ? Math.min(1, Math.max(0, parseFloat(parsed.position_size_ratio)))
          : undefined,
        timestamp: Date.now(),
        ai_model: this.model,
      };
    } catch (error) {
      return this.generateFallbackSignal(context, (error as Error).message);
    }
  }

  private normalizeSignal(signal: string): 'BUY' | 'SELL' | 'HOLD' {
    const s = signal?.toUpperCase();
    if (s === 'BUY' || s === '做多' || s === '买入') return 'BUY';
    if (s === 'SELL' || s === '做空' || s === '卖出') return 'SELL';
    return 'HOLD';
  }

  private normalizeConfidence(conf: string): ConfidenceLevel {
    const c = conf?.toUpperCase();
    if (c === 'HIGH' || c === '高') return 'HIGH';
    if (c === 'MEDIUM' || c === '中') return 'MEDIUM';
    return 'LOW';
  }

  // -----------------------------------------
  // 本地信号生成 (同步/回测)
  // -----------------------------------------

  private generateLocalSignal(
    prompt: string,
    context: MarketContext
  ): TradingSignal {
    const { technical, sentiment, position } = context;
    const price = context.current_price;

    // 基于规则的本地分析
    let score = 0;
    let reasons: string[] = [];

    // 趋势分析
    if (technical.trend.sma_alignment === 'bullish') {
      score += 0.2;
      reasons.push('SMA多头排列');
    } else if (technical.trend.sma_alignment === 'bearish') {
      score -= 0.2;
      reasons.push('SMA空头排列');
    }

    // RSI 分析
    if (technical.momentum.rsi < 30) {
      score += 0.15;
      reasons.push('RSI超卖');
    } else if (technical.momentum.rsi > 70) {
      score -= 0.15;
      reasons.push('RSI超买');
    }

    // MACD 分析
    if (technical.momentum.macd.histogram > 0) {
      score += 0.15;
      reasons.push('MACD柱正值');
    } else {
      score -= 0.15;
      reasons.push('MACD柱负值');
    }

    // 布林带位置
    if (technical.volatility.bb_position < 0.2) {
      score += 0.1;
      reasons.push('价格触及布林下轨');
    } else if (technical.volatility.bb_position > 0.8) {
      score -= 0.1;
      reasons.push('价格触及布林上轨');
    }

    // 情绪分析
    if (sentiment.fear_greed_index < 30) {
      score += 0.1;
      reasons.push('市场极度恐惧');
    } else if (sentiment.fear_greed_index > 70) {
      score -= 0.1;
      reasons.push('市场极度贪婪');
    }

    // 成交量
    if (technical.volume.ratio > 1.5) {
      score += 0.1;
      reasons.push('成交量放大');
    }

    // 确定信号
    let signal: 'BUY' | 'SELL' | 'HOLD' = 'HOLD';
    if (score > 0.3) signal = 'BUY';
    else if (score < -0.3) signal = 'SELL';

    // 确定置信度
    let confidence: ConfidenceLevel = 'MEDIUM';
    let confidenceScore = Math.abs(score);
    if (confidenceScore > 0.5) {
      confidence = 'HIGH';
      confidenceScore = 0.8;
    } else if (confidenceScore < 0.2) {
      confidence = 'LOW';
      confidenceScore = 0.3;
    }

    // 计算止盈止损
    let stopLoss: number | undefined;
    let takeProfit: number | undefined;
    let targetPrice: number | undefined;

    if (signal === 'BUY') {
      stopLoss = price * (1 - 0.01);
      takeProfit = price * (1 + 0.02 * (confidence === 'HIGH' ? 1.5 : 1));
      targetPrice = takeProfit;
    } else if (signal === 'SELL') {
      stopLoss = price * (1 + 0.01);
      takeProfit = price * (1 - 0.02 * (confidence === 'HIGH' ? 1.5 : 1));
      targetPrice = takeProfit;
    }

    return {
      signal_id: `signal_${Date.now()}`,
      signal,
      confidence,
      confidence_score: confidenceScore,
      reasoning: reasons.length > 0 ? reasons.join(', ') : '信号不明确',
      target_price: targetPrice,
      stop_loss: stopLoss,
      take_profit: takeProfit,
      position_size_ratio: confidence === 'HIGH' ? 0.1 : confidence === 'MEDIUM' ? 0.05 : 0.02,
      timestamp: Date.now(),
      ai_model: 'local_rule_based',
    };
  }

  // -----------------------------------------
  // 回退信号
  // -----------------------------------------

  private generateFallbackSignal(
    context: MarketContext,
    reason: string
  ): TradingSignal {
    logger.warning(`Generating fallback signal: ${reason}`);

    const { technical } = context;
    const price = context.current_price;

    // 简单的回退策略
    let signal: 'BUY' | 'SELL' | 'HOLD' = 'HOLD';
    let stopLoss: number | undefined;
    let takeProfit: number | undefined;

    if (technical.momentum.rsi < 30 && technical.momentum.macd.histogram > 0) {
      signal = 'BUY';
      stopLoss = price * 0.99;
      takeProfit = price * 1.02;
    } else if (technical.momentum.rsi > 70 && technical.momentum.macd.histogram < 0) {
      signal = 'SELL';
      stopLoss = price * 1.01;
      takeProfit = price * 0.98;
    }

    return {
      signal_id: `signal_${Date.now()}`,
      signal,
      confidence: 'LOW',
      confidence_score: 0.3,
      reasoning: `回退信号: ${reason}`,
      stop_loss: stopLoss,
      take_profit: takeProfit,
      position_size_ratio: 0.02,
      timestamp: Date.now(),
      ai_model: this.model,
    };
  }

  // -----------------------------------------
  // 工具
  // -----------------------------------------

  private delay(ms: number): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }
}

// ============================================
// 便捷函数
// ============================================

let globalAnalyzer: DeepSeekAnalyzer | null = null;

export function createDeepSeekAnalyzer(config: DeepSeekConfig): DeepSeekAnalyzer {
  return new DeepSeekAnalyzer(config);
}

export function getGlobalAnalyzer(): DeepSeekAnalyzer | null {
  return globalAnalyzer;
}

export function setGlobalAnalyzer(analyzer: DeepSeekAnalyzer): void {
  globalAnalyzer = analyzer;
}
