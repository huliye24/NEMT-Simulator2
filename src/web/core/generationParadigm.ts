/**
 * Copyright 2026 NEMT Lab
 *
 * 统一生成范式 - 所有功能的生成都遵循同一套逻辑
 *
 * 核心理念：软件的成熟体现在新增能力是否仍然遵循同一套生成逻辑
 *
 * 生成流程：
 * Schema → Constraints → Validation → Generation → Registry
 *
 * 所有实体都必须：
 * 1. 定义 Schema (数据结构)
 * 2. 声明 Constraints (约束)
 * 3. 通过 Validation (验证)
 * 4. 由 Generator 生成
 * 5. 在 Registry 注册
 */

// ============================================
// 类型定义
// ============================================

/**
 * Schema 定义
 */
export interface Schema<T = any> {
  name: string;
  version: string;
  description?: string;
  fields: FieldSchema[];
  computed?: string[];
  indexes?: string[];
  constraints?: string[];
}

export interface FieldSchema {
  name: string;
  type: FieldType;
  required?: boolean;
  default?: any;
  description?: string;

  // 类型特定约束
  minLength?: number;
  maxLength?: number;
  min?: number;
  max?: number;
  pattern?: string;
  format?: string;
  enum?: any[];

  // 验证
  validator?: string;  // 验证器名称
}

export type FieldType =
  | 'string'
  | 'number'
  | 'boolean'
  | 'date'
  | 'datetime'
  | 'enum'
  | 'array'
  | 'object'
  | 'union';

/**
 * 约束定义
 */
export interface Constraint<T = any> {
  id: string;
  name: string;
  description: string;

  // 约束类型
  type: 'required' | 'unique' | 'range' | 'pattern' | 'custom' | 'relationship';

  // 验证函数
  validate: (value: T, context?: any) => ValidationResult;

  // 优先级
  priority: number;

  // 自动修复
  autoFix?: (value: T) => T;
}

export interface ValidationResult {
  valid: boolean;
  errors: ValidationError[];
  warnings: ValidationWarning[];
}

export interface ValidationError {
  path: string;
  message: string;
  constraintId?: string;
}

export interface ValidationWarning {
  path: string;
  message: string;
}

/**
 * 生成器定义
 */
export interface Generator<TInput = any, TOutput = any> {
  id: string;
  name: string;
  description?: string;

  // 输入 Schema
  inputSchema: Schema<TInput>;

  // 输出 Schema
  outputSchema?: Schema<TOutput>;

  // 生成函数
  generate: (input: TInput, context?: GenerationContext) => GeneratedOutput<TOutput>;

  // 约束
  constraints: Constraint[];
}

export interface GeneratedOutput<T = any> {
  data: T;
  metadata: {
    generatedBy: string;
    generatedAt: number;
    constraints: string[];
    warnings: string[];
  };
}

export interface GenerationContext {
  registry: EntityRegistry;
  validators: ValidatorEngine;
  previousOutput?: any;
}

// ============================================
// 实体注册表
// ============================================

export interface RegisteredEntity {
  name: string;
  schema: Schema;
  constraints: Constraint[];
  generators: Generator[];
  createdAt: number;
  updatedAt: number;
}

export class EntityRegistry {
  private entities: Map<string, RegisteredEntity> = new Map();
  private schemas: Map<string, Schema> = new Map();

  /**
   * 注册实体
   */
  register(entity: RegisteredEntity): void {
    this.entities.set(entity.name, {
      ...entity,
      updatedAt: Date.now()
    });
    this.schemas.set(entity.name, entity.schema);
  }

  /**
   * 获取实体
   */
  get(name: string): RegisteredEntity | undefined {
    return this.entities.get(name);
  }

  /**
   * 获取 Schema
   */
  getSchema(name: string): Schema | undefined {
    return this.schemas.get(name);
  }

  /**
   * 获取所有实体
   */
  getAll(): RegisteredEntity[] {
    return Array.from(this.entities.values());
  }

  /**
   * 查找实体
   */
  find(predicate: (entity: RegisteredEntity) => boolean): RegisteredEntity[] {
    return Array.from(this.entities.values()).filter(predicate);
  }
}

// ============================================
// 验证引擎
// ============================================

export class ValidatorEngine {
  private validators: Map<string, Constraint> = new Map();
  private registry: EntityRegistry;

  constructor(registry: EntityRegistry) {
    this.registry = registry;
  }

  /**
   * 注册验证器
   */
  register(constraint: Constraint): void {
    this.validators.set(constraint.id, constraint);
  }

  /**
   * 验证数据
   */
  validate(data: any, schema: Schema): ValidationResult {
    const errors: ValidationError[] = [];
    const warnings: ValidationWarning[] = [];

    // 验证每个字段
    for (const field of schema.fields) {
      const value = data[field.name];

      // 必填检查
      if (field.required && (value === undefined || value === null)) {
        errors.push({
          path: field.name,
          message: `${field.name} 是必填字段`
        });
        continue;
      }

      if (value === undefined || value === null) continue;

      // 类型检查
      const typeValid = this.validateType(value, field.type);
      if (!typeValid) {
        errors.push({
          path: field.name,
          message: `${field.name} 类型错误，期望 ${field.type}`
        });
      }

      // 长度检查
      if (field.type === 'string') {
        if (field.minLength && value.length < field.minLength) {
          errors.push({
            path: field.name,
            message: `${field.name} 长度不能少于 ${field.minLength}`
          });
        }
        if (field.maxLength && value.length > field.maxLength) {
          errors.push({
            path: field.name,
            message: `${field.name} 长度不能超过 ${field.maxLength}`
          });
        }
        if (field.pattern && !new RegExp(field.pattern).test(value)) {
          errors.push({
            path: field.name,
            message: `${field.name} 格式不正确`
          });
        }
      }

      // 范围检查
      if (field.type === 'number') {
        if (field.min !== undefined && value < field.min) {
          errors.push({
            path: field.name,
            message: `${field.name} 不能小于 ${field.min}`
          });
        }
        if (field.max !== undefined && value > field.max) {
          errors.push({
            path: field.name,
            message: `${field.name} 不能大于 ${field.max}`
          });
        }
      }

      // 枚举检查
      if (field.enum && !field.enum.includes(value)) {
        errors.push({
          path: field.name,
          message: `${field.name} 必须是 [${field.enum.join(', ')}] 之一`
        });
      }
    }

    return {
      valid: errors.length === 0,
      errors,
      warnings
    };
  }

  /**
   * 验证类型
   */
  private validateType(value: any, type: FieldType): boolean {
    switch (type) {
      case 'string': return typeof value === 'string';
      case 'number': return typeof value === 'number';
      case 'boolean': return typeof value === 'boolean';
      case 'date': return value instanceof Date || !isNaN(Date.parse(value));
      case 'datetime': return value instanceof Date || !isNaN(Date.parse(value));
      case 'enum': return true; // 枚举由具体验证器处理
      case 'array': return Array.isArray(value);
      case 'object': return typeof value === 'object' && value !== null && !Array.isArray(value);
      default: return true;
    }
  }

  /**
   * 获取验证器
   */
  getValidator(id: string): Constraint | undefined {
    return this.validators.get(id);
  }
}

// ============================================
// 生成引擎
// ============================================

export class GenerationEngine {
  private registry: EntityRegistry;
  private validator: ValidatorEngine;
  private generators: Map<string, Generator> = new Map();

  constructor(registry: EntityRegistry, validator: ValidatorEngine) {
    this.registry = registry;
    this.validator = validator;
  }

  /**
   * 注册生成器
   */
  register(generator: Generator): void {
    // 确保输入 Schema 已注册
    if (!this.registry.get(generator.inputSchema.name)) {
      this.registry.register({
        name: generator.inputSchema.name,
        schema: generator.inputSchema,
        constraints: generator.constraints,
        generators: [generator],
        createdAt: Date.now(),
        updatedAt: Date.now()
      });
    }

    this.generators.set(generator.id, generator);
  }

  /**
   * 生成
   */
  generate<TInput, TOutput>(
    generatorId: string,
    input: TInput,
    context?: Partial<GenerationContext>
  ): GeneratedOutput<TOutput> {
    const generator = this.generators.get(generatorId);
    if (!generator) {
      throw new Error(`Generator not found: ${generatorId}`);
    }

    // 1. 验证输入
    const validation = this.validator.validate(input, generator.inputSchema);
    if (!validation.valid) {
      return {
        data: null as any,
        metadata: {
          generatedBy: generatorId,
          generatedAt: Date.now(),
          constraints: [],
          warnings: validation.errors.map(e => e.message)
        }
      };
    }

    // 2. 生成
    const fullContext: GenerationContext = {
      registry: this.registry,
      validators: this.validator,
      ...context
    };

    const output = generator.generate(input, fullContext);

    // 3. 验证输出 (如果有)
    if (generator.outputSchema && output.data) {
      const outputValidation = this.validator.validate(output.data, generator.outputSchema);
      if (!outputValidation.valid) {
        output.metadata.warnings.push(...outputValidation.errors.map(e => e.message));
      }
    }

    // 4. 记录约束
    output.metadata.constraints = generator.constraints.map(c => c.id);

    return output;
  }

  /**
   * 获取生成器
   */
  get(generatorId: string): Generator | undefined {
    return this.generators.get(generatorId);
  }

  /**
   * 获取所有生成器
   */
  getAll(): Generator[] {
    return Array.from(this.generators.values());
  }
}

// ============================================
// 预定义生成器工厂
// ============================================

export function createFormGenerator(schema: Schema): Generator {
  return {
    id: `form_${schema.name}`,
    name: `生成 ${schema.name} 表单`,
    description: `基于 ${schema.name} Schema 生成表单组件`,
    inputSchema: schema,
    outputSchema: {
      name: `${schema.name}_form`,
      version: '1.0',
      fields: [
        { name: 'fields', type: 'array', description: '表单字段配置' },
        { name: 'layout', type: 'enum', enum: ['vertical', 'horizontal', 'grid'] },
        { name: 'validators', type: 'array', description: '验证器配置' }
      ]
    },
    constraints: [],
    generate: (input, context) => {
      const fields = schema.fields.map(field => ({
        name: field.name,
        type: inferComponentType(field),
        label: field.description || field.name,
        required: field.required,
        placeholder: `请输入${field.description || field.name}`,
        ...(field.enum && { options: field.enum.map(v => ({ label: v, value: v })) }),
        ...(field.min !== undefined && { min: field.min }),
        ...(field.max !== undefined && { max: field.max })
      }));

      return {
        data: {
          fields,
          layout: 'vertical',
          validators: schema.fields
            .filter(f => f.validator)
            .map(f => ({ field: f.name, validator: f.validator }))
        },
        metadata: {
          generatedBy: `form_${schema.name}`,
          generatedAt: Date.now(),
          constraints: [],
          warnings: []
        }
      };
    }
  };
}

export function createTableGenerator(schema: Schema): Generator {
  return {
    id: `table_${schema.name}`,
    name: `生成 ${schema.name} 表格`,
    description: `基于 ${schema.name} Schema 生成表格组件`,
    inputSchema: schema,
    constraints: [],
    generate: (input, context) => {
      const columns = schema.fields.map(field => ({
        key: field.name,
        title: field.description || field.name,
        sortable: field.type === 'number' || field.type === 'date',
        filterable: field.type === 'string' || field.enum !== undefined,
        width: field.type === 'string' && field.maxLength && field.maxLength > 100 ? 200 : 100
      }));

      return {
        data: { columns },
        metadata: {
          generatedBy: `table_${schema.name}`,
          generatedAt: Date.now(),
          constraints: [],
          warnings: []
        }
      };
    }
  };
}

export function createValidationGenerator(schema: Schema): Generator {
  return {
    id: `validation_${schema.name}`,
    name: `生成 ${schema.name} 验证器`,
    description: `基于 ${schema.name} Schema 生成验证函数`,
    inputSchema: schema,
    constraints: [],
    generate: (input, context) => {
      const validators = schema.fields.map(field => {
        const rules: string[] = [];

        if (field.required) rules.push('required');
        if (field.type === 'string') {
          if (field.minLength) rules.push(`minLength:${field.minLength}`);
          if (field.maxLength) rules.push(`maxLength:${field.maxLength}`);
          if (field.pattern) rules.push(`pattern:${field.pattern}`);
        }
        if (field.type === 'number') {
          if (field.min !== undefined) rules.push(`min:${field.min}`);
          if (field.max !== undefined) rules.push(`max:${field.max}`);
        }
        if (field.enum) rules.push(`enum:[${field.enum.join(',')}]`);

        return { field: field.name, rules };
      });

      return {
        data: { validators },
        metadata: {
          generatedBy: `validation_${schema.name}`,
          generatedAt: Date.now(),
          constraints: [],
          warnings: []
        }
      };
    }
  };
}

// ============================================
// 辅助函数
// ============================================

function inferComponentType(field: FieldSchema): string {
  if (field.enum) {
    return field.enum.length <= 3 ? 'radio' : 'select';
  }

  switch (field.type) {
    case 'boolean': return 'switch';
    case 'number': return field.min !== undefined || field.max !== undefined ? 'slider' : 'number';
    case 'date': return 'date';
    case 'datetime': return 'datetime';
    case 'string':
      if (field.maxLength && field.maxLength > 100) return 'textarea';
      return 'input';
    default: return 'input';
  }
}

// ============================================
// 全局实例
// ============================================

export const globalRegistry = new EntityRegistry();
export const globalValidator = new ValidatorEngine(globalRegistry);
export const globalGenerator = new GenerationEngine(globalRegistry, globalValidator);

// ============================================
// React Hook
// ============================================

import React, { useState, useCallback, useMemo } from 'react';

export function useGeneration() {
  const [output, setOutput] = useState<GeneratedOutput | null>(null);
  const [validation, setValidation] = useState<ValidationResult | null>(null);

  const generate = useCallback(<TInput, TOutput>(
    generatorId: string,
    input: TInput
  ) => {
    try {
      const result = globalGenerator.generate<TInput, TOutput>(generatorId, input);
      setOutput(result);
      setValidation({ valid: true, errors: [], warnings: [] });
      return result;
    } catch (error) {
      setValidation({
        valid: false,
        errors: [{ path: '', message: String(error) }],
        warnings: []
      });
      return null;
    }
  }, []);

  const registerEntity = useCallback((entity: RegisteredEntity) => {
    globalRegistry.register(entity);
  }, []);

  return {
    generate,
    registerEntity,
    output,
    validation,
    registry: globalRegistry,
    generator: globalGenerator
  };
}

// ============================================
// Schema 生成器
// ============================================

export function defineSchema<T extends Record<string, any>>(
  name: string,
  fields: (() => FieldSchema[]) | FieldSchema[]
): Schema {
  return {
    name,
    version: '1.0.0',
    fields: typeof fields === 'function' ? fields() : fields
  };
}

export function field(
  name: string,
  type: FieldType,
  options?: Partial<FieldSchema>
): FieldSchema {
  return { name, type, ...options };
}

export const t = {
  string: (name: string, options?: Partial<FieldSchema>) => field(name, 'string', options),
  number: (name: string, options?: Partial<FieldSchema>) => field(name, 'number', options),
  boolean: (name: string, options?: Partial<FieldSchema>) => field(name, 'boolean', options),
  date: (name: string, options?: Partial<FieldSchema>) => field(name, 'date', options),
  datetime: (name: string, options?: Partial<FieldSchema>) => field(name, 'datetime', options),
  enum: (name: string, values: any[], options?: Partial<FieldSchema>) =>
    field(name, 'enum', { enum: values, ...options }),
  array: (name: string, options?: Partial<FieldSchema>) => field(name, 'array', options),
  object: (name: string, options?: Partial<FieldSchema>) => field(name, 'object', options)
};
