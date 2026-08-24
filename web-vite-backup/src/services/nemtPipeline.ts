/**
 * NEMT Pipeline Service
 * 完整的流程: Notion读 → NEMT分析 → 信号生成 → 结果展示
 *
 * 支持两种模式:
 * 1. 本地模式: 直接使用 TypeScript 实现 NEMT 分析
 * 2. 远程模式: 通过 HTTP API 调用 Python quant-sync-server
 */

import {
  NEMTParams,
  NEMTSignals,
  MarketPhase,
  Direction,
  SignalType,
  DEFAULT_PARAMS,
  ExperimentResult,
  PHASE_STRATEGIES,
  PhaseStrategy
} from '../types/nemt';
import { NEMTSimulator, generateDemoData } from '../utils/nemtCore';
import { NEMTSignalIndicators } from '../utils/nemtSignals';

// =====================
// 配置
// =====================

const API_CONFIG = {
  // Python API 服务器地址
  baseUrl: 'http://localhost:8080',
  timeout: 30000, // 30秒超时
};

// =====================
// 类型定义
// =====================

// 交易信号类型
export interface TradingSignal {
  id: string;
  symbol: string;
  type: SignalType;
  direction: Direction;
  price: number;
  confidence: number;
  reason: string;
  timestamp: string;
  phase: MarketPhase;
  indicators: {
    dci: number;
    spectralWidth: number;
    vortexMaturity: number;
    resonanceConfidence: number;
  };
}

// Pipeline 执行结果
export interface PipelineResult {
  success: boolean;
  signals: TradingSignal[];
  currentPhase: MarketPhase;
  phaseStrategy: PhaseStrategy;
  experimentResult: ExperimentResult | null;
  nemtSignals: NEMTSignals;
  error?: string;
  logs?: PipelineLogEntry[];
  steps?: Record<string, any>;
}

// Pipeline 日志条目
export interface PipelineLogEntry {
  timestamp: string;
  level: 'INFO' | 'SUCCESS' | 'WARNING' | 'ERROR';
  step: string;
  message: string;
  data?: any;
}

// HTTP API 响应
interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
  logs?: PipelineLogEntry[];
  steps?: Record<string, any>;
}

// =====================
// 信号历史存储
// =====================

class SignalHistory {
  private signals: TradingSignal[] = [];
  private maxSize = 100;

  add(signal: TradingSignal): void {
    this.signals.unshift(signal);
    if (this.signals.length > this.maxSize) {
      this.signals.pop();
    }
  }

  getAll(): TradingSignal[] {
    return [...this.signals];
  }

  getRecent(count: number = 10): TradingSignal[] {
    return this.signals.slice(0, count);
  }

  clear(): void {
    this.signals = [];
  }

  setFromArray(signals: TradingSignal[]): void {
    this.signals = signals.slice(0, this.maxSize);
  }
}

// 全局信号历史实例
export const signalHistory = new SignalHistory();

// =====================
// HTTP 客户端
// =====================

class ApiClient {
  private baseUrl: string;
  private timeout: number;

  constructor(baseUrl: string, timeout: number = 30000) {
    this.baseUrl = baseUrl;
    this.timeout = timeout;
  }

  async post<T>(endpoint: string, body: any): Promise<ApiResponse<T>> {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), this.timeout);

      const response = await fetch(`${this.baseUrl}${endpoint}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(body),
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      if (error instanceof Error) {
        if (error.name === 'AbortError') {
          throw new Error(`请求超时 (${this.timeout}ms)`);
        }
        throw error;
      }
      throw new Error('Unknown error');
    }
  }

  async get<T>(endpoint: string): Promise<ApiResponse<T>> {
    try {
      const response = await fetch(`${this.baseUrl}${endpoint}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      if (error instanceof Error) {
        throw error;
      }
      throw new Error('Unknown error');
    }
  }
}

// =====================
// NEMT Pipeline 服务
// =====================

export class NEMTPipelineService {
  private simulator: NEMTSimulator;
  private signalIndicators: NEMTSignalIndicators;
  private apiClient: ApiClient;
  private useRemote: boolean = false;
  private logs: PipelineLogEntry[] = [];

  constructor() {
    this.simulator = new NEMTSimulator();
    this.signalIndicators = new NEMTSignalIndicators();
    this.apiClient = new ApiClient(API_CONFIG.baseUrl, API_CONFIG.timeout);
  }

  /**
   * 设置是否使用远程 API
   */
  setUseRemote(useRemote: boolean): void {
    this.useRemote = useRemote;
    this.addLog('INFO', 'CONFIG', `运行模式: ${useRemote ? '远程 (Python)' : '本地 (TypeScript)'}`);
  }

  /**
   * 获取日志
   */
  getLogs(): PipelineLogEntry[] {
    return [...this.logs];
  }

  /**
   * 清空日志
   */
  clearLogs(): void {
    this.logs = [];
  }

  /**
   * 添加日志
   */
  private addLog(level: PipelineLogEntry['level'], step: string, message: string, data?: any): void {
    const entry: PipelineLogEntry = {
      timestamp: new Date().toISOString(),
      level,
      step,
      message,
      data,
    };
    this.logs.push(entry);
    console.log(`[${level}] [${step}] ${message}`);
  }

  /**
   * 设置参数
   */
  setParams(params: Partial<NEMTParams>): void {
    this.simulator.setParams(params);
  }

  /**
   * 获取参数
   */
  getParams(): NEMTParams {
    return this.simulator.getParams();
  }

  /**
   * 检查 API 服务器状态
   */
  async checkServerStatus(): Promise<{ available: boolean; message: string }> {
    try {
      const response = await this.apiClient.get('/api/pipeline/status');
      if (response.success) {
        return {
          available: true,
          message: 'API 服务器正常',
        };
      }
      return {
        available: false,
        message: response.error || '未知错误',
      };
    } catch (error) {
      return {
        available: false,
        message: error instanceof Error ? error.message : '连接失败',
      };
    }
  }

  /**
   * 运行完整流程
   * @param prices 价格序列
   * @param symbol 交易对
   * @param notionPageId Notion 页面 ID（可选）
   */
  async runPipeline(
    prices: number[],
    symbol: string = 'BTCUSDT',
    notionPageId?: string
  ): Promise<PipelineResult> {
    this.clearLogs();
    this.addLog('INFO', 'PIPELINE', '开始运行 NEMT Pipeline...');

    try {
      if (this.useRemote) {
        return await this.runRemotePipeline(prices, symbol, notionPageId);
      } else {
        return await this.runLocalPipeline(prices, symbol);
      }
    } catch (error) {
      this.addLog('ERROR', 'PIPELINE', `Pipeline 执行失败: ${error instanceof Error ? error.message : 'Unknown error'}`);
      return {
        success: false,
        signals: [],
        currentPhase: MarketPhase.PHASE_A_NOISE,
        phaseStrategy: PHASE_STRATEGIES[MarketPhase.PHASE_A_NOISE],
        experimentResult: null,
        nemtSignals: this.getEmptySignals(),
        error: error instanceof Error ? error.message : 'Unknown error',
        logs: this.logs,
      };
    }
  }

  /**
   * 运行远程 Pipeline（调用 Python API）
   */
  private async runRemotePipeline(
    prices: number[],
    symbol: string,
    notionPageId?: string
  ): Promise<PipelineResult> {
    this.addLog('INFO', 'STEP_0', `连接 API 服务器: ${API_CONFIG.baseUrl}`);

    try {
      const response = await this.apiClient.post<any>('/api/pipeline/run', {
        prices,
        symbol,
        notion_page_id: notionPageId,
      });

      this.addLog('INFO', 'STEP_RESPONSE', '收到 API 响应');

      if (response.success) {
        // 处理返回的日志
        if (response.logs) {
          response.logs.forEach((log: PipelineLogEntry) => {
            this.addLog(log.level, log.step, log.message, log.data);
          });
        }

        // 从步骤中提取数据
        const nemtData = response.steps?.nemt_analysis?.data;
        const signalData = response.steps?.signal_generate?.signal;

        // 转换为本地格式
        const experimentResult = this.convertNEMTResult(nemtData);
        const signals = signalData ? [this.convertSignal(signalData)] : [];

        // 更新信号历史
        if (signals.length > 0) {
          signals.forEach(s => signalHistory.add(s));
        }

        const currentPhase = this.detectPhase(experimentResult);
        const phaseStrategy = PHASE_STRATEGIES[currentPhase];

        this.addLog('SUCCESS', 'COMPLETE', 'Pipeline 执行成功!');

        return {
          success: true,
          signals,
          currentPhase,
          phaseStrategy,
          experimentResult,
          nemtSignals: this.getSignalsFromResult(experimentResult),
          logs: this.logs,
          steps: response.steps,
        };
      } else {
        this.addLog('ERROR', 'API', `API 调用失败: ${response.error}`);
        throw new Error(response.error || 'API 调用失败');
      }
    } catch (error) {
      this.addLog('WARNING', 'API', `远程调用失败，切换到本地模式: ${error instanceof Error ? error.message : error}`);
      this.useRemote = false;
      return await this.runLocalPipeline(prices, symbol);
    }
  }

  /**
   * 运行本地 Pipeline（使用 TypeScript）
   */
  private async runLocalPipeline(
    prices: number[],
    symbol: string
  ): Promise<PipelineResult> {
    this.addLog('INFO', 'LOCAL', '使用本地 TypeScript 引擎');

    // 1. NEMT 分析
    this.addLog('INFO', 'STEP_1', '开始 NEMT 分析...');
    const result = this.simulator.runExperiment(prices);
    this.addLog('SUCCESS', 'STEP_1', `NEMT 分析完成 - 谱宽: ${result.spectralWidth.toFixed(6)}`);

    // 2. 计算信号指标
    this.addLog('INFO', 'STEP_2', '计算信号指标...');
    const signals = this.signalIndicators.getFullSignals(
      prices,
      this.generateMockVolumes(prices.length),
      this.generateMockOI(prices.length),
      this.generateMockFunding(prices.length),
      this.generateMockBBW(prices.length),
      Array.from(result.spectrum),
      Array.from(result.freqs)
    );
    this.addLog('SUCCESS', 'STEP_2', `信号计算完成 - 相位: ${signals.phase}`);

    // 3. 确定相位和策略
    const phaseStrategy = PHASE_STRATEGIES[signals.phase];

    // 4. 生成交易信号
    this.addLog('INFO', 'STEP_3', '生成交易信号...');
    const tradingSignals = this.generateTradingSignals(
      signals,
      result,
      symbol,
      prices[prices.length - 1]
    );
    this.addLog('SUCCESS', 'STEP_3', `生成 ${tradingSignals.length} 个交易信号`);

    // 5. 添加到历史
    tradingSignals.forEach(s => {
      signalHistory.add(s);
      this.addLog('INFO', 'SIGNAL', `${s.type} - ${s.direction} @ ${s.price.toFixed(2)} (置信度: ${(s.confidence * 100).toFixed(0)}%)`);
    });

    this.addLog('SUCCESS', 'COMPLETE', 'Pipeline 执行成功!');

    return {
      success: true,
      signals: tradingSignals,
      currentPhase: signals.phase,
      phaseStrategy,
      experimentResult: result,
      nemtSignals: signals,
      logs: this.logs,
    };
  }

  /**
   * 从 Notion 读取策略参数（通过 API）
   */
  async readNotionStrategy(pageId: string): Promise<NEMTParams | null> {
    try {
      this.addLog('INFO', 'NOTION', `从 Notion 读取策略: ${pageId}`);

      if (this.useRemote) {
        const response = await this.apiClient.post<any>('/api/notion/strategy', {
          page_id: pageId,
        });

        if (response.success && response.data) {
          this.addLog('SUCCESS', 'NOTION', `策略读取成功: ${response.data.name}`);
          return this.convertParams(response.data);
        }
      }

      // 本地模式返回默认参数
      this.addLog('INFO', 'NOTION', '使用默认策略参数');
      return DEFAULT_PARAMS;
    } catch (error) {
      this.addLog('WARNING', 'NOTION', `策略读取失败: ${error instanceof Error ? error.message : 'Unknown'}`);
      return DEFAULT_PARAMS;
    }
  }

  /**
   * 写入回测结果到 Notion（通过 API）
   */
  async writeBacktestResult(
    sourcePageId: string,
    result: ExperimentResult
  ): Promise<boolean> {
    try {
      this.addLog('INFO', 'BACKTEST', `写入回测结果到 Notion: ${sourcePageId}`);

      if (this.useRemote) {
        const response = await this.apiClient.post<any>('/api/notion/backtest', {
          source_page_id: sourcePageId,
          result: result,
        });

        if (response.success) {
          this.addLog('SUCCESS', 'BACKTEST', '回测结果写入成功');
          return true;
        }
      }

      this.addLog('INFO', 'BACKTEST', '回测结果已记录');
      return true;
    } catch (error) {
      this.addLog('WARNING', 'BACKTEST', `写入失败: ${error instanceof Error ? error.message : 'Unknown'}`);
      return false;
    }
  }

  /**
   * 获取信号历史
   */
  getSignalHistory(): TradingSignal[] {
    return signalHistory.getAll();
  }

  // =====================
  // 私有方法
  // =====================

  private generateTradingSignals(
    signals: NEMTSignals,
    result: ExperimentResult,
    symbol: string,
    currentPrice: number
  ): TradingSignal[] {
    const tradingSignals: TradingSignal[] = [];
    const timestamp = new Date().toISOString();

    // 涡旋突破信号
    if (signals.vortex.isVortex && signals.vortex.maturityScore > 5) {
      tradingSignals.push({
        id: `${Date.now()}_vortex`,
        symbol,
        type: SignalType.VORTEX_BREAKOUT,
        direction: signals.dci.direction === 'bullish' ? Direction.BULLISH :
                   signals.dci.direction === 'bearish' ? Direction.BEARISH : Direction.NEUTRAL,
        price: currentPrice,
        confidence: Math.min(signals.vortex.maturityScore / 10, 1),
        reason: `涡旋成熟度: ${signals.vortex.maturityScore.toFixed(1)}/10`,
        timestamp,
        phase: signals.phase,
        indicators: {
          dci: signals.dci.value,
          spectralWidth: signals.spectralWidth || result.spectralWidth,
          vortexMaturity: signals.vortex.maturityScore,
          resonanceConfidence: signals.resonance.confidence
        }
      });
    }

    // 随机共振触发信号
    if (signals.resonance.isResonance) {
      tradingSignals.push({
        id: `${Date.now()}_resonance`,
        symbol,
        type: SignalType.RESONANCE_TRIGGER,
        direction: signals.resonance.bullish ? Direction.BULLISH : Direction.BEARISH,
        price: currentPrice,
        confidence: signals.resonance.confidence,
        reason: `随机共振触发，置信度: ${(signals.resonance.confidence * 100).toFixed(0)}%`,
        timestamp,
        phase: signals.phase,
        indicators: {
          dci: signals.dci.value,
          spectralWidth: signals.spectralWidth || result.spectralWidth,
          vortexMaturity: signals.vortex.maturityScore,
          resonanceConfidence: signals.resonance.confidence
        }
      });
    }

    // 趋势回调信号（仅在 D 相）
    if (signals.phase === MarketPhase.PHASE_D_TREND && signals.dci.value > 0.65) {
      tradingSignals.push({
        id: `${Date.now()}_trend`,
        symbol,
        type: SignalType.TREND_CALLBACK,
        direction: signals.dci.direction === 'bullish' ? Direction.BULLISH : Direction.BEARISH,
        price: currentPrice,
        confidence: signals.dci.value,
        reason: `趋势运行期，DCI: ${signals.dci.value.toFixed(2)}`,
        timestamp,
        phase: signals.phase,
        indicators: {
          dci: signals.dci.value,
          spectralWidth: signals.spectralWidth || result.spectralWidth,
          vortexMaturity: signals.vortex.maturityScore,
          resonanceConfidence: signals.resonance.confidence
        }
      });
    }

    return tradingSignals;
  }

  private convertNEMTResult(data: any): ExperimentResult {
    if (!data) {
      return this.simulator.runExperiment([]);
    }

    // 从 API 数据转换为本地格式
    return {
      spectralWidth: data.spectralWidth || data.spectral_width || 0,
      meanFrequency: data.meanFrequency || data.mean_frequency || 0,
      resonance: {
        numPeaks: data.numPeaks || data.num_peaks || 0,
        peakFrequencies: data.resonancePeaks || data.resonance_peaks || [],
      },
      spectrum: new Float64Array(data.spectrum || []),
      freqs: new Float64Array(data.frequencies || data.freqs || []),
      evolution: data.evolution || [],
      params: data.params || DEFAULT_PARAMS,
    };
  }

  private convertSignal(data: any): TradingSignal {
    return {
      id: data.id || `sig_${Date.now()}`,
      symbol: data.symbol || 'BTCUSDT',
      type: this.convertSignalType(data.type || data.action || 'hold'),
      direction: this.convertDirection(data.direction || 'neutral'),
      price: data.price || 0,
      confidence: data.confidence || 0.5,
      reason: data.reason || '',
      timestamp: data.timestamp || new Date().toISOString(),
      phase: this.convertPhase(data.phase),
      indicators: {
        dci: data.indicators?.dci || 0.5,
        spectralWidth: data.indicators?.spectralWidth || 0,
        vortexMaturity: data.indicators?.vortexMaturity || 0,
        resonanceConfidence: data.indicators?.resonanceConfidence || 0,
      },
    };
  }

  private convertSignalType(type: string): SignalType {
    const typeMap: Record<string, SignalType> = {
      'vortex_breakout': SignalType.VORTEX_BREAKOUT,
      'resonance_trigger': SignalType.RESONANCE_TRIGGER,
      'trend_callback': SignalType.TREND_CALLBACK,
      'buy': SignalType.VORTEX_BREAKOUT,
      'sell': SignalType.VORTEX_BREAKOUT,
      'hold': SignalType.RESONANCE_TRIGGER,
    };
    return typeMap[type.toLowerCase()] || SignalType.RESONANCE_TRIGGER;
  }

  private convertDirection(dir: string): Direction {
    const dirMap: Record<string, Direction> = {
      'bullish': Direction.BULLISH,
      'bearish': Direction.BEARISH,
      'neutral': Direction.NEUTRAL,
      'long': Direction.BULLISH,
      'short': Direction.BEARISH,
    };
    return dirMap[dir.toLowerCase()] || Direction.NEUTRAL;
  }

  private convertPhase(phase: string): MarketPhase {
    const phaseMap: Record<string, MarketPhase> = {
      'PHASE_A_NOISE': MarketPhase.PHASE_A_NOISE,
      'PHASE_B_VORTEX': MarketPhase.PHASE_B_VORTEX,
      'PHASE_C_RESONANCE': MarketPhase.PHASE_C_RESONANCE,
      'PHASE_D_TREND': MarketPhase.PHASE_D_TREND,
      'A': MarketPhase.PHASE_A_NOISE,
      'B': MarketPhase.PHASE_B_VORTEX,
      'C': MarketPhase.PHASE_C_RESONANCE,
      'D': MarketPhase.PHASE_D_TREND,
    };
    return phaseMap[phase] || MarketPhase.PHASE_A_NOISE;
  }

  private convertParams(data: any): NEMTParams {
    return {
      alpha: data.alpha || 0.1,
      beta: data.beta || 1.0,
      noiseLevel: data.noise || data.noiseLevel || 0.2,
      dt: data.dt || 0.01,
      dx: data.dx || 1.0,
      steps: data.steps || 200,
      n: data.n || 1000,
    };
  }

  private detectPhase(result: ExperimentResult): MarketPhase {
    const sw = result.spectralWidth;
    if (sw < 0.01) return MarketPhase.PHASE_D_TREND;
    if (sw < 0.03) return MarketPhase.PHASE_C_RESONANCE;
    if (sw < 0.05) return MarketPhase.PHASE_B_VORTEX;
    return MarketPhase.PHASE_A_NOISE;
  }

  private getSignalsFromResult(result: ExperimentResult): NEMTSignals {
    const phase = this.detectPhase(result);
    return {
      dci: { value: 0.5, noiseState: 'medium', direction: 'neutral', trend: 'stable' },
      vortex: { bbwNarrow: false, volumeUniform: false, oiHighFlat: false, fundingNeutral: false, isVortex: false, maturityScore: 0 },
      resonance: { longTermCritical: false, shortTermNoise: false, triggerFactor: false, isResonance: false, bullish: false, confidence: 0 },
      phase,
      phaseConfidence: 0.5,
      spectralWidth: result.spectralWidth,
    };
  }

  private getEmptySignals(): NEMTSignals {
    return {
      dci: { value: 0.5, noiseState: 'medium', direction: 'neutral', trend: 'stable' },
      vortex: { bbwNarrow: false, volumeUniform: false, oiHighFlat: false, fundingNeutral: false, isVortex: false, maturityScore: 0 },
      resonance: { longTermCritical: false, shortTermNoise: false, triggerFactor: false, isResonance: false, bullish: false, confidence: 0 },
      phase: MarketPhase.PHASE_A_NOISE,
      phaseConfidence: 0,
      spectralWidth: null
    };
  }

  private generateMockVolumes(length: number): number[] {
    return Array.from({ length }, () => Math.random() * 1000000);
  }

  private generateMockOI(length: number): number[] {
    return Array.from({ length }, (_, i) => 50000000 + Math.sin(i / 10) * 10000000);
  }

  private generateMockFunding(length: number): number[] {
    return Array.from({ length }, () => (Math.random() - 0.5) * 0.001);
  }

  private generateMockBBW(length: number): number[] {
    return Array.from({ length }, (_, i) => 0.02 + Math.sin(i / 20) * 0.01 + Math.random() * 0.005);
  }
}

// =====================
// 单例
// =====================

let pipelineService: NEMTPipelineService | null = null;

export function getPipelineService(): NEMTPipelineService {
  if (!pipelineService) {
    pipelineService = new NEMTPipelineService();
  }
  return pipelineService;
}
