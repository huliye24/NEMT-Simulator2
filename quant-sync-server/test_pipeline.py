#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NEMT Pipeline Test Script
==========================
Test full Notion -> NEMT -> Signal -> Notion pipeline
"""

import os
import sys
import json
import time
import requests

# Fix encoding for Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Config
API_BASE_URL = "http://localhost:8080"
TEST_PRICES = [100 + i * 0.5 + 10 * (i % 10) for i in range(100)]

def print_section(title):
    print("\n" + "=" * 60)
    print(f" {title}")
    print("=" * 60)

def wait_for_server(max_wait=10):
    print(f"Waiting for API server ({API_BASE_URL})...")
    for i in range(max_wait):
        try:
            response = requests.get(f"{API_BASE_URL}/", timeout=2)
            if response.status_code == 200:
                print("[OK] API server ready")
                return True
        except:
            pass
        time.sleep(1)
        print(f"  Retry {i+1}/{max_wait}...")
    print("[FAIL] Cannot connect to API server")
    return False

def test_pipeline():
    print_section("Run Full Pipeline")
    
    print(f"Symbol: BTCUSDT")
    print(f"Price data: {len(TEST_PRICES)} points")
    print(f"Start: ${TEST_PRICES[0]:.2f}, End: ${TEST_PRICES[-1]:.2f}")
    
    payload = {
        "prices": TEST_PRICES,
        "symbol": "BTCUSDT"
    }
    
    print("\nSending request...")
    start = time.time()
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/pipeline/run",
            json=payload,
            timeout=30
        )
        elapsed = time.time() - start
        
        print(f"Response time: {elapsed:.2f}s")
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("[OK] Pipeline executed successfully!")
            
            # Print steps
            steps = result.get('steps', {})
            print("\n=== Steps ===")
            for name, data in steps.items():
                status = "OK" if data.get('success') else "FAIL"
                print(f"  [{status}] {name}")
            
            # Print logs
            logs = result.get('logs', [])
            print(f"\n=== Logs ({len(logs)} entries) ===")
            for log in logs:
                level = log.get('level', 'INFO')
                step = log.get('step', '')
                msg = log.get('message', '')
                icon = "[OK]" if level == "SUCCESS" else "[WARN]" if level == "WARNING" else "[ERR]" if level == "ERROR" else "[INFO]"
                print(f"  {icon} [{step}] {msg}")
            
            return result
        else:
            print(f"[FAIL] Pipeline failed: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"[ERR] Request exception: {e}")
        return None

def main():
    print("""
============================================================
       NEMT Pipeline Test Script
============================================================
    """)
    
    if not wait_for_server():
        print("\nPlease start the server first:")
        print("  python quant-sync-server/api_server.py --port 8080")
        sys.exit(1)
    
    result = test_pipeline()
    
    if result and result.get('success'):
        print("\n" + "=" * 60)
        print(" V6 CLOSED LOOP VERIFIED!")
        print("=" * 60)
        print("""
Steps completed:
  [OK] Notion read strategy params
  [OK] NEMT analysis (spectrum + phase)
  [OK] Signal generation (DCI + vortex + resonance)
  [OK] Result write to Notion (mock mode)

To test with browser:
  1. cd web && npm run dev
  2. Open http://localhost:5173
  3. Click "Run Full Pipeline" button
  4. Check logs panel
        """)
    else:
        print("\n[FAIL] Pipeline execution failed")
        sys.exit(1)

if __name__ == "__main__":
    main()