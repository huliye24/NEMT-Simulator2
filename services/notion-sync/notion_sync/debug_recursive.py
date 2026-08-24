#!/usr/bin/env python3
"""直接测试递归同步"""
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

def get_page(page_id):
    resp = requests.get(f"{NOTION_API_BASE}/pages/{page_id}", headers=headers, timeout=30)
    return resp.json()

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
        print(f"    Fetched {len(results)} blocks, total {len(blocks)}, has_more={data.get('has_more')}, cursor={data.get('next_cursor')}")
        if not data.get("has_more"):
            break
        cursor = data.get("next_cursor")
        if not cursor:
            break
        time.sleep(0.1)
    return blocks

def get_page_children_ids(page_id):
    """获取页面的直接子页面 ID"""
    blocks = get_blocks(page_id)
    child_ids = []
    for block in blocks:
        block_type = block.get("type")
        if block_type in ("child_page", "child_database"):
            child_id = block.get(block_type, {}).get("id")
            if child_id:
                child_ids.append(child_id)
    return child_ids

def extract_title(page):
    props = page.get("properties", {})
    for key, val in props.items():
        if val.get("type") == "title":
            texts = val.get("title", [])
            if texts:
                return "".join(t.get("plain_text", "") for t in texts)
    return page.get("id", "Untitled")[:8]

def sync_page(page_id, parent_path="", depth=0):
    indent = "  " * depth
    print(f"{indent}[RECURSE depth={depth}] Syncing {page_id}")
    
    # Get page
    page = get_page(page_id)
    title = extract_title(page)
    print(f"{indent}  Title: {title}")
    
    # Get children
    child_ids = get_page_children_ids(page_id)
    print(f"{indent}  Children: {len(child_ids)}")
    
    # Show first few children
    for cid in child_ids[:3]:
        cpage = get_page(cid)
        ctitle = extract_title(cpage)
        print(f"{indent}    - {ctitle}")
    
    # Recurse
    for i, child_id in enumerate(child_ids):
        print(f"{indent}  Recursing into child {i+1}/{len(child_ids)}: {child_id}")
        sync_page(child_id, f"{parent_path}/{title}", depth + 1)
        time.sleep(0.1)
    
    return len(child_ids)

# Test with first 2 children of root
print("=" * 60)
print("测试递归同步")
print("=" * 60)

child_ids = get_page_children_ids(ROOT_PAGE_ID)
print(f"\nRoot has {len(child_ids)} children\n")

# Test first child
if child_ids:
    first_child = child_ids[0]
    page = get_page(first_child)
    title = extract_title(page)
    print(f"\nFirst child: {title}")
    grandchildren = get_page_children_ids(first_child)
    print(f"  Grandchildren: {len(grandchildren)}")
    
    # Test second child
    if len(child_ids) > 1:
        second_child = child_ids[1]
        page = get_page(second_child)
        title = extract_title(page)
        print(f"\nSecond child: {title}")
        grandchildren = get_page_children_ids(second_child)
        print(f"  Grandchildren: {len(grandchildren)}")
        for gid in grandchildren[:5]:
            gpage = get_page(gid)
            gtitle = extract_title(gpage)
            print(f"    - {gtitle}")

print("\n" + "=" * 60)
print("测试递归调用")
print("=" * 60)
sync_page(ROOT_PAGE_ID, OBSIDIAN_NEMT, 0)
