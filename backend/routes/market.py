"""
Market Routes
/market/*
"""

from fastapi import APIRouter, HTTPException
from typing import List, Optional

from nemt_adapter.engine import adapter

router = APIRouter()


@router.get("/state")
async def get_market_state(symbol: Optional[str] = "BTCUSDT"):
    """
    获取市场状态

    Args:
        symbol: 交易对，默认 BTCUSDT

    Returns:
        Market State JSON
    """
    try:
        state = adapter.get_market_state(symbol)
        return {
            "symbol": state.symbol,
            "phase": state.phase,
            "dci": state.dci,
            "signal": state.signal,
            "confidence": state.confidence,
            "price": state.price,
            "change24h": state.change24h,
            "timestamp": "2026-08-25T10:00:00Z",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/states")
async def get_all_market_states():
    """
    获取所有市场状态

    Returns:
        List of Market State JSON
    """
    symbols = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT", "ADAUSDT"]
    states = []

    for symbol in symbols:
        try:
            state = adapter.get_market_state(symbol)
            states.append({
                "symbol": state.symbol,
                "phase": state.phase,
                "dci": state.dci,
                "signal": state.signal,
                "confidence": state.confidence,
                "price": state.price,
                "change24h": state.change24h,
            })
        except Exception as e:
            print(f"Error getting state for {symbol}: {e}")

    return {
        "states": states,
        "count": len(states),
        "timestamp": "2026-08-25T10:00:00Z",
    }
