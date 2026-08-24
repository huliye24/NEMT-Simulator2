#!/usr/bin/env python3
"""带调试的同步脚本"""
import os
import sys
import json
import hashlib
import time
import requests

sys.stdout.reconfigure(encoding='utf-8')

NOTION_TOKEN = open('/root/quant-sync-server/.env').read().strip().split('=')[1]
NOTION_VERSION = "2022-06-28"
NOTION_API_BASE = "https://api.notion.com/v1"
OBSIDIAN_NEMT = "/root/obsidian_vault/NEMT_Notion"
ROOT_PAGE_ID = "34317dca0dd280c9b1b4f1f0bbe7832c"

headers = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Notion-Version": NOTION_VERSION,
}

def extract_title(page):
    props = page.get("properties", {})
    for key, val in props.items():
        if val.get("type") == "title":
            texts = val.get("title", [])
            if texts:
                return "".join(t.get("plain_text", "") for t in texts)
    return page.get("id", "Untitled")[:8]

def get_blocks(block_id):
    blocks = []
    cursor = None
    while True:
        params = {"page_size": 100}
        if cursor:
            params["start_cursor"] = cursor
        resp = requests.get(f"{NOTION_API_BASE}/blocks/{block_id}/children", headers=headers, params=params, timeout=30)
        data = resp.json()
        blocks.extend(data.get("results", []))
        if not data.get("has_more"):
            break
        cursor = data.get("next_cursor")
        if not cursor:
            break
        time.sleep(0.1)
    return blocks

def get_page(page_id):
    resp = requests.get(f"{NOTION_API_BASE}/pages/{page_id}", headers=headers, timeout=30)
    return resp.json()

# Test: Get root page children
print("=" * 60)
print("测试根页面子页面")
print("=" * 60)

blocks = get_blocks(ROOT_PAGE_ID)
print(f"Root blocks: {len(blocks)}")

child_pages = [b for b in blocks if b.get('type') == 'child_page']
print(f"Child pages: {len(child_pages)}")

# Get first child page
if child_pages:
    first_child = child_pages[0]
    child_id = first_child.get('id')
    child_title = first_child.get('child_page', {}).get('title', 'no title')
    print(f"\n获取第一个子页面: {child_title} ({child_id})")
    
    # Get page data
    page = get_page(child_id)
    print(f"Page title: {extract_title(page)}")
    
    # Get page blocks
    page_blocks = get_blocks(child_id)
    print(f"Page blocks: {len(page_blocks)}")
    
    # Check if page has child pages
    sub_children = [b for b in page_blocks if b.get('type') == 'child_page']
    print(f"Sub-children: {len(sub_children)}")
    for sc in sub_children[:3]:
        print(f"  - {sc.get('child_page', {}).get('title', 'no title')}")
