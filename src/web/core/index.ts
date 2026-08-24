/**
 * Copyright 2026 NEMT Lab
 *
 * 核心模块导出
 */

// ============================================
// 生成范式
// ============================================

export {
  // 生成引擎
  EntityRegistry,
  ValidatorEngine,
  GenerationEngine,
  globalRegistry,
  globalValidator,
  globalGenerator,
  useGeneration,

  // Schema 工具
  defineSchema,
  field,
  t
} from './generationParadigm';

// 类型
export type {
  Schema,
  FieldSchema,
  FieldType,
  Constraint,
  ValidationResult,
  ValidationError,
  ValidationWarning,
  Generator,
  GeneratedOutput,
  RegisteredEntity,
  GenerationContext
} from './generationParadigm';

// ============================================
// 实体注册
// ============================================

export {
  entityManager,
  useEntity,
  useEntities,
  EntityManager
} from './entityRegistry';

export type {
  EntityInstance
} from './entityRegistry';

// Schema 定义
export {
  StrategySchema,
  CapsuleSchema,
  SignalSchema,
  RiskRuleSchema,
  MetricSchema,
  WorkflowSchema
} from './entityRegistry';

// ============================================
// 验证管道
// ============================================

export {
  validationPipeline,
  BusinessValidators,
  useValidation,
  ValidationPipeline
} from './validationPipeline';

export type {
  ValidationRule,
  ValidationPipe
} from './validationPipeline';

// ============================================
// 文档生成
// ============================================

export {
  documentationGenerator,
  DocumentationViewer,
  SchemaTable,
  DocumentationGenerator
} from './documentationGenerator';

export type {
  Documentation,
  DocumentationSection,
  EntityDocumentation,
  FieldDocumentation,
  ApiDocumentation,
  SchemaDocumentation
} from './documentationGenerator';
