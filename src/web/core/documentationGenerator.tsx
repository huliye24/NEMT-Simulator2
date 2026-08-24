/**
 * Copyright 2026 NEMT Lab
 *
 * 自我文档生成系统
 *
 * 核心理念：代码即文档，文档从代码中自动生成
 *
 * 文档来源：
 * - Schema 定义
 * - 约束声明
 * - 组件注释
 * - API 定义
 */

// ============================================
// 文档类型
// ============================================

export interface Documentation {
  version: string;
  generatedAt: number;
  sections: DocumentationSection[];
  entities: EntityDocumentation[];
  apis: ApiDocumentation[];
  schemas: SchemaDocumentation[];
}

export interface DocumentationSection {
  id: string;
  title: string;
  content: string;
  order: number;
}

export interface EntityDocumentation {
  name: string;
  description: string;
  schema: string;
  fields: FieldDocumentation[];
  constraints: string[];
  example?: any;
}

export interface FieldDocumentation {
  name: string;
  type: string;
  description: string;
  required: boolean;
  constraints: string[];
  example?: any;
}

export interface ApiDocumentation {
  path: string;
  method: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH';
  description: string;
  parameters: ParameterDocumentation[];
  response: ResponseDocumentation;
  errors: ErrorDocumentation[];
}

export interface ParameterDocumentation {
  name: string;
  type: string;
  required: boolean;
  description: string;
  example?: any;
}

export interface ResponseDocumentation {
  status: number;
  description: string;
  schema: string;
}

export interface ErrorDocumentation {
  code: string;
  message: string;
  description: string;
}

export interface SchemaDocumentation {
  name: string;
  version: string;
  description: string;
  fields: FieldDocumentation[];
}

// ============================================
// 文档生成器
// ============================================

import { Schema, FieldSchema } from './generationParadigm';

export class DocumentationGenerator {
  private docs: Documentation = {
    version: '1.0.0',
    generatedAt: Date.now(),
    sections: [],
    entities: [],
    apis: [],
    schemas: []
  };

  /**
   * 生成完整文档
   */
  generate(): Documentation {
    return {
      ...this.docs,
      generatedAt: Date.now()
    };
  }

  /**
   * 添加章节
   */
  addSection(section: Omit<DocumentationSection, 'id'>): void {
    this.docs.sections.push({
      ...section,
      id: `section_${Date.now()}`
    });
  }

  /**
   * 从 Schema 生成实体文档
   */
  generateEntityDoc(schema: Schema): EntityDocumentation {
    return {
      name: schema.name,
      description: schema.description || '',
      schema: schema.name,
      fields: schema.fields.map(field => this.generateFieldDoc(field)),
      constraints: schema.constraints || []
    };
  }

  /**
   * 生成字段文档
   */
  generateFieldDoc(field: FieldSchema): FieldDocumentation {
    const constraints: string[] = [];

    if (field.required) constraints.push('必填');
    if (field.minLength) constraints.push(`最小长度: ${field.minLength}`);
    if (field.maxLength) constraints.push(`最大长度: ${field.maxLength}`);
    if (field.min !== undefined) constraints.push(`最小值: ${field.min}`);
    if (field.max !== undefined) constraints.push(`最大值: ${field.max}`);
    if (field.enum) constraints.push(`可选值: ${field.enum.join(', ')}`);
    if (field.pattern) constraints.push(`正则: ${field.pattern}`);

    return {
      name: field.name,
      type: field.type,
      description: field.description || '',
      required: field.required || false,
      constraints,
      example: field.default
    };
  }

  /**
   * 添加 API 文档
   */
  addApi(api: ApiDocumentation): void {
    this.docs.apis.push(api);
  }

  /**
   * 添加 Schema 文档
   */
  addSchema(schema: Schema): void {
    this.docs.schemas.push({
      name: schema.name,
      version: schema.version,
      description: schema.description || '',
      fields: schema.fields.map(f => this.generateFieldDoc(f))
    });
  }

  /**
   * 生成 Markdown
   */
  toMarkdown(): string {
    let md = `# NEMT Platform 文档\n\n`;
    md += `> 自动生成于 ${new Date().toISOString()}\n\n`;

    // 章节
    if (this.docs.sections.length > 0) {
      md += `## 概述\n\n`;
      for (const section of this.docs.sections) {
        md += `${section.content}\n\n`;
      }
    }

    // Schema
    if (this.docs.schemas.length > 0) {
      md += `## 数据模型\n\n`;
      for (const schema of this.docs.schemas) {
        md += `### ${schema.name}\n\n`;
        md += `${schema.description}\n\n`;
        md += `| 字段 | 类型 | 必填 | 描述 |\n`;
        md += `|------|------|------|------|\n`;

        for (const field of schema.fields) {
          md += `| ${field.name} | ${field.type} | ${field.required ? '是' : '否'} | ${field.description} |\n`;
        }

        md += `\n`;
      }
    }

    // API
    if (this.docs.apis.length > 0) {
      md += `## API 参考\n\n`;

      for (const api of this.docs.apis) {
        md += `### ${api.method} ${api.path}\n\n`;
        md += `${api.description}\n\n`;

        if (api.parameters.length > 0) {
          md += `**参数:**\n\n`;
          md += `| 参数 | 类型 | 必填 | 描述 |\n`;
          md += `|------|------|------|------|\n`;

          for (const param of api.parameters) {
            md += `| ${param.name} | ${param.type} | ${param.required ? '是' : '否'} | ${param.description} |\n`;
          }

          md += `\n`;
        }

        md += `**响应:** ${api.response.status} - ${api.response.description}\n\n`;

        if (api.errors.length > 0) {
          md += `**错误码:**\n\n`;
          for (const error of api.errors) {
            md += `- \`${error.code}\`: ${error.message}\n`;
          }
          md += `\n`;
        }
      }
    }

    return md;
  }

  /**
   * 生成 JSON Schema
   */
  toJsonSchema(schema: Schema): any {
    const properties: Record<string, any> = {};
    const required: string[] = [];

    for (const field of schema.fields) {
      properties[field.name] = this.fieldToJsonSchema(field);
      if (field.required) {
        required.push(field.name);
      }
    }

    return {
      $schema: 'http://json-schema.org/draft-07/schema#',
      title: schema.name,
      description: schema.description,
      type: 'object',
      properties,
      required: required.length > 0 ? required : undefined
    };
  }

  /**
   * 字段转 JSON Schema
   */
  private fieldToJsonSchema(field: FieldSchema): any {
    let schema: any = { description: field.description };

    switch (field.type) {
      case 'string':
        schema.type = 'string';
        if (field.minLength) schema.minLength = field.minLength;
        if (field.maxLength) schema.maxLength = field.maxLength;
        if (field.pattern) schema.pattern = field.pattern;
        if (field.format) schema.format = field.format;
        break;
      case 'number':
        schema.type = 'number';
        if (field.min !== undefined) schema.minimum = field.min;
        if (field.max !== undefined) schema.maximum = field.max;
        break;
      case 'boolean':
        schema.type = 'boolean';
        break;
      case 'date':
      case 'datetime':
        schema.type = 'string';
        schema.format = field.type === 'date' ? 'date' : 'date-time';
        break;
      case 'enum':
        schema.type = typeof field.enum?.[0] === 'string' ? 'string' : 'number';
        if (field.enum) schema.enum = field.enum;
        break;
      case 'array':
        schema.type = 'array';
        break;
      case 'object':
        schema.type = 'object';
        break;
    }

    if (field.default !== undefined) {
      schema.default = field.default;
    }

    return schema;
  }
}

// ============================================
// 全局实例
// ============================================

export const documentationGenerator = new DocumentationGenerator();

// ============================================
// 文档视图组件
// ============================================

import React, { useState, useEffect } from 'react';

export const DocumentationViewer: React.FC<{
  generator?: DocumentationGenerator;
}> = ({ generator }) => {
  const [activeTab, setActiveTab] = useState<'overview' | 'schemas' | 'apis'>('overview');
  const [markdown, setMarkdown] = useState('');

  useEffect(() => {
    if (generator) {
      setMarkdown(generator.toMarkdown());
    }
  }, [generator]);

  return (
    <div style={{
      background: '#0f172a',
      borderRadius: '12px',
      border: '1px solid #334155',
      overflow: 'hidden'
    }}>
      {/* 标签 */}
      <div style={{
        display: 'flex',
        borderBottom: '1px solid #334155'
      }}>
        {[
          { id: 'overview', label: '概述' },
          { id: 'schemas', label: '数据模型' },
          { id: 'apis', label: 'API' }
        ].map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id as any)}
            style={{
              flex: 1,
              padding: '12px',
              border: 'none',
              background: activeTab === tab.id ? '#1e293b' : 'transparent',
              color: activeTab === tab.id ? '#a78bfa' : '#64748b',
              cursor: 'pointer',
              fontSize: '13px'
            }}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* 内容 */}
      <div style={{ padding: '20px' }}>
        <pre style={{
          color: '#94a3b8',
          fontSize: '12px',
          fontFamily: 'monospace',
          whiteSpace: 'pre-wrap',
          margin: 0
        }}>
          {markdown || '暂无文档'}
        </pre>
      </div>
    </div>
  );
};

// ============================================
// Schema 表格组件
// ============================================

export const SchemaTable: React.FC<{
  schema: Schema;
}> = ({ schema }) => {
  return (
    <div style={{
      background: '#1e293b',
      borderRadius: '8px',
      overflow: 'hidden'
    }}>
      <table style={{
        width: '100%',
        borderCollapse: 'collapse',
        fontSize: '13px'
      }}>
        <thead>
          <tr style={{ background: '#0f172a' }}>
            <th style={thStyle}>字段</th>
            <th style={thStyle}>类型</th>
            <th style={thStyle}>必填</th>
            <th style={thStyle}>描述</th>
          </tr>
        </thead>
        <tbody>
          {schema.fields.map((field, i) => (
            <tr
              key={field.name}
              style={{
                background: i % 2 === 0 ? 'transparent' : '#1e293b50'
              }}
            >
              <td style={tdStyle}>
                <code style={{ color: '#a78bfa' }}>{field.name}</code>
              </td>
              <td style={tdStyle}>
                <span style={{
                  color: '#10b981',
                  fontFamily: 'monospace'
                }}>
                  {field.type}
                </span>
              </td>
              <td style={tdStyle}>
                {field.required ? (
                  <span style={{ color: '#ef4444' }}>是</span>
                ) : (
                  <span style={{ color: '#64748b' }}>否</span>
                )}
              </td>
              <td style={{ ...tdStyle, color: '#94a3b8' }}>
                {field.description || '-'}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

const thStyle: React.CSSProperties = {
  padding: '12px 16px',
  textAlign: 'left',
  color: '#64748b',
  fontWeight: 500,
  fontSize: '11px',
  textTransform: 'uppercase',
  letterSpacing: '0.5px'
};

const tdStyle: React.CSSProperties = {
  padding: '12px 16px',
  color: '#e2e8f0',
  borderTop: '1px solid #33415520'
};
