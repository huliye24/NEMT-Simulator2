/**
 * Copyright 2026 NEMT Lab
 *
 * 统一验证管道 - 所有数据都经过同一套验证
 *
 * 核心理念：验证不是附加的，而是生成流程的一部分
 */

// ============================================
// 管道定义
// ============================================

import { Schema, ValidationResult, ValidationError, ValidationWarning } from './generationParadigm';

export interface ValidationRule {
  id: string;
  name: string;
  type: 'type' | 'range' | 'pattern' | 'custom' | 'business';
  validator: (value: any) => boolean;
  message: string;
}

export interface ValidationPipe {
  id: string;
  name: string;
  schema: Schema;
  rules: ValidationRule[];
  transformers: Transformer[];
}

export interface Transformer {
  id: string;
  name: string;
  transform: (value: any) => any;
}

// ============================================
// 管道执行器
// ============================================

export class ValidationPipeline {
  private pipes: Map<string, ValidationPipe> = new Map();

  /**
   * 注册管道
   */
  register(pipe: ValidationPipe): void {
    this.pipes.set(pipe.id, pipe);
  }

  /**
   * 执行验证
   */
  validate(data: any, schema: Schema): ValidationResult {
    const errors: ValidationError[] = [];
    const warnings: ValidationWarning[] = [];

    // 验证每个字段
    for (const field of schema.fields) {
      const value = data[field.name];

      // 必填验证
      if (field.required && (value === undefined || value === null || value === '')) {
        errors.push({
          path: field.name,
          message: `${field.name} 是必填字段`
        });
        continue;
      }

      if (value === undefined || value === null) continue;

      // 类型验证
      const typeError = this.validateType(value, field);
      if (typeError) {
        errors.push({ path: field.name, message: typeError });
      }

      // 范围验证
      const rangeError = this.validateRange(value, field);
      if (rangeError) {
        errors.push({ path: field.name, message: rangeError });
      }

      // 模式验证
      if (field.pattern && typeof value === 'string') {
        const pattern = new RegExp(field.pattern);
        if (!pattern.test(value)) {
          errors.push({
            path: field.name,
            message: `${field.name} 格式不正确`
          });
        }
      }

      // 枚举验证
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
   * 类型验证
   */
  private validateType(value: any, field: Schema['fields'][0]): string | null {
    const expectedType = field.type;

    switch (expectedType) {
      case 'string':
        if (typeof value !== 'string') {
          return `${field.name} 必须是字符串`;
        }
        break;
      case 'number':
        if (typeof value !== 'number' || isNaN(value)) {
          return `${field.name} 必须是数字`;
        }
        break;
      case 'boolean':
        if (typeof value !== 'boolean') {
          return `${field.name} 必须是布尔值`;
        }
        break;
      case 'date':
      case 'datetime':
        if (isNaN(Date.parse(value))) {
          return `${field.name} 必须是有效的日期`;
        }
        break;
      case 'array':
        if (!Array.isArray(value)) {
          return `${field.name} 必须是数组`;
        }
        break;
      case 'object':
        if (typeof value !== 'object' || value === null || Array.isArray(value)) {
          return `${field.name} 必须是对象`;
        }
        break;
    }

    return null;
  }

  /**
   * 范围验证
   */
  private validateRange(value: any, field: Schema['fields'][0]): string | null {
    if (field.type === 'string') {
      if (field.minLength && value.length < field.minLength) {
        return `${field.name} 长度不能少于 ${field.minLength}`;
      }
      if (field.maxLength && value.length > field.maxLength) {
        return `${field.name} 长度不能超过 ${field.maxLength}`;
      }
    }

    if (field.type === 'number') {
      if (field.min !== undefined && value < field.min) {
        return `${field.name} 不能小于 ${field.min}`;
      }
      if (field.max !== undefined && value > field.max) {
        return `${field.name} 不能大于 ${field.max}`;
      }
    }

    return null;
  }

  /**
   * 转换数据
   */
  transform(data: any, transformers: Transformer[]): any {
    let result = { ...data };

    for (const transformer of transformers) {
      for (const key in result) {
        try {
          result[key] = transformer.transform(result[key]);
        } catch (e) {
          // 忽略转换错误
        }
      }
    }

    return result;
  }

  /**
   * 获取管道
   */
  getPipe(id: string): ValidationPipe | undefined {
    return this.pipes.get(id);
  }
}

// ============================================
// 业务规则验证器
// ============================================

export const BusinessValidators = {
  // 策略验证
  strategy: {
    nameRequired: (data: any): ValidationResult => {
      const errors: ValidationError[] = [];

      if (!data.name || data.name.trim().length === 0) {
        errors.push({ path: 'name', message: '策略名称不能为空' });
      }

      if (data.name && data.name.length > 100) {
        errors.push({ path: 'name', message: '策略名称不能超过100字符' });
      }

      return { valid: errors.length === 0, errors, warnings: [] };
    },

    statusTransition: (data: any, previousStatus?: string): ValidationResult => {
      const errors: ValidationError[] = [];

      const validTransitions: Record<string, string[]> = {
        draft: ['testing', 'archived'],
        testing: ['running', 'draft', 'archived'],
        running: ['paused', 'archived'],
        paused: ['running', 'archived'],
        archived: ['draft']
      };

      if (previousStatus && data.status !== previousStatus) {
        const allowed = validTransitions[previousStatus] || [];
        if (!allowed.includes(data.status)) {
          errors.push({
            path: 'status',
            message: `状态不能从 ${previousStatus} 转换到 ${data.status}`
          });
        }
      }

      return { valid: errors.length === 0, errors, warnings: [] };
    },

    runningLimit: (data: any, currentRunning: number): ValidationResult => {
      const errors: ValidationError[] = [];
      const warnings: ValidationWarning[] = [];

      if (data.status === 'running' && currentRunning >= 10) {
        warnings.push({
          path: 'status',
          message: `当前已有 ${currentRunning} 个策略运行中，建议不超过 10 个`
        });
      }

      return { valid: errors.length === 0, errors, warnings };
    }
  },

  // 胶囊验证
  capsule: {
    coreOnline: (data: any, coreCapsules: any[]): ValidationResult => {
      const errors: ValidationError[] = [];

      const coreTypes = ['market', 'risk'];
      const onlineCapsules = coreCapsules.filter(c => c.status === 'active').map(c => c.type);

      for (const type of coreTypes) {
        if (!onlineCapsules.includes(type)) {
          errors.push({
            path: 'capsule',
            message: `核心胶囊 ${type} 必须保持在线`
          });
        }
      }

      return { valid: errors.length === 0, errors, warnings: [] };
    }
  },

  // 信号验证
  signal: {
    priceValid: (data: any): ValidationResult => {
      const errors: ValidationError[] = [];

      if (data.price !== undefined && data.price <= 0) {
        errors.push({ path: 'price', message: '价格必须大于0' });
      }

      if (data.confidence !== undefined && (data.confidence < 0 || data.confidence > 1)) {
        errors.push({ path: 'confidence', message: '置信度必须在0-1之间' });
      }

      return { valid: errors.length === 0, errors, warnings: [] };
    }
  }
};

// ============================================
// 全局实例
// ============================================

export const validationPipeline = new ValidationPipeline();

// ============================================
// React Hook
// ============================================

import React, { useState, useCallback, useMemo } from 'react';

export function useValidation(schema: Schema) {
  const [result, setResult] = useState<ValidationResult | null>(null);

  const validate = useCallback((data: any): ValidationResult => {
    const validationResult = validationPipeline.validate(data, schema);
    setResult(validationResult);
    return validationResult;
  }, [schema]);

  const validateWithBusiness = useCallback((data: any, businessRules: Array<(data: any) => ValidationResult>): ValidationResult => {
    // 先执行 Schema 验证
    let combinedResult = validationPipeline.validate(data, schema);

    // 再执行业务规则
    for (const rule of businessRules) {
      const ruleResult = rule(data);
      combinedResult.errors.push(...ruleResult.errors);
      combinedResult.warnings.push(...ruleResult.warnings);
    }

    combinedResult.valid = combinedResult.errors.length === 0;
    setResult(combinedResult);

    return combinedResult;
  }, [schema]);

  return {
    result,
    validate,
    validateWithBusiness,
    isValid: result?.valid ?? true
  };
}
