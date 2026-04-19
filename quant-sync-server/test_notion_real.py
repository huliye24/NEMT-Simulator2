#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Notion 读写测试脚本
==================
测试策略读取和回测结果写入
"""

import os
import sys
import json
import time
import requests

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# 从 .env 加载配置
def load_env():
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    config = {}
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                if '=' in line:
                    key, val = line.strip().split('=', 1)
                    config[key] = val
    return config

config = load_env()
NOTION_TOKEN = config.get('NOTION_TOKEN', '')
STRATEGY_DB = config.get('NOTION_STRATEGY_DB', '')
BACKTEST_DB = config.get('NOTION_BACKTEST_DB', '')
SIGNAL_DB = config.get('NOTION_SIGNAL_DB', '')
NOTION_VERSION = "2022-06-28"
BASE_URL = "https://api.notion.com/v1"

def notion_headers():
    return {
        'Authorization': f'Bearer {NOTION_TOKEN}',
        'Content-Type': 'application/json',
        'Notion-Version': NOTION_VERSION,
    }

def print_section(title):
    print("\n" + "=" * 60)
    print(f" {title}")
    print("=" * 60)

def test_read_strategies():
    """测试读取策略列表"""
    print_section("1. Read Strategy DB")
    
    url = f"{BASE_URL}/databases/{STRATEGY_DB}/query"
    response = requests.post(url, headers=notion_headers(), json={})
    
    if response.status_code == 200:
        data = response.json()
        results = data.get('results', [])
        print(f"[OK] Found {len(results)} strategy entries")
        return True
    else:
        print(f"[FAIL] Query failed: {response.status_code}")
        return False

def test_create_strategy():
    """测试创建策略"""
    print_section("2. Create Strategy")
    
    url = f"{BASE_URL}/pages"
    payload = {
        "parent": {"database_id": STRATEGY_DB},
        "properties": {
            "Name": {
                "title": [{"text": {"content": "BTC Default Strategy"}}]
            },
            "Description": {
                "rich_text": [{"text": {"content": "Default NEMT strategy for BTC/USDT"}}]
            },
            "Alpha": {"number": 0.1},
            "Beta": {"number": 1.0},
            "Noise": {"number": 0.2},
            "DT": {"number": 0.01},
            "DX": {"number": 1.0},
            "Steps": {"number": 200},
            "N": {"number": 1000},
            "DataSource": {"select": {"name": "BTCUSDT"}},
            "Interval": {"select": {"name": "1m"}},
            "Enabled": {"checkbox": True},
            "Tags": {"multi_select": [{"name": "Default"}, {"name": "BTC"}]},
        }
    }
    
    response = requests.post(url, headers=notion_headers(), json=payload)
    
    if response.status_code == 200:
        data = response.json()
        page_id = data['id'].replace('-', '')
        print(f"[OK] Created strategy page")
        print(f"     ID: {page_id}")
        print(f"     URL: https://notion.so/{page_id}")
        return page_id
    else:
        print(f"[FAIL] Create failed: {response.status_code}")
        print(f"       {response.text[:200]}")
        return None

def test_create_backtest(strategy_name, strategy_page_id):
    """测试创建回测���果"""
    print_section("3. Create Backtest Result")
    
    url = f"{BASE_URL}/pages"
    payload = {
        "parent": {"database_id": BACKTEST_DB},
        "properties": {
            "Name": {
                "title": [{"text": {"content": f"Backtest {strategy_name} {time.strftime('%Y-%m-%d %H:%M')}"}}]
            },
            "Strategy": {
                "rich_text": [{"text": {"content": strategy_name}}]
            },
            "TotalTrades": {"number": 42},
            "WinRate": {"number": 0.65},
            "TotalPnL": {"number": 1250.50},
            "MaxDrawdown": {"number": 0.15},
            "ProfitFactor": {"number": 2.3},
            "SharpeRatio": {"number": 1.8},
            "SpectralWidth": {"number": 0.0234},
            "MeanFrequency": {"number": 0.1567},
            "ResonancePeaks": {"number": 3},
            "ExecutionTime": {"number": 1250},
            "Status": {"select": {"name": "Completed"}},
        }
    }
    
    response = requests.post(url, headers=notion_headers(), json=payload)
    
    if response.status_code == 200:
        data = response.json()
        page_id = data['id'].replace('-', '')
        print(f"[OK] Created backtest page")
        print(f"     ID: {page_id}")
        print(f"     URL: https://notion.so/{page_id}")
        return page_id
    else:
        print(f"[FAIL] Create failed: {response.status_code}")
        return None

def test_create_signal():
    """测试创建信号"""
    print_section("4. Create Trading Signal")
    
    url = f"{BASE_URL}/pages"
    payload = {
        "parent": {"database_id": SIGNAL_DB},
        "properties": {
            "Name": {
                "title": [{"text": {"content": f"BTC Signal {time.strftime('%H:%M:%S')}"}}]
            },
            "Symbol": {"select": {"name": "BTCUSDT"}},
            "Action": {"select": {"name": "Buy"}},
            "Price": {"number": 67500.00},
            "Confidence": {"number": 0.75},
            "Phase": {"select": {"name": "C"}},
            "Direction": {"select": {"name": "Bullish"}},
            "Reason": {
                "rich_text": [{"text": {"content": "Vortex maturity: 7.5/10, Resonance triggered"}}]
            },
            "DCI": {"number": 0.68},
            "SpectralWidth": {"number": 0.0234},
            "VortexMaturity": {"number": 7.5},
            "ResonanceConfidence": {"number": 0.65},
            "Status": {"select": {"name": "Pending"}},
        }
    }
    
    response = requests.post(url, headers=notion_headers(), json=payload)
    
    if response.status_code == 200:
        data = response.json()
        page_id = data['id'].replace('-', '')
        print(f"[OK] Created signal page")
        print(f"     ID: {page_id}")
        print(f"     URL: https://notion.so/{page_id}")
        return page_id
    else:
        print(f"[FAIL] Create failed: {response.status_code}")
        return None

def main():
    print("""
============================================================
       Notion Read/Write Test
============================================================
    """)
    
    print(f"[INFO] Using configuration:")
    print(f"       Strategy DB: {STRATEGY_DB[:20]}...")
    print(f"       Backtest DB:  {BACKTEST_DB[:20]}...")
    print(f"       Signal DB:    {SIGNAL_DB[:20]}...")
    
    # 1. 读取策略
    if not test_read_strategies():
        return
    
    # 2. 创建策略
    strategy_id = test_create_strategy()
    
    # 3. 创建回测结果
    if strategy_id:
        test_create_backtest("BTC Default Strategy", strategy_id)
    
    # 4. 创建信号
    test_create_signal()
    
    print("""
============================================================
 Test Complete!
============================================================

Check your Notion databases:
  - Strategy DB: https://notion.so/""" + STRATEGY_DB + """
  - Backtest DB:  https://notion.so/""" + BACKTEST_DB + """
  - Signal DB:    https://notion.so/""" + SIGNAL_DB + """

Now restart the API server and test in browser:
  python api_server.py --port 8080
    """)

if __name__ == "__main__":
    main()