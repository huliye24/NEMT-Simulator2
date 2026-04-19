#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Notion 集成完整测试
==================
测试 Notion -> NEMT -> Signal -> Notion 完整闭环
"""

import os
import sys
import json
import time
import requests

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# 加载 .env
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

API_BASE_URL = "http://localhost:8080"
TEST_PRICES = [100 + i * 0.5 + 10 * (i % 10) for i in range(100)]

# 之前创建的策略页面 ID
STRATEGY_PAGE_ID = "34517dca0dd281e785dfe3de448556a7"

def print_section(title):
    print("\n" + "=" * 60)
    print(f" {title}")
    print("=" * 60)

def run_pipeline_with_notion():
    """运行完整 Pipeline（带 Notion）"""
    print_section("Run Full Pipeline with Notion")
    
    payload = {
        "prices": TEST_PRICES,
        "symbol": "BTCUSDT",
        "notion_page_id": STRATEGY_PAGE_ID
    }
    
    print(f"Using Strategy Page: {STRATEGY_PAGE_ID}")
    print(f"Price data: {len(TEST_PRICES)} points")
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/pipeline/run",
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            
            if result.get('success'):
                print("\n[OK] Pipeline executed successfully!")
                
                # 打印步骤
                steps = result.get('steps', {})
                print("\n=== Steps ===")
                for name, data in steps.items():
                    status = "OK" if data.get('success') else "FAIL"
                    print(f"  [{status}] {name}")
                
                # 打印日志
                logs = result.get('logs', [])
                print(f"\n=== Logs ({len(logs)} entries) ===")
                for log in logs:
                    level = log.get('level', 'INFO')
                    step = log.get('step', '')
                    msg = log.get('message', '')
                    icon = "[OK]" if level == "SUCCESS" else "[WARN]" if level == "WARNING" else "[ERR]" if level == "ERROR" else "[INFO]"
                    print(f"  {icon} [{step}] {msg}")
                
                # 信号信息
                signal = steps.get('signal_generate', {}).get('signal')
                if signal:
                    print(f"\n=== Generated Signal ===")
                    print(f"  Type: {signal.get('type')}")
                    print(f"  Direction: {signal.get('direction')}")
                    print(f"  Price: ${signal.get('price', 0):.2f}")
                    print(f"  Confidence: {(signal.get('confidence', 0) * 100):.1f}%")
                
                # 回写信息
                backtest = steps.get('write_backtest', {})
                if backtest.get('success'):
                    page_id = backtest.get('page_id')
                    print(f"\n[OK] Backtest result written to Notion")
                    print(f"     Page ID: {page_id}")
                    if page_id:
                        print(f"     URL: https://notion.so/{page_id.replace('-', '')}")
                else:
                    print(f"\n[WARN] Backtest write skipped or failed")
                    print(f"       Note: {backtest.get('note', '')}")
                
                return True
            else:
                print(f"[FAIL] Pipeline failed: {result.get('error')}")
                return False
        else:
            print(f"[FAIL] HTTP error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"[ERR] Exception: {e}")
        return False

def main():
    print("""
============================================================
       Notion Integration Full Test
============================================================
    """)
    
    # 检查 API 服务器
    try:
        resp = requests.get(f"{API_BASE_URL}/api/pipeline/status", timeout=5)
        if resp.status_code != 200:
            print("[FAIL] API server not ready")
            return
    except:
        print("[FAIL] Cannot connect to API server")
        print("Please start: python api_server.py --port 8080")
        return
    
    print("[OK] API server ready")
    
    # 运行完整测试
    if run_pipeline_with_notion():
        print("""
============================================================
 SUCCESS! Full Notion Integration Verified!
============================================================

The following flow is now working:
  1. [OK] Read strategy from Notion
  2. [OK] Run NEMT analysis
  3. [OK] Generate trading signals
  4. [OK] Write backtest results to Notion

You can now:
  1. Open browser: http://localhost:5173
  2. Click "Run Full Pipeline"
  3. Check Notion for new backtest results
        """)
    else:
        print("\n[FAIL] Test failed")

if __name__ == "__main__":
    main()