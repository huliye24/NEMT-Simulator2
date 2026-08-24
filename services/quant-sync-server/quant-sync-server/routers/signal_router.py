#!/usr/bin/env python3
# Copyright 2026 NEMT Lab
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
信号路由器 - 交易信号的逻辑分发
===================================
负责将算法生成的交易信号分发到不同的目标

核心功能:
1. 信号验证与过滤
2. 信号分发 (Notion, Redis, Go Server)
3. 信号状态追踪
4. 冷却期管理

使用方式:
    from routers.signal_router import SignalRouter
    router = SignalRouter()
    router.send_signal(signal)
"""

import os
import json
import logging
import time
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from ..config import config

logger = logging.getLogger(__name__)


# ============================================================================
# 信号类型枚举
# ============================================================================
class SignalType(Enum):
    """信号类型"""
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"
    CLOSE = "close"  # 平仓


class SignalSource(Enum):
    """信号来源"""
    NEMT = "nemt"           # NEMT 理论分析
    RSI = "rsi"             # RSI 指标
    MACD = "macd"           # MACD 指标
    MA_CROSS = "ma_cross"   # 均线交叉
    BOLLINGER = "bollinger"  # 布林带
    COMPOSITE = "composite"  # 复合信号


@dataclass
class TradingSignal:
    """
    交易信号 - 算法 → 执行层的核心载体
    ===================================
    """
    # 基础信息
    signal_id: str = field(default_factory=lambda: f"{int(time.time()*1000)}")
    symbol: str = "BTCUSDT"
    action: SignalType = SignalType.HOLD

    # 价格信息
    price: float = 0.0
    stop_loss: float = 0.0
    take_profit: float = 0.0

    # 数量/金额
    quantity: float = 0.0
    amount: float = 0.0  # 合约价值

    # 信号质量
    confidence: float = 0.0  # 0-1
    source: SignalSource = SignalSource.COMPOSITE

    # 关联指标
    indicators: Dict[str, float] = field(default_factory=dict)

    # NEMT 关联
    nemt_spectral_width: float = 0.0
    nemt_mean_frequency: float = 0.0
    nemt_resonance_peaks: int = 0

    # 时间戳
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    created_at: float = field(default_factory=lambda: time.time())

    def to_dict(self) -> Dict[str, Any]:
        return {
            'signal_id': self.signal_id,
            'symbol': self.symbol,
            'action': self.action.value,
            'price': self.price,
            'stop_loss': self.stop_loss,
            'take_profit': self.take_profit,
            'quantity': self.quantity,
            'amount': self.amount,
            'confidence': self.confidence,
            'source': self.source.value,
            'indicators': self.indicators,
            'nemt': {
                'spectral_width': self.nemt_spectral_width,
                'mean_frequency': self.nemt_mean_frequency,
                'resonance_peaks': self.nemt_resonance_peaks,
            },
            'timestamp': self.timestamp,
        }

    def to_go_format(self) -> Dict[str, Any]:
        """转换为 Go 服务器格式"""
        return {
            'signal_id': self.signal_id,
            'symbol': self.symbol,
            'side': self.action.value.upper(),
            'price': self.price,
            'stop_loss': self.stop_loss,
            'take_profit': self.take_profit,
            'quantity': self.quantity,
            'amount': self.amount,
            'confidence': self.confidence,
            'source': self.source.value,
            'indicators': self.indicators,
            'nemt': {
                'spectral_width': self.nemt_spectral_width,
                'mean_frequency': self.nemt_mean_frequency,
                'resonance_peaks': self.nemt_resonance_peaks,
            },
            'timestamp': self.timestamp,
        }

    def to_notion_format(self) -> Dict[str, Any]:
        """转换为 Notion 格式"""
        return {
            'Name': {'title': [{'text': {'content': f"{self.symbol} {self.action.value.upper()}"}}]},
            'Symbol': {'select': {'name': self.symbol}},
            'Action': {'select': {'name': self.action.value.capitalize()}},
            'Price': {'number': self.price},
            'Confidence': {'number': round(self.confidence * 100, 1)},
            'Source': {'select': {'name': self.source.value}},
        }


# ============================================================================
# 信号路由器
# ============================================================================
class SignalRouter:
    """
    信号路由器 - 协议转换的路由层
    ===================================

    核心职责:
    1. 验证信号有效性
    2. 管理信号冷却期
    3. 分发信号到多个目标

    使用流程:
    1. 初始化: router = SignalRouter()
    2. 配置目标: router.add_target('redis', redis_target)
    3. 发送信号: router.send(signal)
    """

    def __init__(self):
        # 目标配置
        self._targets: Dict[str, Any] = {}

        # 信号追踪
        self._signal_history: List[TradingSignal] = []
        self._last_signal_time: Dict[str, float] = {}  # symbol -> timestamp
        self._cooldown: float = 60.0  # 默认冷却期 60 秒

        # 回调函数
        self._callbacks: Dict[str, List[Callable]] = {}

        # 初始化默认目标
        self._init_default_targets()

    def _init_default_targets(self):
        """初始化默认目标"""
        # Redis 目标
        try:
            import redis
            redis_client = redis.Redis(
                host=config.redis.host,
                port=config.redis.port,
                decode_responses=True
            )
            redis_client.ping()
            self._targets['redis'] = redis_client
            logger.info(f"✅ Redis 信号目标已配置: {config.redis.host}:{config.redis.port}")
        except Exception as e:
            logger.warning(f"⚠️  Redis 连接失败: {e}")

        # HTTP 目标 (Go Server)
        if config.go_server.http_url:
            self._targets['http'] = config.go_server.http_url
            logger.info(f"✅ HTTP 信号目标已配置: {config.go_server.http_url}")

    # ------------------------------------------------------------------------
    # 目标管理
    # ------------------------------------------------------------------------
    def add_target(self, name: str, target: Any):
        """
        添加信号目标

        Args:
            name: 目标名称 ('redis', 'http', 'notion')
            target: 目标对象
        """
        self._targets[name] = target
        logger.info(f"➕ 信号目标已添加: {name}")

    def remove_target(self, name: str):
        """移除信号目标"""
        if name in self._targets:
            del self._targets[name]
            logger.info(f"➖ 信号目标已移除: {name}")

    def set_cooldown(self, seconds: float):
        """设置冷却期 (秒)"""
        self._cooldown = seconds
        logger.info(f"⏱️  信号冷却期设置为: {seconds}s")

    # ------------------------------------------------------------------------
    # 信号处理
    # ------------------------------------------------------------------------
    def validate_signal(self, signal: TradingSignal) -> tuple[bool, str]:
        """
        验证信号有效性

        Returns:
            (是否有效, 错误信息)
        """
        if signal.action == SignalType.HOLD:
            return True, ""  # HOLD 信号总是有效

        if signal.price <= 0:
            return False, "价格必须大于 0"

        if signal.confidence < 0:
            signal.confidence = 0
        elif signal.confidence > 1:
            signal.confidence = 1

        if signal.confidence < 0.3:
            return False, f"信号置信度过低: {signal.confidence:.2%}"

        if signal.quantity <= 0 and signal.amount <= 0:
            return False, "必须指定数量或金额"

        return True, ""

    def check_cooldown(self, symbol: str) -> bool:
        """
        检查冷却期

        Returns:
            True 表示可以发送信号，False 表示在冷却期内
        """
        if symbol not in self._last_signal_time:
            return True

        elapsed = time.time() - self._last_signal_time[symbol]
        return elapsed >= self._cooldown

    def should_send(self, signal: TradingSignal) -> bool:
        """
        判断是否应该发送信号

        考虑因素:
        1. 信号类型 (HOLD 信号通常不发送)
        2. 冷却期
        3. 置信度阈值
        """
        # HOLD 信号不发送
        if signal.action == SignalType.HOLD:
            return False

        # 检查冷却期
        if not self.check_cooldown(signal.symbol):
            logger.info(f"⏳ {signal.symbol} 在冷却期内，跳过")
            return False

        # 检查置信度
        if signal.confidence < 0.5:
            logger.info(f"⚠️  {signal.symbol} 置信度 {signal.confidence:.2%} 低于阈值")
            return False

        return True

    # ------------------------------------------------------------------------
    # 信号发送
    # ------------------------------------------------------------------------
    def send(self, signal: TradingSignal,
             targets: List[str] = None) -> Dict[str, bool]:
        """
        发送信号到指定目标

        Args:
            signal: 交易信号
            targets: 目标列表 (None = 所有目标)

        Returns:
            各目标的发送结果
        """
        results = {}

        # 默认目标
        if targets is None:
            targets = list(self._targets.keys())

        # 发送到每个目标
        for target_name in targets:
            if target_name not in self._targets:
                logger.warning(f"⚠️  未知目标: {target_name}")
                results[target_name] = False
                continue

            try:
                success = self._send_to_target(target_name, signal)
                results[target_name] = success
            except Exception as e:
                logger.error(f"❌ 发送信号到 {target_name} 失败: {e}")
                results[target_name] = False

        # 更新追踪
        if any(results.values()):  # 至少有一个成功
            self._update_tracking(signal)

        return results

    def _send_to_target(self, target_name: str, signal: TradingSignal) -> bool:
        """发送到单个目标"""
        target = self._targets[target_name]

        if target_name == 'redis':
            return self._send_to_redis(target, signal)
        elif target_name == 'http':
            return self._send_to_http(target, signal)
        elif target_name == 'notion':
            return self._send_to_notion(target, signal)
        else:
            logger.warning(f"未知目标类型: {target_name}")
            return False

    def _send_to_redis(self, redis_client, signal: TradingSignal) -> bool:
        """发送到 Redis"""
        try:
            stream_key = f"signals:{signal.symbol.lower()}"

            data = {
                'signal_id': signal.signal_id,
                'action': signal.action.value,
                'price': str(signal.price),
                'confidence': str(signal.confidence),
                'source': signal.source.value,
                'indicators': json.dumps(signal.indicators),
                'nemt_sw': str(signal.nemt_spectral_width),
                'nemt_mf': str(signal.nemt_mean_frequency),
                'timestamp': signal.timestamp,
            }

            redis_client.xadd(stream_key, data, maxlen=1000)
            logger.info(f"📤 信号已发送到 Redis: {stream_key}")
            return True

        except Exception as e:
            logger.error(f"Redis 发送失败: {e}")
            return False

    def _send_to_http(self, http_url: str, signal: TradingSignal) -> bool:
        """发送到 HTTP 服务器 (Go Server)"""
        try:
            import requests

            payload = signal.to_go_format()
            response = requests.post(
                f"{http_url}/api/signals",
                json=payload,
                timeout=5
            )

            if response.status_code == 200:
                logger.info(f"📤 信号已发送到 HTTP: {http_url}")
                return True
            else:
                logger.warning(f"HTTP 响应异常: {response.status_code}")
                return False

        except Exception as e:
            logger.error(f"HTTP 发送失败: {e}")
            return False

    def _send_to_notion(self, notion_adapter, signal: TradingSignal) -> bool:
        """发送到 Notion"""
        try:
            return notion_adapter.write_signal(signal)
        except Exception as e:
            logger.error(f"Notion 发送失败: {e}")
            return False

    # ------------------------------------------------------------------------
    # 追踪与回调
    # ------------------------------------------------------------------------
    def _update_tracking(self, signal: TradingSignal):
        """更新追踪状态"""
        # 更新时间戳
        self._last_signal_time[signal.symbol] = time.time()

        # 添加到历史
        self._signal_history.append(signal)

        # 限制历史长度
        if len(self._signal_history) > 1000:
            self._signal_history = self._signal_history[-500:]

        # 触发回调
        self._trigger_callbacks(signal)

    def add_callback(self, name: str, callback: Callable):
        """
        添加信号回调

        Args:
            name: 回调名称
            callback: 回调函数，接收 (signal, results) 参数
        """
        if name not in self._callbacks:
            self._callbacks[name] = []
        self._callbacks[name].append(callback)
        logger.info(f"➕ 回调已添加: {name}")

    def _trigger_callbacks(self, signal: TradingSignal):
        """触发所有回调"""
        for callbacks in self._callbacks.values():
            for callback in callbacks:
                try:
                    callback(signal, {})
                except Exception as e:
                    logger.error(f"回调执行失败: {e}")

    # ------------------------------------------------------------------------
    # 查询方法
    # ------------------------------------------------------------------------
    def get_history(self, symbol: str = None, limit: int = 100) -> List[TradingSignal]:
        """获取信号历史"""
        if symbol:
            return [s for s in self._signal_history if s.symbol == symbol][-limit:]
        return self._signal_history[-limit:]

    def get_last_signal(self, symbol: str) -> Optional[TradingSignal]:
        """获取最近一个信号"""
        history = self.get_history(symbol, limit=1)
        return history[0] if history else None

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            'total_signals': len(self._signal_history),
            'targets': list(self._targets.keys()),
            'cooldown': self._cooldown,
            'by_action': self._count_by_action(),
            'by_symbol': self._count_by_symbol(),
        }

    def _count_by_action(self) -> Dict[str, int]:
        counts = {}
        for s in self._signal_history:
            action = s.action.value
            counts[action] = counts.get(action, 0) + 1
        return counts

    def _count_by_symbol(self) -> Dict[str, int]:
        counts = {}
        for s in self._signal_history:
            counts[s.symbol] = counts.get(s.symbol, 0) + 1
        return counts


# ============================================================================
# 信号生成器
# ============================================================================
class SignalGenerator:
    """
    信号生成器 - 基于 NEMT 结果生成交易信号
    ===========================================

    策略逻辑:
    1. 谱宽高 → 市场相干性低 → 趋势信号
    2. 共振峰多 → 周期性明显 → 震荡策略
    3. 频率偏离 → 趋势形成 → 顺势信号
    """

    def __init__(self, router: SignalRouter = None):
        self.router = router or SignalRouter()

        # 策略参数
        self.spectral_width_threshold = 0.1
        self.confidence_threshold = 0.5

    def generate_from_nemt(self,
                          nemt_result: Dict,
                          price: float,
                          symbol: str = "BTCUSDT") -> Optional[TradingSignal]:
        """
        从 NEMT 结果生成信号

        Args:
            nemt_result: NEMT 分析结果
            price: 当前价格
            symbol: 交易对

        Returns:
            交易信号或 None
        """
        signal = TradingSignal()
        signal.symbol = symbol
        signal.price = price
        signal.source = SignalSource.NEMT

        # 提取 NEMT 指标
        sw = nemt_result.get('spectral_width', 0)
        mf = nemt_result.get('mean_frequency', 0)
        peaks = len(nemt_result.get('resonance_peaks', []))

        signal.nemt_spectral_width = sw
        signal.nemt_mean_frequency = mf
        signal.nemt_resonance_peaks = peaks

        # 指标存储
        signal.indicators = {
            'spectral_width': sw,
            'mean_frequency': mf,
            'resonance_peaks': peaks,
        }

        # 信号生成逻辑
        if sw > self.spectral_width_threshold:
            # 高谱宽 → 低相干性 → 趋势可能
            signal.action = SignalType.BUY if mf > 0 else SignalType.SELL
            signal.confidence = min(sw * 5, 1.0)  # 归一化置信度
            signal.reason = f"高谱宽({sw:.4f})，市场相干性低，趋势形成"
        else:
            # 低谱宽 → 高相干性 → 震荡/均值回归
            signal.action = SignalType.HOLD
            signal.confidence = 0.3
            signal.reason = f"低谱宽({sw:.4f})，市场稳定，观望"

        # 添加止损/止盈
        if signal.action != SignalType.HOLD:
            risk_pct = 0.02  # 2% 风险
            signal.stop_loss = price * (1 - risk_pct if signal.action == SignalType.BUY else 1 + risk_pct)
            signal.take_profit = price * (1 + risk_pct * 2 if signal.action == SignalType.BUY else 1 - risk_pct * 2)

        return signal

    def send_if_valid(self, signal: TradingSignal) -> Dict[str, bool]:
        """验证并发送信号"""
        # 验证
        valid, error = self.router.validate_signal(signal)
        if not valid:
            logger.info(f"⏭️  信号无效: {error}")
            return {}

        # 检查是否应该发送
        if not self.router.should_send(signal):
            return {}

        # 发送
        return self.router.send(signal)


# ============================================================================
# 便捷函数
# ============================================================================
def create_signal(symbol: str, action: str, price: float,
                  confidence: float = 0.7,
                  source: str = "nemt") -> TradingSignal:
    """快速创建信号"""
    signal = TradingSignal()
    signal.symbol = symbol
    signal.action = SignalType(action.lower())
    signal.price = price
    signal.confidence = confidence
    signal.source = SignalSource(source)
    return signal


# ============================================================================
# 单元测试
# ============================================================================
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    # 测试信号路由
    router = SignalRouter()

    # 生成测试信号
    signal = create_signal("BTCUSDT", "buy", 50000, confidence=0.8)

    # 验证
    valid, error = router.validate_signal(signal)
    print(f"信号验证: {'✅ 通过' if valid else '❌ 失败'}")
    if error:
        print(f"  原因: {error}")

    # 统计
    stats = router.get_stats()
    print(f"路由器统计: {json.dumps(stats, indent=2)}")

    # 测试信号生成
    generator = SignalGenerator(router)

    nemt_result = {
        'spectral_width': 0.15,
        'mean_frequency': 0.05,
        'resonance_peaks': [{'frequency': 0.1, 'amplitude': 0.8}],
    }

    signal = generator.generate_from_nemt(nemt_result, 50000)
    print(f"\n生成的信号:")
    print(f"  动作: {signal.action.value}")
    print(f"  置信度: {signal.confidence:.2%}")
    print(f"  原因: {signal.reason}")
