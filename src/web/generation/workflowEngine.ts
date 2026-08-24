/**
 * Copyright 2026 NEMT Lab
 *
 * 工作流自动编排器 - 约束驱动的工作流
 *
 * 核心理念：工作流不是被设计的，而是从业务规则中推导出来的
 *
 * 工作流要素：
 * - Node: 工作节点 (执行单元)
 * - Edge: 连接边 (数据流)
 * - Trigger: 触发器 (启动条件)
 * - Context: 上下文 (数据共享)
 * - Policy: 策略 (执行规则)
 */

// ============================================
// 类型定义
// ============================================

export type NodeType =
  | 'task'       // 普通任务
  | 'condition'  // 条件分支
  | 'parallel'   // 并行执行
  | 'loop'       // 循环
  | 'subflow'    // 子流程
  | 'event'      // 事件监听
  | 'delay'      // 延迟
  | 'merge';     // 合并

export type NodeStatus = 'idle' | 'pending' | 'running' | 'completed' | 'failed' | 'skipped';
export type EdgeType = 'flow' | 'data' | 'condition';

export interface WorkflowNode {
  id: string;
  type: NodeType;
  name: string;
  description?: string;

  // 位置 (可视化)
  position: { x: number; y: number };

  // 配置
  config: Record<string, any>;

  // 输入输出
  inputs: Port[];
  outputs: Port[];

  // 状态
  status: NodeStatus;
  result?: any;
  error?: string;

  // 执行信息
  startTime?: number;
  endTime?: number;
  duration?: number;
}

export interface Port {
  id: string;
  name: string;
  type: string;
  required?: boolean;
}

export interface WorkflowEdge {
  id: string;
  source: string;  // 源节点 ID
  sourcePort: string;
  target: string;  // 目标节点 ID
  targetPort: string;
  type: EdgeType;

  // 条件 (用于条件边)
  condition?: string;

  // 数据映射
  mapping?: Record<string, string>;
}

export interface WorkflowTrigger {
  id: string;
  name: string;
  type: 'manual' | 'scheduled' | 'event' | 'api';

  // 配置
  config: {
    cron?: string;
    eventType?: string;
    endpoint?: string;
  };

  enabled: boolean;
}

export interface WorkflowContext {
  id: string;
  variables: Record<string, any>;
  data: Record<string, any>;
  metadata: {
    startedAt: number;
    startedBy?: string;
    executionId: string;
  };
}

export interface Workflow {
  id: string;
  name: string;
  description?: string;
  version: string;

  nodes: WorkflowNode[];
  edges: WorkflowEdge[];

  triggers: WorkflowTrigger[];

  // 元数据
  createdAt: number;
  updatedAt: number;
  status: 'draft' | 'active' | 'paused' | 'archived';
}

// ============================================
// 工作流引擎
// ============================================

export class WorkflowEngine {
  private workflows: Map<string, Workflow> = new Map();
  private runningExecutions: Map<string, WorkflowContext> = new Map();

  /**
   * 创建工作流
   */
  createWorkflow(workflow: Workflow): void {
    this.workflows.set(workflow.id, workflow);
  }

  /**
   * 获取工作流
   */
  getWorkflow(id: string): Workflow | undefined {
    return this.workflows.get(id);
  }

  /**
   * 执行工作流
   */
  async execute(workflowId: string, input?: Record<string, any>): Promise<WorkflowContext> {
    const workflow = this.workflows.get(workflowId);
    if (!workflow) {
      throw new Error(`Workflow ${workflowId} not found`);
    }

    // 创建执行上下文
    const context: WorkflowContext = {
      id: `exec_${Date.now()}_${Math.random().toString(36).substr(2, 6)}`,
      variables: {},
      data: input || {},
      metadata: {
        startedAt: Date.now(),
        executionId: `run_${Date.now()}`
      }
    };

    this.runningExecutions.set(context.id, context);

    // 找到起始节点
    const startNodes = workflow.nodes.filter(n => n.inputs.length === 0);

    // 执行
    for (const node of startNodes) {
      await this.executeNode(workflow, node, context);
    }

    return context;
  }

  /**
   * 执行节点
   */
  private async executeNode(
    workflow: Workflow,
    node: WorkflowNode,
    context: WorkflowContext
  ): Promise<void> {
    // 更新节点状态
    node.status = 'running';
    node.startTime = Date.now();

    try {
      // 根据节点类型执行
      switch (node.type) {
        case 'task':
          await this.executeTask(node, context);
          break;
        case 'condition':
          await this.executeCondition(workflow, node, context);
          return; // 条件节点特殊处理
        case 'parallel':
          await this.executeParallel(workflow, node, context);
          return;
        case 'loop':
          await this.executeLoop(workflow, node, context);
          return;
        case 'delay':
          await this.executeDelay(node, context);
          break;
        default:
          node.result = { status: 'skipped', reason: 'Unsupported node type' };
      }

      node.status = 'completed';
      node.endTime = Date.now();
      node.duration = node.endTime - (node.startTime || 0);

      // 执行后续节点
      await this.executeNextNodes(workflow, node, context);

    } catch (error) {
      node.status = 'failed';
      node.error = error instanceof Error ? error.message : String(error);
      node.endTime = Date.now();
      node.duration = node.endTime - (node.startTime || 0);
    }
  }

  /**
   * 执行任务节点
   */
  private async executeTask(node: WorkflowNode, context: WorkflowContext): Promise<void> {
    const { handler } = node.config;

    if (typeof handler === 'function') {
      node.result = await handler(context);
    } else {
      // 模拟任务执行
      node.result = {
        status: 'completed',
        output: `Task ${node.name} executed`
      };
    }
  }

  /**
   * 执行条件节点
   */
  private async executeCondition(
    workflow: Workflow,
    node: WorkflowNode,
    context: WorkflowContext
  ): Promise<void> {
    const { expression } = node.config;

    // 评估条件
    let shouldExecute = false;

    if (typeof expression === 'function') {
      shouldExecute = expression(context);
    } else if (typeof expression === 'string') {
      // 简单表达式解析
      try {
        const func = new Function('ctx', `with(ctx) { return ${expression}; }`);
        shouldExecute = func(context);
      } catch {
        shouldExecute = false;
      }
    }

    // 找到符合条件的分支
    const outgoingEdges = workflow.edges.filter(e => e.source === node.id);

    for (const edge of outgoingEdges) {
      const targetNode = workflow.nodes.find(n => n.id === edge.target);
      if (!targetNode) continue;

      // 检查条件是否匹配
      const conditionMatches = !edge.condition ||
        (shouldExecute && edge.condition === 'true') ||
        (!shouldExecute && edge.condition === 'false');

      if (conditionMatches) {
        await this.executeNode(workflow, targetNode, context);
      } else {
        targetNode.status = 'skipped';
      }
    }
  }

  /**
   * 执行并行节点
   */
  private async executeParallel(
    workflow: Workflow,
    node: WorkflowNode,
    context: WorkflowContext
  ): Promise<void> {
    const outgoingEdges = workflow.edges.filter(e => e.source === node.id);
    const parallelNodes = outgoingEdges
      .map(e => workflow.nodes.find(n => n.id === e.target))
      .filter(Boolean) as WorkflowNode[];

    // 并行执行所有分支
    await Promise.all(
      parallelNodes.map(n => this.executeNode(workflow, n, context))
    );
  }

  /**
   * 执行循环节点
   */
  private async executeLoop(
    workflow: Workflow,
    node: WorkflowNode,
    context: WorkflowContext
  ): Promise<void> {
    const { maxIterations = 10, condition } = node.config;

    let iterations = 0;
    let shouldContinue = true;

    while (shouldContinue && iterations < maxIterations) {
      iterations++;

      // 执行循环体
      const loopBody = workflow.nodes.find(n => n.id === node.id);
      const outgoingEdges = workflow.edges.filter(e => e.source === node.id);
      const bodyNodes = outgoingEdges
        .map(e => workflow.nodes.find(n => n.id === e.target))
        .filter(Boolean) as WorkflowNode[];

      for (const bodyNode of bodyNodes) {
        await this.executeNode(workflow, bodyNode, context);
      }

      // 检查循环条件
      if (typeof condition === 'function') {
        shouldContinue = condition(context, iterations);
      } else if (typeof condition === 'string') {
        try {
          const func = new Function('ctx', 'iter', `with(ctx) { return ${condition}; }`);
          shouldContinue = func(context, iterations);
        } catch {
          shouldContinue = false;
        }
      } else {
        shouldContinue = iterations < maxIterations;
      }
    }

    node.result = { iterations };
  }

  /**
   * 执行延迟节点
   */
  private async executeDelay(node: WorkflowNode, context: WorkflowContext): Promise<void> {
    const { duration } = node.config;

    if (typeof duration === 'number') {
      await new Promise(resolve => setTimeout(resolve, duration));
    }

    node.result = { delayed: duration };
  }

  /**
   * 执行后续节点
   */
  private async executeNextNodes(
    workflow: Workflow,
    currentNode: WorkflowNode,
    context: WorkflowContext
  ): Promise<void> {
    const outgoingEdges = workflow.edges.filter(e => e.source === currentNode.id);

    for (const edge of outgoingEdges) {
      // 数据映射
      if (edge.mapping) {
        for (const [targetKey, sourceKey] of Object.entries(edge.mapping)) {
          context.variables[targetKey] = context.variables[sourceKey] ||
            currentNode.result?.[sourceKey];
        }
      }

      const nextNode = workflow.nodes.find(n => n.id === edge.target);
      if (nextNode && nextNode.status === 'idle') {
        await this.executeNode(workflow, nextNode, context);
      }
    }
  }

  /**
   * 从模板创建工作流
   */
  createFromTemplate(
    name: string,
    template: 'simple' | 'approval' | 'pipeline' | 'state-machine'
  ): Workflow {
    const baseWorkflow: Workflow = {
      id: `wf_${Date.now()}`,
      name,
      version: '1.0.0',
      nodes: [],
      edges: [],
      triggers: [{
        id: `trigger_${Date.now()}`,
        name: 'Manual Trigger',
        type: 'manual',
        config: {},
        enabled: true
      }],
      createdAt: Date.now(),
      updatedAt: Date.now(),
      status: 'draft'
    };

    switch (template) {
      case 'simple':
        return this.createSimpleWorkflow(baseWorkflow);
      case 'approval':
        return this.createApprovalWorkflow(baseWorkflow);
      case 'pipeline':
        return this.createPipelineWorkflow(baseWorkflow);
      case 'state-machine':
        return this.createStateMachineWorkflow(baseWorkflow);
      default:
        return baseWorkflow;
    }
  }

  private createSimpleWorkflow(wf: Workflow): Workflow {
    wf.nodes = [
      {
        id: 'start',
        type: 'event',
        name: '开始',
        position: { x: 100, y: 100 },
        inputs: [],
        outputs: [{ id: 'out', name: 'next', type: 'flow' }],
        config: { event: 'start' },
        status: 'idle'
      },
      {
        id: 'process',
        type: 'task',
        name: '处理',
        position: { x: 300, y: 100 },
        inputs: [{ id: 'in', name: 'input', type: 'flow' }],
        outputs: [{ id: 'out', name: 'next', type: 'flow' }],
        config: { handler: async (ctx: WorkflowContext) => ({ processed: true }) },
        status: 'idle'
      },
      {
        id: 'end',
        type: 'task',
        name: '结束',
        position: { x: 500, y: 100 },
        inputs: [{ id: 'in', name: 'input', type: 'flow' }],
        outputs: [],
        config: { handler: async (ctx: WorkflowContext) => ({ completed: true }) },
        status: 'idle'
      }
    ];

    wf.edges = [
      { id: 'e1', source: 'start', sourcePort: 'out', target: 'process', targetPort: 'in', type: 'flow' },
      { id: 'e2', source: 'process', sourcePort: 'out', target: 'end', targetPort: 'in', type: 'flow' }
    ];

    return wf;
  }

  private createApprovalWorkflow(wf: Workflow): Workflow {
    wf.nodes = [
      {
        id: 'submit',
        type: 'task',
        name: '提交申请',
        position: { x: 100, y: 100 },
        inputs: [],
        outputs: [{ id: 'out', name: 'next', type: 'flow' }],
        config: {},
        status: 'idle'
      },
      {
        id: 'approve',
        type: 'condition',
        name: '审批',
        position: { x: 300, y: 100 },
        inputs: [{ id: 'in', name: 'input', type: 'flow' }],
        outputs: [
          { id: 'approve', name: '通过', type: 'flow' },
          { id: 'reject', name: '拒绝', type: 'flow' }
        ],
        config: { expression: (ctx: WorkflowContext) => ctx.variables.approved },
        status: 'idle'
      },
      {
        id: 'process-approved',
        type: 'task',
        name: '处理通过',
        position: { x: 500, y: 50 },
        inputs: [{ id: 'in', name: 'input', type: 'flow' }],
        outputs: [],
        config: {},
        status: 'idle'
      },
      {
        id: 'notify-reject',
        type: 'task',
        name: '通知拒绝',
        position: { x: 500, y: 150 },
        inputs: [{ id: 'in', name: 'input', type: 'flow' }],
        outputs: [],
        config: {},
        status: 'idle'
      }
    ];

    wf.edges = [
      { id: 'e1', source: 'submit', sourcePort: 'out', target: 'approve', targetPort: 'in', type: 'flow' },
      { id: 'e2', source: 'approve', sourcePort: 'approve', target: 'process-approved', targetPort: 'in', type: 'flow', condition: 'true' },
      { id: 'e3', source: 'approve', sourcePort: 'reject', target: 'notify-reject', targetPort: 'in', type: 'flow', condition: 'false' }
    ];

    return wf;
  }

  private createPipelineWorkflow(wf: Workflow): Workflow {
    const stages = ['获取数据', '清洗数据', '分析数据', '生成报告'];

    wf.nodes = stages.map((stage, i) => ({
      id: `stage_${i}`,
      type: 'task' as NodeType,
      name: stage,
      position: { x: 100 + i * 200, y: 100 },
      inputs: i === 0 ? [] : [{ id: 'in', name: 'input', type: 'flow' }],
      outputs: i === stages.length - 1 ? [] : [{ id: 'out', name: 'next', type: 'flow' }],
      config: {},
      status: 'idle' as NodeStatus
    }));

    wf.edges = wf.nodes.slice(0, -1).map((node, i) => ({
      id: `edge_${i}`,
      source: node.id,
      sourcePort: 'out',
      target: wf.nodes[i + 1].id,
      targetPort: 'in',
      type: 'flow' as EdgeType
    }));

    return wf;
  }

  private createStateMachineWorkflow(wf: Workflow): Workflow {
    const states = ['草稿', '审核中', '已发布', '已归档'];

    wf.nodes = states.map((state, i) => ({
      id: `state_${i}`,
      type: 'condition' as NodeType,
      name: state,
      position: { x: 100 + i * 150, y: 100 },
      inputs: i === 0 ? [] : [{ id: 'in', name: 'input', type: 'flow' }],
      outputs: [{ id: 'out', name: 'next', type: 'flow' }],
      config: { expression: () => true },
      status: 'idle' as NodeStatus
    }));

    return wf;
  }
}

// ============================================
// 全局实例
// ============================================

export const workflowEngine = new WorkflowEngine();

// 预设工作流
workflowEngine.createFromTemplate('简单流程', 'simple');
workflowEngine.createFromTemplate('审批流程', 'approval');
workflowEngine.createFromTemplate('数据管道', 'pipeline');
workflowEngine.createFromTemplate('状态机', 'state-machine');
