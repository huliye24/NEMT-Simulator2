#!/usr/bin/env python3
"""精确对比两个过滤方法"""
import os
import sys
import json
import time
import requests

sys.stdout.reconfigure(encoding='utf-8')

NOTION_TOKEN = open('/root/quant-sync-server/.env').read().strip().split('=')[1]
NOTION_VERSION = "2022-06-28"
NOTION_API_BASE = "https://api.notion.com/v1"
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

# Get all blocks
print("Getting blocks...")
blocks = get_blocks(ROOT_PAGE_ID)
print(f"Total blocks: {len(blocks)}")

# Method 1: Direct filter (worked in earlier debug)
child_pages_method1 = [b for b in blocks if b.get('type') == 'child_page']
print(f"\nMethod 1 (direct get type): {len(child_pages_method1)} child pages")
if child_pages_method1:
    print(f"  First: {child_pages_method1[0].get('child_page', {}).get('title')}")

# Method 2: Block type check
child_pages_method2 = []
for block in blocks:
    block_type = block.get("type")
    if block_type in ("child_page", "child_database"):
        child_id = block.get(block_type, {}).get("id")
        if child_id:
            child_pages_method2.append(block)
print(f"\nMethod 2 (block_type check): {len(child_pages_method2)} child pages")

# Check block types distribution
types = {}
for b in blocks:
    t = b.get("type", "N/A")
    types[t] = types.get(t, 0) + 1
print(f"\nBlock types distribution: {types}")

# Check if the child_page blocks look different
child_page_blocks = [b for b in blocks if b.get('type') == 'child_page']
if child_page_blocks:
    first = child_page_blocks[0]
    print(f"\nFirst child_page block keys: {list(first.keys())}")
    print(f"First child_page block['child_page']: {first.get('child_page')}")
    print(f"First child_page block id: {first.get('id')}")
