"""
NEMT Engine API
FastAPI backend for NEMT Web Alpha
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from routes.market import router as market_router
from routes.analysis import router as analysis_router
from routes.simulation import router as simulation_router
from routes.execution import router as execution_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时加载 NEMT Engine
    print("🚀 NEMT Engine API Starting...")
    yield
    # 关闭时清理资源
    print("👋 NEMT Engine API Shutting down...")


# 创建 FastAPI 应用
app = FastAPI(
    title="NEMT Engine API",
    description="NEMT Quant System API - Connect Web Frontend to NEMT Core Engine",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(market_router, prefix="/market", tags=["Market"])
app.include_router(analysis_router, prefix="/analysis", tags=["Analysis"])
app.include_router(simulation_router, prefix="/simulation", tags=["Simulation"])
app.include_router(execution_router, prefix="/execution", tags=["Execution"])


@app.get("/")
async def root():
    """根路径"""
    return {
        "name": "NEMT Engine API",
        "version": "0.1.0",
        "status": "running",
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "ok", "engine": "connected"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
