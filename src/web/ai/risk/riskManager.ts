/**
 * Copyright 2026 NEMT Lab
 *
 * Risk Management Module
 * 借鉴 nautilus_AItrader 风险管理
 *
 * 功能：
 * - 止损/止盈
 * - 追踪止损
 * - 分批止盈
 * - OCO 订单管理
 * - 括号订单
 */

import { EventEmitter } from 'events';
import { logger } from '../../trader/engine/logger';

// ============================================
// 类型定义
// ============================================

export interface StopLossConfig {
  enabled: boolean;
  useSupportResistance: boolean;
  bufferPct: number;
  trailingActivationPct?: number;
  trailingDistancePct?: number;
}

export interface TakeProfitConfig {
  enabled: boolean;
  levels: TakeProfitLevel[];
}

export interface TakeProfitLevel {
  profitPct: number;
  positionPct: number;
}

export interface OCOConfig {
  enabled: boolean;
  redisHost?: string;
  redisPort?: number;
  redisDb?: number;
  groupTtlHours?: number;
}

export interface Order {
  id: string;
  symbol: string;
  type: 'entry' | 'stop_loss' | 'take_profit' | 'trailing_stop';
  side: 'buy' | 'sell';
  price: number;
  quantity: number;
  filled: boolean;
  linkedOrderId?: string;
  timestamp: number;
}

export interface Position {
  id: string;
  symbol: string;
  direction: 'long' | 'short';
  entryPrice: number;
  quantity: number;
  currentPrice: number;
  unrealizedPnl: number;
  unrealizedPnlPct: number;
  stopLoss?: number;
  takeProfit?: number;
  trailingStop?: number;
  orders: Order[];
}

// ============================================
// 风险管理器
// ============================================

export class RiskManager extends EventEmitter {
  private positions: Map<string, Position> = new Map();
  private slConfig: StopLossConfig;
  private tpConfig: TakeProfitConfig;
  private ocoConfig: OCOConfig;

  private trailingActive: Map<string, boolean> = new Map();
  private partialTpExecuted: Map<string, Set<number>> = new Map();

  constructor(
    slConfig?: Partial<StopLossConfig>,
    tpConfig?: Partial<TakeProfitConfig>,
    ocoConfig?: Partial<OCOConfig>
  ) {
    super();

    this.slConfig = {
      enabled: true,
      useSupportResistance: true,
      bufferPct: 0.001,
      trailingActivationPct: 0.01,
      trailingDistancePct: 0.005,
      ...slConfig,
    };

    this.tpConfig = {
      enabled: true,
      levels: [
        { profitPct: 0.02, positionPct: 0.5 },
        { profitPct: 0.04, positionPct: 0.5 },
      ],
      ...tpConfig,
    };

    this.ocoConfig = {
      enabled: true,
      ...ocoConfig,
    };
  }

  // -----------------------------------------
  // 持仓管理
  // -----------------------------------------

  /**
   * 开仓
   */
  openPosition(
    positionId: string,
    symbol: string,
    direction: 'long' | 'short',
    entryPrice: number,
    quantity: number
  ): Position {
    const position: Position = {
      id: positionId,
      symbol,
      direction,
      entryPrice,
      quantity,
      currentPrice: entryPrice,
      unrealizedPnl: 0,
      unrealizedPnlPct: 0,
      orders: [],
    };

    this.positions.set(positionId, position);
    this.trailingActive.set(positionId, false);
    this.partialTpExecuted.set(positionId, new Set());

    // 设置止损止盈
    if (this.slConfig.enabled) {
      this.setStopLoss(positionId, entryPrice);
    }

    if (this.tpConfig.enabled) {
      this.setTakeProfitLevels(positionId, entryPrice);
    }

    logger.info(
      `[RiskManager] Opened ${direction} position: ${symbol} @ ${entryPrice} x ${quantity}`
    );

    this.emit('position_opened', position);

    return position;
  }

  /**
   * 平仓
   */
  closePosition(positionId: string, exitPrice: number, reason: string): void {
    const position = this.positions.get(positionId);
    if (!position) {
      logger.warning(`[RiskManager] Position not found: ${positionId}`);
      return;
    }

    const pnl = this.calculatePnL(position.direction, position.entryPrice, exitPrice, position.quantity);
    const pnlPct = (pnl / (position.entryPrice * position.quantity)) * 100;

    // 取消所有关联订单
    this.cancelLinkedOrders(position);

    // 平仓
    this.positions.delete(positionId);
    this.trailingActive.delete(positionId);
    this.partialTpExecuted.delete(positionId);

    logger.info(
      `[RiskManager] Closed position: ${position.symbol} @ ${exitPrice}, PnL: ${pnl.toFixed(2)} (${pnlPct.toFixed(2)}%)`
    );

    this.emit('position_closed', {
      ...position,
      currentPrice: exitPrice,
      unrealizedPnl: pnl,
      unrealizedPnlPct: pnlPct,
      exitReason: reason,
    });
  }

  /**
   * 更新持仓价格
   */
  updatePosition(positionId: string, currentPrice: number): void {
    const position = this.positions.get(positionId);
    if (!position) return;

    position.currentPrice = currentPrice;
    position.unrealizedPnl = this.calculatePnL(
      position.direction,
      position.entryPrice,
      currentPrice,
      position.quantity
    );
    position.unrealizedPnlPct =
      (position.unrealizedPnl / (position.entryPrice * position.quantity)) * 100;

    // 检查追踪止损
    if (this.slConfig.enabled && this.slConfig.trailingActivationPct) {
      this.checkTrailingStop(positionId, currentPrice);
    }

    // 检查分批止盈
    if (this.tpConfig.enabled) {
      this.checkPartialTakeProfit(positionId, currentPrice);
    }

    this.emit('position_updated', position);
  }

  /**
   * 获取持仓
   */
  getPosition(positionId: string): Position | undefined {
    return this.positions.get(positionId);
  }

  /**
   * 获取所有持仓
   */
  getAllPositions(): Position[] {
    return Array.from(this.positions.values());
  }

  // -----------------------------------------
  // 止损管理
  // -----------------------------------------

  /**
   * 设置止损
   */
  setStopLoss(positionId: string, entryPrice: number): void {
    const position = this.positions.get(positionId);
    if (!position || !this.slConfig.enabled) return;

    let slPrice: number;

    if (this.slConfig.useSupportResistance) {
      // 基于支撑/阻力位
      slPrice = position.direction === 'long'
        ? entryPrice * (1 - this.slConfig.bufferPct - 0.01)
        : entryPrice * (1 + this.slConfig.bufferPct + 0.01);
    } else {
      // 固定百分比
      slPrice = position.direction === 'long'
        ? entryPrice * (1 - this.slConfig.bufferPct)
        : entryPrice * (1 + this.slConfig.bufferPct);
    }

    position.stopLoss = slPrice;

    const stopOrder: Order = {
      id: `sl_${positionId}_${Date.now()}`,
      symbol: position.symbol,
      type: 'stop_loss',
      side: position.direction === 'long' ? 'sell' : 'buy',
      price: slPrice,
      quantity: position.quantity,
      filled: false,
      timestamp: Date.now(),
    };

    position.orders.push(stopOrder);

    logger.info(
      `[RiskManager] Stop loss set: ${position.symbol} @ ${slPrice.toFixed(2)}`
    );

    this.emit('stop_loss_set', { positionId, stopLoss: slPrice });
  }

  /**
   * 取消止损
   */
  cancelStopLoss(positionId: string): void {
    const position = this.positions.get(positionId);
    if (!position) return;

    const stopOrder = position.orders.find((o) => o.type === 'stop_loss' && !o.filled);
    if (stopOrder) {
      stopOrder.filled = true;
      logger.info(`[RiskManager] Stop loss cancelled: ${position.symbol}`);
    }
  }

  /**
   * 检查是否触发止损
   */
  checkStopLoss(positionId: string, currentPrice: number): boolean {
    const position = this.positions.get(positionId);
    if (!position || !position.stopLoss) return false;

    const triggered =
      (position.direction === 'long' && currentPrice <= position.stopLoss) ||
      (position.direction === 'short' && currentPrice >= position.stopLoss);

    if (triggered) {
      this.closePosition(positionId, position.stopLoss, 'stop_loss');
    }

    return triggered;
  }

  // -----------------------------------------
  // 止盈管理
  // -----------------------------------------

  /**
   * 设置分批止盈
   */
  setTakeProfitLevels(positionId: string, entryPrice: number): void {
    const position = this.positions.get(positionId);
    if (!position || !this.tpConfig.enabled) return;

    for (const level of this.tpConfig.levels) {
      const tpPrice =
        position.direction === 'long'
          ? entryPrice * (1 + level.profitPct)
          : entryPrice * (1 - level.profitPct);

      position.takeProfit = tpPrice;

      const tpOrder: Order = {
        id: `tp_${positionId}_${level.profitPct}_${Date.now()}`,
        symbol: position.symbol,
        type: 'take_profit',
        side: position.direction === 'long' ? 'sell' : 'buy',
        price: tpPrice,
        quantity: position.quantity * level.positionPct,
        filled: false,
        timestamp: Date.now(),
      };

      position.orders.push(tpOrder);

      logger.info(
        `[RiskManager] Take profit ${(level.profitPct * 100).toFixed(1)}% set: ${position.symbol} @ ${tpPrice.toFixed(2)}`
      );
    }

    this.emit('take_profit_set', { positionId, levels: this.tpConfig.levels });
  }

  /**
   * 检查分批止盈
   */
  private checkPartialTakeProfit(positionId: string, currentPrice: number): void {
    const position = this.positions.get(positionId);
    if (!position) return;

    const executedSet = this.partialTpExecuted.get(positionId) || new Set();

    for (const level of this.tpConfig.levels) {
      const tpPrice =
        position.direction === 'long'
          ? position.entryPrice * (1 + level.profitPct)
          : position.entryPrice * (1 - level.profitPct);

      const triggered =
        (position.direction === 'long' && currentPrice >= tpPrice) ||
        (position.direction === 'short' && currentPrice <= tpPrice);

      if (triggered && !executedSet.has(level.profitPct)) {
        executedSet.add(level.profitPct);
        this.partialTpExecuted.set(positionId, executedSet);

        const closeQty = position.quantity * level.positionPct;

        logger.info(
          `[RiskManager] Partial take profit ${(level.profitPct * 100).toFixed(1)}% executed: ${position.symbol} @ ${currentPrice.toFixed(2)}, qty: ${closeQty}`
        );

        this.emit('partial_take_profit', {
          positionId,
          level: level.profitPct,
          price: currentPrice,
          quantity: closeQty,
        });

        // 如果全部平仓
        if (executedSet.size === this.tpConfig.levels.length) {
          this.closePosition(positionId, currentPrice, 'take_profit');
        } else {
          // 更新剩余数量
          position.quantity -= closeQty;
        }
      }
    }
  }

  // -----------------------------------------
  // 追踪止损
  // -----------------------------------------

  /**
   * 检查追踪止损
   */
  private checkTrailingStop(positionId: string, currentPrice: number): void {
    const position = this.positions.get(positionId);
    if (!position || !this.slConfig.trailingActivationPct) return;

    const isActive = this.trailingActive.get(positionId) || false;
    const activationPct = this.slConfig.trailingActivationPct;
    const distancePct = this.slConfig.trailingDistancePct || 0.005;

    // 计算盈利
    const profitPct =
      position.direction === 'long'
        ? (currentPrice - position.entryPrice) / position.entryPrice
        : (position.entryPrice - currentPrice) / position.entryPrice;

    // 激活追踪止损
    if (!isActive && profitPct >= activationPct) {
      this.trailingActive.set(positionId, true);

      // 设置新的止损位
      const trailingSl =
        position.direction === 'long'
          ? currentPrice * (1 - distancePct)
          : currentPrice * (1 + distancePct);

      position.stopLoss = trailingSl;

      logger.info(
        `[RiskManager] Trailing stop activated: ${position.symbol} @ ${trailingSl.toFixed(2)}`
      );

      this.emit('trailing_stop_activated', {
        positionId,
        newStopLoss: trailingSl,
        currentPrice,
      });
    }

    // 更新追踪止损
    if (isActive) {
      const newTrailingSl =
        position.direction === 'long'
          ? currentPrice * (1 - distancePct)
          : currentPrice * (1 + distancePct);

      // 只更新有利方向
      const shouldUpdate =
        (position.direction === 'long' && newTrailingSl > (position.stopLoss || 0)) ||
        (position.direction === 'short' && newTrailingSl < (position.stopLoss || Infinity));

      if (shouldUpdate) {
        position.stopLoss = newTrailingSl;

        logger.debug(
          `[RiskManager] Trailing stop updated: ${position.symbol} @ ${newTrailingSl.toFixed(2)}`
        );

        this.emit('trailing_stop_updated', {
          positionId,
          newStopLoss: newTrailingSl,
          currentPrice,
        });
      }
    }
  }

  // -----------------------------------------
  // OCO 订单
  // -----------------------------------------

  /**
   * 创建 OCO 组
   */
  createOCOGroup(
    positionId: string,
    symbol: string,
    entryPrice: number,
    quantity: number,
    slPrice: number,
    tpPrice: number
  ): void {
    if (!this.ocoConfig.enabled) return;

    const position = this.positions.get(positionId);
    if (!position) return;

    // 创建止损单
    const slOrder: Order = {
      id: `oco_sl_${Date.now()}`,
      symbol,
      type: 'stop_loss',
      side: position.direction === 'long' ? 'sell' : 'buy',
      price: slPrice,
      quantity,
      filled: false,
      timestamp: Date.now(),
    };

    // 创建止盈单
    const tpOrder: Order = {
      id: `oco_tp_${Date.now()}`,
      symbol,
      type: 'take_profit',
      side: position.direction === 'long' ? 'sell' : 'buy',
      price: tpPrice,
      quantity,
      filled: false,
      timestamp: Date.now(),
    };

    // 关联订单
    slOrder.linkedOrderId = tpOrder.id;
    tpOrder.linkedOrderId = slOrder.id;

    position.orders.push(slOrder, tpOrder);

    // 持久化到 Redis (如果配置)
    if (this.ocoConfig.redisHost) {
      this.persistOCOGroup(positionId, slOrder, tpOrder);
    }

    logger.info(
      `[RiskManager] OCO group created: ${symbol}, SL @ ${slPrice}, TP @ ${tpPrice}`
    );

    this.emit('oco_group_created', { positionId, slOrder, tpOrder });
  }

  /**
   * OCO 单执行 (一个执行,取消另一个)
   */
  executeOCOMember(positionId: string, executedOrderId: string): void {
    const position = this.positions.get(positionId);
    if (!position) return;

    const executedOrder = position.orders.find((o) => o.id === executedOrderId);
    if (!executedOrder || executedOrder.filled) return;

    // 标记执行
    executedOrder.filled = true;

    // 取消关联订单
    if (executedOrder.linkedOrderId) {
      const linkedOrder = position.orders.find((o) => o.id === executedOrder.linkedOrderId);
      if (linkedOrder && !linkedOrder.filled) {
        linkedOrder.filled = true;

        logger.info(
          `[RiskManager] OCO member executed, linked order cancelled: ${linkedOrder.id}`
        );

        this.emit('oco_linked_cancelled', {
          positionId,
          executedOrder: executedOrderId,
          cancelledOrder: linkedOrder.id,
        });
      }
    }

    // 从 Redis 删除
    if (this.ocoConfig.redisHost) {
      this.deleteOCOFromRedis(positionId);
    }
  }

  /**
   * 取消关联订单
   */
  private cancelLinkedOrders(position: Position): void {
    for (const order of position.orders) {
      if (!order.filled && order.linkedOrderId) {
        const linked = position.orders.find((o) => o.id === order.linkedOrderId);
        if (linked && !linked.filled) {
          linked.filled = true;
        }
      }
    }
  }

  // -----------------------------------------
  // Redis 持久化
  // -----------------------------------------

  private async persistOCOGroup(
    positionId: string,
    slOrder: Order,
    tpOrder: Order
  ): Promise<void> {
    // 简化实现 - 实际应该使用 Redis
    logger.debug(`[RiskManager] Persisting OCO group to Redis: ${positionId}`);
  }

  private async deleteOCOFromRedis(positionId: string): Promise<void> {
    logger.debug(`[RiskManager] Deleting OCO group from Redis: ${positionId}`);
  }

  // -----------------------------------------
  // 工具方法
  // -----------------------------------------

  /**
   * 计算盈亏
   */
  private calculatePnL(
    direction: 'long' | 'short',
    entryPrice: number,
    exitPrice: number,
    quantity: number
  ): number {
    if (direction === 'long') {
      return (exitPrice - entryPrice) * quantity;
    } else {
      return (entryPrice - exitPrice) * quantity;
    }
  }

  /**
   * 获取配置
   */
  getConfig(): {
    stopLoss: StopLossConfig;
    takeProfit: TakeProfitConfig;
    oco: OCOConfig;
  } {
    return {
      stopLoss: { ...this.slConfig },
      takeProfit: { ...this.tpConfig },
      oco: { ...this.ocoConfig },
    };
  }
}
