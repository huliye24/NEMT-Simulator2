"""
Simulation Routes
/simulation/*
"""

from fastapi import APIRouter, HTTPException
from typing import Optional

from nemt_adapter.engine import adapter

router = APIRouter()


@router.get("/signal")
async def get_simulation_signal(symbol: Optional[str] = "BTCUSDT"):
    """
    获取模拟交易信号

    Args:
        symbol: 交易对，默认 BTCUSDT

    Returns:
        Simulation Signal JSON
    """
    try:
        signal = adapter.get_simulation_signal(symbol)
        return signal
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/signals")
async def get_all_simulation_signals():
    """
    获取所有模拟交易信号

    Returns:
        List of Simulation Signals
    """
    symbols = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT"]
    signals = []

    for symbol in symbols:
        try:
            signal = adapter.get_simulation_signal(symbol)
            signals.append(signal)
        except Exception as e:
            print(f"Error getting signal for {symbol}: {e}")

    return {
        "signals": signals,
        "count": len(signals),
    }
