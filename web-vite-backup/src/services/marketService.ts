/**
 * NEMT 市场数据服务
 * 提供模拟市场数据，支持多交易所/多币种
 */

export interface KLine {
  timestamp: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  symbol: string;
  interval: string;
}

export interface MarketData {
  symbol: string;
  price: number;
  bid: number;
  ask: number;
  volume: number;
  change_24h: number;
  change_pct_24h: number;
  high_24h: number;
  low_24h: number;
  timestamp: string;
}

export interface TickerData {
  symbol: string;
  price: number;
  change_24h: number;
  change_pct_24h: number;
  high_24h: number;
  low_24h: number;
  volume_24h: number;
}

// 默认模拟价格
const DEFAULT_PRICES: Record<string, number> = {
  'BTCUSDT': 67500,
  'ETHUSDT': 3450,
  'BNBUSDT': 580,
  'SOLUSDT': 145,
  'XRPUSDT': 0.52,
  'ADAUSDT': 0.45,
  'DOGEUSDT': 0.12,
  'AVAXUSDT': 35,
};

// 波动率配置
const VOLATILITY = 0.002;

class MockMarketService {
  private prices: Record<string, number> = { ...DEFAULT_PRICES };
  private subscribers: Map<string, ((data: MarketData) => void)[]> = new Map();
  private intervalId: number | null = null;
  private isRunning = false;

  /**
   * 启动模拟数据流
   */
  start(): void {
    if (this.isRunning) return;
    this.isRunning = true;
    
    this.intervalId = window.setInterval(() => {
      this.updatePrices();
      this.notifySubscribers();
    }, 1000);
    
    console.log('[MarketService] Started mock market data stream');
  }

  /**
   * 停止模拟数据流
   */
  stop(): void {
    if (this.intervalId !== null) {
      window.clearInterval(this.intervalId);
      this.intervalId = null;
    }
    this.isRunning = false;
    console.log('[MarketService] Stopped mock market data stream');
  }

  /**
   * 更新所有价格
   */
  private updatePrices(): void {
    for (const symbol of Object.keys(this.prices)) {
      // 随机游走
      const change = (Math.random() - 0.5) * 2 * VOLATILITY;
      this.prices[symbol] *= (1 + change);
    }
  }

  /**
   * 通知订阅者
   */
  private notifySubscribers(): void {
    const data = this.getAllTickers();
    
    for (const [symbol, callbacks] of this.subscribers) {
      const ticker = data.find(t => t.symbol === symbol);
      if (ticker && callbacks.length > 0) {
        callbacks.forEach(cb => {
          try {
            cb({
              symbol: ticker.symbol,
              price: ticker.price,
              bid: ticker.price * 0.9999,
              ask: ticker.price * 1.0001,
              volume: ticker.volume_24h,
              change_24h: ticker.change_24h,
              change_pct_24h: ticker.change_pct_24h,
              high_24h: ticker.high_24h,
              low_24h: ticker.low_24h,
              timestamp: new Date().toISOString()
            });
          } catch (e) {
            console.error('[MarketService] Subscriber error:', e);
          }
        });
      }
    }
  }

  /**
   * 获取当前价格
   */
  getPrice(symbol: string): number {
    return this.prices[symbol] || 0;
  }

  /**
   * 获取所有行情
   */
  getAllTickers(): TickerData[] {
    return Object.entries(this.prices).map(([symbol, price]) => {
      const basePrice = DEFAULT_PRICES[symbol] || price;
      const change = price - basePrice;
      const changePct = (change / basePrice) * 100;
      
      return {
        symbol,
        price,
        change_24h: change,
        change_pct_24h: changePct,
        high_24h: price * 1.02,
        low_24h: price * 0.98,
        volume_24h: Math.random() * 1000000000 + 500000000
      };
    });
  }

  /**
   * 获取单个币种行情
   */
  getTicker(symbol: string): TickerData | null {
    const price = this.prices[symbol];
    if (!price) return null;
    
    const basePrice = DEFAULT_PRICES[symbol] || price;
    const change = price - basePrice;
    const changePct = (change / basePrice) * 100;
    
    return {
      symbol,
      price,
      change_24h: change,
      change_pct_24h: changePct,
      high_24h: price * 1.02,
      low_24h: price * 0.98,
      volume_24h: Math.random() * 1000000000 + 500000000
    };
  }

  /**
   * 获取历史K线
   */
  getHistoryKlines(symbol: string, interval: string = '1h', limit: number = 100): KLine[] {
    const klines: KLine[] = [];
    const basePrice = this.prices[symbol] || DEFAULT_PRICES[symbol] || 67000;
    let currentTime = Date.now();
    
    // 根据周期确定时间间隔
    const intervalMs = this.parseInterval(interval);
    
    for (let i = limit - 1; i >= 0; i--) {
      const timestamp = new Date(currentTime - i * intervalMs);
      const priceVariation = 1 + (Math.random() - 0.5) * 0.1;
      const price = basePrice * priceVariation;
      
      const open = price * (1 + (Math.random() - 0.5) * 0.002);
      const close = price * (1 + (Math.random() - 0.5) * 0.002);
      const high = Math.max(open, close) * (1 + Math.random() * 0.003);
      const low = Math.min(open, close) * (1 - Math.random() * 0.003);
      const volume = Math.random() * 10000 * (basePrice / 1000);
      
      klines.push({
        timestamp: timestamp.toISOString(),
        open,
        high,
        low,
        close,
        volume,
        symbol,
        interval
      });
    }
    
    return klines;
  }

  /**
   * 解析时间周期
   */
  private parseInterval(interval: string): number {
    const units: Record<string, number> = {
      'm': 60 * 1000,
      'h': 60 * 60 * 1000,
      'd': 24 * 60 * 60 * 1000,
      'w': 7 * 24 * 60 * 60 * 1000
    };
    
    const match = interval.match(/^(\d+)([mhdw])$/);
    if (match) {
      const value = parseInt(match[1]);
      const unit = match[2];
      return value * units[unit];
    }
    
    return 60 * 60 * 1000; // 默认1小时
  }

  /**
   * 订阅实时数据
   */
  subscribe(symbol: string, callback: (data: MarketData) => void): () => void {
    if (!this.subscribers.has(symbol)) {
      this.subscribers.set(symbol, []);
    }
    this.subscribers.get(symbol)!.push(callback);
    
    // 自动启动
    if (!this.isRunning) {
      this.start();
    }
    
    // 返回取消订阅函数
    return () => {
      const callbacks = this.subscribers.get(symbol);
      if (callbacks) {
        const index = callbacks.indexOf(callback);
        if (index > -1) {
          callbacks.splice(index, 1);
        }
      }
    };
  }

  /**
   * 获取状态
   */
  getStatus(): { running: boolean; symbols: string[]; subscribers: number } {
    return {
      running: this.isRunning,
      symbols: Object.keys(this.prices),
      subscribers: Array.from(this.subscribers.values()).reduce((sum, cbs) => sum + cbs.length, 0)
    };
  }
}

// 单例导出
export const marketService = new MockMarketService();

// 便捷函数
export function getMarketService(): MockMarketService {
  return marketService;
}

export function startMarketData(): void {
  marketService.start();
}

export function stopMarketData(): void {
  marketService.stop();
}

export function subscribeMarketData(symbol: string, callback: (data: MarketData) => void): () => void {
  return marketService.subscribe(symbol, callback);
}
