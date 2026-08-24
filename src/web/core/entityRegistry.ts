/**
 * Copyright 2026 NEMT Lab
 *
 * 实体注册系统 - 所有实体都通过约束注册
 *
 * 核心理念：软件中的一切都是实体，都必须遵循同一套生成逻辑
 *
 * 实体类型：
 * - Strategy (策略)
 * - Capsule (胶囊)
 * - Signal (信号)
 * - RiskRule (风控规则)
 * - Metric (指标)
 * - Workflow (工作流)
 */

// ============================================
// 预定义实体 Schema
// ============================================

import { Schema, FieldSchema } from './generationParadigm';

export const StrategySchema: Schema = {
  name: 'Strategy',
  version: '1.0.0',
  description: '交易策略',
  fields: [
    { name: 'id', type: 'string', required: true, description: '唯一标识' },
    { name: 'name', type: 'string', required: true, minLength: 1, maxLength: 100, description: '策略名称' },
    { name: 'author', type: 'string', required: true, description: '作者' },
    { name: 'description', type: 'string', maxLength: 1000, description: '描述' },
    { name: 'version', type: 'string', required: true, pattern: '^\\d+\\.\\d+\\.\\d+$', description: '版本号' },
    { name: 'status', type: 'enum', enum: ['draft', 'testing', 'running', 'paused', 'archived'], required: true, description: '状态' },
    { name: 'tags', type: 'array', description: '标签' },
    { name: 'createdAt', type: 'datetime', required: true, description: '创建时间' },
    { name: 'updatedAt', type: 'datetime', required: true, description: '更新时间' },
    { name: 'metrics', type: 'object', description: '性能指标',
      required: false // 简化处理
    },
    { name: 'config', type: 'object', description: '策略配置' },
    { name: 'source', type: 'string', description: '源代码' }
  ],
  indexes: ['id', 'status', 'author'],
  constraints: ['strategy_name_required', 'strategy_unique_name', 'strategy_status_transition']
};

export const CapsuleSchema: Schema = {
  name: 'Capsule',
  version: '1.0.0',
  description: '功能胶囊',
  fields: [
    { name: 'id', type: 'string', required: true, description: '唯一标识' },
    { name: 'name', type: 'string', required: true, minLength: 1, maxLength: 50, description: '胶囊名称' },
    { name: 'type', type: 'enum', enum: ['market', 'signal', 'risk', 'execution', 'monitor'], required: true, description: '胶囊类型' },
    { name: 'status', type: 'enum', enum: ['inactive', 'active', 'error', 'maintenance'], required: true, description: '状态' },
    { name: 'instanceCount', type: 'number', min: 0, max: 100, description: '实例数量' },
    { name: 'cpuUsage', type: 'number', min: 0, max: 100, description: 'CPU使用率' },
    { name: 'memoryUsage', type: 'number', min: 0, max: 100, description: '内存使用率' },
    { name: 'lastHeartbeat', type: 'datetime', description: '最后心跳时间' },
    { name: 'config', type: 'object', description: '胶囊配置' }
  ],
  indexes: ['id', 'type', 'status'],
  constraints: ['capsule_minimum', 'capsule_instance_max']
};

export const SignalSchema: Schema = {
  name: 'Signal',
  version: '1.0.0',
  description: '交易信号',
  fields: [
    { name: 'id', type: 'string', required: true, description: '唯一标识' },
    { name: 'strategyId', type: 'string', required: true, description: '策略ID' },
    { name: 'type', type: 'enum', enum: ['BUY', 'SELL', 'HOLD'], required: true, description: '信号类型' },
    { name: 'symbol', type: 'string', required: true, description: '交易品种' },
    { name: 'price', type: 'number', min: 0, required: true, description: '信号价格' },
    { name: 'quantity', type: 'number', min: 0, description: '数量' },
    { name: 'confidence', type: 'number', min: 0, max: 1, description: '置信度' },
    { name: 'timestamp', type: 'datetime', required: true, description: '生成时间' },
    { name: 'status', type: 'enum', enum: ['pending', 'executed', 'rejected', 'expired'], description: '状态' }
  ],
  indexes: ['id', 'strategyId', 'timestamp'],
  constraints: []
};

export const RiskRuleSchema: Schema = {
  name: 'RiskRule',
  version: '1.0.0',
  description: '风控规则',
  fields: [
    { name: 'id', type: 'string', required: true, description: '唯一标识' },
    { name: 'name', type: 'string', required: true, description: '规则名称' },
    { name: 'type', type: 'enum', enum: ['position', 'loss', 'exposure', 'leverage', 'custom'], required: true, description: '规则类型' },
    { name: 'enabled', type: 'boolean', required: true, description: '是否启用' },
    { name: 'priority', type: 'number', min: 1, max: 100, description: '优先级' },
    { name: 'threshold', type: 'number', required: true, description: '阈值' },
    { name: 'action', type: 'enum', enum: ['block', 'warn', 'reduce', 'close'], required: true, description: '触发动作' },
    { name: 'scope', type: 'enum', enum: ['global', 'strategy', 'symbol'], description: '作用范围' }
  ],
  indexes: ['id', 'type', 'enabled'],
  constraints: []
};

export const MetricSchema: Schema = {
  name: 'Metric',
  version: '1.0.0',
  description: '性能指标',
  fields: [
    { name: 'id', type: 'string', required: true, description: '唯一标识' },
    { name: 'name', type: 'string', required: true, description: '指标名称' },
    { name: 'type', type: 'enum', enum: ['counter', 'gauge', 'histogram', 'summary'], required: true, description: '指标类型' },
    { name: 'value', type: 'number', required: true, description: '当前值' },
    { name: 'unit', type: 'string', description: '单位' },
    { name: 'timestamp', type: 'datetime', required: true, description: '采集时间' },
    { name: 'tags', type: 'object', description: '标签' }
  ],
  indexes: ['id', 'name', 'timestamp'],
  constraints: []
};

export const WorkflowSchema: Schema = {
  name: 'Workflow',
  version: '1.0.0',
  description: '工作流',
  fields: [
    { name: 'id', type: 'string', required: true, description: '唯一标识' },
    { name: 'name', type: 'string', required: true, description: '工作流名称' },
    { name: 'description', type: 'string', description: '描述' },
    { name: 'nodes', type: 'array', required: true, description: '节点' },
    { name: 'edges', type: 'array', required: true, description: '边' },
    { name: 'status', type: 'enum', enum: ['draft', 'active', 'paused', 'archived'], description: '状态' },
    { name: 'triggers', type: 'array', description: '触发器' },
    { name: 'createdAt', type: 'datetime', required: true, description: '创建时间' }
  ],
  indexes: ['id', 'status'],
  constraints: []
};

// ============================================
// 实体管理器
// ============================================

import { EntityRegistry, ValidationResult } from './generationParadigm';

export interface EntityInstance {
  id: string;
  _schema: string;
  _createdAt: number;
  _updatedAt: number;
  [key: string]: any;
}

export class EntityManager {
  private registry: EntityRegistry;
  private instances: Map<string, Map<string, EntityInstance>> = new Map();

  constructor(registry: EntityRegistry) {
    this.registry = registry;

    // 注册所有预定义 Schema
    this.registerSchema(StrategySchema);
    this.registerSchema(CapsuleSchema);
    this.registerSchema(SignalSchema);
    this.registerSchema(RiskRuleSchema);
    this.registerSchema(MetricSchema);
    this.registerSchema(WorkflowSchema);

    // 初始化实例存储
    this.instances.set('Strategy', new Map());
    this.instances.set('Capsule', new Map());
    this.instances.set('Signal', new Map());
    this.instances.set('RiskRule', new Map());
    this.instances.set('Metric', new Map());
    this.instances.set('Workflow', new Map());
  }

  /**
   * 注册 Schema
   */
  registerSchema(schema: Schema): void {
    this.registry.register({
      name: schema.name,
      schema,
      constraints: [],
      generators: [],
      createdAt: Date.now(),
      updatedAt: Date.now()
    });
  }

  /**
   * 创建实体
   */
  create<T extends EntityInstance>(
    entityType: string,
    data: Partial<T>
  ): { entity: T; validation: ValidationResult } {
    const schema = this.registry.getSchema(entityType);
    if (!schema) {
      throw new Error(`Schema not found: ${entityType}`);
    }

    // 验证数据
    const validator = this.getValidator(entityType);
    const validation = validator.validate(data, schema);

    if (!validation.valid) {
      return {
        entity: null as any,
        validation
      };
    }

    // 创建实体
    const entity: EntityInstance = {
      id: data.id || `${entityType.toLowerCase()}_${Date.now()}`,
      _schema: entityType,
      _createdAt: Date.now(),
      _updatedAt: Date.now(),
      ...data
    } as EntityInstance;

    // 存储
    const typeInstances = this.instances.get(entityType);
    if (typeInstances) {
      typeInstances.set(entity.id, entity);
    }

    return { entity: entity as T, validation };
  }

  /**
   * 获取实体
   */
  get<T extends EntityInstance>(entityType: string, id: string): T | undefined {
    const typeInstances = this.instances.get(entityType);
    return typeInstances?.get(id) as T | undefined;
  }

  /**
   * 查询实体
   */
  query<T extends EntityInstance>(
    entityType: string,
    predicate: (entity: T) => boolean
  ): T[] {
    const typeInstances = this.instances.get(entityType);
    if (!typeInstances) return [];

    return Array.from(typeInstances.values()).filter(
      (entity): entity is T => predicate(entity as T)
    );
  }

  /**
   * 更新实体
   */
  update<T extends EntityInstance>(
    entityType: string,
    id: string,
    data: Partial<T>
  ): { entity: T; validation: ValidationResult } {
    const existing = this.get<T>(entityType, id);
    if (!existing) {
      return {
        entity: null as any,
        validation: {
          valid: false,
          errors: [{ path: 'id', message: 'Entity not found' }],
          warnings: []
        }
      };
    }

    // 合并数据
    const merged = { ...existing, ...data, _updatedAt: Date.now() };

    // 验证
    const schema = this.registry.getSchema(entityType);
    const validator = this.getValidator(entityType);
    const validation = validator.validate(merged, schema!);

    if (validation.valid) {
      const typeInstances = this.instances.get(entityType);
      typeInstances?.set(id, merged);
    }

    return { entity: merged, validation };
  }

  /**
   * 删除实体
   */
  delete(entityType: string, id: string): boolean {
    const typeInstances = this.instances.get(entityType);
    return typeInstances?.delete(id) || false;
  }

  /**
   * 获取所有实体
   */
  getAll<T extends EntityInstance>(entityType: string): T[] {
    const typeInstances = this.instances.get(entityType);
    return typeInstances ? Array.from(typeInstances.values()) as T[] : [];
  }

  /**
   * 获取验证器
   */
  private getValidator(entityType: string) {
    // 简单的验证器实现
    const schema = this.registry.getSchema(entityType);
    return {
      validate: (data: any, schema: Schema) => {
        const errors: { path: string; message: string }[] = [];

        for (const field of schema.fields) {
          const value = data[field.name];

          if (field.required && (value === undefined || value === null)) {
            errors.push({ path: field.name, message: `${field.name} 是必填字段` });
            continue;
          }

          if (value === undefined || value === null) continue;

          // 类型检查
          const expectedType = field.type;
          const actualType = Array.isArray(value) ? 'array' : typeof value;

          if (expectedType !== 'object' && expectedType !== actualType) {
            // 允许一些类型兼容
            if (!(expectedType === 'number' && actualType === 'string' && !isNaN(Number(value)))) {
              errors.push({
                path: field.name,
                message: `${field.name} 类型错误，期望 ${expectedType}`
              });
            }
          }
        }

        return { valid: errors.length === 0, errors, warnings: [] };
      }
    };
  }

  /**
   * 获取统计
   */
  getStats(): Record<string, number> {
    const stats: Record<string, number> = {};
    this.instances.forEach((instances, type) => {
      stats[type] = instances.size;
    });
    return stats;
  }
}

// ============================================
// 全局实例
// ============================================

import { globalRegistry } from './generationParadigm';

export const entityManager = new EntityManager(globalRegistry);

// ============================================
// React Hook
// ============================================

import React, { useState, useCallback, useMemo } from 'react';

export function useEntity<T extends EntityInstance>(
  entityType: string,
  id?: string
) {
  const [entity, setEntity] = useState<T | undefined>(
    id ? entityManager.get<T>(entityType, id) : undefined
  );
  const [validation, setValidation] = useState<ValidationResult | null>(null);

  const create = useCallback((data: Partial<T>) => {
    const result = entityManager.create<T>(entityType, data);
    setValidation(result.validation);
    if (result.validation.valid) {
      setEntity(result.entity);
    }
    return result;
  }, [entityType]);

  const update = useCallback((data: Partial<T>) => {
    if (!entity) return { entity: undefined, validation: null };
    const result = entityManager.update<T>(entityType, entity.id, data);
    setValidation(result.validation);
    if (result.validation.valid) {
      setEntity(result.entity);
    }
    return result;
  }, [entityType, entity]);

  const remove = useCallback(() => {
    if (!entity) return false;
    const success = entityManager.delete(entityType, entity.id);
    if (success) setEntity(undefined);
    return success;
  }, [entityType, entity]);

  return {
    entity,
    validation,
    create,
    update,
    remove
  };
}

export function useEntities<T extends EntityInstance>(entityType: string) {
  const [entities, setEntities] = useState<T[]>(() => entityManager.getAll<T>(entityType));

  const refresh = useCallback(() => {
    setEntities(entityManager.getAll<T>(entityType));
  }, [entityType]);

  const query = useCallback((predicate: (entity: T) => boolean) => {
    return entityManager.query<T>(entityType, predicate);
  }, [entityType]);

  return {
    entities,
    refresh,
    query,
    stats: entityManager.getStats()
  };
}
