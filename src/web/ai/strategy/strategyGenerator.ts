/**
 * Copyright 2026 NEMT Lab
 *
 * DeepSeek Strategy Generator
 * AI-powered strategy creation using DeepSeek
 */

import type { Strategy, StrategyMetrics } from '../../stores/strategyStore';

// ============================================
// API 配置
// ============================================

const DEEPSEEK_API_KEY = 'sk-51a318c74def4d24a0eef6bf3aa5aec9';
const DEEPSEEK_BASE_URL = 'https://api.deepseek.com';
const DEEPSEEK_MODEL = 'deepseek-chat';

// ============================================
// 生成结果类型
// ============================================

export interface GeneratedStrategy {
  name: string;
  author: string;
  description: string;
  version: string;
  tags: string[];
  // 技术指标配置
  indicators: {
    type: 'rsi' | 'macd' | 'nemt' | 'bollinger' | 'mixed';
    params: Record<string, number>;
  };
  // 入场/出场规则描述
  entryRules: string;
  exitRules: string;
  // 风险管理
  riskManagement: {
    stopLoss: number;
    takeProfit: number;
    maxPositionSize: number;
  };
  // 市场适用性
  marketConditions: string[];
  timeframe: string;
  // AI 生成的原始响应（用于调试）
  rawResponse?: string;
}

export interface StrategyGenerationRequest {
  /** 用户的需求描述 */
  userDescription: string;
  /** 交易品种 */
  symbol?: string;
  /** 偏好的时间周期 */
  preferredTimeframe?: string;
  /** 风险偏好: low, medium, high */
  riskTolerance?: 'low' | 'medium' | 'high';
  /** 策略类型偏好 */
  strategyType?: 'trend_following' | 'mean_reversion' | 'breakout' | 'arbitrage' | 'ai_driven' | 'any';
}

// ============================================
// DeepSeek Strategy Generator
// ============================================

export class DeepSeekStrategyGenerator {
  private apiKey: string;
  private model: string;
  private baseUrl: string;

  constructor(apiKey?: string) {
    this.apiKey = apiKey || DEEPSEEK_API_KEY;
    this.model = DEEPSEEK_MODEL;
    this.baseUrl = DEEPSEEK_BASE_URL;
  }

  // -----------------------------------------
  // 核心方法
  // -----------------------------------------

  /**
   * 根据用户描述生成策略
   */
  async generateStrategy(request: StrategyGenerationRequest): Promise<GeneratedStrategy> {
    const prompt = this.buildPrompt(request);
    const response = await this.callDeepSeek(prompt);
    return this.parseGeneratedStrategy(response, request);
  }

  /**
   * 生成多个策略供选择
   */
  async generateMultipleStrategies(
    request: StrategyGenerationRequest,
    count: number = 3
  ): Promise<GeneratedStrategy[]> {
    const multiPrompt = this.buildMultiPrompt(request, count);
    const response = await this.callDeepSeek(multiPrompt);
    return this.parseMultipleStrategies(response, request);
  }

  /**
   * 优化现有策略
   */
  async optimizeStrategy(
    existingStrategy: Strategy,
    optimizationGoal: string
  ): Promise<GeneratedStrategy> {
    const prompt = this.buildOptimizationPrompt(existingStrategy, optimizationGoal);
    const response = await this.callDeepSeek(prompt);
    return this.parseGeneratedStrategy(response, { userDescription: optimizationGoal });
  }

  // -----------------------------------------
  // Prompt 构建
  // -----------------------------------------

  private buildPrompt(request: StrategyGenerationRequest): string {
    const { userDescription, symbol = 'BTCUSDT', riskTolerance = 'medium', strategyType = 'any' } = request;

    return `你是一个专业的量化交易策略设计师。请根据用户需求设计一个完整的交易策略。

## 用户需求
${userDescription}

## 交易品种
${symbol}

## 风险偏好
${riskTolerance === 'low' ? '低风险：严格止损，小仓位，追求稳定收益' :
  riskTolerance === 'high' ? '高风险：宽松止损，大仓位，追求高收益' :
  '中等风险：平衡收益与风险'}

## 策略类型偏好
${strategyType === 'trend_following' ? '趋势跟踪策略' :
  strategyType === 'mean_reversion' ? '均值回归策略' :
  strategyType === 'breakout' ? '突破策略' :
  strategyType === 'arbitrage' ? '套利策略' :
  strategyType === 'ai_driven' ? 'AI 驱动策略' :
  '任意类型'}

## 输出要求
请生成一个完整的策略配置，返回 JSON 格式：

{
  "name": "策略名称（简洁有意义的英文名）",
  "author": "NEMT + DeepSeek",
  "description": "策略描述（50字以内）",
  "version": "1.0.0",
  "tags": ["标签1", "标签2"],
  "indicators": {
    "type": "rsi|macd|nemt|bollinger|mixed",
    "params": {
      "param1": 数值,
      "param2": 数值
    }
  },
  "entryRules": "入场规则描述",
  "exitRules": "出场规则描述",
  "riskManagement": {
    "stopLoss": 止损百分比（0-1，如0.05表示5%）,
    "takeProfit": 止盈百分比（0-1，如0.10表示10%）,
    "maxPositionSize": 最大仓位（0-1，如0.2表示20%）
  },
  "marketConditions": ["适用市场条件1", "适用市场条件2"],
  "timeframe": "策略适用的时间周期"
}

只返回 JSON，不要其他内容。`.trim();
  }

  private buildMultiPrompt(request: StrategyGenerationRequest, count: number): string {
    const basePrompt = this.buildPrompt(request);
    return basePrompt.replace(
      '只返回 JSON，不要其他内容。',
      `返回包含 ${count} 个策略的 JSON 数组：
[
  { 策略1配置 },
  { 策略2配置 },
  ...
]
只返回 JSON 数组，不要其他内容。`
    );
  }

  private buildOptimizationPrompt(existingStrategy: Strategy, optimizationGoal: string): string {
    return `你是量化策略优化专家。请优化以下现有策略。

## 现有策略
- 名称: ${existingStrategy.name}
- 描述: ${existingStrategy.description}
- 版本: ${existingStrategy.version}
- 标签: ${existingStrategy.tags.join(', ')}

## 优化目标
${optimizationGoal}

## 输出要求
返回优化后的策略配置，JSON 格式：
{
  "name": "优化后的策略名称",
  "author": "NEMT + DeepSeek (Optimized)",
  "description": "优化后的策略描述",
  "version": "升级后的版本号",
  "tags": ["标签"],
  "indicators": { "type": "...", "params": {...} },
  "entryRules": "入场规则",
  "exitRules": "出场规则",
  "riskManagement": { "stopLoss": 0.xx, "takeProfit": 0.xx, "maxPositionSize": 0.xx },
  "marketConditions": ["..."],
  "timeframe": "..."
}

只返回 JSON，不要其他内容。`.trim();
  }

  // -----------------------------------------
  // API 调用
  // -----------------------------------------

  private async callDeepSeek(prompt: string): Promise<string> {
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
            content: '你是一个专业的量化交易策略设计师，只返回 JSON 格式的数据。',
          },
          { role: 'user', content: prompt },
        ],
        temperature: 0.7,
        max_tokens: 2000,
      }),
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`DeepSeek API error: ${response.status} - ${errorText}`);
    }

    const data = await response.json();
    const content = data.choices?.[0]?.message?.content;

    if (!content) {
      throw new Error('DeepSeek API returned empty response');
    }

    return content;
  }

  // -----------------------------------------
  // 响应解析
  // -----------------------------------------

  private parseGeneratedStrategy(
    content: string,
    request: StrategyGenerationRequest
  ): GeneratedStrategy {
    try {
      const jsonMatch = content.match(/(\[[\s\S]*\]|\{[\s\S]*\})/);
      if (!jsonMatch) {
        throw new Error('No JSON found in response');
      }

      let parsed = JSON.parse(jsonMatch[0]);

      // 如果返回的是数组，取第一个
      if (Array.isArray(parsed)) {
        parsed = parsed[0];
      }

      const validated = this.validateAndCompleteStrategy(parsed, request);
      validated.rawResponse = content;

      return validated;
    } catch (error) {
      console.error('[DeepSeekStrategyGenerator] Parse error:', error);
      // 返回一个基于请求的默认策略
      return this.createDefaultStrategy(request);
    }
  }

  private parseMultipleStrategies(
    content: string,
    request: StrategyGenerationRequest
  ): GeneratedStrategy[] {
    try {
      const jsonMatch = content.match(/(\[[\s\S]*\])/);
      if (!jsonMatch) {
        return [this.createDefaultStrategy(request)];
      }

      let parsed = JSON.parse(jsonMatch[0]);
      if (!Array.isArray(parsed)) {
        parsed = [parsed];
      }

      return parsed.map((p: any) => {
        try {
          const validated = this.validateAndCompleteStrategy(p, request);
          return validated;
        } catch {
          return this.createDefaultStrategy(request);
        }
      });
    } catch (error) {
      console.error('[DeepSeekStrategyGenerator] Multi-parse error:', error);
      return [this.createDefaultStrategy(request)];
    }
  }

  private validateAndCompleteStrategy(
    data: any,
    request: StrategyGenerationRequest
  ): GeneratedStrategy {
    return {
      name: data.name || 'Unnamed Strategy',
      author: data.author || 'NEMT + DeepSeek',
      description: data.description || 'AI generated strategy',
      version: data.version || '1.0.0',
      tags: Array.isArray(data.tags) ? data.tags : ['AI Generated'],
      indicators: {
        type: this.normalizeIndicatorType(data.indicators?.type),
        params: typeof data.indicators?.params === 'object' ? data.indicators.params : {},
      },
      entryRules: data.entryRules || 'Based on AI analysis',
      exitRules: data.exitRules || 'AI controlled exit',
      riskManagement: {
        stopLoss: this.clamp(this.normalizeNumber(data.riskManagement?.stopLoss), 0.01, 0.5),
        takeProfit: this.clamp(this.normalizeNumber(data.riskManagement?.takeProfit), 0.01, 1),
        maxPositionSize: this.clamp(this.normalizeNumber(data.riskManagement?.maxPositionSize), 0.01, 1),
      },
      marketConditions: Array.isArray(data.marketConditions)
        ? data.marketConditions
        : ['Volatile markets'],
      timeframe: data.timeframe || request.preferredTimeframe || '1h',
      rawResponse: data.rawResponse,
    };
  }

  private normalizeIndicatorType(type: string | undefined): GeneratedStrategy['indicators']['type'] {
    if (!type) return 'mixed';
    const t = type.toLowerCase();
    if (t.includes('rsi')) return 'rsi';
    if (t.includes('macd')) return 'macd';
    if (t.includes('nemt')) return 'nemt';
    if (t.includes('bollinger') || t.includes('bb')) return 'bollinger';
    return 'mixed';
  }

  private normalizeNumber(value: any): number {
    if (typeof value === 'number') return value;
    if (typeof value === 'string') {
      const parsed = parseFloat(value);
      return isNaN(parsed) ? 0.1 : parsed;
    }
    return 0.1;
  }

  private clamp(value: number, min: number, max: number): number {
    return Math.min(max, Math.max(min, value));
  }

  private createDefaultStrategy(request: StrategyGenerationRequest): GeneratedStrategy {
    return {
      name: `${request.symbol || 'BTC'} ${request.riskTolerance || 'balanced'} Strategy`,
      author: 'NEMT + DeepSeek',
      description: 'AI generated trading strategy based on your requirements',
      version: '1.0.0',
      tags: ['AI Generated', request.strategyType || 'mixed'],
      indicators: {
        type: 'mixed',
        params: { rsiPeriod: 14, macdFast: 12, macdSlow: 26 },
      },
      entryRules: 'AI powered entry signals',
      exitRules: 'AI powered exit signals',
      riskManagement: {
        stopLoss: request.riskTolerance === 'low' ? 0.02 : request.riskTolerance === 'high' ? 0.10 : 0.05,
        takeProfit: request.riskTolerance === 'low' ? 0.05 : request.riskTolerance === 'high' ? 0.25 : 0.10,
        maxPositionSize: 0.2,
      },
      marketConditions: ['BTC markets', 'Trending conditions'],
      timeframe: request.preferredTimeframe || '1h',
    };
  }
}

// ============================================
// 便捷函数
// ============================================

let generatorInstance: DeepSeekStrategyGenerator | null = null;

export function getStrategyGenerator(): DeepSeekStrategyGenerator {
  if (!generatorInstance) {
    generatorInstance = new DeepSeekStrategyGenerator(DEEPSEEK_API_KEY);
  }
  return generatorInstance;
}

export async function generateStrategyFromDescription(
  userDescription: string,
  options?: Partial<StrategyGenerationRequest>
): Promise<GeneratedStrategy> {
  const generator = getStrategyGenerator();
  return generator.generateStrategy({
    userDescription,
    ...options,
  });
}

export async function generateMultipleStrategiesFromDescription(
  userDescription: string,
  count?: number,
  options?: Partial<StrategyGenerationRequest>
): Promise<GeneratedStrategy[]> {
  const generator = getStrategyGenerator();
  return generator.generateMultipleStrategies(
    { userDescription, ...options },
    count
  );
}
