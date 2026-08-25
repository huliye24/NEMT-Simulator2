"""
Execution Routes
/execution/*
订单执行和风险管理
"""

from fastapi import APIRouter, HTTPException
from typing import Optional, List

from services.binance_connector import BinanceConnector
from services.risk_gate import RiskGate, RiskConfig
from services.order_manager import OrderManager

router = APIRouter()

# 初始化服务
risk_config = RiskConfig(
    max_position_size=10000.0,
    max_position_ratio=0.3,
    daily_loss_limit=500.0,
)
risk_gate = RiskGate(risk_config)
binance = BinanceConnector()
order_manager = OrderManager(binance, risk_gate)


@router.get("/status")
async def get_execution_status():
    """获取执行状态"""
    return {
        "exchange": binance.get_api_status(),
        "risk_gate": risk_gate.get_status(),
        "order_stats": order_manager.get_stats(),
    }


@router.post("/connect")
async def connect_exchange(api_key: Optional[str] = None, api_secret: Optional[str] = None):
    """连接交易所"""
    try:
        success = await binance.connect()
        return {
            "connected": success,
            "paper_trading": binance.is_paper_trading(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/order")
async def create_order(
    symbol: str = "BTCUSDT",
    signal: str = "WAIT",
    confidence: float = 50.0,
    dci: float = 50.0,
):
    """
    创建订单

    Signal → Risk Check → Order
    """
    try:
        order = await order_manager.create_order_from_signal(
            symbol=symbol,
            signal=signal,
            confidence=confidence,
            dci=dci,
        )

        if order:
            return {
                "success": True,
                "order": {
                    "id": order.id,
                    "symbol": order.symbol,
                    "side": order.side.value,
                    "type": order.type.value,
                    "quantity": order.quantity,
                    "price": order.price,
                    "status": order.status.value,
                },
                "message": "Order created successfully",
            }
        else:
            return {
                "success": False,
                "order": None,
                "message": "Order blocked by Risk Gate",
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/orders")
async def get_orders(status: Optional[str] = None):
    """获取订单列表"""
    try:
        if status == "open":
            records = order_manager.get_open_orders()
        else:
            records = order_manager.get_order_history()

        return {
            "orders": [
                {
                    "id": r.order.id,
                    "symbol": r.order.symbol,
                    "side": r.order.side.value,
                    "quantity": r.order.quantity,
                    "price": r.order.price,
                    "status": r.order.status.value,
                    "signal": r.signal,
                    "reason": r.reason,
                    "created_at": r.created_at,
                }
                for r in records
            ],
            "count": len(records),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/emergency-stop")
async def emergency_stop(enable: bool = True):
    """紧急停止"""
    risk_gate.set_emergency_stop(enable)
    return {
        "emergency_stop": risk_gate.is_emergency_stop(),
        "message": "Emergency stop activated" if enable else "Emergency stop released",
    }


@router.get("/risk/config")
async def get_risk_config():
    """获取风险配置"""
    return {
        "max_position_size": risk_config.max_position_size,
        "max_position_ratio": risk_config.max_position_ratio,
        "daily_loss_limit": risk_config.daily_loss_limit,
        "max_leverage": risk_config.max_leverage,
        "allowed_symbols": risk_config.allowed_symbols,
    }
