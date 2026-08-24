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
 * Notion 看板组件
 * 支持: 交易日志、策略流水线、研究任务、信号预警
 */

import React, { useState, useEffect, useCallback, useMemo } from 'react';
import {
  NotionBoardStatus,
  NotionPriority,
  NotionTag,
  NotionConfig,
  NotionSyncState,
  AnyNotionTask,
  TradeLogTask,
  StrategyPipelineTask,
  ResearchTask,
  SignalAlertTask,
  BOARD_STATUS_CONFIG,
  PRIORITY_CONFIG,
  TAG_CONFIG,
  DEFAULT_NOTION_CONFIG,
} from '../types/notion';
import { NotionService, initNotionService } from '../services/notionService';
import {
  LayoutDashboard,
  RefreshCw,
  Settings,
  Plus,
  X,
  ChevronDown,
  ChevronUp,
  ExternalLink,
  AlertCircle,
  CheckCircle,
  Clock,
  Trash2,
  Edit2,
  Save,
} from 'lucide-react';

// =====================
// 看板配置
// =====================

interface NotionBoardProps {
  initialConfig?: Partial<NotionConfig>;
  onTaskCreated?: (task: AnyNotionTask) => void;
  onTaskUpdated?: (task: AnyNotionTask) => void;
  onTaskDeleted?: (taskId: string) => void;
  onConfigChange?: (config: NotionConfig) => void;
}

// =====================
// 子组件
// =====================

/** 同步状态指示器 */
const SyncStatusBadge: React.FC<{ status: NotionSyncState['status']; error?: string | null }> = ({
  status,
  error,
}) => {
  const config = {
    idle: { icon: <Clock size={14} />, label: '空闲', color: '#6b7280', bg: '#f3f4f6' },
    syncing: { icon: <RefreshCw size={14} className="spin" />, label: '同步中...', color: '#3b82f6', bg: '#dbeafe' },
    success: { icon: <CheckCircle size={14} />, label: '已同步', color: '#10b981', bg: '#d1fae5' },
    error: { icon: <AlertCircle size={14} />, label: '错误', color: '#ef4444', bg: '#fee2e2' },
  };

  const current = config[status];

  return (
    <div
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: '6px',
        padding: '4px 12px',
        borderRadius: '20px',
        background: current.bg,
        color: current.color,
        fontSize: '12px',
        fontWeight: 500,
      }}
      title={error || undefined}
    >
      {current.icon}
      {current.label}
    </div>
  );
};

/** 优先级徽章 */
const PriorityBadge: React.FC<{ priority: NotionPriority }> = ({ priority }) => {
  const config = PRIORITY_CONFIG[priority];
  return (
    <span
      style={{
        padding: '2px 8px',
        borderRadius: '4px',
        background: config.color + '20',
        color: config.color,
        fontSize: '11px',
        fontWeight: 600,
      }}
    >
      {config.label}
    </span>
  );
};

/** 标签徽章 */
const TagBadge: React.FC<{ tag: NotionTag }> = ({ tag }) => {
  const config = TAG_CONFIG[tag];
  return (
    <span
      style={{
        padding: '2px 8px',
        borderRadius: '4px',
        background: config.color + '15',
        color: config.color,
        fontSize: '10px',
        fontWeight: 500,
      }}
    >
      {config.label}
    </span>
  );
};

/** 任务卡片 */
interface TaskCardProps {
  task: AnyNotionTask;
  onEdit: (task: AnyNotionTask) => void;
  onDelete: (taskId: string) => void;
  onStatusChange: (taskId: string, status: NotionBoardStatus) => void;
}

const TaskCard: React.FC<TaskCardProps> = ({ task, onEdit, onDelete, onStatusChange }) => {
  const [expanded, setExpanded] = useState(false);

  const renderTradeLogDetails = (t: TradeLogTask) => (
    <div style={{ marginTop: '12px', fontSize: '12px', color: '#666' }}>
      {t.symbol && <div>交易对: <strong>{t.symbol}</strong></div>}
      {t.direction && <div>方向: <strong style={{ color: t.direction === 'long' ? '#10b981' : '#ef4444' }}>{t.direction === 'long' ? '做多' : '做空'}</strong></div>}
      {t.entryPrice && <div>入场: <strong>${t.entryPrice.toLocaleString()}</strong></div>}
      {t.exitPrice && <div>出场: <strong>${t.exitPrice.toLocaleString()}</strong></div>}
      {t.pnl !== undefined && <div>盈亏: <strong style={{ color: t.pnl >= 0 ? '#10b981' : '#ef4444' }}>${t.pnl.toFixed(2)} ({t.pnlPercent?.toFixed(2) || 0}%)</strong></div>}
      {t.tradePhase && <div>相位: <strong>{t.tradePhase}</strong></div>}
      {t.leverage && <div>杠杆: <strong>{t.leverage}x</strong></div>}
    </div>
  );

  const renderStrategyDetails = (t: StrategyPipelineTask) => (
    <div style={{ marginTop: '12px', fontSize: '12px', color: '#666' }}>
      {t.strategyName && <div>策略名: <strong>{t.strategyName}</strong></div>}
      {t.stage && <div>阶段: <strong>{t.stage}</strong></div>}
      {t.backtestPeriod && <div>回测周期: <strong>{t.backtestPeriod}</strong></div>}
      {t.riskLevel && <div>风险等级: <strong style={{ color: t.riskLevel === 'high' ? '#ef4444' : t.riskLevel === 'medium' ? '#f59e0b' : '#10b981' }}>{t.riskLevel}</strong></div>}
    </div>
  );

  const renderSignalDetails = (t: SignalAlertTask) => (
    <div style={{ marginTop: '12px', fontSize: '12px', color: '#666' }}>
      {t.signalName && <div>信号名: <strong>{t.signalName}</strong></div>}
      {t.signalCategory && <div>类别: <strong>{t.signalCategory}</strong></div>}
      {t.signalStrength !== undefined && (
        <div>
          强度: 
          <div style={{ width: '100px', height: '6px', background: '#e5e7eb', borderRadius: '3px', marginTop: '4px' }}>
            <div style={{ width: `${t.signalStrength}%`, height: '100%', background: t.signalStrength > 70 ? '#ef4444' : t.signalStrength > 40 ? '#f59e0b' : '#10b981', borderRadius: '3px' }} />
          </div>
        </div>
      )}
      {t.symbol && <div>交易对: <strong>{t.symbol}</strong></div>}
      {t.marketPhase && <div>相位: <strong>{t.marketPhase}</strong></div>}
      {t.resolved !== undefined && <div>状态: <strong style={{ color: t.resolved ? '#10b981' : '#f59e0b' }}>{t.resolved ? '已解决' : '待处理'}</strong></div>}
    </div>
  );

  const renderResearchDetails = (t: ResearchTask) => (
    <div style={{ marginTop: '12px', fontSize: '12px', color: '#666' }}>
      {t.researchTopic && <div>主题: <strong>{t.researchTopic}</strong></div>}
      {t.researchType && <div>类型: <strong>{t.researchType}</strong></div>}
      {t.progress !== undefined && (
        <div>
          进度: 
          <div style={{ width: '100px', height: '6px', background: '#e5e7eb', borderRadius: '3px', marginTop: '4px' }}>
            <div style={{ width: `${t.progress}%`, height: '100%', background: '#3b82f6', borderRadius: '3px' }} />
          </div>
          <span style={{ fontSize: '10px' }}>{t.progress}%</span>
        </div>
      )}
      {t.deadline && <div>截止: <strong>{new Date(t.deadline).toLocaleDateString()}</strong></div>}
    </div>
  );

  const renderDetails = () => {
    switch (task.taskType) {
      case 'trade_log': return renderTradeLogDetails(task as TradeLogTask);
      case 'strategy_pipeline': return renderStrategyDetails(task as StrategyPipelineTask);
      case 'signal_alert': return renderSignalDetails(task as SignalAlertTask);
      case 'research_task': return renderResearchDetails(task as ResearchTask);
      default: return null;
    }
  };

  return (
    <div
      style={{
        background: 'white',
        borderRadius: '8px',
        padding: '12px',
        marginBottom: '8px',
        boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
        border: '1px solid #f0f0f0',
        transition: 'all 0.2s',
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.boxShadow = '0 2px 8px rgba(0,0,0,0.15)';
        e.currentTarget.style.borderColor = '#d9d9d9';
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.boxShadow = '0 1px 3px rgba(0,0,0,0.1)';
        e.currentTarget.style.borderColor = '#f0f0f0';
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div style={{ flex: 1 }}>
          <div style={{ fontSize: '13px', fontWeight: 500, color: '#1a1a2e', marginBottom: '6px' }}>
            {task.title}
          </div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px', marginBottom: '6px' }}>
            <PriorityBadge priority={task.priority} />
            {task.tags.slice(0, 3).map((tag) => (
              <TagBadge key={tag} tag={tag} />
            ))}
            {task.tags.length > 3 && (
              <span style={{ fontSize: '10px', color: '#888' }}>+{task.tags.length - 3}</span>
            )}
          </div>
        </div>
        <div style={{ display: 'flex', gap: '4px' }}>
          <button
            onClick={() => setExpanded(!expanded)}
            style={{ padding: '4px', border: 'none', background: 'none', cursor: 'pointer', color: '#666' }}
          >
            {expanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
          </button>
        </div>
      </div>

      {expanded && (
        <>
          {renderDetails()}
          {task.description && (
            <div style={{ marginTop: '8px', fontSize: '12px', color: '#666', fontStyle: 'italic' }}>
              {task.description}
            </div>
          )}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '12px', paddingTop: '8px', borderTop: '1px solid #f0f0f0' }}>
            <div style={{ fontSize: '10px', color: '#888' }}>
              更新于 {new Date(task.updatedAt).toLocaleDateString()}
            </div>
            <div style={{ display: 'flex', gap: '8px' }}>
              <select
                value={task.status}
                onChange={(e) => onStatusChange(task.id, e.target.value as NotionBoardStatus)}
                style={{ padding: '4px 8px', fontSize: '11px', borderRadius: '4px', border: '1px solid #d9d9d9' }}
              >
                {Object.entries(BOARD_STATUS_CONFIG).map(([key, config]) => (
                  <option key={key} value={key}>{config.label}</option>
                ))}
              </select>
              <button
                onClick={() => onEdit(task)}
                style={{ padding: '4px', border: 'none', background: 'none', cursor: 'pointer', color: '#3b82f6' }}
                title="编辑"
              >
                <Edit2 size={14} />
              </button>
              <button
                onClick={() => onDelete(task.id)}
                style={{ padding: '4px', border: 'none', background: 'none', cursor: 'pointer', color: '#ef4444' }}
                title="删除"
              >
                <Trash2 size={14} />
              </button>
              {task.notionUrl && (
                <a
                  href={task.notionUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  style={{ padding: '4px', color: '#666' }}
                  title="在 Notion 中打开"
                >
                  <ExternalLink size={14} />
                </a>
              )}
            </div>
          </div>
        </>
      )}
    </div>
  );
};

/** 新建任务表单 */
interface TaskFormProps {
  taskTypes: Array<{ value: string; label: string }>;
  onSubmit: (data: Partial<AnyNotionTask> & { title: string; status: NotionBoardStatus; priority: NotionPriority; tags: NotionTag[] }) => void;
  onCancel: () => void;
  initialData?: Partial<AnyNotionTask>;
}

const TaskForm: React.FC<TaskFormProps> = ({ taskTypes, onSubmit, onCancel, initialData }) => {
  const [title, setTitle] = useState(initialData?.title || '');
  const [description, setDescription] = useState(initialData?.description || '');
  const [status, setStatus] = useState<NotionBoardStatus>(initialData?.status || 'backlog');
  const [priority, setPriority] = useState<NotionPriority>(initialData?.priority || 'medium');
  const [tags, setTags] = useState<NotionTag[]>(initialData?.tags || []);
  const [taskType, setTaskType] = useState<string>(initialData?.taskType || 'research_task');

  // 任务类型特定字段
  const [symbol, setSymbol] = useState((initialData as TradeLogTask)?.symbol || '');
  const [direction, setDirection] = useState<'long' | 'short'>((initialData as TradeLogTask)?.direction || 'long');
  const [entryPrice, setEntryPrice] = useState((initialData as TradeLogTask)?.entryPrice?.toString() || '');
  const [strategyName, setStrategyName] = useState((initialData as StrategyPipelineTask)?.strategyName || '');
  const [stage, setStage] = useState<string>((initialData as StrategyPipelineTask)?.stage || 'idea');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim()) return;

    onSubmit({
      title: title.trim(),
      description,
      status,
      priority,
      tags,
      taskType: taskType as any,
      ...(taskType === 'trade_log' && { symbol, direction, entryPrice: entryPrice ? parseFloat(entryPrice) : undefined }),
      ...(taskType === 'strategy_pipeline' && { strategyName, stage }),
    });
  };

  const toggleTag = (tag: NotionTag) => {
    setTags((prev) => prev.includes(tag) ? prev.filter((t) => t !== tag) : [...prev, tag]);
  };

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      background: 'rgba(0,0,0,0.5)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 1000,
    }}>
      <div style={{
        background: 'white',
        borderRadius: '12px',
        padding: '24px',
        width: '90%',
        maxWidth: '500px',
        maxHeight: '90vh',
        overflow: 'auto',
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
          <h3 style={{ margin: 0, fontSize: '18px' }}>{initialData ? '编辑任务' : '新建任务'}</h3>
          <button onClick={onCancel} style={{ padding: '4px', border: 'none', background: 'none', cursor: 'pointer' }}>
            <X size={20} />
          </button>
        </div>

        <form onSubmit={handleSubmit}>
          {/* 标题 */}
          <div style={{ marginBottom: '16px' }}>
            <label style={{ display: 'block', fontSize: '13px', fontWeight: 500, marginBottom: '4px' }}>标题 *</label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="输入任务标题"
              required
              style={{
                width: '100%',
                padding: '8px 12px',
                border: '1px solid #d9d9d9',
                borderRadius: '6px',
                fontSize: '14px',
                boxSizing: 'border-box',
              }}
            />
          </div>

          {/* 任务类型 */}
          <div style={{ marginBottom: '16px' }}>
            <label style={{ display: 'block', fontSize: '13px', fontWeight: 500, marginBottom: '4px' }}>任务类型</label>
            <select
              value={taskType}
              onChange={(e) => setTaskType(e.target.value)}
              style={{
                width: '100%',
                padding: '8px 12px',
                border: '1px solid #d9d9d9',
                borderRadius: '6px',
                fontSize: '14px',
              }}
            >
              {taskTypes.map((t) => (
                <option key={t.value} value={t.value}>{t.label}</option>
              ))}
            </select>
          </div>

          {/* 任务类型特定字段 */}
          {taskType === 'trade_log' && (
            <div style={{ marginBottom: '16px' }}>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '13px', fontWeight: 500, marginBottom: '4px' }}>交易对</label>
                  <input
                    type="text"
                    value={symbol}
                    onChange={(e) => setSymbol(e.target.value)}
                    placeholder="BTCUSDT"
                    style={{ width: '100%', padding: '8px 12px', border: '1px solid #d9d9d9', borderRadius: '6px', fontSize: '14px' }}
                  />
                </div>
                <div>
                  <label style={{ display: 'block', fontSize: '13px', fontWeight: 500, marginBottom: '4px' }}>方向</label>
                  <select
                    value={direction}
                    onChange={(e) => setDirection(e.target.value as 'long' | 'short')}
                    style={{ width: '100%', padding: '8px 12px', border: '1px solid #d9d9d9', borderRadius: '6px', fontSize: '14px' }}
                  >
                    <option value="long">做多</option>
                    <option value="short">做空</option>
                  </select>
                </div>
              </div>
              <div style={{ marginTop: '12px' }}>
                <label style={{ display: 'block', fontSize: '13px', fontWeight: 500, marginBottom: '4px' }}>入场价格</label>
                <input
                  type="number"
                  value={entryPrice}
                  onChange={(e) => setEntryPrice(e.target.value)}
                  placeholder="0.00"
                  step="any"
                  style={{ width: '100%', padding: '8px 12px', border: '1px solid #d9d9d9', borderRadius: '6px', fontSize: '14px' }}
                />
              </div>
            </div>
          )}

          {taskType === 'strategy_pipeline' && (
            <div style={{ marginBottom: '16px' }}>
              <div style={{ marginBottom: '12px' }}>
                <label style={{ display: 'block', fontSize: '13px', fontWeight: 500, marginBottom: '4px' }}>策略名称</label>
                <input
                  type="text"
                  value={strategyName}
                  onChange={(e) => setStrategyName(e.target.value)}
                  placeholder="策略名称"
                  style={{ width: '100%', padding: '8px 12px', border: '1px solid #d9d9d9', borderRadius: '6px', fontSize: '14px' }}
                />
              </div>
              <div>
                <label style={{ display: 'block', fontSize: '13px', fontWeight: 500, marginBottom: '4px' }}>阶段</label>
                <select
                  value={stage}
                  onChange={(e) => setStage(e.target.value)}
                  style={{ width: '100%', padding: '8px 12px', border: '1px solid #d9d9d9', borderRadius: '6px', fontSize: '14px' }}
                >
                  <option value="idea">想法</option>
                  <option value="research">研究</option>
                  <option value="backtest">回测</option>
                  <option value="optimization">优化</option>
                  <option value="paper_trading">模拟交易</option>
                  <option value="live_ready">待实盘</option>
                  <option value="live">实盘中</option>
                </select>
              </div>
            </div>
          )}

          {/* 状态和优先级 */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '16px' }}>
            <div>
              <label style={{ display: 'block', fontSize: '13px', fontWeight: 500, marginBottom: '4px' }}>状态</label>
              <select
                value={status}
                onChange={(e) => setStatus(e.target.value as NotionBoardStatus)}
                style={{ width: '100%', padding: '8px 12px', border: '1px solid #d9d9d9', borderRadius: '6px', fontSize: '14px' }}
              >
                {Object.entries(BOARD_STATUS_CONFIG).map(([key, config]) => (
                  <option key={key} value={key}>{config.label}</option>
                ))}
              </select>
            </div>
            <div>
              <label style={{ display: 'block', fontSize: '13px', fontWeight: 500, marginBottom: '4px' }}>优先级</label>
              <select
                value={priority}
                onChange={(e) => setPriority(e.target.value as NotionPriority)}
                style={{ width: '100%', padding: '8px 12px', border: '1px solid #d9d9d9', borderRadius: '6px', fontSize: '14px' }}
              >
                {Object.entries(PRIORITY_CONFIG).map(([key, config]) => (
                  <option key={key} value={key}>{config.label}</option>
                ))}
              </select>
            </div>
          </div>

          {/* 标签 */}
          <div style={{ marginBottom: '16px' }}>
            <label style={{ display: 'block', fontSize: '13px', fontWeight: 500, marginBottom: '8px' }}>标签</label>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
              {(Object.keys(TAG_CONFIG) as NotionTag[]).map((tag) => (
                <button
                  key={tag}
                  type="button"
                  onClick={() => toggleTag(tag)}
                  style={{
                    padding: '4px 10px',
                    borderRadius: '4px',
                    border: '1px solid',
                    borderColor: tags.includes(tag) ? TAG_CONFIG[tag].color : '#d9d9d9',
                    background: tags.includes(tag) ? TAG_CONFIG[tag].color + '20' : 'white',
                    color: tags.includes(tag) ? TAG_CONFIG[tag].color : '#666',
                    fontSize: '12px',
                    cursor: 'pointer',
                  }}
                >
                  {TAG_CONFIG[tag].label}
                </button>
              ))}
            </div>
          </div>

          {/* 描述 */}
          <div style={{ marginBottom: '20px' }}>
            <label style={{ display: 'block', fontSize: '13px', fontWeight: 500, marginBottom: '4px' }}>描述</label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="任务描述..."
              rows={3}
              style={{
                width: '100%',
                padding: '8px 12px',
                border: '1px solid #d9d9d9',
                borderRadius: '6px',
                fontSize: '14px',
                resize: 'vertical',
              }}
            />
          </div>

          {/* 按钮 */}
          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px' }}>
            <button
              type="button"
              onClick={onCancel}
              style={{
                padding: '10px 20px',
                borderRadius: '6px',
                border: '1px solid #d9d9d9',
                background: 'white',
                cursor: 'pointer',
                fontSize: '14px',
              }}
            >
              取消
            </button>
            <button
              type="submit"
              style={{
                padding: '10px 20px',
                borderRadius: '6px',
                border: 'none',
                background: '#1890ff',
                color: 'white',
                cursor: 'pointer',
                fontSize: '14px',
                fontWeight: 500,
              }}
            >
              <Save size={14} style={{ marginRight: '6px', verticalAlign: 'middle' }} />
              {initialData ? '保存' : '创建'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

/** 配置面板 */
interface ConfigPanelProps {
  config: NotionConfig;
  onSave: (config: NotionConfig) => void;
  onClose: () => void;
}

const ConfigPanel: React.FC<ConfigPanelProps> = ({ config, onSave, onClose }) => {
  const [apiKey, setApiKey] = useState(config.apiKey);
  const [databaseId, setDatabaseId] = useState(config.databaseId);
  const [syncInterval, setSyncInterval] = useState(config.syncInterval / 1000);

  const handleSave = () => {
    onSave({
      ...config,
      apiKey,
      databaseId,
      syncInterval: syncInterval * 1000,
    });
    onClose();
  };

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      background: 'rgba(0,0,0,0.5)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 1000,
    }}>
      <div style={{
        background: 'white',
        borderRadius: '12px',
        padding: '24px',
        width: '90%',
        maxWidth: '500px',
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
          <h3 style={{ margin: 0, fontSize: '18px' }}>Notion 配置</h3>
          <button onClick={onClose} style={{ padding: '4px', border: 'none', background: 'none', cursor: 'pointer' }}>
            <X size={20} />
          </button>
        </div>

        <div style={{ marginBottom: '16px' }}>
          <label style={{ display: 'block', fontSize: '13px', fontWeight: 500, marginBottom: '4px' }}>
            API Key <span style={{ color: '#ef4444' }}>*</span>
          </label>
          <input
            type="password"
            value={apiKey}
            onChange={(e) => setApiKey(e.target.value)}
            placeholder="secret_xxxxxxxxxxxxxx"
            style={{
              width: '100%',
              padding: '8px 12px',
              border: '1px solid #d9d9d9',
              borderRadius: '6px',
              fontSize: '14px',
              boxSizing: 'border-box',
            }}
          />
          <div style={{ fontSize: '11px', color: '#888', marginTop: '4px' }}>
            在 Notion Integration 页面获取 API Key
          </div>
        </div>

        <div style={{ marginBottom: '16px' }}>
          <label style={{ display: 'block', fontSize: '13px', fontWeight: 500, marginBottom: '4px' }}>
            Database ID <span style={{ color: '#ef4444' }}>*</span>
          </label>
          <input
            type="text"
            value={databaseId}
            onChange={(e) => setDatabaseId(e.target.value)}
            placeholder="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
            style={{
              width: '100%',
              padding: '8px 12px',
              border: '1px solid #d9d9d9',
              borderRadius: '6px',
              fontSize: '14px',
              boxSizing: 'border-box',
            }}
          />
          <div style={{ fontSize: '11px', color: '#888', marginTop: '4px' }}>
            在 Notion 数据库页面 URL 中获取 (32位字符)
          </div>
        </div>

        <div style={{ marginBottom: '20px' }}>
          <label style={{ display: 'block', fontSize: '13px', fontWeight: 500, marginBottom: '4px' }}>
            同步间隔 (秒)
          </label>
          <input
            type="number"
            value={syncInterval}
            onChange={(e) => setSyncInterval(parseInt(e.target.value) || 30)}
            min={10}
            max={300}
            style={{
              width: '100%',
              padding: '8px 12px',
              border: '1px solid #d9d9d9',
              borderRadius: '6px',
              fontSize: '14px',
              boxSizing: 'border-box',
            }}
          />
        </div>

        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px' }}>
          <button
            onClick={onClose}
            style={{
              padding: '10px 20px',
              borderRadius: '6px',
              border: '1px solid #d9d9d9',
              background: 'white',
              cursor: 'pointer',
              fontSize: '14px',
            }}
          >
            取消
          </button>
          <button
            onClick={handleSave}
            disabled={!apiKey || !databaseId}
            style={{
              padding: '10px 20px',
              borderRadius: '6px',
              border: 'none',
              background: (!apiKey || !databaseId) ? '#ccc' : '#1890ff',
              color: 'white',
              cursor: (!apiKey || !databaseId) ? 'not-allowed' : 'pointer',
              fontSize: '14px',
              fontWeight: 500,
            }}
          >
            保存配置
          </button>
        </div>
      </div>
    </div>
  );
};

// =====================
// 主组件
// =====================

export const NotionBoard: React.FC<NotionBoardProps> = ({
  initialConfig,
  onTaskCreated,
  onTaskUpdated,
  onTaskDeleted,
  onConfigChange,
}) => {
  const [config, setConfig] = useState<NotionConfig>({
    ...DEFAULT_NOTION_CONFIG,
    ...initialConfig,
  });
  const [tasks, setTasks] = useState<AnyNotionTask[]>([]);
  const [syncState, setSyncState] = useState<NotionSyncState>({
    status: 'idle',
    lastSyncTime: null,
    error: null,
    pendingChanges: 0,
  });
  const [showConfig, setShowConfig] = useState(!initialConfig?.apiKey);
  const [showTaskForm, setShowTaskForm] = useState(false);
  const [editingTask, setEditingTask] = useState<AnyNotionTask | null>(null);
  const [activeFilters, setActiveFilters] = useState<{
    status?: NotionBoardStatus;
    priority?: NotionPriority;
    tag?: NotionTag;
    taskType?: string;
  }>({});
  const [service, setService] = useState<NotionService | null>(null);

  // 初始化服务
  useEffect(() => {
    if (config.apiKey && config.databaseId) {
      const notionService = initNotionService(config);
      setService(notionService);

      const unsubscribe = notionService.subscribe((state) => {
        setSyncState(state);
      });

      return () => unsubscribe();
    }
  }, [config.apiKey, config.databaseId]);

  // 同步任务
  const syncTasks = useCallback(async () => {
    if (!service) return;
    try {
      const fetchedTasks = await service.syncTasks();
      setTasks(fetchedTasks);
    } catch (error) {
      console.error('Sync error:', error);
    }
  }, [service]);

  // 初始同步
  useEffect(() => {
    if (service && config.apiKey && config.databaseId) {
      syncTasks();
    }
  }, [service, syncTasks, config.apiKey, config.databaseId]);

  // 定时同步
  useEffect(() => {
    if (!config.enabled || !service) return;

    const interval = setInterval(syncTasks, config.syncInterval);
    return () => clearInterval(interval);
  }, [config.enabled, config.syncInterval, service, syncTasks]);

  // 过滤任务
  const filteredTasks = useMemo(() => {
    return tasks.filter((task) => {
      if (activeFilters.status && task.status !== activeFilters.status) return false;
      if (activeFilters.priority && task.priority !== activeFilters.priority) return false;
      if (activeFilters.tag && !task.tags.includes(activeFilters.tag as NotionTag)) return false;
      if (activeFilters.taskType && task.taskType !== activeFilters.taskType) return false;
      return true;
    });
  }, [tasks, activeFilters]);

  // 按状态分组
  const groupedTasks = useMemo(() => {
    const columns: Record<NotionBoardStatus, AnyNotionTask[]> = {
      backlog: [],
      in_progress: [],
      review: [],
      completed: [],
      archived: [],
    };

    filteredTasks.forEach((task) => {
      if (columns[task.status]) {
        columns[task.status].push(task);
      }
    });

    return columns;
  }, [filteredTasks]);

  // 创建任务
  const handleCreateTask = async (data: Parameters<typeof TaskForm>[0]['onSubmit'] extends (data: infer T) => void ? T : never) => {
    if (!service) return;

    try {
      await service.createTask(data as any);
      await syncTasks();
      setShowTaskForm(false);
      onTaskCreated?.(data as any);
    } catch (error) {
      console.error('Create task error:', error);
    }
  };

  // 更新任务
  const handleUpdateTask = async (data: Parameters<typeof TaskForm>[0]['onSubmit'] extends (data: infer T) => void ? T : never) => {
    if (!service || !editingTask) return;

    try {
      await service.updateTask({
        taskId: editingTask.id,
        updates: data as any,
      });
      await syncTasks();
      setEditingTask(null);
      onTaskUpdated?.(data as any);
    } catch (error) {
      console.error('Update task error:', error);
    }
  };

  // 删除任务
  const handleDeleteTask = async (taskId: string) => {
    if (!service) return;
    if (!confirm('确定要删除这个任务吗？')) return;

    try {
      await service.archiveTask(taskId);
      await syncTasks();
      onTaskDeleted?.(taskId);
    } catch (error) {
      console.error('Delete task error:', error);
    }
  };

  // 快速更新状态
  const handleStatusChange = async (taskId: string, newStatus: NotionBoardStatus) => {
    if (!service) return;

    try {
      await service.updateTask({
        taskId,
        updates: { status: newStatus },
      });
      setTasks((prev) =>
        prev.map((t) => (t.id === taskId ? { ...t, status: newStatus } : t))
      );
    } catch (error) {
      console.error('Status change error:', error);
    }
  };

  const taskTypes = [
    { value: 'research_task', label: '研究任务' },
    { value: 'trade_log', label: '交易日志' },
    { value: 'strategy_pipeline', label: '策略流水线' },
    { value: 'signal_alert', label: '信号预警' },
  ];

  return (
    <div style={{ padding: '0' }}>
      {/* 工具栏 */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: '20px',
        flexWrap: 'wrap',
        gap: '12px',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <h2 style={{ margin: 0, fontSize: '20px', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '8px' }}>
            <LayoutDashboard size={24} color="#1890ff" />
            Notion 看板
          </h2>
          <SyncStatusBadge status={syncState.status} error={syncState.error} />
          {syncState.lastSyncTime && (
            <span style={{ fontSize: '12px', color: '#888' }}>
              上次同步: {new Date(syncState.lastSyncTime).toLocaleTimeString()}
            </span>
          )}
        </div>

        <div style={{ display: 'flex', gap: '8px' }}>
          <button
            onClick={syncTasks}
            disabled={syncState.status === 'syncing'}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              padding: '8px 16px',
              border: '1px solid #d9d9d9',
              borderRadius: '6px',
              background: 'white',
              cursor: 'pointer',
              fontSize: '13px',
            }}
          >
            <RefreshCw size={14} className={syncState.status === 'syncing' ? 'spin' : ''} />
            同步
          </button>
          <button
            onClick={() => setShowTaskForm(true)}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              padding: '8px 16px',
              border: 'none',
              borderRadius: '6px',
              background: '#1890ff',
              color: 'white',
              cursor: 'pointer',
              fontSize: '13px',
              fontWeight: 500,
            }}
          >
            <Plus size={14} />
            新建任务
          </button>
          <button
            onClick={() => setShowConfig(true)}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              padding: '8px 16px',
              border: '1px solid #d9d9d9',
              borderRadius: '6px',
              background: 'white',
              cursor: 'pointer',
              fontSize: '13px',
            }}
          >
            <Settings size={14} />
            配置
          </button>
        </div>
      </div>

      {/* 过滤器 */}
      <div style={{
        display: 'flex',
        gap: '8px',
        marginBottom: '20px',
        flexWrap: 'wrap',
      }}>
        <select
          value={activeFilters.taskType || ''}
          onChange={(e) => setActiveFilters({ ...activeFilters, taskType: e.target.value || undefined })}
          style={{ padding: '6px 12px', borderRadius: '6px', border: '1px solid #d9d9d9', fontSize: '13px' }}
        >
          <option value="">所有类型</option>
          {taskTypes.map((t) => (
            <option key={t.value} value={t.value}>{t.label}</option>
          ))}
        </select>
        <select
          value={activeFilters.priority || ''}
          onChange={(e) => setActiveFilters({ ...activeFilters, priority: e.target.value as NotionPriority || undefined })}
          style={{ padding: '6px 12px', borderRadius: '6px', border: '1px solid #d9d9d9', fontSize: '13px' }}
        >
          <option value="">所有优先级</option>
          {Object.entries(PRIORITY_CONFIG).map(([key, config]) => (
            <option key={key} value={key}>{config.label}</option>
          ))}
        </select>
        <select
          value={activeFilters.tag || ''}
          onChange={(e) => setActiveFilters({ ...activeFilters, tag: e.target.value as NotionTag || undefined })}
          style={{ padding: '6px 12px', borderRadius: '6px', border: '1px solid #d9d9d9', fontSize: '13px' }}
        >
          <option value="">所有标签</option>
          {(Object.keys(TAG_CONFIG) as NotionTag[]).map((tag) => (
            <option key={tag} value={tag}>{TAG_CONFIG[tag].label}</option>
          ))}
        </select>
        {(activeFilters.taskType || activeFilters.priority || activeFilters.tag) && (
          <button
            onClick={() => setActiveFilters({})}
            style={{
              padding: '6px 12px',
              borderRadius: '6px',
              border: 'none',
              background: '#f0f0f0',
              color: '#666',
              fontSize: '13px',
              cursor: 'pointer',
            }}
          >
            清除筛选
          </button>
        )}
        <span style={{ marginLeft: 'auto', fontSize: '12px', color: '#888', alignSelf: 'center' }}>
          共 {filteredTasks.length} 个任务
        </span>
      </div>

      {/* 看板列 */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
        gap: '16px',
      }}>
        {(Object.entries(BOARD_STATUS_CONFIG) as [NotionBoardStatus, { label: string; color: string }][]).map(
          ([status, config]) => (
            <div
              key={status}
              style={{
                background: '#f8f9fa',
                borderRadius: '12px',
                padding: '16px',
                minHeight: '400px',
              }}
            >
              <div style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                marginBottom: '16px',
                paddingBottom: '12px',
                borderBottom: `3px solid ${config.color}`,
              }}>
                <span style={{ fontSize: '14px', fontWeight: 600, color: config.color }}>
                  {config.label}
                </span>
                <span style={{
                  background: config.color + '20',
                  color: config.color,
                  padding: '2px 8px',
                  borderRadius: '10px',
                  fontSize: '11px',
                  fontWeight: 600,
                }}>
                  {groupedTasks[status].length}
                </span>
              </div>

              <div style={{ minHeight: '300px' }}>
                {groupedTasks[status].map((task) => (
                  <TaskCard
                    key={task.id}
                    task={task}
                    onEdit={setEditingTask}
                    onDelete={handleDeleteTask}
                    onStatusChange={handleStatusChange}
                  />
                ))}
                {groupedTasks[status].length === 0 && (
                  <div style={{
                    textAlign: 'center',
                    padding: '40px 20px',
                    color: '#888',
                    fontSize: '13px',
                  }}>
                    暂无任务
                  </div>
                )}
              </div>
            </div>
          )
        )}
      </div>

      {/* 任务统计 */}
      <div style={{
        marginTop: '20px',
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
        gap: '12px',
      }}>
        {([
          { label: '待办', status: 'backlog' as NotionBoardStatus },
          { label: '进行中', status: 'in_progress' as NotionBoardStatus },
          { label: '审核', status: 'review' as NotionBoardStatus },
          { label: '已完成', status: 'completed' as NotionBoardStatus },
        ]).map(({ label, status }) => (
          <div
            key={status}
            style={{
              background: 'white',
              borderRadius: '8px',
              padding: '16px',
              textAlign: 'center',
              boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
            }}
          >
            <div style={{ fontSize: '24px', fontWeight: 700, color: BOARD_STATUS_CONFIG[status].color }}>
              {groupedTasks[status].length}
            </div>
            <div style={{ fontSize: '12px', color: '#666', marginTop: '4px' }}>{label}</div>
          </div>
        ))}
      </div>

      {/* 弹窗 */}
      {showConfig && (
        <ConfigPanel
          config={config}
          onSave={(newConfig) => {
            setConfig(newConfig);
            localStorage.setItem('notion_config', JSON.stringify(newConfig));
            onConfigChange?.(newConfig);
          }}
          onClose={() => setShowConfig(false)}
        />
      )}

      {(showTaskForm || editingTask) && (
        <TaskForm
          taskTypes={taskTypes}
          initialData={editingTask || undefined}
          onSubmit={editingTask ? handleUpdateTask : handleCreateTask}
          onCancel={() => {
            setShowTaskForm(false);
            setEditingTask(null);
          }}
        />
      )}

      {/* 动画样式 */}
      <style>{`
        @keyframes spin {
          to { transform: rotate(360deg); }
        }
        .spin {
          animation: spin 1s linear infinite;
        }
      `}</style>
    </div>
  );
};

export default NotionBoard;
