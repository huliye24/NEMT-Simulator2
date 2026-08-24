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
Backtest Module - 策略回测
"""
import json
import logging
from typing import List, Dict, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
import redis

logger = logging.getLogger(__name__)


@dataclass
class Trade:
    """交易记录"""
    timestamp: int
    action: str  # 'buy' or 'sell'
    price: float
    quantity: float
    fee: float = 0.0
    pnl: float = 0.0  # 盈亏


@dataclass
class BacktestResult:
    """回测结果"""
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    total_pnl: float = 0.0
    max_drawdown: float = 0.0
    win_rate: float = 0.0
    avg_profit: float = 0.0
    avg_loss: float = 0.0
    profit_factor: float = 0.0
    trades: List[Trade] = field(default_factory=list)
    
    def calculate(self):
        """计算统计指标"""
        if self.total_trades > 0:
            self.win_rate = self.winning_trades / self.total_trades * 100
            
        winning_pnl = [t.pnl for t in self.trades if t.pnl > 0]
        losing_pnl = [t.pnl for t in self.trades if t.pnl < 0]
        
        if winning_pnl:
            self.avg_profit = sum(winning_pnl) / len(winning_pnl)
        if losing_pnl:
            self.avg_loss = abs(sum(losing_pnl) / len(losing_pnl))
            
        if self.avg_loss > 0:
            self.profit_factor = self.avg_profit / self.avg_loss


class Backtester:
    """回测引擎"""
    
    def __init__(self, 
                 initial_capital: float = 10000.0,
                 fee_rate: float = 0.001,
                 redis_host: str = 'redis',
                 redis_port: int = 6379):
        self.initial_capital = initial_capital
        self.fee_rate = fee_rate
        self.capital = initial_capital
        self.position = 0.0
        self.buy_price = 0.0
        
        # Redis 连接
        self.redis_client = redis.Redis(
            host=redis_host,
            port=redis_port,
            decode_responses=True
        )
        
        # 交易记录
        self.trades: List[Trade] = []
        self.equity_curve: List[float] = []
        
    def load_historical_data(self, symbol: str = 'BTCUSDT', 
                            interval: str = '1m',
                            limit: int = 1000) -> List[Dict]:
        """从 Redis 加载历史数据"""
        stream_key = f"kline:{symbol}:{interval}"
        
        try:
            # 获取最新的 limit 条数据
            data = self.redis_client.xrevrange(stream_key, '+', '-', count=limit)
            
            records = []
            for msg_id, fields in reversed(data):
                record = {
                    'id': msg_id,
                    'timestamp': int(fields.get('close_time', 0)),
                    'open': float(fields.get('open', 0)),
                    'high': float(fields.get('high', 0)),
                    'low': float(fields.get('low', 0)),
                    'close': float(fields.get('close', 0)),
                    'volume': float(fields.get('volume', 0)),
                }
                records.append(record)
                
            logger.info(f"📂 加载了 {len(records)} 条历史数据")
            return records
            
        except Exception as e:
            logger.error(f"加载历史数据失败: {e}")
            return []
            
    def run(self, 
            data: List[Dict],
            strategy: Callable[[Dict, 'Backtester'], Optional[str]]) -> BacktestResult:
        """
        运行回测
        
        Args:
            data: K线数据
            strategy: 策略函数，接收 (kline_data, backtester) 返回 'buy', 'sell', 或 None
        """
        logger.info(f"🚀 开始回测，数据量: {len(data)}")
        
        self.capital = self.initial_capital
        self.position = 0.0
        self.trades = []
        self.equity_curve = []
        
        for kline in data:
            close = kline['close']
            timestamp = kline['timestamp']
            
            # 执行策略
            signal = strategy(kline, self)
            
            if signal == 'buy' and self.position == 0:
                self._buy(close, timestamp)
            elif signal == 'sell' and self.position > 0:
                self._sell(close, timestamp)
                
            # 记录权益
            equity = self.capital + (self.position * close)
            self.equity_curve.append(equity)
            
        # 计算结果
        result = self._calculate_result()
        
        # 保存到 Redis
        self._save_result(result)
        
        return result
        
    def _buy(self, price: float, timestamp: int):
        """买入"""
        fee = self.capital * self.fee_rate
        quantity = (self.capital - fee) / price
        
        self.position = quantity
        self.buy_price = price
        self.capital = 0
        
        trade = Trade(
            timestamp=timestamp,
            action='buy',
            price=price,
            quantity=quantity,
            fee=fee
        )
        self.trades.append(trade)
        
        logger.info(f"🟢 买入 | 价格: ${price:,.2f} | 数量: {quantity:.6f}")
        
    def _sell(self, price: float, timestamp: int):
        """卖出"""
        fee = self.position * price * self.fee_rate
        revenue = self.position * price - fee
        pnl = revenue - (self.buy_price * self.position)
        
        self.capital = revenue
        self.position = 0
        self.buy_price = 0
        
        trade = Trade(
            timestamp=timestamp,
            action='sell',
            price=price,
            quantity=self.position,
            fee=fee,
            pnl=pnl
        )
        self.trades.append(trade)
        
        logger.info(f"🔴 卖出 | 价格: ${price:,.2f} | PnL: ${pnl:.2f}")
        
    def _calculate_result(self) -> BacktestResult:
        """计算回测结果"""
        result = BacktestResult()
        
        sells = [t for t in self.trades if t.action == 'sell']
        result.total_trades = len(sells)
        result.winning_trades = len([t for t in sells if t.pnl > 0])
        result.losing_trades = len([t for t in sells if t.pnl < 0])
        result.total_pnl = sum(t.pnl for t in sells)
        
        # 最大回撤
        peak = self.initial_capital
        for equity in self.equity_curve:
            if equity > peak:
                peak = equity
            drawdown = (peak - equity) / peak * 100
            if drawdown > result.max_drawdown:
                result.max_drawdown = drawdown
                
        result.trades = sells
        result.calculate()
        
        return result
        
    def _save_result(self, result: BacktestResult):
        """保存结果到 Redis"""
        data = {
            'timestamp': int(datetime.now().timestamp() * 1000),
            'initial_capital': self.initial_capital,
            'total_trades': result.total_trades,
            'win_rate': round(result.win_rate, 2),
            'total_pnl': round(result.total_pnl, 2),
            'max_drawdown': round(result.max_drawdown, 2),
            'profit_factor': round(result.profit_factor, 2),
        }
        
        self.redis_client.xadd('backtest:results', data, maxlen=100)
        logger.info(f"💾 回测结果已保存到 Redis")


# 示例策略
def example_strategy(kline: Dict, bt: Backtester) -> Optional[str]:
    """示例：简单均线交叉策略"""
    # 需要访问历史数据，这里简化为演示
    # 实际使用时应该维护自己的指标实例
    
    close = kline['close']
    
    # 示例逻辑：价格 > 均线买入，< 均线卖出
    # 实际应该使用 indicators 模块
    
    if bt.position == 0 and close > 50000:
        return 'buy'
    elif bt.position > 0 and close < 50000:
        return 'sell'
        
    return None


def run_backtest_example():
    """运行示例回测"""
    bt = Backtester(initial_capital=10000)
    
    # 加载数据
    data = bt.load_historical_data()
    
    if not data:
        print("没有足够的数据进行回测")
        return
        
    # 运行回测
    result = bt.run(data, example_strategy)
    
    # 打印结果
    print("\n" + "="*50)
    print("📊 回测结果")
    print("="*50)
    print(f"总交易次数: {result.total_trades}")
    print(f"盈利交易: {result.winning_trades}")
    print(f"亏损交易: {result.losing_trades}")
    print(f"胜率: {result.win_rate:.2f}%")
    print(f"总盈亏: ${result.total_pnl:.2f}")
    print(f"最大回撤: {result.max_drawdown:.2f}%")
    print(f"盈亏比: {result.profit_factor:.2f}")
    print("="*50)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    run_backtest_example()
