#!/usr/bin/env python3
"""
Market Data API - 市场数据API服务

提供HTTP接口供NEMT-Go调用获取市场数据

Usage:
    python services/market_api.py
    uvicorn services.market_api:app --host 0.0.0.0 --port 8000
"""

import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from contextlib import asynccontextmanager

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI, HTTPException, Query, Path as PathParam
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import logging

# 导入数据加载器
from backtest.data.loaders.us_stock_loader import USStockLoader
from backtest.data.loaders.cos_loader import COSLoader
from backtest.data.cache.data_cache import DataCache

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ==================== 请求/响应模型 ====================

class OHLCVRecord(BaseModel):
    """K线数据模型"""
    timestamp: str
    symbol: str
    open: float
    high: float
    low: float
    close: float
    volume: float
    quote_volume: float = 0
    source: str = "unknown"


class USStockResponse(BaseModel):
    """美股数据响应"""
    code: int = 0
    message: str = "success"
    data: Optional[Dict[str, Any]] = None


class StockInfoResponse(BaseModel):
    """股票信息响应"""
    symbol: str
    name: str
    sector: str = ""
    industry: str = ""
    market_cap: float = 0
    current_price: float = 0
    pe_ratio: float = 0


class SymbolListResponse(BaseModel):
    """股票列表响应"""
    symbols: List[str]
    total: int


class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str = "healthy"
    timestamp: str
    version: str = "1.0.0"
    cache_stats: Dict[str, Any] = {}


# ==================== 全局变量 ====================

# COS配置
COS_CONFIG = {
    'Region': os.getenv('COS_REGION', 'ap-guangzhou'),
    'SecretId': os.getenv('COS_SECRET_ID', ''),
    'SecretKey': os.getenv('COS_SECRET_KEY', ''),
    'Bucket': os.getenv('COS_BUCKET', 'nemt-marketdata'),
}

# 全局加载器 (懒加载)
_us_stock_loader: Optional[USStockLoader] = None
_cos_loader: Optional[COSLoader] = None
_data_cache: Optional[DataCache] = None


def get_us_stock_loader() -> USStockLoader:
    """获取或创建USStockLoader"""
    global _us_stock_loader
    if _us_stock_loader is None:
        _us_stock_loader = USStockLoader()
    return _us_stock_loader


def get_cos_loader() -> COSLoader:
    """获取或创建COSLoader"""
    global _cos_loader
    if _cos_loader is None:
        _cos_loader = COSLoader(
            cos_config=COS_CONFIG,
            cache_dir="./cache/market_data"
        )
    return _cos_loader


def get_data_cache() -> DataCache:
    """获取或创建DataCache"""
    global _data_cache
    if _data_cache is None:
        _data_cache = DataCache(max_size=100, persist_path="./cache/market_data")
    return _data_cache


# ==================== 生命周期 ====================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    global us_stock_loader, cos_loader, data_cache

    logger.info("Starting Market Data API...")

    # 初始化加载器
    us_stock_loader = USStockLoader()
    cos_loader = COSLoader(
        cos_config=COS_CONFIG,
        cache_dir="./cache/market_data"
    )
    data_cache = DataCache(max_size=100, persist_path="./cache/market_data")

    logger.info("Market Data API started successfully")

    yield

    logger.info("Shutting down Market Data API...")


# ==================== FastAPI 应用 ====================

app = FastAPI(
    title="NEMT Market Data API",
    description="市场数据API服务 - 支持美股、指数等市场数据",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== 路由定义 ====================

@app.get("/health", response_model=HealthResponse, tags=["健康检查"])
async def health_check():
    """健康检查"""
    stats = get_data_cache().get_stats() if get_data_cache() else {}
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now().isoformat(),
        version="1.0.0",
        cache_stats=stats,
    )


@app.get("/api/v1/market/us_stocks/{symbol}", response_model=USStockResponse, tags=["美股数据"])
async def get_us_stock(
    symbol: str = PathParam(..., description="股票代码", example="AAPL"),
    interval: str = Query("1d", description="时间周期", pattern="^(1d|1w|1M)$"),
    start: Optional[str] = Query(None, description="开始日期 (YYYY-MM-DD)"),
    end: Optional[str] = Query(None, description="结束日期 (YYYY-MM-DD)"),
    limit: Optional[int] = Query(None, description="返回条数限制"),
) -> USStockResponse:
    """
    获取美股历史K线数据

    支持的时间周期: 1d (日线), 1w (周线), 1M (月线)

    **示例请求:**
    ```
    GET /api/v1/market/us_stocks/AAPL?interval=1d&start=2020-01-01&end=2024-12-31
    ```
    """
    loader = get_us_stock_loader()

    try:
        # 解析日期
        start_date = None
        end_date = None

        if start:
            start_date = datetime.strptime(start, "%Y-%m-%d")
        if end:
            end_date = datetime.strptime(end, "%Y-%m-%d")

        # 加载数据
        result = loader.load(
            symbol=symbol.upper(),
            timeframe=interval,
            start_date=start_date,
            end_date=end_date,
            use_cache=True,
        )

        if not result.success:
            raise HTTPException(status_code=404, detail=f"Failed to load {symbol}: {result.error}")

        # 转换数据
        records = []
        for ohlcv in result.data.data:
            records.append(OHLCVRecord(
                timestamp=ohlcv.timestamp.isoformat(),
                symbol=ohlcv.symbol,
                open=ohlcv.open,
                high=ohlcv.high,
                low=ohlcv.low,
                close=ohlcv.close,
                volume=ohlcv.volume,
                quote_volume=ohlcv.quote_volume,
                source=ohlcv.source,
            ))

        # 应用限制
        if limit:
            records = records[-limit:]

        return USStockResponse(
            code=0,
            message="success",
            data={
                "symbol": symbol.upper(),
                "interval": interval,
                "count": len(records),
                "records": [r.model_dump() for r in records],
            }
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {e}")
    except Exception as e:
        logger.error(f"Error loading {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/market/us_stocks/{symbol}/info", response_model=StockInfoResponse, tags=["美股数据"])
async def get_stock_info(
    symbol: str = PathParam(..., description="股票代码"),
) -> StockInfoResponse:
    """获取股票基本信息"""
    loader = get_us_stock_loader()

    try:
        info = loader.get_info(symbol.upper())

        if "error" in info:
            raise HTTPException(status_code=404, detail=info["error"])

        return StockInfoResponse(**info)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting info for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/market/symbols", response_model=SymbolListResponse, tags=["股票列表"])
async def get_symbols(
    category: str = Query("popular", description="分类: popular(推荐), all"),
) -> SymbolListResponse:
    """
    获取支持的股票列表

    - **popular**: 推荐股票列表 (科技、金融、消费等主要股票)
    - **all**: 完整列表
    """
    symbols = USStockLoader.get_popular_stocks()
    return SymbolListResponse(symbols=symbols, total=len(symbols))


@app.get("/api/v1/market/search", response_model=List[Dict[str, str]], tags=["股票搜索"])
async def search_stocks(
    q: str = Query(..., description="搜索关键词", min_length=1),
    limit: int = Query(10, description="返回结果数", ge=1, le=50),
) -> List[Dict[str, str]]:
    """搜索股票"""
    loader = get_us_stock_loader()

    try:
        results = loader.search_stocks(q, limit)
        return results
    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/market/quote/{symbol}", tags=["实时报价"])
async def get_realtime_quote(
    symbol: str = PathParam(..., description="股票代码"),
) -> Dict[str, Any]:
    """获取实时报价"""
    loader = get_us_stock_loader()

    try:
        quote = loader.get_realtime_quote(symbol.upper())

        if quote is None:
            raise HTTPException(status_code=404, detail=f"Quote not available for {symbol}")

        return {
            "code": 0,
            "message": "success",
            "data": quote,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting quote for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/cache/clear", tags=["缓存管理"])
async def clear_cache(
    symbol: Optional[str] = Query(None, description="可选，指定清除特定股票缓存"),
) -> Dict[str, str]:
    """清除缓存"""
    cache = get_data_cache()
    cos = get_cos_loader()

    if cache:
        if symbol:
            cache.invalidate_symbol(symbol.upper())
            message = f"Cache cleared for {symbol}"
        else:
            cache.clear()
            message = "All cache cleared"
    elif cos:
        cos.clear_cache(symbol)
        message = f"Cache cleared" if symbol else "All cache cleared"
    else:
        message = "No cache to clear"

    logger.info(message)
    return {"status": "success", "message": message}


@app.get("/api/v1/cache/stats", tags=["缓存管理"])
async def get_cache_stats() -> Dict[str, Any]:
    """获取缓存统计"""
    cache = get_data_cache()
    cos = get_cos_loader()

    stats = {}
    if cache:
        stats = cache.get_stats()
    elif cos:
        stats = cos.get_cache_stats()

    return {
        "code": 0,
        "message": "success",
        "data": stats,
    }


# ==================== 主入口 ====================

def main():
    import uvicorn

    port = int(os.getenv("PORT", "8000"))
    host = os.getenv("HOST", "0.0.0.0")

    logger.info(f"Starting Market Data API on {host}:{port}")

    uvicorn.run(
        "services.market_api:app",
        host=host,
        port=port,
        reload=False,
        log_level="info",
    )


if __name__ == "__main__":
    main()
