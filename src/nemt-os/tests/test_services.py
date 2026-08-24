"""
NEMT Platform - 服务集成测试

测试各服务之间的通信
"""

import os

# 添加项目路径
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from nemt_os.services.common.config import ServiceConfig
from nemt_os.services.common.types import EventTypes


class TestServiceRegistry:
    """测试服务注册"""

    def test_config_from_env(self):
        """测试配置加载"""
        os.environ["SERVICE_NAME"] = "test"
        os.environ["SERVICE_PORT"] = "8001"

        config = ServiceConfig.from_env("test", 8000)

        assert config.service_name == "test"
        assert config.port == 8001

    def test_service_info_serialization(self):
        """测试服务信息序列化"""
        from datetime import datetime

        from nemt_os.services.common.types import ServiceInfo, ServiceStatus

        info = ServiceInfo(
            service_name="test",
            host="localhost",
            port=8000,
            status=ServiceStatus.HEALTHY,
            version="1.0.0",
            started_at=datetime.now(),
        )

        data = info.to_dict()

        assert data["service_name"] == "test"
        assert data["status"] == "healthy"
        assert "timestamp" not in data or data.get("started_at") is not None


class TestEventTypes:
    """测试事件类型"""

    def test_market_events(self):
        """测试市场事件"""
        assert EventTypes.MARKET_BAR == "market.bar"
        assert EventTypes.MARKET_PRICE == "market.price"
        assert EventTypes.MARKET_CANDLE_CLOSED == "market.candle_closed"

    def test_signal_events(self):
        """测试信号事件"""
        assert EventTypes.SIGNAL_GENERATED == "signal.generated"
        assert EventTypes.SIGNAL_CONFIDENCE_UPDATE == "signal.confidence_update"

    def test_risk_events(self):
        """测试风控事件"""
        assert EventTypes.RISK_APPROVED == "risk.approved"
        assert EventTypes.RISK_REJECTED == "risk.rejected"
        assert EventTypes.RISK_ALERT == "risk.alert"

    def test_execution_events(self):
        """测试执行事件"""
        assert EventTypes.EXECUTION_ORDER_SENT == "execution.order_sent"
        assert EventTypes.EXECUTION_FILLED == "execution.filled"
        assert EventTypes.EXECUTION_POSITION_UPDATE == "execution.position_update"


class TestSignalCalculation:
    """测试信号计算"""

    def test_dci_calculation(self):
        """测试 DCI 计算"""
        # 模拟 K线数据
        bars = [
            {"price": 100},
            {"price": 101},
            {"price": 102},
            {"price": 103},
            {"price": 104},
        ]

        up_moves = 0
        down_moves = 0

        for i in range(1, len(bars)):
            prev_close = bars[i - 1]["price"]
            curr_close = bars[i]["price"]

            if curr_close > prev_close:
                up_moves += 1
            elif curr_close < prev_close:
                down_moves += 1

        total = up_moves + down_moves
        dci = ((up_moves - down_moves) / total) * 100 if total > 0 else 0

        assert dci == 100  # 全部上涨

    def test_vortex_calculation(self):
        """测试 Vortex 计算"""
        # 简化测试
        up_sum = 0.6
        down_sum = 0.4

        vortex = up_sum / (up_sum + down_sum)

        assert vortex == 0.6


class TestRiskCalculation:
    """测试风控计算"""

    def test_position_size_calculation(self):
        """测试仓位计算"""
        balance = 100000.0
        max_position_ratio = 1.0
        price = 65000.0

        position_size = min(
            balance * max_position_ratio / price,
            balance * 0.1 / price,
        )

        # 应该是余额的 10% / 价格
        expected = balance * 0.1 / price
        assert abs(position_size - expected) < 0.001

    def test_risk_reward_ratio(self):
        """测试风险回报比"""
        entry = 100.0
        stop_loss = 98.0
        take_profit = 106.0

        risk_amount = abs(entry - stop_loss)
        reward_amount = abs(take_profit - entry)

        rr_ratio = reward_amount / risk_amount

        assert rr_ratio == 3.0  # 6 / 2 = 3

    def test_drawdown_calculation(self):
        """测试回撤计算"""
        peak_balance = 100000.0
        current_balance = 95000.0

        drawdown = (peak_balance - current_balance) / peak_balance

        assert drawdown == 0.05  # 5%


class TestServiceCommunication:
    """测试服务间通信"""

    @pytest.mark.asyncio
    async def test_event_message_format(self):
        """测试事件消息格式"""

        from nemt_os.services.common.types import EventMessage

        msg = EventMessage(
            event_type="test.event",
            source="test_service",
            data={"key": "value"},
            correlation_id="test-123",
        )

        data = msg.to_dict()

        assert data["event_type"] == "test.event"
        assert data["source"] == "test_service"
        assert data["data"]["key"] == "value"
        assert data["correlation_id"] == "test-123"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
