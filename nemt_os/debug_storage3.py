"""Debug storage issue - step by step"""
import sqlite3
from datetime import datetime
import sys
sys.path.insert(0, '.')

print("=== Debug step by step ===")

# Step 1: 直接创建 storage
from nemt.storage.sqlite_storage import SQLiteStorage

db_path = ':memory:'
print(f"Creating storage with path: {db_path}")

# Check what happens during init
class DebugSQLiteStorage(SQLiteStorage):
    def _init_tables(self):
        print(">>> _init_tables called")
        with self._get_connection() as conn:
            print(f">>> Connection established, db_path: {self.db_path}")
            cursor = conn.cursor()

            # 创建 K线数据表
            sql = """
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
            """
            print(f">>> Executing: {sql[:50]}...")
            cursor.execute(sql)
            conn.commit()

            # Check tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            print(f">>> Tables after CREATE: {[t[0] for t in tables]}")

        print(">>> _init_tables completed")

storage = DebugSQLiteStorage(db_path)

print()
print("=== Checking after init ===")
with storage._get_connection() as conn:
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print(f"Tables: {[t[0] for t in tables]}")

print("Done")
