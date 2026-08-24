#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Notion 数据库创建脚本
====================
自动创建 NEMT 项目所需的三个数据库

使用前：
1. 确保设置了 NOTION_TOKEN 环境变量
2. 或者直接填入下方的 NOTION_TOKEN

创建后会将数据库 ID 输出到 .env 文件
"""

import os
import sys
import json
import requests

# Fix encoding
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# ============ 配置 ============
NOTION_TOKEN = os.environ.get("NOTION_TOKEN", "")
NOTION_VERSION = "2022-06-28"

# 如果没有环境变量，尝试读取 .env 文件
if not NOTION_TOKEN:
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                if line.strip().startswith('NOTION_TOKEN='):
                    NOTION_TOKEN = line.split('=', 1)[1].strip()
                    break

BASE_URL = "https://api.notion.com/v1"

def print_section(title):
    print("\n" + "=" * 60)
    print(f" {title}")
    print("=" * 60)

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
        print(f"[OK] Created: {title}")
        print(f"     ID: {db_id}")
        return db_id
    else:
        print(f"[FAIL] Create {title}: {response.status_code}")
        print(f"       {response.text[:200]}")
        return None

def update_env_file(strategy_db, backtest_db, signal_db):
    """更新 .env 文件"""
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    token_line = f"NOTION_TOKEN={NOTION_TOKEN}\n" if NOTION_TOKEN else ""
    
    content = f"""# NEMT Quant Sync Configuration
# ================================

{token_line}NOTION_STRATEGY_DB={strategy_db}
NOTION_BACKTEST_DB={backtest_db}
NOTION_SIGNAL_DB={signal_db}

# Redis (for signal distribution)
REDIS_HOST=localhost
REDIS_PORT=6379

# Go Server (for signal execution)
GO_SERVER_URL=http://localhost:8081
"""
    
    with open(env_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"\n[OK] Updated .env file: {env_path}")

def create_parent_page():
    """创建父级页面"""
    url = f"{BASE_URL}/pages"
    
    payload = {
        "parent": {"type": "workspace", "workspace": True},
        "properties": {
            "title": {
                "title": [{"type": "text", "text": {"content": "NEMT Quant Dashboard"}}]
            }
        }
    }
    
    response = requests.post(url, headers=notion_headers(), json=payload)
    
    if response.status_code == 200:
        data = response.json()
        page_id = data['id']
        print(f"[OK] Created parent page: NEMT Quant Dashboard")
        print(f"     URL: https://notion.so/{page_id.replace('-', '')}")
        return page_id
    else:
        print(f"[FAIL] Create parent page: {response.status_code}")
        return None

def main():
    print("""
============================================================
       Notion Database Setup Script
============================================================
    """)
    
    # 检查 Token
    if not NOTION_TOKEN:
        print("[WARN] NOTION_TOKEN not set")
        print("")
        print("Please set your Notion token:")
        print("  1. Go to https://www.notion.so/my-integrations")
        print("  2. Create a new integration")
        print("  3. Copy the Internal Integration Secret")
        print("")
        print("Then run:")
        print("  export NOTION_TOKEN=secret_xxx")
        print("  python setup_notion_databases.py")
        print("")
        
        # 创建示例 .env 文件
        print("[INFO] Creating sample .env file...")
        with open('.env.example', 'w') as f:
            f.write("""# NEMT Quant Sync Configuration
# ================================

# Your Notion Integration Token
NOTION_TOKEN=secret_your_token_here

# Database IDs (will be filled after creation)
NOTION_STRATEGY_DB=your_strategy_db_id
NOTION_BACKTEST_DB=your_backtest_db_id
NOTION_SIGNAL_DB=your_signal_db_id

# Redis (for signal distribution)
REDIS_HOST=localhost
REDIS_PORT=6379

# Go Server (for signal execution)
GO_SERVER_URL=http://localhost:8081
""")
        print("[OK] Created .env.example")
        return
    
    print(f"[OK] Notion Token found")
    
    # 创建父级页面
    print_section("Create Parent Page")
    parent_id = create_parent_page()
    
    if not parent_id:
        print("[FAIL] Cannot create parent page. Check your token permissions.")
        return
    
    # 创建三个数据库
    print_section("Create Databases")
    
    # 1. 策略数据库
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
        "CreatedAt": {"created_time": {}},
    }
    
    # 2. 回测数据库
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
    
    # 3. 信号数据库
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
    
    strategy_db = create_database(parent_id, "Strategy DB", strategy_props)
    backtest_db = create_database(parent_id, "Backtest DB", backtest_props)
    signal_db = create_database(parent_id, "Signal DB", signal_props)
    
    # 更新 .env
    print_section("Update .env")
    
    if strategy_db and backtest_db and signal_db:
        update_env_file(strategy_db, backtest_db, signal_db)
    else:
        print("[WARN] Some databases failed to create")
        print("Please update .env manually with the created database IDs")
    
    print("""
============================================================
 Setup Complete!
============================================================

Next steps:
1. Open the parent page in Notion and share it with your integration
2. Update .env with the database IDs
3. Test reading/writing: python test_notion.py

For testing in browser:
1. cd web && npm run dev
2. Open http://localhost:5173
3. Click "Run Full Pipeline" with real Notion integration
    """)

if __name__ == "__main__":
    main()