/**
 * Copyright 2026 NEMT Lab
 *
 * 规则约束引擎 - 软件生成的宪法
 *
 * 核心理念：不是"怎么写"，而是"什么可以做"
 * 约束定义了可能性的边界，生成器在边界内探索最优解
 *
 * 约束类型：
 * - Invariant: 不变量 (必须始终满足)
 * - Precondition: 前置条件 (操作前必须满足)
 * - Postcondition: 后置条件 (操作后必须满足)
 * - Transition: 状态转换 (状态机规则)
 * - Cardinality: 基数约束 (数量限制)
 * - Relationship: 关系约束 (元素间关系)
 * - Property: 属性约束 (值的合法范围)
 */

// ============================================
// 约束类型
// ============================================

export type ConstraintType =
  | 'invariant'    // 不变量
  | 'precondition' // 前置条件
  | 'postcondition' // 后置条件
  | 'transition'   // 状态转换
  | 'cardinality'  // 基数
  | 'relationship' // 关系
  | 'property';    // 属性

export type ConstraintSeverity = 'error' | 'warning' | 'info';

// ============================================
// 约束定义
// ============================================

export interface Constraint<T = any> {
  id: string;
  name: string;
  description: string;
  type: ConstraintType;
  severity: ConstraintSeverity;

  // 约束条件
  condition: (context: ConstraintContext) => boolean;

  // 违反时的消息
  message: (context: ConstraintContext) => string;

  // 约束元数据
  metadata: {
    category: string;
    tags: string[];
    version: number;
    author: 'system' | 'user';
    enabled: boolean;
    weight: number;  // 权重，用于优先级排序
  };

  // 修复建议
  fixes?: Array<{
    name: string;
    description: string;
    apply: (context: ConstraintContext) => ConstraintContext;
  }>;
}

export interface ConstraintContext {
  // 当前状态
  state: Record<string, any>;

  // 实体集合
  entities: Map<string, any[]>;

  // 操作历史
  history: Operation[];

  // 当前操作
  currentOperation?: Operation;

  // 约束变量
  variables: Record<string, any>;
}

export interface Operation {
  id: string;
  type: string;
  timestamp: number;
  entity?: string;
  before?: any;
  after?: any;
  userId?: string;
}

// ============================================
// 约束引擎
// ============================================

export class ConstraintEngine {
  private constraints: Map<string, Constraint> = new Map();
  private constraintHistory: ConstraintViolation[] = [];

  /**
   * 注册约束
   */
  register(constraint: Constraint): void {
    this.constraints.set(constraint.id, constraint);
    console.log(`[ConstraintEngine] Registered: ${constraint.name}`);
  }

  /**
   * 批量注册
   */
  registerBatch(constraints: Constraint[]): void {
    constraints.forEach(c => this.register(c));
  }

  /**
   * 验证约束
   */
  validate(context: ConstraintContext): ValidationResult {
    const violations: ConstraintViolation[] = [];

    for (const constraint of this.constraints.values()) {
      if (!constraint.metadata.enabled) continue;

      try {
        const satisfied = constraint.condition(context);

        if (!satisfied) {
          violations.push({
            constraintId: constraint.id,
            constraintName: constraint.name,
            message: constraint.message(context),
            severity: constraint.severity,
            timestamp: Date.now(),
            context: this.sanitizeContext(context)
          });
        }
      } catch (error) {
        violations.push({
          constraintId: constraint.id,
          constraintName: constraint.name,
          message: `约束评估错误: ${error}`,
          severity: 'error',
          timestamp: Date.now(),
          context: this.sanitizeContext(context)
        });
      }
    }

    // 记录历史
    this.constraintHistory.push(...violations);
    if (this.constraintHistory.length > 1000) {
      this.constraintHistory = this.constraintHistory.slice(-1000);
    }

    return {
      valid: violations.filter(v => v.severity === 'error').length === 0,
      violations,
      errorCount: violations.filter(v => v.severity === 'error').length,
      warningCount: violations.filter(v => v.severity === 'warning').length,
      infoCount: violations.filter(v => v.severity === 'info').length
    };
  }

  /**
   * 预验证 (操作前)
   */
  preValidate(
    context: ConstraintContext,
    operationType: string
  ): ValidationResult {
    const preConstraints = Array.from(this.constraints.values())
      .filter(c =>
        c.type === 'precondition' ||
        c.type === 'invariant' ||
        (c.type === 'transition' && this.isTransitionFor(c, operationType))
      );

    const violations: ConstraintViolation[] = [];

    for (const constraint of preConstraints) {
      if (!constraint.metadata.enabled) continue;

      try {
        const satisfied = constraint.condition(context);

        if (!satisfied) {
          violations.push({
            constraintId: constraint.id,
            constraintName: constraint.name,
            message: `[前置] ${constraint.message(context)}`,
            severity: constraint.severity,
            timestamp: Date.now(),
            context: this.sanitizeContext(context)
          });
        }
      } catch (error) {
        violations.push({
          constraintId: constraint.id,
          constraintName: constraint.name,
          message: `约束评估错误: ${error}`,
          severity: 'error',
          timestamp: Date.now(),
          context: this.sanitizeContext(context)
        });
      }
    }

    return {
      valid: violations.filter(v => v.severity === 'error').length === 0,
      violations,
      errorCount: violations.filter(v => v.severity === 'error').length,
      warningCount: violations.filter(v => v.severity === 'warning').length,
      infoCount: violations.filter(v => v.severity === 'info').length
    };
  }

  /**
   * 后验证 (操作后)
   */
  postValidate(
    context: ConstraintContext,
    operationType: string
  ): ValidationResult {
    const postConstraints = Array.from(this.constraints.values())
      .filter(c =>
        c.type === 'postcondition' ||
        c.type === 'invariant'
      );

    const violations: ConstraintViolation[] = [];

    for (const constraint of postConstraints) {
      if (!constraint.metadata.enabled) continue;

      try {
        const satisfied = constraint.condition(context);

        if (!satisfied) {
          violations.push({
            constraintId: constraint.id,
            constraintName: constraint.name,
            message: `[后置] ${constraint.message(context)}`,
            severity: constraint.severity,
            timestamp: Date.now(),
            context: this.sanitizeContext(context)
          });
        }
      } catch (error) {
        violations.push({
          constraintId: constraint.id,
          constraintName: constraint.name,
          message: `约束评估错误: ${error}`,
          severity: 'error',
          timestamp: Date.now(),
          context: this.sanitizeContext(context)
        });
      }
    }

    return {
      valid: violations.filter(v => v.severity === 'error').length === 0,
      violations,
      errorCount: violations.filter(v => v.severity === 'error').length,
      warningCount: violations.filter(v => v.severity === 'warning').length,
      infoCount: violations.filter(v => v.severity === 'info').length
    };
  }

  /**
   * 获取建议的修复
   */
  getSuggestedFixes(
    context: ConstraintContext,
    constraintId?: string
  ): FixSuggestion[] {
    const suggestions: FixSuggestion[] = [];

    const targetConstraints = constraintId
      ? [this.constraints.get(constraintId)].filter(Boolean) as Constraint[]
      : Array.from(this.constraints.values());

    for (const constraint of targetConstraints) {
      if (!constraint.metadata.enabled || !constraint.fixes) continue;

      try {
        const satisfied = constraint.condition(context);

        if (!satisfied) {
          for (const fix of constraint.fixes) {
            suggestions.push({
              constraintId: constraint.id,
              constraintName: constraint.name,
              fixName: fix.name,
              fixDescription: fix.description,
              apply: () => fix.apply(context)
            });
          }
        }
      } catch (error) {
        // 忽略
      }
    }

    return suggestions;
  }

  /**
   * 启用/禁用约束
   */
  setEnabled(constraintId: string, enabled: boolean): void {
    const constraint = this.constraints.get(constraintId);
    if (constraint) {
      constraint.metadata.enabled = enabled;
    }
  }

  /**
   * 获取所有约束
   */
  getConstraints(): Constraint[] {
    return Array.from(this.constraints.values());
  }

  /**
   * 按类别获取约束
   */
  getConstraintsByCategory(category: string): Constraint[] {
    return Array.from(this.constraints.values())
      .filter(c => c.metadata.category === category);
  }

  /**
   * 获取约束历史
   */
  getHistory(): ConstraintViolation[] {
    return [...this.constraintHistory];
  }

  /**
   * 清除历史
   */
  clearHistory(): void {
    this.constraintHistory = [];
  }

  private isTransitionFor(constraint: Constraint, operationType: string): boolean {
    // 简化检查 - 实际应检查状态转换规则
    return constraint.name.toLowerCase().includes(operationType.toLowerCase());
  }

  private sanitizeContext(context: ConstraintContext): Record<string, any> {
    // 移除敏感数据
    return JSON.parse(JSON.stringify({
      state: context.state,
      entityCount: Object.fromEntries(
        Array.from(context.entities.entries()).map(([k, v]) => [k, v.length])
      ),
      historyLength: context.history.length,
      variables: context.variables
    }));
  }
}

export interface ConstraintViolation {
  constraintId: string;
  constraintName: string;
  message: string;
  severity: ConstraintSeverity;
  timestamp: number;
  context: Record<string, any>;
}

export interface ValidationResult {
  valid: boolean;
  violations: ConstraintViolation[];
  errorCount: number;
  warningCount: number;
  infoCount: number;
}

export interface FixSuggestion {
  constraintId: string;
  constraintName: string;
  fixName: string;
  fixDescription: string;
  apply: () => ConstraintContext;
}

// ============================================
// 平台约束集
// ============================================

export function createPlatformConstraints(): Constraint[] {
  return [
    // 策略约束
    {
      id: 'strategy_name_required',
      name: '策略名称必填',
      description: '策略必须有非空名称',
      type: 'precondition',
      severity: 'error',
      condition: (ctx) => {
        const strategies = ctx.entities.get('strategies') || [];
        return strategies.every(s => s.name && s.name.trim().length > 0);
      },
      message: () => '策略名称不能为空',
      metadata: { category: 'strategy', tags: ['validation'], version: 1, author: 'system', enabled: true, weight: 10 }
    },

    {
      id: 'strategy_unique_name',
      name: '策略名称唯一',
      description: '同一用户的策略名称必须唯一',
      type: 'invariant',
      severity: 'error',
      condition: (ctx) => {
        const strategies = ctx.entities.get('strategies') || [];
        const names = strategies.map(s => `${s.author}:${s.name}`);
        return new Set(names).size === names.length;
      },
      message: () => '存在重复的策略名称',
      metadata: { category: 'strategy', tags: ['uniqueness'], version: 1, author: 'system', enabled: true, weight: 9 }
    },

    {
      id: 'strategy_status_transition',
      name: '状态转换规则',
      description: '策略状态必须按照合法路径转换',
      type: 'transition',
      severity: 'error',
      condition: (ctx) => {
        const validTransitions: Record<string, string[]> = {
          draft: ['testing', 'archived'],
          testing: ['running', 'draft', 'archived'],
          running: ['paused', 'archived'],
          paused: ['running', 'archived'],
          archived: ['draft']
        };

        const operations = ctx.history.filter(op => op.type === 'status_change');
        for (const op of operations.slice(-10)) {
          const from = op.before?.status;
          const to = op.after?.status;
          if (from && to && validTransitions[from] && !validTransitions[from].includes(to)) {
            return false;
          }
        }
        return true;
      },
      message: () => '策略状态转换不合法',
      metadata: { category: 'strategy', tags: ['state-machine'], version: 1, author: 'system', enabled: true, weight: 8 }
    },

    {
      id: 'running_strategy_limit',
      name: '运行策略数量限制',
      description: '最多同时运行 10 个策略',
      type: 'cardinality',
      severity: 'warning',
      condition: (ctx) => {
        const strategies = ctx.entities.get('strategies') || [];
        const running = strategies.filter(s => s.status === 'running').length;
        return running <= 10;
      },
      message: (ctx) => {
        const strategies = ctx.entities.get('strategies') || [];
        const running = strategies.filter(s => s.status === 'running').length;
        return `当前运行 ${running} 个策略，建议不超过 10 个`;
      },
      metadata: { category: 'strategy', tags: ['limit'], version: 1, author: 'system', enabled: true, weight: 5 }
    },

    // 胶囊约束
    {
      id: 'capsule_minimum',
      name: '核心胶囊必须在线',
      description: '市场胶囊和风控胶囊必须保持在线',
      type: 'invariant',
      severity: 'error',
      condition: (ctx) => {
        const capsules = ctx.entities.get('capsules') || [];
        const coreCapsules = ['market', 'risk'];
        return coreCapsules.every(id => {
          const capsule = capsules.find(c => c.id === id);
          return capsule && capsule.status === 'active';
        });
      },
      message: () => '核心胶囊 (市场/风控) 必须保持在线',
      metadata: { category: 'capsule', tags: ['core'], version: 1, author: 'system', enabled: true, weight: 10 }
    },

    {
      id: 'capsule_instance_max',
      name: '胶囊实例上限',
      description: '单个胶囊最多 100 个实例',
      type: 'cardinality',
      severity: 'warning',
      condition: (ctx) => {
        const capsules = ctx.entities.get('capsules') || [];
        return capsules.every(c => c.instanceCount <= 100);
      },
      message: (ctx) => {
        const capsules = ctx.entities.get('capsules') || [];
        const overLimit = capsules.filter(c => c.instanceCount > 100);
        return overLimit.length > 0
          ? `${overLimit.map(c => c.name).join(', ')} 实例数超过限制`
          : '';
      },
      metadata: { category: 'capsule', tags: ['limit'], version: 1, author: 'system', enabled: true, weight: 6 }
    },

    // 操作约束
    {
      id: 'operation_rate_limit',
      name: '操作频率限制',
      description: '同一操作每秒最多 10 次',
      type: 'property',
      severity: 'warning',
      condition: (ctx) => {
        const now = Date.now();
        const recentOps = ctx.history.filter(
          op => now - op.timestamp < 1000
        );
        const opCounts: Record<string, number> = {};
        for (const op of recentOps) {
          opCounts[op.type] = (opCounts[op.type] || 0) + 1;
        }
        return Object.values(opCounts).every(count => count <= 10);
      },
      message: () => '操作频率过高，请稍后再试',
      metadata: { category: 'operation', tags: ['rate-limit'], version: 1, author: 'system', enabled: true, weight: 7 }
    }
  ];
}

// ============================================
// 全局约束引擎实例
// ============================================

export const constraintEngine = new ConstraintEngine();
constraintEngine.registerBatch(createPlatformConstraints());

// ============================================
// React Hook
// ============================================

import React, { useState, useEffect, useCallback } from 'react';

export function useConstraints() {
  const [violations, setViolations] = useState<ConstraintViolation[]>([]);
  const [isValid, setIsValid] = useState(true);

  const validate = useCallback((context: ConstraintContext): ValidationResult => {
    const result = constraintEngine.validate(context);
    setViolations(result.violations);
    setIsValid(result.valid);
    return result;
  }, []);

  const preValidate = useCallback((context: ConstraintContext, operationType: string) => {
    const result = constraintEngine.preValidate(context, operationType);
    setViolations(result.violations);
    setIsValid(result.valid);
    return result;
  }, []);

  const postValidate = useCallback((context: ConstraintContext, operationType: string) => {
    const result = constraintEngine.postValidate(context, operationType);
    setViolations(result.violations);
    setIsValid(result.valid);
    return result;
  }, []);

  const getFixes = useCallback((context: ConstraintContext) => {
    return constraintEngine.getSuggestedFixes(context);
  }, []);

  return {
    violations,
    isValid,
    validate,
    preValidate,
    postValidate,
    getFixes,
    constraints: constraintEngine.getConstraints(),
    history: constraintEngine.getHistory()
  };
}
