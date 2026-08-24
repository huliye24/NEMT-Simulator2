/**
 * Copyright 2026 NEMT Lab
 *
 * Sentiment Fetcher
 * 市场情绪数据获取
 */

export interface SentimentConfig {
  enabled?: boolean;
  lookbackHours?: number;
  apiUrl?: string;
}

export interface SentimentResult {
  fear_greed_index: number;
  sentiment_label: '极度恐惧' | '恐惧' | '中性' | '贪婪' | '极度贪婪';
  social_volume: number;
  trend: 'positive' | 'negative' | 'neutral';
  timestamp: number;
}

export class SentimentDataFetcher {
  private config: Required<SentimentConfig>;
  private cache: SentimentResult | null = null;
  private cacheTime: number = 0;
  private cacheTTL: number = 5 * 60 * 1000; // 5 分钟缓存

  constructor(config?: SentimentConfig) {
    this.config = {
      enabled: config?.enabled ?? true,
      lookbackHours: config?.lookbackHours ?? 4,
      apiUrl: config?.apiUrl ?? 'https://api.alternative.me/fng/',
    };
  }

  /**
   * 获取情绪数据
   */
  async fetch(): Promise<SentimentResult> {
    // 检查缓存
    if (this.cache && Date.now() - this.cacheTime < this.cacheTTL) {
      return this.cache;
    }

    if (!this.config.enabled) {
      return this.getDefaultSentiment();
    }

    try {
      const response = await fetch(this.config.apiUrl);
      const data = await response.json();

      const fearGreedIndex = parseInt(data.data?.[0]?.value || '50');

      const result: SentimentResult = {
        fear_greed_index: fearGreedIndex,
        sentiment_label: this.getSentimentLabel(fearGreedIndex),
        social_volume: this.estimateSocialVolume(fearGreedIndex),
        trend: this.getSentimentTrend(fearGreedIndex),
        timestamp: Date.now(),
      };

      this.cache = result;
      this.cacheTime = Date.now();

      return result;
    } catch (error) {
      console.warn('[Sentiment] Fetch failed, using default:', error);
      return this.getDefaultSentiment();
    }
  }

  /**
   * 获取默认情绪 (用于 API 不可用时)
   */
  private getDefaultSentiment(): SentimentResult {
    return {
      fear_greed_index: 50,
      sentiment_label: '中性',
      social_volume: 1000,
      trend: 'neutral',
      timestamp: Date.now(),
    };
  }

  /**
   * 获取情绪标签
   */
  private getSentimentLabel(index: number): SentimentResult['sentiment_label'] {
    if (index <= 25) return '极度恐惧';
    if (index <= 45) return '恐惧';
    if (index <= 55) return '中性';
    if (index <= 75) return '贪婪';
    return '极度贪婪';
  }

  /**
   * 估算社交量
   */
  private estimateSocialVolume(fearGreedIndex: number): number {
    // 恐惧时社交量较低,贪婪时较高
    const base = 1000;
    const variation = (fearGreedIndex - 50) * 20;
    return Math.max(100, base + variation);
  }

  /**
   * 获取情绪趋势
   */
  private getSentimentTrend(fearGreedIndex: number): SentimentResult['trend'] {
    if (fearGreedIndex > 55) return 'positive';
    if (fearGreedIndex < 45) return 'negative';
    return 'neutral';
  }

  /**
   * 设置启用状态
   */
  setEnabled(enabled: boolean): void {
    this.config.enabled = enabled;
  }

  /**
   * 是否启用
   */
  isEnabled(): boolean {
    return this.config.enabled;
  }
}

// ============================================
// 全局实例
// ============================================

let globalFetcher: SentimentDataFetcher | null = null;

export function getSentimentFetcher(): SentimentDataFetcher {
  if (!globalFetcher) {
    globalFetcher = new SentimentDataFetcher();
  }
  return globalFetcher;
}
