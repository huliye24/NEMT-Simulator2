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
 * 本地看板组件
 * 不依赖外部API，数据保存在 localStorage
 */

import React, { useState, useEffect, useCallback, useMemo } from 'react';
import {
  LayoutDashboard,
  Plus,
  X,
  ChevronDown,
  ChevronUp,
  Edit2,
  Trash2,
  Save,
  GripVertical,
  Calendar,
  Tag,
  Filter,
} from 'lucide-react';

// =====================
// 类型定义
// =====================

export type KanbanStatus = 'backlog' | 'todo' | 'in_progress' | 'review' | 'done';
export type Priority = 'low' | 'medium' | 'high' | 'urgent';

export interface KanbanTask {
  id: string;
  title: string;
  description?: string;
  status: KanbanStatus;
  priority: Priority;
  tags: string[];
  createdAt: string;
  updatedAt: string;
  dueDate?: string;
  assignee?: string;
  order: number;
}

// =====================
// 配置
// =====================

export const STATUS_CONFIG: Record<KanbanStatus, { label: string; color: string; bgColor: string }> = {
  backlog: { label: '待归档', color: '#6b7280', bgColor: '#f3f4f6' },
  todo: { label: '待办', color: '#3b82f6', bgColor: '#dbeafe' },
  in_progress: { label: '进行中', color: '#f59e0b', bgColor: '#fef3c7' },
  review: { label: '审核', color: '#8b5cf6', bgColor: '#ede9fe' },
  done: { label: '已完成', color: '#10b981', bgColor: '#d1fae5' },
};

export const PRIORITY_CONFIG: Record<Priority, { label: string; color: string; bgColor: string }> = {
  low: { label: '低', color: '#6b7280', bgColor: '#f3f4f6' },
  medium: { label: '中', color: '#3b82f6', bgColor: '#dbeafe' },
  high: { label: '高', color: '#f59e0b', bgColor: '#fef3c7' },
  urgent: { label: '紧急', color: '#ef4444', bgColor: '#fee2e2' },
};

export const TAG_OPTIONS = [
  { id: 'analysis', label: '分析', color: '#3b82f6' },
  { id: 'backtest', label: '回测', color: '#10b981' },
  { id: 'live', label: '实盘', color: '#ef4444' },
  { id: 'research', label: '研究', color: '#8b5cf6' },
  { id: 'development', label: '开发', color: '#f59e0b' },
  { id: 'review', label: '审核', color: '#ec4899' },
  { id: 'vortex', label: '涡旋', color: '#06b6d4' },
  { id: 'resonance', label: '共振', color: '#84cc16' },
  { id: 'trend', label: '趋势', color: '#6366f1' },
  { id: 'risk', label: '风控', color: '#f43f5e' },
];

// =====================
// 工具函数
// =====================

const generateId = () => `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;

const loadTasks = (): KanbanTask[] => {
  try {
    const saved = localStorage.getItem('kanban_tasks');
    return saved ? JSON.parse(saved) : [];
  } catch {
    return [];
  }
};

const saveTasks = (tasks: KanbanTask[]) => {
  localStorage.setItem('kanban_tasks', JSON.stringify(tasks));
};

// =====================
// 子组件
// =====================

/** 优先级徽章 */
const PriorityBadge: React.FC<{ priority: Priority }> = ({ priority }) => {
  const config = PRIORITY_CONFIG[priority];
  return (
    <span
      style={{
        padding: '2px 8px',
        borderRadius: '4px',
        background: config.bgColor,
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
const TagBadge: React.FC<{ tag: string }> = ({ tag }) => {
  const config = TAG_OPTIONS.find(t => t.id === tag);
  if (!config) return null;
  return (
    <span
      style={{
        padding: '2px 6px',
        borderRadius: '3px',
        background: config.color + '20',
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
  task: KanbanTask;
  onEdit: (task: KanbanTask) => void;
  onDelete: (taskId: string) => void;
  onStatusChange: (taskId: string, status: KanbanStatus) => void;
}

const TaskCard: React.FC<TaskCardProps> = ({ task, onEdit, onDelete, onStatusChange }) => {
  const [expanded, setExpanded] = useState(false);
  const statusConfig = STATUS_CONFIG[task.status];

  return (
    <div
      draggable
      style={{
        background: 'white',
        borderRadius: '8px',
        padding: '12px',
        marginBottom: '8px',
        boxShadow: '0 1px 3px rgba(0,0,0,0.08)',
        border: '1px solid #e5e7eb',
        cursor: 'grab',
        transition: 'all 0.2s',
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.boxShadow = '0 4px 12px rgba(0,0,0,0.12)';
        e.currentTarget.style.transform = 'translateY(-2px)';
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.boxShadow = '0 1px 3px rgba(0,0,0,0.08)';
        e.currentTarget.style.transform = 'translateY(0)';
      }}
    >
      {/* 拖拽手柄 */}
      <div style={{
        position: 'absolute',
        left: '4px',
        top: '50%',
        transform: 'translateY(-50%)',
        color: '#d1d5db',
        opacity: 0.5,
      }}>
        <GripVertical size={14} />
      </div>

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', position: 'relative' }}>
        <div style={{ flex: 1 }}>
          {/* 标题 */}
          <div style={{ 
            fontSize: '14px', 
            fontWeight: 500, 
            color: '#1f2937', 
            marginBottom: '8px',
            lineHeight: 1.4,
          }}>
            {task.title}
          </div>

          {/* 标签行 */}
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px', marginBottom: '8px' }}>
            <PriorityBadge priority={task.priority} />
            {task.tags.slice(0, 2).map((tag) => (
              <TagBadge key={tag} tag={tag} />
            ))}
            {task.tags.length > 2 && (
              <span style={{ fontSize: '10px', color: '#9ca3af' }}>+{task.tags.length - 2}</span>
            )}
          </div>

          {/* 底部信息 */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '11px', color: '#9ca3af' }}>
            {task.dueDate && (
              <span style={{ display: 'flex', alignItems: 'center', gap: '2px' }}>
                <Calendar size={12} />
                {new Date(task.dueDate).toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })}
              </span>
            )}
          </div>
        </div>

        {/* 操作按钮 */}
        <div style={{ display: 'flex', gap: '4px', opacity: 0 }}>
          <button
            onClick={(e) => { e.stopPropagation(); onEdit(task); }}
            style={{ padding: '4px', border: 'none', background: 'none', cursor: 'pointer', color: '#6b7280', borderRadius: '4px' }}
            title="编辑"
          >
            <Edit2 size={14} />
          </button>
          <button
            onClick={(e) => { e.stopPropagation(); onDelete(task.id); }}
            style={{ padding: '4px', border: 'none', background: 'none', cursor: 'pointer', color: '#ef4444', borderRadius: '4px' }}
            title="删除"
          >
            <Trash2 size={14} />
          </button>
        </div>
      </div>

      {/* 展开详情 */}
      {expanded && (
        <div style={{ marginTop: '12px', paddingTop: '12px', borderTop: '1px solid #f3f4f6' }}>
          {task.description && (
            <p style={{ fontSize: '13px', color: '#6b7280', margin: '0 0 12px 0', lineHeight: 1.5 }}>
              {task.description}
            </p>
          )}
          
          {/* 快速状态切换 */}
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px' }}>
            {(Object.entries(STATUS_CONFIG) as [KanbanStatus, typeof STATUS_CONFIG.backlog][]).map(([key, config]) => (
              <button
                key={key}
                onClick={() => onStatusChange(task.id, key)}
                style={{
                  padding: '4px 8px',
                  borderRadius: '4px',
                  border: 'none',
                  background: task.status === key ? config.bgColor : '#f3f4f6',
                  color: task.status === key ? config.color : '#6b7280',
                  fontSize: '11px',
                  cursor: 'pointer',
                  fontWeight: task.status === key ? 600 : 400,
                }}
              >
                {config.label}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* 展开/收起按钮 */}
      <button
        onClick={() => setExpanded(!expanded)}
        style={{
          position: 'absolute',
          bottom: '-8px',
          left: '50%',
          transform: 'translateX(-50%)',
          padding: '2px 8px',
          border: '1px solid #e5e7eb',
          borderRadius: '10px',
          background: 'white',
          cursor: 'pointer',
          fontSize: '10px',
          color: '#9ca3af',
        }}
      >
        {expanded ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
      </button>
    </div>
  );
};

/** 任务表单 */
interface TaskFormProps {
  onSubmit: (task: Omit<KanbanTask, 'id' | 'createdAt' | 'updatedAt' | 'order'>) => void;
  onCancel: () => void;
  initialData?: KanbanTask;
}

const TaskForm: React.FC<TaskFormProps> = ({ onSubmit, onCancel, initialData }) => {
  const [title, setTitle] = useState(initialData?.title || '');
  const [description, setDescription] = useState(initialData?.description || '');
  const [status, setStatus] = useState<KanbanStatus>(initialData?.status || 'todo');
  const [priority, setPriority] = useState<Priority>(initialData?.priority || 'medium');
  const [tags, setTags] = useState<string[]>(initialData?.tags || []);
  const [dueDate, setDueDate] = useState(initialData?.dueDate || '');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim()) return;

    onSubmit({
      title: title.trim(),
      description,
      status,
      priority,
      tags,
      dueDate: dueDate || undefined,
    });
  };

  const toggleTag = (tagId: string) => {
    setTags(prev => prev.includes(tagId) ? prev.filter(t => t !== tagId) : [...prev, tagId]);
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
        borderRadius: '16px',
        padding: '24px',
        width: '90%',
        maxWidth: '480px',
        maxHeight: '90vh',
        overflow: 'auto',
        boxShadow: '0 20px 60px rgba(0,0,0,0.2)',
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
          <h3 style={{ margin: 0, fontSize: '18px', fontWeight: 600 }}>
            {initialData ? '编辑任务' : '新建任务'}
          </h3>
          <button onClick={onCancel} style={{ padding: '4px', border: 'none', background: 'none', cursor: 'pointer', color: '#6b7280' }}>
            <X size={20} />
          </button>
        </div>

        <form onSubmit={handleSubmit}>
          {/* 标题 */}
          <div style={{ marginBottom: '20px' }}>
            <label style={{ display: 'block', fontSize: '13px', fontWeight: 500, marginBottom: '6px', color: '#374151' }}>
              任务标题 *
            </label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="输入任务标题..."
              required
              autoFocus
              style={{
                width: '100%',
                padding: '10px 14px',
                border: '2px solid #e5e7eb',
                borderRadius: '8px',
                fontSize: '14px',
                boxSizing: 'border-box',
                outline: 'none',
                transition: 'border-color 0.2s',
              }}
              onFocus={(e) => e.target.style.borderColor = '#3b82f6'}
              onBlur={(e) => e.target.style.borderColor = '#e5e7eb'}
            />
          </div>

          {/* 描述 */}
          <div style={{ marginBottom: '20px' }}>
            <label style={{ display: 'block', fontSize: '13px', fontWeight: 500, marginBottom: '6px', color: '#374151' }}>
              任务描述
            </label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="详细描述任务内容..."
              rows={3}
              style={{
                width: '100%',
                padding: '10px 14px',
                border: '2px solid #e5e7eb',
                borderRadius: '8px',
                fontSize: '14px',
                resize: 'vertical',
                boxSizing: 'border-box',
                outline: 'none',
              }}
              onFocus={(e) => e.target.style.borderColor = '#3b82f6'}
              onBlur={(e) => e.target.style.borderColor = '#e5e7eb'}
            />
          </div>

          {/* 状态和优先级 */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '20px' }}>
            <div>
              <label style={{ display: 'block', fontSize: '13px', fontWeight: 500, marginBottom: '6px', color: '#374151' }}>
                状态
              </label>
              <select
                value={status}
                onChange={(e) => setStatus(e.target.value as KanbanStatus)}
                style={{
                  width: '100%',
                  padding: '10px 14px',
                  border: '2px solid #e5e7eb',
                  borderRadius: '8px',
                  fontSize: '14px',
                  cursor: 'pointer',
                }}
              >
                {(Object.entries(STATUS_CONFIG) as [KanbanStatus, typeof STATUS_CONFIG.backlog][]).map(([key, config]) => (
                  <option key={key} value={key}>{config.label}</option>
                ))}
              </select>
            </div>
            <div>
              <label style={{ display: 'block', fontSize: '13px', fontWeight: 500, marginBottom: '6px', color: '#374151' }}>
                优先级
              </label>
              <select
                value={priority}
                onChange={(e) => setPriority(e.target.value as Priority)}
                style={{
                  width: '100%',
                  padding: '10px 14px',
                  border: '2px solid #e5e7eb',
                  borderRadius: '8px',
                  fontSize: '14px',
                  cursor: 'pointer',
                }}
              >
                {(Object.entries(PRIORITY_CONFIG) as [Priority, typeof PRIORITY_CONFIG.low][]).map(([key, config]) => (
                  <option key={key} value={key}>{config.label}</option>
                ))}
              </select>
            </div>
          </div>

          {/* 截止日期 */}
          <div style={{ marginBottom: '20px' }}>
            <label style={{ display: 'block', fontSize: '13px', fontWeight: 500, marginBottom: '6px', color: '#374151' }}>
              截止日期
            </label>
            <input
              type="date"
              value={dueDate}
              onChange={(e) => setDueDate(e.target.value)}
              style={{
                width: '100%',
                padding: '10px 14px',
                border: '2px solid #e5e7eb',
                borderRadius: '8px',
                fontSize: '14px',
                boxSizing: 'border-box',
              }}
            />
          </div>

          {/* 标签 */}
          <div style={{ marginBottom: '24px' }}>
            <label style={{ display: 'block', fontSize: '13px', fontWeight: 500, marginBottom: '8px', color: '#374151' }}>
              <Tag size={14} style={{ marginRight: '4px', verticalAlign: 'middle' }} />
              标签
            </label>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
              {TAG_OPTIONS.map((tag) => (
                <button
                  key={tag.id}
                  type="button"
                  onClick={() => toggleTag(tag.id)}
                  style={{
                    padding: '6px 12px',
                    borderRadius: '16px',
                    border: '2px solid',
                    borderColor: tags.includes(tag.id) ? tag.color : '#e5e7eb',
                    background: tags.includes(tag.id) ? tag.color + '15' : 'white',
                    color: tags.includes(tag.id) ? tag.color : '#6b7280',
                    fontSize: '12px',
                    cursor: 'pointer',
                    fontWeight: tags.includes(tag.id) ? 600 : 400,
                    transition: 'all 0.2s',
                  }}
                >
                  {tag.label}
                </button>
              ))}
            </div>
          </div>

          {/* 按钮 */}
          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px' }}>
            <button
              type="button"
              onClick={onCancel}
              style={{
                padding: '12px 24px',
                borderRadius: '8px',
                border: '2px solid #e5e7eb',
                background: 'white',
                cursor: 'pointer',
                fontSize: '14px',
                fontWeight: 500,
                color: '#6b7280',
              }}
            >
              取消
            </button>
            <button
              type="submit"
              style={{
                padding: '12px 24px',
                borderRadius: '8px',
                border: 'none',
                background: 'linear-gradient(135deg, #3b82f6 0%, #2563eb 100%)',
                color: 'white',
                cursor: 'pointer',
                fontSize: '14px',
                fontWeight: 600,
                boxShadow: '0 4px 12px rgba(59, 130, 246, 0.3)',
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

// =====================
// 主组件
// =====================

interface KanbanBoardProps {
  title?: string;
  accentColor?: string;
}

export const KanbanBoard: React.FC<KanbanBoardProps> = ({ 
  title = '看板',
  accentColor = '#3b82f6'
}) => {
  const [tasks, setTasks] = useState<KanbanTask[]>(() => loadTasks());
  const [showForm, setShowForm] = useState(false);
  const [editingTask, setEditingTask] = useState<KanbanTask | null>(null);
  const [filterPriority, setFilterPriority] = useState<Priority | ''>('');
  const [filterTag, setFilterTag] = useState<string>('');
  const [searchQuery, setSearchQuery] = useState('');

  // 保存任务到 localStorage
  useEffect(() => {
    saveTasks(tasks);
  }, [tasks]);

  // 过滤任务
  const filteredTasks = useMemo(() => {
    return tasks.filter((task) => {
      if (filterPriority && task.priority !== filterPriority) return false;
      if (filterTag && !task.tags.includes(filterTag)) return false;
      if (searchQuery && !task.title.toLowerCase().includes(searchQuery.toLowerCase())) return false;
      return true;
    });
  }, [tasks, filterPriority, filterTag, searchQuery]);

  // 按状态分组
  const groupedTasks = useMemo(() => {
    const columns: Record<KanbanStatus, KanbanTask[]> = {
      backlog: [],
      todo: [],
      in_progress: [],
      review: [],
      done: [],
    };

    filteredTasks
      .sort((a, b) => a.order - b.order)
      .forEach((task) => {
        if (columns[task.status]) {
          columns[task.status].push(task);
        }
      });

    return columns;
  }, [filteredTasks]);

  // 创建任务
  const handleCreateTask = (data: Omit<KanbanTask, 'id' | 'createdAt' | 'updatedAt' | 'order'>) => {
    const newTask: KanbanTask = {
      ...data,
      id: generateId(),
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      order: tasks.filter(t => t.status === data.status).length,
    };
    setTasks(prev => [...prev, newTask]);
    setShowForm(false);
  };

  // 更新任务
  const handleUpdateTask = (data: Omit<KanbanTask, 'id' | 'createdAt' | 'updatedAt' | 'order'>) => {
    if (!editingTask) return;
    setTasks(prev => prev.map(t => 
      t.id === editingTask.id 
        ? { ...t, ...data, updatedAt: new Date().toISOString() }
        : t
    ));
    setEditingTask(null);
  };

  // 删除任务
  const handleDeleteTask = (taskId: string) => {
    if (!confirm('确定要删除这个任务吗？')) return;
    setTasks(prev => prev.filter(t => t.id !== taskId));
  };

  // 快速更新状态
  const handleStatusChange = (taskId: string, newStatus: KanbanStatus) => {
    setTasks(prev => prev.map(t => 
      t.id === taskId 
        ? { ...t, status: newStatus, updatedAt: new Date().toISOString() }
        : t
    ));
  };

  // 计算统计数据
  const stats = useMemo(() => ({
    total: tasks.length,
    todo: tasks.filter(t => t.status === 'todo').length,
    inProgress: tasks.filter(t => t.status === 'in_progress').length,
    done: tasks.filter(t => t.status === 'done').length,
    urgent: tasks.filter(t => t.priority === 'urgent').length,
  }), [tasks]);

  return (
    <div style={{ 
      minHeight: '100vh',
      background: '#f8fafc',
      padding: '24px',
    }}>
      {/* 顶部标题栏 */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: '24px',
        flexWrap: 'wrap',
        gap: '16px',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{
            width: '40px',
            height: '40px',
            borderRadius: '10px',
            background: `linear-gradient(135deg, ${accentColor} 0%, ${accentColor}dd 100%)`,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: 'white',
          }}>
            <LayoutDashboard size={22} />
          </div>
          <div>
            <h1 style={{ margin: 0, fontSize: '24px', fontWeight: 700, color: '#1f2937' }}>{title}</h1>
            <p style={{ margin: '2px 0 0', fontSize: '13px', color: '#9ca3af' }}>
              共 {stats.total} 个任务 · {stats.inProgress} 进行中 · {stats.done} 已完成
            </p>
          </div>
        </div>

        {/* 搜索框 */}
        <div style={{ position: 'relative' }}>
          <input
            type="text"
            placeholder="搜索任务..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            style={{
              width: '240px',
              padding: '10px 14px 10px 40px',
              border: '2px solid #e5e7eb',
              borderRadius: '8px',
              fontSize: '14px',
              outline: 'none',
            }}
          />
          <Filter size={16} style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: '#9ca3af' }} />
        </div>

        <button
          onClick={() => setShowForm(true)}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            padding: '12px 20px',
            border: 'none',
            borderRadius: '10px',
            background: `linear-gradient(135deg, ${accentColor} 0%, ${accentColor}dd 100%)`,
            color: 'white',
            cursor: 'pointer',
            fontSize: '14px',
            fontWeight: 600,
            boxShadow: `0 4px 14px ${accentColor}40`,
          }}
        >
          <Plus size={18} />
          新建任务
        </button>
      </div>

      {/* 过滤器 */}
      <div style={{
        display: 'flex',
        gap: '12px',
        marginBottom: '20px',
        flexWrap: 'wrap',
        alignItems: 'center',
      }}>
        <select
          value={filterPriority}
          onChange={(e) => setFilterPriority(e.target.value as Priority || '')}
          style={{
            padding: '8px 12px',
            borderRadius: '8px',
            border: '2px solid #e5e7eb',
            fontSize: '13px',
            cursor: 'pointer',
            background: 'white',
          }}
        >
          <option value="">所有优先级</option>
          {(Object.entries(PRIORITY_CONFIG) as [Priority, typeof PRIORITY_CONFIG.low][]).map(([key, config]) => (
            <option key={key} value={key}>{config.label}</option>
          ))}
        </select>

        <select
          value={filterTag}
          onChange={(e) => setFilterTag(e.target.value)}
          style={{
            padding: '8px 12px',
            borderRadius: '8px',
            border: '2px solid #e5e7eb',
            fontSize: '13px',
            cursor: 'pointer',
            background: 'white',
          }}
        >
          <option value="">所有标签</option>
          {TAG_OPTIONS.map((tag) => (
            <option key={tag.id} value={tag.id}>{tag.label}</option>
          ))}
        </select>

        {(filterPriority || filterTag || searchQuery) && (
          <button
            onClick={() => { setFilterPriority(''); setFilterTag(''); setSearchQuery(''); }}
            style={{
              padding: '8px 12px',
              borderRadius: '8px',
              border: 'none',
              background: '#f3f4f6',
              color: '#6b7280',
              fontSize: '13px',
              cursor: 'pointer',
            }}
          >
            清除筛选
          </button>
        )}

        {stats.urgent > 0 && (
          <div style={{
            padding: '8px 12px',
            borderRadius: '8px',
            background: '#fee2e2',
            color: '#ef4444',
            fontSize: '13px',
            fontWeight: 600,
          }}>
            {stats.urgent} 个紧急任务
          </div>
        )}
      </div>

      {/* 看板列 */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(5, 1fr)',
        gap: '16px',
        minHeight: 'calc(100vh - 240px)',
      }}>
        {(Object.entries(STATUS_CONFIG) as [KanbanStatus, typeof STATUS_CONFIG.backlog][]).map(([status, config]) => (
          <div
            key={status}
            style={{
              background: '#f1f5f9',
              borderRadius: '12px',
              padding: '12px',
              display: 'flex',
              flexDirection: 'column',
            }}
          >
            {/* 列标题 */}
            <div style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              marginBottom: '12px',
              paddingBottom: '12px',
              borderBottom: `3px solid ${config.color}`,
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span style={{ fontSize: '14px', fontWeight: 700, color: '#374151' }}>
                  {config.label}
                </span>
                <span style={{
                  background: config.bgColor,
                  color: config.color,
                  padding: '2px 10px',
                  borderRadius: '12px',
                  fontSize: '12px',
                  fontWeight: 700,
                }}>
                  {groupedTasks[status].length}
                </span>
              </div>
              <button
                onClick={() => {
                  setStatus && setStatus(status);
                  setShowForm(true);
                }}
                style={{
                  padding: '4px',
                  border: 'none',
                  borderRadius: '6px',
                  background: 'transparent',
                  cursor: 'pointer',
                  color: '#9ca3af',
                }}
                title="添加任务"
              >
                <Plus size={16} />
              </button>
            </div>

            {/* 任务列表 */}
            <div style={{ flex: 1, minHeight: '200px' }}>
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
                  color: '#cbd5e1',
                  fontSize: '13px',
                }}>
                  <div style={{ fontSize: '32px', marginBottom: '8px' }}>📋</div>
                  暂无任务
                </div>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* 统计卡片 */}
      <div style={{
        marginTop: '24px',
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))',
        gap: '12px',
      }}>
        {[
          { label: '待办', value: stats.todo, color: '#3b82f6' },
          { label: '进行中', value: stats.inProgress, color: '#f59e0b' },
          { label: '已完成', value: stats.done, color: '#10b981' },
          { label: '紧急', value: stats.urgent, color: '#ef4444' },
        ].map((item) => (
          <div
            key={item.label}
            style={{
              background: 'white',
              borderRadius: '12px',
              padding: '16px',
              textAlign: 'center',
              boxShadow: '0 2px 8px rgba(0,0,0,0.06)',
            }}
          >
            <div style={{ fontSize: '28px', fontWeight: 800, color: item.color }}>
              {item.value}
            </div>
            <div style={{ fontSize: '12px', color: '#9ca3af', marginTop: '4px' }}>
              {item.label}
            </div>
          </div>
        ))}
      </div>

      {/* 任务表单弹窗 */}
      {(showForm || editingTask) && (
        <TaskForm
          initialData={editingTask || undefined}
          onSubmit={editingTask ? handleUpdateTask : handleCreateTask}
          onCancel={() => {
            setShowForm(false);
            setEditingTask(null);
          }}
        />
      )}
    </div>
  );
};

// 用于设置新建任务时的默认状态
let setStatusCallback: ((status: KanbanStatus) => void) | null = null;

export const setKanbanDefaultStatus = (status: KanbanStatus) => {
  if (setStatusCallback) {
    setStatusCallback(status);
  }
};

export default KanbanBoard;
