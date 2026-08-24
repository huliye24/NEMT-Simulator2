#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 2 Review - Sync to Obsidian
"""

import os
import sys
import requests
from datetime import datetime

# Fix encoding FIRST
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Load config
def load_env():
    env_path = os.path.join(os.path.dirname(__file__), 'obsidian.env')
    if os.path.exists(env_path):
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()

load_env()

OBSIDIAN_API_KEY = os.environ.get("OBSIDIAN_API_KEY", "")
OBSIDIAN_HOST = os.environ.get("OBSIDIAN_HOST", "127.0.0.1")
OBSIDIAN_PORT = os.environ.get("OBSIDIAN_PORT", "27124")
BASE_URL = f"https://{OBSIDIAN_HOST}:{OBSIDIAN_PORT}"


def get_headers():
    return {'Authorization': f'Bearer {OBSIDIAN_API_KEY}'}


def check_connection():
    try:
        response = requests.get(f"{BASE_URL}/vault/", headers=get_headers(), verify=False, timeout=5)
        return response.status_code == 200
    except:
        return False


def create_note(folder, filename, content):
    path = f"{folder}/{filename}.md" if folder else f"{filename}.md"
    try:
        response = requests.put(
            f"{BASE_URL}/vault/{path}",
            headers={'Authorization': f'Bearer {OBSIDIAN_API_KEY}'},
            data=content.encode('utf-8'),
            verify=False
        )
        # 200, 201, 204 都是成功状态码
        success = response.status_code in [200, 201, 204]
        status = "[OK]" if success else "[FAIL]"
        print(f"  {status} {path}")
        if not success:
            print(f"      Status: {response.status_code}, Response: {response.text[:200]}")
        return success
    except Exception as e:
        print(f"  [ERROR] {path}: {e}")
        return False


def create_folder(folder):
    try:
        response = requests.post(
            f"{BASE_URL}/vault/{folder}/",
            headers=get_headers(),
            verify=False
        )
        return response.status_code in [200, 201]
    except:
        return True


def generate_phase2_detail_note():
    content = """# Phase 2 Review - Data Layer

**Phase**: Kitchen Phase - Data Layer
**Completed**: """ + datetime.now().strftime('%Y-%m-%d %H:%M') + """
**Time**: ~2 hours
**Status**: PASS

---

## 1. Phase Goals

From NEMT_Quant_OS_Electron.md Phase 2:

- Market Data Abstraction Layer (BaseMarketProvider)
- KLine Data Structure
- Data Storage Layer (SQLite)
- Redis Event Bus
- Notion Adapter Skeleton
- Acceptance: Can display mock market data

---

## 2. Task List

| # | Task | Status | Output |
|---|------|--------|--------|
| 1 | Market Data Abstraction | DONE | nemt/market_providers/base.py |
| 2 | Mock Market Provider | DONE | nemt/market_providers/mock_provider.py |
| 3 | SQLite Storage | DONE | nemt/storage/sqlite_storage.py |
| 4 | Redis Event Bus | DONE | nemt/event_bus/event_bus.py |
| 5 | Notion Adapter | DONE | nemt/adapters/notion/notion_adapter.py |
| 6 | Frontend Market Service | DONE | web/src/services/marketService.ts |
| 7 | Frontend Market Panel | DONE | web/src/components/MarketPanel.tsx |
| 8 | Acceptance Tests | DONE | nemt_os/tests/test_phase2.py |

---

## 3. Architecture Design

### 3.1 Market Data Abstraction Layer

BaseMarketProvider abstract base class:
- connect() - Connect to data source
- get_latest() - Get latest KLine
- get_history() - Get historical KLines
- get_ticker() - Get real-time ticker

### 3.2 Mock Data Provider

Supported symbols: BTCUSDT, ETHUSDT, BNBUSDT, SOLUSDT

Default price config, supports real-time mock data stream

### 3.3 SQLite Storage Architecture

Tables:
- klines - KLine data
- strategies - Strategy config
- backtests - Backtest results
- signals - Signal history
- system_config - System config

### 3.4 Event Bus Design

Event types:
- market.tick
- signal.generated
- strategy.created
- backtest.completed
- system.status

Optional Redis Pub/Sub integration

---

## 4. Problems Solved

### 4.1 SQLite Memory Database Issue

Problem: OperationalError: no such table: klines

Cause: SQLite :memory: creates independent instance per connection

Solution: Use shared connection mode

```python
if db_path == ':memory:':
    self._shared_conn = sqlite3.connect(':memory:', check_same_thread=False)
```

### 4.2 KLine Timestamp Unique Constraint Conflict

Problem: All KLines using same timestamp caused constraint conflict

Solution: Use different timestamps with timedelta

---

## 5. Acceptance Test Results

```
[PASS] Market Provider - OK
[PASS] Data Storage - OK
[PASS] Event Bus - OK
[PASS] Notion Adapter - OK
```

Phase 2 Acceptance Tests: ALL PASSED

---

## 6. New Files

```
nemt_os/
├── nemt/
│   ├── market_providers/
│   │   ├── __init__.py
│   │   ├── base.py (~180 lines)
│   │   └── mock_provider.py (~250 lines)
│   ├── storage/
│   │   ├── __init__.py
│   │   └── sqlite_storage.py (~580 lines)
│   ├── event_bus/
│   │   ├── __init__.py
│   │   └── event_bus.py (~250 lines)
│   └── adapters/notion/
│       ├── __init__.py
│       └── notion_adapter.py (~350 lines)
├── tests/
│   └── test_phase2.py (~200 lines)

web/src/
├── services/
│   └── marketService.ts (~280 lines)
└── components/
    └── MarketPanel.tsx (~350 lines)
```

Total: ~2,440 lines of new code

---

## 7. Frontend Integration

### 7.1 Market Panel Component

- Real-time price display
- Symbol switching
- 24h market data

### 7.2 Navigation Update

Added "Market Data" tab

---

## 8. Next Phase (Phase 3)

Phase 3: Chef Phase - NEMT Core

Tasks:
- Implement NLS equation
- Implement Four-Phase Detection
- Implement Spectral Analysis
- Implement Signal Generation
- Acceptance: NEMT Core can output valid signals

Estimated time: ~15-20 hours

---

## 9. Key Decisions

| Decision | Choice | Reason |
|----------|---------|--------|
| Data Source Abstraction | Provider Pattern | Supports multi-source switching |
| Storage Solution | SQLite | Lightweight, no dependencies |
| Event Communication | Local+Redis Optional | Dev-friendly, prod-scalable |
| Mock Strategy | Deterministic+Random | Test & demo |

---

## 10. Lessons Learned

### What Went Well
1. Interface-first design - Define abstract base class first
2. Mock-first - Avoid external dependencies
3. Test-driven - Acceptance tests ensure correctness

### Can Improve
1. Debugging - Should use simple script to locate issues first
2. Test data - Consider using time series generator
3. Error handling - Add more edge case tests

---

Next: Phase 3 - NEMT Core Implementation
"""

    return content


def generate_worklog_entry():
    content = """# Phase 2 Work Log

**Date**: """ + datetime.now().strftime('%Y-%m-%d') + """
**Phase**: Phase 2 - Data Layer
**Time**: ~2 hours

## Completed Tasks

- [x] Market Data Abstraction Layer (BaseMarketProvider + Mock)
- [x] KLine Data Structure
- [x] SQLite Data Storage
- [x] Redis Event Bus
- [x] Notion Adapter Skeleton
- [x] Frontend Market Service and Panel
- [x] All Acceptance Tests Passed

## Key Metrics

| Metric | Value |
|--------|-------|
| New Code Lines | ~2,440 |
| New Files | 8 |
| Test Cases | All Passed |
| Modules Covered | 4/5 |

## Problems Encountered

1. SQLite memory database connection issue - SOLVED
2. KLine timestamp unique constraint conflict - SOLVED

## Next Steps

Phase 3: NEMT Core Implementation
- NLS equation
- Four-phase detection
- Spectral analysis
- Signal generation

## Review Date

""" + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + """

---

## Detailed Problems

### Problem 1: SQLite Memory Database

**Error**: `sqlite3.OperationalError: no such table: klines`

**Root Cause**: SQLite's `:memory:` database creates a new independent database instance for each new connection. Tables created in one connection are not visible in other connections.

**Solution**: Use a shared connection pattern:

```python
def __init__(self, db_path: str = "data/nemt_storage.db"):
    self.db_path = db_path
    
    if db_path == ':memory:':
        self._shared_conn = sqlite3.connect(':memory:', check_same_thread=False)
        self._shared_conn.row_factory = sqlite3.Row
    else:
        self._shared_conn = None
    
    self._init_tables()
```

### Problem 2: KLine Timestamp Constraint

**Error**: Only 1 KLine saved instead of 10

**Root Cause**: All KLines in the test used the same timestamp (`datetime.now()`), which violated the `UNIQUE(symbol, interval, timestamp)` constraint.

**Solution**: Add time intervals between KLines:

```python
from datetime import timedelta
base_time = datetime.now()
klines = []
for i in range(10):
    kline = KLine(
        timestamp=base_time - timedelta(seconds=10 * (10 - i)),
        ...
    )
    klines.append(kline)
```
"""

    return content


def main():
    print("=" * 60)
    print("Phase 2 Review - Sync to Obsidian")
    print("=" * 60)
    print("")

    if not OBSIDIAN_API_KEY or OBSIDIAN_API_KEY == "your-obsidian-api-key-here":
        print("[ERROR] OBSIDIAN_API_KEY not configured!")
        print("Please edit obsidian.env")
        return

    print("[INFO] Target: NEMT-Simulator Vault")

    if not check_connection():
        print("[ERROR] Cannot connect to Obsidian")
        print("Make sure Obsidian is running with Local REST API enabled")
        return

    # Create folders
    print("")
    print("[INFO] Creating folders...")
    create_folder("PhaseHistory")
    create_folder("WorkLog")

    # Sync notes
    print("")
    print("[INFO] Syncing notes...")

    create_note("PhaseHistory", "Phase2-DataLayer-Review", generate_phase2_detail_note())
    create_note("WorkLog", f"Phase2-{datetime.now().strftime('%Y-%m-%d')}", generate_worklog_entry())

    print("")
    print("=" * 60)
    print("Phase 2 Review synced to Obsidian!")
    print("=" * 60)


if __name__ == "__main__":
    main()
