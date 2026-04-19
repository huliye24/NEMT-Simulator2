"""Debug storage issue"""
from datetime import datetime
from nemt.storage import init_database
from nemt.market_providers.base import KLine

storage = init_database(':memory:')
print('[OK] Database initialized')

# Test save_klines
klines = []
for i in range(3):
    kline = KLine(
        timestamp=datetime.now(),
        open=67000 + i,
        high=67100 + i,
        low=66900 + i,
        close=67050 + i,
        volume=12345,
        symbol='BTCUSDT',
        interval='1h'
    )
    klines.append(kline)

print(f'Created {len(klines)} klines')
count = storage.save_klines(klines)
print(f'Saved {count} klines')

# Check tables
with storage._get_connection() as conn:
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print(f'Tables: {[t[0] for t in tables]}')

# Try to get klines
result = storage.get_klines('BTCUSDT', limit=5)
print(f'Retrieved {len(result)} klines')
