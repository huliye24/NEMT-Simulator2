# -*- coding: utf-8 -*-
"""
NEMT MCP 服务 - 回测接口

支持策略：
- ma_cross: 均线交叉策略
- turtle:   海龟交易法
"""

import sys
import json
import traceback
from typing import Any, Dict

__version__ = "1.1.0"


def run_backtest(
    symbol: str = "BTC/USDT",
    days: int = 30,
    initial_capital: float = 10000.0,
    interval: str = "1h",
    strategy_type: str = "ma_cross",
    # MA Cross 参数
    fast_period: int = 5,
    slow_period: int = 20,
    # Turtle 参数
    entry_period: int = 20,
    exit_period: int = 10,
    atr_period: int = 20,
    max_units: int = 4,
) -> Dict[str, Any]:
    """
    运行回测
    
    Args:
        symbol: 交易对，如 "BTC/USDT"
        days: 回测天数
        initial_capital: 初始资金
        interval: K线周期，如 "1h", "4h", "1d"
        strategy_type: 策略类型，"ma_cross" 或 "turtle"
        fast_period: 快线周期 (均线策略)
        slow_period: 慢线周期 (均线策略)
        entry_period: 入场周期 (海龟策略)
        exit_period: 出场周期 (海龟策略)
        atr_period: ATR周期 (海龟策略)
        max_units: 最大仓位单位 (海龟策略)
    
    Returns:
        回测结果字典
    """
    try:
        import pandas as pd
        import numpy as np
        
        # 获取数据
        df = fetch_binance_data(symbol, interval, days)
        if df is None or len(df) == 0:
            return {
                "success": False,
                "error": f"无法获取 {symbol} 的市场数据",
            }
        
        # 根据策略类型执行回测
        if strategy_type == "turtle":
            result = _run_turtle_strategy(
                df, initial_capital, entry_period, exit_period, atr_period, max_units
            )
        else:
            result = _run_ma_cross_strategy(
                df, initial_capital, fast_period, slow_period
            )
        
        return {
            "success": True,
            "symbol": symbol,
            "days": days,
            "interval": interval,
            "strategy_type": strategy_type,
            **result,
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc(),
        }


def _run_ma_cross_strategy(
    df, initial_capital: float, fast_period: int, slow_period: int
) -> Dict[str, Any]:
    """均线交叉策略"""
    import pandas as pd
    
    # 计算均线
    df['fast_ma'] = df['close'].rolling(fast_period).mean()
    df['slow_ma'] = df['close'].rolling(slow_period).mean()
    
    # 回测
    capital = initial_capital
    position = 0
    trades = []
    entry_price = 0
    entry_time = None
    
    for i, row in df.iterrows():
        if pd.isna(row['fast_ma']) or pd.isna(row['slow_ma']):
            continue
        
        price = row['close']
        timestamp = row['timestamp']
        
        # 金叉买入
        if row['fast_ma'] > row['slow_ma'] and position == 0:
            position = capital / price * 0.95
            entry_price = price
            entry_time = timestamp
            capital = 0
        
        # 死叉卖出
        elif row['fast_ma'] < row['slow_ma'] and position > 0:
            capital = position * price * 0.995
            pnl = (price - entry_price) / entry_price * 100
            trades.append({
                "entry_time": str(entry_time),
                "exit_time": str(timestamp),
                "entry_price": float(entry_price),
                "exit_price": float(price),
                "pnl_pct": round(float(pnl), 4),
            })
            position = 0
    
    # 平仓
    if position > 0 and len(df) > 0:
        final_price = df.iloc[-1]['close']
        capital = position * final_price
    
    # 统计
    total_return = (capital - initial_capital) / initial_capital * 100
    winning_trades = len([t for t in trades if t['pnl_pct'] > 0])
    win_rate = winning_trades / len(trades) * 100 if trades else 0
    
    return {
        "summary": {
            "initial_capital": float(initial_capital),
            "final_capital": round(float(capital), 2),
            "total_return_pct": round(float(total_return), 2),
            "total_trades": len(trades),
            "win_rate": round(float(win_rate), 1),
            "fast_period": fast_period,
            "slow_period": slow_period,
        },
        "trades": trades[-10:] if len(trades) > 10 else trades,
    }


def _run_turtle_strategy(
    df, initial_capital: float, entry_period: int, exit_period: int,
    atr_period: int, max_units: int
) -> Dict[str, Any]:
    """
    海龟交易法策略
    
    规则：
    - 入场：价格突破过去 N 日最高价
    - 加仓：每上涨 0.5N 加仓，最多加 max_units 次
    - 止损：跌破 2N 止损
    - 出场：跌破 M 日最低价
    """
    import pandas as pd
    
    # 计算 True Range 和 ATR
    df['tr'] = pd.concat([
        df['high'] - df['low'],
        abs(df['high'] - df['close'].shift(1)),
        abs(df['low'] - df['close'].shift(1))
    ], axis=1).max(axis=1)
    df['atr'] = df['tr'].rolling(atr_period).mean()
    
    # 计算入场和出场高低点
    df['entry_high'] = df['high'].rolling(entry_period).max().shift(1)
    df['exit_low'] = df['low'].rolling(exit_period).min().shift(1)
    
    # 回测
    capital = initial_capital
    position = 0
    entry_price = 0
    entry_time = None
    units = 0  # 当前持仓单位数
    stop_loss = 0  # 止损价
    trades = []
    
    for i, row in df.iterrows():
        if pd.isna(row['atr']) or pd.isna(row['entry_high']) or pd.isna(row['exit_low']):
            continue
        
        price = row['close']
        high = row['high']
        low = row['low']
        atr = row['atr']
        timestamp = row['timestamp']
        
        # 入场条件：突破 20 日最高价
        if position == 0 and high > row['entry_high']:
            unit_size = capital * 0.01 / atr if atr > 0 else 0  # 每单位风险 1%
            if unit_size > 0:
                position = unit_size
                entry_price = row['entry_high']
                entry_time = timestamp
                stop_loss = entry_price - 2 * atr
                units = 1
                capital = 0
        
        # 加仓条件：价格高于入场价 + 0.5N
        elif position > 0 and units < max_units:
            add_price = entry_price + 0.5 * atr
            if price >= add_price:
                unit_size = capital * 0.01 / atr if atr > 0 else 0
                if unit_size > 0 and capital > 0:
                    position += unit_size
                    entry_price = (entry_price * units + price) / (units + 1)
                    units += 1
                    stop_loss = entry_price - 2 * atr
        
        # 止损条件：跌破 2N 止损
        elif position > 0 and low < stop_loss:
            capital = position * stop_loss * 0.995
            pnl = (stop_loss - entry_price) / entry_price * 100
            trades.append({
                "entry_time": str(entry_time),
                "exit_time": str(timestamp),
                "entry_price": float(entry_price),
                "exit_price": float(stop_loss),
                "pnl_pct": round(float(pnl), 4),
                "exit_reason": "stop_loss",
                "units": units,
            })
            position = 0
            units = 0
        
        # 出场条件：跌破 10 日最低价
        elif position > 0 and low < row['exit_low']:
            capital = position * price * 0.995
            pnl = (price - entry_price) / entry_price * 100
            trades.append({
                "entry_time": str(entry_time),
                "exit_time": str(timestamp),
                "entry_price": float(entry_price),
                "exit_price": float(price),
                "pnl_pct": round(float(pnl), 4),
                "exit_reason": "exit_low",
                "units": units,
            })
            position = 0
            units = 0
    
    # 平仓
    if position > 0 and len(df) > 0:
        final_price = df.iloc[-1]['close']
        capital = position * final_price
    
    # 统计
    total_return = (capital - initial_capital) / initial_capital * 100
    winning_trades = len([t for t in trades if t['pnl_pct'] > 0])
    win_rate = winning_trades / len(trades) * 100 if trades else 0
    
    # 计算最大回撤
    equity_curve = [initial_capital]
    for t in trades:
        equity_curve.append(equity_curve[-1] * (1 + t['pnl_pct'] / 100))
    
    peak = initial_capital
    max_dd = 0
    for e in equity_curve:
        if e > peak:
            peak = e
        dd = (peak - e) / peak * 100 if peak > 0 else 0
        max_dd = max(max_dd, dd)
    
    return {
        "summary": {
            "initial_capital": float(initial_capital),
            "final_capital": round(float(capital), 2),
            "total_return_pct": round(float(total_return), 2),
            "total_trades": len(trades),
            "win_rate": round(float(win_rate), 1),
            "max_drawdown_pct": round(float(max_dd), 2),
            "entry_period": entry_period,
            "exit_period": exit_period,
            "atr_period": atr_period,
            "max_units": max_units,
        },
        "trades": trades[-10:] if len(trades) > 10 else trades,
    }


def fetch_binance_data(symbol: str, interval: str, days: int):
    """从 Binance 获取 K 线数据"""
    try:
        import ccxt
        import pandas as pd
        from datetime import datetime, timedelta
        
        exchange = ccxt.binance()
        since = int((datetime.now() - timedelta(days=days)).timestamp() * 1000)
        
        ohlcv = exchange.fetch_ohlcv(symbol.replace('/', ''), interval, since=since)
        
        if not ohlcv:
            return None
        
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        
        return df
        
    except ImportError:
        return None
    except Exception:
        return None


def handle_request(request: Dict) -> Dict:
    """处理 MCP 请求"""
    method = request.get("method")
    params = request.get("params", {})
    
    if method == "tools/call":
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        
        if tool_name == "run_backtest":
            result = run_backtest(**arguments)
            return {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "result": result,
            }
        else:
            return {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "error": {"code": -32601, "message": f"Unknown tool: {tool_name}"},
            }
    
    elif method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": request.get("id"),
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "nemt-backtest", "version": __version__},
            },
        }
    
    elif method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": request.get("id"),
            "result": {
                "tools": [
                    {
                        "name": "run_backtest",
                        "description": "运行 NEMT 回测，支持均线交叉(ma_cross)和海龟交易法(turtle)",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "symbol": {
                                    "type": "string",
                                    "description": "交易对",
                                    "default": "BTC/USDT"
                                },
                                "days": {
                                    "type": "number",
                                    "description": "回测天数",
                                    "default": 30
                                },
                                "initial_capital": {
                                    "type": "number",
                                    "description": "初始资金",
                                    "default": 10000
                                },
                                "interval": {
                                    "type": "string",
                                    "description": "K线周期: 1h, 4h, 1d",
                                    "default": "1h"
                                },
                                "strategy_type": {
                                    "type": "string",
                                    "description": "策略类型: ma_cross 或 turtle",
                                    "default": "ma_cross"
                                },
                                "fast_period": {
                                    "type": "number",
                                    "description": "快线周期 (均线策略)",
                                    "default": 5
                                },
                                "slow_period": {
                                    "type": "number",
                                    "description": "慢线周期 (均线策略)",
                                    "default": 20
                                },
                                "entry_period": {
                                    "type": "number",
                                    "description": "入场周期 (海龟策略)",
                                    "default": 20
                                },
                                "exit_period": {
                                    "type": "number",
                                    "description": "出场周期 (海龟策略)",
                                    "default": 10
                                },
                                "atr_period": {
                                    "type": "number",
                                    "description": "ATR周期 (海龟策略)",
                                    "default": 20
                                },
                                "max_units": {
                                    "type": "number",
                                    "description": "最大仓位单位 (海龟策略)",
                                    "default": 4
                                },
                            },
                        },
                    }
                ]
            },
        }
    
    else:
        return {
            "jsonrpc": "2.0",
            "id": request.get("id"),
            "error": {"code": -32601, "message": f"Unknown method: {method}"},
        }


def main():
    """MCP 主循环"""
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        
        try:
            request = json.loads(line)
            response = handle_request(request)
            print(json.dumps(response, ensure_ascii=False), flush=True)
        except json.JSONDecodeError:
            print(json.dumps({"jsonrpc": "2.0", "error": {"code": -32700, "message": "Parse error"}}), flush=True)


if __name__ == "__main__":
    main()
