/**
 * Copyright 2026 NEMT Lab
 *
 * UI组件自动生成器 - 约束驱动的界面
 *
 * 核心理念：UI 不是设计的，而是从数据结构和业务规则中推导出来的
 *
 * 生成流程：
 * 1. 分析数据结构
 * 2. 推导展示形式
 * 3. 生成组件
 * 4. 绑定交互
 */

// ============================================
// 类型定义
// ============================================

import React from 'react';

export type ComponentType =
  | 'input'      // 文本输入
  | 'textarea'    // 多行文本
  | 'number'     // 数字输入
  | 'select'     // 下拉选择
  | 'checkbox'   // 复选框
  | 'switch'     // 开关
  | 'radio'      // 单选
  | 'date'       // 日期
  | 'datetime'   // 日期时间
  | 'slider'     // 滑块
  | 'color'      // 颜色选择
  | 'file'       // 文件上传
  | 'array'      // 数组输入
  | 'object'     // 对象输入
  | 'readonly';  // 只读文本

export interface FieldConfig {
  name: string;
  label: string;
  type: ComponentType;
  placeholder?: string;
  help?: string;

  // 值
  value?: any;

  // 验证
  required?: boolean;
  disabled?: boolean;
  readOnly?: boolean;

  // 选项 (用于 select/radio/checkbox)
  options?: Array<{ label: string; value: any }>;

  // 范围 (用于 number/slider)
  min?: number;
  max?: number;
  step?: number;

  // 样式
  className?: string;
  style?: React.CSSProperties;

  // 布局
  span?: number;  // 栅格跨度

  // 事件
  onChange?: (value: any) => void;
  onValidate?: (value: any) => ValidationResult;
}

export interface FormConfig {
  title?: string;
  description?: string;
  fields: FieldConfig[];
  layout?: 'horizontal' | 'vertical' | 'grid';
  columns?: number;  // 栅格列数
  showSubmit?: boolean;
  submitText?: string;
  cancelText?: string;
}

export interface ValidationResult {
  valid: boolean;
  error?: string;
}

export interface GeneratedComponent {
  type: ComponentType;
  props: Record<string, any>;
  validation?: FieldConfig['onValidate'];
}

// ============================================
// 组件生成器
// ============================================

export class ComponentGenerator {
  private baseStyles = {
    label: {
      display: 'block',
      marginBottom: '6px',
      fontSize: '13px',
      fontWeight: 500,
      color: '#94a3b8'
    },
    input: {
      width: '100%',
      padding: '10px 12px',
      borderRadius: '8px',
      border: '1px solid #334155',
      background: '#0f172a',
      color: '#e2e8f0',
      fontSize: '14px',
      outline: 'none',
      transition: 'border-color 0.2s, box-shadow 0.2s'
    },
    error: {
      marginTop: '4px',
      fontSize: '12px',
      color: '#ef4444'
    },
    help: {
      marginTop: '4px',
      fontSize: '11px',
      color: '#64748b'
    }
  };

  /**
   * 从数据类型推导组件
   */
  inferComponentType(field: { name: string; type: string; enumValues?: any[] }): ComponentType {
    // 枚举 -> 下拉或单选
    if (field.enumValues && field.enumValues.length > 0) {
      if (field.enumValues.length <= 3) return 'radio';
      return 'select';
    }

    // 布尔 -> 开关
    if (field.type === 'boolean') return 'switch';

    // 数字范围
    if (field.type === 'number') return 'number';

    // 日期时间
    if (field.type === 'date') {
      if (field.name.includes('time')) return 'datetime';
      return 'date';
    }

    // 大文本
    if (field.name.includes('description') || field.name.includes('content')) {
      return 'textarea';
    }

    // 数组
    if (field.type === 'array') return 'array';

    // 对象
    if (field.type === 'object') return 'object';

    // 默认文本输入
    return 'input';
  }

  /**
   * 从字段配置生成组件
   */
  generateComponent(config: FieldConfig): React.ReactNode {
    const {
      type, label, placeholder, help, required, disabled,
      options, min, max, step, style, onChange, value
    } = config;

    const baseProps = {
      disabled,
      value,
      style: { ...this.baseStyles.input, ...style },
      onChange: (e: any) => onChange?.(e.target?.value ?? e)
    };

    const renderLabel = () => (
      <label style={this.baseStyles.label}>
        {label}
        {required && <span style={{ color: '#ef4444', marginLeft: '4px' }}>*</span>}
      </label>
    );

    const renderHelp = () => help && (
      <div style={this.baseStyles.help}>{help}</div>
    );

    switch (type) {
      case 'input':
        return (
          <div>
            {renderLabel()}
            <input type="text" placeholder={placeholder} {...baseProps} />
            {renderHelp()}
          </div>
        );

      case 'textarea':
        return (
          <div>
            {renderLabel()}
            <textarea
              placeholder={placeholder}
              rows={4}
              style={{ ...baseProps, resize: 'vertical', minHeight: '80px' }}
            />
            {renderHelp()}
          </div>
        );

      case 'number':
        return (
          <div>
            {renderLabel()}
            <input
              type="number"
              placeholder={placeholder}
              min={min}
              max={max}
              step={step || 1}
              {...baseProps}
            />
            {renderHelp()}
          </div>
        );

      case 'select':
        return (
          <div>
            {renderLabel()}
            <select {...baseProps} style={{ ...baseProps.style, cursor: 'pointer' }}>
              <option value="">{placeholder || '请选择'}</option>
              {options?.map(opt => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
            {renderHelp()}
          </div>
        );

      case 'switch':
        return (
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            {renderLabel()}
            <div
              onClick={() => !disabled && onChange?.(!value)}
              style={{
                width: '44px',
                height: '24px',
                borderRadius: '12px',
                background: value ? '#10b981' : '#334155',
                position: 'relative',
                cursor: disabled ? 'not-allowed' : 'pointer',
                transition: 'background 0.2s'
              }}
            >
              <div style={{
                width: '20px',
                height: '20px',
                borderRadius: '50%',
                background: '#fff',
                position: 'absolute',
                top: '2px',
                left: value ? '22px' : '2px',
                transition: 'left 0.2s'
              }} />
            </div>
          </div>
        );

      case 'checkbox':
        return (
          <div>
            {options?.map(opt => (
              <label
                key={opt.value}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  marginBottom: '8px',
                  cursor: disabled ? 'not-allowed' : 'pointer'
                }}
              >
                <input
                  type="checkbox"
                  checked={opt.value === value}
                  disabled={disabled}
                  onChange={() => onChange?.(opt.value)}
                  style={{ width: '16px', height: '16px' }}
                />
                <span style={{ fontSize: '14px', color: '#e2e8f0' }}>{opt.label}</span>
              </label>
            ))}
          </div>
        );

      case 'radio':
        return (
          <div>
            {options?.map(opt => (
              <label
                key={opt.value}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  marginBottom: '8px',
                  cursor: disabled ? 'not-allowed' : 'pointer'
                }}
              >
                <input
                  type="radio"
                  name={config.name}
                  checked={opt.value === value}
                  disabled={disabled}
                  onChange={() => onChange?.(opt.value)}
                  style={{ width: '16px', height: '16px' }}
                />
                <span style={{ fontSize: '14px', color: '#e2e8f0' }}>{opt.label}</span>
              </label>
            ))}
          </div>
        );

      case 'date':
        return (
          <div>
            {renderLabel()}
            <input type="date" {...baseProps} />
            {renderHelp()}
          </div>
        );

      case 'datetime':
        return (
          <div>
            {renderLabel()}
            <input type="datetime-local" {...baseProps} />
            {renderHelp()}
          </div>
        );

      case 'slider':
        return (
          <div>
            {renderLabel()}
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <input
                type="range"
                min={min || 0}
                max={max || 100}
                step={step || 1}
                value={value ?? min ?? 0}
                onChange={(e) => onChange?.(parseFloat(e.target.value))}
                disabled={disabled}
                style={{ flex: 1, ...this.baseStyles.input }}
              />
              <span style={{
                minWidth: '40px',
                textAlign: 'right',
                color: '#e2e8f0',
                fontFamily: 'monospace'
              }}>
                {value ?? min ?? 0}
              </span>
            </div>
            {renderHelp()}
          </div>
        );

      case 'readonly':
        return (
          <div>
            {renderLabel()}
            <div style={{
              padding: '10px 12px',
              background: '#0f172a',
              borderRadius: '8px',
              color: '#64748b',
              fontSize: '14px'
            }}>
              {placeholder || '-'}
            </div>
          </div>
        );

      default:
        return null;
    }
  }

  /**
   * 从 schema 生成表单
   */
  generateForm(config: FormConfig): React.ReactNode {
    const {
      title,
      description,
      fields,
      layout = 'vertical',
      columns = 2,
      showSubmit = true,
      submitText = '提交',
      cancelText = '取消'
    } = config;

    const [formData, setFormData] = React.useState<Record<string, any>>({});
    const [errors, setErrors] = React.useState<Record<string, string>>({});

    const handleSubmit = (e: React.FormEvent) => {
      e.preventDefault();

      // 验证
      const newErrors: Record<string, string> = {};
      fields.forEach(field => {
        if (field.required && !formData[field.name]) {
          newErrors[field.name] = `${field.label} 是必填项`;
        }
      });

      setErrors(newErrors);

      if (Object.keys(newErrors).length === 0) {
        console.log('Form submitted:', formData);
      }
    };

    const fieldStyle = layout === 'grid'
      ? { gridColumn: `span ${fields.find(f => f.span)?.span || 1}` }
      : {};

    return (
      <form onSubmit={handleSubmit} style={{ maxWidth: '800px' }}>
        {title && (
          <h3 style={{
            margin: '0 0 8px',
            fontSize: '18px',
            color: '#e2e8f0'
          }}>
            {title}
          </h3>
        )}

        {description && (
          <p style={{
            margin: '0 0 24px',
            fontSize: '13px',
            color: '#64748b'
          }}>
            {description}
          </p>
        )}

        <div style={{
          display: layout === 'grid' ? 'grid' : 'flex',
          gridTemplateColumns: `repeat(${columns}, 1fr)`,
          gap: '20px',
          flexDirection: layout === 'horizontal' ? 'row' : 'column'
        }}>
          {fields.map(field => (
            <div key={field.name} style={fieldStyle}>
              {this.generateComponent({
                ...field,
                value: formData[field.name],
                onChange: (value) => {
                  setFormData(prev => ({ ...prev, [field.name]: value }));
                  setErrors(prev => ({ ...prev, [field.name]: '' }));
                }
              })}
              {errors[field.name] && (
                <div style={this.baseStyles.error}>{errors[field.name]}</div>
              )}
            </div>
          ))}
        </div>

        {showSubmit && (
          <div style={{
            display: 'flex',
            gap: '12px',
            marginTop: '24px',
            paddingTop: '24px',
            borderTop: '1px solid #334155'
          }}>
            <button
              type="submit"
              style={{
                padding: '12px 24px',
                borderRadius: '8px',
                border: 'none',
                background: 'linear-gradient(135deg, #8b5cf6 0%, #6366f1 100%)',
                color: '#fff',
                fontSize: '14px',
                fontWeight: 500,
                cursor: 'pointer'
              }}
            >
              {submitText}
            </button>

            <button
              type="button"
              style={{
                padding: '12px 24px',
                borderRadius: '8px',
                border: '1px solid #475569',
                background: 'transparent',
                color: '#94a3b8',
                fontSize: '14px',
                cursor: 'pointer'
              }}
            >
              {cancelText}
            </button>
          </div>
        )}
      </form>
    );
  }
}

// ============================================
// 表格生成器
// ============================================

export interface TableColumn {
  key: string;
  title: string;
  width?: number | string;
  align?: 'left' | 'center' | 'right';
  render?: (value: any, record: any, index: number) => React.ReactNode;
  sortable?: boolean;
  filterable?: boolean;
}

export interface TableConfig {
  columns: TableColumn[];
  dataSource: any[];
  rowKey?: string;
  selectable?: boolean;
  onRowClick?: (record: any) => void;
  emptyText?: string;
  loading?: boolean;
}

export class TableGenerator {
  private sortOrder: Record<string, 'asc' | 'desc'> = {};
  private filterValue: Record<string, string> = {};

  generate(config: TableConfig): React.ReactNode {
    const {
      columns,
      dataSource,
      rowKey = 'id',
      selectable,
      onRowClick,
      emptyText = '暂无数据',
      loading
    } = config;

    // 应用排序
    let sortedData = [...dataSource];
    Object.entries(this.sortOrder).forEach(([key, order]) => {
      sortedData.sort((a, b) => {
        const aVal = a[key];
        const bVal = b[key];
        if (aVal < bVal) return order === 'asc' ? -1 : 1;
        if (aVal > bVal) return order === 'asc' ? 1 : -1;
        return 0;
      });
    });

    // 应用过滤
    sortedData = sortedData.filter(row => {
      return Object.entries(this.filterValue).every(([key, value]) => {
        if (!value) return true;
        const cellValue = String(row[key] || '').toLowerCase();
        return cellValue.includes(value.toLowerCase());
      });
    });

    const handleSort = (key: string) => {
      this.sortOrder[key] = this.sortOrder[key] === 'asc' ? 'desc' : 'asc';
    };

    const handleFilter = (key: string, value: string) => {
      this.filterValue[key] = value;
    };

    const styles = {
      container: {
        background: '#1e293b',
        borderRadius: '12px',
        overflow: 'hidden',
        border: '1px solid #334155'
      },
      header: {
        background: '#0f172a',
        borderBottom: '1px solid #334155'
      },
      headerCell: {
        padding: '12px 16px',
        fontSize: '12px',
        fontWeight: 600,
        color: '#94a3b8',
        textTransform: 'uppercase',
        letterSpacing: '0.5px'
      },
      row: {
        borderBottom: '1px solid #1e293b',
        transition: 'background 0.15s'
      },
      cell: {
        padding: '12px 16px',
        fontSize: '14px',
        color: '#e2e8f0'
      },
      empty: {
        padding: '48px',
        textAlign: 'center' as const,
        color: '#64748b'
      }
    };

    return (
      <div style={styles.container}>
        {loading && (
          <div style={{
            padding: '8px 16px',
            background: '#f59e0b20',
            color: '#f59e0b',
            fontSize: '12px'
          }}>
            加载中...
          </div>
        )}

        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr style={styles.header}>
              {selectable && (
                <th style={{ ...styles.headerCell, width: '40px' }}>
                  <input type="checkbox" />
                </th>
              )}
              {columns.map(col => (
                <th
                  key={col.key}
                  style={{
                    ...styles.headerCell,
                    textAlign: col.align || 'left',
                    width: col.width,
                    cursor: col.sortable ? 'pointer' : 'default'
                  }}
                  onClick={() => col.sortable && handleSort(col.key)}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                    {col.title}
                    {col.sortable && (
                      <span style={{ fontSize: '10px', opacity: 0.5 }}>
                        {this.sortOrder[col.key] === 'asc' ? '↑' : this.sortOrder[col.key] === 'desc' ? '↓' : '↕'}
                      </span>
                    )}
                  </div>
                  {col.filterable && (
                    <input
                      type="text"
                      placeholder="过滤..."
                      value={this.filterValue[col.key] || ''}
                      onChange={(e) => handleFilter(col.key, e.target.value)}
                      onClick={(e) => e.stopPropagation()}
                      style={{
                        width: '100%',
                        marginTop: '8px',
                        padding: '4px 8px',
                        borderRadius: '4px',
                        border: '1px solid #334155',
                        background: '#0f172a',
                        color: '#e2e8f0',
                        fontSize: '11px'
                      }}
                    />
                  )}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {sortedData.length === 0 ? (
              <tr>
                <td colSpan={columns.length} style={styles.empty}>
                  {emptyText}
                </td>
              </tr>
            ) : (
              sortedData.map((record, index) => (
                <tr
                  key={record[rowKey]}
                  style={{
                    ...styles.row,
                    cursor: onRowClick ? 'pointer' : 'default'
                  }}
                  onClick={() => onRowClick?.(record)}
                  onMouseEnter={(e) => e.currentTarget.style.background = '#1e293b'}
                  onMouseLeave={(e) => e.currentTarget.style.background = 'transparent'}
                >
                  {selectable && (
                    <td style={styles.cell}>
                      <input type="checkbox" />
                    </td>
                  )}
                  {columns.map(col => (
                    <td
                      key={col.key}
                      style={{
                        ...styles.cell,
                        textAlign: col.align || 'left'
                      }}
                    >
                      {col.render
                        ? col.render(record[col.key], record, index)
                        : record[col.key]
                      }
                    </td>
                  ))}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    );
  }
}

// ============================================
// 全局实例
// ============================================

export const componentGenerator = new ComponentGenerator();
export const tableGenerator = new TableGenerator();
