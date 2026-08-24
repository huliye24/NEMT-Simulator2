#!/usr/bin/env python3
"""Debug the actual NotionClient.get_blocks call"""
import os
import sys
import json
import time
import hashlib
import requests
from typing import Dict, List, Optional, Any

sys.stdout.reconfigure(encoding='utf-8')

NOTION_TOKEN = open('/root/quant-sync-server/.env').read().strip().split('=')[1]
NOTION_API_BASE = "https://api.notion.com/v1"
NOTION_VERSION = "2022-06-28"
ROOT_PAGE_ID = "34317dca0dd280c9b1b4f1f0bbe7832c"

class NotionClient:
    def __init__(self, token: str):
        self.token = token
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Notion-Version": NOTION_VERSION,
            "Content-Type": "application/json"
        }
    
    def _request(self, method: str, endpoint: str, data=None, params=None) -> Dict:
        url = f"{NOTION_API_BASE}/{endpoint}"
        try:
            if method == "POST":
                resp = requests.post(url, headers=self.headers, json=data or {}, params=params, timeout=30)
            elif method == "GET":
                resp = requests.get(url, headers=self.headers, params=params, timeout=30)
            elif method == "PATCH":
                resp = requests.patch(url, headers=self.headers, json=data, params=params, timeout=30)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            if resp.status_code >= 400:
                return {"error": resp.text}
            return resp.json()
        except Exception as e:
            return {"error": str(e)}
    
    def get_page(self, page_id: str) -> Dict:
        return self._request("GET", f"pages/{page_id}")
    
    def get_blocks(self, block_id: str, page_size: int = 100) -> List[Dict]:
        blocks = []
        cursor = None
        
        while True:
            params = {"page_size": page_size}
            if cursor:
                params["start_cursor"] = cursor
            
            print(f"    _request GET blocks/{block_id}/children params={params}")
            result = self._request("GET", f"blocks/{block_id}/children", params=params)
            
            if "error" in result:
                print(f"    ERROR: {result['error'][:200]}")
                break
            
            items = result.get("results", [])
            print(f"    Got {len(items)} blocks, has_more={result.get('has_more')}, next_cursor={result.get('next_cursor')}")
            blocks.extend(items)
            
            if not result.get("has_more"):
                print(f"    No more pages")
                break
            
            cursor = result.get("next_cursor")
            if not cursor:
                print(f"    No cursor, breaking")
                break
            
            time.sleep(0.1)
        
        return blocks

client = NotionClient(NOTION_TOKEN)

# Test: call get_page_children_ids using the actual NotionClient
print("=" * 60)
print("Testing NotionClient.get_blocks")
print("=" * 60)

print("\nCalling get_blocks on root page...")
blocks = client.get_blocks(ROOT_PAGE_ID)
print(f"\nTotal blocks returned: {len(blocks)}")

child_ids = []
for block in blocks:
    block_type = block.get("type")
    if block_type in ("child_page", "child_database"):
        child_id = block.get(block_type, {}).get("id")
        if child_id:
            child_ids.append(child_id)

print(f"Child IDs found: {len(child_ids)}")
for cid in child_ids[:5]:
    print(f"  - {cid}")

# Now call get_page on first child
if child_ids:
    print(f"\nGetting first child page: {child_ids[0]}")
    page = client.get_page(child_ids[0])
    title = ""
    for key, val in page.get("properties", {}).items():
        if val.get("type") == "title":
            title = "".join(t.get("plain_text", "") for t in val.get("title", []))
    print(f"  Title: {title}")
    
    # Get its blocks
    child_blocks = client.get_blocks(child_ids[0])
    print(f"  Blocks: {len(child_blocks)}")
    sub_children = [b for b in child_blocks if b.get('type') in ('child_page', 'child_database')]
    print(f"  Sub-children: {len(sub_children)}")
