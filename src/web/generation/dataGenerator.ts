/**
 * Copyright 2026 NEMT Lab
 *
 * 数据结构自动生成器 - 约束驱动的数据模型
 *
 * 核心理念：数据结构不是预先定义的，而是从约束中推导出来的
 *
 * 工作原理：
 * 1. 收集字段约束
 * 2. 分析约束依赖
 * 3. 生成最小完备的数据结构
 * 4. 验证生成的数据结构
 */

// ============================================
// 类型定义
// ============================================

export type FieldType =
  | 'string'
  | 'number'
  | 'boolean'
  | 'date'
  | 'enum'
  | 'array'
  | 'object'
  | 'union'
  | 'record';

export interface FieldConstraint {
  name: string;
  type: FieldType;

  // 通用约束
  required?: boolean;
  default?: any;
  nullable?: boolean;

  // 字符串约束
  minLength?: number;
  maxLength?: number;
  pattern?: RegExp;
  format?: 'email' | 'url' | 'uuid' | 'date' | 'time' | 'datetime';

  // 数值约束
  minimum?: number;
  maximum?: number;
  exclusiveMin?: number;
  exclusiveMax?: number;
  multipleOf?: number;

  // 枚举约束
  enumValues?: any[];

  // 数组约束
  itemType?: FieldType;
  minItems?: number;
  maxItems?: number;
  uniqueItems?: boolean;

  // 对象约束
  properties?: FieldConstraint[];

  // 联合类型
  oneOf?: FieldConstraint[];

  // 自定义验证
  validator?: (value: any) => boolean;
  errorMessage?: string;
}

export interface DataSchema {
  name: string;
  version: string;
  description?: string;
  fields: FieldConstraint[];
  indexes?: string[];
  computed?: string[];
  constraints?: string[];
}

export interface GeneratedData<T = any> {
  data: T;
  schema: DataSchema;
  metadata: {
    generatedAt: number;
    seed: number;
    constraints: string[];
    validation: ValidationResult;
  };
}

export interface ValidationResult {
  valid: boolean;
  errors: ValidationError[];
  warnings: ValidationWarning[];
}

export interface ValidationError {
  path: string;
  message: string;
  value?: any;
  constraint?: string;
}

export interface ValidationWarning {
  path: string;
  message: string;
}

// ============================================
// 数据生成器
// ============================================

export class DataGenerator {
  private seed: number;

  constructor(seed?: number) {
    this.seed = seed || Date.now();
  }

  /**
   * 生成随机数 (确定性)
   */
  private random(): number {
    this.seed = (this.seed * 9301 + 49297) % 233280;
    return this.seed / 233280;
  }

  /**
   * 从约束生成数据
   */
  generate(constraint: FieldConstraint): any {
    const { type, nullable, default: defaultVal } = constraint;

    // 可空处理
    if (nullable && this.random() < 0.1) {
      return null;
    }

    switch (type) {
      case 'string':
        return this.generateString(constraint);
      case 'number':
        return this.generateNumber(constraint);
      case 'boolean':
        return this.random() > 0.5;
      case 'date':
        return this.generateDate(constraint);
      case 'enum':
        return this.generateEnum(constraint);
      case 'array':
        return this.generateArray(constraint);
      case 'object':
        return this.generateObject(constraint);
      case 'union':
        return this.generateUnion(constraint);
      case 'record':
        return this.generateRecord(constraint);
      default:
        return null;
    }
  }

  private generateString(constraint: FieldConstraint): string {
    const { format, minLength = 1, maxLength = 100, pattern } = constraint;

    let value: string;

    switch (format) {
      case 'email':
        value = `user${this.random().toString(36).substr(2, 6)}@example.com`;
        break;
      case 'url':
        value = `https://example.com/${this.random().toString(36).substr(2, 8)}`;
        break;
      case 'uuid':
        value = this.generateUUID();
        break;
      case 'date':
        value = this.generateDateValue();
        break;
      case 'time':
        value = this.generateTimeValue();
        break;
      case 'datetime':
        value = this.generateDateTimeValue();
        break;
      default:
        value = this.generateRandomString(maxLength);
    }

    // 模式验证
    if (pattern) {
      let attempts = 0;
      while (!pattern.test(value) && attempts < 100) {
        value = this.generateRandomString(maxLength);
        attempts++;
      }
    }

    // 长度限制
    if (value.length < minLength) {
      value = value.padEnd(minLength, '0');
    }
    if (value.length > maxLength) {
      value = value.substring(0, maxLength);
    }

    return value;
  }

  private generateNumber(constraint: FieldConstraint): number {
    const {
      minimum = 0,
      maximum = 100,
      exclusiveMin,
      exclusiveMax,
      multipleOf
    } = constraint;

    let value = minimum + this.random() * (maximum - minimum);

    // 排除边界
    if (exclusiveMin !== undefined && value === exclusiveMin) {
      value = exclusiveMin + 0.001;
    }
    if (exclusiveMax !== undefined && value === exclusiveMax) {
      value = exclusiveMax - 0.001;
    }

    // 倍数约束
    if (multipleOf) {
      value = Math.round(value / multipleOf) * multipleOf;
    }

    // 保留合理精度
    return Number(value.toFixed(4));
  }

  private generateDate(constraint: FieldConstraint): string {
    return this.generateDateTimeValue();
  }

  private generateEnum(constraint: FieldConstraint): any {
    const { enumValues } = constraint;
    if (!enumValues || enumValues.length === 0) return null;
    return enumValues[Math.floor(this.random() * enumValues.length)];
  }

  private generateArray(constraint: FieldConstraint): any[] {
    const { itemType, minItems = 0, maxItems = 10, uniqueItems } = constraint;

    const itemConstraint: FieldConstraint = {
      name: 'item',
      type: itemType || 'string'
    };

    const count = Math.floor(minItems + this.random() * (maxItems - minItems + 1));
    const items: any[] = [];

    for (let i = 0; i < count; i++) {
      const item = this.generate(itemConstraint);
      items.push(item);
    }

    if (uniqueItems) {
      return [...new Set(items.map(i => JSON.stringify(i)))].map(i => JSON.parse(i));
    }

    return items;
  }

  private generateObject(constraint: FieldConstraint): Record<string, any> {
    const { properties } = constraint;
    if (!properties) return {};

    const obj: Record<string, any> = {};

    for (const prop of properties) {
      // 跳过可选字段
      if (!prop.required && this.random() < 0.3) {
        continue;
      }

      obj[prop.name] = this.generate(prop);
    }

    return obj;
  }

  private generateUnion(constraint: FieldConstraint): any {
    const { oneOf } = constraint;
    if (!oneOf || oneOf.length === 0) return null;

    const chosen = oneOf[Math.floor(this.random() * oneOf.length)];
    return this.generate(chosen);
  }

  private generateRecord(constraint: FieldConstraint): Record<string, any> {
    const { itemType, maxItems = 10 } = constraint;

    const itemConstraint: FieldConstraint = {
      name: 'value',
      type: itemType || 'string'
    };

    const count = Math.floor(this.random() * maxItems);
    const record: Record<string, any> = {};

    for (let i = 0; i < count; i++) {
      const key = `key_${i}_${this.random().toString(36).substr(2, 4)}`;
      record[key] = this.generate(itemConstraint);
    }

    return record;
  }

  private generateRandomString(length: number): string {
    const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
    let result = '';
    for (let i = 0; i < length; i++) {
      result += chars.charAt(Math.floor(this.random() * chars.length));
    }
    return result;
  }

  private generateUUID(): string {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
      const r = this.random() * 16 | 0;
      const v = c === 'x' ? r : (r & 0x3 | 0x8);
      return v.toString(16);
    });
  }

  private generateDateValue(): string {
    const date = new Date(Date.now() - this.random() * 365 * 24 * 60 * 60 * 1000);
    return date.toISOString().split('T')[0];
  }

  private generateTimeValue(): string {
    const hours = Math.floor(this.random() * 24);
    const minutes = Math.floor(this.random() * 60);
    const seconds = Math.floor(this.random() * 60);
    return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
  }

  private generateDateTimeValue(): string {
    return new Date(Date.now() - this.random() * 365 * 24 * 60 * 60 * 1000).toISOString();
  }
}

// ============================================
// 数据验证器
// ============================================

export class DataValidator {
  /**
   * 验证数据
   */
  validate(data: any, schema: DataSchema): ValidationResult {
    const errors: ValidationError[] = [];
    const warnings: ValidationWarning[] = [];

    for (const field of schema.fields) {
      const value = data[field.name];
      const fieldResult = this.validateField(value, field, field.name);
      errors.push(...fieldResult.errors);
      warnings.push(...fieldResult.warnings);
    }

    return {
      valid: errors.length === 0,
      errors,
      warnings
    };
  }

  private validateField(
    value: any,
    constraint: FieldConstraint,
    path: string
  ): { errors: ValidationError[]; warnings: ValidationWarning[] } {
    const errors: ValidationError[] = [];
    const warnings: ValidationWarning[] = [];

    // 空值检查
    if (value === null || value === undefined) {
      if (constraint.required) {
        errors.push({
          path,
          message: `${path} 是必填字段`,
          constraint: 'required'
        });
      }
      return { errors, warnings };
    }

    // 类型检查
    const actualType = this.getType(value);
    const expectedType = constraint.type;

    if (!this.isTypeCompatible(actualType, expectedType)) {
      errors.push({
        path,
        message: `${path} 类型错误: 期望 ${expectedType}, 实际 ${actualType}`,
        value,
        constraint: 'type'
      });
      return { errors, warnings };
    }

    // 类型特定验证
    switch (constraint.type) {
      case 'string':
        this.validateString(value, constraint, path, errors, warnings);
        break;
      case 'number':
        this.validateNumber(value, constraint, path, errors, warnings);
        break;
      case 'array':
        this.validateArray(value, constraint, path, errors, warnings);
        break;
      case 'object':
        this.validateObject(value, constraint, path, errors, warnings);
        break;
    }

    // 自定义验证
    if (constraint.validator && !constraint.validator(value)) {
      errors.push({
        path,
        message: constraint.errorMessage || `${path} 验证失败`,
        value,
        constraint: 'custom'
      });
    }

    return { errors, warnings };
  }

  private validateString(
    value: string,
    constraint: FieldConstraint,
    path: string,
    errors: ValidationError[],
    warnings: ValidationWarning[]
  ): void {
    const { minLength, maxLength, pattern, format } = constraint;

    if (minLength !== undefined && value.length < minLength) {
      errors.push({
        path,
        message: `${path} 长度不能少于 ${minLength}`,
        value,
        constraint: 'minLength'
      });
    }

    if (maxLength !== undefined && value.length > maxLength) {
      errors.push({
        path,
        message: `${path} 长度不能超过 ${maxLength}`,
        value,
        constraint: 'maxLength'
      });
    }

    if (pattern && !pattern.test(value)) {
      errors.push({
        path,
        message: `${path} 格式不正确`,
        value,
        constraint: 'pattern'
      });
    }

    if (format) {
      if (!this.validateFormat(value, format)) {
        warnings.push({
          path,
          message: `${path} 格式可能不正确 (期望 ${format})`
        });
      }
    }
  }

  private validateNumber(
    value: number,
    constraint: FieldConstraint,
    path: string,
    errors: ValidationError[],
    warnings: ValidationWarning[]
  ): void {
    const { minimum, maximum, exclusiveMin, exclusiveMax, multipleOf } = constraint;

    if (minimum !== undefined && value < minimum) {
      errors.push({
        path,
        message: `${path} 不能小于 ${minimum}`,
        value,
        constraint: 'minimum'
      });
    }

    if (maximum !== undefined && value > maximum) {
      errors.push({
        path,
        message: `${path} 不能大于 ${maximum}`,
        value,
        constraint: 'maximum'
      });
    }

    if (exclusiveMin !== undefined && value <= exclusiveMin) {
      errors.push({
        path,
        message: `${path} 必须大于 ${exclusiveMin}`,
        value,
        constraint: 'exclusiveMin'
      });
    }

    if (exclusiveMax !== undefined && value >= exclusiveMax) {
      errors.push({
        path,
        message: `${path} 必须小于 ${exclusiveMax}`,
        value,
        constraint: 'exclusiveMax'
      });
    }

    if (multipleOf !== undefined && value % multipleOf !== 0) {
      errors.push({
        path,
        message: `${path} 必须是 ${multipleOf} 的倍数`,
        value,
        constraint: 'multipleOf'
      });
    }
  }

  private validateArray(
    value: any[],
    constraint: FieldConstraint,
    path: string,
    errors: ValidationError[],
    warnings: ValidationWarning[]
  ): void {
    const { minItems, maxItems, uniqueItems, itemType } = constraint;

    if (minItems !== undefined && value.length < minItems) {
      errors.push({
        path,
        message: `${path} 至少需要 ${minItems} 个元素`,
        value,
        constraint: 'minItems'
      });
    }

    if (maxItems !== undefined && value.length > maxItems) {
      errors.push({
        path,
        message: `${path} 最多 ${maxItems} 个元素`,
        value,
        constraint: 'maxItems'
      });
    }

    if (uniqueItems) {
      const unique = new Set(value.map(i => JSON.stringify(i)));
      if (unique.size !== value.length) {
        errors.push({
          path,
          message: `${path} 元素必须唯一`,
          value,
          constraint: 'uniqueItems'
        });
      }
    }
  }

  private validateObject(
    value: Record<string, any>,
    constraint: FieldConstraint,
    path: string,
    errors: ValidationError[],
    warnings: ValidationWarning[]
  ): void {
    const { properties } = constraint;

    if (!properties) return;

    for (const prop of properties) {
      const propPath = `${path}.${prop.name}`;
      const propValue = value[prop.name];

      const propResult = this.validateField(propValue, prop, propPath);
      errors.push(...propResult.errors);
      warnings.push(...propResult.warnings);
    }
  }

  private getType(value: any): string {
    if (value === null) return 'null';
    if (Array.isArray(value)) return 'array';
    return typeof value;
  }

  private isTypeCompatible(actual: string, expected: FieldType): boolean {
    if (actual === expected) return true;

    // 数字和布尔可以互相转换
    if ((actual === 'number' || actual === 'boolean') && expected === 'number') return true;

    // 对象类型
    if (expected === 'object' && actual === 'object') return true;

    return false;
  }

  private validateFormat(value: string, format: string): boolean {
    const patterns: Record<string, RegExp> = {
      email: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
      url: /^https?:\/\/.+/,
      uuid: /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i,
      date: /^\d{4}-\d{2}-\d{2}$/,
      time: /^\d{2}:\d{2}:\d{2}$/,
      datetime: /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}/
    };

    const pattern = patterns[format];
    return pattern ? pattern.test(value) : true;
  }
}

// ============================================
// 策略数据结构
// ============================================

export const StrategySchema: DataSchema = {
  name: 'Strategy',
  version: '1.0.0',
  description: '交易策略数据结构',
  fields: [
    { name: 'id', type: 'string', required: true, format: 'uuid' },
    { name: 'name', type: 'string', required: true, minLength: 1, maxLength: 100 },
    { name: 'author', type: 'string', required: true },
    { name: 'description', type: 'string', maxLength: 1000 },
    { name: 'version', type: 'string', required: true, pattern: /^\d+\.\d+\.\d+/ },
    { name: 'status', type: 'enum', required: true, enumValues: ['draft', 'testing', 'running', 'paused', 'archived'] },
    { name: 'tags', type: 'array', itemType: 'string', maxItems: 20 },
    { name: 'createdAt', type: 'date', required: true },
    { name: 'updatedAt', type: 'date', required: true },
    { name: 'metrics', type: 'object', required: true, properties: [
      { name: 'totalTrades', type: 'number', minimum: 0 },
      { name: 'winRate', type: 'number', minimum: 0, maximum: 1 },
      { name: 'totalPnL', type: 'number' },
      { name: 'sharpeRatio', type: 'number', minimum: -10, maximum: 10 }
    ]}
  ],
  indexes: ['id', 'status', 'author'],
  constraints: ['strategy_name_required', 'strategy_status_transition']
};

// ============================================
// 全局实例
// ============================================

export const dataGenerator = new DataGenerator();
export const dataValidator = new DataValidator();

// ============================================
// 工具函数
// ============================================

export function generateStrategyData(): GeneratedData {
  const data = dataGenerator.generate({
    name: 'strategy',
    type: 'object',
    properties: StrategySchema.fields
  } as FieldConstraint);

  const validation = dataValidator.validate(data, StrategySchema);

  return {
    data,
    schema: StrategySchema,
    metadata: {
      generatedAt: Date.now(),
      seed: dataGenerator['seed'],
      constraints: StrategySchema.constraints || [],
      validation
    }
  };
}

export function validateData(data: any, schema: DataSchema): ValidationResult {
  return dataValidator.validate(data, schema);
}
