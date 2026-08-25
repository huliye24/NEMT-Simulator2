"""
Analysis Routes
/analysis/*
"""

from fastapi import APIRouter, HTTPException
from typing import Optional

from nemt_adapter.engine import adapter

router = APIRouter()


@router.get("/report")
async def get_analysis_report(symbol: Optional[str] = "BTCUSDT"):
    """
    获取分析报告

    Args:
        symbol: 交易对，默认 BTCUSDT

    Returns:
        Analysis Report JSON
    """
    try:
        report = adapter.get_analysis_report(symbol)
        return {
            "symbol": report.symbol,
            "summary": report.summary,
            "reasoning": report.reasoning,
            "recommendation": report.recommendation,
            "confidence": report.confidence,
            "dci": report.dci,
            "phase": report.phase,
            "generated_at": "2026-08-25T10:00:00Z",
            "author": "NEMT Engine",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/reports")
async def get_all_analysis_reports():
    """
    获取所有分析报告

    Returns:
        List of Analysis Reports
    """
    symbols = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT"]
    reports = []

    for symbol in symbols:
        try:
            report = adapter.get_analysis_report(symbol)
            reports.append({
                "symbol": report.symbol,
                "summary": report.summary,
                "reasoning": report.reasoning,
                "recommendation": report.recommendation,
                "confidence": report.confidence,
                "dci": report.dci,
                "phase": report.phase,
            })
        except Exception as e:
            print(f"Error getting report for {symbol}: {e}")

    return {
        "reports": reports,
        "count": len(reports),
    }
