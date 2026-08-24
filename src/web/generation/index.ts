/**
 * Copyright 2026 NEMT Lab
 *
 * 生成系统导出
 */

export {
  ConstraintEngine,
  constraintEngine,
  useConstraints,
  createPlatformConstraints
} from './constraints';

export type {
  Constraint,
  ConstraintType,
  ConstraintSeverity,
  ConstraintContext,
  ValidationResult,
  ConstraintViolation,
  FixSuggestion
} from './constraints';

export {
  DataGenerator,
  DataValidator,
  dataGenerator,
  dataValidator,
  generateStrategyData,
  validateData,
  StrategySchema
} from './dataGenerator';

export type {
  FieldType,
  FieldConstraint,
  DataSchema,
  GeneratedData,
  ValidationResult as DataValidationResult,
  ValidationError,
  ValidationWarning
} from './dataGenerator';

export {
  ComponentGenerator,
  TableGenerator,
  componentGenerator,
  tableGenerator
} from './componentGenerator';

export type {
  ComponentType,
  FieldConfig,
  FormConfig,
  TableColumn,
  TableConfig
} from './componentGenerator';

export {
  WorkflowEngine,
  workflowEngine
} from './workflowEngine';

export type {
  NodeType,
  NodeStatus,
  EdgeType,
  WorkflowNode,
  WorkflowEdge,
  WorkflowTrigger,
  WorkflowContext,
  Workflow
} from './workflowEngine';
