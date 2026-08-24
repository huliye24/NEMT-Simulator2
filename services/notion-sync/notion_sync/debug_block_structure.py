#!/usr/bin/env python3
"""Check exact block structure"""
import os
import sys
import time
import requests
from typing import Dict, List

sys.stdout.reconfigure(encoding='utf-8')

NOTION_TOKEN = open('/root/quant-sync-server/.env').read().strip().split('=')[1]
NOTION_API_BASE = "https://api.notion.com/v1"
NOTION_VERSION = "2022-06-28"
ROOT_PAGE_ID = "34317dca0dd280c9b1b4f1f0bbe7832c"

headers = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Notion-Version": NOTION_VERSION,
}

def get_blocks(block_id):
    blocks = []
    cursor = None
    while True:
        params = {"page_size": 100}
        if cursor:
            params["start_cursor"] = cursor
        resp = requests.get(f"{NOTION_API_BASE}/blocks/{block_id}/children", headers=headers, params=params, timeout=30)
        data = resp.json()
        results = data.get("results", [])
        blocks.extend(results)
        if not data.get("has_more"):
            break
        cursor = data.get("next_cursor")
        if not cursor:
            break
        time.sleep(0.1)
    return blocks

blocks = get_blocks(ROOT_PAGE_ID)
print(f"Total blocks: {len(blocks)}")

# Print first 5 blocks with all keys
for i, b in enumerate(blocks[:5]):
    print(f"\nBlock {i}:")
    print(f"  type value: {repr(b.get('type'))}")
    print(f"  type == 'child_page': {b.get('type') == 'child_page'}")
    print(f"  'type' in b: {'type' in b}")
    print(f"  keys: {list(b.keys())}")

# Check child_page blocks
child_page_blocks = [b for b in blocks if b.get('type') == 'child_page']
print(f"\nFiltered child_page blocks: {len(child_page_blocks)}")

# Try different filters
filter1 = [b for b in blocks if 'child_page' in b]
filter2 = [b for b in blocks if b.get('type') in ['child_page']]
filter3 = [b for b in blocks if "child_page" in str(b.get('type'))]
print(f"Filter 'child_page' in b: {len(filter1)}")
print(f"Filter type in list: {len(filter2)}")
print(f"Filter substring: {len(filter3)}")

# Check with ==
filter4 = [b for b in blocks if b['type'] == 'child_page']
print(f"Filter type == 'child_page': {len(filter4)}")
