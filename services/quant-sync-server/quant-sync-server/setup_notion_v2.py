#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Notion 数据库创建脚本 v2
=======================
使用用户指定的 Token 创建数据库
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
NOTION_TOKEN = "ntn_s640536110656ijG4LStAQzrntOjxNtIhVajRcYSh68eWt"
NOTION_VERSION = "2022-06-28"
BASE_URL = "https://api.notion.com/v1"

def notion_headers():
    return {
        'Authorization': f'Bearer {NOTION_TOKEN}',
        'Content-Type': 'application/json',
        'Notion-Version': NOTION_VERSION,
    }

def search_pages():
    """搜索现有的页面"""
    url = f"{BASE_URL}/search"
    payload = {
        "filter": {"property": "object", "value": "page"},
        "page_size": 10
    }
    response = requests.post(url, headers=notion_headers(), json=payload)
    if response.status_code == 200:
        return response.json().get('results', [])
    return []

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
        print(f"       {response.text[:300]}")
        return None

def main():
    print("""
============================================================
       Notion Database Setup Script v2
============================================================
    """)
    
    # 1. 搜索现有页面
    print("[INFO] Searching for existing pages...")
    pages = search_pages()
    
    if pages:
        print(f"[OK] Found {len(pages)} pages")
        for p in pages[:5]:
            title = "Untitled"
            if p.get('properties', {}).get('title', {}).get('title'):
                title = p['properties']['title']['title'][0]['plain_text']
            pid = p['id']
            print(f"     - {title} ({pid})")
    else:
        print("[WARN] No pages found")
    
    # 用户需要提供一个页面 ID 作为父页面
    # 由于无法直接创建 workspace 页面，我们需要用户手动提供
    print("""
============================================================
 Manual Setup Required
============================================================

Since the integration token doesn't have workspace-level 
access, you need to:

1. Create a new page in Notion manually
2. Share it with the integration
3. Copy the page ID from the URL

Page ID is the last part of the URL:
  https://notion.so/YourPage-xxxxxxxxxxxxxxxxxxxxxx
                                    ^^^^^^^^^^^^^^
                                    This is the page ID

Then run:
  python setup_notion_db_manual.py <page_id>

Example:
  python setup_notion_db_manual.py 1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d
    """)

if __name__ == "__main__":
    main()