/**
 * Copyright 2026 NEMT Lab
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

/**
 * Notion API 服务层
 * 处理与 Notion API 的所有交互
 */

import {
  NotionConfig,
  NotionTask,
  NotionBoardStatus,
  NotionPriority,
  NotionTag,
  NotionSyncState,
  CreateTaskRequest,
  UpdateTaskRequest,
  AnyNotionTask,
  TradeLogTask,
  StrategyPipelineTask,
  ResearchTask,
  SignalAlertTask,
  NOTION_API_BASE,
  NOTION_API_VERSION,
  NotionPage,
  NotionQueryResponse,
} from '../types/notion';

// =====================
// 错误处理
// =====================

export class NotionAPIError extends Error {
  constructor(
    message: string,
    public statusCode?: number,
    public code?: string
  ) {
    super(message);
    this.name = 'NotionAPIError';
  }
}

// =====================
// Notion Service 类
// =====================

export class NotionService {
  private apiKey: string;
  private databaseId: string;
  private syncState: NotionSyncState;
  private listeners: Set<(state: NotionSyncState) => void> = new Set();

  constructor(config: NotionConfig) {
    this.apiKey = config.apiKey;
    this.databaseId = config.databaseId;
    this.syncState = {
      status: 'idle',
      lastSyncTime: null,
      error: null,
      pendingChanges: 0,
    };
  }

  // =====================
  // 配置管理
  // =====================

  updateConfig(config: Partial<NotionConfig>): void {
    if (config.apiKey !== undefined) this.apiKey = config.apiKey;
    if (config.databaseId !== undefined) this.databaseId = config.databaseId;
  }

  isConfigured(): boolean {
    return Boolean(this.apiKey && this.databaseId);
  }

  // =====================
  // 状态管理
  // =====================

  getSyncState(): NotionSyncState {
    return { ...this.syncState };
  }

  subscribe(listener: (state: NotionSyncState) => void): () => void {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }

  private notifyListeners(): void {
    this.listeners.forEach((listener) => listener({ ...this.syncState }));
  }

  private setState(updates: Partial<NotionSyncState>): void {
    this.syncState = { ...this.syncState, ...updates };
    this.notifyListeners();
  }

  // =====================
  // API 请求辅助方法
  // =====================

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    if (!this.apiKey) {
      throw new NotionAPIError('Notion API key is not configured');
    }

    const url = `${NOTION_API_BASE}${endpoint}`;
    
    const response = await fetch(url, {
      ...options,
      headers: {
        'Authorization': `Bearer ${this.apiKey}`,
        'Notion-Version': NOTION_API_VERSION,
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new NotionAPIError(
        error.message || `Notion API error: ${response.status}`,
        response.status,
        error.code
      );
    }

    return response.json();
  }

  // =====================
  // 数据库操作
  // =====================

  /**
   * 查询数据库中的所有任务
   */
  async queryTasks(
    filter?: {
      status?: NotionBoardStatus;
      priority?: NotionPriority;
      tag?: NotionTag;
    },
    sorts?: Array<{ property: string; direction: 'ascending' | 'descending' }>
  ): Promise<NotionPage[]> {
    const body: Record<string, unknown> = {
      page_size: 100,
    };

    // 构建过滤条件
    if (filter) {
      const conditions: Record<string, unknown>[] = [];
      
      if (filter.status) {
        conditions.push({
          property: 'Status',
          select: { equals: filter.status },
        });
      }
      
      if (filter.priority) {
        conditions.push({
          property: 'Priority',
          select: { equals: filter.priority },
        });
      }
      
      if (filter.tag) {
        conditions.push({
          property: 'Tags',
          multi_select: { contains: filter.tag },
        });
      }
      
      if (conditions.length === 1) {
        body.filter = conditions[0];
      } else if (conditions.length > 1) {
        body.filter = { and: conditions };
      }
    }

    // 排序
    if (sorts && sorts.length > 0) {
      body.sorts = sorts.map((s) => ({
        property: s.property,
        direction: s.direction,
      }));
    } else {
      body.sorts = [{ property: 'Created', direction: 'descending' }];
    }

    const response = await this.request<NotionQueryResponse>(
      `/databases/${this.databaseId}/query`,
      { method: 'POST', body: JSON.stringify(body) }
    );

    return response.results;
  }

  /**
   * 获取单个页面详情
   */
  async getPage(pageId: string): Promise<NotionPage> {
    return this.request<NotionPage>(`/pages/${pageId}`);
  }

  /**
   * 创建新任务
   */
  async createTask(request: CreateTaskRequest): Promise<NotionPage> {
    const properties: Record<string, unknown> = {
      Name: {
        title: [{ text: { content: request.title } }],
      },
      Status: {
        select: { name: request.status },
      },
      Priority: {
        select: { name: request.priority },
      },
      Tags: {
        multi_select: request.tags.map((tag) => ({ name: tag })),
      },
      Created: {
        date: { start: new Date().toISOString() },
      },
      Type: {
        select: { name: request.taskType },
      },
    };

    if (request.description) {
      properties['Description'] = {
        rich_text: [{ text: { content: request.description } }],
      };
    }

    // 添加类型特定字段
    const typeSpecificProps = this.buildTypeSpecificProperties(request);
    Object.assign(properties, typeSpecificProps);

    return this.request<NotionPage>(`/pages`, {
      method: 'POST',
      body: JSON.stringify({
        parent: { database_id: this.databaseId },
        properties,
      }),
    });
  }

  /**
   * 更新任务
   */
  async updateTask(request: UpdateTaskRequest): Promise<NotionPage> {
    const properties: Record<string, unknown> = {};

    if (request.updates.title !== undefined) {
      properties['Name'] = {
        title: [{ text: { content: request.updates.title } }],
      };
    }

    if (request.updates.status !== undefined) {
      properties['Status'] = {
        select: { name: request.updates.status },
      };
    }

    if (request.updates.priority !== undefined) {
      properties['Priority'] = {
        select: { name: request.updates.priority },
      };
    }

    if (request.updates.tags !== undefined) {
      properties['Tags'] = {
        multi_select: request.updates.tags.map((tag) => ({ name: tag })),
      };
    }

    if (request.updates.description !== undefined) {
      properties['Description'] = {
        rich_text: [{ text: { content: request.updates.description } }],
      };
    }

    return this.request<NotionPage>(`/pages/${request.taskId}`, {
      method: 'PATCH',
      body: JSON.stringify({ properties }),
    });
  }

  /**
   * 删除任务 (归档)
   */
  async archiveTask(taskId: string): Promise<NotionPage> {
    return this.request<NotionPage>(`/pages/${taskId}`, {
      method: 'PATCH',
      body: JSON.stringify({ archived: true }),
    });
  }

  /**
   * 恢复归档的任务
   */
  async restoreTask(taskId: string): Promise<NotionPage> {
    return this.request<NotionPage>(`/pages/${taskId}`, {
      method: 'PATCH',
      body: JSON.stringify({ archived: false }),
    });
  }

  // =====================
  // 同步操作
  // =====================

  /**
   * 同步所有任务
   */
  async syncTasks(): Promise<AnyNotionTask[]> {
    if (!this.isConfigured()) {
      throw new NotionAPIError('Notion is not configured');
    }

    this.setState({ status: 'syncing', error: null });

    try {
      const pages = await this.queryTasks();
      const tasks = pages.map((page) => this.parseNotionPage(page));
      
      this.setState({
        status: 'success',
        lastSyncTime: new Date().toISOString(),
        error: null,
      });

      return tasks;
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      this.setState({
        status: 'error',
        error: errorMessage,
      });
      throw error;
    }
  }

  // =====================
  // 辅助方法
  // =====================

  /**
   * 解析 Notion Page 为任务对象
   */
  private parseNotionPage(page: NotionPage): AnyNotionTask {
    const props = page.properties;
    
    const baseTask = {
      id: page.id,
      notionPageId: page.id,
      notionUrl: page.url,
      title: this.extractText(props.Name?.title),
      status: this.extractSelect(props.Status) as NotionBoardStatus,
      priority: this.extractSelect(props.Priority) as NotionPriority,
      tags: this.extractMultiSelect(props.Tags),
      createdAt: props.Created?.date?.start || page.created_time,
      updatedAt: page.last_edited_time,
      description: this.extractText(props.Description?.rich_text),
      taskType: (this.extractSelect(props.Type) || 'research_task') as NotionTask['taskType'],
    };

    // 根据任务类型解析特定字段
    const taskType = baseTask.taskType;
    
    if (taskType === 'trade_log') {
      return this.parseTradeLogTask(page, baseTask);
    } else if (taskType === 'strategy_pipeline') {
      return this.parseStrategyPipelineTask(page, baseTask);
    } else if (taskType === 'signal_alert') {
      return this.parseSignalAlertTask(page, baseTask);
    } else {
      return this.parseResearchTask(page, baseTask);
    }
  }

  private parseTradeLogTask(page: NotionPage, base: Partial<NotionTask>): TradeLogTask {
    const props = page.properties;
    return {
      ...base as NotionTask,
      taskType: 'trade_log',
      symbol: this.extractText(props.Symbol?.rich_text),
      direction: this.extractSelect(props.Direction) as 'long' | 'short' | undefined,
      entryPrice: props.EntryPrice?.number,
      exitPrice: props.ExitPrice?.number,
      positionSize: props.PositionSize?.number,
      pnl: props.PnL?.number,
      pnlPercent: props.PnLPercent?.number,
      tradePhase: this.extractSelect(props.TradePhase),
      signalType: this.extractSelect(props.SignalType),
      entryReason: this.extractText(props.EntryReason?.rich_text),
      exitReason: this.extractText(props.ExitReason?.rich_text),
      stopLoss: props.StopLoss?.number,
      takeProfit: props.TakeProfit?.number,
      leverage: props.Leverage?.number,
      openedAt: props.OpenedAt?.date?.start,
      closedAt: props.ClosedAt?.date?.start,
      spectralWidth: props.SpectralWidth?.number,
      dciValue: props.DCIValue?.number,
      vortexMaturity: props.VortexMaturity?.number,
      resonanceConfidence: props.ResonanceConfidence?.number,
    };
  }

  private parseStrategyPipelineTask(page: NotionPage, base: Partial<NotionTask>): StrategyPipelineTask {
    const props = page.properties;
    return {
      ...base as NotionTask,
      taskType: 'strategy_pipeline',
      strategyName: this.extractText(props.StrategyName?.rich_text),
      stage: (this.extractSelect(props.Stage) || 'idea') as any,
      previousStage: this.extractSelect(props.PreviousStage) as any,
      backtestPeriod: this.extractText(props.BacktestPeriod?.rich_text),
      riskLevel: this.extractSelect(props.RiskLevel) as 'low' | 'medium' | 'high' | undefined,
      notes: this.extractText(props.Notes?.rich_text),
    };
  }

  private parseSignalAlertTask(page: NotionPage, base: Partial<NotionTask>): SignalAlertTask {
    const props = page.properties;
    return {
      ...base as NotionTask,
      taskType: 'signal_alert',
      signalName: this.extractText(props.SignalName?.rich_text),
      signalCategory: this.extractSelect(props.SignalCategory) as any,
      signalStrength: props.SignalStrength?.number,
      signalValue: props.SignalValue?.number,
      threshold: props.Threshold?.number,
      symbol: this.extractText(props.Symbol?.rich_text),
      marketPhase: this.extractSelect(props.MarketPhase),
      priceLevel: props.PriceLevel?.number,
      acknowledged: props.Acknowledged?.checkbox,
      actionTaken: this.extractText(props.ActionTaken?.rich_text),
      resolved: props.Resolved?.checkbox,
      triggeredAt: props.TriggeredAt?.date?.start,
      acknowledgedAt: props.AcknowledgedAt?.date?.start,
      resolvedAt: props.ResolvedAt?.date?.start,
    };
  }

  private parseResearchTask(page: NotionPage, base: Partial<NotionTask>): ResearchTask {
    const props = page.properties;
    return {
      ...base as NotionTask,
      taskType: 'research_task',
      researchTopic: this.extractText(props.ResearchTopic?.rich_text),
      researchType: this.extractSelect(props.ResearchType) as any,
      findings: this.extractText(props.Findings?.rich_text),
      conclusion: this.extractText(props.Conclusion?.rich_text),
      progress: props.Progress?.number,
      deadline: props.Deadline?.date?.start,
    };
  }

  private extractText(value?: unknown): string {
    if (!value || !Array.isArray(value)) return '';
    return (value as Array<{ plain_text: string }>).map((v) => v.plain_text).join('');
  }

  private extractSelect(value?: unknown): string {
    const prop = value as { name?: string } | undefined;
    return prop?.name || '';
  }

  private extractMultiSelect(value?: unknown): NotionTag[] {
    if (!value || !Array.isArray(value)) return [];
    return (value as Array<{ name: string }>).map((v) => v.name as NotionTag);
  }

  /**
   * 构建类型特定的属性
   */
  private buildTypeSpecificProperties(request: CreateTaskRequest): Record<string, unknown> {
    const props: Record<string, unknown> = {};

    if (request.taskType === 'trade_log') {
      const tradeData = request as CreateTaskRequest & Partial<TradeLogTask>;
      if (tradeData.symbol) props['Symbol'] = { rich_text: [{ text: { content: tradeData.symbol } }] };
      if (tradeData.direction) props['Direction'] = { select: { name: tradeData.direction } };
      if (tradeData.entryPrice) props['EntryPrice'] = { number: tradeData.entryPrice };
      if (tradeData.exitPrice) props['ExitPrice'] = { number: tradeData.exitPrice };
      if (tradeData.positionSize) props['PositionSize'] = { number: tradeData.positionSize };
      if (tradeData.pnl) props['PnL'] = { number: tradeData.pnl };
      if (tradeData.pnlPercent) props['PnLPercent'] = { number: tradeData.pnlPercent };
    }

    if (request.taskType === 'strategy_pipeline') {
      const strategyData = request as CreateTaskRequest & Partial<StrategyPipelineTask>;
      if (strategyData.strategyName) props['StrategyName'] = { rich_text: [{ text: { content: strategyData.strategyName } }] };
      if (strategyData.stage) props['Stage'] = { select: { name: strategyData.stage } };
      if (strategyData.riskLevel) props['RiskLevel'] = { select: { name: strategyData.riskLevel } };
    }

    if (request.taskType === 'signal_alert') {
      const signalData = request as CreateTaskRequest & Partial<SignalAlertTask>;
      if (signalData.signalName) props['SignalName'] = { rich_text: [{ text: { content: signalData.signalName } }] };
      if (signalData.signalCategory) props['SignalCategory'] = { select: { name: signalData.signalCategory } };
      if (signalData.signalStrength) props['SignalStrength'] = { number: signalData.signalStrength };
      if (signalData.symbol) props['Symbol'] = { rich_text: [{ text: { content: signalData.symbol } }] };
    }

    if (request.taskType === 'research_task') {
      const researchData = request as CreateTaskRequest & Partial<ResearchTask>;
      if (researchData.researchTopic) props['ResearchTopic'] = { rich_text: [{ text: { content: researchData.researchTopic } }] };
      if (researchData.researchType) props['ResearchType'] = { select: { name: researchData.researchType } };
      if (researchData.progress !== undefined) props['Progress'] = { number: researchData.progress };
      if (researchData.deadline) props['Deadline'] = { date: { start: researchData.deadline } };
    }

    return props;
  }
}

// =====================
// 工厂函数
// =====================

let notionServiceInstance: NotionService | null = null;

export function getNotionService(config?: NotionConfig): NotionService {
  if (!notionServiceInstance && config) {
    notionServiceInstance = new NotionService(config);
  }
  if (!notionServiceInstance) {
    throw new Error('NotionService not initialized');
  }
  return notionServiceInstance;
}

export function initNotionService(config: NotionConfig): NotionService {
  notionServiceInstance = new NotionService(config);
  return notionServiceInstance;
}
