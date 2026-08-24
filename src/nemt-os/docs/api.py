"""
NEMT Simulator API Documentation

# OpenAPI 3.0 Specification
"""

OPENAPI_SPEC = {
    "openapi": "3.0.0",
    "info": {
        "title": "NEMT Simulator API",
        "version": "1.0.0",
        "description": "NEMT Simulator - Container-Ready Trading System",
    },
    "servers": [{"url": "/api/v1", "description": "API v1"}],
    "paths": {
        "/health": {
            "get": {
                "summary": "健康检查",
                "tags": ["System"],
                "responses": {
                    "200": {
                        "description": "健康",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "status": {"type": "string"},
                                        "timestamp": {"type": "number"},
                                    },
                                }
                            }
                        },
                    }
                },
            }
        },
        "/capsules": {
            "get": {
                "summary": "获取所有胶囊",
                "tags": ["Capsules"],
                "responses": {
                    "200": {
                        "description": "胶囊列表",
                        "content": {
                            "application/json": {
                                "schema": {"type": "array", "items": {"$ref": "#/components/schemas/Capsule"}}
                            }
                        },
                    }
                },
            }
        },
        "/capsules/{capsule_id}": {
            "get": {
                "summary": "获取胶囊详情",
                "tags": ["Capsules"],
                "parameters": [{"name": "capsule_id", "in": "path", "required": True, "schema": {"type": "string"}}],
                "responses": {
                    "200": {
                        "description": "胶囊详情",
                        "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Capsule"}}},
                    }
                },
            }
        },
        "/strategies": {
            "get": {
                "summary": "获取所有策略",
                "tags": ["Strategies"],
                "responses": {"200": {"description": "策略列表"}},
            },
            "post": {
                "summary": "创建策略",
                "tags": ["Strategies"],
                "requestBody": {
                    "required": True,
                    "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Strategy"}}},
                },
                "responses": {"201": {"description": "创建成功"}},
            },
        },
        "/strategies/{strategy_id}/backtest": {
            "post": {
                "summary": "运行回测",
                "tags": ["Strategies"],
                "parameters": [{"name": "strategy_id", "in": "path", "required": True}],
                "requestBody": {
                    "content": {"application/json": {"schema": {"$ref": "#/components/schemas/BacktestConfig"}}}
                },
                "responses": {
                    "200": {
                        "description": "回测结果",
                        "content": {"application/json": {"schema": {"$ref": "#/components/schemas/BacktestResult"}}},
                    }
                },
            }
        },
        "/market/klines": {
            "get": {
                "summary": "获取K线数据",
                "tags": ["Market"],
                "parameters": [
                    {"name": "symbol", "in": "query", "required": True},
                    {"name": "interval", "in": "query", "required": True},
                    {"name": "limit", "in": "query"},
                ],
                "responses": {"200": {"description": "K线数据"}},
            }
        },
        "/metrics": {
            "get": {
                "summary": "获取指标",
                "tags": ["Metrics"],
                "responses": {"200": {"description": "Prometheus 格式指标", "content": {"text/plain": {}}}},
            }
        },
    },
    "components": {
        "schemas": {
            "Capsule": {
                "type": "object",
                "properties": {
                    "capsule_id": {"type": "string"},
                    "name": {"type": "string"},
                    "state": {"type": "string"},
                    "health": {"type": "string"},
                    "metrics": {"type": "object"},
                },
            },
            "Strategy": {
                "type": "object",
                "properties": {
                    "strategy_id": {"type": "string"},
                    "name": {"type": "string"},
                    "type": {"type": "string"},
                    "params": {"type": "object"},
                    "status": {"type": "string"},
                },
            },
            "BacktestConfig": {
                "type": "object",
                "properties": {
                    "symbol": {"type": "string"},
                    "interval": {"type": "string"},
                    "start_time": {"type": "string"},
                    "end_time": {"type": "string"},
                    "initial_capital": {"type": "number"},
                },
            },
            "BacktestResult": {
                "type": "object",
                "properties": {
                    "backtest_id": {"type": "string"},
                    "metrics": {"type": "object"},
                    "equity_curve": {"type": "array", "items": {"type": "number"}},
                    "trades": {"type": "array"},
                },
            },
        },
        "securitySchemes": {"ApiKeyAuth": {"type": "apiKey", "in": "header", "name": "X-API-Key"}},
    },
}

# API 端点文档
API_ENDPOINTS = """
# NEMT Simulator API

## 系统
- `GET /health` - 健康检查
- `GET /ready` - 就绪检查
- `GET /metrics` - Prometheus 指标

## 胶囊
- `GET /api/v1/capsules` - 获取所有胶囊
- `GET /api/v1/capsules/{id}` - 获取胶囊详情
- `POST /api/v1/capsules/{id}/start` - 启动胶囊
- `POST /api/v1/capsules/{id}/stop` - 停止胶囊
- `GET /api/v1/capsules/{id}/metrics` - 获取胶囊指标

## 策略
- `GET /api/v1/strategies` - 获取所有策略
- `POST /api/v1/strategies` - 创建策略
- `GET /api/v1/strategies/{id}` - 获取策略详情
- `PUT /api/v1/strategies/{id}` - 更新策略
- `DELETE /api/v1/strategies/{id}` - 删除策略
- `POST /api/v1/strategies/{id}/backtest` - 运行回测

## 市场数据
- `GET /api/v1/market/klines` - 获取K线数据
- `GET /api/v1/market/ticker` - 获取行情
- `GET /api/v1/market/orderbook` - 获取订单簿

## 回测
- `GET /api/v1/backtests` - 获取回测列表
- `GET /api/v1/backtests/{id}` - 获取回测结果
- `DELETE /api/v1/backtests/{id}` - 删除回测

## 认证
所有 API 需要在请求头中包含:
```
X-API-Key: your-api-key
```
"""
