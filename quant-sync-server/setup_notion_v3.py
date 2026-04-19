#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Notion 数据库创建脚本 v3
=======================
使用 NEMT 寒鸦行动页面作为父页面
"""

import os
import sys
import json
import requests

# Fix encoding
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

NOTION_TOKEN = "ntn_s640536110656ijG4LStAQzrntOjxNtIhVajRcYSh68eWt"
NOTION_VERSION = "2022-06-28"
BASE_URL = "https://api.notion.com/v1"

# NEMT 寒鸦行动页面 ID
PARENT_PAGE_ID = "34317dca-0dd2-80c9-b1b4-f1f0bbe7832c"

def notion_headers():
    return {
        'Authorization': f'Bearer {NOTION_TOKEN}',
        'Content-Type': 'application/json',
        'Notion-Version': NOTION_VERSION,
    }

def create_database(parent_id, title, properties):
    """创建 Notion 数据库"""
    url = f"{BASE_URL}/databases"
    
    payload = {
        "parent": {"page_id": parent_id},
        "title": [{"type": "text", "text": {"content": title}}],
        "properties": properties
    }
    
    response = requests.post(url, headers=notion_headers(), json=payload)
    
    if response.status_code == 200:
        data = response.json()
        db_id = data['id'].replace('-', '')
        url_id = db_id.replace(' ', '')
        print(f"[OK] Created: {title}")
        print(f"     ID: {db_id}")
        print(f"     URL: https://notion.so/{url_id}")
        return db_id
    else:
        print(f"[FAIL] Create {title}: {response.status_code}")
        print(f"       {response.text[:300]}")
        return None

def update_env(strategy_db, backtest_db, signal_db):
    """更新 .env 文件"""
    content = f"""# NEMT Quant Sync Configuration
# ================================

NOTION_TOKEN={NOTION_TOKEN}

# Database IDs
NOTION_STRATEGY_DB={strategy_db}
NOTION_BACKTEST_DB={backtest_db}
NOTION_SIGNAL_DB={signal_db}

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# Go Server
GO_SERVER_URL=http://localhost:8081
"""
    with open('.env', 'w') as f:
        f.write(content)
    print(f"\n[OK] Updated .env file")

def main():
    print("""
============================================================
       Notion Database Setup v3
       Parent: NEMT 寒鸦行动
============================================================
    """)
    
    # 策略数据库
    strategy_props = {
        "Name": {"title": {}},
        "Description": {"rich_text": {}},
        "Alpha": {"number": {"format": "number"}},
        "Beta": {"number": {"format": "number"}},
        "Noise": {"number": {"format": "number"}},
        "DT": {"number": {"format": "number"}},
        "DX": {"number": {"format": "number"}},
        "Steps": {"number": {"format": "number"}},
        "N": {"number": {"format": "number"}},
        "DataSource": {"select": {"options": [{"name": "BTCUSDT"}, {"name": "ETHUSDT"}]}},
        "Interval": {"select": {"options": [{"name": "1m"}, {"name": "5m"}, {"name": "15m"}, {"name": "1h"}, {"name": "4h"}, {"name": "1d"}]}},
        "Enabled": {"checkbox": {}},
        "Tags": {"multi_select": {}},
    }
    
    # 回测数据库
    backtest_props = {
        "Name": {"title": {}},
        "Strategy": {"rich_text": {}},
        "TotalTrades": {"number": {"format": "number"}},
        "WinRate": {"number": {"format": "percent"}},
        "TotalPnL": {"number": {"format": "dollar"}},
        "MaxDrawdown": {"number": {"format": "percent"}},
        "ProfitFactor": {"number": {"format": "number"}},
        "SharpeRatio": {"number": {"format": "number"}},
        "SpectralWidth": {"number": {"format": "number"}},
        "MeanFrequency": {"number": {"format": "number"}},
        "ResonancePeaks": {"number": {"format": "number"}},
        "ExecutionTime": {"number": {"format": "number"}},
        "Status": {"select": {"options": [{"name": "Running"}, {"name": "Completed"}, {"name": "Failed"}]}},
    }
    
    # 信号数据库
    signal_props = {
        "Name": {"title": {}},
        "Symbol": {"select": {"options": [{"name": "BTCUSDT"}, {"name": "ETHUSDT"}]}},
        "Action": {"select": {"options": [{"name": "Buy"}, {"name": "Sell"}, {"name": "Hold"}, {"name": "Close"}]}},
        "Price": {"number": {"format": "dollar"}},
        "Confidence": {"number": {"format": "percent"}},
        "Phase": {"select": {"options": [{"name": "A"}, {"name": "B"}, {"name": "C"}, {"name": "D"}]}},
        "Direction": {"select": {"options": [{"name": "Bullish"}, {"name": "Bearish"}, {"name": "Neutral"}]}},
        "Reason": {"rich_text": {}},
        "DCI": {"number": {"format": "number"}},
        "SpectralWidth": {"number": {"format": "number"}},
        "VortexMaturity": {"number": {"format": "number"}},
        "ResonanceConfidence": {"number": {"format": "percent"}},
        "Status": {"select": {"options": [{"name": "Pending"}, {"name": "Sent"}, {"name": "Executed"}, {"name": "Cancelled"}]}},
    }
    
    print("[INFO] Creating databases...")
    
    strategy_db = create_database(PARENT_PAGE_ID, "Strategy DB", strategy_props)
    backtest_db = create_database(PARENT_PAGE_ID, "Backtest DB", backtest_props)
    signal_db = create_database(PARENT_PAGE_ID, "Signal DB", signal_props)
    
    if all([strategy_db, backtest_db, signal_db]):
        update_env(strategy_db, backtest_db, signal_db)
        print("""
============================================================
 Setup Complete!
============================================================

Database URLs:
  - Strategy DB: https://notion.so/""" + strategy_db.replace('-', '') + """
  - Backtest DB: https://notion.so/""" + backtest_db.replace('-', '') + """
  - Signal DB:   https://notion.so/""" + signal_db.replace('-', '') + """

Now test with real Notion:
  python test_notion_real.py
        """)
    else:
        print("[FAIL] Some databases failed to create")

if __name__ == "__main__":
    main()