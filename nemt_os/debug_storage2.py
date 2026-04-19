"""Debug storage issue - detailed"""
import sqlite3
from datetime import datetime
import sys
sys.path.insert(0, '.')

# Direct test
print("=== Direct SQLite test ===")
db_path = ':memory:'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Create table
cursor.execute("""
    CREATE TABLE IF NOT EXISTS klines (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        symbol TEXT NOT NULL,
        interval TEXT NOT NULL,
        timestamp TEXT NOT NULL,
        open REAL NOT NULL,
        high REAL NOT NULL,
        low REAL NOT NULL,
        close REAL NOT NULL,
        volume REAL NOT NULL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
""")
conn.commit()

# Check tables
tables = cursor.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
table_names = [t[0] for t in tables]
print(f"After create - tables: {table_names}")

# Insert data
cursor.execute("""
    INSERT OR REPLACE INTO klines (symbol, interval, timestamp, open, high, low, close, volume)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
""", ('BTCUSDT', '1h', datetime.now().isoformat(), 67000, 67100, 66900, 67050, 12345))
conn.commit()
print(f"After insert - rowcount: {cursor.rowcount}")

# Query
result = cursor.execute('SELECT * FROM klines').fetchall()
print(f"Query result: {len(result)} rows")

conn.close()
print("Direct test PASSED")

print()
print("=== Using nemt.storage ===")
from nemt.storage.sqlite_storage import SQLiteStorage

storage = SQLiteStorage(':memory:')
print("Storage created")

with storage._get_connection() as conn:
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    table_names = [t[0] for t in tables]
    print(f"Tables after init: {table_names}")

# Now try to save klines
from nemt.market_providers.base import KLine

klines = [
    KLine(
        timestamp=datetime.now(),
        open=67000,
        high=67100,
        low=66900,
        close=67050,
        volume=12345,
        symbol='BTCUSDT',
        interval='1h'
    )
]

print(f"Trying to save {len(klines)} klines...")
try:
    count = storage.save_klines(klines)
    print(f"Saved {count} klines")
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()

print("Test complete")
