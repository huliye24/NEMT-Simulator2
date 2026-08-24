/**
 * Copyright 2026 NEMT Lab
 *
 * 系统演化引擎 - 自我的生成逻辑
 *
 * 核心理念：结构不是被渲染出来的，而是被系统自身的生成逻辑演化出来的
 *
 * 演化层次：
 * L1: 模式发现 - 观察行为，发现规律
 * L2: 规则提取 - 从规律中抽取可操作的规则
 * L3: 结构生成 - 基于规则递归生成新结构
 * L4: 自适应 - 基于反馈持续优化
 */

// ============================================
// 类型定义
// ============================================

/**
 * 观察事件 - 系统的感知输入
 */
export interface Observation {
  id: string;
  timestamp: number;
  type: 'action' | 'state' | 'metric' | 'pattern';
  source: string;           // 来源组件
  action?: string;         // 操作类型
  payload: Record<string, any>;  // 事件数据
  metadata?: {
    userId?: string;
    sessionId?: string;
    duration?: number;
  };
}

/**
 * 发现模式 - 观察的抽象
 */
export interface DiscoveredPattern {
  id: string;
  name: string;
  description: string;
  confidence: number;       // 置信度 0-1
  support: number;          // 支持度
  occurrences: number;      // 出现次数
  firstSeen: number;
  lastSeen: number;
  antecedents: string[];    // 前置条件
  consequents: string[];    // 结论
  metrics: {
    frequency: number;       // 频率
    avgDuration?: number;    // 平均持续时间
    successRate?: number;    // 成功率
  };
}

/**
 * 生成规则 - 模式的规则化
 */
export interface GenerationRule {
  id: string;
  name: string;
  patternId: string;        // 来源模式
  priority: number;         // 优先级
  condition: RuleCondition; // 触发条件
  action: RuleAction;       // 执行动作
  feedback: RuleFeedback;   // 反馈机制
  metadata: {
    createdAt: number;
    updatedAt: number;
    version: number;
    author: 'system' | 'user';
    enabled: boolean;
  };
}

export interface RuleCondition {
  type: 'always' | 'threshold' | 'pattern' | 'composite';
  expression?: string;       // 可执行表达式
  thresholds?: {
    metric: string;
    operator: '>' | '<' | '>=' | '<=' | '==';
    value: number;
  }[];
  patterns?: string[];      // 依赖的模式
  composite?: {
    operator: 'and' | 'or' | 'not';
    conditions: RuleCondition[];
  };
}

export interface RuleAction {
  type: 'generate' | 'transform' | 'adapt' | 'notify' | 'composite';
  target: string;           // 目标结构
  template?: string;         // 生成模板
  transformation?: {
    type: 'map' | 'filter' | 'aggregate' | 'reduce';
    params: Record<string, any>;
  };
  children?: RuleAction[];
}

export interface RuleFeedback {
  enabled: boolean;
  signals: ('positive' | 'negative' | 'neutral')[];
  adjustStrategy: 'increment' | 'decrement' | 'reset' | 'none';
  threshold: number;
}

/**
 * 生成的结构
 */
export interface GeneratedStructure {
  id: string;
  type: 'component' | 'layout' | 'workflow' | 'rule' | 'pattern';
  name: string;
  source: {
    ruleId: string;
    patternId: string;
  };
  content: any;              // 结构内容
  lineage: string[];        // 父结构 ID
  depth: number;             // 递归深度
  metadata: {
    createdAt: number;
    fitness: number;         // 适应度
    usageCount: number;
    lastUsed: number;
  };
}

/**
 * 演化状态
 */
export interface EvolutionState {
  phase: 'observing' | 'analyzing' | 'generating' | 'adapting' | 'idle';
  level: 1 | 2 | 3 | 4;
  observations: number;
  patterns: number;
  rules: number;
  structures: number;
  fitness: number;
}

// ============================================
// 模式发现器 (L1)
// ============================================

class PatternDiscoverer {
  private observations: Observation[] = [];
  private slidingWindow = 1000;  // 滑动窗口大小
  private minSupport = 3;        // 最小支持度
  private patterns: DiscoveredPattern[] = [];

  /**
   * 观察事件
   */
  observe(observation: Omit<Observation, 'id' | 'timestamp'>): void {
    const obs: Observation = {
      ...observation,
      id: `obs_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      timestamp: Date.now()
    };

    this.observations.push(obs);

    // 滑动窗口
    if (this.observations.length > this.slidingWindow) {
      this.observations = this.observations.slice(-this.slidingWindow);
    }

    // 触发模式发现
    this.discoverPatterns();
  }

  /**
   * 发现模式
   */
  private discoverPatterns(): void {
    // 序列模式发现
    this.findSequentialPatterns();

    // 频率模式发现
    this.findFrequencyPatterns();

    // 关联模式发现
    this.findAssociationRules();
  }

  /**
   * 发现序列模式
   */
  private findSequentialPatterns(): void {
    // 简化的序列模式发现
    const sequences: Map<string, { count: number; first: number; last: number }> = new Map();

    for (let i = 0; i < this.observations.length - 1; i++) {
      const current = this.observations[i];
      const next = this.observations[i + 1];

      const key = `${current.action || current.type}->${next.action || next.type}`;
      const existing = sequences.get(key);

      if (existing) {
        existing.count++;
        existing.last = next.timestamp;
      } else {
        sequences.set(key, {
          count: 1,
          first: current.timestamp,
          last: next.timestamp
        });
      }
    }

    // 生成模式
    sequences.forEach((data, key) => {
      if (data.count >= this.minSupport) {
        const [antecedent, consequent] = key.split('->');

        const pattern: DiscoveredPattern = {
          id: `pattern_seq_${key.replace(/[^a-zA-Z0-9]/g, '_')}`,
          name: `序列: ${antecedent} → ${consequent}`,
          description: `观察到 ${data.count} 次的序列模式`,
          confidence: Math.min(1, data.count / 10),
          support: data.count / this.observations.length,
          occurrences: data.count,
          firstSeen: data.first,
          lastSeen: data.last,
          antecedents: [antecedent],
          consequents: [consequent],
          metrics: {
            frequency: data.count / ((data.last - data.first) || 1) * 1000
          }
        };

        this.updatePattern(pattern);
      }
    });
  }

  /**
   * 发现频率模式
   */
  private findFrequencyPatterns(): void {
    const counts: Map<string, { count: number; totalDuration: number }> = new Map();

    this.observations.forEach(obs => {
      const key = obs.action || obs.type;
      const existing = counts.get(key);

      if (existing) {
        existing.count++;
        existing.totalDuration += obs.metadata?.duration || 0;
      } else {
        counts.set(key, { count: 1, totalDuration: obs.metadata?.duration || 0 });
      }
    });

    counts.forEach((data, key) => {
      if (data.count >= this.minSupport) {
        const pattern: DiscoveredPattern = {
          id: `pattern_freq_${key}`,
          name: `高频: ${key}`,
          description: `${key} 出现 ${data.count} 次`,
          confidence: Math.min(1, data.count / 20),
          support: data.count / this.observations.length,
          occurrences: data.count,
          firstSeen: this.observations[0]?.timestamp || Date.now(),
          lastSeen: this.observations[this.observations.length - 1]?.timestamp || Date.now(),
          antecedents: [],
          consequents: [key],
          metrics: {
            frequency: data.count,
            avgDuration: data.totalDuration / data.count
          }
        };

        this.updatePattern(pattern);
      }
    });
  }

  /**
   * 发现关联规则
   */
  private findAssociationRules(): void {
    // 简化的关联规则发现
    // 寻找经常一起出现的 action 和 state
  }

  /**
   * 更新模式
   */
  private updatePattern(pattern: DiscoveredPattern): void {
    const existingIndex = this.patterns.findIndex(p => p.id === pattern.id);

    if (existingIndex >= 0) {
      const existing = this.patterns[existingIndex];
      pattern.confidence = (existing.confidence + pattern.confidence) / 2;
      pattern.occurrences += existing.occurrences;
      pattern.lastSeen = Math.max(existing.lastSeen, pattern.lastSeen);
      this.patterns[existingIndex] = pattern;
    } else {
      this.patterns.push(pattern);
    }

    // 限制模式数量
    if (this.patterns.length > 100) {
      this.patterns.sort((a, b) => b.confidence - a.confidence);
      this.patterns = this.patterns.slice(0, 100);
    }
  }

  /**
   * 获取高置信度模式
   */
  getHighConfidencePatterns(threshold = 0.6): DiscoveredPattern[] {
    return this.patterns
      .filter(p => p.confidence >= threshold)
      .sort((a, b) => b.confidence - a.confidence);
  }

  /**
   * 获取所有模式
   */
  getPatterns(): DiscoveredPattern[] {
    return [...this.patterns];
  }

  /**
   * 获取观察历史
   */
  getObservations(): Observation[] {
    return [...this.observations];
  }

  /**
   * 清除历史
   */
  clear(): void {
    this.observations = [];
    this.patterns = [];
  }
}

// ============================================
// 规则引擎 (L2)
// ============================================

class RuleEngine {
  private rules: Map<string, GenerationRule> = new Map();
  private ruleHistory: { ruleId: string; executedAt: number; success: boolean }[] = [];

  /**
   * 注册规则
   */
  registerRule(rule: GenerationRule): void {
    this.rules.set(rule.id, rule);
    console.log(`[RuleEngine] Registered rule: ${rule.name}`);
  }

  /**
   * 从模式生成规则
   */
  generateRuleFromPattern(pattern: DiscoveredPattern): GenerationRule | null {
    if (pattern.confidence < 0.5 || pattern.occurrences < 3) {
      return null;
    }

    const rule: GenerationRule = {
      id: `rule_${pattern.id}`,
      name: `规则: ${pattern.name}`,
      patternId: pattern.id,
      priority: pattern.confidence * pattern.occurrences,
      condition: {
        type: pattern.antecedents.length > 0 ? 'pattern' : 'always',
        patterns: pattern.antecedents.length > 0 ? pattern.antecedents : undefined
      },
      action: {
        type: 'generate',
        target: pattern.consequents[0] || 'unknown',
        template: `基于 ${pattern.name} 模式生成`
      },
      feedback: {
        enabled: true,
        signals: ['positive', 'negative'],
        adjustStrategy: 'increment',
        threshold: 0.3
      },
      metadata: {
        createdAt: Date.now(),
        updatedAt: Date.now(),
        version: 1,
        author: 'system',
        enabled: true
      }
    };

    return rule;
  }

  /**
   * 评估条件
   */
  evaluateCondition(condition: RuleCondition, context: Record<string, any>): boolean {
    switch (condition.type) {
      case 'always':
        return true;

      case 'threshold':
        if (!condition.thresholds) return false;
        return condition.thresholds.every(t => {
          const value = context[t.metric];
          switch (t.operator) {
            case '>': return value > t.value;
            case '<': return value < t.value;
            case '>=': return value >= t.value;
            case '<=': return value <= t.value;
            case '==': return value === t.value;
            default: return false;
          }
        });

      case 'pattern':
        return condition.patterns?.every(p => context[p]) || false;

      case 'composite':
        if (!condition.composite) return false;
        const results = condition.composite.conditions.map(c => this.evaluateCondition(c, context));
        switch (condition.composite.operator) {
          case 'and': return results.every(Boolean);
          case 'or': return results.some(Boolean);
          case 'not': return !results[0];
          default: return false;
        }

      default:
        return false;
    }
  }

  /**
   * 执行规则
   */
  execute(rules: GenerationRule[], context: Record<string, any>): GenerationRule | null {
    const enabledRules = rules
      .filter(r => r.metadata.enabled)
      .sort((a, b) => b.priority - a.priority);

    for (const rule of enabledRules) {
      if (this.evaluateCondition(rule.condition, context)) {
        this.ruleHistory.push({
          ruleId: rule.id,
          executedAt: Date.now(),
          success: true
        });

        console.log(`[RuleEngine] Executed rule: ${rule.name}`);
        return rule;
      }
    }

    return null;
  }

  /**
   * 提供反馈
   */
  provideFeedback(ruleId: string, signal: 'positive' | 'negative' | 'neutral'): void {
    const rule = this.rules.get(ruleId);
    if (!rule || !rule.feedback.enabled) return;

    const history = this.ruleHistory.filter(h => h.ruleId === ruleId);
    const recentHistory = history.slice(-10);

    const positiveCount = recentHistory.filter(h => h.success).length;
    const score = positiveCount / Math.max(recentHistory.length, 1);

    switch (rule.feedback.adjustStrategy) {
      case 'increment':
        rule.priority = Math.min(100, rule.priority * (1 + score * 0.1));
        break;
      case 'decrement':
        rule.priority = Math.max(1, rule.priority * (1 - score * 0.1));
        break;
      case 'reset':
        if (score < rule.feedback.threshold) {
          rule.priority = rule.priority * 0.5;
        }
        break;
    }

    rule.metadata.updatedAt = Date.now();
    rule.metadata.version++;
  }

  /**
   * 获取所有规则
   */
  getRules(): GenerationRule[] {
    return Array.from(this.rules.values());
  }

  /**
   * 获取启用的规则
   */
  getEnabledRules(): GenerationRule[] {
    return this.getRules().filter(r => r.metadata.enabled);
  }
}

// ============================================
// 结构生成器 (L3)
// ============================================

class StructureGenerator {
  private structures: GeneratedStructure[] = [];
  private templates: Map<string, any> = new Map();
  private maxDepth = 5;
  private maxStructures = 50;

  constructor() {
    this.registerDefaultTemplates();
  }

  /**
   * 注册默认模板
   */
  private registerDefaultTemplates(): void {
    // 组件模板
    this.templates.set('component', {
      type: 'component',
      structure: {
        name: '',
        props: {},
        state: {},
        lifecycle: ['mount', 'update', 'unmount']
      }
    });

    // 布局模板
    this.templates.set('layout', {
      type: 'layout',
      structure: {
        direction: 'vertical',
        gap: 16,
        items: []
      }
    });

    // 工作流模板
    this.templates.set('workflow', {
      type: 'workflow',
      structure: {
        steps: [],
        connections: [],
        triggers: []
      }
    });
  }

  /**
   * 生成结构
   */
  generate(
    rule: GenerationRule,
    pattern: DiscoveredPattern,
    parentStructure?: GeneratedStructure
  ): GeneratedStructure | null {
    // 检查深度限制
    if (parentStructure && parentStructure.depth >= this.maxDepth) {
      console.log('[StructureGenerator] Max depth reached');
      return null;
    }

    // 检查数量限制
    if (this.structures.length >= this.maxStructures) {
      // 移除最低适应度结构
      this.structures.sort((a, b) => b.metadata.fitness - a.metadata.fitness);
      this.structures = this.structures.slice(0, this.maxStructures / 2);
    }

    const template = this.templates.get(rule.action.target) || this.generateCustomTemplate(rule);

    const structure: GeneratedStructure = {
      id: `struct_${Date.now()}_${Math.random().toString(36).substr(2, 6)}`,
      type: rule.action.target as any,
      name: `${pattern.name} 生成的 ${rule.action.target}`,
      source: {
        ruleId: rule.id,
        patternId: pattern.id
      },
      content: this.fillTemplate(template, pattern, rule),
      lineage: parentStructure ? [...parentStructure.lineage, parentStructure.id] : [],
      depth: parentStructure ? parentStructure.depth + 1 : 0,
      metadata: {
        createdAt: Date.now(),
        fitness: pattern.confidence * rule.priority / 100,
        usageCount: 0,
        lastUsed: Date.now()
      }
    };

    this.structures.push(structure);
    console.log(`[StructureGenerator] Generated: ${structure.name} (depth: ${structure.depth})`);

    return structure;
  }

  /**
   * 生成自定义模板
   */
  private generateCustomTemplate(rule: GenerationRule): any {
    return {
      type: rule.action.target,
      structure: rule.action.template ? JSON.parse(rule.action.template) : {}
    };
  }

  /**
   * 填充模板
   */
  private fillTemplate(template: any, pattern: DiscoveredPattern, rule: GenerationRule): any {
    const context = {
      pattern,
      rule,
      timestamp: Date.now(),
      random: Math.random().toString(36).substr(2, 6)
    };

    // 深度拷贝模板
    const filled = JSON.parse(JSON.stringify(template));

    // 替换占位符
    const jsonStr = JSON.stringify(filled);
    const replaced = jsonStr.replace(
      /\$\{([^}]+)\}/g,
      (_, path) => {
        const keys = path.split('.');
        let value: any = context;
        for (const key of keys) {
          value = value?.[key];
        }
        return value?.toString() || path;
      }
    );

    return JSON.parse(replaced);
  }

  /**
   * 评估适应度
   */
  evaluateFitness(structureId: string, metrics: { usage: number; success: number; time: number }): void {
    const structure = this.structures.find(s => s.id === structureId);
    if (!structure) return;

    const { usage, success, time } = metrics;

    // 适应度 = 使用频率 * 成功率 * 时间效率
    const fitness = (usage * 0.3 + success * 0.5 + (1 / Math.max(time, 1)) * 0.2);

    structure.metadata.fitness = (structure.metadata.fitness + fitness) / 2;
    structure.metadata.usageCount += usage;
    structure.metadata.lastUsed = Date.now();
  }

  /**
   * 获取高适应度结构
   */
  getHighFitnessStructures(threshold = 0.5): GeneratedStructure[] {
    return this.structures
      .filter(s => s.metadata.fitness >= threshold)
      .sort((a, b) => b.metadata.fitness - a.metadata.fitness);
  }

  /**
   * 获取结构树
   */
  getStructureTree(): GeneratedStructure | null {
    // 找到根结构 (没有父结构)
    const roots = this.structures.filter(s => s.lineage.length === 0);
    if (roots.length === 0) return null;

    // 返回最新的根结构
    return roots.sort((a, b) => b.metadata.createdAt - a.metadata.createdAt)[0];
  }

  /**
   * 获取所有结构
   */
  getStructures(): GeneratedStructure[] {
    return [...this.structures];
  }
}

// ============================================
// 演化引擎 (L4 - 主控制器)
// ============================================

export class EvolutionEngine {
  private discoverer: PatternDiscoverer;
  private ruleEngine: RuleEngine;
  private generator: StructureGenerator;
  private state: EvolutionState;
  private tickInterval: number | null = null;
  private observers: Set<(state: EvolutionState) => void> = new Set();

  constructor() {
    this.discoverer = new PatternDiscoverer();
    this.ruleEngine = new RuleEngine();
    this.generator = new StructureGenerator();
    this.state = this.getDefaultState();

    // 监听模式发现，自动生成规则
    this.autoGenerateRules();
  }

  private getDefaultState(): EvolutionState {
    return {
      phase: 'idle',
      level: 1,
      observations: 0,
      patterns: 0,
      rules: 0,
      structures: 0,
      fitness: 0
    };
  }

  /**
   * 观察事件
   */
  observe(observation: Omit<Observation, 'id' | 'timestamp'>): void {
    this.discoverer.observe(observation);
    this.updateState();
  }

  /**
   * 自动生成规则
   */
  private autoGenerateRules(): void {
    const patterns = this.discoverer.getHighConfidencePatterns(0.6);

    patterns.forEach(pattern => {
      const existingRules = this.ruleEngine.getRules();
      if (existingRules.some(r => r.patternId === pattern.id)) return;

      const rule = this.ruleEngine.generateRuleFromPattern(pattern);
      if (rule) {
        this.ruleEngine.registerRule(rule);
      }
    });

    this.updateState();
  }

  /**
   * 演化一步
   */
  evolve(context: Record<string, any> = {}): GeneratedStructure | null {
    this.state.phase = 'generating';
    this.notifyObservers();

    const rules = this.ruleEngine.getEnabledRules();
    const patterns = this.discoverer.getHighConfidencePatterns();

    if (patterns.length === 0 || rules.length === 0) {
      this.state.phase = 'idle';
      this.updateState();
      return null;
    }

    // 选择最佳规则
    const rule = this.ruleEngine.execute(rules, context);
    if (!rule) {
      this.state.phase = 'idle';
      this.updateState();
      return null;
    }

    // 找到对应模式
    const pattern = patterns.find(p => p.id === rule.patternId);
    if (!pattern) {
      this.state.phase = 'idle';
      this.updateState();
      return null;
    }

    // 生成结构
    const structure = this.generator.generate(rule, pattern);

    this.state.phase = 'adapting';
    this.updateState();

    // 模拟适应度评估
    setTimeout(() => {
      this.generator.evaluateFitness(structure?.id || '', {
        usage: Math.floor(Math.random() * 10),
        success: Math.random(),
        time: Math.random() * 1000
      });
      this.state.phase = 'idle';
      this.updateState();
    }, 100);

    return structure;
  }

  /**
   * 启动演化循环
   */
  start(intervalMs = 5000): void {
    if (this.tickInterval) return;

    this.state.phase = 'observing';
    this.notifyObservers();

    this.tickInterval = window.setInterval(() => {
      this.evolve();
    }, intervalMs);

    console.log('[EvolutionEngine] Started');
  }

  /**
   * 停止演化
   */
  stop(): void {
    if (this.tickInterval) {
      clearInterval(this.tickInterval);
      this.tickInterval = null;
    }

    this.state.phase = 'idle';
    this.notifyObservers();
    console.log('[EvolutionEngine] Stopped');
  }

  /**
   * 重置
   */
  reset(): void {
    this.stop();
    this.discoverer.clear();
    this.state = this.getDefaultState();
    this.notifyObservers();
    console.log('[EvolutionEngine] Reset');
  }

  /**
   * 获取状态
   */
  getState(): EvolutionState {
    return { ...this.state };
  }

  /**
   * 获取摘要
   */
  getSummary(): {
    observations: number;
    patterns: DiscoveredPattern[];
    rules: GenerationRule[];
    structures: GeneratedStructure[];
    topStructure: GeneratedStructure | null;
  } {
    return {
      observations: this.discoverer.getObservations().length,
      patterns: this.discoverer.getPatterns(),
      rules: this.ruleEngine.getRules(),
      structures: this.generator.getStructures(),
      topStructure: this.generator.getStructureTree()
    };
  }

  /**
   * 订阅状态变化
   */
  subscribe(observer: (state: EvolutionState) => void): () => void {
    this.observers.add(observer);
    return () => this.observers.delete(observer);
  }

  private notifyObservers(): void {
    this.observers.forEach(o => o(this.getState()));
  }

  private updateState(): void {
    const summary = this.getSummary();
    this.state = {
      ...this.state,
      observations: summary.observations,
      patterns: summary.patterns.length,
      rules: summary.rules.length,
      structures: summary.structures.length,
      fitness: summary.structures.reduce((sum, s) => sum + s.metadata.fitness, 0) / Math.max(summary.structures.length, 1)
    };
    this.notifyObservers();
  }
}

// ============================================
// 全局演化引擎实例
// ============================================

export const evolutionEngine = new EvolutionEngine();

// ============================================
// React Hook
// ============================================

import React, { useState, useEffect } from 'react';

export function useEvolution() {
  const [state, setState] = useState<EvolutionState>(evolutionEngine.getState());
  const [summary, setSummary] = useState(evolutionEngine.getSummary());

  useEffect(() => {
    const unsubscribe = evolutionEngine.subscribe(setState);
    return unsubscribe;
  }, []);

  useEffect(() => {
    const interval = setInterval(() => {
      setSummary(evolutionEngine.getSummary());
    }, 1000);
    return () => clearInterval(interval);
  }, []);

  return {
    state,
    summary,
    observe: evolutionEngine.observe.bind(evolutionEngine),
    evolve: evolutionEngine.evolve.bind(evolutionEngine),
    start: evolutionEngine.start.bind(evolutionEngine),
    stop: evolutionEngine.stop.bind(evolutionEngine),
    reset: evolutionEngine.reset.bind(evolutionEngine)
  };
}
