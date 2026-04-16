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
Redis 数据订阅器 & 信号生成器
"""
import os
import json
import time
import logging
from typing import Optional
import redis
from indicators import RSI, MACD, BollingerBands, SMA

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)


class RedisSubscriber:
    """订阅 Redis Stream 中的 K线数据"""
    
    def __init__(self, redis_host: str = None, redis_port: int = 6379):
        self.redis_host = redis_host or os.getenv('REDIS_HOST', 'redis')
        self.redis_port = redis_port
        
        self.client = redis.Redis(
            host=self.redis_host,
            port=self.redis_port,
            decode_responses=True
        )
        
        # 指标实例
        self.rsi = RSI(period=14)
        self.macd = MACD(fast=12, slow=26, signal=9)
        self.bb = BollingerBands(period=20, std_dev=2)
        self.sma_fast = SMA(period=5)
        self.sma_slow = SMA(period=20)
        
        self.last_signal_time = 0
        self.signal_cooldown = 60  # 信号冷却时间（秒）
        
    def connect(self) -> bool:
        """测试 Redis 连接"""
        try:
            self.client.ping()
            logger.info(f"✅ Redis 连接成功: {self.redis_host}:{self.redis_port}")
            return True
        except redis.ConnectionError as e:
            logger.error(f"❌ Redis 连接失败: {e}")
            return False
            
    def subscribe_klines(self, symbol: str = 'BTCUSDT', interval: str = '1m'):
        """订阅 K线 Stream"""
        stream_key = f"kline:{symbol}:{interval}"
        
        logger.info(f"📡 开始订阅: {stream_key}")
        
        last_id = '0'  # 从最新开始
        
        while True:
            try:
                # 阻塞读取新数据
                result = self.client.xread({stream_key: last_id}, count=1, block=2000)
                
                if not result:
                    continue
                    
                for stream, messages in result:
                    for msg_id, data in messages:
                        last_id = msg_id
                        
                        # 解析数据
                        kline_data = {
                            'symbol': data.get('symbol'),
                            'interval': data.get('interval'),
                            'open': float(data.get('open', 0)),
                            'high': float(data.get('high', 0)),
                            'low': float(data.get('low', 0)),
                            'close': float(data.get('close', 0)),
                            'volume': float(data.get('volume', 0)),
                            'close_time': data.get('close_time'),
                        }
                        
                        # 计算指标
                        self._calculate_indicators(kline_data)
                        
    def _calculate_indicators(self, data: dict):
        """计算所有指标并生成信号"""
        close = data['close']
        
        # 更新各指标
        rsi_value = self.rsi.update(close)
        macd_result = self.macd.update(close)
        bb_result = self.bb.update(close)
        sma_f = self.sma_fast.update(close)
        sma_s = self.sma_slow.update(close)
        
        # 生成综合信号
        signals = []
        
        # RSI 信号
        rsi_signal = self.rsi.get_signal()
        if rsi_signal != 'neutral':
            signals.append(('RSI', rsi_signal, rsi_value))
            
        # MACD 信号
        macd_signal = self.macd.get_signal()
        if macd_signal != 'neutral':
            signals.append(('MACD', macd_signal, macd_result))
            
        # 均线交叉信号
        if sma_f and sma_s:
            if len(self.sma_fast.values) > 1 and len(self.sma_slow.values) > 1:
                prev_f = self.sma_fast.values[-2]
                prev_s = self.sma_slow.values[-2]
                curr_f = sma_f
                curr_s = sma_s
                
                # 金叉
                if prev_f <= prev_s and curr_f > curr_s:
                    signals.append(('MA', 'golden_cross', f'{sma_f}/{sma_s}'))
                # 死叉
                elif prev_f >= prev_s and curr_f < curr_s:
                    signals.append(('MA', 'death_cross', f'{sma_f}/{sma_s}'))
        
        # 布林带信号
        if bb_result:
            bb_signal = self.bb.get_position(close)
            if bb_signal in ['above_upper', 'below_lower']:
                signals.append(('BB', bb_signal, bb_result))
        
        # 打印状态和信号
        self._print_status(data, rsi_value, macd_result, bb_result, sma_f, sma_s)
        
        # 发送信号
        if signals:
            self._emit_signals(data, signals)
            
    def _print_status(self, data: dict, rsi, macd, bb, sma_f, sma_s):
        """打印当前状态"""
        symbol = data['symbol']
        close = data['close']
        
        status = f"📊 {symbol} | ${close:,.2f}"
        
        if rsi:
            status += f" | RSI: {rsi:.1f}"
        if macd:
            status += f" | MACD: {macd[0]:.4f}"
        if sma_f and sma_s:
            status += f" | SMA: {sma_f:.2f}/{sma_s:.2f}"
            
        print(status)
        
    def _emit_signals(self, data: dict, signals: list):
        """发送信号到 Redis"""
        current_time = time.time()
        
        # 冷却检查
        if current_time - self.last_signal_time < self.signal_cooldown:
            return
            
        self.last_signal_time = current_time
        
        signal_data = {
            'symbol': data['symbol'],
            'price': data['close'],
            'signals': json.dumps(signals, ensure_ascii=False),
            'timestamp': int(current_time * 1000),
        }
        
        # 写入信号 Stream
        self.client.xadd('signals:stream', signal_data, maxlen=1000)
        
        # 打印信号
        logger.info(f"🚨 信号触发: {signals}")
        

def main():
    """主函数"""
    logger.info("═══════════════════════════════════════════════")
    logger.info("     📈 BTC 技术指标计算器 v1.0")
    logger.info("═══════════════════════════════════════════════")
    
    subscriber = RedisSubscriber()
    
    if not subscriber.connect():
        logger.error("无法连接到 Redis，退出")
        return
    
    try:
        subscriber.subscribe_klines('BTCUSDT', '1m')
    except KeyboardInterrupt:
        logger.info("🛑 收到退出信号")


if __name__ == '__main__':
    main()
